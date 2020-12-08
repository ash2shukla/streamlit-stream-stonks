from json import load
from pathlib import Path
from enum import Enum


SEC_TYPES = ("TRT", "STP", "SP", "BND", "ETF", "PFS", "WAR", "PRF", "DR", "UNT", "EQS")

SYMBLS = load(open(Path(__file__).parent.parent / "static" / "symbols.json"))


class MatColors(Enum):
    RED_700 = "#ff4444"
    GREEN_700 = "#00C851"
