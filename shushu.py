from card_data_parsers import VCFParser, ParserError
from simple_slack import SimpleSlack

try:
    file = "/Users/iinbar@tripactions.com/Downloads/input.vcf"
    with open(file) as input_file:
        SimpleSlack.post_message_to_slack(f"Processing local file {file}")
        result = VCFParser.parse(
            file_obj=input_file,
            account_number_mask_begin=4,
            account_number_mask_end=4
        )
    #print(json.dumps(result))
except ParserError as e:
    print(f'Omg! error {e}')
