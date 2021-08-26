from .transaction import Transaction


class CDFTransaction(Transaction):
    nickname: str

    lodging_nights: int
    lodging_check_in_date: str
    lodging_checkout_date: str
    lodging_total_fare: str

    airline_travel_date: str
    airline_fare_base_code: str
    airline_service_class: str
    airline_carrier_code: str

    general_ticket_issue_date: str
    general_ticket_number: str
    general_issuing_carrier: str
    general_travel_agency_name: str
    general_travel_agency_code: str
    general_ticket_total_fare: str
