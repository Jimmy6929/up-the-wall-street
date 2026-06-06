#!/usr/bin/env bash
# Canonical working-tree change signature for the self-review loop.
#
# Both the Stop hook and the /review coordinator call THIS script so they
# compute the same diff_sha — otherwise the "already passed this exact diff"
# cache would desync and the loop could re-review needlessly.
#
# Covers tracked changes (git diff HEAD) AND untracked, non-ignored files
# (path + blob hash, so their content counts). Prints a sha256 hex string.
#
# Usage: review-sha.sh [REPO_ROOT]
set -uo pipefail

ROOT="${1:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -n "$ROOT" ] || { printf ''; exit 0; }

{
  git -C "$ROOT" diff HEAD 2>/dev/null
  git -C "$ROOT" ls-files --others --exclude-standard -z 2>/dev/null \
    | while IFS= read -r -d '' f; do
        # Never let the loop's own state dir affect the signature — otherwise
        # writing last-review.json would invalidate the PASS-cache it sets.
        case "$f" in
          .claude/review-local/*) continue ;;
        esac
        printf 'U %s %s\n' "$f" "$(git -C "$ROOT" hash-object -- "$ROOT/$f" 2>/dev/null)"
      done
} | shasum -a 256 | awk '{print $1}'
