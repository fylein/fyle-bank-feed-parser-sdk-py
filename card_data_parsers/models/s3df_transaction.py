from .transaction import Transaction


class S3DFTransaction(Transaction):
    general_issuing_carrier: str
    general_travel_agency_name: str
    general_travel_agency_code: str
    general_ticket_total_fare: str
    general_ticket_total_tax: str

    lodging_total_fare: str
    lodging_nights: int

    airline_trip_leg_number: str
    airline_carrier_code: str
    airline_service_class: str
    airline_ticket_number: str
    airline_travel_date: str
    airline_total_fare: str
