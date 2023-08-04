from dataclasses import asdict, dataclass
from io import BufferedReader
from typing import Mapping

import requests

from .client import Client, ClientType
from .network import Network


@dataclass(kw_only=True)
class HiveTestSuite:
    url: str
    name: str
    description: str
    id: int

    @classmethod
    def start(cls, url: str, name: str, description: str) -> "HiveTestSuite":
        req = {"Name": name, "Description": description}
        response = requests.post(url, json=req)
        response.raise_for_status()
        id = response.json()
        return cls(url=f"{url}/{id}", name=name, description=description, id=id)

    def end(self):
        response = requests.delete(self.url)
        response.raise_for_status()

    def start_test(self, name: str, description: str) -> "HiveTest":
        url = f"{self.url}/test"
        return HiveTest.start(url=url, name=name, description=description)

    def create_network(self, name):  # -> Network:
        url = f"{self.url}/network"
        return Network.create(url=url, name=name)


@dataclass(kw_only=True)
class HiveTestResult:
    test_pass: bool
    details: str

    def to_dict(self):
        d = asdict(self)
        d["pass"] = d.pop("test_pass")
        return d


@dataclass(kw_only=True)
class HiveTest:
    url: str
    name: str
    description: str
    id: int

    @classmethod
    def start(cls, url: str, name: str, description: str) -> "HiveTest":
        req = {"Name": name, "Description": description}
        response = requests.post(url, json=req)
        response.raise_for_status()
        id = response.json()
        return cls(url=f"{url}/{id}", name=name, description=description, id=id)

    def end(self, result: HiveTestResult):
        response = requests.post(self.url, json=result.to_dict())
        response.raise_for_status()

    def start_client(
        self,
        client_type: ClientType,
        parameters: Mapping[str, str],
        files: Mapping[str, str | bytes | BufferedReader],
    ) -> Client | None:
        url = f"{self.url}/node"
        return Client.start(url=url, client_type=client_type, parameters=parameters, files=files)
