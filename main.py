# This Python file uses the following encoding: utf-8

import random, copy, itertools
import decorators
from decorators import profile

dummy = '@'
maxRounds = 10**3
minWordLength_absolute = 2
maxCandidates = 5
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
        # adjust conditions to take startdummy into account
        conditions = map(lambda x: (x[0]-startdummy, x[1]), conditions) # one square offset if startdummy
        conditions = filter(lambda x: x[0]>=0, conditions) # throw away conditions in negative positions
          
        # calculate the allowed word lengths 
        allowedWordLengths = getAllowedWordLengths(maxHeight, maxWidth, startRow, startCol, across, conditions, startdummy)
      
        # dummy conditions were needed to get valid lengths
        # but are not needed to match words
        conditions = filter(lambda x: x[1]!=dummy, conditions) 
      
        #find a word that satisfies the above conditions
        wordFound = False
        # iterate through all valid word lengths
        for wordLength in reversed(allowedWordLengths):
            if wordLength < minWordLength_absolute: continue #again, can't have one-letter words 
            subLexicon = lexicon[wordLength]
            # only conditions up to the wordLength-th word need apply
            subConditions = filter(lambda x: x[0]<wordLength, conditions) 
            # find all the words that satisfy all conditions
            fittingWords = getFittingWords(subConditions, startdummy, subLexicon)
            random.shuffle(fittingWords)
            while len(fittingWords) > 0 and not wordFound:
                term = fittingWords.pop() # choose one of the fitting words randomly
                terms[(startRow, startCol, across)] = term # add new word to list of terms
                # add dummy chars at the beginning and end of the new word as necessary
                if startdummy: term = dummy + term 
                if len(term) < max(allowedWordLengths): term = term + dummy
                # place new term on grid
                try:
                    grid = placeTermToGrid(term, startRow, startCol, across, grid)
                except:
                    print term, startRow, startCol, across
                    printCrossWord(grid)
                    raise
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
    terms, grid = getBestState(terms, grid, frontStates + deadEndStates) #find best state
    
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
    
    # the more crossings a candidate has the better 
    condLengths = map(len, condList)
    # choose start-position with probability proportional to the number of crossings each candidate has
    power = 3 # the higher this number the higher the probability at the best candidates
    roulette = random.randint(0, sum(map(lambda x:x**power, condLengths)))
    sumSoFar = 0
    for i, cond in enumerate(condList):
        sumSoFar += len(cond)**power
        if sumSoFar >= roulette:
            startRow, startCol, across = startCandidates[i]
            conditions = cond
            break
            
    return startRow, startCol, across, conditions

@profile
def isValidStart(grid, terms, startRow, startCol, across):
    # unless we are at the edge, starting square must be free or dummy
    isEdge = startCol == 0 if across else startRow == 0 
    if not isEdge and len(grid[startRow][startCol]) > 0 and grid[startRow][startCol] != dummy:
        return False
    # iterate backwards beginning from the starting position
    it = reversed(range( (startCol if across else startRow) + 1 )) 
    for i in it:
        r, c = (startRow, i) if across else (i, startCol)
        # if you find a starting position of a previous word 
        # before you find a dummy char or the edge of the crossword
        # then this starting position is invalid 
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
def getAllowedWordLengths(maxHeight, maxWidth, startRow, startCol, across, conditions, startdummy):
    allowed = []
    # if we have a startdummy, pretend the starting position is moved by one square 
    startRow, startCol = (startRow, startCol+startdummy) if across else (startRow+startdummy, startCol)
    minWordLength = 0
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
        fittingWordSets = map(lambda x: subLexicon[x], subConditions)
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
            #if grid[startRow][startCol + offset] != letter and grid[startRow][startCol + offset] != "":
                #raise Exception("Invalid letter placement: " + letter + " -> " + grid[startRow][startCol + offset])
            grid[startRow][startCol + offset] = letter
        else:
            #if grid[startRow + offset][startCol] != letter and grid[startRow + offset][startCol] != "":
                #raise Exception("Invalid letter placement: " + letter + " -> " + grid[startRow + offset][startCol])
            grid[startRow + offset][startCol] = letter
    return grid

@profile
def getBestState(terms, grid, states):
    for t, g in states: 
        # add up the letters of all the terms
        # this rewards crosswords that have many words with many letters each
        if sum(map(len,t.values())) > sum(map(len,terms.values())):
            terms, grid = t, g
    return terms, grid    

def printCrossWord(grid):
    print "\nCrossword:\n\n" + "\n".join(' '.join([x if len(x)>0 else '_' for x in row]) for row in grid)

lexicon, wordLookup = importDictionary()
grid, terms = generateCrossword(7, lexicon, wordLookup)
printCrossWord(grid)
print "\nTerms: " + ', '.join(terms.values()) + "\n"
decorators.printProfiled()
