# Change Log

## [0.15.0]

### Changed

- Bug fixed in `VCFParser` to parse all transaction blocks present in a VCF feed data.

## [0.14.0]

### Changed

- Fixed issue regarding fetching currency other than ISO_4217.

## [0.13.0]

### Changed

- Added support for latest ISO_4217 currencies.

## [0.12.0]

### Changed

- Updated `CDFParser` and `S3DFParser` to parse merchant category codes from the feed data.

## [0.11.0]

### Changed

- Bug fixed in `AmexParser` for correctly parsing Merchant Category Codes (MCC).

## [0.10.0]

### Changed

- Updated `VCFParser` to parse all transaction blocks present in a VCF feed data.

## [0.9.0]

### Changed

- Updated parsers to set `foreign_amount` and `foreign_currency` to `None`, if `foreign_currency` is same as `currency` or if `foreign_currency` or `foreign_amount` is `None`.

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
