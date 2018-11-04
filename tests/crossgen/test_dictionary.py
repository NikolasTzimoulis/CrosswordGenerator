from __future__ import print_function, absolute_import

from src.crossgen import dictionary
import os


def test_deterministic_old():
    dictionary_file = os.path.join(os.path.expanduser('~'), '.crossgen', 'dictionary-en-5000.tsv')

    gt = dictionary.import_d(dictionary_file)
    gt2 = dictionary.import_d(dictionary_file)
    assert gt == gt2


def test_deterministic_new():
    dictionary_file = os.path.join(os.path.expanduser('~'), '.crossgen', 'dictionary-en-5000.tsv')

    res = dictionary.import_d2(dictionary_file)
    res2 = dictionary.import_d2(dictionary_file)
    assert res == res2


def test_same_word_lookup():
    dictionary_file = os.path.join(os.path.expanduser('~'), '.crossgen', 'dictionary-en-5000.tsv')

    gt = dictionary.import_d(dictionary_file)
    res = dictionary.import_d2(dictionary_file)

    assert gt['word_lookup'].keys() == res['word_lookup'].keys()

    for key in gt['word_lookup']:
        assert gt['word_lookup'][key] == tuple(res['word_lookup'][key])


def test_same_lexicon():
    dictionary_file = os.path.join(os.path.expanduser('~'), '.crossgen', 'dictionary-en-5000.tsv')

    gt = dictionary.import_d(dictionary_file)
    res = dictionary.import_d2(dictionary_file)

    assert gt['lexicon'].keys() == res['lexicon'].keys()
    for key in gt['lexicon'].keys():
        assert gt['lexicon'][key] == res['lexicon'][key]
