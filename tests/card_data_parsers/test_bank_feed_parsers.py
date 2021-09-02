import pytest
import os
from glob import glob
import json
from jsondiff import diff
import logging
from dataclasses import asdict
from card_data_parsers import AmexParser, CDFParser, VCFParser, HappayParser, S3DFParser, ParserError, filter_none_values


logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger('test_card_data_parsers')
logger.setLevel(logging.DEBUG)


PARSERS_TESTS_DIR_MAPPINGS = {
    'amex': AmexParser,
    'cdf': CDFParser,
    'vcf': VCFParser,
    'happay': HappayParser,
    's3df': S3DFParser,
}


def get_test_sets():
    test_sets = []

    for parser_dir in PARSERS_TESTS_DIR_MAPPINGS:
        test_case_paths = glob(f'./tests/card_data_parsers/{parser_dir}/*')
        for test_case_path in test_case_paths:
            test_sets.append(
                (PARSERS_TESTS_DIR_MAPPINGS[parser_dir], test_case_path))

    return test_sets


@pytest.mark.parametrize('parser,test_case_path', get_test_sets())
def test_parser(parser, test_case_path):  
    assert parser is not None
    assert test_case_path is not None

    is_negative = os.path.basename(test_case_path).startswith('n')

    expected = None
    if is_negative:
        with open(os.path.join(test_case_path, 'expected.txt')) as expected_file:
            expected = expected_file.read()
    else:
        with open(os.path.join(test_case_path, 'expected.json')) as expected_file:
            expected = json.loads(expected_file.read())

    actual = None
    with open(os.path.join(test_case_path, 'data')) as data_file:
        with open(os.path.join(test_case_path, 'args.json')) as args_file:
            args = json.loads(args_file.read())
            try:
                result = parser.parse(file_obj=data_file, **args)
                if not is_negative:
                    actual = [filter_none_values(asdict(item)) for item in result]
            except ParserError as e:
                if is_negative:
                    actual = str(e)
                else:
                    raise e

    if is_negative:
        assert actual is not None, 'Actual error is None'
        assert expected == actual, 'Expected and actual value are not matching'
    else:
        jd = diff(expected, actual)
        assert jd == {},  'Expected and actual json has difference'
