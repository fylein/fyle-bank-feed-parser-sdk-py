from dataclasses import dataclass, asdict


@dataclass
class CardAccount:
    cardholder_id: str = None
    account_number: str = None
    hierarchy_node: str = None
    card_type: str = None
    status_code: str = None