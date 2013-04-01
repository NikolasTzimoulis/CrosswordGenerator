# This Python file uses the following encoding: utf-8

import random, re

def importDictionary():
    filename = 'dictionary-en.tsv'
    dictionary = open(filename, 'r')
    lexicon = []
    for line in dictionary:
        lang, term, pos, definition = line.split('\t')
        if len(term) < 2 or not re.match("^[A-Za-z]*$", term):
            continue #skip one-letter words
        lexicon.append((term, definition))
    return lexicon

def generateCrossword(dimensions, lexicon):
    maxHeight, maxWidth = dimensions
    grid = [[""]*maxWidth for _ in range(maxHeight)]
    print grid
    for _ in range(5):
        #set the position and direction for the new word
        startRow, startCol = (random.randint(0, maxHeight - 1), random.randint(0, maxWidth - 1))
        direction = random.random() > 0.5 # True = horizontal
        #find all crossing points with pre-existing words
        letters = []
        if direction: #move horizontally
            letters = grid[startRow][startCol:]
        else:
            letters = [row[startCol] for row in grid[startRow:]]
        letterPos = 0
        conditions = []
        for letter in letters:
            if len(letter) > 0:
                conditions.append((letterPos, letter))
                letterPos += 1
        print "Conditions: " + str(conditions) + str(startRow) + str(startCol)
        #find all the words that satisfy the above conditions
        maxWordLength = maxWidth - startCol if direction else maxHeight - startRow
        if maxWordLength < 2:
            continue #again, can't have one-letter words
        firstEntry = random.randint(0, len(lexicon) - 1)
        for entry in lexicon[firstEntry:]:
            term = entry[0]
            if len(term) > maxWordLength:
                continue
            satisfiedConditions = 0
            for c in conditions:
                if c[0] < len(term) and term[c[0]] != c[1]:
                    break
                else:
                    satisfiedConditions += 1
            if satisfiedConditions == len(conditions):
                wordIndex = 0
                if direction:
                    for col in range(startCol, len(term) + startCol):
                        grid[startRow][col] = term[wordIndex]
                        wordIndex += 1
                else:
                    for row in range(startRow, len(term) + startRow):
                        grid[row][startCol] = term[wordIndex]
                        wordIndex += 1
                break #word found
        print "Crossword: "
        crossword = "\n".join(str(row) for row in grid) #newline for each row
        print crossword


lexicon = importDictionary()
generateCrossword((5,5), lexicon)
