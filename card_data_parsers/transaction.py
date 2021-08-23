from typing import Dict, List, Optional
from typing_extensions import TypedDict


class Transaction(TypedDict):
    '''
    General fields to expect in a transaction i.e. parsers response.

    Attributes
    ----------
    bank_name: Bank name (pass it via default_values)

    vendor: Vendor or merchant

    transaction_type: Credit or debit

    currency: Currency

    amount: Amount in local currency

    account_number: Account number

    transaction_dt: Date time

    external_id: Unique string based on some of fields present

    orig_amount: Refers to amount in foreign currency

    orig_currency: Refers to foreign currency
    '''
    bank_name: Optional[str]
    vendor: str
    transaction_type: str
    currency: str
    amount: str
    account_number: str
    transaction_dt: str
    transaction_date: str  # TODO: get rid of this
    external_id: str
    orig_amount: Optional[str]
    orig_currency: Optional[str]