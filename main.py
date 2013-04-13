# This Python file uses the following encoding: utf-8

import random, copy, itertools
import decorators
from decorators import profile

dummy = '@'
maxRounds = 10**3
minWordLength_absolute = 2
maxCandidates = 3
profiled = decorators.profiled

@profile
def importDictionary():
    print "Importing dictionary...",
    filenameRaw = 'dictionary-en.tsv'
    dictionaryRaw = open(filenameRaw, 'r')
    lexicon = {}
    wordLookup = {}
    wordId = 0
    for line in dictionaryRaw:
        lang, term, pos, definition = line.split('\t')
        wordLength = len(term)
        if wordLength >= minWordLength_absolute and term.isalpha():
            if wordLength not in lexicon: lexicon[wordLength] = {} 
            for index, letter in enumerate(term):
                if (index, letter.upper()) not in lexicon[wordLength]: lexicon[wordLength][(index, letter.upper())]=set([])
                lexicon[wordLength][(index, letter.upper())].add(wordId)
                wordLookup[wordId] = (term.upper(), definition)
            wordId += 1
    dictionaryRaw.close()
    print "\t[DONE]"
    return lexicon, wordLookup

@profile
def generateCrossword(size, lexicon, wordLookup):
    print "Generating crossword",
    maxHeight = maxWidth = size
    startOrder = set(itertools.combinations_with_replacement(range(size),2))
    startOrder = startOrder.union([(x[1], x[0]) for x in startOrder])
    startOrder = sorted(startOrder, cmp=lambda x,y: x[0]+x[1]-y[0]-y[1]+10*(min(x)-min(y)))
    terms = {}
    grid = [[""]*maxWidth for _ in range(maxHeight)]
    frontStates = [ (terms, grid) ]
    deadEndStates = []
    for i in range(maxRounds):
        terms, grid = copy.deepcopy(frontStates[-1])
        
        if i%(maxRounds/10)==0: print '.', # progress bar; one dot every 10% of the rounds
        
        # find a good starting position for the next word
        startRow, startCol, across, conditions = getStartPos(startOrder, grid, terms)
        
        # decide whether a dummy character is needed in the beginning of the word
        startdummy = shouldStartDummy(startRow, startCol, across, grid)
          
        # calculate the maximum and minimum length of the word 
        allowedWordLengths = getAllowedWordLengths(maxHeight, maxWidth, startRow, startCol, across, conditions)

        if max(allowedWordLengths) < minWordLength_absolute: continue #again, can't have one-letter words
        
        conditions = filter(lambda x: x[1]!=dummy, conditions) # dummy conditions are not needed (I think)
        
        #find a word that satisfies the above conditions
        wordFound = False
        # iterate through all valid word lengths
        for wordLength in reversed(allowedWordLengths):
            # words of maxWordLength should only be considered if we don't need a dummy char at the beginning of the word
            if startdummy and wordLength == max(allowedWordLengths): continue 
            subLexicon = lexicon[wordLength]
            # only conditions up to the wordLength-th word need apply
            subConditions = filter(lambda x: x[0]<wordLength, conditions) 
            # find all the words that satisfy all conditions
            fittingWords = getFittingWords(subConditions, startdummy, subLexicon)
            if len(fittingWords) > 0:
                term = random.choice(fittingWords) # choose one of the fitting words randomly
                terms[(startRow, startCol, across)] = term # add new word to list of terms
                # add dummy chars at the beginning and end of the new word as necessary
                if startdummy: term = dummy + term 
                if len(term) < max(allowedWordLengths): term = term + dummy
                # place new term on grid
                try:
                    grid = placeTermToGrid(term, startRow, startCol, across, grid)
                except:
                    pass
                newState = (copy.deepcopy(terms), copy.deepcopy(grid))
                if newState not in deadEndStates: # reject if we have already tried this word
                    frontStates.append(newState)
                    #printCrossWord(grid)
                    wordFound = True
                    break
                else: # revert grid and terms to what they were before adding the rejected word
                    terms, grid = copy.deepcopy(frontStates[-1])
                    
        if not wordFound: # we need to backtrack!
            deadEndStates.append( frontStates.pop() )
    for t, g in frontStates + deadEndStates: #find best state!
        if len(t) > len(terms):
            terms, grid = t, g
    print "\t[DONE]"
    return grid, terms

@profile
def getStartPos(startOrder, grid, terms):
    # find free positions close to left-uppermost corner
    startCandidates = []
    for startRow, startCol in startOrder:
        if len(startCandidates) >= maxCandidates: break
        for across in [True, False]:
            if isValidStart(grid, terms, startRow, startCol, across):
                startCandidates.append((startRow, startCol, across))    
    #find all crossing points with pre-existing words for each candidate
    condList = map(lambda x: getConditions(grid, x[0], x[1], x[2]), startCandidates)
    # best candidate is the one with the most crossings
    condLengths = map(len, condList)
    bestPosIndex = condLengths.index(max(condLengths))
    startRow, startCol, across = startCandidates[bestPosIndex]
    conditions = condList[bestPosIndex]
    return startRow, startCol, across, conditions

@profile
def isValidStart(grid, terms, startRow, startCol, across):
    # iterate backwards beginning from the starting position
    it = reversed(range( (startCol if across else startRow) + 1 )) 
    for i in it:
        r, c = (startRow, i) if across else (i, startCol)
        # if you find a starting position of a previous word 
        # before you find a dummy char or the edge of the crossword
        #then this starting position is invalid 
        if (r, c, across) in terms:
            return False
        elif grid[r][c] == dummy:
            break
    return True

@profile
def getConditions(grid, startRow, startCol, across):
    letters = []
    if across: #move horizontally
        letters = grid[startRow][startCol:]
    else:
        letters = [row[startCol] for row in grid[startRow:]]
    return [(index, letter) for index, letter in enumerate(letters) if len(letter) > 0]

@profile
def shouldStartDummy(startRow, startCol, across, grid):
    startdummy = True
    if across and startCol == 0 and not grid[startRow][startCol] == dummy:
        startdummy = False
    elif not across and startRow == 0 and not grid[startRow][startCol] == dummy:
        startdummy = False
    return startdummy

@profile        
def getAllowedWordLengths(maxHeight, maxWidth, startRow, startCol, across, conditions):
    allowed = []
    minWordLength = 1
    while (minWordLength in [x[0] for x in conditions]) and (minWordLength, dummy) not in conditions:
        minWordLength += 1
    for wordLength in range(minWordLength, maxWidth - startCol + 1 if across else maxHeight - startRow + 1):
        if wordLength not in [x[0] for x in conditions] or (wordLength, dummy) in conditions: 
            allowed.append(wordLength)   
            if (wordLength, dummy) in conditions:
                break
    return allowed

@profile
def getFittingWords(subConditions, startdummy, subLexicon):
    # calculate the lists of words that satisfy each condition
    # their intersection are the words that satisfy all conditions 
    if len(subConditions) > 0: 
        fittingWordSets = map(lambda x: subLexicon[ (x[0]-startdummy, x[1]) ], subConditions)
        fittingWordIds = reduce(lambda x,y: x.intersection(y), fittingWordSets)
    else: # if there are no conditions, take all words!
        fittingWordSets = subLexicon.values()
        fittingWordIds = reduce(lambda x,y: x.union(y), fittingWordSets)
    fittingWords = map(lambda x: wordLookup[x][0], fittingWordIds)
    return fittingWords

@profile
def placeTermToGrid(term, startRow, startCol, across, grid):
    # iterate through the positions on the grid where the term must be placed
    # and put in the letters of the term one by one
    for offset, letter in enumerate(term):
        if across:
            if grid[startRow][startCol + offset] != letter and grid[startRow][startCol + offset] != "":
                raise Exception("Invalid letter placement: " + letter + " -> " + grid[startRow][startCol + offset])
            grid[startRow][startCol + offset] = letter
        else:
            if grid[startRow + offset][startCol] != letter and grid[startRow + offset][startCol] != "":
                raise Exception("Invalid letter placement: " + letter + " -> " + grid[startRow + offset][startCol])
            grid[startRow + offset][startCol] = letter
    return grid
    

def printCrossWord(grid):
    print "\nCrossword:\n\n" + "\n".join(' '.join([x if len(x)>0 else '_' for x in row]) for row in grid)

lexicon, wordLookup = importDictionary()
grid, terms = generateCrossword(8, lexicon, wordLookup)
printCrossWord(grid)
print "\nTerms: " + ', '.join(terms.values())
decorators.printProfiled()
