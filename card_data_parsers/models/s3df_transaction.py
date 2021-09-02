from dataclasses import dataclass, asdict
from .transaction import Transaction


@dataclass
class S3DFTransaction(Transaction):
    general_issuing_carrier: str = None
    general_travel_agency_name: str = None
    general_travel_agency_code: str = None
    general_ticket_total_fare: str = None
    general_ticket_total_tax: str = None

    lodging_total_fare: str = None
    lodging_nights: int = None

    airline_trip_leg_number: str = None
    airline_carrier_code: str = None
    airline_service_class: str = None
    airline_ticket_number: str = None
    airline_travel_date: str = None
    airline_total_fare: str = None
