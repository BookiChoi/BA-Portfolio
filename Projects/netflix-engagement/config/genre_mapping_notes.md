Author: human

# Genre mapping notes (frozen before any genre share is computed)

- Source: TMDB movie and TV genre lists. Ids are in genre_mapping.csv.
- Rule: a title's primary group is the group with the smallest group_priority among its TMDB genres. A title with no genre stays unlabelled.
- Order logic: format- or audience-defined groups first (documentary and reality, kids and family, animation), then story genres, then broad ones. Drama is last because TMDB attaches it to a very large share of titles and it would otherwise absorb them.
- Group count: 8, within the 6 to 8 set in 02_questions.md. Groups with a mean share below 5% are not tested.
- Judgment calls (changed only before results, never after):
  1. Horror is merged into Crime & Thriller to keep 8 groups.
  2. War, History and Music go to Drama; Western goes to Action & Adventure.
  3. Kids & Family sits above Animation, so children's animation counts as Kids & Family and anime and adult animation count as Animation.

*Writing note: the first draft of this mapping was prepared by Claude in chat; I reviewed every row and the three judgment calls above before committing.*