# This Python file uses the following encoding: utf-8

import random, re

dummy = '@'
maxRounds = 100

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
    terms = {}
    for i in range(maxRounds):
        if i%(maxRounds/10)==0: print '.',
        #set the position and direction for the new word
        across = random.random() > 0.5 # select direction for the word: either across or down
        # find position closest to left-uppermost corner that does not have a word starting from it 
        startRow = startCol = 0
        while (startRow, startCol, across) in terms.keys():
            if startRow == startCol:
                startRow += 1
            elif startRow > startCol:
                startCol, startRow = startRow, startCol
            else:
                startRow = startCol
        
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
                terms[(startRow, startCol, across)] = term.replace(dummy, '')
                for offset, letter in enumerate(term):
                    if across:
                        grid[startRow][startCol + offset] = letter
                    else:
                        grid[startRow + offset][startCol] = letter
                #print term
                #print "Crossword:\n" + "\n".join(str(row) for row in grid) #newline for each row
                break #word found 
    return grid, terms

def printCrossWord(grid):
    print "CROSSWORD:\n\n" + "\n".join(' '.join([x if len(x)>0 else '_' for x in row]) for row in grid)


lexicon = importDictionary()
grid, terms = generateCrossword((5,5), lexicon)
printCrossWord(grid)
print "\nTERMS: " + ', '.join(terms.values())
