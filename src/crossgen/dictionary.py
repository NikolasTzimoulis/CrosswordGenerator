from __future__ import print_function, absolute_import

from collections import namedtuple

import csv
import sys

from src.crossgen import constants


def wiktionary_keys():
    return ['lang', 'term', 'pos', 'definition']


def group_by_word_len(dictionary):
    pass


def count_lines(filename):
    with open(filename, 'r') as fin:
        return sum(1 for _ in fin)


def load_dictionary(filename):
    with open(filename, 'r') as fin:
        data = csv.DictReader(fin, fieldnames=wiktionary_keys(), delimiter='\t', quotechar='|')
        Word = namedtuple('Word', 'lang term pos definition')
        for item in data:
            item['term'] = item['term'].upper()
            yield Word(**item)


def filter_dictionary(data, min_term_len=constants.minWordLength_absolute):
    long_enough = (item for item in data if len(item.term) >= min_term_len)
    long_enough_alphas = (item for item in long_enough if item.term.isalpha())
    return long_enough_alphas


def import_d2(filename):
    print('Importing dictionary...')
    data = load_dictionary(filename)
    total_lines = count_lines(filename)
    lexicon = {}
    word_lookup = {word_id: item for word_id, item in enumerate(filter_dictionary(data))}

    for word_id, item in word_lookup.items():
        print(f'{word_id}/{total_lines} words imported ({word_id * 100 / total_lines}%)', end='\r', flush=True)
        sys.stdout.flush()
        word_length = len(item.term)
        lw = {} if word_length not in lexicon else lexicon[word_length]
        for idx, letter in enumerate(item.term):
            lw[(idx, letter)] = {word_id} if (idx, letter) not in lw else lw[(idx, letter)] | {word_id}
        lexicon[word_length] = lw
    print('\t[DONE]')
    return {'lexicon': lexicon, 'word_lookup': word_lookup}


def import_d(filename):
    print('Importing dictionary...')
    dictionary_raw = open(filename, 'r')
    total_lines = count_lines(filename)
    lexicon = {}
    word_lookup = {}
    word_id = 0
    for line in dictionary_raw:
        print(f'{word_id}/{total_lines} words imported ({word_id * 100 / total_lines}%)', end='\r', flush=True)
        sys.stdout.flush()
        lang, term, pos, definition = line.strip('\n').split('\t')
        word_length = len(term)
        if word_length >= constants.minWordLength_absolute and term.isalpha():
            if word_length not in lexicon:
                lexicon[word_length] = {}
            for index, letter in enumerate(term):
                if (index, letter.upper()) not in lexicon[word_length]:
                    lexicon[word_length][(index, letter.upper())] = set([])
                lexicon[word_length][(index, letter.upper())].add(word_id)
                word_lookup[word_id] = (lang, term.upper(), pos, definition)
            word_id += 1
    dictionary_raw.close()
    print('\t[DONE]')
    return {'lexicon': lexicon, 'word_lookup': word_lookup}
