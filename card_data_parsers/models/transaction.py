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
    
    starting_bill_date: Refers to the starting bill date in a billing period (if this is not available but ending_bill_date is 
    available, this will get defaulted to ending_bill_date - 1 month )
    
    ending_bill_date: Refers to the ending bill date in a billing period
    
    post_date: Refers to the posting date of the bank transaction.
    '''
    account_number: str = None
    transaction_dt: str = None
    currency: str = None
    amount: str = None
    foreign_amount: str = None
    foreign_currency: str = None
    transaction_type: str = None
    vendor: str = None
    description: str = None
    external_id: str = None
    bank_name: str = None
    starting_bill_date: str = None
    ending_bill_date: str = None
    post_date: str = None