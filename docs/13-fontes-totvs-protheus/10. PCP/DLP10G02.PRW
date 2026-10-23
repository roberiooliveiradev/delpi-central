
#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"

// ntipo == 1 -> TELA
// ntipo == 2 -> BROWSE
USER FUNCTION DLP10G02(nTipo)

    Local cOP:= ""
    Local cRecur:= ""
    Local cOpera:= ""
    Local cRoteiro:= ""
    Local cProd:= ""

    /*
AND HY_OP='07627601001   '
AND HY_RECURSO =''
AND HY_OPERAC =''
AND HY_ROTEIRO =''


    */
    IF nTipo == 1
        IF INCLUI
            cFil     := M->H6_FILIAL
            cOP     :=   M->H6_OP
            cRecur  := M->H6_RECURSO
            cOpera  := M->H6_OPERAC
            cProd   := M->H6_PRODUTO
        ELSE
            cFil     := SH6->H6_FILIAL
            cOP     := SH6->H6_OP
            cRecur  := SH6->H6_RECURSO
            cOpera  := SH6->H6_OPERAC
            cProd   := SH6->H6_PRODUTO
        ENDIF

    ELSE
        cFil     := SH6->H6_FILIAL
        cOP     := SH6->H6_OP
        cRecur  := SH6->H6_RECURSO
        cOpera  := SH6->H6_OPERAC
        cProd   := SH6->H6_PRODUTO
    ENDIF

    cDescOper :=  fGetOP(  cOP,cRecur,cOpera,cProd  ,cFil )

rETURN cDescOper



STATIC function fGetOP(  cOP,cRecur,cOpera,cProd ,cFil  )
    cRetDesc := space(20)

    cSql := ""
    cEol := chr(10)

    IF ALLTRIM(cOP) == '08407801001'
        CONOUT("STOP")
    ENDIF
    cRoteiro := POSICIONE('SB1',1,XFILIAL("SB1")+cProd,'B1_OPERPAD')
    cSql :="SELECT * FROM dbo." + retsqlname("SHY") + " SHY " + cEol
    cSql +="WHERE D_E_L_E_T_=''  " + cEol
    cSql +="AND HY_FILIAL =  "+VALTOSQL( cFil) + cEol
    cSql +="AND HY_OP =       "+VALTOSQL(cOP) + cEol
    /*cSql +="AND (HY_RECURSO =  "+VALTOSQL(cRecur) + cEol
    cSql +="OR HY_CTRAB =   "+VALTOSQL(cRecur)+ cEol
    cSql +=") AND HY_OPERAC =   "+VALTOSQL(cOpera)+ cEol*/
    cSql +=" AND HY_OPERAC =   "+VALTOSQL(cOpera)+ cEol
    cSql +=" AND HY_ROTEIRO = "+VALTOSQL(cRoteiro) + cEol

    If Select('TMPSHY') <> 0
        TMPSHY->(dbCloseArea())
    Endif


    TCQuery cSql Alias TMPSHY New
    //TMPIMP->( RecCount() )
    IF  TMPSHY->(!eof())
        cRetDesc := TMPSHY->HY_DESCRI
    Endif


Return cRetDesc
