#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"

/**					If lA140IQTD
    aA140IQTD := ExecBlock("A140IQTD",.F.,.F.,{cProduto,cUM,cSEGUM,nQtSEGUM,nQtdeIt,nPrcIt,nTotIt,lConvUM,cCodigo,cLoja,cDoc,cSerie,cTipoNF,Iif(cTipoNF $ "BD",.T.,.F.),oXML})
    If ValType(aA140IQTD) == "A" .And. Len(aA140IQTD) == 4
        nQtdeIt	 := aA140IQTD[1]
        nPrcIt	 := aA140IQTD[2]
        nTotIt	 := aA140IQTD[3]
        nQtSEGUM := aA140IQTD[4]
EndIf	*/
user function A140IQTD()

    Local cProduto  := PARAMIXB[1]
    Local cUM       := PARAMIXB[2]
    Local cSEGUM    := PARAMIXB[3]
    Local nQtSEGUM  := PARAMIXB[4]
    Local nQtdeIt   := PARAMIXB[5]
    Local nPrcIt    := PARAMIXB[6]
    Local nTotIt    := PARAMIXB[7]
    Local lConvUM   := PARAMIXB[8]
    Local cForn     := PARAMIXB[9]
    Local cLoja     := PARAMIXB[10]
    Local cDoc      := PARAMIXB[11]
    Local nSerie    := PARAMIXB[12]
    Local nTipo     := PARAMIXB[13]
    Local lA5A7     := PARAMIXB[14]
    Local oXML      := PARAMIXB[15]

    Local aRet := Array(4)

    nQtd :=	0.00
    nVlrUnit := 0.00

    /*    A5_CONV
    A5_TPCONV*/
    //A5_FILIAL, A5_FORNECE, A5_LOJA, A5_PRODUTO, A5_FABR, A5_FALOJA, A5_REFGRD, R_E_C_N_O_, D_E_L_E_T_
    // Gabriel
    //A7_FILIAL, A7_CLIENTE, A7_LOJA, A7_PRODUTO, R_E_C_N_O_, D_E_L_E_T_
    IF !lA5A7
        conout("Posicionou SA5  nQtdeIt "+cvaltochar(nQtdeIt))
        conout("Posicionou SA5  nPrcIt "+cvaltochar(nPrcIt))
        //  MsgStop("gabriel", "GABRIEL2")
        IF 	SA5->(MsSeek(xFilial("SA5")+cForn+cLoja+cProduto    ))
            conout("Posicionou SA5")
            if SA5->A5_CONV> 0.00

                // cUm := SA7->A7_UM3

                IF ALLTRIM(SA5->A5_TPCONV) $ "D"
                    nQtd := nQtdeIt / SA5->A5_CONV
                    nVlrUnit :=  nPrcIt *   SA5->A5_CONV
                ELSE
                    nQtd := nQtdeIt * SA5->A5_CONV
                    nVlrUnit :=  nPrcIt /   SA5->A5_CONV
                ENDIF

            ENDIF
            conout("Posicionou SA5  nQtd "+cvaltochar(nQtd))
            conout("Posicionou SA5  nVlrUnit "+cvaltochar(nVlrUnit))
        ENDIF
    else
        //-------------------------------------------------------------------------------
        /*/ Ajustado para contemplar o Cliente X Produto nas notas de beneficiamento
            No momento de Sair é necessario inverter os operadores Quando entra com o Fator
            multiplicador tem a necessidade de fazer o fator de divisão
            @author  Gabriel Araujo
            @since   05/02/2025
        /*/
        //-------------------------------------------------------------------------------
        IF 	SA7->(MsSeek(xFilial("SA7")+cForn+cLoja+cProduto))
            if ALLTRIM(SA7->A7_NF3UM) $ "S"

                cUm := SA7->A7_UM3

                IF ALLTRIM(SA7->A7_TPCONV) $ "D"
                    nQtd := nQtdeIt * SA7->A7_CONV3
                    nVlrUnit :=  nPrcIt *   SA7->A7_CONV3

                ELSE
                    nQtd := nQtdeIt / SA7->A7_CONV3
                    nVlrUnit :=  nPrcIt /    SA7->A7_CONV3
                ENDIF


            ENDIF
        endif


    ENDIF


    //if alltrim(cForn) == "000338" .and. alltrim(cProduto) $ '10020003'
    if nQtd> 0 .and.  nVlrUnit > 0
        aRet[1] := nQtd
        aRet[2] := nVlrUnit
        aRet[3] := nTotIt
        aRet[4] := nQtSEGUM

    else
        aRet[1] := nQtdeIt
        aRet[2] := nPrcIt
        aRet[3] := nTotIt
        aRet[4] := nQtSEGUM

    endif
    conout("aRet[1] "+cvaltochar(aRet[1]))
Return aRet
