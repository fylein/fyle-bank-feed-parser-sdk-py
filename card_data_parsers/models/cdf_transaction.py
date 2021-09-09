from dataclasses import dataclass, asdict
from .transaction import Transaction


@dataclass
class CDFTransaction(Transaction):
    nickname: str = None

    lodging_nights: int = None
    lodging_check_in_date: str = None
    lodging_checkout_date: str = None
    lodging_total_fare: str = None

    airline_travel_date: str = None
    airline_fare_base_code: str = None
    airline_service_class: str = None
    airline_carrier_code: str = None

    general_ticket_issue_date: str = None
    general_ticket_number: str = None
    general_issuing_carrier: str = None
    general_travel_agency_name: str = None
    general_travel_agency_code: str = None
    general_ticket_total_fare: str = None
