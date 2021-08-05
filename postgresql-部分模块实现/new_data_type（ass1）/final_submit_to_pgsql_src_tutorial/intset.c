#include "postgres.h"

#include "fmgr.h"
#include "libpq/pqformat.h"        /* needed for send/recv functions */
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <stdlib.h>
#include <ctype.h>
#include "access/hash.h"
#include "utils/builtins.h"
#include <sys/types.h>
#include <regex.h>

PG_MODULE_MAGIC;

typedef struct intSet {
    char v_len[VARHDRSZ];
    int num_comma;
    int num_int;
    int intset[1];
} intSet;


/*****************************************************************************
 * Input/Output functions
 *****************************************************************************/
// 完成,
PG_FUNCTION_INFO_V1(intset_in);

Datum
intset_in(PG_FUNCTION_ARGS) {
    char *str = PG_GETARG_CSTRING(0);
    intSet *result;
    // check 有效性，invalid intSet报错

    // part1
    int status = 0;
    int flag = REG_EXTENDED;
    regmatch_t pmatch[1];
    const size_t nmatch = 1;
    regex_t reg;
    const char *pattern = "^\\s*\\{((\\s*[0-9]+\\s*[,])*\\s*[0-9]+\\s*)*\\s*\\}\\s*$";
    char *buf =str;
    // part 2
    const char s[2] = ",";
    const char s1[5] ="{, }";
    char *token;
    char *token1;
    char *copy_str;
    char *copy_str_1;
    int *array,array_len=13,count_array=0,comma_counter=0;
    // part3
    int *diff_array,i,j,diff_num=1,state=0,tmp=0;

    regcomp(&reg, pattern, flag);
    status = regexec(&reg, buf, nmatch, pmatch, 0);
    if(status == REG_NOMATCH){
        ereport(ERROR,
                (errcode(ERRCODE_INVALID_TEXT_REPRESENTATION),
                        errmsg("invalid input syntax for type %s: \"%s\"",
                               "intSet", str)));
    }
    // 假设数据读取过来的都是对的,读进来的是一个intSet类型的值，考虑如何分割字符串（strtok）
    // 转换成int加入int array
    // int array去重+排序
    // 遍历导入result
    // 假设数据读取过来的都是对的,读进来的是一个intSet类型的值，考虑如何分割字符串

    array=malloc(sizeof(int)*array_len);
    copy_str=malloc(sizeof(char)*(strlen(str)+1));
    copy_str_1=malloc(sizeof(char)*(strlen(str)+1));
    strcpy(copy_str,str);
    strcpy(copy_str_1,str);
    token = strtok(str, s);

    // check the comma number
    while( token != NULL ){
        comma_counter++;
        token = strtok(NULL, s);
    }
    comma_counter--;
    // array add,and check num_number,转换成int加入int array(动态内存)
    token1 = strtok(copy_str, s1);
    while( token1 != NULL ){
        if (count_array==array_len){
            array_len=array_len*2;
            array=realloc(array,sizeof(int)*array_len);
        }
        array[count_array]=atoi(token1);
        count_array++;
        token1 = strtok(NULL, s1);
    }
//    elog(NOTICE,"count_array:%d\n",count_array);
    // check invalid error{ 1 2,3,4}
    if (comma_counter<count_array-1){
        ereport(ERROR,
                (errcode(ERRCODE_INVALID_TEXT_REPRESENTATION),
                        errmsg("invalid input syntax for type %s: \"%s\"",
                               "intSet", copy_str_1)));
    }

    // 数据读取过来的都是对的
    // int array去重
    diff_array=malloc(sizeof(int)*count_array);
    diff_array[0]=array[0];
    for (i=1;i<count_array;i++){
        for (j = 0; j < diff_num; j++) {
            if (diff_array[j]==array[i]){
                state=1;
                break;
            }
        }
        if (state==0){
            diff_array[diff_num]=array[i];
            diff_num++;
        }
        state=0;
    }
    // int array 排序
    for (int k = 0; k < diff_num-1; k++) {
        for (int l = 0; l < diff_num-1-k; l++) {
            if (diff_array[l+1]<diff_array[l]){
                tmp=diff_array[l];
                diff_array[l]=diff_array[l+1];
                diff_array[l+1]=tmp;
            }
        }
    }

    // into result
    result=(intSet *) palloc(VARHDRSZ+sizeof(int)*2+sizeof(int)*diff_num);
    SET_VARSIZE(result,VARHDRSZ+sizeof(int)*2+sizeof(int)*diff_num);

    // 解决 { }问题
    if (comma_counter==0 && count_array==0){
        result->num_int=0;
        result->num_comma=0;
    } else{
        result->num_int=diff_num;
        result->num_comma=comma_counter;
    }

    for (int i = 0; i < count_array; i++) {
        if (result->num_int==0){
            break;
        }
        result->intset[i]=diff_array[i];
    }
    free(copy_str);
    free(copy_str_1);
    free(array);
    regfree(&reg);
    PG_RETURN_POINTER(result);
}



PG_FUNCTION_INFO_V1(intset_out);

Datum
intset_out(PG_FUNCTION_ARGS) {
    intSet *paramSet = (intSet *) PG_GETARG_POINTER(0);
    char *result,strNum[100];
    int length;
    length=74328;
    // malloc/ palloc
    result=malloc(sizeof(char)*length);

    result[0]='\0';
    strcat(result,"{");
    if (paramSet->num_int>0){
        pg_ltoa(paramSet->intset[0],strNum);
        strcat(result,strNum);
        for (int i = 1; i < paramSet->num_int; i++) {
            strcat(result,",");
            pg_ltoa(paramSet->intset[i],strNum);
            strcat(result,strNum);
        }
    }
    strcat(result,"}");
    PG_RETURN_CSTRING(psprintf("%s",result));
    free(result);
}




// 完成1，=
PG_FUNCTION_INFO_V1(intset_eq);

Datum
intset_eq(PG_FUNCTION_ARGS) {
    intSet *a = (intSet *) PG_GETARG_POINTER(0);
    intSet *b = (intSet *) PG_GETARG_POINTER(1);
    // 知道要返回的值，和输入的值（intset）
    int result=1;
    // 如果长度不相等，else相等
    if (a->num_int!=b->num_int){
        result=0;
    } else{
        for (int i = 0; i < a->num_int; i++) {
            if (a->intset[i]!=b->intset[i]){
                result=0;
                break;
            }
        }
    }
    PG_RETURN_BOOL(result);
}



// 完成2，#
PG_FUNCTION_INFO_V1(intset_cardinality);

Datum
intset_cardinality(PG_FUNCTION_ARGS) {
    intSet *a = (intSet *) PG_GETARG_POINTER(0);
    PG_RETURN_INT32(a->num_int);
}






// ? ,完成3， intSet contains the integer i,return bool
PG_FUNCTION_INFO_V1(intset_contain);

Datum
intset_contain(PG_FUNCTION_ARGS) {
    int32  a =  PG_GETARG_INT32(0);
    intSet *b = (intSet *) PG_GETARG_POINTER(1);
    // 知道要返回的值，和输入的值（intset）
    int result=0;
    for (int i = 0; i < b->num_int; i++) {
        if (b->intset[i]==a){
            result=1;
            break;
        }
    }
    PG_RETURN_BOOL(result);
}




// 完成4,A - B,in A and not in B,
PG_FUNCTION_INFO_V1(intset_difference);

Datum
intset_difference(PG_FUNCTION_ARGS) {
    intSet *a = (intSet *) PG_GETARG_POINTER(0);
    intSet *b = (intSet *) PG_GETARG_POINTER(1);
    intSet *result;
    int *array,counter=0,array_len=13,flag;
    array=malloc(sizeof(int)*array_len);
    for (int i = 0; i < a->num_int; i++) {
        flag=0;
        for (int j = 0; j < b->num_int; j++) {
            if (a->intset[i]==b->intset[j]){
                flag=1;
                break;
            }
        }
        if (counter==array_len){
            array_len=array_len*2;
            array=realloc(array,sizeof(int)*array_len);
        }
        if (flag==0){
            array[counter]=a->intset[i];
            counter++;
        }else{
            continue;
        }
    }
    result=(intSet *) palloc(VARHDRSZ+sizeof(int)*2+sizeof(int)*counter);
    //设置一下
    SET_VARSIZE(result,VARHDRSZ+sizeof(int)*2+sizeof(int)*counter);
    result->num_int=counter;
    for (int i = 0; i < counter; i++) {
        result->intset[i]=array[i];
    }
    free(array);
    PG_RETURN_POINTER(result);
}





// <> ，完成5，A and B ARE NOT EQUAL，pass,
PG_FUNCTION_INFO_V1(intset_ineq);

Datum
intset_ineq(PG_FUNCTION_ARGS) {
    intSet *a = (intSet *) PG_GETARG_POINTER(0);
    intSet *b = (intSet *) PG_GETARG_POINTER(1);

    int result=0;
    if (a->num_int!=b->num_int){
        result=1;
    } else{
        for (int i = 0; i < a->num_int; i++) {
            if (a->intset[i]!=b->intset[i]){
                result=1;
                break;
            }
        }
    }
    PG_RETURN_BOOL(result);
}




// @<,pass,完成6
PG_FUNCTION_INFO_V1(intset_improper_subset);

Datum
intset_improper_subset(PG_FUNCTION_ARGS) {
    intSet *a = (intSet *) PG_GETARG_POINTER(0);
    intSet *b = (intSet *) PG_GETARG_POINTER(1);
    int result=0,counter=0;
    for (int i = 0; i <a->num_int ; i++) {
        for (int j = 0; j < b->num_int; j++) {
            if (a->intset[i]==b->intset[j]){
                counter++;
                break;
            }
        }
    }
    if (counter==a->num_int){
        result=1;
    }
    PG_RETURN_BOOL(result);
}



// >@,pass,完成7
PG_FUNCTION_INFO_V1(intset_improper_superset);

Datum
intset_improper_superset(PG_FUNCTION_ARGS) {
    intSet *a = (intSet *) PG_GETARG_POINTER(0);
    intSet *b = (intSet *) PG_GETARG_POINTER(1);
    int result=0,counter=0;
    for (int i = 0; i <b->num_int ; i++) {
        for (int j = 0; j < a->num_int; j++) {
            if (b->intset[i]==a->intset[j]){
                counter++;
                break;
            }
        }
    }
    if (counter==b->num_int){
        result=1;
    }
    PG_RETURN_BOOL(result);
}





// || ,A 并 B,完成8
PG_FUNCTION_INFO_V1(intset_union);

Datum
intset_union(PG_FUNCTION_ARGS) {
    intSet *a = (intSet *) PG_GETARG_POINTER(0);
    intSet *b = (intSet *) PG_GETARG_POINTER(1);
    intSet *result;
    int *array,counter=0,array_len=13;
    int *final_array,counter_final=1,state=0,tmp=0;
    array=malloc(sizeof(int)*array_len);
    if (a->num_int!=0 || b->num_int!=0){
        for (int i = 0; i < a->num_int; i++) {
            if (counter==array_len){
                array_len=array_len*2;
                array=realloc(array,sizeof(int)*array_len);
            }
            array[counter]=a->intset[i];
            counter ++;
        }

        for (int j = 0; j < b->num_int; j++) {
            if (counter==array_len){
                array_len=array_len*2;
                array=realloc(array,sizeof(int)*array_len);
            }
            array[counter]=b->intset[j];
            counter ++;
        }
        final_array=malloc(sizeof(int)*counter);
        // 去重
        final_array[0]=array[0];
        for (int i=1;i<counter;i++){
            for (int j = 0; j < counter_final; j++) {
                if (final_array[j]==array[i]){
                    state=1;
                    break;
                }
            }
            if (state==0){
                final_array[counter_final]=array[i];
                counter_final++;
            }
            state=0;
        }
        // 排序
        for (int k = 0; k < counter_final-1; k++) {
            for (int l = 0; l < counter_final-1-k; l++) {
                if (final_array[l+1]<final_array[l]){
                    tmp=final_array[l];
                    final_array[l]=final_array[l+1];
                    final_array[l+1]=tmp;
                }
            }
        }
        result=(intSet *) palloc(VARHDRSZ+sizeof(int)*2+sizeof(int)*counter_final);
        //设置一下
        SET_VARSIZE(result,VARHDRSZ+sizeof(int)*2+sizeof(int)*counter_final);
        result->num_int=counter_final;
        for (int i = 0; i < counter_final; i++) {
//        elog(NOTICE,"index:%d,value:%d\n",i,array[i]);
            result->intset[i]=final_array[i];
        }
        free(final_array);
    } else{
        result=(intSet *) palloc(VARHDRSZ+sizeof(int)*2+sizeof(int));
        //设置一下
        SET_VARSIZE(result,VARHDRSZ+sizeof(int)*2+sizeof(int));
        result->num_int=0;
    }
    free(array);
    PG_RETURN_POINTER(result);
}







//&&,完成9
PG_FUNCTION_INFO_V1(intset_intersection);

Datum
intset_intersection(PG_FUNCTION_ARGS) {
    intSet *a = (intSet *) PG_GETARG_POINTER(0);
    intSet *b = (intSet *) PG_GETARG_POINTER(1);
    intSet *result;
    int *array,counter=0,array_len=13;
    array=malloc(sizeof(int)*array_len);
    for (int i = 0; i < a->num_int; i++) {
        for (int j = 0; j < b->num_int; j++) {
            if (a->intset[i]==b->intset[j]){
                if (counter==array_len){
                    array_len=array_len*2;
                    array=realloc(array,sizeof(int)*array_len);
                }
                array[counter]=b->intset[j];
                counter++;
                break;
            }
        }
    }
    result=(intSet *) palloc(VARHDRSZ+sizeof(int)*2+sizeof(int)*counter);
    //设置一下
    SET_VARSIZE(result,VARHDRSZ+sizeof(int)*2+sizeof(int)*counter);
    result->num_int=counter;
    for (int i = 0; i < counter; i++) {
//        elog(NOTICE,"index:%d,value:%d\n",i,array[i]);
        result->intset[i]=array[i];
    }
    free(array);
    PG_RETURN_POINTER(result);
}




int cmpfunc(const void * a,const void * b);
int cmpfunc(const void * a,const void * b){
    return (*(int *)a -*(int *)b);
}
// !!,完成10
PG_FUNCTION_INFO_V1(intset_disjunction);

Datum
intset_disjunction(PG_FUNCTION_ARGS) {
    intSet *a = (intSet *) PG_GETARG_POINTER(0);
    intSet *b = (intSet *) PG_GETARG_POINTER(1);
    intSet *result;
    int *array,counter=0,array_len=13,flag;
    array=malloc(sizeof(int)*array_len);
    // A -B
    for (int i = 0; i < a->num_int; i++) {
        flag=0;
        for (int j = 0; j < b->num_int; j++) {
            if (a->intset[i]==b->intset[j]){
                flag=1;
                break;
            }
        }
        if (counter==array_len){
            array_len=array_len*2;
            array=realloc(array,sizeof(int)*array_len);
        }
        if (flag==0){
            array[counter]=a->intset[i];
            counter++;
        }
    }
    // B-A
    for (int i = 0; i < b->num_int; i++) {
        flag=0;
        for (int j = 0; j < a->num_int; j++) {
            if (b->intset[i]==a->intset[j]){
                flag=1;
                break;
            }
        }
        if (counter==array_len){
            array_len=array_len*2;
            array=realloc(array,sizeof(int)*array_len);
        }
        if (flag==0){
            array[counter]=b->intset[i];
            counter++;
        }
    }
    //排序
    qsort(array,counter,sizeof(int),cmpfunc);
    result=(intSet *) palloc(VARHDRSZ+sizeof(int)*2+sizeof(int)*counter);
    //设置一下
    SET_VARSIZE(result,VARHDRSZ+sizeof(int)*2+sizeof(int)*counter);
    result->num_int=counter;
    for (int i = 0; i < counter; i++) {
//        elog(NOTICE,"index:%d,value:%d\n",i,array[i]);
        result->intset[i]=array[i];
    }
    free(array);
    PG_RETURN_POINTER(result);
}