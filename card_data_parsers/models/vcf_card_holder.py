from dataclasses import dataclass, asdict
from .card_holder import CardHolder
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class VCFCardHolder(CardHolder):
    pass