#include "protheus.ch"
#include "parmtype.ch"

//-------------------------------------------------------------------
/*/{Protheus.doc} DLP10G05
Função para gatilhar o campo do campo C1_PRODUTO PARA O  C1 C1_DATPRF com a data de necessidade, considerando lead time:
Formula para Calculo: Prazo Lead Time + Data Atual + 1 Dia
Prazo Lead Time: BZ_PE E BZ_TIPE
Tome como base a função getIniTime comxfun.prx
@author  Eduardo Dalitz
@since   20/02/2025
@version 1.0
/*/
//-------------------------------------------------------------------

// IIF(EXISTFUNC("U_DLP10G04") ,U_DLP10G04(M->C2_PRODUTO,M->C2_QUANT),0.00)                                                                                                                               
User function DLP10G05(dDatPrf)
    Local nPrazo := 0
    Local dDtIniCom := dDataBase
    Default dDatPrf := dDatabase

    If Empty(RetFldProd(SB1->B1_COD,"B1_FORPRZ"))
        nPrazo := RetFldProd(SB1->B1_COD,"B1_PE")
    Else
        nPrazo := Formula(RetFldProd(SB1->B1_COD,"B1_FORPRZ"))
        If ValType(nPrazo) # "N"
            Help(" ",1,"FORMUL")
            nPrazo	:= 0
        EndIf
        nPrazo := IIF(nPrazo == Nil,0,nPrazo)  // Nao existe a formula
    EndIf

    If nPrazo > 0
        If RetFldProd(SB1->B1_COD,"B1_TIPE") == "D"//Dias
            dDtiniCom := daysum(DaySum(dDatPrf,nPrazo),1)
        ElseIf RetFldProd(SB1->B1_COD,"B1_TIPE") == "M"// Mes
            dDtIniCom := daysum(MonthSum(dDatPrf,nPrazo),1)
        ElseIf RetFldProd(SB1->B1_COD,"B1_TIPE") == "S"// Semana
            nPrazo 	  *= 7
            dDtiniCom := daysum(DaySum(dDatPrf,nPrazo),1)
        ElseIf RetFldProd(SB1->B1_COD,"B1_TIPE") == "A"// Ano
            dDtIniCom := daysum(YearSum(dDatPrf,nPrazo),1)
        ElseIf RetFldProd(SB1->B1_COD,"B1_TIPE") == "H"// Hora
            nPrazo 	  := Int(nPrazo/24)
            dDtiniCom := daysum(DaySum(dDatPrf,nPrazo),1)
        EndIf
    Endif

Return dDtIniCom
