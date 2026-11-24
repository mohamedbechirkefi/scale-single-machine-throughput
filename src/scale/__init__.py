# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""SCALE: single-machine study of what bottlenecks dominate local request throughput.

Modules are kept separate as master prompt section 4 requires:
``data`` (ingestion: synthetic dataset and request streams), ``server``
(system under test, arms A0 to A4), ``loadgen`` (load generation),
``metrics`` (pure metric and statistics functions), ``runner``
(experiment orchestration), ``schema`` and ``manifest`` (result
serialisation and provenance), ``report`` (tables, figures, PDF) and
``cli`` (command line).
"""

__version__ = "0.1.0"
