from typing import List
from ..log import getLogger
from .parser import Parser, ParserError
from ..models import AmexTransaction
from ..utils import generate_external_id, get_currency_from_country_code, get_iso_date_string, is_amount, mask_card_number, has_null_value_for_attrs, remove_leading_zeros


logger = getLogger(__name__)


class AmexParser(Parser):

    @staticmethod
    def __extract_amount(amount, decimal_place_indicator):
        amount = remove_leading_zeros(amount)

        # making the string '1234' into '12.34' and so on according to decimal_place_indicator
        amount = float(amount) / (10 ** int(decimal_place_indicator))
        return str(amount)

    @staticmethod
    def __extract_currency(currency):
        currency = remove_leading_zeros(currency, 3)

        # getting the currency from ISO code
        currency = get_currency_from_country_code(currency)
        return currency

    @staticmethod
    def __extract_transaction_type(sign_indicator):
        transaction_type = None
        if sign_indicator == '+':
            transaction_type = 'debit'
        elif sign_indicator == '-':
            transaction_type = 'credit'
        return transaction_type

    @staticmethod
    def __extract_transaction_fields(txn_line, default_values):
        # From the AMEX specifications:
        # Billing Account Number - 208 - account number
        # Last Name - 228 - ninckname
        # First Name - 258 - nickname
        # Middle Name - 278 - nickname
        # Charge Date - 589 - transaction date
        # Transaction ID (Unique Global Trans ID) - 632 - external id
        # Billed Amount - 738 - amount
        # Billed Currency ISO Code - 770 - currency
        # Local Charge Amount - 812 - original amount
        # Local Currency ISO Code - 859 - original currency
        # Sign Indicator - 737 - transaction type (+ means debit and - means credit)
        # Charge Description Line 1 - 947 - description
        # Service Establishment Brand Name - 1868 - vendor
        # Service Establishment Chain Name - 1838 - vendor
        # Service Establishment Name 1 - 1914 - vendor

        txn = AmexTransaction(**default_values)
        txn.account_number = txn_line[207:227].strip()
        txn.nickname = txn_line[257:277].strip() + ' ' + txn_line[277:297].strip() + ' ' + txn_line[227:257].strip()
        txn.amount = txn_line[737:752].strip()
        txn.currency = txn_line[769:772].strip()
        txn.foreign_amount = txn_line[811:826].strip()
        txn.foreign_currency = txn_line[858:861].strip()
        txn.transaction_dt = get_iso_date_string(txn_line[588:598].strip(), "%Y-%m-%d")
        txn.transaction_type = txn_line[736:737].strip()
        txn.description = txn_line[946:991].strip()
        txn.external_id = txn_line[631:681].strip()
        txn.post_date = get_iso_date_string(txn_line[573:581].strip(), "%Y%m%d")
        txn.decimal_place_indicator = txn_line[768:769].strip()
        txn.merchant_category_code = txn_line[1677:1681].strip()

        if txn_line[1867:1897].strip() is not None and txn_line[1867:1897].strip() != '':
            # service_establishment_brand_name
            txn.vendor = txn_line[1867:1897].strip()
        elif txn_line[1837:1867].strip() is not None and txn_line[1837:1867].strip() != '':
            # service_establishment_chain_name
            txn.vendor = txn_line[1837:1867].strip()
        elif txn_line[1913:1953].strip() is not None and txn_line[1913:1953].strip() != '':
            # service_establishment_name_1
            txn.vendor = txn_line[1913:1953].strip()
        return txn

    @staticmethod
    def __extract_car_rental_transaction_fields(txn, line_item):
        txn.car_rental_date = get_iso_date_string(line_item[1171:1181].strip(), '%Y-%m-%d')
        car_rental_days = line_item[1350:1352].strip()
        if car_rental_days:
            txn.car_rental_days = int(car_rental_days)
        txn.car_return_date = get_iso_date_string(line_item[1181:1191].strip(), '%Y-%m-%d')
        return txn

    @staticmethod
    def __extract_airline_transaction_fields(txn, line_item):
        txn.airline_service_class = line_item[1281:1321].strip()
        txn.airline_carrier_code = line_item[1321:1363].strip()
        txn.airline_travel_agency_name = line_item[1363:1403].strip()
        txn.airline_ticket_number = line_item[1494:1509].strip()
        txn.airline_type = line_item[1590:1593].strip()
        return txn

    @staticmethod
    def __extract_lodging_transaction_fields(txn, line_item):
        txn.lodging_check_in_date = get_iso_date_string(line_item[1236:1246].strip(), '%Y-%m-%d')
        txn.lodging_checkout_date = get_iso_date_string(line_item[1246:1256].strip(), '%Y-%m-%d')
        lodging_nights = line_item[1256:1260].strip()
        if lodging_nights:
            txn.lodging_nights = int(lodging_nights)
        txn.hotel_country = line_item[1334:1337].strip()
        txn.hotel_city = line_item[1275:1305].strip()

        return txn

    @staticmethod
    def __extract_transactions(txn_lines, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields):
        txns = []
        for txn_line in txn_lines:
            txn = AmexParser.__extract_transaction_fields(txn_line, default_values)
            if txn_line[904:907].strip() == '01':
                txn = AmexParser.__extract_airline_transaction_fields(
                    txn, txn_line)
            if txn_line[904:907].strip() == '03':
                txn = AmexParser.__extract_lodging_transaction_fields(
                    txn, txn_line)
            if txn_line[904:907].strip() == '04':
                txn = AmexParser.__extract_car_rental_transaction_fields(
                    txn, txn_line)

            txn.transaction_type = AmexParser.__extract_transaction_type(
                        txn.transaction_type)
            if txn.transaction_type is None:
                raise ParserError(f'Transaction type is missing')

            if txn.foreign_currency is None or txn.foreign_amount is None or (txn.foreign_currency == txn.currency):
                txn.foreign_amount = None
                txn.foreign_currency = None
            else:
                txn.foreign_currency = AmexParser.__extract_currency(
                    txn.foreign_currency)
                if txn.foreign_currency is None:
                    raise ParserError(f'foreign_currency is missing')
                txn.foreign_amount = AmexParser.__extract_amount(
                    txn.foreign_amount, txn.decimal_place_indicator)

            txn.amount = AmexParser.__extract_amount(
                txn.amount, txn.decimal_place_indicator)
            txn.currency = AmexParser.__extract_currency(txn.currency)
            if txn.currency is None:
                raise ParserError(f'Currency is missing')

            # Masking the card number
            if account_number_mask_begin is not None and account_number_mask_end is not None:
                txn.account_number = mask_card_number(
                    txn.account_number, 
                    account_number_mask_begin,
                    account_number_mask_end
                )

            # adding actual AMEX transaction_id before modifying it
            txn.transaction_id = txn.external_id

            external_id = str(txn.external_id + txn.account_number + txn.transaction_dt + txn.description + txn.currency + txn.amount)
            if txn.foreign_currency is not None and txn.foreign_amount is not None:
                external_id = str(external_id + txn.foreign_currency + txn.foreign_amount)
            txn.external_id = generate_external_id(external_id)

            txn.decimal_place_indicator = None

            if has_null_value_for_attrs(txn, mandatory_fields):
                raise ParserError('One or many mandatory fields missing.')

            txns.append(txn)
        return txns

    @staticmethod
    def __check_if_transaction_line(line):
        # Checks if the line is the transaction line or header lines
        # From specs file:
        # Record Type 0: File Header
        # Record Type 8: Market Header & Market Summary
        # Record Type 1: Transaction Detail
        # Record Type 2: Card Member Summary
        is_transaction = False
        if line[0] == '1':
            is_transaction = True
        return is_transaction

    @staticmethod
    def parse(file_obj, account_number_mask_begin=None, account_number_mask_end=None, default_values={}, mandatory_fields=[]) -> List[AmexTransaction]:
        txn_lines = []
        file_content = file_obj.readlines()
        for line in file_content:
            is_transaction = AmexParser.__check_if_transaction_line(line)
            if is_transaction:
                txn_lines.append(line)

        return AmexParser.__extract_transactions(
            txn_lines, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields)
