Author: human

# Genre mapping notes (frozen before any genre share is computed)

- Source: IMDb Non-Commercial Datasets (title.basics genres, up to three per title). Names are in genre_mapping.csv. This replaces an earlier draft that used TMDB genre ids; the groups and the priority logic are unchanged.
- Rule: a title's primary group is the group with the smallest group_priority among its IMDb genres. A title whose genres are all unmapped stays unlabelled. A row with an empty group means "not mappable".
- Order logic: format- or audience-defined groups first (documentary and reality, kids and family, animation), then story genres, then broad ones. Drama is last because IMDb attaches it to a very large share of titles and it would otherwise absorb them.
- Group count: 8, within the 6 to 8 set in 02_questions.md. Groups with a mean share below 5% are not tested.
- Judgment calls (changed only before results, never after):
  1. Horror and Film-Noir are merged into Crime & Thriller to keep 8 groups.
  2. War, History, Biography, Music and Musical go to Drama; Western and Sport go to Action & Adventure.
  3. Kids & Family sits above Animation, so children's animation counts as Kids & Family and anime and adult animation count as Animation.
  4. News, Talk-Show and Game-Show go with Documentary & Reality.
  5. Short and Adult are not mapped: they are format or content flags, not genres.

*Writing note: the first draft of this mapping was prepared by Claude in chat; I reviewed every row and the five judgment calls above before committing.*