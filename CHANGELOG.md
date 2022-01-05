# Change Log

## [0.6.0]

### Changed

- Added AMEX transaction_id as `transaction_id` in AMEX Parser.

## [0.5.0]

### Changed

- Updated `cdf_parser.py` to parse all of the `CorporateEntity` entities.

## [0.4.0]

### Changed

- Updated `vcf_parser.py` to parse `000...` amounts as zero.

## [0.3.0]

### Changed

- Changed `transaction_dt` to include milliseconds. Updated function `get_iso_date_string`.
  - Affects `external_id`
