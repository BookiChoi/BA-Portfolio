Author: human
Status: ready-for-coach

# 02 Business Questions

Scope: every question is answered separately for yellow taxi and for Uber/Lyft (high-volume FHV).
A combined view is supporting context for each decision maker, not a separate question.
Analysis period: the most recent 12 full months available (Oct 2025 - Sep 2026).
(Reason: all months are after the congestion fee started on 2025-01-05, so no policy
change falls inside the period. Final months depend on file sizes in 03.)

## Q1

### Decision to be made
A yellow-taxi fleet operations manager and an Uber/Lyft operations manager each decide
in which pickup areas to put drivers, and where drivers are likely to end up after
airport trips.

### Question
Q1a: Which pickup zones have the most trips? Q1b: Where do trips that start at an
airport zone end?

### Hypothesis
Q1a: Airport zones will rank among the top 5 pickup zones by number of trips, for both
yellow taxi and Uber/Lyft.
Q1b: Among trips that start at an airport zone, the top 5 destination zones will
account for at least 40% of those trips.

### Metric
Q1a: trip count per pickup zone (PULocationID), ranked, per service.
Q1b: share of airport-origin trips going to each destination zone (DOLocationID);
share of the top 5 destinations combined. Airport zones = zones whose name contains
an airport in the TLC taxi zone lookup (list fixed in 03, before any result).

### Data needed
Yellow and high-volume FHV trip records: pickup and dropoff datetime, PULocationID,
DOLocationID. Taxi zone lookup. One row = one trip.

### Decision rule
Q1a: if an airport zone is in the top 5 for a service, that operations manager keeps
a standing airport plan; otherwise airport coverage is planned like any other zone.
Q1b: if the top 5 destinations hold at least 40% of airport-origin trips, plan
repositioning for those 5 zones; otherwise do not plan zone-specific repositioning.

## Q2

### Decision to be made
The same operations managers decide whether it is worth putting effort into the
low-volume pickup zones, or whether to concentrate drivers on the busiest ones.

### Question
How concentrated are trips across pickup zones (Pareto-style)?

### Hypothesis
The top 20% of pickup zones will account for at least 80% of trips, for both
services.

### Metric
Zones with at least one trip in the period, ranked by trips. Cumulative share of
trips held by the top 20% of those zones.

### Data needed
Same as Q1a.

### Decision rule
If the top 20% hold at least 80% of trips, concentrate drivers on the top zones and
keep only a basic coverage plan elsewhere; if less than 80%, plan coverage for the
wider set of zones.

## Q3

### Decision to be made
The same operations managers decide whether to use one driver plan or separate
weekday and weekend plans.

### Question
Do average daily trips differ between weekdays and weekends?

### Hypothesis
Yellow taxi: average weekend-day trips will be at least 10% lower than weekday trips.
Uber/Lyft: average weekend-day trips will be within 10% of weekday trips.

### Metric
Average daily trips on weekdays (Mon-Fri) vs weekend days (Sat-Sun), overall and for
the top 20 pickup zones, per service. Public holidays: handling fixed in the 04 plan.

### Data needed
Pickup datetime per trip; one row = one trip.

### Decision rule
If weekend and weekday averages differ by more than 10% for a service, that operations
manager uses separate weekday and weekend plans; otherwise one plan.

## Q4

### Decision to be made
An operations manager decides whether to move existing drivers, or add drivers, into
areas that look high in demand but lightly covered.

### Question
Are there pickup zones with high demand but weak coverage? (Uber/Lyft only, see Metric.)

### Hypothesis
At least one zone in the top quarter by trips will have a median wait time at least
1.5 times the median wait of the other top-quarter zones.

### Metric
Wait time = pickup_datetime minus request_datetime (high-volume FHV only). Per zone:
trips and median wait. "Underserved" = top quarter by trips and the longest 20% of
median waits. Yellow taxi is excluded because street hails have no request time.

### Data needed
High-volume FHV records: request_datetime, pickup_datetime, PULocationID. Fields must
be checked in the real files. Only a proxy: no driver counts or supply data exist.

### Decision rule
If at least one zone is underserved in most of the 12 months, the operations manager
tests moving or adding drivers there; otherwise no action.