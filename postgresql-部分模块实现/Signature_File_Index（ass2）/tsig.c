// tsig.c ... functions on Tuple Signatures (tsig's)
// part of signature indexed files
// Written by John Shepherd, March 2019

#include <unistd.h>
#include <string.h>
#include "defs.h"
#include "tsig.h"
#include "reln.h"
#include "hash.h"
#include "bits.h"


// generate codewords

Bits codewords(char *attr_value, int m, int k) {
    int nbits = 0;
    Bits cword = newBits(m);
    srandom(hash_any(attr_value, strlen(attr_value)));
    while (nbits < k) {
        int i = random() % m;
        if (!bitIsSet(cword, i)) {
            setBit(cword, i);
            nbits++;
        }
    }
    return cword;
}

// make a tuple signature

Bits makeTupleSig(Reln r, Tuple t) {
    assert(r != NULL && t != NULL);
    //TODO
    Bits tupleSignature = newBits(r->params.tm);
    char **attr_array = tupleVals(r, t);
    char strs[3];
    char strc[3];
    strcpy(strs, "s");
    strcpy(strc, "c");
    if (strcmp(&sigType(r), strs) == 0) {
        for (int i = 0; i < r->params.nattrs; i++) {
            if (strcmp(attr_array[i], "?") != 0) {
                Bits cw = codewords(attr_array[i], r->params.tm, r->params.tk);
                orBits(tupleSignature, cw);
            }
        }
    } else if (strcmp(&sigType(r), strc) == 0) {
        int u = r->params.tm / r->params.nattrs;
        int modAll = r->params.tm % r->params.nattrs;
        for (int i = 0; i < r->params.nattrs; i++) {
            if (strcmp(attr_array[i], "?") != 0) {
                if (i==0){
                    Bits cwFirst = codewords(attr_array[0], u+modAll,(u+modAll)/2);
                    Count allPositions_0 = u+modAll;
                    for (int j = 0; j < allPositions_0; j++) {
                        if (bitIsSet(cwFirst,j)){
                            setBit(tupleSignature,j);
                        }
                    }
                } else{
                    Bits cw = codewords(attr_array[i], u,u/2);
                    Count allPositions_i = u;
                    for (int k = 0; k < allPositions_i; k++) {
                        if (bitIsSet(cw,k)){
                            setBit(tupleSignature,k+u*i+modAll);
                        }
                    }
                }
            }
        }
    }
    return tupleSignature;
}

// find "matching" pages using tuple signatures

void findPagesUsingTupSigs(Query q) {
    assert(q != NULL);
    //TODO

    // setAllBits(q->pages); // remove this
    //对应的关系
    Reln r = q->rel;
    // data page最多几个tuple
    Count maxTupPerDataPage=maxTupsPP(r);
    // tupsig的文件
    File tupleSigFile=tsigFile(r);
    // tuple signature的m
    Count mOfTupLeSig=tsigBits(r);
    // 生成用来匹配sigpages中signature的query signature
    Bits queryTupSignature=makeTupleSig(r,q->qstring);
    // 记录需要examine的pages
    Bits pages=q->pages;
    // 有多少tuple signature page
    Count numOfSignaturePage=nTsigPages(r);
    // 每个page 最多几个tuple
    Count maxTupPerSigPage=maxTsigsPP(r);
    for (int i = 0; i < numOfSignaturePage; i++) {
        Page curPage=getPage(tupleSigFile,i);
        for (int j = 0; j < pageNitems(curPage); j++) {
            Bits curTsig=newBits(mOfTupLeSig);
            getBits(curPage,j,curTsig);
            if (isSubset(queryTupSignature,curTsig)){
                Count aimDataPage=(i*maxTupPerSigPage+j)/maxTupPerDataPage;
                setBit(pages,aimDataPage);
            }
            //freeBits(curTsig);
            q->nsigs++;
        }
        q->nsigpages++;
    }
    // The printf below is primarily for debugging
    // Remove it before submitting this function
//    printf("Matched Pages:");
//    showBits(q->pages);
//    putchar('\n');
}
