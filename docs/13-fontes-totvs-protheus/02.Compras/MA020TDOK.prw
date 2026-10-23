#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"

user function MA020TDOK ()

    conout("stops")

    if altera .or. inclui
        cTabPRC := M->A2_ZTABPRC
        cCodFor:= iif(altera,SA2->A2_COD,M->A2_COD)
        cLojFor := iif(altera,SA2->A2_LOJA,M->A2_LOJA)
        IF !eMPTY(cTabPRC)
            if FWAlertYesNo("Deseja atualizar tabela Produto X Fornecedor ?","Delpi - Compras")
                FWMsgRun(, {|| fPrcSA2(cTabPRC,cCodFor,cLojFor) } , "Delpi", "Processando")
            endif
        endif
    endif

Return .t.


static function fPrcSA2(cTabPRC,cCodFor,cLojFor)

    Local cEol := chr(10)

    cUpd := "UPDATE  dbo." + retsqlname("SA5") +  cEol
    cUpd += "   SET A5_CODTAB  = "+valtosql(cTabPRC) + cEol
    cUpd += "   WHERE D_E_L_E_T_ = ''" + cEol
    cUpd += "   AND A5_PRODUTO+A5_FORNECE+A5_LOJA  IN (SELECT   DISTINCT  AIB_CODPRO + AIB_CODFOR+AIB_LOJFOR " + cEol
    cUpd += "       FROM dbo." + retsqlname("AIB") + " AIB " + cEol
    cUpd += "               WHERE AIB.D_E_L_E_T_ = ''" + cEol
    cUpd += "                   AND AIB.AIB_CODFOR = " + valtosql(cCodFor) + cEol
    cUpd += "                   and	AIB.AIB_LOJFOR = " + valtosql(cLojFor) + cEol
    cUpd += "                   and	AIB.AIB_CODTAB = " + valtosql(cTabPRC) +" )"

    conout(cUpd)
    TCSQLExec(cUpd)
Return
