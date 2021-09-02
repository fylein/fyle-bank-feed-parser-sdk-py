import logging
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree
from typing import List
from ..log import getLogger
from .parser import Parser, ParserError
from ..models import S3DFTransaction
from ..utils import get_currency_from_country_code, is_amount, mask_card_number, generate_external_id, get_iso_date_string, expand_with_default_values, has_null_value_for_keys


logger = getLogger(__name__)


class S3DFParser(Parser):

    @staticmethod
    def __get_element_by_tag(root, name):
        for child in root.iter(name):
            return child
        return None

    @staticmethod
    def __get_elements_by_tag(root, name):
        elements = []
        for child in root.iter(name):
            elements.append(child)
        return elements

    @staticmethod
    def __get_attribute_value(element, attribute):
        return element.attrib[attribute]

    @staticmethod
    def __get_amount(amount, exponent):
        amount_str = str(amount)
        exponent = int(exponent)
        amount = amount_str[:-exponent] + '.' + amount_str[-exponent:]
        if not is_amount(amount):
            return None
        else:
            amount = amount.strip("0")
        if amount.endswith('.'):
            amount = amount[:-1]
        return amount

    @staticmethod
    def __get_transaction_field(root, account_number):
        trxn = {}

        trxn['account_number'] = account_number

        ftrxn = S3DFParser.__get_element_by_tag(
            root, 'FinancialTransaction_5000')
        card_acceptor = S3DFParser.__get_element_by_tag(
            root, 'CardAcceptor_5001')

        # Date
        trxn['transaction_dt'] = S3DFParser.__get_element_by_tag(
            ftrxn, 'TransactionDate').text
        trxn['transaction_dt'] = get_iso_date_string(
            trxn['transaction_dt'].strip(), '%Y-%m-%d')

        # Transaction Type
        trxn['transaction_type'] = S3DFParser.__get_element_by_tag(
            ftrxn, 'DebitOrCreditIndicator').text
        if trxn['transaction_type'] == 'D':
            trxn['transaction_type'] = 'debit'
        elif trxn['transaction_type'] == 'C':
            trxn['transaction_type'] = 'credit'

        # amount
        amount = S3DFParser.__get_element_by_tag(
            ftrxn, 'AmountInPostedCurrency')
        currency_exponent = amount.attrib['CurrencyExponent']
        trxn['amount'] = S3DFParser.__get_amount(
            amount.text, currency_exponent)

        # currency
        trxn['currency'] = S3DFParser.__get_element_by_tag(
            ftrxn, 'PostedCurrencyCode').text
        if trxn['currency'] != None:
            trxn['currency'] = get_currency_from_country_code(trxn['currency'])
        else:
            return None

        # foreign_amount
        foreign_amount = S3DFParser.__get_element_by_tag(
            ftrxn, 'AmountInOriginalCurrency')
        orig_currency_exponent = trxn['foreign_amount'] = foreign_amount.attrib['CurrencyExponent']
        trxn['foreign_amount'] = S3DFParser.__get_amount(
            foreign_amount.text, orig_currency_exponent)
        if trxn['foreign_amount'] == None:
            return None

        # foreign_currency
        trxn['foreign_currency'] = S3DFParser.__get_element_by_tag(
            ftrxn, 'OriginalCurrencyCode').text
        if trxn['foreign_currency'] != None:
            trxn['foreign_currency'] = get_currency_from_country_code(
                trxn['foreign_currency'])
        else:
            return None

        if trxn['foreign_currency'] == trxn['currency']:
            del trxn['foreign_currency']
            del trxn['foreign_amount']

        # Vendor
        trxn['vendor'] = S3DFParser.__get_element_by_tag(
            card_acceptor, 'CardAcceptorName').text
        trxn['vendor'] = str(trxn['vendor']) + ', ' + S3DFParser.__get_element_by_tag(
            card_acceptor, 'CardAcceptorStateProvince').text

        # external Id
        external_id = S3DFParser.__get_element_by_tag(
            ftrxn, 'ProcessorTransactionId').text
        trxn['external_id'] = generate_external_id(external_id)

        return trxn

    @staticmethod
    def __extract_general_ticket_transaction_fields(trxn, line_item):

        general_ticket_trxn = S3DFParser.__get_element_by_tag(
            line_item, 'PassengerTransportDetailGeneralTicketInformation_5020')

        trxn['general_issuing_carrier'] = S3DFParser.__get_element_by_tag(
            general_ticket_trxn, 'IssuingCarrier').text
        trxn['general_travel_agency_name'] = S3DFParser.__get_element_by_tag(
            general_ticket_trxn, 'TravelAgencyName').text
        trxn['general_travel_agency_code'] = S3DFParser.__get_element_by_tag(
            general_ticket_trxn, 'TravelAgencyCode').text

        total_amount = S3DFParser.__get_element_by_tag(
            general_ticket_trxn, 'TotalFare')
        if total_amount is not None:
            currency_exponent = total_amount.attrib['CurrencyExponent']
            trxn['general_ticket_total_fare'] = S3DFParser.__get_amount(
                total_amount.text, currency_exponent)
        else:
            trxn['general_ticket_total_fare'] = None

        total_tax_amount = S3DFParser.__get_element_by_tag(
            general_ticket_trxn, 'TotalTaxAmount')
        if total_tax_amount is not None:
            currency_exponent = total_tax_amount.attrib['CurrencyExponent']
            trxn['general_ticket_total_tax'] = S3DFParser.__get_amount(
                total_tax_amount.text, currency_exponent)
        else:
            trxn['general_ticket_total_tax'] = None

        return trxn

    @staticmethod
    def __extract_lodging_transaction_fields(trxn, line_item):

        lodging_trxn = S3DFParser.__get_element_by_tag(
            line_item, 'LodgingSummaryAddendum_5030')

        total_amount = S3DFParser.__get_element_by_tag(
            lodging_trxn, 'TotalChargesAmount')
        if total_amount is not None:
            currency_exponent = total_amount.attrib['CurrencyExponent']
            trxn['lodging_total_fare'] = S3DFParser.__get_amount(
                total_amount.text, currency_exponent)
        else:
            trxn['lodging_total_fare'] = None
        lodging_nights = S3DFParser.__get_element_by_tag(
            lodging_trxn, 'TotalRoomNights').text
        if lodging_nights:
            trxn['lodging_nights'] = int(lodging_nights)

        return trxn

    @staticmethod
    def __extract_airline_transaction_fields(trxn, line_item):

        airline_trxn = S3DFParser.__get_element_by_tag(
            line_item, 'PassengerTransportDetailTripLegData_5021')

        trxn['airline_trip_leg_number'] = S3DFParser.__get_element_by_tag(
            airline_trxn, 'TripLegNum').text
        trxn['airline_carrier_code'] = S3DFParser.__get_element_by_tag(
            airline_trxn, 'CarrierCode').text
        trxn['airline_service_class'] = S3DFParser.__get_element_by_tag(
            airline_trxn, 'ServiceClass').text
        trxn['airline_ticket_number'] = S3DFParser.__get_element_by_tag(
            airline_trxn, 'ExchangeTicketNum').text

        travel_date = S3DFParser.__get_element_by_tag(
            airline_trxn, 'TravelDate')
        if travel_date is not None:
            trxn['airline_travel_date'] = travel_date.text
            trxn['airline_travel_date'] = get_iso_date_string(
                trxn['airline_travel_date'].strip(), '%Y-%m-%d')
        else:
            trxn['airline_travel_date'] = None

        total_amount = S3DFParser.__get_element_by_tag(
            airline_trxn, 'FareAmount')
        if total_amount is not None:
            currency_exponent = total_amount.attrib['CurrencyExponent']
            trxn['airline_total_fare'] = S3DFParser.__get_amount(
                total_amount.text, currency_exponent)
        else:
            trxn['airline_total_fare'] = None

        return trxn

    @staticmethod
    def __extract_transactions(root, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields):
        trxns = []
        issuer_entity = S3DFParser.__get_element_by_tag(root, 'IssuerEntity')
        if issuer_entity is None:
            return None
        corporate_entity = S3DFParser.__get_element_by_tag(
            issuer_entity, 'CorporateEntity')
        if corporate_entity == None:
            return None
        account_entities = S3DFParser.__get_elements_by_tag(
            corporate_entity, 'AccountEntity')
        for account in account_entities:
            account_number = mask_card_number(
                account.attrib['AccountNumber'], account_number_mask_begin, account_number_mask_end)
            financial_transaction_entities = S3DFParser.__get_elements_by_tag(
                account, 'FinancialTransactionEntity')

            for transaction in financial_transaction_entities:
                trxn = S3DFParser.__get_transaction_field(
                    transaction, account_number)

                expand_with_default_values(trxn, default_values)

                general_ticket_transaction_entities = S3DFParser.__get_elements_by_tag(
                    transaction, 'PassengerTransportEntity')
                lodging_transaction_entities = S3DFParser.__get_elements_by_tag(
                    transaction, 'LodgingSummaryAddendumEntity')
                airline_transaction_entities = S3DFParser.__get_elements_by_tag(
                    transaction, 'PassengerTransportDetailTripLegDataEntity')
                for lodging_trxn in lodging_transaction_entities:
                    trxn = S3DFParser.__extract_lodging_transaction_fields(
                        trxn, lodging_trxn)
                for airline_trxn in airline_transaction_entities:
                    trxn = S3DFParser.__extract_airline_transaction_fields(
                        trxn, airline_trxn)
                for general_ticket_trxn in general_ticket_transaction_entities:
                    trxn = S3DFParser.__extract_general_ticket_transaction_fields(
                        trxn, general_ticket_trxn)
                if trxn:
                    if has_null_value_for_keys(trxn, mandatory_fields):
                        raise ParserError(
                            'One or many mandatory fields missing.')

                    trxns.append(S3DFTransaction(**trxn))
                else:
                    return None

        return trxns

    @staticmethod
    def parse(file_obj, account_number_mask_begin, account_number_mask_end, default_values={}, mandatory_fields=[]) -> List[S3DFTransaction]:
        root: ElementTree = ET.parse(file_obj).getroot()
        if root is None:
            return None

        return S3DFParser.__extract_transactions(
            root, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields)
