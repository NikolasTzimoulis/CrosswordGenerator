# This Python file uses the following encoding: utf-8
from __future__ import print_function, absolute_import

import copy
import itertools
import os
import random
import sys

from src.crossgen import constants, decorators, dictionary
from src.crossgen.constants import minWordLength_absolute, dummy, maxCandidates


@decorators.profile
def generateCrossword(size, lexicon, wordLookup):
    print('Generating crossword')
    maxHeight = maxWidth = size
    startOrder = set(itertools.combinations_with_replacement(range(size),2))
    startOrder = startOrder.union([(x[1], x[0]) for x in startOrder])
    # startOrder = sorted(startOrder, cmp=lambda x,y: x[0]+x[1]-y[0]-y[1]+10*(min(x)-min(y)))
    startOrder = sorted(startOrder, key=lambda x: x[0] + x[1] + 10 * min(x))
    terms = {}
    grid = [[""]*maxWidth for _ in range(maxHeight)]
    frontStates = [ (terms, grid) ]
    deadEndStates = []
    for i in range(constants.maxRounds):
        terms, grid = copy.deepcopy(frontStates[-1])
        percent = i * 100 / constants.maxRounds
        print(f'{i}/{constants.maxRounds} ({percent}%)', end='\r')  # progress bar
        
        # find a good starting position for the next word
        startRow, startCol, across, conditions = getStartPos(startOrder, grid, terms)
        
        # decide whether a dummy character is needed in the beginning of the word
        startdummy = shouldStartDummy(startRow, startCol, across, grid)
        # adjust conditions to take startdummy into account
        conditions = [(x[0] - startdummy, x[1]) for x in conditions]  # one square offset if startdummy
        conditions = [cond for cond in conditions if cond[0] >= 0]  # throw away conditions in negative positions
          
        # calculate the allowed word lengths 
        allowedWordLengths = getAllowedWordLengths(maxHeight, maxWidth, startRow, startCol, across, conditions, startdummy)
      
        # dummy conditions were needed to get valid lengths
        # but are not needed to match words
        conditions = [cond for cond in conditions if cond[1] != dummy]
      
        # find a word that satisfies the above conditions
        wordFound = False
        # iterate through all valid word lengths
        for wordLength in reversed(allowedWordLengths):
            if wordLength < minWordLength_absolute:
                continue  # again, can't have one-letter words
            subLexicon = lexicon[wordLength]
            # only conditions up to the wordLength-th word need apply
            subConditions = [cond for cond in conditions if cond[0] < wordLength]
            # find all the words that satisfy all conditions
            fittingWords = getFittingWords(subConditions, startdummy, subLexicon, wordLookup)
            random.shuffle(fittingWords)
            while len(fittingWords) > 0 and not wordFound:
                term = fittingWords.pop()  # choose one of the fitting words randomly
                terms[(startRow, startCol, across)] = term # add new word to list of terms
                # add dummy chars at the beginning and end of the new word as necessary
                if startdummy: term = dummy + term 
                if len(term) < max(allowedWordLengths): term = term + dummy
                # place new term on grid
                try:
                    grid = placeTermToGrid(term, startRow, startCol, across, grid)
                except Exception as ex:
                    print(term, startRow, startCol, across)
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
    
    print("\t[DONE]")
    return grid, terms


@decorators.profile
def getStartPos(startOrder, grid, terms):
    # find free positions close to left-uppermost corner
    startCandidates = []
    startRow = 0
    startCol = 0
    across = False
    for startRow, startCol in startOrder:
        if len(startCandidates) >= maxCandidates: break
        for across in [True, False]:
            if isValidStart(grid, terms, startRow, startCol, across):
                startCandidates.append((startRow, startCol, across))    
    #find all crossing points with pre-existing words for each candidate
    condList = [getConditions(grid, x[0], x[1], x[2]) for x in startCandidates]
    
    # the more crossings a candidate has the better 
    # choose start-position with probability proportional to the number of crossings each candidate has
    power = 3  # the higher this number the higher the probability at the best candidates
    roulette = random.randint(0, sum([len(x) ** power for x in condList]))
    sumSoFar = 0
    conditions = []
    for i, cond in enumerate(condList):
        sumSoFar += len(cond)**power
        if sumSoFar >= roulette:
            startRow, startCol, across = startCandidates[i]
            conditions = cond
            break
            
    return startRow, startCol, across, conditions


@decorators.profile
def isValidStart(grid, terms, startRow, startCol, across):
    # unless we are at the edge, starting square must be free or dummy
    isEdge = startCol == 0 if across else startRow == 0 
    if not isEdge and len(grid[startRow][startCol]) > 0 and grid[startRow][startCol] != dummy:
        return False
    # iterate backwards beginning from the starting position
    it = reversed(range((startCol if across else startRow) + 1))
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


@decorators.profile
def getConditions(grid, startRow, startCol, across):
    letters = []
    if across: #move horizontally
        letters = grid[startRow][startCol:]
    else:
        letters = [row[startCol] for row in grid[startRow:]]
    return [(index, letter) for index, letter in enumerate(letters) if len(letter) > 0]


@decorators.profile
def shouldStartDummy(startRow, startCol, across, grid):
    startdummy = True
    if across and startCol == 0 and not grid[startRow][startCol] == dummy:
        startdummy = False
    elif not across and startRow == 0 and not grid[startRow][startCol] == dummy:
        startdummy = False
    return startdummy


@decorators.profile
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


@decorators.profile
def getFittingWords(subConditions, startdummy, subLexicon, wordLookup):
    # calculate the lists of words that satisfy each condition
    # their intersection are the words that satisfy all conditions 
    if len(subConditions) > 0: 
        try:
            fittingWordSets = [subLexicon[x] for x in subConditions]
            fittingWordIds = set.intersection(set(fittingWordSets[0]), *itertools.islice(fittingWordSets, 1, None))
        except:
            fittingWordIds = []
    else: # if there are no conditions, take all words!
        fittingWordSets = list(subLexicon.values())
        fittingWordIds = set.union(set(fittingWordSets[0]), *itertools.islice(fittingWordSets, 1, None))
    fittingWords = [wordLookup[wid][0] for wid in fittingWordIds]
    return fittingWords


@decorators.profile
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


@decorators.profile
def getBestState(terms, grid, states):
    for t, g in states: 
        # add up the letters of all the terms
        # this rewards crosswords that have many words with many letters each
        # if sum(map(len, t.values())) > sum(map(len, terms.values())):
        if sum([len(v) for v in t.values()]) > sum([len(v) for v in terms.values()]):
            terms, grid = t, g
    return terms, grid    


def printCrossWord(grid):
    print("\nCrossword:\n\n" + "\n".join(' '.join([x if len(x)>0 else '_' for x in row]) for row in grid))


def run(dictionary_file, new=True):
    if new:
        d = dictionary.import_d(dictionary_file)
    else:
        d = dictionary.import_d2(dictionary_file)
    grid, terms = generateCrossword(5, **d)
    printCrossWord(grid)
    print("\nTerms: " + ', '.join(terms.values()) + "\n")
    decorators.printProfiled()


def profile(expr):
    import cProfile
    cProfile.run(expr)


if __name__ == "__main__":
    dictionary_file = os.path.join(os.path.expanduser('~'), '.crossgen', 'dictionary-en-5000.tsv')
    mode = None if len(sys.argv) < 2 else sys.argv[1]
    if mode == 'profile':
        profile('run(dictionary_file)')
    elif mode == 'run':
        run(dictionary_file)
    elif mode == 'new':
        run(dictionary_file, new=True)
    elif mode == 'old':
        run(dictionary_file, new=False)
    else:
        run(dictionary_file)
