"""Test the functions looking at what's on-chain."""

# pylint: disable=W0212,R0903,C0103

import json
from typing import Final

import pycardano as pyc

from src.simple_sign.backend import KupoContext, ValidTx, _get_staking_from_addr
from src.simple_sign.types import Alias

tx_data: Final[
    dict
] = """
[
  {
    "transaction_index": 19,
    "transaction_id": "791c3d699f1236a227edd611dc6408034523b98858cd15b4b495415c2835a242",
    "output_index": 0,
    "address": "addr1qy0pwlnkznxhq50fhwh8ac90c0yt54n6y9krg054daehxzqgp4e92w5qwg3jlp6xqyfh7hxrwv74gu3t6awu0v84vhmszrx6vt",
    "value": {
      "coins": 1233712,
      "assets": {
        "5e43f3c51d80434a0be558da4272f189ea1a36f4d8b5165da7ca1e60.427569646c657246657374303235": 1
      }
    },
    "datum_hash": null,
    "script_hash": null,
    "created_at": {
      "slot_no": 139250846,
      "header_hash": "af3249be9a3bc21b6a98cc57e693c17ec2afbe50b7bc5e1da5ece75312f83d87"
    },
    "spent_at": null
  },
  {
    "transaction_index": 16,
    "transaction_id": "2c53ca6f6848870d9a872f7fdbfb56ea9fd05d57d92445f460b62167ea3cca7f",
    "output_index": 0,
    "address": "addr1q983mnp8yhmga4h0wz8ha9eaxdpusx7dp36ca6y3jd2nyly00f3ztshzchqy4rt5tcqtprvr38f56u9h46wlthvd9a2s6rw6vc",
    "value": {
      "coins": 1611940,
      "assets": {
        "84063e20b788729b48e6455b1f97062d54b15114c37aeda24fd27c0e.454d5552474f2078204e4d4b522053756d6d69742023343233": 1,
        "5e43f3c51d80434a0be558da4272f189ea1a36f4d8b5165da7ca1e60.427569646c657246657374313139": 1,
        "5964c3813d1abae676a8d88547d73a842f62576befc7b93753c12c2c.4353595032343239": 1
      }
    },
    "datum_hash": null,
    "script_hash": null,
    "created_at": {
      "slot_no": 139161268,
      "header_hash": "a29abdc22c9f89f891709330bd6965b4c647de73a996c517952366c9c95e71bf"
    },
    "spent_at": null
  }
]
"""

md_data = """
[
  {
    "address": "addr123",
    "staking": "stake123",
    "transaction": "tx123",
    "hash": "2e8dde3ec1e295abb4ff18491658c04b1ade5329f13967d391f91e42eca07047",
    "raw": "a11902a2a1636d7367836852454749535445526349544e7839303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303020",
    "schema": {
      "674": {
        "map": [
          {
            "k": {
              "string": "msg"
            },
            "v": {
              "list": [
                {
                  "string": "REGISTER"
                },
                {
                  "string": "ITN"
                },
                {
                  "string": "00000000000000000000000000000000000000000000000000000000 "
                }
              ]
            }
          }
        ]
      }
    }
  }
]
"""


def my_callable(md: list[dict]) -> list[Alias]:
    """A function to use to test callbacks in the backend."""
    addresses = []
    for item in md:
        assert (
            "address" in item
        ), "metadata dictionary should have been augmented with address"
        assert (
            "staking" in item
        ), "metadata dictionary should have been augmented with staking"
        try:
            value = item["schema"]["674"]["map"][0]["v"]["list"]
        except KeyError:
            continue
        try:
            action = value[0]["string"]
            project = value[1]["string"]
            vkh = value[2]["string"]
        except IndexError:
            continue
        try:
            if (
                action.upper().strip() != "REGISTER"
                and project.upper().strip() != "ITN"
            ):
                continue
        except ValueError:
            continue
        try:
            network = pyc.Network.MAINNET
            verification_key_hash = pyc.VerificationKeyHash.from_primitive(vkh)
            address = pyc.Address(verification_key_hash, network=network)
            addresses.append(
                Alias(
                    alias=str(address),
                    address=item["address"],
                    staking=item["staking"],
                    tx=item["transaction"],
                )
            )
        except ValueError:
            continue
    return addresses


class MockMetadataResponse:
    """Mock requests response for our requests functions."""

    @staticmethod
    def json():
        """Return a dictionary representation of our data."""
        return json.loads(md_data)


def test_get_valid_tx_private():
    """Ensure that our processing of valid transactions is doing
    something sensible.
    """
    value = 1233712
    policy = "5e43f3c51d80434a0be558da4272f189ea1a36f4d8b5165da7ca1e60"
    context = KupoContext("mock_address", 9999)
    valid_txs = context._get_valid_txs(json.loads(tx_data), value, policy)
    assert len(valid_txs) == 1
    assert valid_txs == [
        ValidTx(
            slot=139250846,
            tx_id="791c3d699f1236a227edd611dc6408034523b98858cd15b4b495415c2835a242",
            address="addr1qy0pwlnkznxhq50fhwh8ac90c0yt54n6y9krg054daehxzqgp4e92w5qwg3jlp6xqyfh7hxrwv74gu3t6awu0v84vhmszrx6vt",
            staking="stake1uyyq6uj482q8yge0sarqzymltnphx025wg4awhw8kr6ktacaez36t",
        )
    ]


def test_retrieve_metadata_private(mocker):
    """Test our mocked function below to ensure that it is being
    sensible.
    """
    context = KupoContext("mock_address", 9999)
    mocker.patch("requests.get", return_value=MockMetadataResponse())
    resp = context._retrieve_metadata(
        "674",
        [
            ValidTx(
                123,
                "tx123",
                "addr123",
                "stake123",
            )
        ],
    )
    assert isinstance(resp, list)
    assert resp[0]["address"] == "addr123"
    assert resp[0]["staking"] == "stake123"


def test_retrieve_metadata_private_fail(mocker):
    """Test our mocked function below to ensure that it is being
    sensible. In this test the metadata label is incorrect.
    """
    context = KupoContext("mock_address", 9999)
    mocker.patch("requests.get", return_value=MockMetadataResponse())
    resp = context._retrieve_metadata(
        "675",
        [
            ValidTx(
                123,
                "tx123",
                "addr123",
                "stake123",
            )
        ],
    )
    assert len(resp) == 0 and isinstance(resp, list)


def test_aliased_signing_addresses(mocker):
    """Ensure we can trace aliased addresses. This test provides
    somewhat of an integration test and so other smaller units need
    testing independently, e.g. metadata retrieval.
    """
    context = KupoContext("mock_address", 9999)
    mocker.patch(
        "src.simple_sign.backend.KupoContext._retrieve_unspent_utxos",
        return_value=json.loads(tx_data),
    )
    mocker.patch(
        "src.simple_sign.backend.KupoContext._retrieve_metadata",
        return_value=json.loads(md_data),
    )
    md_output = context.retrieve_metadata(
        value=1233712,
        policy="5e43f3c51d80434a0be558da4272f189ea1a36f4d8b5165da7ca1e60",
        tag="674",
        callback=my_callable,
    )
    assert md_output == [
        Alias(
            alias="addr1vyqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqkdl5mw",
            address="addr123",
            staking="stake123",
            tx="tx123",
        )
    ]


def test_get_staking_addr_behavior():
    """Make sure we are handling exceptions if we search for a staking
    address instead of a spending or enterprise address.
    """
    test_staking: Final[
        str
    ] = "stake1uyyq6uj482q8yge0sarqzymltnphx025wg4awhw8kr6ktacaez36t"
    res = _get_staking_from_addr(test_staking)
    assert res == test_staking
