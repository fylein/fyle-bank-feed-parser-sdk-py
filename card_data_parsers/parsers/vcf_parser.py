import logging
import csv
from typing import List
from ..log import getLogger
from .parser import Parser, ParserError
from ..models import VCFTransaction
from ..utils import get_currency_from_country_code, is_amount, mask_card_number, generate_external_id, get_iso_date_string, has_null_value_for_keys, remove_leading_zeros


logger = getLogger(__name__)


class VCFParser(Parser):

    @staticmethod
    def __extract_amount(amount):
        amount = remove_leading_zeros(amount)
        # making the string '1234' into '12.34'
        # If 0000... amount, then it gets stripped, so making it 0.0
        if amount == '':
            amount = '0.0'
        elif len(amount) <= 2:
            amount = '.' + amount
        else:
            amount = amount[0:len(amount)-2]+'.'+amount[-2:]
        if not is_amount(amount):
            logger.warn(f'Not a valid amount {amount}')
            return None
        return amount

    @staticmethod
    def __extract_transaction_type(trxn_type):
        credits = ['11', '30', '31', '61', '63', '65', '71', '73']
        debits = ['10', '20', '22', '40', '50', '52', '54',
                  '56', '62', '64', '66', '80', '82', '84', '86', '88']
        if trxn_type in credits:
            return 'credit'
        elif trxn_type in debits:
            return 'debit'
        raise ParserError(f'Not a valid transaction type {trxn_type}')

    @staticmethod
    def __process_transaction(txn, account_number_mask_begin, account_number_mask_end):
        txn.transaction_type = VCFParser.__extract_transaction_type(
            txn.transaction_type)
        if txn.transaction_type == None:
            raise ParserError('Transaction type missing.')

        if txn.foreign_currency is None or txn.foreign_amount is None or (txn.foreign_currency == txn.currency):
            txn.foreign_currency = None
            txn.foreign_amount = None
        else:
            txn.foreign_currency = remove_leading_zeros(
                txn.foreign_currency, 3)
            txn.foreign_currency = get_currency_from_country_code(
                txn.foreign_currency)
            if txn.foreign_currency == None:
                raise ParserError('foreign_currency missing.')
            txn.foreign_amount = VCFParser.__extract_amount(
                txn.foreign_amount)

        txn.amount = VCFParser.__extract_amount(txn.amount)
        if txn.amount == None:
            raise ParserError(f'Not a valid amount')
        txn.currency = remove_leading_zeros(txn.currency, 3)
        # currency utils to convert to currency ISO string
        txn.currency = get_currency_from_country_code(txn.currency)
        if txn.currency == None:
            raise ParserError('currency missing.')

        txn.transaction_dt = get_iso_date_string(
            txn.transaction_dt.strip(), '%m%d%Y')

        txn.post_date = get_iso_date_string(
            txn.post_date.strip(), '%m%d%Y')
        
        card_num = txn.account_number
        # Masking the card number
        if account_number_mask_begin is not None and account_number_mask_end is not None:
            txn.account_number = mask_card_number(
                txn.account_number, 
                account_number_mask_begin, 
                account_number_mask_end
            )
            
        external_id = str(txn.external_id) + txn.account_number + \
            txn.transaction_dt + txn.vendor + \
            txn.currency + txn.amount
        if txn.foreign_currency is not None and txn.foreign_amount is not None:
            external_id = external_id + \
                txn.foreign_currency + txn.foreign_amount
        txn.external_id = generate_external_id(external_id)
        return txn

    @staticmethod
    def __process_airline_transaction(airline_trxn):
        airline_trxn.airline_travel_date = get_iso_date_string(
            airline_trxn.airline_travel_date.strip(), '%m%d%Y')

        if airline_trxn.airline_total_fare is not None:
            airline_trxn.airline_total_fare = VCFParser.__extract_amount(
                airline_trxn.airline_total_fare)

        return airline_trxn

    @staticmethod
    def __process_lodging_transaction(lodging_trxn):
        lodging_trxn.lodging_check_in_date = get_iso_date_string(
            lodging_trxn.lodging_check_in_date.strip(), '%m%d%Y')

        return lodging_trxn

    @staticmethod
    def __extract_transaction_fields(transaction, default_values):
        txn = VCFTransaction(**default_values)
        txn.account_number = transaction[1].strip()
        txn.vendor = transaction[8].strip()
        txn.amount = transaction[14].strip()
        txn.currency = transaction[19].strip()
        txn.foreign_amount = transaction[13].strip()
        txn.foreign_currency = transaction[15].strip()
        txn.transaction_type = transaction[17].strip()
        txn.transaction_dt = transaction[18].strip()
        txn.external_id = transaction[3].strip()
        txn.merchant_category_code = transaction[16].strip()
        txn.sequence_number = transaction[4].strip()
        txn.post_date = transaction[2].strip()

        # other amounts to consider are
        # at positions 20, 28, 29
        # if 28 is present then do not add the other 20 , 29
        # values exists in 20 and 29
        return txn

    @staticmethod
    def __extract_car_rental_transaction_fields(txn, line_item):
        txn.car_rental_merchant_category_code = line_item[29].strip()
        txn.car_rental_supplier_name = line_item[30].strip()
        return txn

    @staticmethod
    def __extract_airline_booking_transaction_fields(txn, line_item):
        txn.airline_merchant_category_code = line_item[22].strip()
        txn.airline_supplier_name = line_item[23].strip()
        txn.airline_travel_agency_name = line_item[7].strip()
        txn.airline_total_fare = line_item[14].strip()
        txn.airline_travel_date = line_item[5].strip()
        txn.airline_ticket_number = line_item[9].strip()
        return txn

    @staticmethod
    def __extract_lodging_transaction_fields(txn, line_item):
        txn.lodging_merchant_category_code = line_item[29].strip()
        txn.lodging_supplier_name = line_item[30].strip()
        txn.lodging_check_in_date = line_item[6].strip()
        lodging_nights = line_item[23].strip()
        if lodging_nights:
            txn.lodging_nights = int(lodging_nights)
        return txn

    @staticmethod
    def __extract_fleet_product_transaction_fields(txn, line_item):
        txn.fleet_product_merchant_category_code = line_item[11].strip()
        txn.fleet_product_supplier_name = line_item[12].strip()
        return txn

    @staticmethod
    def __extract_fleet_service_transaction_fields(txn, line_item):
        txn.fleet_service_merchant_category_code = line_item[46].strip()
        txn.fleet_service_supplier_name = line_item[47].strip()
        return txn

    @staticmethod
    def __extract_transactions_from_block_after_index(start_index, lines, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields):
        '''
        Returns the transactions present in a single block, from the given `start_index`.
        This function only parses the 1st block of transactions that is detected from given `start_index`.

                Parameters:
                        start_index (int): Starting index of `lines` to search block from

                Returns:
                        txns (list): List of transactions parsed
                        end_index (int): Ending index of first found block after start index from `lines`, of block, if found any, otherwise -1
        '''
        end_index = -1
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

        # Identifying header and trailer of first valid card transaction block
        # We'll ignore further blocks by checking if start/end values are -1 or not
        for index, line in enumerate(lines[start_index:], start=start_index):
            if line[0].strip() == '8' and (line[4].strip() == '05' or line[4].strip() == '5') and card_transactions_block_start == -1:
                card_transactions_block_start = index + 1
            if line[0].strip() == '9' and (line[4].strip() == '05' or line[4].strip() == '5') and card_transactions_block_end == -1:
                card_transactions_block_end = index - 1
                end_index = index
            if line[0].strip() == '8' and (line[4].strip() == '02' or line[4].strip() == '2') and car_rental_transactions_block_start == -1:
                car_rental_transactions_block_start = index + 1
            if line[0].strip() == '9' and (line[4].strip() == '02' or line[4].strip() == '2') and car_rental_transactions_block_end == -1:
                car_rental_transactions_block_end = index - 1
                end_index = index
            if line[0].strip() == '8' and (line[4].strip() == '09' or line[4].strip() == '9') and lodging_transactions_block_start == -1:
                lodging_transactions_block_start = index + 1
            if line[0].strip() == '9' and (line[4].strip() == '09' or line[4].strip() == '9') and lodging_transactions_block_end == -1:
                lodging_transactions_block_end = index - 1
                end_index = index
            if line[0].strip() == '8' and line[4].strip() == '14' and airline_booking_transactions_block_start == -1:
                airline_booking_transactions_block_start = index + 1
            if line[0].strip() == '9' and line[4].strip() == '14' and airline_booking_transactions_block_end == -1:
                airline_booking_transactions_block_end = index - 1
                end_index = index
            if line[0].strip() == '8' and line[4].strip() == '17' and fleet_service_transactions_block_start == -1:
                fleet_service_transactions_block_start = index + 1
            if line[0].strip() == '9' and line[4].strip() == '17' and fleet_service_transactions_block_end == -1:
                fleet_service_transactions_block_end = index - 1
                end_index = index
            if line[0].strip() == '8' and line[4].strip() == '18' and fleet_product_transactions_block_start == -1:
                fleet_product_transactions_block_start = index + 1
            if line[0].strip() == '9' and line[4].strip() == '18' and fleet_product_transactions_block_end == -1:
                fleet_product_transactions_block_end = index - 1
                end_index = index

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

        txns = []
        for transaction in card_transactions:
            txn = VCFParser.__extract_transaction_fields(transaction, default_values)

            txn_sequence_num = txn.sequence_number

            txn = VCFParser.__process_transaction(
                txn, account_number_mask_begin, account_number_mask_end)
            if txn is None:
                raise ParserError(f'unable to parse transaction.')

            for car_rental_transaction in car_rental_transactions:
                if car_rental_transaction[4].strip() == txn_sequence_num:
                    txn = VCFParser.__extract_car_rental_transaction_fields(
                        txn, car_rental_transaction)

            for airline_booking_trxn in airline_booking_transactions:
                if airline_booking_trxn[4].strip() == txn_sequence_num:
                    txn = VCFParser.__extract_airline_booking_transaction_fields(
                        txn, airline_booking_trxn)
                    txn = VCFParser.__process_airline_transaction(txn)

            for lodging_trxn in lodging_transactions:
                if lodging_trxn[4].strip() == txn_sequence_num:
                    txn = VCFParser.__extract_lodging_transaction_fields(
                        txn, lodging_trxn)
                    txn = VCFParser.__process_lodging_transaction(txn)

            for fleet_product_trxn in fleet_product_transactions:
                if fleet_product_trxn[4].strip() == txn_sequence_num:
                    txn = VCFParser.__extract_fleet_product_transaction_fields(
                        txn, fleet_product_trxn)

            for fleet_service_trxn in fleet_service_transactions:
                if fleet_service_trxn[4].strip() == txn_sequence_num:
                    txn = VCFParser.__extract_fleet_service_transaction_fields(
                        txn, fleet_service_trxn)

            if has_null_value_for_keys(txn, mandatory_fields):
                raise ParserError(
                    'One or many mandatory fields missing.')

            txns.append(txn)

        return txns, end_index

    @staticmethod
    def __extract_transactions(lines, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields):
        txns = []

        # Parsing all vcf txn blocks present in given lines
        start_index = 0
        total_lines = len(lines)
        while start_index < total_lines:
            block_txns, end_index = VCFParser.__extract_transactions_from_block_after_index(
                start_index, lines, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields)
            txns.extend(block_txns)
            if end_index == -1:
                break
            start_index = end_index + 1

        return txns

    @staticmethod
    def __cleanup_fields(line) -> str:
        for index, field in enumerate(line):
            if all(str(value) == '0' for value in field):
                line[index] = ''
        return line

    @staticmethod
    def parse(file_obj, account_number_mask_begin=None, account_number_mask_end=None, default_values={}, mandatory_fields=[]) -> List[VCFTransaction]:
        reader = csv.reader(file_obj, delimiter='\t', quoting=csv.QUOTE_NONE)

        trxn_lines = []

        for line in reader:
            cleaned_line = VCFParser.__cleanup_fields(line)
            trxn_lines.append(cleaned_line)

        return VCFParser.__extract_transactions(
            trxn_lines, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields)
