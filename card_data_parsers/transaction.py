from typing import Dict, List, Optional
from typing_extensions import TypedDict


class Transaction(TypedDict):
    bank_name: str
    vendor: str
    sync_type: str
    transaction_type: str
    currency: str
    amount: str
    transaction_date: str  # TODO: get rid of this
    account_number: str
    transaction_dt: str
    external_id: str
    orig_amount: Optional[str]
    orig_currency: Optional[str]
