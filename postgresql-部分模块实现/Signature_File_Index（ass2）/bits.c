// bits.c ... functions on bit-strings
// part of signature indexed files
// Bit-strings are arbitrarily long byte arrays
// Least significant bits (LSB) are in array[0]
// Most significant bits (MSB) are in array[nbytes-1]

// Written by John Shepherd, March 2019

#include <assert.h>
#include "defs.h"
#include "bits.h"
#include "page.h"

typedef struct _BitsRep {
    Count nbits;          // how many bits
    Count nbytes;          // how many bytes in array
    Byte bitstring[1];  // array of bytes to hold bits
    // actual array size is nbytes
} BitsRep;

// create a new Bits object

Bits newBits(int nbits) {
    Count nbytes = iceil(nbits, 8);
    Bits new = malloc(2 * sizeof(Count) + nbytes);
    new->nbits = nbits;
    new->nbytes = nbytes;
    memset(&(new->bitstring[0]), 0, nbytes);
    return new;
}

// release memory associated with a Bits object

void freeBits(Bits b) {
    //TODO
    free(b);
}

// check if the bit at position is 1

Bool bitIsSet(Bits b, int position) {
    assert(b != NULL);
    assert(0 <= position && position < b->nbits);
    //TODO
    Count whichArray = position / 8;
    Count offset = position % 8;
    Byte mask = (1 << offset);
    if ((b->bitstring[whichArray] & mask)!=0) {
        return TRUE;
    } else{
        return FALSE; // remove this
    }

}

// check whether one Bits b1 is a subset of Bits b2

Bool isSubset(Bits b1, Bits b2) {
    assert(b1 != NULL && b2 != NULL);
    assert(b1->nbytes == b2->nbytes);
    //TODO
    Count allPositions = b1->nbits;
    for (int i = 0; i < allPositions; i++) {
        if (bitIsSet(b1, i)) {
            if (bitIsSet(b2, i)) {
                continue;
            } else {
                return FALSE;
            }
        }
    }
    return TRUE;
}

// set the bit at position to 1

void setBit(Bits b, int position) {
    assert(b != NULL);
    assert(0 <= position && position < b->nbits);
    //TODO
    Count whichArray = position / 8;
    Count offset = position % 8;
    Byte mask = (1 << offset);
    b->bitstring[whichArray] = b->bitstring[whichArray] | mask;
}

// set all bits to 1

void setAllBits(Bits b) {
    assert(b != NULL);
    //TODO
    for (int i = 0; i < b->nbytes; i++) {
        for (int j = 0; j < 8; j++) {
            Byte mask = (1 << j);
            b->bitstring[i] = b->bitstring[i] | mask;
        }
    }
}

// set the bit at position to 0

void unsetBit(Bits b, int position) {
    assert(b != NULL);
    assert(0 <= position && position < b->nbits);
    //TODO
    Count whichArray = position / 8;
    Count offset = position % 8;
    Byte mask = (1 << (offset));
    if (bitIsSet(b, position)) {
        b->bitstring[whichArray] = b->bitstring[whichArray] ^ mask;
    }
}

// set all bits to 0

void unsetAllBits(Bits b) {
    assert(b != NULL);
    //TODO
    Count allPositions = b->nbits;
    for (int i = 0; i < allPositions; i++) {
        for (int j = 0; j < 8; j++) {
            Count whichArray = i / 8;
            Count offset = i % 8;
            Byte mask = (1 << (offset));
            if (bitIsSet(b, i)) {
                b->bitstring[whichArray] = b->bitstring[whichArray] ^ mask;
            }
        }
    }
}

// bitwise AND ... b1 = b1 & b2

void andBits(Bits b1, Bits b2) {
    assert(b1 != NULL && b2 != NULL);
    assert(b1->nbytes == b2->nbytes);
    //TODO
    Count allPositions = b1->nbits;
    for (int i = 0; i < allPositions; i++) {
        for (int j = 0; j < 8; j++) {
            if (bitIsSet(b2, i)) {
                if (bitIsSet(b1, i)) {
                    setBit(b1, i);
                }
            } else {
                unsetBit(b1, i);
            }
        }
    }
}

// bitwise OR ... b1 = b1 | b2

void orBits(Bits b1, Bits b2) {
    assert(b1 != NULL && b2 != NULL);
    assert(b1->nbytes == b2->nbytes);
    //TODO
    Count allPositions = b1->nbits;
    for (int i = 0; i < allPositions; i++) {
        for (int j = 0; j < 8; j++) {
            if (bitIsSet(b1, i)) {
                setBit(b1, i);
            } else {
                if (bitIsSet(b2, i)) {
                    setBit(b1, i);
                }
            }
        }
    }
}

// left-shift ... b1 = b1 << n
// negative n gives right shift

void shiftBits(Bits b, int n) {
    // TODO
    int allPositions = b->nbits;
    if (n > 0) {
        for (int i = allPositions - n - 1; i >= 0; i--) {
            if (bitIsSet(b, i)) {
                setBit(b, i + n);
                unsetBit(b, i);
            } else {
                unsetBit(b, i + n);
            }
        }
    } else if (n < 0) {
        int abs_n = -n;
        for (int i = abs_n; i < allPositions; i++) {
            if (bitIsSet(b, i)) {
                setBit(b, i - abs_n);
                unsetBit(b, i); // 左补0or左补1？先补0
            } else {
                unsetBit(b, i - abs_n);
            }
        }
    }
}

// get a bit-string (of length b->nbytes)
// from specified position in Page buffer
// and place it in a BitsRep structure

void getBits(Page p, Offset pos, Bits b) {
    //TODO
    Count length = b->nbytes;
    Byte *start = addrInPage(p, pos, length);
    memcpy(b->bitstring, start, length);
}

// copy the bit-string array in a BitsRep
// structure to specified position in Page buffer

void putBits(Page p, Offset pos, Bits b) {
    //TODO
    Count length = b->nbytes;
    Byte *start = addrInPage(p, pos, length);
    memcpy(start, b->bitstring, length);
}

// show Bits on stdout
// display in order MSB to LSB
// do not append '\n'

void showBits(Bits b) {
    assert(b != NULL);
    //printf("(%d,%d)",b->nbits,b->nbytes);
    for (int i = b->nbytes - 1; i >= 0; i--) {
        for (int j = 7; j >= 0; j--) {
            Byte mask = (1 << j);
            if (b->bitstring[i] & mask)
                putchar('1');
            else
                putchar('0');
        }
    }
}
