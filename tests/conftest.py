# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Shared fixtures: small synthetic databases and in-process servers (loopback only)."""

import os

import pytest

from scale.config import Workload
from scale.data import build_database
from scale.server import serve_in_thread

SMALL = Workload(rows=2000, payload_bytes=64, dataset_seed=7)


@pytest.fixture(scope="session")
def small_dbs(tmp_path_factory):
    d = tmp_path_factory.mktemp("db")
    plain = str(d / "plain.sqlite")
    indexed = str(d / "indexed.sqlite")
    build_database(plain, SMALL, index=False)
    build_database(indexed, SMALL, index=True)
    return {"plain": plain, "indexed": indexed}


@pytest.fixture
def fresh_db(tmp_path):
    """A fresh writable copy per test, built by the generator (never shared state)."""

    def make(index: bool = False, workload: Workload = SMALL) -> str:
        p = str(tmp_path / f"db-{index}-{workload.rows}.sqlite")
        if not os.path.exists(p):
            build_database(p, workload, index=index)
        return p

    return make


@pytest.fixture
def server_factory(fresh_db):
    started = []

    def make(arm: str, workload: Workload = SMALL, **kw):
        from scale.config import ARMS

        db = fresh_db(index=ARMS[arm].index, workload=workload)
        srv, th = serve_in_thread(arm, db, workload.rows, **kw)
        started.append(srv)
        return srv

    yield make
    for srv in started:
        srv.shutdown()
        srv.server_close()
