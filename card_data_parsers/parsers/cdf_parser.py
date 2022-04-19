import logging
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree
from typing import List
from ..log import getLogger
from .parser import Parser, ParserError
from ..models import CDFTransaction
from ..utils import get_currency_from_country_code, is_amount, mask_card_number, generate_external_id, get_iso_date_string, has_null_value_for_attrs


logger = getLogger(__name__)


class CDFParser(Parser):

    @staticmethod
    def __get_element_by_tag(root, name):
        for child in root.iter(name):
            return child
        return None

    @staticmethod
    def __get_elements_by_tag(root: ElementTree, name: str):
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
            logger.warn(f'Not a valid amount {amount}')
            return None
        amount = amount.strip('0')
        if amount.endswith('.'):
            amount = amount[:-1]
        return amount

    @staticmethod
    def __extract_transaction_fields(root: ElementTree, account_number, nickname, default_values):
        txn = CDFTransaction(**default_values)

        txn.account_number = account_number

        ftrxn = CDFParser.__get_element_by_tag(
            root, 'FinancialTransaction_5000')
        card_acceptor = CDFParser.__get_element_by_tag(
            root, 'CardAcceptor_5001')

        # Date
        txn.transaction_dt = CDFParser.__get_element_by_tag(
            ftrxn, 'TransactionDate').text
        txn.transaction_dt = get_iso_date_string(
            txn.transaction_dt.strip(), '%Y-%m-%d')

        # Post Date
        txn.post_date = CDFParser.__get_element_by_tag(
            ftrxn, 'PostingDate').text
        txn.post_date = get_iso_date_string(
            txn.post_date.strip(), '%Y-%m-%d')

        # Transaction Type
        txn.transaction_type = CDFParser.__get_element_by_tag(
            ftrxn, 'DebitOrCreditIndicator').text
        if txn.transaction_type == 'D':
            txn.transaction_type = 'debit'
        elif txn.transaction_type == 'C':
            txn.transaction_type = 'credit'

        # amount
        amount = CDFParser.__get_element_by_tag(
            ftrxn, 'AmountInPostedCurrency')
        currency_exponent = amount.attrib['CurrencyExponent']
        txn.amount = CDFParser.__get_amount(amount.text, currency_exponent)

        # currency
        txn.currency = CDFParser.__get_element_by_tag(
            ftrxn, 'PostedCurrencyCode').text
        if txn.currency is None:
            return None
        txn.currency = get_currency_from_country_code(txn.currency)

        # foreign_amount
        foreign_amount = CDFParser.__get_element_by_tag(
            ftrxn, 'AmountInOriginalCurrency')
        orig_currency_exponent = foreign_amount.attrib['CurrencyExponent']
        txn.foreign_amount = CDFParser.__get_amount(
            foreign_amount.text, orig_currency_exponent)

        # foreign_currency
        txn.foreign_currency = CDFParser.__get_element_by_tag(
            ftrxn, 'OriginalCurrencyCode').text
        if txn.foreign_currency is None:
            return None
        txn.foreign_currency = get_currency_from_country_code(
            txn.foreign_currency)

        if txn.foreign_currency is None or txn.foreign_amount is None or (txn.foreign_currency == txn.currency):
            txn.foreign_currency = None
            txn.foreign_amount = None

        # Vendor
        txn.vendor = CDFParser.__get_element_by_tag(
            card_acceptor, 'CardAcceptorName').text

        # Nickname
        if nickname is not None:
            txn.nickname = nickname

        # external Id
        external_id = '' + \
            CDFParser.__get_element_by_tag(
                ftrxn, 'ProcessorTransactionId').text
        external_id = external_id + \
            CDFParser.__get_element_by_tag(
                ftrxn, 'MasterCardFinancialTransactionId').text
        txn.external_id = generate_external_id(external_id)

        return txn

    @staticmethod
    def __process_date(txn_date):
        if txn_date is not None:
            txn_date = txn_date.text
            txn_date = get_iso_date_string(txn_date, '%Y-%m-%d')
        else:
            txn_date = None

        return txn_date

    @staticmethod
    def __extract_lodging_transaction_fields(txn, line_item):
        lodging_trxn = CDFParser.__get_element_by_tag(
            line_item, 'LodgingSummaryAddendum_5030')

        lodging_nights = CDFParser.__get_element_by_tag(
            lodging_trxn, 'TotalRoomNights').text
        if lodging_nights:
            txn.lodging_nights = int(lodging_nights)
        check_in_date = CDFParser.__get_element_by_tag(
            lodging_trxn, 'ArrivalDate')
        txn.lodging_check_in_date = CDFParser.__process_date(check_in_date)
        departure_date = CDFParser.__get_element_by_tag(
            lodging_trxn, 'DepartureDate')
        txn.lodging_checkout_date = CDFParser.__process_date(
            departure_date)

        total_amount = CDFParser.__get_element_by_tag(
            lodging_trxn, 'TotalAmountChargedOnCreditCardAmount')
        if total_amount is not None:
            currency_exponent = total_amount.attrib['CurrencyExponent']
            txn.lodging_total_fare = CDFParser.__get_amount(
                total_amount.text, currency_exponent)
        else:
            txn.lodging_total_fare = None

        return txn

    @staticmethod
    def __extract_airline_transaction_fields(txn, line_item):
        airline_trxn = CDFParser.__get_element_by_tag(
            line_item, 'PassengerTransportDetailTripLegData_5021')

        travel_date = CDFParser.__get_element_by_tag(
            airline_trxn, 'TravelDate')
        txn.airline_travel_date = CDFParser.__process_date(travel_date)

        if CDFParser.__get_element_by_tag(airline_trxn, 'FareBaseCode') is not None:
            txn.airline_fare_base_code = CDFParser.__get_element_by_tag(
                airline_trxn, 'FareBaseCode').text
        else:
            txn.airline_fare_base_code = None
        if CDFParser.__get_element_by_tag(airline_trxn, 'ServiceClass') is not None:
            txn.airline_service_class = CDFParser.__get_element_by_tag(
                airline_trxn, 'ServiceClass').text
        else:
            txn.airline_service_class = None
        if CDFParser.__get_element_by_tag(airline_trxn, 'CarrierCode') is not None:
            txn.airline_carrier_code = CDFParser.__get_element_by_tag(
                airline_trxn, 'CarrierCode').text
        else:
            txn.airline_carrier_code = None

        return txn

    @staticmethod
    def __extract_general_ticket_transaction_fields(txn, line_item):
        general_ticket_trxn = CDFParser.__get_element_by_tag(
            line_item, 'PassengerTransportDetailGeneralTicketInformation_5020')

        issue_date = CDFParser.__get_element_by_tag(
            general_ticket_trxn, 'IssueDate')
        txn.general_ticket_issue_date = CDFParser.__process_date(
            issue_date)

        if CDFParser.__get_element_by_tag(general_ticket_trxn, 'TicketNum') is not None:
            txn.general_ticket_number = CDFParser.__get_element_by_tag(
                general_ticket_trxn, 'TicketNum').text
        else:
            txn.general_ticket_number = None
        if CDFParser.__get_element_by_tag(general_ticket_trxn, 'IssuingCarrier') is not None:
            txn.general_issuing_carrier = CDFParser.__get_element_by_tag(
                general_ticket_trxn, 'IssuingCarrier').text
        else:
            txn.general_issuing_carrier = None
        if CDFParser.__get_element_by_tag(general_ticket_trxn, 'TravelAgencyName') is not None:
            txn.general_travel_agency_name = CDFParser.__get_element_by_tag(
                general_ticket_trxn, 'TravelAgencyName').text
        else:
            txn.general_travel_agency_name = None
        if CDFParser.__get_element_by_tag(general_ticket_trxn, 'TravelAgencyCode') is not None:
            txn.general_travel_agency_code = CDFParser.__get_element_by_tag(
                general_ticket_trxn, 'TravelAgencyCode').text
        else:
            txn.general_travel_agency_code = None

        total_amount = CDFParser.__get_element_by_tag(
            general_ticket_trxn, 'TotalFare')
        if total_amount is not None:
            currency_exponent = total_amount.attrib['CurrencyExponent']
            txn.general_ticket_total_fare = CDFParser.__get_amount(
                total_amount.text, currency_exponent)
        else:
            txn.general_ticket_total_fare = None

        return txn

    @staticmethod
    def __check_transmission_headers(root):
        # minimun identification for a CDF file is to have below tags.
        cdf_file_identifier = CDFParser.__get_element_by_tag(
            root, 'CDFTransmissionFile')
        if cdf_file_identifier is None:
            return False
        transamission_header = CDFParser.__get_element_by_tag(
            cdf_file_identifier, 'TransmissionHeader_1000')
        transamission_trailer = CDFParser.__get_element_by_tag(
            cdf_file_identifier, 'TransmissionTrailer_9999')
        if transamission_header is None or transamission_trailer is None:
            return False
        return True

    @staticmethod
    def __extract_nickname(account):
        nickname = None
        nameline1 = CDFParser.__get_element_by_tag(account, 'NameLine1')
        if nameline1 is not None:
            nickname = nameline1.text
        return nickname

    @staticmethod
    def __extract_transactions(root, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields):
        txns = []
        issuer_entity = CDFParser.__get_element_by_tag(root, 'IssuerEntity')
        if issuer_entity is None:
            return []
        corporate_entities = CDFParser.__get_elements_by_tag(
            issuer_entity, 'CorporateEntity')
        for corporate_entity in corporate_entities:
            if corporate_entity == None:
                continue

            account_entities = CDFParser.__get_elements_by_tag(
                corporate_entity, 'AccountEntity')

            for account in account_entities:
                nickname = CDFParser.__extract_nickname(account)
                account_number = account.attrib['AccountNumber']
                if account_number_mask_begin is not None and account_number_mask_end is not None:
                    account_number = mask_card_number(
                        account_number, 
                        account_number_mask_begin,
                        account_number_mask_end
                    )
                
                financial_transaction_entities = CDFParser.__get_elements_by_tag(
                    account, 'FinancialTransactionEntity')

                for transaction in financial_transaction_entities:
                    txn = CDFParser.__extract_transaction_fields(
                        transaction, account_number, nickname, default_values)

                    lodging_transaction_entities = CDFParser.__get_elements_by_tag(
                        transaction, 'LodgingSummaryAddendumEntity')
                    airline_transaction_entities = CDFParser.__get_elements_by_tag(
                        transaction, 'PassengerTransportDetailTripLegDataEntity')
                    general_ticket_transaction_entities = CDFParser.__get_elements_by_tag(
                        transaction, 'PassengerTransportEntity')
                    for lodging_trxn in lodging_transaction_entities:
                        txn = CDFParser.__extract_lodging_transaction_fields(
                            txn, lodging_trxn)
                    for airline_trxn in airline_transaction_entities:
                        txn = CDFParser.__extract_airline_transaction_fields(
                            txn, airline_trxn)
                    for general_ticket_trxn in general_ticket_transaction_entities:
                        txn = CDFParser.__extract_general_ticket_transaction_fields(
                            txn, general_ticket_trxn)
                    if txn:
                        if has_null_value_for_attrs(txn, mandatory_fields):
                            raise ParserError(
                                'One or many mandatory fields missing.')

                        txns.append(txn)
                    else:
                        return None

        return txns

    @staticmethod
    def parse(file_obj, account_number_mask_begin=None, account_number_mask_end=None, default_values={}, mandatory_fields=[]) -> List[CDFTransaction]:
        root: ElementTree = ET.parse(file_obj).getroot()
        if root is None:
            return None

        if not CDFParser.__check_transmission_headers(root):
            return None

        return CDFParser.__extract_transactions(
            root, account_number_mask_begin, account_number_mask_end, default_values, mandatory_fields)
