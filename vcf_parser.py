from card_data_parsers import VCFParser, ParserError
import boto3
import json
import os

print('Loading function')

solid_parsed_bucket = os.environ['SOLID_PARSED_BUCKET']
solid_sqs_queue = os.environ['SOLID_SQS_QUEUE']
s3_client = boto3.client('s3')
sqs = boto3.resource('sqs')

def handler(event, context):
    for record in event['Records']:

        bucket = record['s3']['bucket']['name']
        input_file = record['s3']['object']['key']

        if input_file.endswith('.vcf'):
            try:
                output_file = input_file.replace(".vcf", ".json")
                obj = s3_client.get_object(Bucket=bucket, Key=input_file)
                body = obj['Body'].read().decode('utf-8').splitlines()

                result = VCFParser.parse(
                    file_obj=body,
                    account_number_mask_begin=4,
                    account_number_mask_end=4
                )
                body = json.dumps(result).encode('utf-8')
                s3_put = s3_client.put_object(Body=body, Bucket=solid_parsed_bucket, Key=output_file)
                queue = sqs.get_queue_by_name(QueueName=solid_sqs_queue)

                # Create a new message
                response = queue.send_message(MessageBody=json.dumps(s3_put))

                # The response is NOT a resource, but gives you a message ID and MD5
                print(response.get('MessageId'))
                print(response.get('MD5OfMessageBody'))
            except ParserError as e:
                print(f'Omg! error {e}')
        else:
            print(f'File {input_file} is not a VCF file')