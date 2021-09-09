from dataclasses import dataclass, asdict
from .transaction import Transaction


@dataclass
class VCFTransaction(Transaction):
    merchant_category_code: str = None

    sequence_number: str = None

    car_rental_merchant_category_code: str = None
    car_rental_supplier_name: str = None

    airline_merchant_category_code: str = None
    airline_supplier_name: str = None
    airline_travel_agency_name: str = None
    airline_total_fare: str = None
    airline_travel_date: str = None
    airline_ticket_number: str = None

    lodging_merchant_category_code: str = None
    lodging_supplier_name: str = None
    lodging_check_in_date: str = None
    lodging_nights: int = None

    fleet_product_merchant_category_code: str = None
    fleet_product_supplier_name: str = None

    fleet_service_merchant_category_code: str = None
    fleet_service_supplier_name: str = None
