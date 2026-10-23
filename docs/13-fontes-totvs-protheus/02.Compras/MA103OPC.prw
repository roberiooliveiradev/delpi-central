#INCLUDE 'totvs.ch'
#INCLUDE 'FWMVCDEF.CH'
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWPrintSetup.ch"
#Include 'TopConn.ch'
#Include "RPTDef.ch"
#INCLUDE "PROTHEUS.CH"
#INCLUDE "AP5MAIL.CH"

User Function MA103OPC()
    Local aRet := {}

    CONOUT("STOP")
    ///CHKFILE("ZA1")
    //  aAdd(aRet,{'Etiqueta Almox', 'U_DL04A01', 0, 5})
    aAdd(aRet,{'Etiqueta Delpi', 'U_DLP10E05A(SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA,SF1->F1_FILIAL)', 0, 5})
    aadd(aRet,{'Etiqueta Delpi - Novo', 'U_DLP10E05N(SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA,SF1->F1_FILIAL)', 0, 5})
    //   aAdd(aRet,{'Dlp Ins Emp', 'U_D10E05B()', 0, 5})

Return aRet



