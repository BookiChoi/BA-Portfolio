# Operating notes (update after each project)

## Status
- netflix-engagement: finished through step 09 (step 10 skipped), merged to main on 2026-11-13. Score the dated prediction when Netflix's annual report is out (Feb-Mar 2027).
- Next: Olist (Kaggle). Decision candidates: A delivery promise policy, B seller quality checks, C category/shipping policy, D repeat purchase.

## Lessons from the first run
- AI-written research can cite links that do not support the claim. Open at least 2-3 links myself; record the check in a human-authored review note (01_research_review.md).
- Do not edit AI-authored workflow files. Record corrections as human notes or as amendment blocks before the approval line.
- Stop conditions in the plan (scope cap, pilot hand check) worked as designed. Decide, amend the plan, then rerun.
- The guard hook blocks any command containing the approval phrase. Approval lines are typed by the human in an editor.
- If a stop report is saved as 05_analysis.md, rename it (05a_, 05b_) before rerunning, otherwise the state script thinks step 05 is complete.
- Fix rules before seeing results: decision rule, thresholds, mapping tables, scope.
- "Nothing found" is a valid result; state limits, do not claim "no effect".
- Usage per step (Netflix, session %): data profile +3, question coach +1, analysis (partial) +9. Check /usage before and after each step.
- Prefer company-published, recent data; check the terms before choosing. Raw data stays outside the repo.
- PRs merge with a merge commit, not squash.
EOF