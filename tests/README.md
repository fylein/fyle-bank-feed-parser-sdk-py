# Tests

## Structure

All the parsers related test cases files are stored in `tests/card_data_parsers/<parser>/<p|n[0-9]>`.

`p|n[0-9]` = Positive (p) | Negative (n) test case`

e.g. `tests/card_data_parsers/amex/p1`


For each test case directory contains -
  - args.json - Arguments to pass to `parse` function
  - data - Input file contaning parser encoded data
  - expected.json - If positive test case i.e. with output
  - expected.txt - If negative test case i.e. with error message


Above test cases files are dynamically loaded as `pytest` test cases using `tests/card_data_parsers/test_bank_feed_parsers.py`.


To run tests, run this from root path
`python -m pytest -o log_cli=true --log-cli-level=DEBUG -vv`.
