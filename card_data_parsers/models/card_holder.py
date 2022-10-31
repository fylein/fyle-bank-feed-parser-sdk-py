from dataclasses import dataclass, asdict

@dataclass
class CardHolder:
    load_transaction_code: int = 1
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