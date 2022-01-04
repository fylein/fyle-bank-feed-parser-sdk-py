from dataclasses import dataclass
from .transaction import Transaction


@dataclass
class AmexTransaction(Transaction):
    nickname: str = None
    merchant_category_code: str = None
    lodging_check_in_date: str = None
    lodging_checkout_date: str = None
    lodging_nights: int = None
    hotel_country: str = None
    hotel_city: str = None
    car_rental_date: str = None
    car_return_date: str = None
    airline_service_class: str = None
    airline_carrier_code: str = None
    airline_travel_agency_name: str = None
    airline_ticket_number: str = None
    airline_type: str = None
    transaction_id: str = None
