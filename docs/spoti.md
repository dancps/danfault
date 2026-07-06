# spoti — Spotify from the command line

A CLI that controls Spotify through the **Spotify Web API**. Because it talks to
Spotify's servers (not a local app), it can drive *any* of your devices — laptop,
phone, or speakers.

## Why the Web API (and not `dbus-send`)?

| Approach | Linux | macOS | Reach |
|----------|:-----:|:-----:|-------|
| `dbus-send` / `playerctl` | ✅ | ❌ | Local app only (MPRIS over D-Bus, Linux-only) |
| AppleScript (`osascript`) | ❌ | ✅ | Local Mac app only |
| **Web API (this tool)** | ✅ | ✅ | **Any device on your account** |

D-Bus does not exist on macOS, and AppleScript can only reach the Spotify app
running on the same Mac. The Web API works everywhere and can control playback on
your phone or a speaker from your terminal.

## Install

```bash
cd python/danfault
pip install -e .
```

This registers the standalone `spoti` command. The same commands are also
available under `danfault spotify ...`.

## One-time setup: get a Client ID

The Web API requires you to register a (free) app to get a **Client ID**. This
takes about two minutes.

1. Go to <https://developer.spotify.com/dashboard> and log in with your normal
   Spotify account.
2. Click **Create app**.
3. Fill in any **name** and **description** (e.g. `spoti-cli`).
4. **Redirect URI** — type exactly:

   ```
   http://127.0.0.1:8888/callback
   ```

   It must match character-for-character (use `127.0.0.1`, *not* `localhost`).
5. Under **APIs to use**, check **Web API**.
6. Save, open the app, and copy the **Client ID**.

Then log in once:

```bash
spoti login --client-id <your-client-id>
```

The Client ID is saved, so future logins are just `spoti login`. You can also
provide it via the `SPOTIFY_CLIENT_ID` environment variable instead.

> The Client ID is **not** a secret — it's safe to keep in config. Thanks to
> PKCE (below) there is no client *secret* involved at all.

## How login works

`spoti login` uses OAuth 2.0 **Authorization Code with PKCE**. In plain terms:

1. The CLI generates a one-time random secret (the *code verifier*) and a hashed
   version of it (the *code challenge*).
2. Your **browser opens** to Spotify's "Allow access?" page, carrying the
   challenge.
3. You click **Accept**.
4. Spotify redirects your browser to `http://127.0.0.1:8888/callback?code=…`.
   The CLI is running a **tiny local web server** on that port that catches the
   redirect — so there's nothing to copy-paste.
5. The CLI sends the code **plus the original verifier** to Spotify, which proves
   the request came from the same program that started it, and gets back your
   tokens.
6. The browser shows a "✓ Authorized — you can close this tab" page, and the
   local server shuts down.

PKCE is what lets a CLI authenticate **without a client secret**: the verifier
takes its place and is generated fresh each time, never stored long-term.

## Token storage & security

After login, Spotify issues two tokens, cached in:

```
~/.config/danfault/spotify.json
```

| Token | Lifetime | Purpose |
|-------|----------|---------|
| **access token** | ~1 hour | Sent with every API call to authorize it |
| **refresh token** | long-lived | Used to silently mint a new access token when it expires |

What keeps this safe:

- **The file is in your home folder, never in the repo or git.**
- **It's locked to `chmod 600`** (owner read/write only) because the refresh
  token is a real credential — anyone who has it could control your Spotify.
- **No client secret exists** to leak (that's the point of PKCE).
- **Scopes are minimal.** The tool requests only what it needs:
  - Playback: `user-read-playback-state`, `user-modify-playback-state`, `user-read-currently-playing`
  - Playlists (read-only): `playlist-read-private`, `playlist-read-collaborative`
  The token cannot read your email, modify your library, or write anything.
- **Refresh is automatic.** When the 1-hour access token expires, the CLI uses
  the refresh token to get a new one — you won't be asked to log in again.

To revoke locally, run `spoti logout` (deletes the file). To fully revoke
access, remove the app under your Spotify account's *Apps* settings.

> **Re-login after scope changes.** If you first logged in before the playlist
> scopes were added, run `spoti login` once more to pick them up.

## Command reference

| Command | What it does |
|---------|--------------|
| `spoti login [--client-id <id>]` | Authorize via the browser; cache tokens |
| `spoti logout` | Delete the cached tokens |
| `spoti now` | Show the currently playing track + state + device |
| `spoti play` | Resume playback |
| `spoti play "<song>"` | Search for a song and pick one to play (arrow-key menu) |
| `spoti play "<song>" --first/-f` | Play the top result, skipping the picker |
| `spoti pause` | Pause playback |
| `spoti playpause` (alias `spoti pp`) | Toggle based on current state |
| `spoti next` | Skip to next track |
| `spoti prev` | Go to previous track |
| `spoti vol <0-100> [--yes/-y]` | Set volume (asks to confirm a jump up of +50 or more; `-y` skips the prompt) |
| `spoti shuffle <on\|off>` | Toggle shuffle |
| `spoti repeat <track\|context\|off>` | Set repeat mode |
| `spoti devices` | List your devices (● = active) |
| `spoti transfer "<name>"` | Move playback to a device (name is fuzzy-matched) |
| `spoti search "<query>" [--play] [--type track]` | List results; `--play` opens the picker to play one |
| `spoti playlist-export "<query>"` | Export a playlist to JSON for analysis |
| `spoti enrich-bpm <file.json>` | Patch exported JSON with BPM from GetSongBPM |
| `spoti ui [--dir <path>]` | Open the analysis dashboard in the browser |

The picker (used by `play "<song>"` and `search --play`) is an arrow-key menu
(↑/↓ + Enter). In a non-interactive terminal it falls back to a numbered prompt
(`Play which? [1-N]`, `0` to cancel).

Examples:

```bash
spoti now
spoti vol 40
spoti shuffle on
spoti transfer "MacBook"
spoti play "so what miles davis"        # pick from a menu
spoti play "so what miles davis" -f     # just play the top hit
spoti search "miles davis"              # list only
spoti search "kind of blue" --type album --play
```

---

## Playlist analysis

### 1 · Export a playlist

`playlist-export` writes every track in a playlist to a JSON file. Pass a
search query, a Spotify URI, a share URL, or a raw playlist ID:

```bash
spoti playlist-export "corremo"
spoti playlist-export spotify:playlist:6daUP1z3VZCaDFcatFd8gW
spoti playlist-export 6daUP1z3VZCaDFcatFd8gW --output ~/data/corremo.json
spoti playlist-export "lofi" --no-audio-features   # skip the feature fetch
```

The file is self-contained — it includes track metadata and attempts to embed
Spotify audio features (BPM, energy, etc.) per track. Those features require
an extended Spotify app tier; if the request returns 403 the export still
succeeds but `features` will be `null` per track.

### 2 · Enrich with BPM (GetSongBPM)

Spotify's audio-features endpoint was restricted in November 2024 for most app
tiers. `enrich-bpm` fetches BPM from [GetSongBPM](https://getsongbpm.com) as an
alternative and patches the exported JSON in-place.

#### Get a free API key

1. Go to <https://getsongbpm.com/api> and fill in the registration form.
   - Email: your normal email.
   - Website: your GitHub repo URL works (`https://github.com/dancps/danfault`).
2. They'll email you a key.
3. Add a backlink somewhere visible (their only requirement for the free tier):

   ```markdown
   BPM data sourced from [GetSongBPM](https://getsongbpm.com).
   ```

#### Run

```bash
spoti enrich-bpm corremo.json --api-key YOUR_KEY   # key is saved after first run
spoti enrich-bpm corremo.json                      # subsequent runs
spoti enrich-bpm corremo.json --force              # re-fetch even tracks that already have BPM
spoti enrich-bpm corremo.json --delay 0.5          # slow down if hitting rate limits
```

The key is persisted to `~/.config/danfault/spotify.json`.

#### BPM cache

Lookups are cached in `~/.config/danfault/bpm_cache.json` keyed by
`"artist|title"`. Running `enrich-bpm` on a second playlist that shares tracks
will not re-query the API for those tracks — it reads from the cache instead.

### 3 · Dashboard (`spoti ui`)

A React/Vite dashboard with two tabs:
- **Library** — all exported `.json` files in the directory.
- **Analysis** — artist distribution, BPM histogram, and BPM-over-playlist
  charts for the selected playlist.

#### First-time build

```bash
cd python/danfault/spoti-ui
npm install
npm run build
```

#### Run

```bash
cd ~/data          # wherever your exported .json files are
spoti ui           # opens http://127.0.0.1:8889 in the browser
spoti ui --dir ~/data --port 8889   # explicit options
```

#### Dev mode (hot reload)

Two terminals:

```bash
# Terminal 1 — Python API server only
spoti ui --dev

# Terminal 2 — Vite dev server
cd python/danfault/spoti-ui && npm run dev
```

Visit `http://localhost:5173`. Changes to `.jsx` files reload instantly.

---

## Data files

### Playlist JSON — `<playlist_name>.json`

Written by `playlist-export`, patched by `enrich-bpm`.

```
{
  "playlist": {
    "id", "name", "description", "owner", "total", "snapshot_id"
  },
  "tracks": [
    {
      "added_at":    "2026-06-13T15:31:48Z",
      "id":          "spotify track ID",
      "name":        "Track Title",
      "uri":         "spotify:track:...",
      "duration_ms": 230880,
      "popularity":  41,
      "explicit":    false,
      "artists":     [{ "id": "...", "name": "Artist" }],
      "album":       { "id": "...", "name": "Album", "release_date": "2006-06-01" },
      "url":         "https://open.spotify.com/track/...",
      "features":    { "tempo": 128.4, "energy": 0.82, ... },  // null if unavailable
      "bpm":         128,        // from GetSongBPM (enrich-bpm)
      "bpm_source":  "getsongbpm"
    },
    ...
  ]
}
```

`features` fields (when available): `tempo`, `energy`, `danceability`, `valence`,
`loudness`, `acousticness`, `instrumentalness`, `liveness`, `speechiness`,
`key`, `mode`, `time_signature`.

### BPM cache — `~/.config/danfault/bpm_cache.json`

Shared across all playlists. Keyed by `"artist|title"` (lowercase).

```
{
  "fresno|absolutamente nada": {
    "bpm": 128,
    "source": "getsongbpm",
    "artist": "Fresno",
    "title": "Absolutamente Nada"
  },
  ...
}
```

---

## Troubleshooting

**`No active device`** — The Web API can only control a device Spotify already
knows is awake. Open Spotify somewhere (phone, desktop app, web player), then:

```bash
spoti devices            # see what's available
spoti transfer "<name>"  # wake/target a device
```

**Browser didn't open / redirect failed** — Make sure the redirect URI in the
Developer Dashboard is exactly `http://127.0.0.1:8888/callback`. If port 8888 is
in use, close whatever is holding it and re-run `spoti login`.

**`INVALID_CLIENT` or auth errors** — The Client ID is wrong or the redirect URI
doesn't match. Re-copy the Client ID and re-run `spoti login --client-id <id>`.

**Want to start over** — `spoti logout` clears the cached tokens; log in again
to re-authorize.

**`playlist-export` returns empty / permission error** — You need the playlist
scopes. Run `spoti login` again (even if already logged in) to pick up
`playlist-read-private` and `playlist-read-collaborative`.

**Audio features return 403** — Spotify restricted the `/audio-features`
endpoint in November 2024 for apps not on extended quota. The export will
succeed but `features` will be `null`. Use `spoti enrich-bpm` to get BPM from
GetSongBPM instead.

**`enrich-bpm` shows `—` for most tracks** — The search may not be matching.
Try with `--force` to re-run and inspect the output — fuzzy matching prefers
tracks where both title and artist overlap. Unusual punctuation or featuring
credits (e.g. `"Song (feat. X)"`) can reduce match quality.

**UI shows "No exported playlists found"** — Run `spoti ui` from the directory
that contains your `.json` files, or pass `--dir ~/path/to/jsons`.
