from dataclasses import dataclass, asdict

@dataclass
class Company:
    '''
    General fields to expect in a company i.e. parsers response.

    Attributes
    ----------
    TODO: add the rest
    '''
    load_transaction_code: int = 1
    company_id: str = None
    company_name: str = None
    address_line_1: str = None
    address_line_2: str = None
    city: str = None
    state: str = None
    iso_country_code: str = None
    postal_code: str = None