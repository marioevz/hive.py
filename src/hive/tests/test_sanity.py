"""
Sanity tests for the Hive simulation framework.

Requirements
------------

Start a hive simulator in dev mode with an execution, beacon and validator
client:

```shell
./hive --dev --client go-ethereum,lighthouse-bn,lighthouse-vc --client-file \
    --docker.output
```
"""

import os
from re import match

import pytest

from hive.client import ClientRole
from hive.parameters import Parameter
from hive.simulation import Simulation
from hive.testing import HiveTestResult


@pytest.fixture
def sim():
    # TODO: Start hive in dev mode here
    yield Simulation(url="http://127.0.0.1:3000")
    # TODO: Clean it up here


def test_sanity(sim: Simulation):
    clients = sim.client_types()

    assert clients

    suite = sim.start_suite("my_test_suite", "my test suite description")

    assert suite is not None

    t = suite.start_test("my_test", "my test description")
    assert t is not None

    c1 = t.start_client(
        client_type=clients[0],
        environment={},
        files={
            "genesis.json": os.path.join("src", "hive", "tests", "genesis.json"),
        },
    )
    assert c1 is not None

    # Check enode
    enode = c1.enode()
    assert (
        match(r"enode://[0-9a-fA-F]{128}@\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+", str(enode))
        is not None
    )

    n = suite.create_network("my_network")

    n.connect_client(c1)

    c2 = t.start_client(
        client_type=clients[0],
        environment={
            Parameter.Bootnode: str(enode),
        },
        files={
            "genesis.json": os.path.join("src", "hive", "tests", "genesis.json"),
        },
    )

    n.connect_client(c2)

    t.end(result=HiveTestResult(test_pass=True, details="some details"))
    suite.end()


def test_clients_by_role(sim: Simulation):
    execution_clients = sim.client_types(role=ClientRole.ExecutionClient)
    assert len(execution_clients) == 1, "Expected 1 execution client, got {}".format(
        len(execution_clients)
    )

    beacon_clients = sim.client_types(role=ClientRole.BeaconClient)
    assert len(beacon_clients) == 1, "Expected 1 consensus client, got {}".format(
        len(beacon_clients)
    )

    validator_clients = sim.client_types(role=ClientRole.ValidatorClient)
    assert len(validator_clients) == 1, "Expected 1 validator client, got {}".format(
        len(validator_clients)
    )
