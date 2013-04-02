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
    terms = []
    for _ in range(10):
        #set the position and direction for the new word
        startRow = random.randint(0, maxHeight - 1)
        startCol = random.randint(0, maxWidth  - 1)
        across = random.random() > 0.5 # select direction for the word: either across or down
        
        #find all crossing points with pre-existing words
        letters = []
        if across: #move horizontally
            letters = grid[startRow][startCol:]
        else:
            letters = [row[startCol] for row in grid[startRow:]]
        conditions = [(index, letter) for index, letter in enumerate(letters) if len(letter) > 0]
        #print "Conditions: " + str(conditions) + ", starting row: " + str(startRow) + ", starting column: " + str(startCol)
        # decide whether a dummy character is needed in the beginning of the word
        startdummy = True
        if across and startCol == 0 and not grid[startRow][startCol] == dummy:
            startdummy = False
        elif not across and startRow == 0 and not grid[startRow][startCol] == dummy:
            startdummy = False  
        # calculate the maximum length of the word
        maxWordLength = maxWidth - startCol if across else maxHeight - startRow
        if maxWordLength < 2: continue #again, can't have one-letter words
        
        #find a word that satisfies the above conditions, starting from a random place in the lexicon
        firstEntry = random.randint(0, len(lexicon) - 1)
        for term, definition in lexicon[firstEntry:]:
            if startdummy: term = dummy + term 
            if len(term) > maxWordLength or term in terms: 
                continue
            elif len(term) < maxWordLength:
                term = term + dummy
            satisfiedConditions = sum(i >= len(term) or term[i] == letter for i, letter in conditions)
            if satisfiedConditions == len(conditions):
                terms.append(term.replace(dummy, ''))
                for offset, letter in enumerate(term):
                    if across:
                        grid[startRow][startCol + offset] = letter
                    else:
                        grid[startRow + offset][startCol] = letter
                #print term
                #print "Crossword:\n" + "\n".join(str(row) for row in grid) #newline for each row
                break #word found 
    return grid, terms


lexicon = importDictionary()
grid, terms = generateCrossword((5,5), lexicon)
print "CROSSWORD:\n\n" + "\n".join(' '.join([x if len(x)>0 else '_' for x in row]) for row in grid)
print "\nTERMS: " + ', '.join(terms)
