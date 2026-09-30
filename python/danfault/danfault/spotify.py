"""Control Spotify from the command line via the Spotify Web API.

Unlike ``dbus-send`` (Linux-only) or AppleScript (controls only the local Mac
app), the Web API can drive *any* of your devices — laptop, phone, speakers.

Auth is OAuth 2.0 **Authorization Code with PKCE**: ``spoti login`` opens your
browser, you click *Accept*, and a tiny local server catches the redirect — no
copy-pasting. PKCE means there is no client *secret* to store; only a public
Client ID (from the Spotify Developer Dashboard) is needed. Tokens are cached in
``~/.config/danfault/spotify.json`` (locked to ``chmod 600``) and refreshed
silently when they expire.

CLI (installed as the standalone ``spoti`` command, also wired into
``danfault spotify``)::

    spoti login --client-id <id>     # one-time; then just `spoti login`
    spoti now
    spoti play | pause | playpause | next | prev
    spoti vol 40
    spoti shuffle on | off
    spoti repeat track | context | off
    spoti devices
    spoti transfer "MacBook"
    spoti search "miles davis" --play
    spoti playlist-export "my playlist"
    spoti playlist-export spotify:playlist:<id> --output tracks.json

See ``docs/spoti.md`` for setup and a full reference.
"""

import base64
import hashlib
import http.server
import json
import os
import re
import secrets
import sys
import threading
import time
import urllib.parse
import webbrowser
from difflib import get_close_matches
from pathlib import Path
from typing import Optional

import requests
import typer

from danfault.logs import Loggir

log = Loggir()

# ──────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

GETSONGBPM_API = "https://api.getsongbpm.com"

CALLBACK_PORT = 8888
REDIRECT_URI = f"http://127.0.0.1:{CALLBACK_PORT}/callback"

SCOPES = (
    "user-read-playback-state "
    "user-modify-playback-state "
    "user-read-currently-playing "
    "playlist-read-private "
    "playlist-read-collaborative"
)

CONFIG_FILE = Path.home() / ".config" / "danfault" / "spotify.json"
BPM_CACHE_FILE = Path.home() / ".config" / "danfault" / "bpm_cache.json"

# Refresh a little before the access token actually expires.
_EXPIRY_SKEW = 60  # seconds

app = typer.Typer(help="Control Spotify from the command line (Web API).")


# ──────────────────────────────────────────────────────────────────────────
# Config / token storage
# ──────────────────────────────────────────────────────────────────────────


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            log.warning("Could not read %s; treating as empty.", CONFIG_FILE)
    return {}


def _save_config(data: dict) -> None:
    """Persist config and lock the file to owner-only (it holds a refresh token)."""
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except OSError:
        pass  # Best-effort on filesystems without POSIX perms.


def _client_id(explicit: Optional[str] = None) -> str:
    """Resolve the Client ID: explicit arg → env var → config file."""
    cid = explicit or os.environ.get("SPOTIFY_CLIENT_ID") or _load_config().get("client_id")
    if not cid:
        raise typer.BadParameter(
            "No Spotify Client ID found. Create an app at "
            "https://developer.spotify.com/dashboard (redirect URI "
            f"{REDIRECT_URI}), then run: spoti login --client-id <id>  "
            "(or set SPOTIFY_CLIENT_ID)."
        )
    return cid


# ──────────────────────────────────────────────────────────────────────────
# PKCE + OAuth flow
# ──────────────────────────────────────────────────────────────────────────


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _pkce_pair() -> tuple:
    """Return (code_verifier, code_challenge) for the PKCE flow."""
    verifier = _b64url(secrets.token_bytes(64))
    challenge = _b64url(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    """One-shot handler that captures the ?code= redirect from Spotify."""

    # Filled in by the server instance.
    result: dict = {}

    def do_GET(self):  # noqa: N802 (stdlib naming)
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return
        params = urllib.parse.parse_qs(parsed.query)
        self.server.result = {  # type: ignore[attr-defined]
            "code": params.get("code", [None])[0],
            "state": params.get("state", [None])[0],
            "error": params.get("error", [None])[0],
        }
        ok = self.server.result.get("code") and not self.server.result.get("error")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        title = "✓ Authorized" if ok else "✗ Authorization failed"
        body = "You can close this tab and return to the terminal."
        self.wfile.write(
            f"<html><body style='font-family:sans-serif;text-align:center;"
            f"margin-top:4rem'><h2>{title}</h2><p>{body}</p></body></html>".encode()
        )

    def log_message(self, *args):  # silence the default stderr logging
        pass


def _run_auth_flow(client_id: str) -> None:
    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)
    query = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
            "state": state,
            "code_challenge_method": "S256",
            "code_challenge": challenge,
        }
    )
    url = f"{AUTH_URL}?{query}"

    server = http.server.HTTPServer(("127.0.0.1", CALLBACK_PORT), _CallbackHandler)
    server.result = {}  # type: ignore[attr-defined]

    log.info("Opening your browser to authorize Spotify…")
    if not webbrowser.open(url):
        log.warning("Could not open a browser automatically. Visit this URL:\n%s", url)

    server.handle_request()  # blocks until the single callback arrives
    server.server_close()
    result = server.result  # type: ignore[attr-defined]

    if result.get("error"):
        log.error("Authorization denied: %s", result["error"])
        raise typer.Exit(code=1)
    if not result.get("code"):
        log.error("No authorization code received.")
        raise typer.Exit(code=1)
    if result.get("state") != state:
        log.error("State mismatch — aborting for safety.")
        raise typer.Exit(code=1)

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": result["code"],
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "code_verifier": verifier,
        },
        timeout=15,
    )
    if resp.status_code != 200:
        log.error("Token exchange failed (%s): %s", resp.status_code, resp.text)
        raise typer.Exit(code=1)

    tok = resp.json()
    cfg = _load_config()
    cfg.update(
        {
            "client_id": client_id,
            "access_token": tok["access_token"],
            "refresh_token": tok.get("refresh_token", cfg.get("refresh_token")),
            "expires_at": time.time() + tok.get("expires_in", 3600),
        }
    )
    _save_config(cfg)
    log.info("Logged in. Token cached at %s", CONFIG_FILE)


def _refresh_access_token() -> str:
    cfg = _load_config()
    refresh = cfg.get("refresh_token")
    if not refresh:
        log.error("No refresh token. Run: spoti login")
        raise typer.Exit(code=1)

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": _client_id(),
        },
        timeout=15,
    )
    if resp.status_code != 200:
        log.error("Token refresh failed (%s): %s. Try: spoti login", resp.status_code, resp.text)
        raise typer.Exit(code=1)

    tok = resp.json()
    cfg["access_token"] = tok["access_token"]
    # Spotify may omit a new refresh token — keep the existing one if so.
    cfg["refresh_token"] = tok.get("refresh_token", refresh)
    cfg["expires_at"] = time.time() + tok.get("expires_in", 3600)
    _save_config(cfg)
    return cfg["access_token"]


def _get_access_token() -> str:
    cfg = _load_config()
    if not cfg.get("access_token"):
        log.error("Not logged in. Run: spoti login --client-id <id>")
        raise typer.Exit(code=1)
    if time.time() >= cfg.get("expires_at", 0) - _EXPIRY_SKEW:
        return _refresh_access_token()
    return cfg["access_token"]


# ──────────────────────────────────────────────────────────────────────────
# API wrapper
# ──────────────────────────────────────────────────────────────────────────


def _api(method: str, path: str, **kwargs):
    """Call the Web API. Returns parsed JSON, or None for empty/204 responses.

    Handles a 401 by refreshing the token once and retrying, and turns the
    common "no active device" case into a friendly message.
    """
    url = path if path.startswith("http") else f"{API_BASE}{path}"

    def _do(token: str):
        headers = {"Authorization": f"Bearer {token}", **kwargs.pop("headers", {})}
        return requests.request(method, url, headers=headers, timeout=15, **kwargs)

    token = _get_access_token()
    resp = _do(token)
    if resp.status_code == 401:
        resp = _do(_refresh_access_token())

    if resp.status_code == 204 or not resp.content:
        return None
    if resp.status_code == 404:
        log.error(
            "No active device. Open Spotify on a device (then `spoti devices` / "
            "`spoti transfer <name>`) and try again."
        )
        raise typer.Exit(code=1)
    if resp.status_code >= 400:
        msg = resp.text
        try:
            msg = resp.json().get("error", {}).get("message", msg)
        except (ValueError, AttributeError):
            pass
        log.error("Spotify API error (%s): %s", resp.status_code, msg)
        raise typer.Exit(code=1)

    try:
        return resp.json()
    except ValueError:
        return None


# ──────────────────────────────────────────────────────────────────────────
# Small helpers
# ──────────────────────────────────────────────────────────────────────────


def _fmt_track(item: Optional[dict]) -> str:
    if not item:
        return "(unknown track)"
    artists = ", ".join(a["name"] for a in item.get("artists", []))
    name = item.get("name", "?")
    album = item.get("album", {}).get("name")
    return f"{artists} — {name}" + (f"  ({album})" if album else "")


def _resolve_device(name: str) -> str:
    data = _api("GET", "/me/player/devices") or {}
    devices = data.get("devices", [])
    if not devices:
        log.error("No devices found. Open Spotify on a device first.")
        raise typer.Exit(code=1)
    by_name = {d["name"]: d["id"] for d in devices}
    # Exact (case-insensitive) first, then fuzzy.
    for dname, did in by_name.items():
        if dname.lower() == name.lower():
            return did
    match = get_close_matches(name, list(by_name), n=1, cutoff=0.3)
    if not match:
        names = ", ".join(by_name) or "(none)"
        log.error("No device matching %r. Available: %s", name, names)
        raise typer.Exit(code=1)
    return by_name[match[0]]


def _search(query: str, type_: str = "track", limit: int = 5) -> list:
    """Run a catalog search and return the list of result items."""
    data = _api("GET", "/search", params={"q": query, "type": type_, "limit": limit}) or {}
    return data.get(f"{type_}s", {}).get("items", [])


def _result_label(item: dict, type_: str) -> str:
    return _fmt_track(item) if type_ == "track" else item.get("name", "?")


def _print_results(items: list, type_: str) -> None:
    for i, item in enumerate(items, 1):
        typer.echo(f"{i}. {_result_label(item, type_)}")


def _pick(items: list, type_: str) -> Optional[dict]:
    """Let the user choose a result. Arrow-key menu on a TTY, numbered prompt otherwise.

    Returns the chosen item, or None if cancelled.
    """
    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            import questionary

            choices = [
                questionary.Choice(_result_label(it, type_), value=idx)
                for idx, it in enumerate(items)
            ]
            idx = questionary.select("Pick one to play:", choices=choices).ask()
            return items[idx] if idx is not None else None
        except ImportError:
            log.warning(
                "questionary not installed; using a numbered prompt. "
                "Install it with: pip install questionary"
            )

    # Non-interactive (or no questionary): numbered fallback.
    _print_results(items, type_)
    sel = typer.prompt(f"Play which? [1-{len(items)}] (0 to cancel)", default=0, type=int)
    return items[sel - 1] if 1 <= sel <= len(items) else None


def _play_item(item: dict, type_: str) -> None:
    if type_ == "track":
        _api("PUT", "/me/player/play", json={"uris": [item["uri"]]})
    else:
        _api("PUT", "/me/player/play", json={"context_uri": item["uri"]})
    log.info("▶ playing %s", _result_label(item, type_))


# ──────────────────────────────────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────────────────────────────────


@app.command()
def login(client_id: Optional[str] = typer.Option(None, "--client-id", help="Spotify app Client ID")):
    """Authorize via the browser and cache tokens locally."""
    cid = _client_id(client_id)
    if client_id:
        cfg = _load_config()
        cfg["client_id"] = client_id
        _save_config(cfg)
    _run_auth_flow(cid)


@app.command()
def logout():
    """Delete the cached tokens."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        log.info("Removed %s", CONFIG_FILE)
    else:
        log.info("Nothing to remove.")


@app.command()
def now():
    """Show the currently playing track."""
    data = _api("GET", "/me/player/currently-playing")
    if not data or not data.get("item"):
        log.info("Nothing playing.")
        return
    state = "▶ playing" if data.get("is_playing") else "⏸ paused"
    device = (data.get("device") or {}).get("name", "")
    typer.echo(f"{state}  {_fmt_track(data['item'])}" + (f"  @ {device}" if device else ""))


@app.command()
def play(
    song: Optional[str] = typer.Argument(None, help="Song to search and play; omit to resume"),
    first: bool = typer.Option(False, "--first", "-f", help="Play the top result, skipping the picker"),
):
    """Resume playback, or search for a song and play it."""
    if song is None:
        _api("PUT", "/me/player/play")
        log.info("▶ play")
        return
    items = _search(song, "track")
    if not items:
        log.info("No results for %r.", song)
        return
    if first:
        _play_item(items[0], "track")
        return
    chosen = _pick(items, "track")
    if chosen:
        _play_item(chosen, "track")
    else:
        log.info("Cancelled.")


@app.command()
def pause():
    """Pause playback."""
    _api("PUT", "/me/player/pause")
    log.info("⏸ pause")


@app.command()
def playpause():
    """Toggle play/pause based on the current state."""
    data = _api("GET", "/me/player") or {}
    if data.get("is_playing"):
        _api("PUT", "/me/player/pause")
        log.info("⏸ pause")
    else:
        _api("PUT", "/me/player/play")
        log.info("▶ play")


@app.command(name="pp")
def pp():
    """Alias for `playpause`."""
    playpause()


@app.command()
def next():
    """Skip to the next track."""
    _api("POST", "/me/player/next")
    log.info("⏭ next")


@app.command(name="prev")
def prev():
    """Go to the previous track."""
    _api("POST", "/me/player/previous")
    log.info("⏮ previous")


@app.command()
def vol(
    level: int = typer.Argument(..., help="Volume 0–100"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip the large-jump confirmation"),
):
    """Set the volume (0–100). Confirms before a jump up of 50 or more."""
    level = max(0, min(100, level))
    # Guardrail: a large positive jump can be a painful surprise — confirm first.
    if not yes:
        current = (_api("GET", "/me/player") or {}).get("device", {}).get("volume_percent")
        if current is not None and level - current >= 50:
            if not typer.confirm(
                f"Raise volume from {current}% to {level}% (+{level - current})?"
            ):
                log.info("Volume unchanged.")
                raise typer.Abort()
    _api("PUT", "/me/player/volume", params={"volume_percent": level})
    log.info("🔊 volume %d%%", level)


@app.command()
def shuffle(state: str = typer.Argument(..., help="on | off")):
    """Turn shuffle on or off."""
    s = state.lower()
    if s not in ("on", "off"):
        raise typer.BadParameter("state must be 'on' or 'off'")
    _api("PUT", "/me/player/shuffle", params={"state": "true" if s == "on" else "false"})
    log.info("🔀 shuffle %s", s)


@app.command()
def repeat(mode: str = typer.Argument(..., help="track | context | off")):
    """Set repeat mode (track, context, or off)."""
    m = mode.lower()
    if m not in ("track", "context", "off"):
        raise typer.BadParameter("mode must be 'track', 'context', or 'off'")
    _api("PUT", "/me/player/repeat", params={"state": m})
    log.info("🔁 repeat %s", m)


@app.command()
def devices():
    """List your available Spotify devices."""
    data = _api("GET", "/me/player/devices") or {}
    items = data.get("devices", [])
    if not items:
        log.info("No devices found. Open Spotify on a device first.")
        return
    for d in items:
        marker = "●" if d.get("is_active") else "○"
        vol = d.get("volume_percent")
        vol_str = f"  {vol}%" if vol is not None else ""
        typer.echo(f"{marker} {d['name']}  [{d.get('type', '?')}]{vol_str}")


@app.command()
def transfer(name: str = typer.Argument(..., help="Device name (fuzzy matched)")):
    """Transfer playback to a device by name."""
    device_id = _resolve_device(name)
    _api("PUT", "/me/player", json={"device_ids": [device_id], "play": True})
    log.info("➡ transferred playback to %r", name)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    play: bool = typer.Option(False, "--play", help="Pick a result to play"),
    type_: str = typer.Option("track", "--type", help="track | album | artist | playlist"),
):
    """Search the Spotify catalog. With --play, pick a result to play."""
    items = _search(query, type_)
    if not items:
        log.info("No results for %r.", query)
        return
    if not play:
        _print_results(items, type_)
        return
    chosen = _pick(items, type_)
    if chosen:
        _play_item(chosen, type_)
    else:
        log.info("Cancelled.")


def _extract_playlist_id(value: str) -> str:
    """Accept a Spotify URI, URL, or raw ID and return just the playlist ID."""
    # spotify:playlist:<id>
    if value.startswith("spotify:playlist:"):
        return value.split(":")[-1]
    # https://open.spotify.com/playlist/<id>?...
    if "open.spotify.com/playlist/" in value:
        return value.split("/playlist/")[-1].split("?")[0]
    # Assume raw ID
    return value.strip()


def _fetch_all_playlist_tracks(playlist_id: str) -> list[dict]:
    """Fetch every track in a playlist, handling Spotify's 100-item page limit."""
    tracks = []
    url = f"/playlists/{playlist_id}/tracks"
    params = {"limit": 100, "offset": 0, "fields": (
        "next,items(added_at,track(id,name,uri,duration_ms,popularity,explicit,"
        "artists(id,name),album(id,name,release_date),"
        "external_urls))"
    )}
    while url:
        page = _api("GET", url, params=params) or {}
        for item in page.get("items", []):
            t = item.get("track")
            if not t or t.get("id") is None:  # skip local/null tracks
                continue
            tracks.append({
                "added_at": item.get("added_at"),
                "id": t["id"],
                "name": t.get("name"),
                "uri": t.get("uri"),
                "duration_ms": t.get("duration_ms"),
                "popularity": t.get("popularity"),
                "explicit": t.get("explicit"),
                "artists": [{"id": a["id"], "name": a["name"]} for a in t.get("artists", [])],
                "album": {
                    "id": t["album"]["id"],
                    "name": t["album"]["name"],
                    "release_date": t["album"].get("release_date"),
                } if t.get("album") else None,
                "url": (t.get("external_urls") or {}).get("spotify"),
            })
        url = page.get("next")
        params = {}  # next URL already contains all query params
    return tracks


_AF_FIELDS = (
    "tempo", "energy", "danceability", "valence", "loudness",
    "acousticness", "instrumentalness", "liveness", "speechiness",
    "key", "mode", "time_signature",
)


def _fetch_audio_features(track_ids: list[str]) -> dict:
    """Return {track_id: {tempo, energy, …}} for the given IDs (batched).

    Uses requests directly (not _api) so a 403 is a soft warning, not a hard exit.
    Spotify restricted this endpoint in Nov 2024 for most app tiers.
    """
    out: dict = {}
    token = _get_access_token()
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i : i + 100]
        resp = requests.get(
            f"{API_BASE}/audio-features",
            headers={"Authorization": f"Bearer {token}"},
            params={"ids": ",".join(batch)},
            timeout=15,
        )
        if resp.status_code == 403:
            log.warning(
                "Audio features unavailable (403) — Spotify restricted this endpoint "
                "in Nov 2024 for most app tiers. BPM/energy data will be skipped."
            )
            break
        if resp.status_code != 200:
            log.warning("Audio features request failed (%s); skipping.", resp.status_code)
            break
        for af in resp.json().get("audio_features") or []:
            if af and af.get("id"):
                out[af["id"]] = {k: af.get(k) for k in _AF_FIELDS}
    return out


@app.command(name="playlist-export")
def playlist_export(
    query: str = typer.Argument(..., help="Playlist name/search query, Spotify URI, or URL"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output JSON file (default: <playlist>.json)"),
    audio_features: bool = typer.Option(True, "--audio-features/--no-audio-features", help="Embed BPM and audio features into each track"),
):
    """Export all tracks from a playlist to a JSON file for analysis."""
    # Resolve to a playlist ID — either directly or via search.
    is_direct = (
        query.startswith("spotify:playlist:")
        or "open.spotify.com/playlist/" in query
        or re.fullmatch(r"[A-Za-z0-9]{22}", query)
    )

    if is_direct:
        playlist_id = _extract_playlist_id(query)
        meta = _api("GET", f"/playlists/{playlist_id}", params={
            "fields": "id,name,description,owner(display_name),snapshot_id,tracks(total)"
        }) or {}
        playlist_name = meta.get("name", playlist_id)
    else:
        results = _search(query, "playlist", limit=10)
        if not results:
            log.error("No playlists found for %r.", query)
            raise typer.Exit(code=1)
        chosen = _pick(results, "playlist")
        if not chosen:
            log.info("Cancelled.")
            return
        playlist_id = chosen["id"]
        meta = chosen

    playlist_name = meta.get("name", playlist_id)
    total = (meta.get("tracks") or {}).get("total") if isinstance(meta.get("tracks"), dict) else meta.get("tracks", {}).get("total", "?")
    owner = (meta.get("owner") or {}).get("display_name", "?")

    typer.echo(f"Exporting: {playlist_name}  ({total} tracks)  by {owner}")

    tracks = _fetch_all_playlist_tracks(playlist_id)

    if audio_features:
        typer.echo("Fetching audio features (BPM, energy, key, …)…")
        ids = [t["id"] for t in tracks if t.get("id")]
        af_map = _fetch_audio_features(ids)
        for t in tracks:
            t["features"] = af_map.get(t["id"])
        if not af_map:
            typer.echo("  Audio features unavailable — exporting without BPM/energy data.")

    payload = {
        "playlist": {
            "id": meta.get("id", playlist_id),
            "name": playlist_name,
            "description": meta.get("description", ""),
            "owner": owner,
            "total": len(tracks),
            "snapshot_id": meta.get("snapshot_id"),
        },
        "tracks": tracks,
    }

    if output is None:
        safe_name = re.sub(r'[^\w\- ]', '', playlist_name).strip().replace(" ", "_")
        output = Path(f"{safe_name}.json")

    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    typer.echo(f"Saved {len(tracks)} tracks → {output}")


# ──────────────────────────────────────────────────────────────────────────
# BPM enrichment via GetSongBPM  (https://getsongbpm.com/api)
# ──────────────────────────────────────────────────────────────────────────


def _bpm_cache_load() -> dict:
    """Load the shared BPM cache (keyed by 'artist|title')."""
    if BPM_CACHE_FILE.exists():
        try:
            return json.loads(BPM_CACHE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _bpm_cache_save(cache: dict) -> None:
    BPM_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BPM_CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False))


def _bpm_cache_key(artist: str, title: str) -> str:
    return f"{artist.lower().strip()}|{title.lower().strip()}"


def _getsongbpm_key(explicit: Optional[str] = None) -> str:
    key = explicit or os.environ.get("GETSONGBPM_API_KEY") or _load_config().get("getsongbpm_api_key")
    if not key:
        raise typer.BadParameter(
            "No GetSongBPM API key. Register (free) at https://getsongbpm.com/api "
            "then pass --api-key or set GETSONGBPM_API_KEY."
        )
    return key


def _bpm_lookup(api_key: str, artist: str, title: str) -> Optional[float]:
    """Search GetSongBPM for a single track and return its BPM, or None."""
    lookup = f"song:{urllib.parse.quote(title)}+artist:{urllib.parse.quote(artist)}"
    try:
        resp = requests.get(
            f"{GETSONGBPM_API}/search/",
            params={"api_key": api_key, "type": "both", "lookup": lookup},
            timeout=10,
        )
    except requests.RequestException:
        return None

    if resp.status_code != 200:
        return None

    results = resp.json().get("search") or []
    if not results:
        return None

    # Pick the best match: prefer results where both title and artist match closely.
    title_lc = title.lower()
    artist_lc = artist.lower()
    for r in results[:5]:
        r_title = (r.get("title") or "").lower()
        r_artist = (r.get("artist") or {}).get("name", "").lower()
        title_ok = title_lc in r_title or r_title in title_lc
        artist_ok = artist_lc in r_artist or r_artist in artist_lc
        if title_ok and artist_ok:
            try:
                return float(r["tempo"])
            except (KeyError, ValueError, TypeError):
                pass

    # Looser fallback: title-only match
    for r in results[:3]:
        r_title = (r.get("title") or "").lower()
        if title_lc in r_title or r_title in title_lc:
            try:
                return float(r["tempo"])
            except (KeyError, ValueError, TypeError):
                pass

    return None


@app.command(name="enrich-bpm")
def enrich_bpm(
    playlist_file: Path = typer.Argument(..., help="Exported playlist JSON to enrich"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="GetSongBPM API key (or GETSONGBPM_API_KEY env var)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file (default: overwrites input)"),
    force: bool = typer.Option(False, "--force", "-f", help="Re-fetch even tracks that already have BPM"),
    delay: float = typer.Option(0.25, "--delay", help="Seconds between API calls (be kind to the free tier)"),
):
    """Fetch BPM for each track from GetSongBPM and patch the playlist JSON.

    Requires a free API key from https://getsongbpm.com/api
    (only needs an email; a GitHub repo URL is accepted as the website).
    """
    key = _getsongbpm_key(api_key)

    # Persist the key for future calls
    if api_key:
        cfg = _load_config()
        cfg["getsongbpm_api_key"] = api_key
        _save_config(cfg)

    try:
        data = json.loads(playlist_file.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        log.error("Could not read %s: %s", playlist_file, exc)
        raise typer.Exit(code=1)

    tracks = data.get("tracks", [])
    pl_name = data.get("playlist", {}).get("name", playlist_file.stem)

    todo = [t for t in tracks if force or t.get("bpm") is None]
    if not todo:
        typer.echo(f"All {len(tracks)} tracks already have BPM. Use --force to re-fetch.")
        return

    bpm_cache = _bpm_cache_load()
    cache_hits = sum(
        1 for t in todo
        if _bpm_cache_key(((t.get("artists") or [{}])[0]).get("name", ""), t.get("name", "")) in bpm_cache
    )
    typer.echo(
        f"Enriching {len(todo)}/{len(tracks)} tracks from '{pl_name}' "
        f"({cache_hits} cached, {len(todo) - cache_hits} to fetch)…"
    )

    found = skipped = fetched = 0
    pad = len(str(len(todo)))
    cache_dirty = False

    for i, track in enumerate(todo, 1):
        artist = ((track.get("artists") or [{}])[0]).get("name", "")
        title = track.get("name", "")
        ck = _bpm_cache_key(artist, title)

        if ck in bpm_cache:
            entry = bpm_cache[ck]
            bpm = entry.get("bpm")
            source = entry.get("source", "getsongbpm")
            from_cache = True
        else:
            bpm = _bpm_lookup(key, artist, title)
            source = "getsongbpm" if bpm else None
            bpm_cache[ck] = {"bpm": bpm, "source": source, "artist": artist, "title": title}
            cache_dirty = True
            from_cache = False
            fetched += 1
            if i < len(todo):
                time.sleep(delay)

        track["bpm"] = bpm
        track["bpm_source"] = source

        marker = f"{bpm:.0f} BPM" if bpm else "—"
        tag = " (cached)" if from_cache else ""
        typer.echo(f"  [{i:>{pad}}/{len(todo)}] {artist} — {title}: {marker}{tag}")

        if bpm:
            found += 1
        else:
            skipped += 1

    if cache_dirty:
        _bpm_cache_save(bpm_cache)
        typer.echo(f"  BPM cache updated → {BPM_CACHE_FILE}  ({len(bpm_cache)} entries)")

    out = output or playlist_file
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    typer.echo(f"\nFound {found}/{len(todo)} BPMs → {out}")
    if skipped:
        typer.echo(f"  {skipped} tracks not matched on GetSongBPM.")


# ──────────────────────────────────────────────────────────────────────────
# Dashboard UI  (React/Vite build served as static files)
# ──────────────────────────────────────────────────────────────────────────

_UI_DIR = Path(__file__).parent.parent / "spoti-ui"

_PLACEHOLDER_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Spoti Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2/plotly.min.js"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0d0d0d;--surface:#1a1a1a;--surface2:#252525;
  --green:#1db954;--text:#e4e4e4;--muted:#666;--radius:10px;
}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;min-height:100vh}
header{background:#000;padding:14px 28px;display:flex;align-items:center;gap:10px;border-bottom:1px solid #1a1a1a}
header h1{color:var(--green);font-size:1.05rem;letter-spacing:-.01em;font-weight:700}
header small{color:var(--muted);font-size:.78rem}
.tabs{background:var(--surface);display:flex;padding:0 24px;border-bottom:1px solid #222}
.tab{padding:11px 18px;cursor:pointer;font-size:.86rem;color:var(--muted);border-bottom:2px solid transparent;user-select:none;transition:color .12s,border-color .12s}
.tab.active{color:var(--text);border-color:var(--green)}
.tab:hover:not(.active){color:var(--text)}
.pane{display:none;padding:28px;max-width:1100px;margin:0 auto}
.pane.active{display:block}

/* Library */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px}
.card{background:var(--surface);border-radius:var(--radius);padding:18px;border:2px solid transparent;transition:border-color .12s,background .12s;display:flex;flex-direction:column}
.card:hover{background:var(--surface2)}
.card.sel{border-color:var(--green)}
.card-name{font-weight:600;font-size:.9rem;margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card-sub{font-size:.76rem;color:var(--muted);flex:1}
.btn{margin-top:14px;background:var(--green);color:#000;border:none;border-radius:20px;padding:7px 0;font-size:.78rem;font-weight:700;cursor:pointer;width:100%;transition:background .1s}
.btn:hover{background:#1ed760}

/* Analysis */
.anlys-head{margin-bottom:22px}
.anlys-head h2{font-size:1.05rem;margin-bottom:4px}
.anlys-head p{color:var(--muted);font-size:.82rem}
.chart-stack{display:flex;flex-direction:column;gap:18px}
.chart-box{background:var(--surface);border-radius:var(--radius);padding:20px 18px}
.chart-box h3{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:14px}
.chart-box h3 em{color:var(--green);font-style:normal}

.ph{color:var(--muted);padding:60px;text-align:center;font-size:.9rem;line-height:1.6}
.ph code{background:var(--surface);padding:2px 7px;border-radius:4px;font-size:.82rem;color:var(--text)}
</style>
</head>
<body>
<header>
  <h1>&#9899; Spoti</h1>
  <small>Dashboard</small>
</header>
<div class="tabs">
  <div class="tab active" data-tab="library">Library</div>
  <div class="tab" data-tab="analysis">Analysis</div>
</div>
<div class="pane active" id="pane-library">
  <div id="lib" class="ph">Loading&hellip;</div>
</div>
<div class="pane" id="pane-analysis">
  <div id="anlys" class="ph">&#8592; Pick a playlist in the Library tab.</div>
</div>

<script>
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}

const GREEN='#1db954';
const BASE={paper_bgcolor:'#1a1a1a',plot_bgcolor:'#1a1a1a',
  font:{color:'#e4e4e4',family:'-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',size:12},
  xaxis:{gridcolor:'#2b2b2b',zerolinecolor:'#2b2b2b'},
  yaxis:{gridcolor:'#2b2b2b',zerolinecolor:'#2b2b2b'}};
const CFG={responsive:true,displayModeBar:false};

// ── tabs ──────────────────────────────────────────────────────────────────
document.querySelectorAll('.tab').forEach(tab=>{
  tab.addEventListener('click',()=>{
    document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t===tab));
    document.querySelectorAll('.pane').forEach(p=>p.classList.toggle('active',p.id==='pane-'+tab.dataset.tab));
    if(tab.dataset.tab==='analysis')
      document.querySelectorAll('[id^="ch-"]').forEach(el=>Plotly.Plots.resize(el));
  });
});

// ── library ───────────────────────────────────────────────────────────────
async function loadLib(){
  const playlists=await fetch('/api/playlists').then(r=>r.json());
  const el=document.getElementById('lib');
  if(!playlists.length){
    el.innerHTML='<div class="ph">No exported playlists found.<br>Run <code>spoti playlist-export &ldquo;my playlist&rdquo;</code> first.</div>';
    return;
  }
  el.className='grid';
  el.innerHTML=playlists.map(p=>`
    <div class="card" data-file="${esc(p.file)}">
      <div class="card-name" title="${esc(p.name)}">${esc(p.name)}</div>
      <div class="card-sub">${p.total} tracks &middot; ${esc(p.owner)}</div>
      <button class="btn">Analyse &rarr;</button>
    </div>`).join('');
  el.querySelectorAll('.btn').forEach(btn=>{
    btn.addEventListener('click',()=>analyse(btn.closest('.card').dataset.file));
  });
}

// ── analysis ──────────────────────────────────────────────────────────────
async function analyse(file){
  document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t.dataset.tab==='analysis'));
  document.querySelectorAll('.pane').forEach(p=>p.classList.toggle('active',p.id==='pane-analysis'));
  document.querySelectorAll('.card').forEach(c=>c.classList.toggle('sel',c.dataset.file===file));

  const el=document.getElementById('anlys');
  el.className='ph'; el.textContent='Fetching audio features…';

  const [playlist,features]=await Promise.all([
    fetch('/api/playlist?file='+encodeURIComponent(file)).then(r=>r.json()),
    fetch('/api/audio-features?file='+encodeURIComponent(file)).then(r=>r.json()),
  ]);
  render(playlist,features,el);
}

function render(playlist,features,el){
  const tracks=playlist.tracks||[];
  const pl=playlist.playlist||{};

  // artist counts
  const ac={};
  tracks.forEach(t=>(t.artists||[]).forEach(a=>{ac[a.name]=(ac[a.name]||0)+1}));
  const sorted=Object.entries(ac).sort((a,b)=>b[1]-a[1]).slice(0,25);
  const aNames=sorted.map(([n])=>n).reverse();
  const aCounts=sorted.map(([,c])=>c).reverse();

  // bpm series
  const bpmX=[],bpmY=[],bpmTip=[];
  tracks.forEach((t,i)=>{
    const af=features[t.id];
    if(!af||!af.tempo)return;
    bpmX.push(i+1);
    bpmY.push(+af.tempo.toFixed(1));
    bpmTip.push('#'+(i+1)+' – '+t.name+'<br>'+(t.artists||[]).map(a=>a.name).join(', '));
  });
  const hasBpm=bpmX.length>0;

  el.className='';
  el.innerHTML=`
    <div class="anlys-head">
      <h2>${esc(pl.name||'')}</h2>
      <p>${pl.total||0} tracks &middot; ${esc(pl.owner||'')}</p>
    </div>
    <div class="chart-stack">
      <div class="chart-box"><h3>Artist distribution <em>(top 25)</em></h3><div id="ch-artists"></div></div>
      <div class="chart-box"><h3>BPM distribution</h3><div id="ch-bpm-hist"></div></div>
      <div class="chart-box"><h3>BPM over playlist</h3><div id="ch-bpm-line"></div></div>
    </div>`;

  const artistH=Math.max(260,aNames.length*22+60);
  Plotly.newPlot('ch-artists',[{
    type:'bar',orientation:'h',x:aCounts,y:aNames,
    marker:{color:GREEN},
    hovertemplate:'<b>%{y}</b>: %{x} tracks<extra></extra>',
  }],{...BASE,height:artistH,
    margin:{l:160,r:20,t:8,b:40},
    xaxis:{...BASE.xaxis,title:'Tracks',tickformat:'d'},
  },CFG);

  Plotly.newPlot('ch-bpm-hist',[{
    type:'histogram',x:bpmY,nbinsx:20,
    marker:{color:GREEN,line:{color:'#0d0d0d',width:1}},
    hovertemplate:'BPM ~%{x}: %{y} tracks<extra></extra>',
  }],{...BASE,height:260,
    margin:{l:60,r:20,t:8,b:48},
    xaxis:{...BASE.xaxis,title:'BPM'},
    yaxis:{...BASE.yaxis,title:'Tracks'},
  },CFG);

  Plotly.newPlot('ch-bpm-line',
    hasBpm?[{
      type:'scatter',mode:'lines+markers',
      x:bpmX,y:bpmY,text:bpmTip,
      hovertemplate:'%{text}<br><b>BPM: %{y}</b><extra></extra>',
      line:{color:GREEN,width:1.5},
      marker:{color:GREEN,size:5},
    }]:[],
    {...BASE,height:300,
      margin:{l:60,r:20,t:8,b:48},
      xaxis:{...BASE.xaxis,title:'Track position'},
      yaxis:{...BASE.yaxis,title:'BPM'},
      ...(hasBpm?{}:{annotations:[{
        text:'No BPM data — run <b>spoti login</b> to refresh scopes',
        xref:'paper',yref:'paper',x:.5,y:.5,showarrow:false,
        font:{color:'#666',size:13},
      }]}),
    },CFG);
}

loadLib();
</script>
</body>
</html>"""


def _make_ui_handler(search_dir: Path, dist_dir: Optional[Path]):
    import mimetypes

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            try:
                self._route()
            except Exception as exc:
                self._json({"error": str(exc)}, code=500)

        def _route(self):
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            p = parsed.path

            if p == "/api/playlists":
                self._json(self._list_playlists())
            elif p == "/api/playlist":
                self._json(self._get_playlist(qs.get("file", [None])[0]))
            elif p == "/api/audio-features":
                self._json(self._get_audio_features(qs.get("file", [None])[0]))
            elif dist_dir is not None:
                self._serve_static(p)
            else:
                # --dev mode: no static files, just the API
                self.send_response(404)
                self.end_headers()

        def _serve_static(self, path: str):
            rel = path.lstrip("/") or "index.html"
            target = dist_dir / rel
            # SPA fallback: unknown paths → index.html
            if not target.exists() or target.is_dir():
                target = dist_dir / "index.html"
            try:
                content = target.read_bytes()
                mime, _ = mimetypes.guess_type(str(target))
                self.send_response(200)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Content-Length", len(content))
                self.end_headers()
                self.wfile.write(content)
            except OSError:
                self.send_response(404)
                self.end_headers()

        def _json(self, data, code=200):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        def _list_playlists(self):
            result = []
            for p in sorted(search_dir.glob("*.json")):
                if p.name.startswith("."):
                    continue
                try:
                    data = json.loads(p.read_text())
                    pl = data.get("playlist", {})
                    result.append({
                        "file": p.name,
                        "name": pl.get("name", p.stem),
                        "total": pl.get("total", 0),
                        "owner": pl.get("owner", "?"),
                    })
                except (json.JSONDecodeError, OSError):
                    pass
            return result

        def _get_playlist(self, filename):
            if not filename:
                return {"error": "no file specified"}
            try:
                return json.loads((search_dir / filename).read_text())
            except (OSError, json.JSONDecodeError) as exc:
                return {"error": str(exc)}

        def _get_audio_features(self, filename):
            if not filename:
                return {}
            cache = search_dir / ("." + filename + ".af.json")
            playlist_path = search_dir / filename
            try:
                playlist = json.loads(playlist_path.read_text())
            except (OSError, json.JSONDecodeError):
                return {}

            tracks = playlist.get("tracks", [])

            # If the export already has embedded features, use them directly.
            if tracks and tracks[0].get("features") is not None:
                return {t["id"]: t["features"] for t in tracks if t.get("id") and t.get("features")}

            track_ids = [t["id"] for t in tracks if t.get("id")]
            if not track_ids:
                return {}

            stored: dict = {}
            if cache.exists():
                try:
                    stored = json.loads(cache.read_text())
                except (json.JSONDecodeError, OSError):
                    pass

            missing = [tid for tid in track_ids if tid not in stored]
            if missing:
                try:
                    fetched = _fetch_audio_features(missing)
                    stored.update(fetched)
                except Exception:
                    pass
                try:
                    cache.write_text(json.dumps(stored, indent=2))
                except OSError:
                    pass

            return stored

        def log_message(self, *args):
            pass

    return _Handler


@app.command()
def ui(
    directory: Optional[Path] = typer.Option(None, "--dir", "-d", help="Directory with exported playlist JSONs (default: cwd)"),
    port: int = typer.Option(8889, "--port", "-p", help="Local server port"),
    dev: bool = typer.Option(False, "--dev", help="API-only mode for use alongside `npm run dev`"),
):
    """Launch the Spoti Dashboard (React UI + local API server).

    First build the UI:  cd python/danfault/spoti-ui && npm i && npm run build
    Dev workflow:        spoti ui --dev  +  npm run dev (in spoti-ui/)
    """
    search_dir = (directory or Path.cwd()).resolve()
    if not search_dir.is_dir():
        log.error("Directory not found: %s", search_dir)
        raise typer.Exit(code=1)

    dist_dir = (_UI_DIR / "dist") if not dev else None

    if not dev and not dist_dir.exists():
        log.error("UI not built. Run:")
        log.error("  cd %s", _UI_DIR)
        log.error("  npm install && npm run build")
        raise typer.Exit(code=1)

    url = f"http://127.0.0.1:{port}"
    server = http.server.HTTPServer(("127.0.0.1", port), _make_ui_handler(search_dir, dist_dir))

    if dev:
        log.info("API server at %s  (Ctrl-C to stop)", url)
        log.info("Start the frontend:  npm run dev --prefix %s", _UI_DIR)
    else:
        log.info("Spoti Dashboard → %s  (Ctrl-C to stop)", url)
        log.info("Serving playlists from %s", search_dir)
        threading.Thread(target=lambda: (time.sleep(0.4), webbrowser.open(url)), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Stopped.")


if __name__ == "__main__":
    app()
