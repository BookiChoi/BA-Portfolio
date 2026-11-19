Author: ai/main-session
Status: draft

# 01b Data profile: Netflix What We Watched reports (7 files)

Numbers only, produced by `pipeline/profile_reports.py`. Machine-readable versions are in `outputs/profile/`.
Definitions: *title-level rows* exclude the `Other Movies` / `Other Shows` rows. *Top-10 share* is the hours of the 10 largest title-level rows divided by the stated total. Percentiles use linear interpolation.

## 1. Size and structure
| file | sheets | type split by | data rows | title-level rows | distinct titles | film rows | series rows | unknown-type rows | Other rows |
|---|---|---|---|---|---|---|---|---|---|
| 2023Jan-Jun.xlsx | Engagement | none (single sheet, no type column) | 18,214 | 18,214 | 18,214 | 0 | 0 | 18,214 | 0 |
| 2023Jul-Dec.xlsx | TV, Film | sheet name | 15,994 | 15,994 | 15,994 | 9,395 | 6,599 | 0 | 0 |
| 2024Jan-Jun.xlsx | TV, Film | sheet name | 16,161 | 16,161 | 16,160 | 9,360 | 6,801 | 0 | 0 |
| 2024Jul-Dec.xlsx | TV, Film | sheet name | 15,563 | 15,563 | 15,561 | 8,680 | 6,883 | 0 | 0 |
| 2025Jan-Jun.xlsx | Shows, Movies | sheet name | 16,182 | 16,182 | 16,177 | 8,674 | 7,508 | 0 | 0 |
| 2025Jul-Dec.xlsx | Shows, Movies | sheet name | 16,470 | 16,468 | 16,465 | 8,724 | 7,746 | 0 | 2 |
| 2026Jan-Jun.xlsx | Shows, Movies | sheet name | 17,372 | 17,370 | 17,367 | 9,178 | 8,194 | 0 | 2 |

## 2. Header position and skipped rows
| file | sheet | header row (Excel) | rows above header (non-empty) | blank rows below | footnote rows | data rows |
|---|---|---|---|---|---|---|
| 2023Jan-Jun.xlsx | Engagement | 6 | 2 | 1 | 0 | 18,214 |
| 2023Jul-Dec.xlsx | TV | 6 | 2 | 1 | 0 | 6,599 |
| 2023Jul-Dec.xlsx | Film | 6 | 2 | 1 | 0 | 9,395 |
| 2024Jan-Jun.xlsx | TV | 6 | 2 | 0 | 0 | 6,801 |
| 2024Jan-Jun.xlsx | Film | 6 | 2 | 0 | 0 | 9,360 |
| 2024Jul-Dec.xlsx | TV | 6 | 2 | 0 | 0 | 6,883 |
| 2024Jul-Dec.xlsx | Film | 6 | 2 | 0 | 0 | 8,680 |
| 2025Jan-Jun.xlsx | Shows | 6 | 2 | 0 | 0 | 7,508 |
| 2025Jan-Jun.xlsx | Movies | 6 | 2 | 0 | 0 | 8,674 |
| 2025Jul-Dec.xlsx | Shows | 6 | 2 | 1 | 1 | 7,746 |
| 2025Jul-Dec.xlsx | Movies | 6 | 2 | 1 | 1 | 8,724 |
| 2026Jan-Jun.xlsx | Shows | 6 | 2 | 1 | 1 | 8,194 |
| 2026Jan-Jun.xlsx | Movies | 6 | 2 | 1 | 1 | 9,178 |

## 3. Total hours and top-10 concentration
| file | total hours (incl. Other) | total hours (title-level) | top-10 hours | top-10 share of total incl. Other (%) | top-10 share of title-level total (%) |
|---|---|---|---|---|---|
| 2023Jan-Jun.xlsx | 93,455,200,000 | 93,455,200,000 | 4,951,700,000 | 5.30 | 5.30 |
| 2023Jul-Dec.xlsx | 90,023,100,000 | 90,023,100,000 | 3,668,100,000 | 4.07 | 4.07 |
| 2024Jan-Jun.xlsx | 94,003,500,000 | 94,003,500,000 | 4,880,100,000 | 5.19 | 5.19 |
| 2024Jul-Dec.xlsx | 94,115,100,000 | 94,115,100,000 | 4,155,600,000 | 4.42 | 4.42 |
| 2025Jan-Jun.xlsx | 95,186,500,000 | 95,186,500,000 | 4,738,100,000 | 4.98 | 4.98 |
| 2025Jul-Dec.xlsx | 96,207,800,000 | 95,450,600,000 | 5,885,800,000 | 6.12 | 6.17 |
| 2026Jan-Jun.xlsx | 97,664,500,000 | 96,804,600,000 | 4,535,400,000 | 4.64 | 4.69 |

## 4. Distributions (all sheets of a file stacked; Other rows included where numeric)
| file | metric | n | min | p25 | median | mean | p75 | p90 | p99 | max |
|---|---|---|---|---|---|---|---|---|---|---|
| 2023Jan-Jun.xlsx | hours_viewed | 18,214 | 100,000 | 200,000 | 700,000 | 5,130,954 | 3,400,000 | 11,500,000 | 68,061,000 | 812,100,000 |
| 2023Jan-Jun.xlsx | runtime_minutes | 0 |  |  |  |  |  |  |  |  |
| 2023Jan-Jun.xlsx | views | 0 |  |  |  |  |  |  |  |  |
| 2023Jul-Dec.xlsx | hours_viewed | 15,994 | 100,000 | 200,000 | 1,000,000 | 5,628,554 | 4,175,000 | 13,300,000 | 71,356,000 | 630,200,000 |
| 2023Jul-Dec.xlsx | runtime_minutes | 15,823 | 6.00 | 98.00 | 117.00 | 249.96 | 280.00 | 548.00 | 1,498 | 23,853 |
| 2023Jul-Dec.xlsx | views | 15,994 | 100,000 | 100,000 | 300,000 | 1,489,540 | 1,200,000 | 3,400,000 | 17,200,000 | 121,000,000 |
| 2024Jan-Jun.xlsx | hours_viewed | 16,161 | 100,000 | 300,000 | 1,000,000 | 5,816,688 | 4,200,000 | 13,500,000 | 73,460,000 | 733,800,000 |
| 2024Jan-Jun.xlsx | runtime_minutes | 15,973 | 6.00 | 98.00 | 117.00 | 252.30 | 284.00 | 549.00 | 1,511 | 23,853 |
| 2024Jan-Jun.xlsx | views | 16,161 | 100,000 | 100,000 | 300,000 | 1,497,729 | 1,200,000 | 3,400,000 | 17,240,000 | 143,800,000 |
| 2024Jul-Dec.xlsx | hours_viewed | 15,563 | 100,000 | 300,000 | 1,000,000 | 6,047,362 | 4,300,000 | 14,400,000 | 75,714,000 | 619,900,000 |
| 2024Jul-Dec.xlsx | runtime_minutes | 15,388 | 6.00 | 99.00 | 120.00 | 265.61 | 298.00 | 573.00 | 1,636 | 23,853 |
| 2024Jul-Dec.xlsx | views | 15,563 | 100,000 | 100,000 | 300,000 | 1,560,785 | 1,200,000 | 3,500,000 | 18,800,000 | 137,300,000 |
| 2025Jan-Jun.xlsx | hours_viewed | 16,182 | 100,000 | 300,000 | 1,000,000 | 5,882,246 | 4,200,000 | 13,400,000 | 75,719,000 | 840,300,000 |
| 2025Jan-Jun.xlsx | runtime_minutes | 15,923 | 2.00 | 100.00 | 122.00 | 274.59 | 306.00 | 580.00 | 1,812 | 23,853 |
| 2025Jan-Jun.xlsx | views | 16,182 | 100,000 | 100,000 | 300,000 | 1,471,623 | 1,100,000 | 3,400,000 | 17,200,000 | 164,700,000 |
| 2025Jul-Dec.xlsx | hours_viewed | 16,470 | 100,000 | 300,000 | 1,100,000 | 5,841,396 | 4,300,000 | 13,100,000 | 69,831,000 | 964,100,000 |
| 2025Jul-Dec.xlsx | runtime_minutes | 16,193 | 9.00 | 100.00 | 123.00 | 274.99 | 308.00 | 576.00 | 1,717 | 23,853 |
| 2025Jul-Dec.xlsx | views | 16,468 | 100,000 | 100,000 | 300,000 | 1,469,098 | 1,200,000 | 3,300,000 | 16,333,000 | 481,600,000 |
| 2026Jan-Jun.xlsx | hours_viewed | 17,372 | 100,000 | 300,000 | 1,000,000 | 5,621,949 | 4,000,000 | 12,300,000 | 70,300,000 | 889,800,000 |
| 2026Jan-Jun.xlsx | runtime_minutes | 17,060 | 9.00 | 100.00 | 123.00 | 275.40 | 308.00 | 571.00 | 1,710 | 23,853 |
| 2026Jan-Jun.xlsx | views | 17,370 | 100,000 | 100,000 | 300,000 | 1,346,598 | 1,100,000 | 3,200,000 | 14,531,000 | 146,900,000 |

## 5. Outliers (Tukey fence: Q3 + 1.5 x IQR)
| file | metric | IQR upper fence | rows above fence | largest title-level value |
|---|---|---|---|---|
| 2023Jan-Jun.xlsx | hours_viewed | 8,200,000 | 2,416 | 812,100,000 |
| 2023Jul-Dec.xlsx | hours_viewed | 10,137,500 | 1,998 | 630,200,000 |
| 2023Jul-Dec.xlsx | views | 2,850,000 | 1,960 | 121,000,000 |
| 2023Jul-Dec.xlsx | runtime_minutes | 553.00 | 1,542 | 23,853 |
| 2024Jan-Jun.xlsx | hours_viewed | 10,050,000 | 2,060 | 733,800,000 |
| 2024Jan-Jun.xlsx | views | 2,850,000 | 1,963 | 143,800,000 |
| 2024Jan-Jun.xlsx | runtime_minutes | 563.00 | 1,501 | 23,853 |
| 2024Jul-Dec.xlsx | hours_viewed | 10,300,000 | 2,063 | 619,900,000 |
| 2024Jul-Dec.xlsx | views | 2,850,000 | 1,904 | 137,300,000 |
| 2024Jul-Dec.xlsx | runtime_minutes | 596.50 | 1,383 | 23,853 |
| 2025Jan-Jun.xlsx | hours_viewed | 10,050,000 | 2,105 | 840,300,000 |
| 2025Jan-Jun.xlsx | views | 2,600,000 | 2,017 | 164,700,000 |
| 2025Jan-Jun.xlsx | runtime_minutes | 615.00 | 1,368 | 23,853 |
| 2025Jul-Dec.xlsx | hours_viewed | 10,300,000 | 2,080 | 964,100,000 |
| 2025Jul-Dec.xlsx | views | 2,850,000 | 1,950 | 481,600,000 |
| 2025Jul-Dec.xlsx | runtime_minutes | 620.00 | 1,330 | 23,853 |
| 2026Jan-Jun.xlsx | hours_viewed | 9,550,000 | 2,185 | 889,800,000 |
| 2026Jan-Jun.xlsx | views | 2,600,000 | 2,101 | 146,900,000 |
| 2026Jan-Jun.xlsx | runtime_minutes | 620.00 | 1,382 | 23,853 |

## 6. Release date and global availability
| file | release date missing (n) | release date missing (%) | release date min | release date max | unparsable dates | global=No (%) | global=Yes (%) | global=* (%) |
|---|---|---|---|---|---|---|---|---|
| 2023Jan-Jun.xlsx | 13,359 | 73.34 | 2010-04-01 | 2023-06-30 | 0 | 75.22 | 24.78 |  |
| 2023Jul-Dec.xlsx | 11,026 | 68.94 | 2010-04-01 | 2023-12-31 | 0 | 70.12 | 29.88 |  |
| 2024Jan-Jun.xlsx | 11,092 | 68.63 | 2010-04-01 | 2024-06-28 | 0 | 73.54 | 26.46 |  |
| 2024Jul-Dec.xlsx | 10,579 | 67.98 | 2010-04-01 | 2024-12-31 | 0 | 72.49 | 27.51 |  |
| 2025Jan-Jun.xlsx | 10,708 | 66.17 | 2010-04-01 | 2025-06-30 | 0 | 71.41 | 28.59 |  |
| 2025Jul-Dec.xlsx | 10,752 | 65.29 | 2010-04-01 | 2025-12-31 | 0 | 69.65 | 30.33 | 0.01 |
| 2026Jan-Jun.xlsx | 11,324 | 65.19 | 2010-04-01 | 2026-06-29 | 0 | 69.58 | 30.41 | 0.01 |

## 7. Per-column missingness, duplicates, header phrases in data rows
| file | column | missing (n) | missing (%) | column in header | distinct | duplicate values | '*' placeholders | header-phrase rows |
|---|---|---|---|---|---|---|---|---|
| 2023Jan-Jun.xlsx | title | 0.00 | 0.00 | True | 18,214 | 0 | 0.00 | 0 |
| 2023Jan-Jun.xlsx | available_globally | 0.00 | 0.00 | True | 2.00 | 18,212 | 0.00 | 0 |
| 2023Jan-Jun.xlsx | release_date | 13,359 | 73.34 | True | 1,665 | 3,190 | 0.00 | 0 |
| 2023Jan-Jun.xlsx | hours_viewed | 0.00 | 0.00 | True | 712.00 | 17,502 | 0.00 | 0 |
| 2023Jan-Jun.xlsx | runtime | 18,214 | 100.00 | False | 0.00 | 0 | 0.00 | 0 |
| 2023Jan-Jun.xlsx | views | 18,214 | 100.00 | False | 0.00 | 0 | 0.00 | 0 |
| 2023Jan-Jun.xlsx | (whole row) |  |  |  |  | 0 |  | 0 |
| 2023Jul-Dec.xlsx | title | 0.00 | 0.00 | True | 15,994 | 0 | 0.00 | 0 |
| 2023Jul-Dec.xlsx | available_globally | 0.00 | 0.00 | True | 2.00 | 15,992 | 0.00 | 0 |
| 2023Jul-Dec.xlsx | release_date | 11,026 | 68.94 | True | 1,732 | 3,236 | 0.00 | 0 |
| 2023Jul-Dec.xlsx | hours_viewed | 0.00 | 0.00 | True | 693.00 | 15,301 | 0.00 | 0 |
| 2023Jul-Dec.xlsx | runtime | 0.00 | 0.00 | True | 1,269 | 14,725 | 171.00 | 0 |
| 2023Jul-Dec.xlsx | views | 0.00 | 0.00 | True | 286.00 | 15,708 | 0.00 | 0 |
| 2023Jul-Dec.xlsx | (whole row) |  |  |  |  | 0 |  | 0 |
| 2024Jan-Jun.xlsx | title | 0.00 | 0.00 | True | 16,160 | 1 | 0.00 | 0 |
| 2024Jan-Jun.xlsx | available_globally | 0.00 | 0.00 | True | 2.00 | 16,159 | 0.00 | 0 |
| 2024Jan-Jun.xlsx | release_date | 11,092 | 68.63 | True | 1,814 | 3,255 | 0.00 | 0 |
| 2024Jan-Jun.xlsx | hours_viewed | 0.00 | 0.00 | True | 724.00 | 15,437 | 0.00 | 0 |
| 2024Jan-Jun.xlsx | runtime | 0.00 | 0.00 | True | 1,284 | 14,877 | 188.00 | 0 |
| 2024Jan-Jun.xlsx | views | 0.00 | 0.00 | True | 285.00 | 15,876 | 0.00 | 0 |
| 2024Jan-Jun.xlsx | (whole row) |  |  |  |  | 0 |  | 0 |
| 2024Jul-Dec.xlsx | title | 0.00 | 0.00 | True | 15,561 | 2 | 0.00 | 0 |
| 2024Jul-Dec.xlsx | available_globally | 0.00 | 0.00 | True | 2.00 | 15,561 | 0.00 | 0 |
| 2024Jul-Dec.xlsx | release_date | 10,579 | 67.98 | True | 1,858 | 3,126 | 0.00 | 0 |
| 2024Jul-Dec.xlsx | hours_viewed | 0.00 | 0.00 | True | 723.00 | 14,840 | 0.00 | 0 |
| 2024Jul-Dec.xlsx | runtime | 0.00 | 0.00 | True | 1,308 | 14,255 | 172.00 | 0 |
| 2024Jul-Dec.xlsx | views | 0.00 | 0.00 | True | 302.00 | 15,261 | 0.00 | 0 |
| 2024Jul-Dec.xlsx | (whole row) |  |  |  |  | 0 |  | 0 |
| 2025Jan-Jun.xlsx | title | 0.00 | 0.00 | True | 16,177 | 5 | 0.00 | 0 |
| 2025Jan-Jun.xlsx | available_globally | 0.00 | 0.00 | True | 2.00 | 16,180 | 0.00 | 0 |
| 2025Jan-Jun.xlsx | release_date | 10,708 | 66.17 | True | 2,003 | 3,471 | 0.00 | 0 |
| 2025Jan-Jun.xlsx | hours_viewed | 0.00 | 0.00 | True | 709.00 | 15,473 | 0.00 | 0 |
| 2025Jan-Jun.xlsx | runtime | 0.00 | 0.00 | True | 1,388 | 14,794 | 171.00 | 0 |
| 2025Jan-Jun.xlsx | views | 0.00 | 0.00 | True | 293.00 | 15,889 | 0.00 | 0 |
| 2025Jan-Jun.xlsx | (whole row) |  |  |  |  | 0 |  | 0 |
| 2025Jul-Dec.xlsx | title | 0.00 | 0.00 | True | 16,467 | 3 | 0.00 | 0 |
| 2025Jul-Dec.xlsx | available_globally | 0.00 | 0.00 | True | 3.00 | 16,467 | 2.00 | 0 |
| 2025Jul-Dec.xlsx | release_date | 10,752 | 65.28 | True | 2,112 | 3,606 | 2.00 | 0 |
| 2025Jul-Dec.xlsx | hours_viewed | 0.00 | 0.00 | True | 702.00 | 15,768 | 0.00 | 0 |
| 2025Jul-Dec.xlsx | runtime | 0.00 | 0.00 | True | 1,390 | 15,080 | 175.00 | 0 |
| 2025Jul-Dec.xlsx | views | 0.00 | 0.00 | True | 289.00 | 16,181 | 2.00 | 0 |
| 2025Jul-Dec.xlsx | (whole row) |  |  |  |  | 0 |  | 0 |
| 2026Jan-Jun.xlsx | title | 0.00 | 0.00 | True | 17,369 | 3 | 0.00 | 0 |
| 2026Jan-Jun.xlsx | available_globally | 0.00 | 0.00 | True | 3.00 | 17,369 | 2.00 | 0 |
| 2026Jan-Jun.xlsx | release_date | 11,324 | 65.19 | True | 2,211 | 3,837 | 2.00 | 0 |
| 2026Jan-Jun.xlsx | hours_viewed | 0.00 | 0.00 | True | 707.00 | 16,665 | 0.00 | 0 |
| 2026Jan-Jun.xlsx | runtime | 0.00 | 0.00 | True | 1,443 | 15,929 | 195.00 | 0 |
| 2026Jan-Jun.xlsx | views | 0.00 | 0.00 | True | 265.00 | 17,107 | 2.00 | 0 |
| 2026Jan-Jun.xlsx | (whole row) |  |  |  |  | 0 |  | 0 |

## 8. Column structure comparison
Reference: `2026Jan-Jun.xlsx:Shows`.
| file | sheet | header_row_excel | n_columns | same_as_reference | columns_in_order |
|---|---|---|---|---|---|
| 2023Jan-Jun.xlsx | Engagement | 6 | 4 | False | Title \| Available Globally? \| Release Date \| Hours Viewed |
| 2023Jul-Dec.xlsx | TV | 6 | 6 | True | Title \| Available Globally? \| Release Date \| Hours Viewed \| Runtime \| Views |
| 2023Jul-Dec.xlsx | Film | 6 | 6 | True | Title \| Available Globally? \| Release Date \| Hours Viewed \| Runtime \| Views |
| 2024Jan-Jun.xlsx | TV | 6 | 6 | True | Title \| Available Globally? \| Release Date \| Hours Viewed \| Runtime \| Views |
| 2024Jan-Jun.xlsx | Film | 6 | 6 | True | Title \| Available Globally? \| Release Date \| Hours Viewed \| Runtime \| Views |
| 2024Jul-Dec.xlsx | TV | 6 | 6 | True | Title \| Available Globally? \| Release Date \| Hours Viewed \| Runtime \| Views |
| 2024Jul-Dec.xlsx | Film | 6 | 6 | True | Title \| Available Globally? \| Release Date \| Hours Viewed \| Runtime \| Views |
| 2025Jan-Jun.xlsx | Shows | 6 | 6 | True | Title \| Available Globally? \| Release Date \| Hours Viewed \| Runtime \| Views |
| 2025Jan-Jun.xlsx | Movies | 6 | 6 | True | Title \| Available Globally? \| Release Date \| Hours Viewed \| Runtime \| Views |
| 2025Jul-Dec.xlsx | Shows | 6 | 6 | True | Title \| Available Globally? \| Release Date \| Hours Viewed \| Runtime \| Views |
| 2025Jul-Dec.xlsx | Movies | 6 | 6 | True | Title \| Available Globally? \| Release Date \| Hours Viewed \| Runtime \| Views |
| 2026Jan-Jun.xlsx | Shows | 6 | 6 | True | Title \| Available Globally? \| Release Date \| Hours Viewed \| Runtime \| Views |
| 2026Jan-Jun.xlsx | Movies | 6 | 6 | True | Title \| Available Globally? \| Release Date \| Hours Viewed \| Runtime \| Views |

## 9. Title overlap between adjacent half-years
`exact` = identical string; `normalized` = NFKC, case-folded, punctuation and spacing removed; `normalized_first_segment` = same, using the part before ` // `.
| earlier | later | match_level | n_earlier | n_later | n_matched | pct_of_earlier | pct_of_later |
|---|---|---|---|---|---|---|---|
| 2023Jan-Jun.xlsx | 2023Jul-Dec.xlsx | exact | 18,214 | 15,994 | 13,608 | 74.71 | 85.08 |
| 2023Jan-Jun.xlsx | 2023Jul-Dec.xlsx | normalized | 18,212 | 15,993 | 13,611 | 74.74 | 85.11 |
| 2023Jan-Jun.xlsx | 2023Jul-Dec.xlsx | normalized_first_segment | 18,152 | 15,948 | 13,589 | 74.86 | 85.21 |
| 2023Jul-Dec.xlsx | 2024Jan-Jun.xlsx | exact | 15,994 | 16,160 | 13,473 | 84.24 | 83.37 |
| 2023Jul-Dec.xlsx | 2024Jan-Jun.xlsx | normalized | 15,993 | 16,159 | 13,474 | 84.25 | 83.38 |
| 2023Jul-Dec.xlsx | 2024Jan-Jun.xlsx | normalized_first_segment | 15,948 | 16,101 | 13,443 | 84.29 | 83.49 |
| 2024Jan-Jun.xlsx | 2024Jul-Dec.xlsx | exact | 16,160 | 15,561 | 13,065 | 80.85 | 83.96 |
| 2024Jan-Jun.xlsx | 2024Jul-Dec.xlsx | normalized | 16,159 | 15,558 | 13,069 | 80.88 | 84.00 |
| 2024Jan-Jun.xlsx | 2024Jul-Dec.xlsx | normalized_first_segment | 16,101 | 15,502 | 13,082 | 81.25 | 84.39 |
| 2024Jul-Dec.xlsx | 2025Jan-Jun.xlsx | exact | 15,561 | 16,177 | 13,111 | 84.26 | 81.05 |
| 2024Jul-Dec.xlsx | 2025Jan-Jun.xlsx | normalized | 15,558 | 16,174 | 13,111 | 84.27 | 81.06 |
| 2024Jul-Dec.xlsx | 2025Jan-Jun.xlsx | normalized_first_segment | 15,502 | 16,117 | 13,159 | 84.89 | 81.65 |
| 2025Jan-Jun.xlsx | 2025Jul-Dec.xlsx | exact | 16,177 | 16,465 | 13,415 | 82.93 | 81.48 |
| 2025Jan-Jun.xlsx | 2025Jul-Dec.xlsx | normalized | 16,174 | 16,463 | 13,462 | 83.23 | 81.77 |
| 2025Jan-Jun.xlsx | 2025Jul-Dec.xlsx | normalized_first_segment | 16,117 | 16,426 | 13,448 | 83.44 | 81.87 |
| 2025Jul-Dec.xlsx | 2026Jan-Jun.xlsx | exact | 16,465 | 17,367 | 13,876 | 84.28 | 79.90 |
| 2025Jul-Dec.xlsx | 2026Jan-Jun.xlsx | normalized | 16,463 | 17,365 | 13,886 | 84.35 | 79.97 |
| 2025Jul-Dec.xlsx | 2026Jan-Jun.xlsx | normalized_first_segment | 16,426 | 17,327 | 13,883 | 84.52 | 80.12 |

### Spelling variants (aggregate; title-level examples kept local, not published)
Columns of the local example table: earlier, later, match_level, title_earlier, title_later, hours_earlier, hours_later. 10 example pairs.
| earlier → later | match_level | examples |
|---|---|---|
| 2023Jan-Jun → 2023Jul-Dec | normalized_first_segment | 2 |
| 2023Jul-Dec → 2024Jan-Jun | normalized_first_segment | 2 |
| 2024Jan-Jun → 2024Jul-Dec | normalized_first_segment | 2 |
| 2024Jul-Dec → 2025Jan-Jun | normalized_first_segment | 2 |
| 2025Jan-Jun → 2025Jul-Dec | normalized | 1 |
| 2025Jul-Dec → 2026Jan-Jun | normalized | 1 |

## 10. Season notation
Counts of series-or-unknown title rows by notation pattern.
| file | pattern | n_titles |
|---|---|---|
| 2023Jan-Jun.xlsx | Limited Series | 193 |
| 2023Jan-Jun.xlsx | Part/Volume/Book N | 204 |
| 2023Jan-Jun.xlsx | Season N | 5,222 |
| 2023Jan-Jun.xlsx | Season N: subtitle | 20 |
| 2023Jan-Jun.xlsx | none | 9,229 |
| 2023Jan-Jun.xlsx | other | 2,938 |
| 2023Jan-Jun.xlsx | trailing number | 408 |
| 2023Jan-Jun.xlsx | contains ' // ' (second-language segment) | 6,575 |
| 2023Jan-Jun.xlsx | all series-or-unknown title rows | 18,214 |
| 2023Jul-Dec.xlsx | Limited Series | 392 |
| 2023Jul-Dec.xlsx | Part/Volume/Book N | 166 |
| 2023Jul-Dec.xlsx | Season N | 4,321 |
| 2023Jul-Dec.xlsx | Season N: subtitle | 20 |
| 2023Jul-Dec.xlsx | none | 232 |
| 2023Jul-Dec.xlsx | other | 1,423 |
| 2023Jul-Dec.xlsx | trailing number | 45 |
| 2023Jul-Dec.xlsx | contains ' // ' (second-language segment) | 2,160 |
| 2023Jul-Dec.xlsx | all series-or-unknown title rows | 6,599 |
| 2024Jan-Jun.xlsx | Limited Series | 387 |
| 2024Jan-Jun.xlsx | Part/Volume/Book N | 151 |
| 2024Jan-Jun.xlsx | Season N | 4,487 |
| 2024Jan-Jun.xlsx | Season N: subtitle | 19 |
| 2024Jan-Jun.xlsx | none | 232 |
| 2024Jan-Jun.xlsx | other | 1,480 |
| 2024Jan-Jun.xlsx | trailing number | 45 |
| 2024Jan-Jun.xlsx | contains ' // ' (second-language segment) | 2,307 |
| 2024Jan-Jun.xlsx | all series-or-unknown title rows | 6,801 |
| 2024Jul-Dec.xlsx | Limited Series | 395 |
| 2024Jul-Dec.xlsx | Part/Volume/Book N | 142 |
| 2024Jul-Dec.xlsx | Season N | 4,506 |
| 2024Jul-Dec.xlsx | Season N: subtitle | 19 |
| 2024Jul-Dec.xlsx | none | 272 |
| 2024Jul-Dec.xlsx | other | 1,512 |
| 2024Jul-Dec.xlsx | trailing number | 37 |
| 2024Jul-Dec.xlsx | contains ' // ' (second-language segment) | 2,422 |
| 2024Jul-Dec.xlsx | all series-or-unknown title rows | 6,883 |
| 2025Jan-Jun.xlsx | Limited Series | 432 |
| 2025Jan-Jun.xlsx | Part/Volume/Book N | 147 |
| 2025Jan-Jun.xlsx | Season N | 4,805 |
| 2025Jan-Jun.xlsx | Season N: subtitle | 25 |
| 2025Jan-Jun.xlsx | none | 275 |
| 2025Jan-Jun.xlsx | other | 1,785 |
| 2025Jan-Jun.xlsx | trailing number | 39 |
| 2025Jan-Jun.xlsx | contains ' // ' (second-language segment) | 2,736 |
| 2025Jan-Jun.xlsx | all series-or-unknown title rows | 7,508 |
| 2025Jul-Dec.xlsx | Limited Series | 446 |
| 2025Jul-Dec.xlsx | Part/Volume/Book N | 150 |
| 2025Jul-Dec.xlsx | Season N | 5,008 |
| 2025Jul-Dec.xlsx | Season N: subtitle | 29 |
| 2025Jul-Dec.xlsx | none | 263 |
| 2025Jul-Dec.xlsx | other | 1,809 |
| 2025Jul-Dec.xlsx | trailing number | 40 |
| 2025Jul-Dec.xlsx | contains ' // ' (second-language segment) | 2,776 |
| 2025Jul-Dec.xlsx | all series-or-unknown title rows | 7,745 |
| 2026Jan-Jun.xlsx | Limited Series | 482 |
| 2026Jan-Jun.xlsx | Part/Volume/Book N | 145 |
| 2026Jan-Jun.xlsx | Season N | 5,181 |
| 2026Jan-Jun.xlsx | Season N: subtitle | 32 |
| 2026Jan-Jun.xlsx | none | 248 |
| 2026Jan-Jun.xlsx | other | 2,065 |
| 2026Jan-Jun.xlsx | trailing number | 40 |
| 2026Jan-Jun.xlsx | contains ' // ' (second-language segment) | 3,030 |
| 2026Jan-Jun.xlsx | all series-or-unknown title rows | 8,193 |

### Examples across half-years (aggregate; title-level examples kept local, not published)
Columns of the local example table: base, file, full_title, notation, pattern, hours_viewed. 111 rows: 8 series bases, top 2 titles per file (15 rows for 2023Jan-Jun, 16 for each other file).
| pattern | rows |
|---|---|
| Season N | 95 |
| trailing number | 9 |
| none | 5 |
| other | 2 |
