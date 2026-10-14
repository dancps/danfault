"""ccanalyze — analyze a Claude Code conversation to see what made its context long.

Give it a session id (full or partial/prefix). The script finds the matching
transcript under ~/.claude/projects/*/<id>.jsonl (org/project agnostic) and reports:

  - peak real context-window usage (tokens actually sent to the model)
  - file size on disk vs. `toolUseResult` bloat (stored-only, not re-sent)
  - event-type breakdown
  - biggest single tool results (what filled the context), joined to tool name
  - cumulative bytes by tool

Pure stdlib. No external dependencies.

Usage:
    ccanalyze <session-id-or-prefix>
    ccanalyze <id> --top 25
    ccanalyze <id> --projects-dir /some/other/.claude/projects
    ccanalyze --list                 # list recent sessions across all projects
"""
import argparse
import glob
import json
import os
import sys


def eprint(*a, **k):
    print(*a, file=sys.stderr, **k)


def default_projects_dir():
    return os.path.expanduser(os.environ.get("CLAUDE_PROJECTS_DIR",
                                             "~/.claude/projects"))


def find_transcript(session_id, projects_dir):
    """Locate <id>.jsonl anywhere under projects_dir. Supports prefix match."""
    exact = glob.glob(os.path.join(projects_dir, "*", session_id + ".jsonl"))
    if exact:
        return exact
    # prefix / substring fallback
    hits = [p for p in glob.glob(os.path.join(projects_dir, "*", "*.jsonl"))
            if session_id in os.path.basename(p)]
    return hits


def resolve_id(needle, projects_dir):
    """Map any id to the session file that contains it.

    `needle` may be a session id (= filename), a message `uuid`, or a
    `leafUuid` / resume pointer. Returns list of (session_id, project, path,
    how) where `how` explains the match.
    """
    hits = []
    for path in glob.glob(os.path.join(projects_dir, "*", "*.jsonl")):
        sid = os.path.basename(path)[:-6]
        proj = os.path.basename(os.path.dirname(path))
        if needle in sid:
            hits.append((sid, proj, path, "filename/sessionId"))
            continue
        # scan contents for uuid / leafUuid matches
        how = None
        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if needle not in line:
                        continue
                    try:
                        o = json.loads(line)
                    except Exception:
                        continue
                    if o.get("uuid") == needle:
                        how = "message uuid (resume leaf)"
                        break
                    if o.get("leafUuid") == needle:
                        how = "leafUuid (resume checkpoint)"
                        break
                    if o.get("parentUuid") == needle:
                        how = "parentUuid (this session was forked FROM it)"
                        break
        except Exception:
            continue
        if how:
            hits.append((sid, proj, path, how))
    return hits


def list_sessions(projects_dir, limit=30):
    files = glob.glob(os.path.join(projects_dir, "*", "*.jsonl"))
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    rows = []
    for p in files[:limit]:
        sid = os.path.basename(p)[:-6]
        proj = os.path.basename(os.path.dirname(p))
        size = os.path.getsize(p)
        rows.append((size, sid, proj))
    return rows


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def load(path):
    events = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            raw = line.rstrip("\n")
            b = len(raw.encode("utf-8"))
            try:
                obj = json.loads(raw)
            except Exception:
                events.append({"line": i, "bytes": b, "obj": None})
                continue
            events.append({"line": i, "bytes": b, "obj": obj})
    return events


def analyze(events, top):
    from collections import Counter

    type_counts = Counter()
    type_bytes = Counter()
    tooluse_bloat = 0
    tooluse_n = 0
    peak = 0
    peak_line = 0
    last_usage = None

    tool_names = {}          # tool_use_id -> name
    result_sizes = []        # (bytes, line, tool_use_id)
    tool_agg = Counter()     # name -> bytes
    tool_cnt = Counter()     # name -> count

    for ev in events:
        o = ev["obj"]
        type_bytes[o.get("type", "?") if o else "<parse_error>"] += ev["bytes"]
        if not o:
            type_counts["<parse_error>"] += 1
            continue
        type_counts[o.get("type", "<none>")] += 1

        if "toolUseResult" in o:
            tooluse_bloat += len(json.dumps(o["toolUseResult"]))
            tooluse_n += 1

        msg = o.get("message")
        if isinstance(msg, dict):
            usage = msg.get("usage")
            if isinstance(usage, dict):
                ctx = (usage.get("input_tokens", 0)
                       + usage.get("cache_read_input_tokens", 0)
                       + usage.get("cache_creation_input_tokens", 0))
                if ctx > peak:
                    peak, peak_line = ctx, ev["line"]
                last_usage = (ev["line"], usage)

            content = msg.get("content")
            if isinstance(content, list):
                for p in content:
                    if not isinstance(p, dict):
                        continue
                    if p.get("type") == "tool_use":
                        tool_names[p.get("id")] = p.get("name")

    # second pass: tool_result sizes now that names are known
    for ev in events:
        o = ev["obj"]
        if not o:
            continue
        msg = o.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for p in content:
            if isinstance(p, dict) and p.get("type") == "tool_result":
                tid = p.get("tool_use_id")
                sz = len(json.dumps(p.get("content")))
                result_sizes.append((sz, ev["line"], tid))
                nm = tool_names.get(tid, "?")
                tool_agg[nm] += sz
                tool_cnt[nm] += 1

    result_sizes.sort(reverse=True)

    return {
        "type_counts": type_counts,
        "type_bytes": type_bytes,
        "tooluse_bloat": tooluse_bloat,
        "tooluse_n": tooluse_n,
        "peak": peak,
        "peak_line": peak_line,
        "last_usage": last_usage,
        "result_sizes": result_sizes[:top],
        "tool_agg": tool_agg,
        "tool_cnt": tool_cnt,
        "tool_names": tool_names,
    }


def report(path, events, a):
    total_bytes = sum(e["bytes"] for e in events)
    print("=" * 60)
    print(f"transcript: {path}")
    print(f"events: {len(events)}   disk size: {human(total_bytes)}")
    print("=" * 60)

    print("\n## Real context-window usage (tokens sent to the model)")
    print(f"  PEAK: {a['peak']:,} tokens  (line {a['peak_line']})")
    if a["last_usage"]:
        ln, u = a["last_usage"]
        print(f"  last turn (line {ln}): "
              f"input={u.get('input_tokens',0):,}  "
              f"cache_read={u.get('cache_read_input_tokens',0):,}  "
              f"cache_creation={u.get('cache_creation_input_tokens',0):,}  "
              f"output={u.get('output_tokens',0):,}")

    print("\n## File bloat (NOT re-sent to the model)")
    print(f"  toolUseResult: {human(a['tooluse_bloat'])} "
          f"across {a['tooluse_n']} results "
          f"({100*a['tooluse_bloat']/max(total_bytes,1):.0f}% of disk file)")

    print("\n## Events by type")
    for k, v in a["type_counts"].most_common():
        print(f"  {v:5d}  {k:22s}  {human(a['type_bytes'][k])}")

    print("\n## Cumulative tool-result bytes by tool (context filler)")
    for k, v in a["tool_agg"].most_common():
        print(f"  {human(v):>9}  {k}  (x{a['tool_cnt'][k]})")

    print("\n## Biggest single tool results (what inflated context)")
    print("  BYTES   LINE   TOOL")
    for sz, ln, tid in a["result_sizes"]:
        print(f"  {sz:7d}  {ln:5d}  {a['tool_names'].get(tid, '?')}")

    # one-line verdict
    if a["tool_agg"]:
        top_tool, top_val = a["tool_agg"].most_common(1)[0]
        share = 100 * top_val / max(sum(a["tool_agg"].values()), 1)
        print(f"\n>>> Biggest driver: '{top_tool}' "
              f"({share:.0f}% of all tool output). "
              f"Scope reads/commands (line ranges, head, filters) to shrink context.")


def main():
    ap = argparse.ArgumentParser(
        description="Analyze what made a Claude Code conversation's context long.")
    ap.add_argument("session_id", nargs="?",
                    help="session id (full or prefix/substring)")
    ap.add_argument("--top", type=int, default=15,
                    help="how many of the biggest tool results to list (default 15)")
    ap.add_argument("--projects-dir", default=default_projects_dir(),
                    help="override the Claude projects dir "
                         "(or set CLAUDE_PROJECTS_DIR)")
    ap.add_argument("--list", action="store_true",
                    help="list recent sessions across all projects and exit")
    ap.add_argument("--resolve", metavar="ID",
                    help="map any id (sessionId, message uuid, or leafUuid) "
                         "to the conversation file that contains it")
    ap.add_argument("--json", action="store_true",
                    help="emit machine-readable JSON instead of a text report")
    args = ap.parse_args()

    projects_dir = os.path.expanduser(args.projects_dir)
    if not os.path.isdir(projects_dir):
        eprint(f"[x] projects dir not found: {projects_dir}")
        sys.exit(2)

    if args.list:
        for size, sid, proj in list_sessions(projects_dir):
            print(f"  {human(size):>8}  {sid}  [{proj}]")
        return

    if args.resolve:
        hits = resolve_id(args.resolve, projects_dir)
        if not hits:
            eprint(f"[x] '{args.resolve}' not found in any session under {projects_dir}")
            sys.exit(1)
        for sid, proj, path, how in hits:
            print(f"  session {sid}  [{proj}]")
            print(f"    matched by: {how}")
            print(f"    file: {path}")
        return

    if not args.session_id:
        ap.error("session_id is required (or use --list)")

    hits = find_transcript(args.session_id, projects_dir)
    if not hits:
        eprint(f"[x] no transcript matching '{args.session_id}' under {projects_dir}")
        eprint("    try: ccanalyze --list")
        sys.exit(1)
    if len(hits) > 1:
        eprint(f"[!] {len(hits)} matches for '{args.session_id}':")
        for h in hits:
            eprint(f"    {os.path.basename(h)[:-6]}  [{os.path.basename(os.path.dirname(h))}]")
        eprint("    pass a longer/exact id.")
        sys.exit(1)

    path = hits[0]
    events = load(path)
    a = analyze(events, args.top)

    if args.json:
        out = {
            "path": path,
            "events": len(events),
            "disk_bytes": sum(e["bytes"] for e in events),
            "peak_context_tokens": a["peak"],
            "tooluse_bloat_bytes": a["tooluse_bloat"],
            "type_counts": dict(a["type_counts"]),
            "tool_agg_bytes": dict(a["tool_agg"]),
            "tool_counts": dict(a["tool_cnt"]),
            "biggest_results": [
                {"bytes": sz, "line": ln,
                 "tool": a["tool_names"].get(tid, "?")}
                for sz, ln, tid in a["result_sizes"]
            ],
        }
        print(json.dumps(out, indent=2))
    else:
        report(path, events, a)


if __name__ == "__main__":
    main()
