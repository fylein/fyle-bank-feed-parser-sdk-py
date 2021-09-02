from dataclasses import dataclass, asdict
from .transaction import Transaction


@dataclass
class HappayTransaction(Transaction):
    nickname: str = None
