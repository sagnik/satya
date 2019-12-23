import pytest
from annotate.utils import get_file_type
from annotate.consts import FILE_TYPE_CONLL, FILE_TYPE_TXT, FILE_TYPE_JSON


def test_get_file_type():
    assert get_file_type('something.txt') == FILE_TYPE_TXT
    assert get_file_type('something.json') == FILE_TYPE_JSON
    assert get_file_type('something.conll') == FILE_TYPE_CONLL
