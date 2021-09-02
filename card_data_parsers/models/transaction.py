from dataclasses import dataclass, asdict


@dataclass
class Transaction:
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

    foreign_amount: Refers to amount in foreign currency

    foreign_currency: Refers to foreign currency
    '''
    account_number: str
    transaction_dt: str
    currency: str
    amount: str
    foreign_amount: str = None
    foreign_currency: str = None
    transaction_type: str  = None
    vendor: str  = None
    description: str  = None
    external_id: str  = None
    bank_name: str  = None
