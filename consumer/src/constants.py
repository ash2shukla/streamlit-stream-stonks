from json import load
from pathlib import Path


SEC_TYPES = ('TRT', 'STP', 'SP', 'BND', 'ETF', 'PFS', 'WAR', 'PRF', 'DR', 'UNT', 'EQS')

SYMBLS = load(open(Path(__file__).parent / "symbols.json"))