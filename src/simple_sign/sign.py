"""Python template repository.

Baseline template for future Python code related to this project.

Replace this docstring and code below with your own code as required.
"""

import argparse
import logging
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


def signature_in_license_pool():
    """Validate whether signing key matches one of those in a pool of
    licenses associated with the project and return True if so.
    """
    raise NotImplementedError("reading from license pool is not yet implemented")


def signature_in_constitution_datum_utxo():
    """Validate whether signing key matches one of those a list of
    addresses in a given constitution UTxO.
    """
    raise NotImplementedError("reading from datum is not yet implemented")


def signature_in_constitution_config():
    """Validate whether signing key matches one of those listed in a
    configuration file.
    """
    raise NotImplementedError("reading from config is not yet implemented")


def sign_with_key(data: str, signing_key: str):
    """Sign with an signing key."""
    skey = pyc.SigningKey.from_json(signing_key)
    vkey = pyc.VerificationKey.from_signing_key(skey)
    logger.info("signing with addr: %s", pyc.Address(vkey.hash()))
    return pyc.sign(data, skey)


def signing_handler(data: str, signing_key: str):
    """Handle signing functions."""
    return sign_with_key(data, signing_key)


def verify_signature(data: str):
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


def verify_handler(data: str):
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
    subparsers.add_parser(arg_sign)
    verify = subparsers.add_parser(arg_verify)
    sign = subparsers.add_parser(arg_sign)
    subparsers.add_parser(arg_version)
    verify.add_argument("-d", "--data", type=str, help="data to verify")
    sign.add_argument("-d", "--data", type=str, help="data to sign")
    sign.add_argument("-s", "--signing_key", type=str, help="signing key")
    args = parser.parse_args()
    if not args.cmd:
        parser.print_usage()
        sys.exit()
    if args.cmd == arg_sign:
        print(signing_handler(args.data, args.signing_key))
    if args.cmd == arg_verify:
        print(verify_handler(args.data))
    if args.cmd == arg_version:
        print(f"simple-sign version: {get_version()}")


if __name__ == "__main__":
    main()
