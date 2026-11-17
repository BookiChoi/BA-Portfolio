Author: human

# 05 Pilot hand check (2026-11-12)

Rule fixed before checking: proceed if at least 27 of 30 matches are the same work. "Unsure" counts as wrong.
Checked: outputs/q1/pilot_table.csv, all 30 rows.

## How the check was done
- Claude (chat) reviewed all 30 rows, using web search for rows 8, 10, 14 and 21. Result: 30 correct, 0 wrong, 0 unsure. This check is not independent of the matching agent (same model family), and the IMDb pages themselves were not opened for rows other than those searched.
- I did not open IMDb pages myself. I accept the AI check as the pilot gate, knowing it is weaker evidence than a hand check.

## Result
- Correct: 30 / 30 (AI check only)
- Wrong: 0 (rows: none)
- Unsure, counted as wrong: 0

## Genre group (not part of the gate)
- The priority table gives coarse groups for some titles: rows 2 (Kids & Family from the Family tag), 3 (Sci-Fi & Fantasy from Fantasy), 11 and 26 (Action & Adventure from Action and Sport). The mapping stays frozen. The share of such cases in the full labelled set is checked in step 05.
- Candidate count was 1 for all 30 rows, so the tie-break rule was not tested.

## Decision
Decision: proceed to full labelling as planned. Match accuracy in the full labelled set rests on the AI check; this is listed as a limitation of the results.