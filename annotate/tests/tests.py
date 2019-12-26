import pytest
from annotate.utils import get_file_type
from annotate.exceptions import *


def test_get_file_type():
    try:
        get_file_type('something.txt') == FILE_TYPE_TXT
    except NoFileFoundError:
        assert True
