---
name: screen
description: Runs a quick green-flag / red-flag screen over a list of leads (or the names in leads.md) to decide which deserve a full research run, without doing the full pipeline. Use when the user wants to triage, screen, or filter several tickers/ideas fast.
argument-hint: [tickers or blank to use leads.md]
---

# Screen

A fast triage, not a verdict. Sort leads into *worth a full `/research`* vs. *skip*. Reference: [playbook/02-screen.md](../../../playbook/02-screen.md).

## Steps
1. **Get the list.** Use the tickers in `$ARGUMENTS` if given; otherwise read `leads.md`.
2. **For each name, a one-line screen** (no deep dives, no precise valuation):
   - **Green flags?** niche / repeat-purchase / boring-or-ignored / low institutional ownership / insider buying / buybacks / spinoff / tech-user.
   - **Red flags?** hottest-in-hottest-industry / "the next [winner]" / whisper-stock (no earnings) / diworseification / single-customer / heavy insider selling.
   - **Excitement check:** does the appeal rest on thrill? (yellow flag)
3. **Rough category guess** (one word) and a **lean**: `research` (promising) · `maybe` (mixed) · `skip` (dominant red flags).
4. **Output a table** — Ticker | quick category | green | red | lean — and update the **Status** column in `leads.md` (`lead → researching/passed`). Recommend which 1–3 names to take to a full `/research`.

Keep it fast and honest: the goal is to spend real effort only on the names that survive the screen. A boring lead surviving is a good sign; an exciting lead is one to be skeptical of.
