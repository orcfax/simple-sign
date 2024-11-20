"""Cardano handlers.

This is very much a work in progress aimed at a very small dApp where
the anticipated amount of data to be returned for a query is very
small. The concept of a backend is not really fleshed out either and
so remains unexported until an interface is implemented or some other
useful/interesting concept.
"""

import logging
from dataclasses import dataclass
from typing import Callable, Final, Optional

import cachetools.func
import pycardano as pyc
import pydantic
import requests


@dataclass
class ValidTx:
    slot: int
    tx_id: str
    address: str
    staking: str


logger = logging.getLogger(__name__)

BACKENDS: Final[list] = ["kupo"]


def _sum_dict(key: str, value: int, accumulator: dict):
    """Increment values in a given dictionary"""
    if key not in accumulator:
        accumulator[key] = value
        return accumulator
    count = accumulator[key]
    count = count + value
    accumulator[key] = count
    return accumulator


def _get_staking_from_addr(addr: str) -> str:
    """Return a staking address if possible from a given address,
    otherwise, return the original address string.
    """
    try:
        address = pyc.Address.from_primitive(addr)
        return str(
            pyc.Address(staking_part=address.staking_part, network=pyc.Network.MAINNET)
        )
    except pyc.exception.InvalidAddressInputException:
        return str(address)
    except TypeError as err:
        logger.error("cannot convert '%s' (%s)", addr, err)
        return str(addr)


class BackendContext:
    """Backend interfaces.

    NB. this will probably prove to be a naive implementation of this
    sort of thing, but lets see. Learning from PyCardano.
    """

    def _retrieve_unspent_utxos(self) -> dict:
        """Retrieve unspent utxos from the backend."""
        raise NotImplementedError()

    def retrieve_staked_holders(self, token_policy: str) -> list:
        """Retrieve a list of staked holders against a given CNT."""
        raise NotImplementedError()

    def retrieve_nft_holders(
        self, policy: str, deny_list: list, addr: str = None
    ) -> list:
        """Retrieve a list of NFT holders, e.g. a license to operate
        a decentralized node.
        """
        raise NotImplementedError()

    def retrieve_metadata(
        self, value: int, policy: str, tag: str, callback: Optional[Callable | None]
    ) -> list:
        """Retrieve metadata from the backend."""
        raise NotImplementedError()


class KupoContext(BackendContext):
    """Kupo backend."""

    def __init__(
        self,
        base_url: str,
        port: int,
    ):
        """Initialize this thing..."""
        self._base_url = base_url
        self._port = port

    @cachetools.func.ttl_cache(ttl=60)
    def _retrieve_unspent_utxos(self, addr: str = None) -> dict:
        """Retrieve unspent utxos from Kupo.

        NB. Kupo must be configured to capture sparingly, i.e. the
        policies and addresses it is watching and slot from which it is
        watching must be as specific as possible for this function to
        perform well.
        """
        kupo_err: Final[str] = "hint"
        request_string = f"{self._base_url}:{self._port}/matches?unspent"
        if addr:
            request_string = f"{self._base_url}:{self._port}/matches/{addr}?unspent"
        logger.info("requesting unspent: '%s'", request_string)
        resp = requests.get(request_string, timeout=30)
        ret = resp.json()
        if kupo_err in ret:
            logger.error("unable to retrieve data due to Kupo request error: %s", ret)
            return []
        return ret

    def _retrieve_metadata(self, tag: str, tx_list: list[ValidTx]):
        """Return metadata based on slot and transaction ID. This is
        very much a Kupo-centric approach. Metadata is not indexed
        locally and instead needs to be retrieved directly from
        a node.

        IMPORTANT: The metadata is modified here to provide information
        about the source address. This is so that the data remains
        accurately coupled with what is retrieved. We can't do this
        with Kupo easily otherwise.
        """
        md_list = []
        for tx in tx_list:
            resp = requests.get(
                f"{self._base_url}:{self._port}/metadata/{tx.slot}?transaction_id={tx.tx_id}",
                timeout=30,
            )
            if not resp.json():
                return md_list
            md_dict = resp.json()
            try:
                _ = md_dict[0]["schema"][tag]
            except (IndexError, KeyError):
                return md_list
            md_dict[0]["address"] = tx.address
            md_dict[0]["staking"] = tx.staking
            md_dict[0]["transaction"] = tx.tx_id
            md_list.append(md_dict[0])
        return md_list

    def retrieve_staked_holders(self, token_policy: str, addr: str = None) -> list:
        """Retrieve a list of staked holders against a given CNT."""
        unspent = self._retrieve_unspent_utxos()
        addresses_with_fact = {}
        for item in unspent:
            unspent_addr = item["address"]
            unspent_staking = _get_staking_from_addr(unspent_addr)
            if addr and addr not in (unspent_addr, unspent_staking):
                # don't process further than we have to if we're only
                # looking for a single address.
                continue
            staking = unspent_staking
            assets = item["value"]["assets"]
            for key, value in assets.items():
                if token_policy in key:
                    addresses_with_fact = _sum_dict(staking, value, addresses_with_fact)
        return addresses_with_fact

    def retrieve_nft_holders(
        self, policy: str, deny_list: list = None, addr: str = None
    ) -> list:
        """Retrieve a list of NFT holders, e.g. a license to operate
        a decentralized node.

        Filtering can be performed elsewhere, but a deny_list is used
        to remove some results that are unhelpful, e.g. the minting
        address if desired.
        """
        if addr:
            unspent = self._retrieve_unspent_utxos(addr)
        else:
            unspent = self._retrieve_unspent_utxos()
        holders = {}
        for item in unspent:
            unspent_addr = item["address"]
            unspent_staking = _get_staking_from_addr(unspent_addr)
            if addr and addr not in (unspent_addr, unspent_staking):
                # don't process further than we have to if we're only
                # looking for a single address.
                continue
            if deny_list and unspent_addr in deny_list:
                continue
            staking = unspent_staking
            assets = item["value"]["assets"]
            for key, _ in assets.items():
                if not key.startswith(policy):
                    continue
                holders[key] = staking
        return holders

    @staticmethod
    def _get_valid_txs(unspent: list[dict], value: int, policy: str) -> list[ValidTx]:
        """Retrieve a list of valid transactions according to our
        policy rules.
        """
        logger.info("getting valid txs for policy: '%s'", policy)
        valid_txs = []
        if not unspent:
            return valid_txs
        for item in unspent:
            coins = item["value"]["coins"]
            if coins != value:
                continue
            assets = item["value"]["assets"]
            for asset in assets:
                if policy not in asset:
                    continue
                slot = item["created_at"]["slot_no"]
                tx_id = item["transaction_id"]
                address = item["address"]
                valid_tx = ValidTx(
                    slot=slot,
                    tx_id=tx_id,
                    address=address,
                    staking=_get_staking_from_addr(address),
                )
                valid_txs.append(valid_tx)
        return valid_txs

    @pydantic.validate_call()
    def retrieve_metadata(
        self,
        value: int,
        policy: str,
        tag: str,
        callback: Optional[Callable | None],
    ) -> list:
        """Retrieve a list of aliased signing addresses. An aliased
        signing address is an address that has been setup using a
        protocol that allows NFT holders to participate in a network
        without having the key to their primary wallets hot/live on the
        decentralized node that they are operating.

        Kupo queries involved:

        ```sh
            curl -s "http://0.0.0.0:1442/matches?unspent"
            curl -s "http://0.0.0.0:1442/metadata/{slot_id}?transaction_id={}"
        ```

        Strategy 1: Retrieve all aliased keys for a policy ID.
                    Capture all values that match.
                    Capture all slots and tx ids for those values.
                    Retrieve metadata for all those txs.
                    Augment metadata with address and staking address.
                    Optionally, use the callback to process the data
                    according to a set of rules.
                    Return the metadata or a list of processed values to
                    the caller.

        NB. the callback must return a list to satisfy the output of the
        primary function.

        NB. this function is not as generic as it could be.

        """
        unspent = self._retrieve_unspent_utxos()
        valid_txs = self._get_valid_txs(unspent, value, policy)
        if not valid_txs:
            return valid_txs
        md = self._retrieve_metadata(tag, valid_txs)
        if not callback:
            return md
        return callback(md)
