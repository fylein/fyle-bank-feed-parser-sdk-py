from dataclasses import dataclass, asdict

@dataclass
class Company:
    load_transaction_code: int = 1
    company_id: str = None
    company_name: str = None
    address_line_1: str = None
    address_line_2: str = None
    city: str = None
    state: str = None
    iso_country_code: str = None
    postal_code: str = None
    card_type: str = None
    issuer_name: str = None