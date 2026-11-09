# Track B — top 20 candidates (highest reduced proper motion)

Harvest: full-sky Gaia DR3 high-PM scan (|pm|>150 mas/yr, G<20, RUWE<1.4,
parallax measured) via gaia.aip.de sync TAP in 4096 source_id chunks
(scripts/aip_chunked.py + aip_parallel.py, merged by merge_chunks.py).
Exclusions: GCNS (I/364/gcns), Kirkpatrick+2024 20-pc census, SIMBAD
LM*/BD*/SD*/WD* otypes (results/known/). Vetting: bp_rp>2.5,
H=G+5*log10(pm)>16 — ultracool-dwarf-like.

Nearest-known cones: 5 arcmin around each candidate (SIMBAD basic and
GCNS gcns.main, both via TAP). Cutouts: Legacy Survey DR9 jpeg 200px.

Rank | source_id | ra,dec | pm_tot | dist(pc) | G | bp_rp | H |
---|---|---|---|---|---|---|---|
1 | [3264554308968041728](#1-gaia-dr3-3264554308968041728) | 53.46488, 0.23476 | 775.1 | 116.9 | 19.90 | 3.18 | 19.35 |
2 | [3638565726166191232](#2-gaia-dr3-3638565726166191232) | 203.00313, -1.31872 | 725.0 | 162.3 | 19.72 | 2.64 | 19.02 |
3 | [3740981802614077568](#3-gaia-dr3-3740981802614077568) | 207.84099, 14.32036 | 576.5 | 127.0 | 19.95 | 2.95 | 18.76 |
4 | [1809891423169666816](#4-gaia-dr3-1809891423169666816) | 303.82301, 17.19514 | 665.2 | 142.0 | 19.56 | 3.67 | 18.68 |
5 | [1463461422659323904](#5-gaia-dr3-1463461422659323904) | 198.73773, 31.19487 | 611.7 | 131.3 | 19.66 | 3.12 | 18.59 |
6 | [3548393270038567296](#6-gaia-dr3-3548393270038567296) | 174.49991, -16.01558 | 481.1 | 147.6 | 19.99 | 2.58 | 18.4 |
7 | [906542492378786304](#7-gaia-dr3-906542492378786304) | 120.75475, 35.81137 | 502.2 | 271.2 | 19.86 | 2.57 | 18.37 |
8 | [6240254230280713088](#8-gaia-dr3-6240254230280713088) | 235.74492, -22.62963 | 480.4 | 147.0 | 19.93 | 2.80 | 18.34 |
9 | [3869943830673393024](#9-gaia-dr3-3869943830673393024) | 159.31678, 9.61718 | 577.9 | 151.7 | 19.46 | 3.22 | 18.27 |
10 | [3420227975592039936](#10-gaia-dr3-3420227975592039936) | 75.03441, 25.69834 | 582.5 | 122.5 | 19.43 | 2.95 | 18.26 |
11 | [5835238195852046592](#11-gaia-dr3-5835238195852046592) | 244.46708, -56.95686 | 515.0 | 173.6 | 19.70 | 2.75 | 18.26 |
12 | [2562041008170889728](#12-gaia-dr3-2562041008170889728) | 25.63399, 5.39054 | 629.9 | 113.5 | 19.24 | 2.98 | 18.23 |
13 | [4086649807215629440](#13-gaia-dr3-4086649807215629440) | 285.00670, -18.23545 | 514.3 | 122.0 | 19.67 | 3.50 | 18.23 |
14 | [6367552422370018304](#14-gaia-dr3-6367552422370018304) | 296.86790, -74.87956 | 472.6 | 121.5 | 19.85 | 2.87 | 18.22 |
15 | [1097667063876844672](#15-gaia-dr3-1097667063876844672) | 125.63364, 70.12469 | 446.7 | 188.2 | 19.96 | 2.63 | 18.21 |
16 | [4326332346950551040](#16-gaia-dr3-4326332346950551040) | 252.04205, -15.04466 | 462.7 | 142.5 | 19.86 | 2.83 | 18.19 |
17 | [3472658737319673984](#17-gaia-dr3-3472658737319673984) | 181.73980, -31.20580 | 534.1 | 156.2 | 19.53 | 2.71 | 18.16 |
18 | [6525740225409416192](#18-gaia-dr3-6525740225409416192) | 352.48967, -50.82096 | 514.3 | 149.6 | 19.60 | 2.92 | 18.16 |
19 | [1932719409002896896](#19-gaia-dr3-1932719409002896896) | 341.71247, 41.23373 | 544.6 | 119.6 | 19.43 | 3.21 | 18.11 |
20 | [4941408733596257152](#20-gaia-dr3-4941408733596257152) | 29.97354, -47.87038 | 471.6 | 152.8 | 19.72 | 2.85 | 18.08 |

### 1. Gaia DR3 3264554308968041728
- position: 53.464875 0.234763  ·  pm_tot 775.1 mas/yr  ·  dist 116.9 pc  ·  G 19.90  ·  bp_rp 3.18  ·  H 19.35  ·  RUWE 0.982
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=53.46487500162021&dec=0.23476270902315283&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: ULAS J033350.84+001406.1 (BD*) at 0.21 arcmin — LIKELY SAME OBJECT (separation matches the ~12.4 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 2. Gaia DR3 3638565726166191232
- position: 203.003134 -1.318716  ·  pm_tot 725.0 mas/yr  ·  dist 162.3 pc  ·  G 19.72  ·  bp_rp 2.64  ·  H 19.02  ·  RUWE 1.022
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=203.00313402419442&dec=-1.3187160074928257&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J13320118-0118568 (PM*) at 0.19 arcmin — LIKELY SAME OBJECT (separation matches the ~11.6 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); nearest GCNS: 3638560954457699200 at 3.66 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 3. Gaia DR3 3740981802614077568
- position: 207.840987 14.320357  ·  pm_tot 576.5 mas/yr  ·  dist 127.0 pc  ·  G 19.95  ·  bp_rp 2.95  ·  H 18.76  ·  RUWE 1.120
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=207.84098739043338&dec=14.32035652898641&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J13512249+1419168 (LM*) at 0.15 arcmin — LIKELY SAME OBJECT (separation matches the ~9.2 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 4. Gaia DR3 1809891423169666816
- position: 303.823013 17.195138  ·  pm_tot 665.2 mas/yr  ·  dist 142.0 pc  ·  G 19.56  ·  bp_rp 3.67  ·  H 18.68  ·  RUWE 1.227
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=303.8230130309377&dec=17.19513806354425&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J20151779+1711528 (PM*) at 0.18 arcmin — LIKELY SAME OBJECT (separation matches the ~10.6 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 5. Gaia DR3 1463461422659323904
- position: 198.737732 31.194866  ·  pm_tot 611.7 mas/yr  ·  dist 131.3 pc  ·  G 19.66  ·  bp_rp 3.12  ·  H 18.59  ·  RUWE 0.993
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=198.73773231899918&dec=31.194865815663185&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J13145778+3111424 (PM*) at 0.16 arcmin — LIKELY SAME OBJECT (separation matches the ~9.8 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 6. Gaia DR3 3548393270038567296
- position: 174.499914 -16.015580  ·  pm_tot 481.1 mas/yr  ·  dist 147.6 pc  ·  G 19.99  ·  bp_rp 2.58  ·  H 18.4  ·  RUWE 1.042
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=174.4999136604724&dec=-16.0155797961285&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: Gaia DR3 3548393270038567296 (PM*) at 0.13 arcmin — LIKELY SAME OBJECT (separation matches the ~7.7 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 7. Gaia DR3 906542492378786304
- position: 120.754753 35.811373  ·  pm_tot 502.2 mas/yr  ·  dist 271.2 pc  ·  G 19.86  ·  bp_rp 2.57  ·  H 18.37  ·  RUWE 0.962
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=120.75475282353541&dec=35.8113732626522&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: SDSS J080301.11+354848.5 (LM*) at 0.13 arcmin — LIKELY SAME OBJECT (separation matches the ~8.0 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 8. Gaia DR3 6240254230280713088
- position: 235.744916 -22.629629  ·  pm_tot 480.4 mas/yr  ·  dist 147.0 pc  ·  G 19.93  ·  bp_rp 2.80  ·  H 18.34  ·  RUWE 1.104
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=235.74491592725505&dec=-22.62962890872988&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J15425932-2237429 (PM*) at 0.13 arcmin — LIKELY SAME OBJECT (separation matches the ~7.7 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 9. Gaia DR3 3869943830673393024
- position: 159.316783 9.617182  ·  pm_tot 577.9 mas/yr  ·  dist 151.7 pc  ·  G 19.46  ·  bp_rp 3.22  ·  H 18.27  ·  RUWE 1.166
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=159.31678337587712&dec=9.617182443335814&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J10371664+0937043 (PM*) at 0.15 arcmin — LIKELY SAME OBJECT (separation matches the ~9.2 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 10. Gaia DR3 3420227975592039936
- position: 75.034406 25.698338  ·  pm_tot 582.5 mas/yr  ·  dist 122.5 pc  ·  G 19.43  ·  bp_rp 2.95  ·  H 18.26  ·  RUWE 1.024
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=75.03440614116737&dec=25.69833774230821&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: Gaia DR3 3420227975592039936 (PM*) at 0.16 arcmin — LIKELY SAME OBJECT (separation matches the ~9.3 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 11. Gaia DR3 5835238195852046592
- position: 244.467083 -56.956859  ·  pm_tot 515.0 mas/yr  ·  dist 173.6 pc  ·  G 19.70  ·  bp_rp 2.75  ·  H 18.26  ·  RUWE 0.977
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=244.4670826384759&dec=-56.95685949000824&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: Gaia DR3 5835238195852046592 (PM*) at 0.14 arcmin — LIKELY SAME OBJECT (separation matches the ~8.2 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 12. Gaia DR3 2562041008170889728
- position: 25.633994 5.390538  ·  pm_tot 629.9 mas/yr  ·  dist 113.5 pc  ·  G 19.24  ·  bp_rp 2.98  ·  H 18.23  ·  RUWE 1.140
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=25.63399381917304&dec=5.390537719216943&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J01423153+0523285 (LM*) at 0.17 arcmin — LIKELY SAME OBJECT (separation matches the ~10.1 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 13. Gaia DR3 4086649807215629440
- position: 285.006699 -18.235451  ·  pm_tot 514.3 mas/yr  ·  dist 122.0 pc  ·  G 19.67  ·  bp_rp 3.50  ·  H 18.23  ·  RUWE 1.049
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=285.0066988977573&dec=-18.235450940669804&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J19000173-1814000 (PM*) at 0.14 arcmin — LIKELY SAME OBJECT (separation matches the ~8.2 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 14. Gaia DR3 6367552422370018304
- position: 296.867897 -74.879564  ·  pm_tot 472.6 mas/yr  ·  dist 121.5 pc  ·  G 19.85  ·  bp_rp 2.87  ·  H 18.22  ·  RUWE 1.067
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=296.86789734756314&dec=-74.87956414312148&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J19472782-7452391 (PM*) at 0.13 arcmin — LIKELY SAME OBJECT (separation matches the ~7.6 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 15. Gaia DR3 1097667063876844672
- position: 125.633643 70.124690  ·  pm_tot 446.7 mas/yr  ·  dist 188.2 pc  ·  G 19.96  ·  bp_rp 2.63  ·  H 18.21  ·  RUWE 1.024
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=125.63364339824899&dec=70.12469027736012&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J08223291+7007350 (PM*) at 0.12 arcmin — LIKELY SAME OBJECT (separation matches the ~7.1 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 16. Gaia DR3 4326332346950551040
- position: 252.042046 -15.044657  ·  pm_tot 462.7 mas/yr  ·  dist 142.5 pc  ·  G 19.86  ·  bp_rp 2.83  ·  H 18.19  ·  RUWE 1.049
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=252.04204579687152&dec=-15.044656800682914&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J16481055-1502377 (PM*) at 0.12 arcmin — LIKELY SAME OBJECT (separation matches the ~7.4 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 17. Gaia DR3 3472658737319673984
- position: 181.739803 -31.205797  ·  pm_tot 534.1 mas/yr  ·  dist 156.2 pc  ·  G 19.53  ·  bp_rp 2.71  ·  H 18.16  ·  RUWE 0.971
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=181.7398034642882&dec=-31.205797063811865&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J12065803-3112274 (PM*) at 0.14 arcmin — LIKELY SAME OBJECT (separation matches the ~8.5 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 18. Gaia DR3 6525740225409416192
- position: 352.489670 -50.820959  ·  pm_tot 514.3 mas/yr  ·  dist 149.6 pc  ·  G 19.60  ·  bp_rp 2.92  ·  H 18.16  ·  RUWE 0.983
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=352.4896696631619&dec=-50.82095924044578&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J23295728-5049079 (PM*) at 0.14 arcmin — LIKELY SAME OBJECT (separation matches the ~8.2 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 19. Gaia DR3 1932719409002896896
- position: 341.712470 41.233729  ·  pm_tot 544.6 mas/yr  ·  dist 119.6 pc  ·  G 19.43  ·  bp_rp 3.21  ·  H 18.11  ·  RUWE 1.013
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=341.71246989515856&dec=41.23372884028572&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J22465016+4114009 (PM*) at 0.15 arcmin — LIKELY SAME OBJECT (separation matches the ~8.7 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery

### 20. Gaia DR3 4941408733596257152
- position: 29.973536 -47.870383  ·  pm_tot 471.6 mas/yr  ·  dist 152.8 pc  ·  G 19.72  ·  bp_rp 2.85  ·  H 18.08  ·  RUWE 1.077
- cutout: <https://www.legacysurvey.org/viewer/jpeg-cutout?ra=29.9735357811094&dec=-47.87038267735997&layer=ls-dr9&size=200>
- nearest known: nearest SIMBAD: 2MASS J01595286-4752136 (PM*) at 0.13 arcmin — LIKELY SAME OBJECT (separation matches the ~7.5 arcsec epoch-2000→2016 proper-motion offset; Simbad lacks the Gaia DR3 cross-id, so source-id exclusion missed it); no GCNS source within 5 arcmin
- verdict: pre-Gaia-designation object missing its Gaia DR3 cross-id in SIMBAD — recovery, not discovery
