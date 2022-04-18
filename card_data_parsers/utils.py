from typing import List
from datetime import datetime
import hashlib
import pycountry
import numbers


country_code_to_currency_dict = {
    "040": "EUR",  # Austria
    "076": "BRL",  # Brazil
    "276": "EUR",  # Germany
    "380": "EUR",  # Italy
    "528": "PAB",  # Panama
    "591": "PAB",  # Panama
    "620": "EUR",  # Portugal
    "642": "RON",  # Romania
    "705": "EUR",  # Slovenia
    "724": "EUR",  # Spain
    "792": "TRY",  # Turkey
    "804": "UAH",  # Ukraine
    "862": "VEF",  # Venezuela
    "704": "VNM"   # Vietnam
}


def get_currency_from_country_code(country_code):
    try:
        currency = pycountry.currencies.get(numeric=country_code).alpha_3
    except KeyError:
        currency = country_code_to_currency_dict[country_code] if country_code in country_code_to_currency_dict else None
    return currency


def is_amount(str):
    if str == None or len(str) == 0:
        return False
    try:
        float(str)
        return True
    except ValueError:
        return False


def mask_card_number(card_number, unmask_begin, unmask_end):
    # UnMask in the begining and the end of the account number
    try:
        if int(unmask_begin) + int(unmask_end) <= len(card_number):
            unmask_begin = int(unmask_begin)
            unmask_end = int(unmask_end)
        else:
            unmask_begin = 0
            unmask_end = 4
    except Exception as e:
        # defult mask ************1234
        return "*" * (len(card_number) - 4) + card_number[-4:]

    card_number = card_number[0:unmask_begin] + "*" * (
        len(card_number) - (unmask_begin + unmask_end)) + card_number[-unmask_end:]
    return card_number


def remove_leading_zeros(value, min_len=None):
    """
    Removes leading zeros.
    but maintaining min length - https://docs.python.org/3/library/stdtypes.html?highlight=zfill#str.zfill
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


def get_iso_date_string(date_string, date_format):
    if date_string != '':
        iso_date_string = datetime.strptime(date_string.strip(), date_format)
        # hack for timezones: set time to 10 o clock
        iso_date_string = iso_date_string.replace(hour=10)
        iso_date_string = iso_date_string.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        iso_date_string = None

    return iso_date_string


def filter_none_values(d: dict) -> dict:
    return {k: v
            for k, v in d.items()
            if v is not None}


def has_null_value_for_attrs(o: object, attrs: List[str]) -> bool:
    for attr in attrs:
        value = getattr(o, attr, None)
        if value is None or value == '':
            return True
    return False


def has_null_value_for_keys(d: dict, keys: List[str]) -> bool:
    for key in keys:
        if (key not in d) or d[key] == '':
            return True
    return False


def expand_with_default_values(d: dict, default_values: dict) -> None:
    for key in default_values:
        if (d.get(key) is None or d[key] == '') and (default_values[key] is not None):
            d[key] = default_values[key]


def generate_external_id(text):
    hash_object = hashlib.md5(text.encode('utf-8'))
    hex_dig = hash_object.hexdigest()
    return hex_dig
