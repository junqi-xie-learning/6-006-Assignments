#!/usr/bin/env python2.7

import unittest
from dnaseqlib import *

### Utility classes ###


class Multidict:
    # Maps integer keys to a set of arbitrary values.
    def __init__(self, pairs=[]):
        # Initializes a new multi-value dictionary, and adds any key-value
        # 2-tuples in the iterable sequence pairs to the data structure.
        self.table = dict()
        for pair in pairs:
            self.put(pair[0], pair[1])

    def put(self, k, v):
        # Associates the value v with the key k.
        if k in self.table:
            self.table[k].append(v)
        else:
            self.table[k] = [v]

    def get(self, k):
        # Gets any values that have been associated with the key k; or, if
        # none have been, returns an empty sequence.
        try:
            return self.table[k]
        except KeyError:
            return []


def subsequenceHashes(seq, k):
    # Given a sequence of nucleotides, return all k-length subsequences
    # and their hashes.  (What else do you need to know about each
    # subsequence?)
    subseq = ''
    for i in range(0, k):
        subseq += seq.next()
    try:
        rh = RollingHash(subseq)
        pos = 0
        while True:
            yield (rh.current_hash(), (pos, subseq))
            previtm = subseq[0]
            subseq = subseq[1:] + seq.next()
            rh.slide(previtm, subseq[-1:])
            pos += 1
    except StopIteration:
        return


def intervalSubsequenceHashes(seq, k, m):
    # Similar to subsequenceHashes(), but returns one k-length subsequence
    # every m nucleotides.  (This will be useful when you try to use two
    # whole data files.)
    try:
        pos = 0
        while True:
            subseq = ''
            for i in range(0, k):
                subseq += seq.next()
            
            rh = RollingHash(subseq)
            yield (rh.current_hash(), (pos, subseq))
            for i in range(0, m - k):
                seq.next()
            pos += m
    except StopIteration:
        return


def getExactSubmatches(a, b, k, m):
    # Searches for commonalities between sequences a and b by comparing
    # subsequences of length k.  The sequences a and b should be iterators
    # that return nucleotides.  The table is built by computing one hash
    # every m nucleotides (for m >= k).
    seqtable = Multidict(intervalSubsequenceHashes(a, k, m))

    for hashval, (bpos, bsubseq) in subsequenceHashes(b, k):
        for apos, asubseq in seqtable.get(hashval):
            if asubseq != bsubseq:
                continue
            yield (apos, bpos)
    return


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print 'Usage: {0} [file_a.fa] [file_b.fa] [output.png]'.format(
            sys.argv[0])
        sys.exit(1)

    # The arguments are, in order: 1) Your getExactSubmatches
    # function, 2) the filename to which the image should be written,
    # 3) a tuple giving the width and height of the image, 4) the
    # filename of sequence A, 5) the filename of sequence B, 6) k, the
    # subsequence size, and 7) m, the sampling interval for sequence
    # A.
    compareSequences(getExactSubmatches,
                     sys.argv[3], (500, 500), sys.argv[1], sys.argv[2], 8, 100)
