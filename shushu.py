import json

from card_data_parsers import VCFParser, ParserError

try:
    with open('input.vcf') as input_file:
        result = VCFParser.parse(
            file_obj=input_file,
            account_number_mask_begin=4,
            account_number_mask_end=4
        )
    print(json.dumps(result))
except ParserError as e:
    print(f'Omg! error {e}')