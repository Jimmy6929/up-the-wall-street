#!/usr/bin/env bash
# PROJECT-LOCAL Stop hook — forked copy of the global self-review loop.
#
# Wired in THIS project's .claude/settings.json. It is isolated from the
# global loop: it keys on .claude/review-local.json (not review.json), so the
# global hook (which keys on review.json, absent here) stays silent and the two
# never double-fire. Does nothing unless review-local.json has "enabled": true.
# When enabled and there are uncommitted changes under codePaths that have not
# passed /review-local, it blocks the stop and directs Claude to run it.
#
# Decision rules (first match wins → allow):
#   0. stop_hook_active is true                  -> allow (never loop the loop)
#   1. cwd is not inside a git repo               -> allow
#   2. no .claude/review-local.json, or disabled  -> allow (opt-in)
#   3. no changed file matches codePaths          -> allow (nothing reviewable)
#   4. [skip-review] in last user message         -> allow (manual bypass)
#   5. last-review PASS for THIS diff_sha         -> allow (already passed)
#   6. attempts >= maxAttempts                    -> allow (already escalated)
#   otherwise                                      -> block + inject "run /review-local"
#
# Output contract: empty + exit 0 = allow. {"decision":"block","reason":...} = block.

set -uo pipefail

INPUT="$(cat 2>/dev/null || echo '{}')"

# Pass the event via env, NOT stdin: `python3 -` reads the SCRIPT from stdin
# (the heredoc), so stdin is unavailable for the event payload.
REVIEW_HOOK_EVENT="$INPUT" python3 - <<'PY'
import json, sys, os, subprocess, fnmatch

def allow():
    sys.exit(0)

def block(reason):
    sys.stdout.write(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)

try:
    event = json.loads(os.environ.get("REVIEW_HOOK_EVENT", "{}") or "{}")
except Exception:
    allow()

# Rule 0 — never recurse into our own block.
if event.get("stop_hook_active"):
    allow()

cwd = event.get("cwd") or os.getcwd()

def git(*args):
    return subprocess.run(["git", "-C", cwd, *args],
                          capture_output=True, text=True).stdout

# Rule 1 — must be inside a git repo.
root = git("rev-parse", "--show-toplevel").strip()
if not root:
    allow()

# Rule 2 — opt-in: config must exist and be enabled.
config_path = os.path.join(root, ".claude", "review-local.json")
if not os.path.isfile(config_path):
    allow()
try:
    cfg = json.load(open(config_path))
except Exception:
    allow()  # malformed config: fail open, never trap the user
if not cfg.get("enabled", False):
    allow()

code_paths = cfg.get("codePaths") or ["**/*"]
try:
    max_attempts = int(cfg.get("maxAttempts", 2))
except (TypeError, ValueError):
    max_attempts = 2

# Rule 3 — at least one changed file must match codePaths.
# -uall lists untracked files individually (without it, git collapses a
# wholly-untracked directory to "?? dir/", which globs like "src/**" miss).
status = subprocess.run(["git", "-C", root, "status", "--porcelain", "-uall"],
                        capture_output=True, text=True).stdout
changed = []
for line in status.splitlines():
    if not line.strip():
        continue
    path = line[3:]
    if " -> " in path:          # rename: "old -> new"
        path = path.split(" -> ", 1)[1]
    changed.append(path.strip().strip('"'))

def matches(f):
    # fnmatch's * spans '/', so "src/**" and "src/*" both match nested paths.
    return any(fnmatch.fnmatch(f, p) for p in code_paths)

if not any(matches(f) for f in changed):
    allow()

# Rule 4 — [skip-review] sentinel in the most recent user message.
tp = event.get("transcript_path")
if tp and os.path.isfile(tp):
    try:
        with open(tp) as fh:
            tail = fh.readlines()[-400:]
        for ln in reversed(tail):
            if '"role":"user"' in ln or '"role": "user"' in ln:
                if "[skip-review]" in ln:
                    allow()
                break
    except Exception:
        pass

# Rule 5 — a prior PASS that still covers this exact diff.
# Use the project-local signature helper so the hook and /review-local agree
# byte-for-byte (it excludes .claude/review-local/ from the signature).
sha_script = os.path.join(root, ".claude", "hooks", "review-sha.sh")
diff_sha = subprocess.run(["bash", sha_script, root],
                          capture_output=True, text=True).stdout.strip()

state_dir = os.path.join(root, ".claude", "review-local")
last_review = os.path.join(state_dir, "last-review.json")
if os.path.isfile(last_review):
    try:
        lr = json.load(open(last_review))
        if lr.get("verdict") == "PASS" and lr.get("diff_sha") == diff_sha:
            allow()
    except Exception:
        pass

# Rule 6 — already escalated; do not loop forever.
attempts_file = os.path.join(state_dir, "attempts.json")
if os.path.isfile(attempts_file):
    try:
        at = json.load(open(attempts_file))
        if int(at.get("attempts", 0)) >= max_attempts:
            allow()
    except Exception:
        pass

# Otherwise — block and direct Claude to run /review-local.
reason = (
    "REVIEW REQUIRED before finishing.\n\n"
    "You have uncommitted code changes (under this project's codePaths) that "
    "have not passed the project-local self-review loop. Before you end the turn:\n\n"
    "1. Run the /review-local slash command now. It runs 3 adversarial reviewers "
    "(Project Goal, Task Goal, Senior Engineer) plus this project's hard "
    "signals (lint / tests / type-check), aggregates the verdict, and writes "
    ".claude/review-local/last-review.json.\n"
    "2. If /review-local returns PASS, you may finish.\n"
    "3. If /review-local returns FAIL, address every item under 'Required changes' "
    "and re-run /review-local. After {n} consecutive FAILs it escalates to the user "
    "automatically.\n"
    "4. To bypass this loop for trivial work (typos, docs, config), include "
    "[skip-review] in the user's message.\n\n"
    "Do not finish the turn without doing this."
).replace("{n}", str(max_attempts))

block(reason)
PY
