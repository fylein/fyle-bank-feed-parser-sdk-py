from abc import ABCMeta, abstractmethod
from typing import List, Iterable
from ..models import Transaction


class Parser:

    @staticmethod
    @abstractmethod
    def parse(
        file_obj: Iterable[str],
        account_number_mask_begin: int,
        account_number_mask_end: int,
        default_values={},
        mandatory_fields=[]
    ) -> List[Transaction]:
        raise NotImplementedError()


class ParserError(Exception):
    pass
