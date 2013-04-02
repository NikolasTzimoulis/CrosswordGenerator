# This Python file uses the following encoding: utf-8

import random, re

dummy = '@'

def importDictionary():
    filename = 'dictionary-en.tsv'
    dictionary = open(filename, 'r')
    lexicon = []
    for line in dictionary:
        lang, term, pos, definition = line.split('\t')
        if len(term) >= 2 and term.isalpha():
            lexicon.append((term.upper(), definition))        
    return lexicon

def generateCrossword(dimensions, lexicon):
    maxHeight, maxWidth = dimensions
    grid = [[""]*maxWidth for _ in range(maxHeight)]
    print grid
    terms = []
    for _ in range(10):
        #set the position and direction for the new word
        startRow = random.randint(0, maxHeight - 1)
        startCol = random.randint(0, maxWidth  - 1)
        across = random.random() > 0.5
        
        #find all crossing points with pre-existing words
        letters = []
        if across: #move horizontally
            letters = grid[startRow][startCol:]
        else:
            letters = [row[startCol] for row in grid[startRow:]]
        conditions = [(index, letter) for index, letter in enumerate(letters) if len(letter) > 0]
        #print "Conditions: " + str(conditions) + ", starting row: " + str(startRow) + ", starting column: " + str(startCol)
        
        #find all the words that satisfy the above conditions
        maxWordLength = maxWidth - startCol if across else maxHeight - startRow
        if maxWordLength < 2: continue #again, can't have one-letter words
        firstEntry = random.randint(0, len(lexicon) - 1)
        for term, definition in lexicon[firstEntry:]:
            if len(term) > maxWordLength or term in terms: continue
            term = term + dummy # extend the term with a dummy character
            satisfiedConditions = sum(i >= len(term) or term[i] == letter for i, letter in conditions)
            if satisfiedConditions == len(conditions):
                terms.append(term[:-1])
                for offset, letter in enumerate(term):
                    if across and startCol + offset < maxWidth:
                        grid[startRow][startCol + offset] = letter
                    elif startRow + offset < maxHeight:
                        grid[startRow + offset][startCol] = letter
                #print term
                #print "Crossword:\n" + "\n".join(str(row) for row in grid) #newline for each row
                break #word found
    return grid, terms

def test():
    pass

lexicon = importDictionary()
grid, terms = generateCrossword((5,5), lexicon)
print "CROSSWORD:\n" + "\n".join(str(row) for row in grid)
print "TERMS:" + str(terms)
