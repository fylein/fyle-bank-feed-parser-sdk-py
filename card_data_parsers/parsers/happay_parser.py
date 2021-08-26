import logging
import csv
import datetime
from typing import List
from .parser import Parser, ParserError
from ..models import HappayTransaction
from ..utils import get_currency_from_country_code, is_amount, mask_card_number, generate_external_id, has_null_value_for_keys, expand_with_default_values


logger = logging.getLogger('happay')
logger.setLevel(logging.INFO)


HAPPAY_FIELDS_MAPPINGS = {
    'transaction_date': 'transaction_dt',
    'account_number': 'account_number',
    'vendor': 'vendor',
    'amount': 'amount',
    'transaction_type': 'transaction_type',
    'description': 'description',
    'external_id': 'external_id',
    'nickname': 'nickname',
    'currency': 'currency',
    'foreign_amount': 'foreign_amount',
    'foreign_currency': 'foreign_currency',
}


class HappayParser(Parser):
    def __init__(self):
        pass

    @staticmethod
    def __strip_spaces(trxn_line):
        for key, value in trxn_line.items():
            trxn_line[key] = value.strip()
        return trxn_line

    @staticmethod
    def __get_transaction_from_line(trxn_line_orig, account_number_mask_begin, account_number_mask_end, default_values):
        """
        Build a transaction line from available fields
        """
        trxn_line = {}

        for key in HAPPAY_FIELDS_MAPPINGS:
            if key in trxn_line_orig:
                trxn_line[HAPPAY_FIELDS_MAPPINGS[key]] = trxn_line_orig[key]

        expand_with_default_values(trxn_line, default_values)

        trxn_line = HappayParser.__strip_spaces(trxn_line)

        # account number
        trxn_line['account_number'] = mask_card_number(
            trxn_line['account_number'], account_number_mask_begin, account_number_mask_end)

        # amount
        trxn_line['amount'] = abs(float(trxn_line['amount']))

        # transaction type
        if trxn_line['transaction_type'] is not None and (trxn_line['transaction_type'].lower() == 'debit' or trxn_line['transaction_type'].lower() == 'credit'):
            trxn_line['transaction_type'] = trxn_line['transaction_type'].lower()
        else:
            logger.info(
                "Transaction type is none or does not satisfy the condition")
            logger.info(trxn_line['transaction_type'])

        # transaction date
        trxn_line['transaction_dt'] = datetime.datetime.strptime(
            trxn_line['transaction_dt'].strip(), "%Y-%m-%d")
        trxn_line['transaction_dt'] = trxn_line['transaction_dt'].strftime(
            "%Y-%m-%dT%H:%M:%SZ")

        # orig amount and orig currency
        if trxn_line['foreign_amount'] and trxn_line['foreign_currency']:
            trxn_line['foreign_amount'] = abs(float(trxn_line['foreign_amount']))
        else:
            del trxn_line['foreign_amount']
            del trxn_line['foreign_currency']

        # external id
        unique_for_transaction = str(trxn_line['account_number']) + str(trxn_line['transaction_dt']) + str(
            trxn_line['amount']) + str(trxn_line['external_id']) + str(trxn_line['vendor']) + trxn_line['bank_name']
        trxn_line['external_id'] = generate_external_id(unique_for_transaction)

        return trxn_line

    @staticmethod
    def __process_transaction_lines(trxn_lines, account_number_mask_begin, account_number_mask_end, default_values):
        txns = []
        for trxn_line in trxn_lines:
            txn = HappayParser.__get_transaction_from_line(
                trxn_line, account_number_mask_begin, account_number_mask_end, default_values)
            txns.append(HappayTransaction(**txn))
        return txns

    @staticmethod
    def parse(file_obj, account_number_mask_begin, account_number_mask_end, default_values={}, mandatory_fields=[]) -> List[HappayTransaction]:
        reader = csv.DictReader(file_obj, delimiter=',')

        # Transaction Lines
        trxn_lines = []
        for line in reader:
            # if key values are having trailing/preceding spaces
            trxn_line = {key.strip().lower(): line[key] for key in line.keys()}
            if not has_null_value_for_keys(trxn_line, mandatory_fields):
                trxn_lines.append(trxn_line)
            else:
                raise ParserError(
                    f'One or many mandatory fields missing.')

        trxns = HappayParser.__process_transaction_lines(
            trxn_lines, account_number_mask_begin, account_number_mask_end, default_values)

        return trxns
