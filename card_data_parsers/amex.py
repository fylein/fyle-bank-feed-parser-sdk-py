import logging
from .parser import Parser, ParserError
from .utils import generate_external_id, get_currency_from_country_code, get_iso_date_string, is_amount, mask_card_number, expand_with_default_values, has_null_value_for_keys


logger = logging.getLogger('amex')
logger.setLevel(logging.INFO)


class AmexParser(Parser):
    def __init__(self):
        pass

    @staticmethod
    def __remove_leading_zeros(value, min_len=None):
        """
        Removes leading zeros.
        but maintaining min length - https://docs.python.org/2/library/string.html#string.zfill
        If min_len given, removes so that the expected minimum length is maintained.
        Examples:
            If 00000440 -> 440
            If 44 -> 44
            If 0000044 -> 044
            If 000044444000 -> 44444000
        """
        value = value.lstrip('0')
        if min_len:
            value = value.zfill(min_len)
        return value

    @staticmethod
    def __process_amount(amount, decimal_place_indicator):
        amount = AmexParser.__remove_leading_zeros(amount)

        # making the string '1234' into '12.34' and so on according to decimal_place_indicator
        amount = float(amount) / (10 ** int(decimal_place_indicator))
        return str(amount)

    @staticmethod
    def __process_currency(currency):
        currency = AmexParser.__remove_leading_zeros(currency, 3)

        # getting the currency from ISO code
        currency = get_currency_from_country_code(currency)
        return currency

    @staticmethod
    def __process_transaction_type(sign_indicator):
        transaction_type = None
        if sign_indicator == '+':
            transaction_type = 'debit'
        elif sign_indicator == '-':
            transaction_type = 'credit'
        return transaction_type

    @staticmethod
    def __process_lodging_transaction(txn):
        txn['lodging_check_in_date'] = get_iso_date_string(
            txn['lodging_check_in_date'], '%Y-%m-%d')
        txn['lodging_checkout_date'] = get_iso_date_string(
            txn['lodging_checkout_date'], '%Y-%m-%d')
        return txn

    @staticmethod
    def __process_car_rental_transaction(txn):
        txn['car_rental_date'] = get_iso_date_string(
            txn['car_rental_date'], '%Y-%m-%d')
        txn['car_return_date'] = get_iso_date_string(
            txn['car_return_date'], '%Y-%m-%d')
        return txn

    @staticmethod
    def __process_transaction(txn, account_number_mask_begin, account_number_mask_end):
        txn['transaction_type'] = AmexParser.__process_transaction_type(
            txn['transaction_type'])
        if txn['transaction_type'] is None:
            raise ParserError(f'Transaction type is missing')

        if txn['orig_currency'] == txn['currency'] and txn['orig_amount'] == txn['amount']:
            del txn['orig_amount']
            del txn['orig_currency']
        else:
            txn['orig_currency'] = AmexParser.__process_currency(
                txn['orig_currency'])
            if txn['orig_currency'] is None:
                raise ParserError(f'orig_currency is missing')
            txn['orig_amount'] = AmexParser.__process_amount(
                txn['orig_amount'], txn['decimal_place_indicator'])

        txn['amount'] = AmexParser.__process_amount(
            txn['amount'], txn['decimal_place_indicator'])
        txn['currency'] = AmexParser.__process_currency(txn['currency'])
        if txn['currency'] is None:
            raise ParserError(f'Currency is missing')

        txn['transaction_dt'] = get_iso_date_string(
            txn['transaction_dt'].strip(), "%Y-%m-%d")
        txn['transaction_date'] = txn['transaction_dt']

        # Masking the card number
        txn['account_number'] = mask_card_number(txn['account_number'], account_number_mask_begin,
                                                 account_number_mask_end)

        txn['sync_type'] = 'BANK FEED - AMEX'

        external_id = str(txn['external_id'] + txn['account_number'] + txn['transaction_dt'] + txn['description'] + txn[
            'currency'] + txn['amount'])
        if 'orig_currency' in txn and 'orig_amount' in txn:
            external_id = str(
                external_id + txn['orig_currency'] + txn['orig_amount'])
        txn['external_id'] = generate_external_id(external_id)

        del txn['decimal_place_indicator']

        return txn

    @staticmethod
    def __extract_transaction_fields(transaction):
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

        txn = {}
        txn['account_number'] = transaction[207:227].strip()
        txn['nickname'] = transaction[257:277].strip(
        ) + ' ' + transaction[277:297].strip() + ' ' + transaction[227:257].strip()
        txn['amount'] = transaction[737:752].strip()
        txn['currency'] = transaction[769:772].strip()
        txn['orig_amount'] = transaction[811:826].strip()
        txn['orig_currency'] = transaction[858:861].strip()
        txn['transaction_dt'] = transaction[588:598].strip()
        txn['transaction_type'] = transaction[736:737].strip()
        txn['description'] = transaction[946:991].strip()
        txn['external_id'] = transaction[631:681].strip()
        txn['decimal_place_indicator'] = transaction[768:769].strip()
        txn['merchant_category_code'] = transaction[1678:1681].strip()

        if transaction[1867:1897].strip() is not None and transaction[1867:1897].strip() != '':
            # service_establishment_brand_name
            txn['vendor'] = transaction[1867:1897].strip()
        elif transaction[1837:1867].strip() is not None and transaction[1837:1867].strip() != '':
            # service_establishment_chain_name
            txn['vendor'] = transaction[1837:1867].strip()
        elif transaction[1913:1953].strip() is not None and transaction[1913:1953].strip() != '':
            # service_establishment_name_1
            txn['vendor'] = transaction[1913:1953].strip()
        return txn

    @staticmethod
    def __extract_car_rental_transaction_fields(txn, line_item):
        txn['car_rental_date'] = line_item[1171:1181].strip()
        car_rental_days = line_item[1350:1352].strip()
        if car_rental_days:
            txn['car_rental_days'] = int(car_rental_days)
        txn['car_return_date'] = line_item[1181:1191].strip()
        return txn

    @staticmethod
    def __extract_airline_transaction_fields(txn, line_item):
        txn['airline_service_class'] = line_item[1281:1321].strip()
        txn['airline_carrier_code'] = line_item[1321:1363].strip()
        txn['airline_travel_agency_name'] = line_item[1363:1403].strip()
        txn['airline_ticket_number'] = line_item[1494:1509].strip()
        txn['airline_type'] = line_item[1590:1593].strip()
        return txn

    @staticmethod
    def __extract_lodging_transaction_fields(txn, line_item):
        txn['lodging_check_in_date'] = line_item[1236:1246].strip()
        txn['lodging_checkout_date'] = line_item[1246:1256].strip()
        lodging_nights = line_item[1256:1260].strip()
        if lodging_nights:
            txn['lodging_nights'] = int(lodging_nights)
        txn['hotel_country'] = line_item[1334:1337].strip()
        txn['hotel_city'] = line_item[1275:1305].strip()
        return txn

    @staticmethod
    def __group_by_transaction_type(txn_lines, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields):
        txns = []
        for transaction in txn_lines:
            txn = AmexParser.__extract_transaction_fields(transaction)
            if transaction[904:907].strip() == '01':
                txn = AmexParser.__extract_airline_transaction_fields(
                    txn, transaction)
            if transaction[904:907].strip() == '03':
                txn = AmexParser.__extract_lodging_transaction_fields(
                    txn, transaction)
                txn = AmexParser.__process_lodging_transaction(txn)
            if transaction[904:907].strip() == '04':
                txn = AmexParser.__extract_car_rental_transaction_fields(
                    txn, transaction)
                txn = AmexParser.__process_car_rental_transaction(txn)

            expand_with_default_values(txn, default_values)

            txn = AmexParser.__process_transaction(
                txn, account_number_mask_begin, account_number_mask_end)

            if has_null_value_for_keys(txn, mandatory_fields):
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
    def parse(file_obj, account_number_mask_begin, account_number_mask_end, default_values={}, mandatory_fields=[]):
        txn_lines = []
        file_content = file_obj.readlines()
        for line in file_content:
            is_transaction = AmexParser.__check_if_transaction_line(line)
            if is_transaction:
                txn_lines.append(line)

        trxns = AmexParser.__group_by_transaction_type(
            txn_lines, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields)

        return trxns
