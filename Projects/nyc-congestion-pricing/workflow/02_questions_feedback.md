Author: ai/question-coach

# 02 Questions: coach feedback

Inputs read: `00_brief.md`, `01_research.md`, `02_questions.md`. No data was opened, so every comment about data is a likelihood, not a finding. The questions are not rewritten here.

## Cross-cutting issues (apply to all questions)

1. **Project and questions do not match.** The project is named "congestion pricing" and the research stage is built around the Congestion Relief Zone fee. None of the four questions uses the fee, the zone, or a before/after view. The period note says no policy change falls inside the window, which is true, but it also means the project cannot say anything about congestion pricing. Either add a question that uses the fee field and zone flag, or accept that this is a general trip-demand project and rename it.
2. **Decision maker is shaky.** Yellow fleet operations managers exist. For Uber/Lyft, drivers are typically independent and the platform does not "put drivers" in zones in the same way. Check that the decision is one this person can actually take. If not, the decision link is only illustrative.
3. **Thresholds are set without a reason.** Top 5, 40%, 80%, 10%, 1.5x and 20% are all stated as fixed cut-offs. Some of them (80/20, 10%) look borrowed from convention. A decision rule that flips on an unexplained cut-off gives a precise answer to an unclear question. For each, state what happens just above and just below, and why that line matters.
4. **Trips are used as a proxy for demand and value.** Trip count ignores trip length, revenue, and driver time. Every "where to put drivers" decision depends on earnings per driver-hour, which these questions never touch.
5. **Scope wording conflicts.** The header says every question is answered separately for both services, but Q4 is Uber/Lyft only. Say so in the header. The brief's third view (combined) is demoted to context. That is fine, but state it as a decision.
6. **Fields are unverified.** `request_datetime` and other fields are not confirmed in the real files (01_research blocker 1). Q4 depends most on this.

## Q1 (Q1a pickup ranking, Q1b airport destinations)

**Structure.** Two questions, two hypotheses and two rules sit under one decision. Treat them as separate questions, or the decision link gets muddy.

**Ambiguity**
- "Airport zone": which zones count, and is Newark included? The list is deferred to 03, which is acceptable only if it is fixed before looking at results, as stated.
- "Most trips" is over the full 12 months. Rankings by hour or day-part may differ a lot, and an operations plan is by time of day.
- Q1b "where drivers are likely to end up" mixes two things: where passengers go, and where the driver is afterwards. Those are the same only if the driver stays at the dropoff.
- Treatment of unknown or outside-zone location IDs is not stated.

**Measurability.** Trip counts per zone are directly measurable. Driver position and driver intent are not. Q1b measures passenger destination only, so the "repositioning" wording over-claims.

**Hidden assumptions**
- Pickup count reflects demand worth serving. Airport pickups for yellow and for HVFHV follow different access rules (queues, holding areas), so a high airport count may not mean drivers can freely choose to go there.
- Zones are comparable units. They differ a lot in size, so ranking raw counts rewards large or dense zones.
- The top 5 test depends on how many zones exist and how they are cut, so 40% is not a stable benchmark.

**Sharper directions**
- Q1a: compare rank by day-part (for example night, morning peak, evening peak) for each service, not only the annual total. Ask whether the top set is stable across months.
- Q1b: compare the destination spread for each airport separately, since different airports likely send trips to different places. Consider borough-level and zone-level views side by side.
- Think about what the hypothesis could show that is not already obvious. Airports being in the top 5 is plausible but the answer changes little.

**Decision link.** Q1a rule ("standing airport plan if top 5") is weak: a plan decision should depend on volume relative to supply, not on rank. Q1b: concentration alone does not tell a manager where to reposition; it needs time of day and trip count per hour.

## Q2 (Pareto concentration)

**Ambiguity**
- "Top 20% of zones": 20% of zones with at least one trip. Zones with a handful of trips inflate the denominator, so the result depends on how many tiny zones exist.
- "Low-volume zones" in the decision is not defined, so "effort" is open.

**Measurability.** The share is easy to compute. "Worth effort" is not: it needs revenue or earnings per trip and cost of covering a zone. Proxy: average fare or trip distance by zone, and the number of trips per hour, so a zone is judged by whether a driver there can stay busy.

**Hidden assumptions**
- Trip share is the right measure of importance.
- Zone geography is neutral. Concentration partly reflects where zones are large or small, and, for yellow, where street hails are practical.
- The result is likely to pass the 80/20 test for both services (this is a prior, not a result). If so, the decision is nearly predetermined and the analysis adds little.

**Sharper directions**
- Report the full cumulative curve and a comparison between services (for example how many zones carry half the trips), rather than one pass/fail point.
- Move from trips to value (fare revenue) or to trips per hour in the zone.
- Check if concentration changes by time of day. Overall concentration can hide that the "busy" zones differ by hour.
- Q2 overlaps with Q1a (same data, same ranking). Make sure Q2 adds a distinct answer.

**Decision link.** The rule says to concentrate drivers on top zones if concentrated. That does not follow cleanly: concentrated demand can also mean top zones are already saturated with supply.

## Q3 (weekday vs weekend)

**Ambiguity**
- "Average daily trips": per calendar day or per day type, and how holidays and the uneven number of weekdays vs weekend days in 12 months are treated (deferred to 04).
- "Differ by more than 10%": in either direction, for overall, for the top 20 zones, or for each of them? The rule does not say how to decide if overall and zone results disagree.
- "Top 20 pickup zones": top by the full period, which is fine, but say so.

**Measurability.** Straightforward from pickup datetime. Missing: any estimate of normal variation. Months vary by season and weather, so one 12-month ratio could hide that the gap is large in some months and absent in others.

**Hidden assumptions**
- A daily total is the right unit for a driver plan. Plans are by shift and hour, and weekends differ mostly in the shape of the day (late night, morning commute), not the total.
- The data contains no anomalies in dates (files can include trips with dates outside the month; 01_research notes errors are likely).

**Sharper directions**
- Compare the hourly profile, weekday vs weekend, per service, rather than the daily total.
- Show monthly ratios to see whether the 10% result is stable, and separate holidays.
- Use a Friday/Saturday night split if the plan question is about nights.

**Decision link.** Today the answer decides "one plan or two". With a 10% cut-off on the daily total, a service could pass with the same total but a very different hourly shape, giving the wrong decision.

## Q4 (high demand, weak coverage; HVFHV only)

**Ambiguity**
- "Underserved" has two definitions: the Metric (top quarter by trips and longest 20% of median waits) and the Hypothesis (a zone with median wait at least 1.5x the others in the top quarter). They do not give the same set.
- "Most of the 12 months": the same zone each month, or any zone?
- "Weak coverage" is not what wait time measures.

**Measurability**
- The metric is a proxy and the file says so. It adds more problems: only completed trips appear, so requests that were cancelled or never matched are invisible, and the worst coverage is likely missing from the data.
- Wait from request to pickup includes the passenger's walking and driver arrival time, and the platform's matching logic. It is not driver supply.
- Check if an on-scene or arrival timestamp exists in the real file. It would separate dispatch time from passenger time. Not verified.

**Hidden assumptions**
- Long wait means too few drivers, rather than traffic, access rules (airports, restricted streets), or surge/pricing policy.
- Wait times are comparable across zones and hours. Late-night waits differ from daytime ones.
- Median wait per zone has enough trips and low noise in every zone and month.

**Logic problem (fix first).** "Underserved" is defined as the top quarter by trips and the longest 20% of waits. By construction some zones always meet it, so "at least one zone underserved in most months" is almost automatically true, and the decision rule would always say "test adding drivers". The rule needs a threshold in absolute terms (for example a wait gap against a reference), not a rank.

**Sharper directions**
- Compare each zone's wait against its own typical hour pattern or against similar zones, not against a rank cut-off.
- Look at persistence: does a zone stay unusually slow across months and hours?
- Test whether long waits coincide with high-demand hours (a supply-vs-demand signature) or are constant (probably structural, not coverage).
- State plainly in the question that this cannot show driver supply, and what follow-up data would.

**Decision link.** The action is moving or adding drivers. A wait-time signal alone would not justify that. It would justify a small test in chosen zones and hours, which is how the rule already phrases it, so keep that framing.

## Top 3 issues to fix first

1. **Q4 rule is circular.** The "underserved" definition is rank-based, so the condition is met by construction and the rule never returns "no action". Also reconcile the two definitions (Metric vs Hypothesis) and the proxy limits (completed trips only, wait is not supply).
2. **Questions and project do not match, and the decisions are weakly linked.** No question uses the congestion fee or the zone, and several decisions (driver placement, plan choice) depend on hour-level behavior and value per trip that the metrics do not include. Decide what the project is about, then align the questions and name the decision maker for each service.
3. **Unjustified cut-offs and pass/fail rules.** Top 5, 40%, 80/20, 10% and 1.5x decide the outcome without a stated reason, and Q2 and Q1a may be near-certain to pass. Replace single thresholds with a reason for each line (what the decision maker would do differently on either side), and consider curves or hourly profiles instead of one number.
