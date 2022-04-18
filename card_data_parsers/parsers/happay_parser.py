import logging
import csv
import datetime
from typing import List
from ..log import getLogger
from .parser import Parser, ParserError
from ..models import HappayTransaction
from ..utils import get_currency_from_country_code, is_amount, mask_card_number, generate_external_id, expand_with_default_values, has_null_value_for_keys


logger = getLogger(__name__)


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

    @staticmethod
    def __strip_spaces(txn):
        for key, value in txn.items():
            txn[key] = value.strip()
        return txn

    @staticmethod
    def __get_transaction_from_line(trxn_line_orig, account_number_mask_begin, account_number_mask_end, default_values):
        txn_line = {}

        for key in HAPPAY_FIELDS_MAPPINGS:
            if key in trxn_line_orig:
                txn_line[HAPPAY_FIELDS_MAPPINGS[key]] = trxn_line_orig[key]

        expand_with_default_values(txn_line, default_values)

        txn_line = HappayParser.__strip_spaces(txn_line)

        txn = HappayTransaction(**txn_line)

        # account number
        if account_number_mask_begin is not None and account_number_mask_end is not None:
            txn.account_number = mask_card_number(
                txn.account_number, 
                account_number_mask_begin,
                account_number_mask_end
            )

        # amount
        txn.amount = abs(float(txn.amount))

        # transaction type
        if txn.transaction_type is not None and (txn.transaction_type.lower() == 'debit' or txn.transaction_type.lower() == 'credit'):
            txn.transaction_type = txn.transaction_type.lower()
        else:
            logger.info(
                "Transaction type is none or does not satisfy the condition")
            logger.info(txn.transaction_type)

        # transaction date
        txn.transaction_dt = datetime.datetime.strptime(txn.transaction_dt.strip(), "%Y-%m-%d")
        txn.transaction_dt = txn.transaction_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # orig amount and orig currency
        if txn.foreign_amount and txn.foreign_currency:
            txn.foreign_amount = abs(float(txn.foreign_amount))
        else:
            txn.foreign_amount = None
            txn.foreign_currency = None

        if txn.foreign_currency is None or txn.foreign_amount is None or (txn.foreign_currency == txn.currency):
            txn.foreign_amount = None
            txn.foreign_currency = None

        # external id
        unique_for_transaction = str(txn.account_number) + str(txn.transaction_dt) + str(
            txn.amount) + str(txn.external_id) + str(txn.vendor) + txn.bank_name
        txn.external_id = generate_external_id(unique_for_transaction)

        return txn

    @staticmethod
    def __extract_transactions(trxn_lines, account_number_mask_begin, account_number_mask_end, default_values):
        txns = []
        for txn in trxn_lines:
            txn = HappayParser.__get_transaction_from_line(
                txn, account_number_mask_begin, account_number_mask_end, default_values)
            txns.append(txn)
        return txns

    @staticmethod
    def parse(file_obj, account_number_mask_begin=None, account_number_mask_end=None, default_values={}, mandatory_fields=[]) -> List[HappayTransaction]:
        reader = csv.DictReader(file_obj, delimiter=',')

        # Transaction Lines
        trxn_lines = []
        for line in reader:
            # if key values are having trailing/preceding spaces
            txn = {key.strip().lower(): line[key] for key in line.keys()}
            if not has_null_value_for_keys(txn, mandatory_fields):
                trxn_lines.append(txn)
            else:
                raise ParserError(
                    f'One or many mandatory fields missing.')

        return HappayParser.__extract_transactions(
            trxn_lines, account_number_mask_begin, account_number_mask_end, default_values)
