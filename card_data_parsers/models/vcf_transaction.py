from .transaction import Transaction


class VCFTransaction(Transaction):
    merchant_category_code: str

    sequence_number: str

    car_rental_merchant_category_code: str
    car_rental_supplier_name: str

    airline_merchant_category_code: str
    airline_supplier_name: str
    airline_travel_agency_name: str
    airline_total_fare: str
    airline_travel_date: str
    airline_ticket_number: str

    lodging_merchant_category_code: str
    lodging_supplier_name: str
    lodging_check_in_date: str
    lodging_nights: int

    fleet_product_merchant_category_code: str
    fleet_product_supplier_name: str

    fleet_service_merchant_category_code: str
    fleet_service_supplier_name: str
