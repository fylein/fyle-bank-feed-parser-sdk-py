# Change Log

## [0.9.0]

### Changed

- Updated `HappayParser` to set `foreign_amount` and `foreign_currency` to `None`, if `foreign_currency` is same as `currency`.

## [0.8.0]

### Changed

- Fetching the `post_date` from amex, cdf, s3df and vcf parsers.

## [0.7.0]

### Changed

- Provided `None` as default value for `account_number_mask_begin` and `account_number_mask_end` arguments, to evade card masking.

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
