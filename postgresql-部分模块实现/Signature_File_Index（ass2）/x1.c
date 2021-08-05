// Test Bits ADT

#include <stdio.h>
#include "defs.h"
#include "reln.h"
#include "tuple.h"
#include "bits.h"

int main(int argc, char **argv)
{
    // or*,and*,isSubset,shiftBits
//    Bits b1 = newBits(8);
//    setBit(b1, 5);
//    setBit(b1, 0);
//    setBit(b1, 1);
//    setBit(b1, 7);
//    printf("t=1: "); showBits(b1); printf("\n");
//
//    Bits b2 = newBits(8);
//    setBit(b2, 3);
//    setBit(b2, 7);
//    setBit(b2, 2);
//    setBit(b2, 0);
//    setBit(b2, 5);
//    printf("t=2: "); showBits(b2); printf("\n");
//    Bits b3 = newBits(8);
//    setBit(b3, 0);
//    setBit(b3, 1);
//    setBit(b3, 5);
//    setBit(b3, 6);
//    setBit(b3, 7);
//    printf("t=3: "); showBits(b3); printf("\n");
//    orBits(b1,b2);
//    printf("or\n");
//    printf("t=3: "); showBits(b1); printf("\n");
//
//    andBits(b1,b2);
//    printf("and\n");
//    printf("t=4: "); showBits(b1); printf("\n");

//    shiftBits(b2,2);
//    printf("shift\n");
//    printf("t=5: "); showBits(b2); printf("\n");
//
//    printf("subset\n");
//    if (isSubset(b1,b3)) printf("Bit b1 is subset of b3\n");


    // setBit*，bitIsSet*，setAllBits*，unsetBit*，unsetAllBits*
	Bits b = newBits(60);
	printf("t=0: "); showBits(b); printf("\n");
	setBit(b, 5);
	printf("t=1: "); showBits(b); printf("\n");
	setBit(b, 0);
	setBit(b, 50);
	setBit(b, 59);
	printf("t=2: "); showBits(b); printf("\n");
	if (bitIsSet(b,5)) printf("Bit 5 is set\n");
	if (bitIsSet(b,10)) printf("Bit 10 is set\n");
	setAllBits(b);
	printf("t=3: "); showBits(b); printf("\n");
	unsetBit(b, 40);
	printf("t=4: "); showBits(b); printf("\n");
	if (bitIsSet(b,20)) printf("Bit 20 is set\n");
	if (bitIsSet(b,40)) printf("Bit 40 is set\n");
	if (bitIsSet(b,50)) printf("Bit 50 is set\n");
    unsetAllBits(b);
    printf("t=5: "); showBits(b); printf("\n");
	setBit(b, 59);
    printf("t=6: "); showBits(b); printf("\n");
	return 0;
}
