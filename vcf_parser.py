from card_data_parsers import VCFParser, ParserError
import boto3
import json

print('Loading function')

s3_client = boto3.client('s3')

def handler(event, context):
    for record in event['Records']:

        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        if key.endswith('vcf'):
            try:
                obj = s3_client.get_object(Bucket=bucket, Key=key)
                body = obj['Body'].read().decode('utf-8').splitlines()

                result = VCFParser.parse(
                    file_obj=body,
                    account_number_mask_begin=4,
                    account_number_mask_end=4
                )
                body = json.dumps(result).encode('utf-8')
                s3_client.put_object(Body=body, Bucket=bucket, Key='output.json')

            except ParserError as e:
                print(f'Omg! error {e}')
        else:
            print(f'File {key} is not a VCF file')