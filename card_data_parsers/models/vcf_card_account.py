from dataclasses import dataclass, asdict
from .card_account import CardAccount
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class VCFCardAccount(CardAccount):
    pass