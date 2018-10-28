from __future__ import print_function, absolute_import

import functools, time

def decorator(d):
    "Make function d a decorator: d wraps a function fn."
    def _d(fn):
        return functools.update_wrapper(d(fn), fn)
    return _d
decorator = decorator(decorator)

@decorator
def countcalls(f):
    "Decorator that makes the function count calls to it, in callcounts[f]."
    def _f(*args):
        callcounts[_f] += 1
        return f(*args)
    callcounts[_f] = 0
    return _f
callcounts = {}

@decorator
def timed(f):
    def _f(*args):
        startTime = time.clock()
        result = f(*args)
        print('Time: ', round(time.clock() - startTime, 1), 's')
        return result
    return _f

@decorator
def counttime(f):
    "Decorator that makes the function count time it spends."
    def _f(*args):
        startTime = time.clock()
        result = f(*args)
        totaltime[_f] += time.clock() - startTime
        return result
    totaltime[_f] = 0
    return _f
totaltime = {}
    
@decorator
def profile(f):
    def _f(*args):
        startTime = time.clock()
        result = f(*args)
        profiled[_f][0] += 1
        profiled[_f][1] += time.clock() - startTime
        return result
    profiled[_f] = [0, 0]
    return _f
profiled = {}

def printProfiled():
    print("\n".join([func.__name__ + ': ' + str(profiled[func][0]) + ' calls in a total of ' + str(profiled[func][1]) + 's' for func in profiled]))

def disabled(f):
    # Example: Use trace = disabled to turn off trace decorators
    return f