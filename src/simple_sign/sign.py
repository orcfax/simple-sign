"""Orcfax simple sign."""

# pylint: disable=W0613

import argparse
import logging
import os
import sys
import time
from typing import Final

import pycardano as pyc

try:
    from src.simple_sign.version import get_version
except ModuleNotFoundError:
    try:
        from version import get_version
    except ModuleNotFoundError:
        from simple_sign.version import get_version

# Set up logging.
logging.basicConfig(
    format="%(asctime)-15s %(levelname)s :: %(filename)s:%(lineno)s:%(funcName)s() :: %(message)s",  # noqa: E501
    datefmt="%Y-%m-%d %H:%M:%S",
    level="INFO",
    handlers=[
        logging.StreamHandler(),
    ],
)

# Format logs using UTC time.
logging.Formatter.converter = time.gmtime


logger = logging.getLogger(__name__)


KNOWN_SIGNERS_CONFIG: Final[str] = "CIP8_NOTARIES"
KUPO_URL: Final[str] = "KUPO_URL_NOTARIES"


class UnknownSigningKey(Exception):
    """Exception to raise when the signing key is unknown."""


def retrieve_aliased(pkey: str) -> str:
    """Retrieve another public key aliased by the given lookup.

    The result might then be used to verify using one of the other
    methods in this library, e.g.

    1. lookup aliased staking key.
    2. lookup staking key in license pool.
    3. if not exists, raise exception, else, pass.

    We want to do this on an address by address basis. The difficulty
    is consistent parsing of metadata that allows this function to be
    broadly applicable across functions.
    """
    raise NotImplementedError("reading staked values is not yet implemented")


def signature_belongs_to_staked_pool(
    pkey: str, token_policy_id: str, min_stake: int
) -> bool:
    """Validate whether the signing key belongs to a someone who has
    enough stake in a given token.
    """
    raise NotImplementedError("reading staked values is not yet implemented")


def signature_in_license_pool(pkey: str, policy_id: str) -> bool:
    """Validate whether signing key matches one of those in a pool of
    licenses associated with the project and return True if so.
    """
    raise NotImplementedError("reading from license pool is not yet implemented")


def signature_in_constitution_datum_utxo(pkey: str) -> bool:
    """Validate whether signing key matches one of those a list of
    addresses in a given constitution UTxO.
    """
    raise NotImplementedError("reading from datum is not yet implemented")


def signature_in_constitution_config(pkey: str) -> bool:
    """Validate whether signing key matches one of those listed in a
    configuration file.
    """
    raise NotImplementedError(
        "reading from a constitution config is not yet implemented"
    )


def retrieve_env_notaries() -> list:
    """Retrieve notaries from the environment."""
    notaries_env = os.getenv(KNOWN_SIGNERS_CONFIG, "")
    if not notaries_env:
        return []
    return [notary.strip() for notary in notaries_env.split(",")]


def signature_in_dapp_environment(pkey: str) -> bool:
    """Validate whether signing key matches one of those configured in
    the environment of the dApp.

    Largely a method for early prototyping. This isn't the most secure
    approach to doing this and especially not for use in decentralized
    systems. This check is only for projects with complete control over
    their own project.
    """
    notaries = retrieve_env_notaries()
    if pkey.strip() not in notaries:
        raise UnknownSigningKey(f"{pkey} is an unknown key")
    return True


def sign_with_key(data: str, signing_key: str) -> str:
    """Sign with an signing key."""
    skey = pyc.SigningKey.from_json(signing_key)
    vkey = pyc.VerificationKey.from_signing_key(skey)
    logger.info("signing with addr: %s", pyc.Address(vkey.hash()))
    return pyc.sign(data, skey)


def signing_handler(data: str, signing_key: str) -> str:
    """Handle signing functions."""
    return sign_with_key(data, signing_key)


def verify_signature(data: str) -> dict:
    """Verify a signature with an address."""
    try:
        status = pyc.verify(data)
    except (TypeError, ValueError) as err:
        # Message might not be invalid signed-CBOR or simply unexpected
        # data.
        logger.info("cannot decode message: %s'' (%s)", data, err)
        return {
            "verified": False,
            "message": None,
            "signing_address": None,
        }
    # Message from pycardano does not treat address as a string.
    return {
        "verified": status["verified"],
        "message": f"{status['message']}",
        "signing_address": f"{status['signing_address']}",
    }


def verify_handler(data: str) -> dict:
    """Verify input data."""
    return verify_signature(data)


def main() -> None:
    """Primary entry point for this script.

    Useful article on sub-commands (which are strangely harder than they should be):

    ```text
        https://dev.to/taikedz/ive-parked-my-side-projects-3o62
    ```

    """
    arg_sign: Final[str] = "sign"
    arg_verify: Final[str] = "verify"
    arg_version: Final[str] = "version"
    parser = argparse.ArgumentParser(
        prog="simple signer",
        description="provides helper functions signing simple data using Cardano primitives",
        epilog="for more information visit https://orcfax.io/",
    )
    subparsers = parser.add_subparsers(dest="cmd")
    verify = subparsers.add_parser(arg_verify)
    sign = subparsers.add_parser(arg_sign)
    subparsers.add_parser(arg_version)
    verify.add_argument("-d", "--data", type=str, help="data to verify")
    verify.add_argument(
        "-l",
        "--list-env",
        action="store_true",
        help=f"list known notaries in the environment at {KNOWN_SIGNERS_CONFIG}",
    )
    sign.add_argument("-d", "--data", type=str, help="data to sign")
    sign.add_argument("-s", "--signing_key", type=str, help="signing key")
    args = parser.parse_args()
    if not args.cmd:
        parser.print_usage()
        sys.exit()
    if args.cmd == arg_sign:
        print(signing_handler(args.data, args.signing_key))
    if args.cmd == arg_verify and not args.list_env:
        if not args.data:
            logger.error("supply data with the `-d` flag")
            sys.exit()
        print(verify_handler(args.data))
    if args.cmd == arg_version:
        print(f"simple-sign version: {get_version()}")
    if args.cmd == "verify" and args.list_env:
        notaries = retrieve_env_notaries()
        if not notaries:
            logger.info(
                "no environment notaries, ensure '%s' is configured",
                KNOWN_SIGNERS_CONFIG,
            )
            sys.exit()
        print(notaries)


if __name__ == "__main__":
    main()
