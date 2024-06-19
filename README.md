# Orcfax Simple Sign

Provides simple signing and verification of data following the approach
outlined in [CIP-8][CIP-8].

[CIP-8]: https://cips.cardano.org/cip/CIP-0008

The command-line application and library is intended to provide helper functions
for consistent signing and verification functions across distributed dapps and
other applications utilizing Cardano off-chain.

## Creating a signing key

You need a signing key and address that can then be used to verify the source
of the signed data.

> If you hold the key, you hold the address that can be used to verify data.

The `cardano-cli` can be used to generate a signing key. E.g. on
preview/preprod.

```sh
cardano-cli address key-gen \
 --verification-key-file payment.vkey \
 --signing-key-file payment.skey
```

```sh
cardano-cli address build \
 --payment-verification-key-file payment.vkey \
 --out-file payment.addr \
 --mainnet
```

The key can then be given to the app with arbitrary data to be signed.

## Basic signing and verification

### Signing

Example signing with `payment.skey` with addr
`addr1v90vykgaft6lylq79u7uvxqc3hxmnf8tz7uyxael6gpz3lsfnggam`:

```sh
python sign.py sign -d "arbitrary data" -s "$(cat payment.skey)"
```

Outputs:

<!--markdownlint-disable -->
```text
84584da301276761646472657373581d615ec2591d4af5f27c1e2f3dc618188dcdb9a4eb17b843773fd20228fe045820d88b447a19aa5ffcabc4270dd38017bda068c9f84b6fb05cb0fee73261fbb777a166686173686564f44e6172626974726172792064617461584025b3ef85838d62f40eb3fe5b1ac7cf802ca4d076a07575572bc88601968bafa2b4aa106c8636cc93bd4337385527cb31194e65925062c59857d69fbccd4f3f01
```
<!--markdownlint-enable -->

### Verification

Example verification, looking for addr
`addr1v90vykgaft6lylq79u7uvxqc3hxmnf8tz7uyxael6gpz3lsfnggam`:

```sh
python sign.py verify \
 -d "84584da301276761646472657373581d615ec2591d4af5f27c1e2f3dc618188dcdb9a4eb17b843773fd20228fe045820d88b447a19aa5ffcabc4270dd38017bda068c9f84b6fb05cb0fee73261fbb777a166686173686564f44e6172626974726172792064617461584025b3ef85838d62f40eb3fe5b1ac7cf802ca4d076a07575572bc88601968bafa2b4aa106c8636cc93bd4337385527cb31194e65925062c59857d69fbccd4f3f01"

```

Outputs:

```python
{
    'verified': True,
    'message': 'arbitrary data',
    'signing_address': 'addr1v90vykgaft6lylq79u7uvxqc3hxmnf8tz7uyxael6gpz3lsfnggam'
}
```

### Verification against a known set

Simple Sign provides enough for most use cases to receive a CIP-8 message,
check that it was signed, and then compare the signer's address against their
own known list of notaries.

To standardise the process Simple Sign will offer a number of helper functions.

#### Notaries in an environment variable

For a small number of notaries an environment variable may be sufficient. Use
`CIP8_NOTARIES=` with comma separated list of Cardano addresses before
invoking `signature_in_dapp_environment(pkey: str)` in your script.

```env
CIP8_NOTARIES=addr1...,addr2...,addr3...
```

Use `--list-env` or `-l` to display the contents of this variable locally:

```sh
python sign.py verify -
```

#### Other methods of checking signers

A number of stubs have been left in the code that might provide methods such
as checking against a UTxO or set of NFT holders in the future. These are yet
to be implemented.

## Developer install

### pip

Setup a virtual environment `venv` and install the local development
requirements as follows:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements/local.txt
```

#### Upgrade dependencies

A `make` recipe is included, simply call `make upgrade`. Alternatively run
`pip-upgrader` once the local requirements have been installed and follow the
prompts. `requirements.txt` and `local.txt` can be updated as desired.

### tox

#### Run tests (all)

```bash
python -m tox
```

#### Run tests-only

```bash
python -m tox -e py3
```

#### Run linting-only

```bash
python -m tox -e linting
```

### pre-commit

Pre-commit can be used to provide more feedback before committing code. This
reduces reduces the number of commits you might want to make when working on
code, it's also an alternative to running tox manually.

To set up pre-commit, providing `pip install` has been run above:

* `pre-commit install`

This repository contains a default number of pre-commit hooks, but there may
be others suited to different projects. A list of other pre-commit hooks can be
found [here][pre-commit-1].

[pre-commit-1]: https://pre-commit.com/hooks.html

## Packaging

The `Makefile` contains helper functions for packaging and release.

Makefile functions can be reviewed by calling `make`  from the root of this
repository:

```make
clean                          Clean the package directory
docs                           Generate documentation
help                           Print this help message
package-check                  Check the distribution is valid
package-deps                   Upgrade dependencies for packaging
package-source                 Package the source code
package-upload                 Upload package to pypi
package-upload-test            Upload package to test.pypi
pre-commit-checks              Run pre-commit-checks.
serve-docs                     Serve the documentation
tar-source                     Package repository as tar for easy distribution
upgrade                        Upgrade project dependencies
```

### pyproject.toml

Packaging consumes the metadata in `pyproject.toml` which helps to describe
the project on the official [pypi.org][pypi-2] repository. Have a look at the
documentation and comments there to help you create a suitably descriptive
metadata file.

### Local packaging

To create a python wheel for testing locally, or distributing to colleagues
run:

* `make package-source`

A `tar` and `whl` file will be stored in a `dist/` directory. The `whl` file
can be installed as follows:

* `pip install <your-package>.whl`

### Publishing

Publishing for public use can be achieved with:

* `make package-upload-test` or `make package-upload`

`make-package-upload-test` will upload the package to [test.pypi.org][pypi-1]
which provides a way to look at package metadata and documentation and ensure
that it is correct before uploading to the official [pypi.org][pypi-2]
repository using `make package-upload`.

[pypi-1]: https://test.pypi.org
[pypi-2]: https://pypi.org
