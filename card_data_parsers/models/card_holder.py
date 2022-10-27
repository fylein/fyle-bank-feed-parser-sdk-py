from dataclasses import dataclass, asdict
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class CardHolder:
    company_id: str = None
    cardholder_id: str = None
    hierarchy_node: str = None
    first_name: str = None
    last_name: str = None
    address_line_1: str = None
    address_line_2: str = None
    city: str = None
    state: str = None
    iso_country_code: str = None
    postal_code: str = None
    phone_no: str = None
    email_address: str = None