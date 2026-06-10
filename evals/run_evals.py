#!/usr/bin/env python3
"""run_evals.py - the automated runner + grader for evals/cases (the agent's val set).

Each case is a fictional company with `given_facts` (the manual-paste data path,
no network) and a frozen, HUMAN-WRITTEN `expected_behavior` checklist. This
harness runs the /research method on each case in a headless Claude Code session,
then grades the result in two layers:

  Layer A - code graders (deterministic, free): the note's frontmatter category
    matches `category_truth`; the verdict is in `grade.verdict_allowed`; every
    metric the note cites matches compute_valuation.compute() re-run on the
    case's given_facts (the anti-hallucination seam); a bear-case section
    exists; check_research_markdown.py's structural gate passes.
  Layer B - LLM judge (default model: opus, NOT the coder's model): each
    expected_behavior item is judged pass/fail against the produced note +
    final response. Items stay human-written and frozen - the same
    anti-Goodhart rule as .claude/review-fixtures/.

Reliability is reported as pass^k - a case passes only if ALL k trials pass
(consistency, not best-of). k=3 by default per the dev-time guidance in the
agent-eval literature; raise it before trusting the agent more.

Cost: every trial is a full /research pipeline in `claude -p` (headless usage
draws from the Agent SDK credit on subscription plans). Routine use:
    python3 evals/run_evals.py --smoke          # trap cases only, k=1, judged
    python3 evals/run_evals.py --smoke --no-judge   # code graders only (free-ish)
Full validation:
    python3 evals/run_evals.py                  # all cases, k=3
    python3 evals/run_evals.py --cases 03,06 --k 1
Re-grade an existing run directory without re-running the agent:
    python3 evals/run_evals.py --grade-only evals/runs/<timestamp>

Isolation: eval notes are written ONLY under evals/runs/<timestamp>/ - never
research/, watchlist.md, leads.md or portfolio.md. Scores append to
evals/scores.tsv (append-only ledger, like the review loop's fixture-scores.tsv).

Stdlib only. Override the headless command via EVAL_CLAUDE_BIN / EVAL_CLAUDE_ARGS.
"""
import argparse
import datetime
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_DIR = os.path.join(ROOT, "evals", "cases")
RUNS_DIR = os.path.join(ROOT, "evals", "runs")
SCORES_TSV = os.path.join(ROOT, "evals", "scores.tsv")
SCRIPTS = os.path.join(ROOT, ".claude", "skills", "research", "scripts")
sys.path.insert(0, SCRIPTS)
from compute_valuation import compute   # noqa: E402 - the same seam /research uses

JUDGE_MODEL = "opus"          # judge != coder model (self-preference mitigation)
TRIAL_TIMEOUT_S = 1800
# Conservative default tool surface for the headless runner: file I/O plus
# python3 only (the deterministic scripts). Widen via EVAL_CLAUDE_ARGS if needed.
DEFAULT_CLAUDE_ARGS = ("--permission-mode acceptEdits --max-turns 80 "
                       "--allowedTools Read,Glob,Grep,Write,Edit,TodoWrite,Task,Skill,"
                       "Bash(python3:*)")

CANON_VERDICTS = ("Buy candidate", "Watchlist", "Pass/Avoid")


# --------------------------------------------------------------------------- #
# Case loading / selection
# --------------------------------------------------------------------------- #
def load_cases(only=None, smoke=False):
    cases = []
    for path in sorted(glob.glob(os.path.join(CASES_DIR, "*.json"))):
        with open(path) as fh:
            case = json.load(fh)
        case["_file"] = os.path.basename(path)
        cases.append(case)
    if only:
        keys = [k.strip() for k in only.split(",") if k.strip()]
        cases = [c for c in cases
                 if any(c["_file"].startswith(k) or k in c.get("name", "") for k in keys)]
    if smoke:
        cases = [c for c in cases if c.get("trap")]
    return cases


# --------------------------------------------------------------------------- #
# Headless runner
# --------------------------------------------------------------------------- #
def runner_prompt(case, outdir):
    facts = json.dumps(case["given_facts"], indent=2)
    ticker = case["given_facts"].get("ticker", "EVAL")
    if "recheck" in case.get("skills", []):
        return f"""EVAL RUN - fictional company, offline. The user already HOLDS this name; \
run the monitoring/recheck flow (.claude/skills/recheck/SKILL.md, playbook/06-monitor-and-sell.md): \
re-test the original story, re-run the numbers with \
python3 .claude/skills/research/scripts/compute_valuation.py (never mental math), and decide \
Hold / Add / Sell by the category's rules.

Rules for this eval run:
- Use ONLY the given_facts below (treat them as user-pasted; the company is fictional - \
no network, no fetch_edgar.py).
- If you write any files, write them ONLY under {outdir}/ - do NOT touch research/, \
watchlist.md, leads.md, or portfolio.md.
- Reply to the user with your recommendation as you normally would.

The original research note (summary): {case.get("prior_note_summary", "(none)")}

User request: {case["query"]}

given_facts (user-pasted):
{facts}
"""
    return f"""EVAL RUN - fictional company, offline. Run the full Lynch research method \
(.claude/skills/research/SKILL.md, the playbook/ pipeline) on the case below.

Rules for this eval run:
- Use ONLY the given_facts below as the data source. Treat them as figures the user \
pasted (the manual-data path in playbook/03-numbers.md). Do NOT fetch from the \
network and do NOT run fetch_edgar.py - the company is fictional.
- Still compute every metric with python3 .claude/skills/research/scripts/compute_valuation.py \
and validate the data file with validate_data.py. Never do the math yourself.
- Write the research note to {outdir}/{ticker}.md (template: templates/research-note.md) \
and the provenance record to {outdir}/{ticker}.data.json.
- Do NOT create or modify anything in research/, watchlist.md, leads.md, or \
portfolio.md - this is an eval, not a real research run.
- If the request is out of scope for the method, say so in your reply exactly as you \
would to the user (a note file is not required in that case).

User request: {case["query"]}

given_facts (user-pasted):
{facts}
"""


def claude_cmd():
    bin_ = os.environ.get("EVAL_CLAUDE_BIN", "claude")
    args = os.environ.get("EVAL_CLAUDE_ARGS", DEFAULT_CLAUDE_ARGS).split()
    return [bin_, "-p", "--output-format", "json"] + args


def run_trial(case, outdir):
    """One headless /research run. The prompt goes via STDIN (a positional
    prompt can be swallowed by variadic flags like --allowedTools). Returns
    (response_text, meta); response_text is None on a runner failure, which
    the caller must count as a FAILED trial - an agent that didn't run is not
    an agent that passed."""
    os.makedirs(outdir, exist_ok=True)
    prompt = runner_prompt(case, outdir)
    try:
        proc = subprocess.run(claude_cmd(), input=prompt, cwd=ROOT,
                              capture_output=True, text=True, timeout=TRIAL_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return None, {"error": f"trial timed out after {TRIAL_TIMEOUT_S}s"}
    with open(os.path.join(outdir, "runner-output.json"), "w") as fh:
        fh.write(proc.stdout or "")
    try:
        meta = json.loads(proc.stdout)
        text = meta.get("result", "")
    except ValueError:
        meta = {"error": f"empty/non-JSON runner output (exit {proc.returncode})",
                "stderr_head": (proc.stderr or "")[:500]}
        text = None
    if isinstance(meta, dict) and meta.get("is_error"):
        meta = {"error": f"runner reported is_error: {str(meta.get('result'))[:300]}"}
        text = None
    with open(os.path.join(outdir, "runner-meta.json"), "w") as fh:
        json.dump(meta if isinstance(meta, dict) else {"raw": str(meta)[:1000]}, fh, indent=2)
    with open(os.path.join(outdir, "response.md"), "w") as fh:
        fh.write(text or "")
    return text, meta


# --------------------------------------------------------------------------- #
# Layer A - code graders (deterministic)
# --------------------------------------------------------------------------- #
def parse_frontmatter(note_text):
    m = re.match(r"\s*---\n(.*?)\n---", note_text, re.DOTALL)
    fm = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fm[k.strip().lower()] = v.strip()
    return fm


def canon_verdict(raw):
    v = (raw or "").lower()
    if "buy" in v:
        return "Buy candidate"
    if "watch" in v:
        return "Watchlist"
    if "pass" in v or "avoid" in v:
        return "Pass/Avoid"
    return raw or ""


def num_in_text(text, x):
    """Anchored 'does this computed number appear in the text' check.

    A number counts as shown only if some whole numeric token in the text
    equals x at that token's own displayed precision — '6' and '6.00' match
    6.0, but '6.4' (hand-computed drift), '16.0' and '112.5' (substring
    collisions) never do."""
    if x is None:
        return True
    for tok in re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", text):
        tok = tok.replace(",", "")
        decimals = len(tok.partition(".")[2])
        if abs(float(tok) - float(x)) <= 0.5 * 10 ** -decimals + 1e-9:
            return True
    return False


def table_value(note, label):
    """Value cell of the first metrics-table row whose metric cell contains label."""
    for line in note.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and label.lower() in cells[0].replace("*", "").lower():
            return cells[1]
    return None


def metric_matches(cell, x):
    """The anti-hallucination contract for a shown metric: the row must exist,
    and any number it shows must match the script's. An honest 'n/a' (e.g. PEG
    declined for a cyclical) passes; a different number never does."""
    if cell is None:
        return False                                  # row missing from the table
    if x is None or re.search(r"n/?a|—", cell, re.IGNORECASE):
        return True
    return num_in_text(cell, x)


def find_note(outdir, ticker):
    for path in sorted(glob.glob(os.path.join(outdir, "*.md"))):
        if os.path.basename(path) != "response.md":
            return path
    return None


def code_grade(case, outdir, response_text):
    """Deterministic checks. Returns a list of {check, pass, detail}."""
    checks = []
    grade = case.get("grade", {})
    require_note = grade.get("require_full_note", True)
    ticker = case["given_facts"].get("ticker", "")
    note_path = find_note(outdir, ticker)

    if not require_note:
        # Conversational/recheck cases: the output isn't a template research note
        # (it may be a reply, or a free-form update with e.g. a then-vs-now
        # comparison table), so the structural code graders don't apply — the
        # frozen expected_behavior items, judged in Layer B, carry these cases.
        return [{"check": "no-template-note-required", "pass": True,
                 "detail": "judge-graded case (require_full_note: false)"}]
    if note_path is None:
        return [{"check": "note-written", "pass": False,
                 "detail": f"no note found in {outdir}"}]
    note = open(note_path).read()
    fm = parse_frontmatter(note)

    truth = case.get("category_truth", "")
    if truth and not truth.startswith("n/a"):
        # BOTH sides may carry a parenthetical qualifier ("Avoid (whisper stock)" /
        # "Avoid (hype over fundamentals)"); the category judgment is the head token.
        truth_main = truth.split("(")[0].strip()
        got = fm.get("category", "")
        got_main = got.split("(")[0].strip()
        checks.append({"check": "category", "pass": got_main.lower() == truth_main.lower(),
                       "detail": f"note={got!r} truth={truth!r}"})

    allowed = grade.get("verdict_allowed")
    if allowed:
        got = canon_verdict(fm.get("verdict", ""))
        checks.append({"check": "verdict", "pass": got in allowed,
                       "detail": f"note={got!r} allowed={allowed}"})

    facts = case["given_facts"]
    if isinstance(facts.get("price"), (int, float)) and \
            isinstance(facts.get("eps_ttm"), (int, float)) and facts["eps_ttm"] > 0:
        m = compute(dict(facts), case.get("category_truth"))
        for key, label in (("pe", "P/E"), ("peg", "PEG")):
            cell = table_value(note, label)
            checks.append({"check": f"metric:{key}",
                           "pass": metric_matches(cell, m.get(key)),
                           "detail": f"table {label}={cell!r} vs computed {m.get(key)} "
                                     "(shown numbers must match the script; n/a is honest)"})

    checks.append({"check": "bear-case", "pass": bool(re.search(r"(?im)^#+.*bear case", note)),
                   "detail": "a '## Bear case' section must exist"})

    chk = subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_research_markdown.py"),
                          note_path], capture_output=True, text=True)
    checks.append({"check": "sources-structural", "pass": chk.returncode == 0,
                   "detail": (chk.stdout or "").strip()[-300:]})
    return checks


# --------------------------------------------------------------------------- #
# Layer B - LLM judge (opus by default, never silently skipped)
# --------------------------------------------------------------------------- #
def judge_prompt(case, note_text, response_text):
    items = "\n".join(f"{i}. {b}" for i, b in enumerate(case["expected_behavior"]))
    return f"""You are an independent, skeptical grader for a Peter Lynch research-agent \
eval. Judge EACH expected-behavior item below against the agent's output. Default to \
fail when the evidence is missing or ambiguous - this is a calibration gate, not a \
cheering section. Do not reward confident prose; reward the specific behavior.

Expected behavior (frozen, human-written):
{items}

=== Agent's research note (may be empty for conversational cases) ===
{note_text or "(no note was written)"}

=== Agent's final reply to the user ===
{response_text}

Output ONLY this JSON, nothing else:
{{"items": [{{"i": 0, "pass": true, "evidence": "<=20 words citing the note/reply"}}, ...]}}"""


def extract_json(text):
    text = re.sub(r"^```(json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in judge output")
    return json.loads(text[start:])


def judge_grade(case, note_text, response_text, model, outdir):
    # The judge prompt is fully self-contained, so run it from a temp cwd OUTSIDE
    # the repo: inside it, the project's Stop hook can hijack the session into a
    # /review-local flow and the judge's "result" becomes a review report instead
    # of the JSON verdict (observed: 21 turns, $2, no JSON). --max-turns stays
    # tight for the same reason - grading is single-shot.
    cmd = [os.environ.get("EVAL_CLAUDE_BIN", "claude"), "-p", "--output-format", "json",
           "--model", model, "--max-turns", "4"]
    proc = subprocess.run(cmd, input=judge_prompt(case, note_text, response_text),
                          cwd=tempfile.gettempdir(), capture_output=True, text=True,
                          timeout=600)
    with open(os.path.join(outdir, "judge-raw.json"), "w") as fh:   # transcript review
        fh.write(proc.stdout or "")
    raw = json.loads(proc.stdout).get("result", "")
    verdicts = extract_json(raw).get("items", [])
    out = []
    for i, behavior in enumerate(case["expected_behavior"]):
        v = next((x for x in verdicts if x.get("i") == i), None)
        out.append({"check": f"judge:{i}", "pass": bool(v and v.get("pass")),
                    "detail": (v or {}).get("evidence", "judge returned no verdict for this item")})
    return out


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def grade_trial(case, outdir, response_text, judge_model, no_judge):
    checks = code_grade(case, outdir, response_text)
    note_path = find_note(outdir, case["given_facts"].get("ticker", ""))
    note_text = open(note_path).read() if note_path else ""
    if not no_judge:
        try:
            checks += judge_grade(case, note_text, response_text, judge_model, outdir)
        except Exception as e:   # a judge failure must FAIL the trial, never pass it
            checks.append({"check": "judge:error", "pass": False, "detail": str(e)[:300]})
    with open(os.path.join(outdir, "grade.json"), "w") as fh:
        json.dump(checks, fh, indent=2)
    return checks


def append_score(mode, k, results, run_dir, note=""):
    header = "date\tmode\tk\tcases\tpassed\tscore\tper_case\trun_dir\tnote\n"
    new = not os.path.exists(SCORES_TSV)
    passed = sum(1 for r in results.values() if r["pass"])
    per_case = ",".join(f"{name}:{r['trials_passed']}/{r['trials']}"
                        for name, r in sorted(results.items()))
    score = f"{passed}/{len(results)}"
    with open(SCORES_TSV, "a") as fh:
        if new:
            fh.write(header)
        fh.write("\t".join([datetime.date.today().isoformat(), mode, str(k),
                            str(len(results)), str(passed), score, per_case,
                            os.path.relpath(run_dir, ROOT), note]) + "\n")
    return score


def main():
    ap = argparse.ArgumentParser(description="Run + grade the research evals (pass^k).")
    ap.add_argument("--k", type=int, default=3, help="trials per case; pass^k (default 3)")
    ap.add_argument("--cases", help="comma-separated case prefixes/names (e.g. 03,06)")
    ap.add_argument("--smoke", action="store_true", help="trap cases only, k=1")
    ap.add_argument("--no-judge", action="store_true", help="code graders only (no LLM judge)")
    ap.add_argument("--judge-model", default=JUDGE_MODEL)
    ap.add_argument("--grade-only", metavar="RUN_DIR",
                    help="re-grade an existing evals/runs/<ts> dir; no agent runs")
    ap.add_argument("--note", default="", help="free-text note for the scores.tsv row")
    args = ap.parse_args()
    k = 1 if args.smoke else args.k
    mode = "smoke" if args.smoke else ("grade-only" if args.grade_only else "full")

    cases = load_cases(args.cases, args.smoke)
    if not cases:
        print("no cases selected", file=sys.stderr)
        return 2

    run_dir = args.grade_only or os.path.join(
        RUNS_DIR, datetime.datetime.now().strftime("%Y-%m-%dT%H-%M-%S"))
    results = {}
    for case in cases:
        name = case["_file"].split(".")[0]
        trials_passed = 0
        n_trials = 0
        for t in range(1, k + 1):
            outdir = os.path.join(run_dir, f"{name}-t{t}")
            if args.grade_only:
                if not os.path.isdir(outdir):
                    continue
                response = open(os.path.join(outdir, "response.md")).read() \
                    if os.path.exists(os.path.join(outdir, "response.md")) else ""
            else:
                print(f"== {name} trial {t}/{k} (headless /research) ==", flush=True)
                response, meta = run_trial(case, outdir)
                if response is None:
                    print(f"   runner error: {meta.get('error')}", file=sys.stderr)
                    n_trials += 1
                    continue
            n_trials += 1
            checks = grade_trial(case, outdir, response, args.judge_model, args.no_judge)
            ok = all(c["pass"] for c in checks)
            trials_passed += ok
            for c in checks:
                if not c["pass"]:
                    print(f"   FAIL {c['check']}: {c['detail']}")
            print(f"   trial {t}: {'PASS' if ok else 'FAIL'}")
        results[name] = {"trials": n_trials, "trials_passed": trials_passed,
                         "pass": n_trials > 0 and trials_passed == n_trials}

    score = append_score(mode, k, results, run_dir, args.note)
    print(f"\npass^{k} score: {score}  (ledger: evals/scores.tsv; artifacts: {run_dir})")
    return 0 if all(r["pass"] for r in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
