from dataclasses import dataclass, asdict
from .transaction import Transaction
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class HappayTransaction(Transaction):
    nickname: str = None
