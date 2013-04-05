# This Python file uses the following encoding: utf-8

import random, copy, itertools
import decorators
from decorators import profile

dummy = '@'
maxRounds = 10**5
minWordLength_absolute = 2
maxCandidates = 3
profiled = decorators.profiled

@profile
def importDictionary():
    filename = 'dictionary-en.tsv'
    dictionaryRaw = open(filename, 'r')
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
    return lexicon, wordLookup

@profile
def generateCrossword(size, lexicon, wordLookup):
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
        
        
        # decide whether a dummy character is needed in the beginning of the word
        startdummy = True
        if across and startCol == 0 and not grid[startRow][startCol] == dummy:
            startdummy = False
        elif not across and startRow == 0 and not grid[startRow][startCol] == dummy:
            startdummy = False  
        # calculate the minimum and maximum length of the word 
        for maxWordLength in range(minWordLength_absolute, maxWidth - startCol + 1 if across else maxHeight - startRow + 1):
            if (maxWordLength-1, dummy) in conditions:
                maxWordLength -= 1 # decrease by one because the iterator will increment it again on its own before breaking
                break
        for minWordLength in range(minWordLength_absolute, maxWordLength+1):
            if minWordLength-1 not in [x[0] for x in conditions] or (minWordLength-1, dummy) in conditions: 
                minWordLength -= 1 # decrease by one because the iterator will increment it again on its own before breaking
                break    
        if maxWordLength < minWordLength_absolute: continue #again, can't have one-letter words
        
        #find a word that satisfies the above conditions
        wordFound = False
        # iterate through all valid word lengths
        for wordLength in reversed(range(minWordLength, maxWordLength+1)):
            # words of maxWordLength should only be considered if we don't need a dummy char at the beginning of the word
            if startdummy and wordLength == maxWordLength: continue 
            subLexicon = lexicon[wordLength]
            # only conditions up to the wordLength-th word need apply
            subConditions = filter(lambda x: x[0]<wordLength, conditions) 
            # calculate the lists of words that satisfy each condition
            # their intersection are the words that satisfy all conditions 
            if len(subConditions) > 0: 
                fittingWordSets = map(lambda x: subLexicon[ (x[0]+startdummy, x[1]) ], subConditions)
                fittingWordIds = reduce(lambda x,y: x.intersection(y), fittingWordSets)
            else: # if there are no conditions, take all words!
                fittingWordSets = subLexicon.values()
                fittingWordIds = reduce(lambda x,y: x.union(y), fittingWordSets)
            fittingWords = map(lambda x: wordLookup[x][0], fittingWordIds)
            if len(fittingWords) > 0:
                term = random.choice(fittingWords) # choose one of the fitting words randomly
                terms[(startRow, startCol, across)] = term # add new word to list of terms
                # add dummy chars at the beginning and end of the new word as necessary
                if startdummy: term = dummy + term 
                if len(term) < maxWordLength: term = term + dummy
                # place new term on grid
                for offset, letter in enumerate(term):
                    if across:
                        grid[startRow][startCol + offset] = letter
                    else:
                        grid[startRow + offset][startCol] = letter
                newState = (copy.deepcopy(terms), copy.deepcopy(grid))
                if newState not in deadEndStates:
                    frontStates.append(newState)
                    #printCrossWord(grid)
                    wordFound = True
                    break
        if not wordFound: # we need to backtrack!
            deadEndStates.append( frontStates.pop() )
    for t, g in frontStates + deadEndStates: #find best state!
        if len(t) > len(terms):
            terms, grid = t, g
    return grid, terms

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
    

def printCrossWord(grid):
    print "\nCrossword:\n\n" + "\n".join(' '.join([x if len(x)>0 else '_' for x in row]) for row in grid)

lexicon, wordLookup = importDictionary()
grid, terms = generateCrossword(5, lexicon, wordLookup)
printCrossWord(grid)
print "\nTerms: " + ', '.join(terms.values())
decorators.printProfiled()
