"""Simple-sign data types"""

from dataclasses import dataclass


@dataclass
class Alias:
    alias: str
    address: str
    staking: str
    tx: str
