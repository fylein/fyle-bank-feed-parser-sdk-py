from dataclasses import dataclass, asdict
from .company import Company
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class VCFCompany(Company):
    pass