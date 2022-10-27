# solid-credit-card-feed-lambda

Solid lambda function for processing credit card feeds (VCF)

## Environment

- S3 bucket for feed files (SOLID_SFTP_BUCKET)
  - The bucket should be accessible via SFTP using "AWS transfer family".
- S3 bucket for processed files (SOLID_PARSED_BUCKET)
- SQS queue (SOLID_SQS_QUEUE)
- Lambda function that is triggered by new files in the SOLID_SFTP_BUCKET, with the following permissions:
  - Read permission to SOLID_SFTP_BUCKET
  - Write permission to SOLID_PARSED_BUCKET
  - Permission to send SQS messages in SOLID_SQS_QUEUE

## Process

1. Credit card company uploads VCF files to the SFTP server.
2. Lambda triggers the handler `vcf_parser.handler`, which convert the files to JSON files and sends SQS message to the queue.
3. Liquid servers read the SQS queue, reads the message that include the name of the new JSON files, and load its content from S3 into temporary database tables.
