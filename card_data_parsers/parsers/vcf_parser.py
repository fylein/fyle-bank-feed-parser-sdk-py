import logging
import csv
from typing import List
from .parser import Parser, ParserError
from ..models import VCFTransaction
from ..utils import get_currency_from_country_code, is_amount, mask_card_number, generate_external_id, get_iso_date_string, expand_with_default_values, has_null_value_for_keys


logger = logging.getLogger('vcf')
logger.setLevel(logging.INFO)


class VCFParser(Parser):
    def __init__(self):
        pass

    @staticmethod
    def __remove_leading_zeros(value, min_len=None):
        '''
        Removes leading zeros. 
        but maintaining min length - https://docs.python.org/2/library/string.html#string.zfill
        If min_len given, removes so that the expected minimum length is maintained.
        Examples:
            If 00000440 -> 440
            If 44 -> 44
            If 0000044 -> 044
            If 000044444000 -> 44444000
        '''
        value = value.lstrip('0')
        if min_len:
            value = value.zfill(min_len)
        return value

    @staticmethod
    def __process_amount(amount):
        amount = VCFParser.__remove_leading_zeros(amount)
        # making the string '1234' into '12.34'
        if len(amount) <= 2:
            amount = '.' + amount
        else:
            amount = amount[0:len(amount)-2]+'.'+amount[-2:]
        if not is_amount(amount):
            raise ParserError(f'Not a valid amount {amount}')
        return amount

    @staticmethod
    def __process_transaction_type(trxn_type):
        credits = ['11', '30', '31', '61', '63', '65', '71', '73']
        debits = ['10', '20', '22', '40', '50', '52', '54',
                  '56', '62', '64', '66', '80', '82', '84', '86', '88']
        if trxn_type in credits:
            return 'credit'
        elif trxn_type in debits:
            return 'debit'
        raise ParserError(f'Not a valid transaction type {trxn_type}')

    @staticmethod
    def __process_transaction(trxn, account_number_mask_begin, account_number_mask_end):
        trxn['transaction_type'] = VCFParser.__process_transaction_type(
            trxn['transaction_type'])
        if trxn['transaction_type'] == None:
            raise ParserError('Transaction type missing.')

        if trxn.get('orig_currency') is None or trxn.get('orig_amount') is None or trxn['orig_currency'] == trxn['currency'] or trxn['orig_amount'] == trxn['amount']:
            del trxn['orig_currency']
            del trxn['orig_amount']
        else:
            trxn['orig_currency'] = VCFParser.__remove_leading_zeros(
                trxn['orig_currency'], 3)
            trxn['orig_currency'] = get_currency_from_country_code(
                trxn['orig_currency'])
            if trxn['orig_currency'] == None:
                raise ParserError('orig_currency missing.')
            trxn['orig_amount'] = VCFParser.__process_amount(
                trxn['orig_amount'])

        trxn['amount'] = VCFParser.__process_amount(trxn['amount'])
        trxn['currency'] = VCFParser.__remove_leading_zeros(
            trxn['currency'], 3)
        # currency utils to convert to currency ISO string
        trxn['currency'] = get_currency_from_country_code(trxn['currency'])
        if trxn['currency'] == None:
            raise ParserError('currency missing.')

        trxn['transaction_dt'] = get_iso_date_string(
            trxn['transaction_dt'].strip(), '%m%d%Y')

        card_num = trxn['account_number']
        # Masking the card number
        trxn['account_number'] = mask_card_number(
            trxn['account_number'], account_number_mask_begin, account_number_mask_end)
        external_id = str(trxn['external_id']) + trxn['account_number'] + \
            trxn['transaction_dt'] + trxn['vendor'] + \
            trxn['currency'] + trxn['amount']
        if 'orig_currency' in trxn and 'orig_amount' in trxn:
            external_id = external_id + \
                trxn['orig_currency'] + trxn['orig_amount']
        trxn['external_id'] = generate_external_id(external_id)
        return trxn

    @staticmethod
    def __process_airline_transaction(airline_trxn):
        airline_trxn['airline_travel_date'] = get_iso_date_string(
            airline_trxn['airline_travel_date'].strip(), '%m%d%Y')

        if airline_trxn['airline_total_fare'] is not None:
            airline_trxn['airline_total_fare'] = VCFParser.__process_amount(
                airline_trxn['airline_total_fare'])
        return airline_trxn

    @staticmethod
    def __process_lodging_transaction(lodging_trxn):
        lodging_trxn['lodging_check_in_date'] = get_iso_date_string(
            lodging_trxn['lodging_check_in_date'].strip(), '%m%d%Y')

        return lodging_trxn

    @staticmethod
    def __extract_transaction_fields(transaction):
        trxn = {}
        trxn['account_number'] = transaction[1].strip()
        trxn['vendor'] = transaction[8].strip()
        trxn['amount'] = transaction[14].strip()
        trxn['currency'] = transaction[19].strip()
        trxn['orig_amount'] = transaction[13].strip()
        trxn['orig_currency'] = transaction[15].strip()
        trxn['transaction_type'] = transaction[17].strip()
        trxn['transaction_dt'] = transaction[18].strip()
        trxn['external_id'] = transaction[3].strip()
        trxn['merchant_category_code'] = transaction[16].strip()
        trxn['sequence_number'] = transaction[4].strip()

        # other amounts to consider are
        # at positions 20, 28, 29
        # if 28 is present then do not add the other 20 , 29
        # values exists in 20 and 29
        return trxn

    @staticmethod
    def __extract_car_rental_transaction_fields(trxn, line_item):
        trxn['car_rental_merchant_category_code'] = line_item[29].strip()
        trxn['car_rental_supplier_name'] = line_item[30].strip()
        return trxn

    @staticmethod
    def __extract_airline_booking_transaction_fields(trxn, line_item):
        trxn['airline_merchant_category_code'] = line_item[22].strip()
        trxn['airline_supplier_name'] = line_item[23].strip()
        trxn['airline_travel_agency_name'] = line_item[7].strip()
        trxn['airline_total_fare'] = line_item[14].strip()
        trxn['airline_travel_date'] = line_item[5].strip()
        trxn['airline_ticket_number'] = line_item[9].strip()
        return trxn

    @staticmethod
    def __extract_lodging_transaction_fields(trxn, line_item):
        trxn['lodging_merchant_category_code'] = line_item[29].strip()
        trxn['lodging_supplier_name'] = line_item[30].strip()
        trxn['lodging_check_in_date'] = line_item[6].strip()
        lodging_nights = line_item[23].strip()
        if lodging_nights:
            trxn['lodging_nights'] = int(lodging_nights)
        return trxn

    @staticmethod
    def __extract_fleet_product_transaction_fields(trxn, line_item):
        trxn['fleet_product_merchant_category_code'] = line_item[11].strip()
        trxn['fleet_product_supplier_name'] = line_item[12].strip()
        return trxn

    @staticmethod
    def __extract_fleet_service_transaction_fields(trxn, line_item):
        trxn['fleet_service_merchant_category_code'] = line_item[46].strip()
        trxn['fleet_service_supplier_name'] = line_item[47].strip()
        return trxn

    @staticmethod
    def __group_by_transaction_type(lines, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields):
        card_transactions_block_start = -1
        card_transactions_block_end = -1

        car_rental_transactions_block_start = -1
        car_rental_transactions_block_end = -1

        airline_booking_transactions_block_start = -1
        airline_booking_transactions_block_end = -1

        lodging_transactions_block_start = -1
        lodging_transactions_block_end = -1

        fleet_service_transactions_block_start = -1
        fleet_service_transactions_block_end = -1

        fleet_product_transactions_block_start = -1
        fleet_product_transactions_block_end = -1

        # identifying header and trailer of card transaction blocks
        for index, line in enumerate(lines):
            if line[0].strip() == '8' and (line[4].strip() == '05' or line[4].strip() == '5'):
                card_transactions_block_start = index + 1
            if line[0].strip() == '9' and (line[4].strip() == '05' or line[4].strip() == '5'):
                card_transactions_block_end = index - 1
            if line[0].strip() == '8' and (line[4].strip() == '02' or line[4].strip() == '2'):
                car_rental_transactions_block_start = index + 1
            if line[0].strip() == '9' and (line[4].strip() == '02' or line[4].strip() == '2'):
                car_rental_transactions_block_end = index - 1
            if line[0].strip() == '8' and (line[4].strip() == '09' or line[4].strip() == '9'):
                lodging_transactions_block_start = index + 1
            if line[0].strip() == '9' and (line[4].strip() == '09' or line[4].strip() == '9'):
                lodging_transactions_block_end = index - 1
            if line[0].strip() == '8' and line[4].strip() == '14':
                airline_booking_transactions_block_start = index + 1
            if line[0].strip() == '9' and line[4].strip() == '14':
                airline_booking_transactions_block_end = index - 1
            if line[0].strip() == '8' and line[4].strip() == '17':
                fleet_service_transactions_block_start = index + 1
            if line[0].strip() == '9' and line[4].strip() == '17':
                fleet_service_transactions_block_end = index - 1
            if line[0].strip() == '8' and line[4].strip() == '18':
                fleet_product_transactions_block_start = index + 1
            if line[0].strip() == '9' and line[4].strip() == '18':
                fleet_product_transactions_block_end = index - 1

        card_transactions = lines[card_transactions_block_start: card_transactions_block_end + 1]
        car_rental_transactions = lines[car_rental_transactions_block_start:
                                        car_rental_transactions_block_end + 1]
        airline_booking_transactions = lines[airline_booking_transactions_block_start:
                                             airline_booking_transactions_block_end + 1]
        lodging_transactions = lines[lodging_transactions_block_start:
                                     lodging_transactions_block_end + 1]
        fleet_service_transactions = lines[fleet_service_transactions_block_start:
                                           fleet_service_transactions_block_end + 1]
        fleet_product_transactions = lines[fleet_product_transactions_block_start:
                                           fleet_product_transactions_block_end + 1]

        trxns = []
        for transaction in card_transactions:
            trxn = VCFParser.__extract_transaction_fields(transaction)

            expand_with_default_values(trxn, default_values)

            txn_sequence_num = trxn['sequence_number']

            trxn = VCFParser.__process_transaction(
                trxn, account_number_mask_begin, account_number_mask_end)
            if trxn is None:
                raise ParserError(f'unable to parse transaction.')

            for car_rental_transaction in car_rental_transactions:
                if car_rental_transaction[4].strip() == txn_sequence_num:
                    trxn = VCFParser.__extract_car_rental_transaction_fields(
                        trxn, car_rental_transaction)

            for airline_booking_trxn in airline_booking_transactions:
                if airline_booking_trxn[4].strip() == txn_sequence_num:
                    trxn = VCFParser.__extract_airline_booking_transaction_fields(
                        trxn, airline_booking_trxn)
                    trxn = VCFParser.__process_airline_transaction(trxn)

            for lodging_trxn in lodging_transactions:
                if lodging_trxn[4].strip() == txn_sequence_num:
                    trxn = VCFParser.__extract_lodging_transaction_fields(
                        trxn, lodging_trxn)
                    trxn = VCFParser.__process_lodging_transaction(trxn)

            for fleet_product_trxn in fleet_product_transactions:
                if fleet_product_trxn[4].strip() == txn_sequence_num:
                    trxn = VCFParser.__extract_fleet_product_transaction_fields(
                        trxn, fleet_product_trxn)

            for fleet_service_trxn in fleet_service_transactions:
                if fleet_service_trxn[4].strip() == txn_sequence_num:
                    trxn = VCFParser.__extract_fleet_service_transaction_fields(
                        trxn, fleet_service_trxn)

            if has_null_value_for_keys(trxn, mandatory_fields):
                raise ParserError(
                    'One or many mandatory fields missing.')

            trxns.append(trxn)

        return trxns

    @staticmethod
    def __cleanup_fields(line) -> str:
        for index, field in enumerate(line):
            if all(str(value) == '0' for value in field):
                line[index] = ''
        return line

    @staticmethod
    def parse(file_obj, account_number_mask_begin, account_number_mask_end, default_values={}, mandatory_fields=[]) -> List[VCFTransaction]:
        reader = csv.reader(file_obj, delimiter='\t', quoting=csv.QUOTE_NONE)

        trxn_lines = []

        for line in reader:
            cleaned_line = VCFParser.__cleanup_fields(line)
            trxn_lines.append(cleaned_line)

        trxns = VCFParser.__group_by_transaction_type(
            trxn_lines, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields)

        return trxns
