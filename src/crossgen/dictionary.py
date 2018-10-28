from src.crossgen import constants, decorators

import csv
import os


@decorators.profile
def import_dict_new(filenameRaw):
    print('Importing dictionary...')
    dictionaryRaw = open(filenameRaw, 'r')
    reader = csv.DictReader(dictionaryRaw, fieldnames=constants.fieldnames, delimiter='\t', quotechar='"')
    lexicon = {}
    wordLookup = {}
    wordId = 0
    for item in reader:
        wordLength = len(item['term'])
        if wordLength >= constants.minWordLength_absolute and item['term'].isalpha():
            if wordLength not in lexicon:
                lexicon[wordLength] = {}
            for index, letter in enumerate(item['term']):
                if (index, letter.upper()) not in lexicon[wordLength]: lexicon[wordLength][(index, letter.upper())] = set([])
                lexicon[wordLength][(index, letter.upper())].add(wordId)
                wordLookup[wordId] = (item['term'].upper(), item['definition'])
            wordId += 1
    dictionaryRaw.close()
    print('\t[DONE]')
    return lexicon, wordLookup


@decorators.profile
def importDictionary(filenameRaw):
    print('Importing dictionary...')
    dictionaryRaw = open(filenameRaw, 'r')
    lexicon = {}
    wordLookup = {}
    wordId = 0
    for line in dictionaryRaw:
        lang, term, pos, definition = line.split('\t')
        wordLength = len(term)
        if wordLength >= constants.minWordLength_absolute and term.isalpha():
            if wordLength not in lexicon: lexicon[wordLength] = {}
            for index, letter in enumerate(term):
                if (index, letter.upper()) not in lexicon[wordLength]: lexicon[wordLength][(index, letter.upper())]=set([])
                lexicon[wordLength][(index, letter.upper())].add(wordId)
                wordLookup[wordId] = (term.upper(), definition)
            wordId += 1
    dictionaryRaw.close()
    print('\t[DONE]')
    return lexicon, wordLookup
