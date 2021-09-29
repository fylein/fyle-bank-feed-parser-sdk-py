# fyle-bank-feed-parser-sdk-py

[![test](https://github.com/fylein/fyle-bank-feed-parser-sdk-py/actions/workflows/test.yml/badge.svg)](https://github.com/fylein/fyle-bank-feed-parser-sdk-py/actions/workflows/test.yml) [![pythonpublish](https://github.com/fylein/fyle-bank-feed-parser-sdk-py/actions/workflows/pythonpublish.yml/badge.svg)](https://github.com/fylein/fyle-bank-feed-parser-sdk-py/actions/workflows/pythonpublish.yml)

Bank feeds parsers collection.


## Usage

To use the VCF parser, use the VCFParser class:

```
from card_data_parsers import VCFParser, ParserError

try:
  with open(dir + '/input.vcf') as input_file:
    result = VCFParser.parse(
      file_obj=input_file,
      account_number_mask_begin=4,
      account_number_mask_end=4
    )
  print(result)
except ParserError as e:
  print(f'Omg! error {e}')
```

Similarly, you can use AmexParser, CDFParser, S3DFParser and HappayParser for the right file types.


## Development

```
pip install -r requirements.txt
```
Check implemented parsers for examples.


### Run tests

```
chmod +x text.sh

./test.sh
```


## Releasing a new version

When a new version is ready for release, create a git tag with version number like -
```
git tag v0.1.0
git push origin v0.1.0
```


## Versioning semantics

The parse method is supposed to return a list of transactions. This is a list of python dict objects that looks like this:

```
[{"bank_name": "Test BANK", "vendor": "Test", "sync_type": "BANK FEED - VCF", "transaction_type": "debit", "currency": "EUR", "amount": "124.74", "transaction_date": "2018-11-30T10:00:00.000000Z", "account_number": "4142********6333", "transaction_dt": "2018-11-30T10:00:00.000000Z", "external_id": "b2a242d1d9814394b594044b77f36f2f"}]
```

If there is any non-backward compatible change to this structure e.g. a key is deleted, then bump up major number. Otherwise, bump up minor number.
