<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
<!-- Draft for LinkedIn (master prompt 11.7). Not published; publication is the owner's decision (G-PUBLIC). Every number is printed in research/paper/manuscript.md. -->

**Draft, not published.**

Cache, index, batching or admission control: which one moves peak throughput most?

I tested this on one laptop, with one Python and SQLite server and a protocol frozen before any confirmatory data. Against a full-scan baseline, read batching raised peak goodput by a factor of 9.005 (98.75 % interval 8.921 to 9.093) and a cache by 2.337 (2.254 to 2.435); bounded concurrency left the peak unchanged. The index reached the measurement ceiling, so which change dominates is unresolved.

The narrow lesson: the remedies that won are the ones that share or remove this system's dominant cost, the full scan. It is one machine and one synthetic workload, not production traffic, and the paper is a preprint draft, not peer-reviewed.

Manuscript, reports and an offline interactive page: https://github.com/mohamedbechirkefi/scale-single-machine-throughput.
