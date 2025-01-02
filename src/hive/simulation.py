import os
from typing import List

import requests

from .client import ClientRole, ClientType
from .testing import HiveTestSuite

# from enode import enode


class Simulation:
    url: str

    def __init__(self, url: str | None = None):
        if not url:
            url = os.getenv("HIVE_SIMULATOR")
            if not url:
                raise ValueError("HIVE_SIMULATOR environment variable not set")

        """
        p = os.getenv("HIVE_TEST_PATTERN")
        if p:
            m = parse_test_pattern(p)
            self.m = m
        """

        self.url = url

    """
    def set_test_pattern(self, p):
        m = parse_test_pattern(p)
        self.m = m

    def test_pattern(self):
        se = self.m.suite.String() if self.m.suite else ""
        te = self.m.test.String() if self.m.test else ""
        return se, te
    """

    def start_suite(self, name: str, description: str) -> HiveTestSuite:
        url = f"{self.url}/testsuite"
        return HiveTestSuite.start(url=url, name=name, description=description)

    def client_types(self, *, role: ClientRole | None = None) -> List[ClientType]:
        url = f"{self.url}/clients"
        response = requests.get(url)
        response.raise_for_status()
        client_list = response.json()
        assert isinstance(client_list, list)
        clients = [ClientType(**x) for x in client_list]
        if role:
            return [c for c in clients if role in c.roles()]
        return clients

    def hive_instance(self) -> dict:
        """Return information about the Hive instance."""
        url = f"{self.url}/hive"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()