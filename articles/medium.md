<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
<!-- Draft for Medium (master prompt 11.7). Not published; publication is the owner's decision (G-PUBLIC). Every number is printed in research/paper/manuscript.md. -->

# How much work can one computer actually handle? (working title, draft)

*Draft, not published. Author: [placeholder: author line, to be confirmed by the owner]. Independent research, not peer-reviewed.*

When a web service is too slow, the usual advice is a cache, an index, batching or a limit on concurrent work. Which one helps most depends on where the time goes in a particular system. This study asked the question for one small, fully specified system: a Python standard-library HTTP server backed by SQLite, on one laptop, on localhost, with a synthetic table of 200,000 rows.

## What was compared

A deliberately simple baseline answers every lookup with a full table scan. Four changes were each applied alone: an in-process cache (A1), an index (A2), read batching (A3) and bounded concurrency (A4). The protocol, the primary metric (peak goodput over a closed-loop concurrency sweep), the intervals and the decision rules were frozen by the owner before any confirmatory data existed. Ten paired blocks ran on a quiet machine.

## What was measured

- **Batching** raised peak goodput by a factor of 9.005 (98.75 % interval 8.921 to 9.093).
- **The cache** raised it by 2.337 (2.254 to 2.435).
- **Bounded concurrency** had no meaningful effect on the peak: 1.015 (1.000 to 1.030). The baseline peaks at four connections, below the admission limit, so the limiter never engages there.
- **The index** was too fast for the measurement harness: its peak sat on the load-generator ceiling in every block, so under the frozen rule it has no confirmatory estimate, and the question of which change dominates is **unresolved**.

## What it does not mean

Both winners are conditional on the full-scan baseline. Batching wins here largely because one scan serves a whole batch; that is not a general value of batching. The size of the batching advantage over the cache also depends on the summary metric: 3.85 under peak goodput, 1.58 under a closed-loop latency bound (both exploratory). An open-loop experiment and a workload-sensitivity experiment were planned and did not run. Nothing here transfers to production traffic or to other hardware.

## Still open

Four decisions are pending the owner: the reading of the frozen rule that excludes the index (the manuscript reports both the frozen-rule reading and exploratory alternatives, 246.8 and 90.8), the parameters of the open-loop experiment, whether the workload experiment runs, and whether the raw run outputs stay committed.

The manuscript, the experiment reports and an offline interactive page with every number and its interval are in the repository: [placeholder: repository URL, not published; publication requires the owner's approval].

*AI assistance: an AI system (Claude, Anthropic) assisted with code, analysis and drafting; it is not an author. Funding: [placeholder: funding statement, to be supplied by the owner]. Competing interests: [placeholder: competing-interests statement, to be supplied by the owner].*
