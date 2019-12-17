import pytest
from annotate.utils import biofy, de_biofy, is_labeled, towkf_sentence


def test_biofy():
    """ test biofy"""
    content = 'Barack Obama'
    label = 'PER'
    assert biofy(content, label) == 'Barack/B-PER Obama/I-PER'


def test_debiofy():
    """test de-biofy"""
    content = 'x/B-PER y/I-PER/B-LOC z/I-PER/I-LOC/B-ORG'
    assert de_biofy(content) == 'x/B-PER y/I-PER/B-LOC z/I-PER/I-LOC'
    assert de_biofy(content, depth=2) == 'x/B-PER y/I-PER z/I-PER'
    assert de_biofy(content, depth=3) == 'x y z'
    content = (
        'www.abc.com/some_page/B-PER www.abc.com/some_page/another/I-PER/B-LOC '
        'www.abc.com/some_page/another/another/I-PER/I-LOC/B-ORG'
    )
    assert (
        de_biofy(content) == 'www.abc.com/some_page/B-PER www.abc.com/some_page/another/I-PER/B-LOC '
        'www.abc.com/some_page/another/another/I-PER/I-LOC'
    )
    assert (
        de_biofy(content, depth=2) == 'www.abc.com/some_page/B-PER www.abc.com/some_page/another/I-PER '
        'www.abc.com/some_page/another/another/I-PER'
    )
    assert (
        de_biofy(content, depth=3) == 'www.abc.com/some_page www.abc.com/some_page/another '
        'www.abc.com/some_page/another/another'
    )


def test_is_labeled():
    """is the selected text labeled"""
    labels = ['PER', 'ORG']
    text = 'Barack/B-PER Obama/I-PER'
    assert is_labeled(text, labels)
    text = 'www.something/com Ford/I-ORG'
    assert not is_labeled(text, labels)
    text = 'x/I-PER y/I-PER'
    assert not is_labeled(text, labels)
    text = 'x/B-PER y/B-ORG'
    assert not is_labeled(text, labels)
    text = 'barack/B-PER hussein/I-PER obama/I-PER'
    following_text = 'jr/I-PER was born in'
    assert not is_labeled(text, labels, following_text)


def test_towkf_sentence():
    """test towkf_sentence
    :return:
    """
    text = 'Barack/B-PER/B-PRES Obama/I-PER/I-PRES was born in 1961/B-DATE'
    result_one = [('Barack', 'B-PER'), ('Obama', 'I-PER'), ('was', 'O'), ('born', 'O'), ('in', 'O'), ('1961', 'B-DATE')]
    result_two = [
        ('Barack', 'B-PER', 'B-PRES'),
        ('Obama', 'I-PER', 'I-PRES'),
        ('was', 'O', 'O'),
        ('born', 'O', 'O'),
        ('in', 'O', 'O'),
        ('1961', 'B-DATE', 'O'),
    ]
    result_three = [
        ('Barack', 'B-PER', 'B-PRES', 'O'),
        ('Obama', 'I-PER', 'I-PRES', 'O'),
        ('was', 'O', 'O', 'O'),
        ('born', 'O', 'O', 'O'),
        ('in', 'O', 'O', 'O'),
        ('1961', 'B-DATE', 'O', 'O'),
    ]
    assert towkf_sentence(text) == result_one
    assert towkf_sentence(text, 2) == result_two
    assert towkf_sentence(text, 3) == result_three

    text = 'Barack/B-PER/B-PRES     Obama/I-PER/I-PRES was born    in 1961/B-DATE'
    assert towkf_sentence(text) == result_one
    assert towkf_sentence(text, 2) == result_two
    assert towkf_sentence(text, 3) == result_three

    text = 'a/B-x b/I-x/B-y c/d/e/I-x/I-y/B-z'
    result_one = [('a', 'B-x'), ('b', 'I-x'), ('c/d/e', 'I-x')]
    result_two = [('a', 'B-x', 'O'), ('b', 'I-x', 'B-y'), ('c/d/e', 'I-x', 'I-y')]
    result_three = [('a', 'B-x', 'O', 'O'), ('b', 'I-x', 'B-y', 'O'), ('c/d/e', 'I-x', 'I-y', 'B-z')]
    assert towkf_sentence(text, 1) == result_one
    assert towkf_sentence(text, 2) == result_two
    assert towkf_sentence(text, 3) == result_three
