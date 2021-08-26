from .transaction import Transaction


class AmexTransaction(Transaction):
    nickname: str
    merchant_category_code: str
    lodging_check_in_date: str
    lodging_checkout_date: str
    lodging_nights: int
    hotel_country: str
    hotel_city: str
    car_rental_date: str
    car_return_date: str
    airline_service_class: str
    airline_carrier_code: str
    airline_travel_agency_name: str
    airline_ticket_number: str
    airline_type: str
