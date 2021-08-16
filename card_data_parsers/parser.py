from abc import ABCMeta, abstractmethod
from typing import List
from .transaction import Transaction

class Parser:

    @staticmethod
    @abstractmethod
    def parse(
        file_obj,
        account_number_mask_begin: int,
        account_number_mask_end: int,
        default_values={},
        mandatory_fields=[]
    ) -> List[Transaction]:
        raise NotImplementedError()


class ParserError(Exception):
    pass
