// bsig.c ... functions on Tuple Signatures (bsig's)
// part of signature indexed files
// Written by John Shepherd, March 2019

#include "defs.h"
#include "reln.h"
#include "query.h"
#include "bsig.h"
#include "psig.h"

void findPagesUsingBitSlices(Query q)
{
	assert(q != NULL);
	//TODO
    //对应的关系
    Reln r = q->rel;
    // bitsSig的文件
    //File bitsSigFile=bsigFile(r);
    // 生成用来匹配sigpages中signature的query signature
    Bits queryPageSignature=makePageSig(r,q->qstring);
    // 记录需要examine的pages
    Bits pages=q->pages;
    setAllBits(pages);
    //pm
    Count numOfBitsTup=psigBits(r);
    Bits checkPage=newBits(numOfBitsTup);

    for (int i = 0; i < numOfBitsTup; i++) {
        if (bitIsSet(queryPageSignature,i)){
            // 定位bit slices
            PageID curBitsPageId=i/maxBsigsPP(r);
            setBit(checkPage,curBitsPageId);
            Count bitsOffset=i%maxBsigsPP(r);
            // 找到which page
            Page bitsPage=getPage(bsigFile(r),curBitsPageId);
            // 找到page的which slice
            Bits maskBits=newBits(bsigBits(r));
            // 取出slice tuple
            getBits(bitsPage,bitsOffset,maskBits);

            // zero bits in Pages which are zero in Slice
            for (int j = 0; j <nPsigs(r) ; j++) {
                if (!bitIsSet(maskBits,j)){
                    unsetBit(pages,j);
                }
            }
            q->nsigs++;
        }
    }
    // how many pages read
    for (int k = 0; k < numOfBitsTup; k++) {
        if (bitIsSet(checkPage,k)){
            q->nsigpages++;
        }
    }
}

