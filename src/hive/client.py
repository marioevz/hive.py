import json
from dataclasses import asdict, dataclass, field
from http import client
from io import BufferedReader, BytesIO
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Any, Dict, List, Mapping, Tuple

import requests


@dataclass(kw_only=True)
class ClientConfig:
    client: str
    networks: List[str] = field(default_factory=list)
    environment: Mapping[str, str] = field(default_factory=dict)


@dataclass(kw_only=True)
class ClientSetup:
    config: ClientConfig
    files: Mapping[str, str | bytes | BufferedReader] = field(default_factory=dict)

    def post_with_files(self, url) -> Tuple[int, Mapping[str, str] | str | None]:
        # Create the dictionary of files to send.
        files = {}
        for filename, open_fn_or_name in self.files.items():
            if isinstance(open_fn_or_name, bytes):
                open_fn_or_name = BytesIO(open_fn_or_name)  # type: ignore
            if isinstance(open_fn_or_name, str):
                open_fn_or_name = open(open_fn_or_name, "rb")
            assert isinstance(open_fn_or_name, BufferedReader)
            files["file"] = (filename, open_fn_or_name)

        # Send the request.
        response = requests.post(
            url,
            data={
                "config": json.dumps(asdict(self.config)),
            },
            files=files,
        )

        if response.status_code != client.OK:
            return response.status_code, None

        try:
            response_json = response.json()
            return response.status_code, response_json
        except Exception as e:
            return response.status_code, str(e)


@dataclass(kw_only=True)
class ClientType:
    name: str
    version: str
    meta: Dict[str, Any]


@dataclass(kw_only=True)
class ClientExecResult:
    stdout: str
    stderr: str
    exit_code: int

    def __post_init__(self):
        self.stdout = self.stdout.strip()
        self.stderr = self.stderr.strip()


@dataclass(kw_only=True)
class ClientEnode:
    id: str
    ip: IPv4Address | IPv6Address
    port: int

    @classmethod
    def from_string(cls, enode: str):
        prefix = "enode://"
        enode = enode.removeprefix(prefix)

        id, ip_port = enode.split("@")

        ip, port = ip_port.split(":")

        return cls(id=id, ip=ip_address(ip), port=int(port))

    def __str__(self) -> str:
        return f"enode://{self.id}@{self.ip}:{self.port}"

    def to_json(self):
        return str(self)


@dataclass(kw_only=True)
class Client:
    url: str
    type: ClientType
    id: str
    ip: str

    @classmethod
    def start(
        cls,
        url,
        client_type: ClientType,
        parameters: Mapping[str, str],
        files: Mapping[str, str | bytes | BufferedReader],
    ):
        client_config = ClientConfig(client=client_type.name, environment=parameters)
        setup = ClientSetup(
            config=client_config,
            files=files,
        )

        errcode, resp = setup.post_with_files(url)

        if resp is None or errcode != 200:
            return None

        assert not isinstance(resp, str)

        return cls(url=url, type=client_type, **resp)

    def stop(self):
        url = f"{self.url}/{self.id}"

        response = requests.delete(url)
        response.raise_for_status()
        return response.json()

    def pause(self):
        url = f"{self.url}/{self.id}/pause"

        response = requests.post(url)
        response.raise_for_status()
        return response.json()

    def unpause(self):
        url = f"{self.url}/{self.id}/pause"

        response = requests.delete(url)
        response.raise_for_status()
        return response.json()

    def exec(self, command: List[str]):
        url = f"{self.url}/{self.id}/exec"

        response = requests.post(url, json={"Command": command})
        response.raise_for_status()
        j = response.json()
        j["exit_code"] = j.pop("exitCode")
        return ClientExecResult(**j)

    def enode(self) -> ClientEnode:
        result = self.exec(["enode.sh"])
        assert result.exit_code == 0

        return ClientEnode.from_string(result.stdout)
