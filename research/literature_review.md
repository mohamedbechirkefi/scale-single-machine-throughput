<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Literature review (M0 draft, not systematic)

This is a targeted, non-systematic review. It is not a systematic review and must not be described as one. Each entry states what was actually opened on 2026-11-24 and what was not.

Verification levels:
- **Read (full text):** the full text or a substantial part was opened.
- **Read (abstract/page):** the abstract or the publisher/author page was opened; the full text was not.
- **Metadata only:** bibliographic metadata checked through the Crossref API (`https://api.crossref.org/works/<DOI>`); content not read.
- **Unverified:** not opened; must not be cited as read.

## 1. Sources

| Key | Reference | Accessed via | Level | Relevance to SCALE |
|---|---|---|---|---|
| little1961 | J. D. C. Little, "A Proof for the Queuing Formula: L = λW", *Operations Research* 9(3):383-387, 1961. DOI 10.1287/opre.9.3.383 | Crossref API; publisher page returned HTTP 403 | Metadata only | Relates concurrency, throughput and response time; used as a consistency check (mean in-flight requests = throughput x mean latency in closed-loop cells) |
| schroeder2006 | B. Schroeder, A. Wierman, M. Harchol-Balter, "Open Versus Closed: A Cautionary Tale", NSDI 2006, USENIX. https://www.usenix.org/legacy/events/nsdi06/tech/full_papers/schroeder/schroeder_html/index.html | USENIX HTML full text | Read (full text, via summarising fetch) | Closed and open workload models can give very different response times under the same load; motivates EXP-003 |
| tene-wrk2 | G. Tene, wrk2 README, https://github.com/giltene/wrk2 (Apache-2.0) | GitHub page | Read (page) | Coordinated omission; constant-rate load with latency measured from the intended send time; motivates the open-loop design |
| mytkowicz2009 | T. Mytkowicz, A. Diwan, M. Hauswirth, P. F. Sweeney, "Producing Wrong Data Without Doing Anything Obviously Wrong!", ASPLOS 2009, pp. 265-276. DOI 10.1145/1508244.1508275 | Crossref API; author group page https://sape.inf.usi.ch/publications/asplos09 | Read (abstract/page) | Measurement bias from innocuous setup changes; motivates randomised arm order and the position check |
| georges2007 | A. Georges, D. Buytaert, L. Eeckhout, "Statistically Rigorous Java Performance Evaluation", OOPSLA 2007, pp. 57-76. DOI 10.1145/1297027.1297033 | Crossref API | Metadata only (its warm-up method is described in kalibera2013, which was read) | Warm-up and repetition methodology |
| kalibera2013 | T. Kalibera, R. Jones, "Rigorous Benchmarking in Reasonable Time", ISMM 2013, pp. 63-74. DOI 10.1145/2464157.2464160 | Author's accepted manuscript, Kent Academic Repository https://kar.kent.ac.uk/33611/ (PDF https://kar.kent.ac.uk/id/document/3127886) | Read (full text extracted locally; abstract and related-work sections read) | Repetition at the highest-variance level; effect-size confidence intervals for ratios |
| kalibera2020 | T. Kalibera, R. Jones, "Quantifying Performance Changes with Effect Size Confidence Intervals", arXiv:2007.10899 | arXiv abstract page | Read (abstract) | Ratio of means with uncertainty as the reporting unit; supports the R_j effect definition |
| dean2013 | J. Dean, L. A. Barroso, "The Tail at Scale", *Communications of the ACM* 56(2):74-80, 2013. DOI 10.1145/2408776.2408794 | Google Research listing https://research.google/pubs/pub40801/ ; Crossref API | Read (abstract) | Why p99 matters and why rare slow episodes dominate at high utilisation |
| gunther2008 | N. J. Gunther, "A General Theory of Computational Scalability Based on Rational Functions", arXiv:0808.1431, 2008 | arXiv abstract page | Read (abstract) | Universal Scalability Law; contention and coherency terms; descriptive fit of G(c) |
| gunther2011 | N. J. Gunther, S. Subramanyam, S. Parvu, "A Methodology for Optimizing Multithreaded System Scalability on Multi-cores", arXiv:1105.4301, 2011 | arXiv abstract page | Read (abstract) | USL applied to memcached and application servers on multi-core machines |
| gan2019 | Y. Gan et al., "An Open-Source Benchmark Suite for Microservices and Their Hardware-Software Implications for Cloud & Edge Systems" (DeathStarBench), ASPLOS 2019, pp. 3-18. DOI 10.1145/3297858.3304013 | Crossref API | Metadata only | Contrast: multi-service cloud benchmarks; SCALE is deliberately single-process and local |
| sqlite-copyright | SQLite copyright page, https://www.sqlite.org/copyright.html | Web page | Read (page) | Licence of the database engine (public domain) |
| hdrhistogram | HdrHistogram site, https://hdrhistogram.github.io/HdrHistogram/ | Web page | Read (page) | Latency histogram recording; CC0 dedication of the original work |

## 2. Synthesis (draft)

- **Measurement methodology is the main risk, not the mechanisms.** Mytkowicz et al. show that innocuous setup choices bias measurements; Kalibera and Jones recommend replicating at the level that carries most variance and reporting ratios with intervals. SCALE therefore replicates whole server processes and reports R_j with bootstrap intervals.
- **The load model can change the answer.** Schroeder et al. show that closed-loop generators yield much lower response times than open-loop ones at the same load, and that the benefit of scheduling changes between the two models. Tene's wrk2 documents coordinated omission in closed-loop latency measurement. SCALE uses closed loop for capacity (primary) and an open-loop, intended-time sensitivity experiment that can overturn the conclusion.
- **Saturation shape.** Little's law links in-flight requests, throughput and latency; Gunther's USL gives a two-parameter description of throughput versus concurrency. SCALE uses both descriptively, not as hypotheses.
- **Tail latency.** Dean and Barroso motivate reporting p99 and not only means.

## 3. Gap and intended contribution (narrow, not a novelty claim)

The mechanisms studied (caching, indexing, batching, admission control) are textbook. No novelty is claimed for them. The intended contribution is a small, fully reproducible, single-machine study that (a) measures all four factors against one simple baseline under one identical workload, (b) reports paired effect sizes with uncertainty across process restarts, and (c) states explicitly whether the ranking survives a change of load model and workload parameters. Whether such a combined, openly reproducible comparison already exists has **not** been established by this search; a further search at M1 is required before any claim about the gap is written in the manuscript.

## 4. Open items for M1

- Obtain and read the full texts of little1961 (or Little 2011, "Little's Law as Viewed on Its 50th Anniversary"), georges2007 and mytkowicz2009 if legally accessible.
- Search for prior single-machine comparisons of caching, indexing, batching and admission control (for example, SQLite performance documentation, admission control literature such as SEDA) and record each as read or unverified.
- Check the PSF licence statement for the Python standard library.
