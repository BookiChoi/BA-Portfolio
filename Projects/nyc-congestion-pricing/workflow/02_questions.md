Author: human
Status: final

# 02 Business Questions

Scope: every question is answered separately for yellow taxi and for Uber/Lyft
(high-volume FHV). A combined view is supporting context for each decision maker,
not a separate question. This is a decision, not an oversight.

Decision makers: a yellow-taxi fleet operations manager, and an Uber/Lyft platform
operations manager. Neither assigns drivers to zones. Each decides what zone and
time-of-day guidance to give drivers (for example "these zones are busy at these
hours"), and where to spend incentives or driver communication.

Known limits (stated before any result):
- Trip count is not earnings. It ignores fare, trip length and driver time.
- Only completed trips are in the data. Unmatched or cancelled requests are invisible.
- Zones differ in size, so raw counts favor large zones.
- Trips with an unknown or outside-zone location ID are excluded and their number is reported.
- Analysis period and months may be reduced after file sizes are known in 03.

## Q1

### Decision to be made
Each operations manager decides which zones to list in driver guidance for each part
of the day, and whether low-volume zones need more than the standard guidance.

### Question
Which pickup zones have the most trips in each part of the day, and how concentrated
are trips across zones?

### Hypothesis
(a) Airport zones will be among the top 5 pickup zones over the whole period, for both services.
(b) Uber/Lyft trips will be less concentrated than yellow taxi trips: more zones will
be needed to cover 80% of Uber/Lyft trips than 80% of yellow taxi trips.

### Metric
Trips per pickup zone (PULocationID) in each day-part, ranked, per service.
Day-parts: overnight 00-05, morning 06-09, midday 10-15, evening 16-19, night 20-23.
Cumulative share curve of zones ranked by trips; report the number of zones needed to
cover 50% and 80% of trips. Stability check: whether the top zone set is the same in
each month.

### Data needed
Yellow and high-volume FHV records: pickup datetime, PULocationID, one row = one trip.
Taxi zone lookup. Airport zones = zones whose name contains an airport in the lookup
(list fixed in 03, before any result).

### Decision rule
Guidance for each day-part lists the smallest set of zones covering 50% of trips in
that day-part. Zones outside that set get standard guidance only. The 50% line is chosen
so the list stays short enough for a driver to read; if a list needs more than 30 zones
the line is lowered to 40%.
If a zone is in the list in every month, it is a standing zone; if only in some months,
it is marked as seasonal.

## Q2

### Decision to be made
Each operations manager decides whether driver guidance for airport trips should name
specific destination areas.

### Question
Where do trips that start at an airport zone end, for each airport separately?

### Hypothesis
Airport-origin trips are more concentrated than trips overall: the top 5 destination
zones of airport-origin trips will hold a larger share of those trips than the top 5
pickup zones hold of all trips (Q1).

### Metric
For each airport zone: share of its trips going to each destination zone (DOLocationID);
combined share of the top 5 destinations. Compared with the top-5 pickup share from Q1.
This measures where passengers go, not where drivers go next. Drivers may not stay near
the drop-off; this is an assumption and is not measured.

### Data needed
Same as Q1, plus DOLocationID.

### Decision rule
If the airport top-5 destination share is larger than the overall top-5 pickup share,
airport guidance names those destination zones. If not, airport guidance does not name
destinations. The line is the overall concentration, because naming destinations only
adds information if airport trips are more concentrated than the average trip.

## Q3

### Decision to be made
Each operations manager decides whether driver guidance for night hours needs separate
weekday and weekend versions.

### Question
Does the shape of the day differ between weekdays and weekends, in particular the share
of trips at night?

### Hypothesis
For both services, the share of trips between 22:00 and 05:00 is higher on weekend days
(Sat-Sun) than on weekdays (Mon-Fri).

### Metric
Hourly profile of trips per day type, per service. Night share = trips from 22:00 to
05:00 divided by all trips, per day type and per month. Daily totals are also reported.
Public holidays are handled in the 04 plan.

### Data needed
Pickup datetime per trip, one row = one trip.

### Decision rule
If, in every month, the weekend-weekday difference in night share is larger than the
difference between two ordinary weekdays (Mon-Thu) in that month, guidance has separate
weekday and weekend versions for night hours. If the direction flips in any month or
the gap is not larger than the Mon-Thu spread, one version is used. The comparison with
Mon-Thu is the line, because it shows the normal day-to-day variation.

## Q4

### Decision to be made
Each operations manager decides whether driver guidance for trips to and from the
Congestion Relief Zone needs to be reviewed, including areas just outside the zone.

### Question
How did the share of trips that start or end in the Congestion Relief Zone change after
the congestion fee began on 2025-01-05?

### Hypothesis
For both services, the share of trips that start or end inside the zone fell between
the Jan-Sep 2024 and Jan-Sep 2026 periods.

### Metric
Share of all trips (per service) with pickup or dropoff in the zone, for the same
calendar months in different years (Jan-Sep) to avoid seasonality.
Pre period: Jan-Sep 2024. Post period: Jan-Sep 2026. Drift baseline: Jan-Sep 2023 to
Jan-Sep 2024, which is before the fee.
Zone membership: taxi zones counted as inside the zone, fixed in 03 from an official
source before any result. Cross-check after 2025-01-05: trips with cbd_congestion_fee
above zero should mostly fall in those zones.
This cannot show that the fee caused the change; other things changed in the same
years.

### Data needed
Yellow and high-volume FHV records for 2023-2026 (Jan-Sep): pickup and dropoff
datetime, PULocationID, DOLocationID, cbd_congestion_fee (2025 onward). Taxi zone
lookup. Check that zone IDs are unchanged across years.

### Decision rule
If the change in share from the pre to the post period is larger in absolute size than
the change in the drift baseline (2023 to 2024), treat it as a real shift and review
guidance for the zone and its neighbouring zones. If not, keep current guidance. The
line is the normal year-to-year movement before the fee.