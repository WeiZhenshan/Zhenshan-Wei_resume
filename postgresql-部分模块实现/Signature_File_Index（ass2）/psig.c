// psig.c ... functions on page signatures (psig's)
// part of signature indexed files
// Written by John Shepherd, March 2019

#include "defs.h"
#include "reln.h"
#include "query.h"
#include "psig.h"
#include "hash.h"

Bits codewords_p(char *attr_value, int m, int k) {
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
// 默认从第1个tuple开始make，此时tuple的signature就是page的signature
Bits makePageSig(Reln r, Tuple t){
	assert(r != NULL && t != NULL);
	//TODO
    Bits pageSignature = newBits(r->params.pm);
    char **attr_array = tupleVals(r, t);
    char strs[3];
    char strc[3];
    strcpy(strs, "s");
    strcpy(strc, "c");
    if (strcmp(&sigType(r), strs) == 0) {
        for (int i = 0; i < r->params.nattrs; i++) {
            if (strcmp(attr_array[i], "?") != 0) {
                Bits cw = codewords_p(attr_array[i], r->params.pm, r->params.tk);
                orBits(pageSignature, cw);
            }
        }
    } else if (strcmp(&sigType(r), strc) == 0) {
        int u = r->params.pm / r->params.nattrs;
        int modAll = r->params.pm % r->params.nattrs;
        int pc=maxTupsPP(r);
        for (int i = 0; i < r->params.nattrs; i++) {
            if (strcmp(attr_array[i], "?") != 0) {
                if (i==0){
                    Bits cwFirst = codewords_p(attr_array[0], u+modAll,(u+modAll)/2/pc);
                    Count allPositions_0 = u+modAll;
                    for (int j = 0; j < allPositions_0; j++) {
                        if (bitIsSet(cwFirst,j)){
                            setBit(pageSignature,j);
                        }
                    }
                } else{
                    Bits cw = codewords_p(attr_array[i], u,u/2/pc);
                    Count allPositions_i = u;
                    for (int k = 0; k < allPositions_i; k++) {
                        if (bitIsSet(cw,k)){
                            setBit(pageSignature,k+u*i+modAll);
                        }
                    }
                }
            }
        }
    }
    return pageSignature;
}




void findPagesUsingPageSigs(Query q)
{
	assert(q != NULL);
	//TODO
    //对应的关系
    Reln r = q->rel;
    // data page最多几个tuple
    // Count maxTupPerDataPage=maxTupsPP(r);
    // Pagesig的文件
    File pageSigFile=psigFile(r);
    // page signature的m
    Count mOfPageSig=psigBits(r);
    // 生成用来匹配sigpages中signature的query signature
    Bits queryPageSignature=makePageSig(r,q->qstring);
    // 记录需要examine的pages
    Bits pages=q->pages;
    // 有多少page signature page
    Count numOfSignaturePage=nPsigPages(r);
    // 每个page 最多几个tuple
    Count maxTupPerSigPage=maxPsigsPP(r);
    for (int i = 0; i < numOfSignaturePage; i++) {
        Page curPage=getPage(pageSigFile, i);
        for (int j = 0; j < pageNitems(curPage); j++) {
            Bits curPsig=newBits(mOfPageSig);
            getBits(curPage,j,curPsig);
            if (isSubset(queryPageSignature,curPsig)){
                Count aimDataPage=i*maxTupPerSigPage+j;
                setBit(pages,aimDataPage);
            }
            //freeBits(curTsig);
            q->nsigs++;
        }
        q->nsigpages++;
    }
	// setAllBits(q->pages); // remove this
}

