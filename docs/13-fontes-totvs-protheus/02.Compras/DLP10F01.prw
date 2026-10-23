#Include 'Protheus.ch'
#INCLUDE 'TOPCONN.CH'
#INCLUDE "TBICONN.CH"

user function DLP10F01(cFun)
    Local cRet := ""
    Local nPProduto := ""
    Local cCodPro := ""
    Local nPPCusto := ""
    Local cCusAnt :=""
//PadR(cProdRef,Len(SB1->B1_COD))

    if UPPER (alltrim(cFun) )$ "MATA110"

        nPPCusto  := aScan(aHeader,{|x| AllTrim(x[2])=="C1_CC"})
        nPProduto := aScan(aHeader,{|x| AllTrim(x[2])=="C1_PRODUTO"})
        cProdRef  := aCols[n][nPProduto]
        cCusAnt   := aCols[n][nPPCusto]

        if EMPTY(cCusAnt)

            cRet      := POSICIONE("SBZ",1,XFILIAL("SBZ")+cProdRef,"BZ_CUSTO")

        else

            cRet:= cCusAnt

        end
    ENDIF

Return  cRet