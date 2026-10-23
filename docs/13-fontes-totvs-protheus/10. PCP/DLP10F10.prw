#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"

//-------------------------------------------------------------------
/*/{Protheus.doc} DLP10F10
Função para validar a quantidade Fixa da OP
@author  author
@since   date
@version version
/*/
//-------------------------------------------------------------------
user function DLP10F10(nQtdOri)
    lRet := .t.
    cCodProd := M->C2_PRODUTO
    cEol := chr(10)
    dbSelectArea("SBZ")
    SBZ->(dbSetOrder(1))
    If   SBZ->(dBSeek(xFilial("SBZ")+cCodProd))



        if !EMPTY( SBZ->BZ_YQBOP ) .and.( Mod(nQtdOri,SBZ->BZ_YQBOP ) !=0)

            cUm   :=     posicione("SB1",1,XFILIAL("SB1")+cCodProd,"B1_UM")
            cDesc :=  Alltrim(posicione("SB1",1,XFILIAL("SB1")+cCodProd,"B1_DESC"))
            cMsg  :=  "Atenção " +cEol
            cMsg  +=  "O Produto "+alltrim(cCodProd)+" - "+cDesc+cEol
            cMsg  +=  " Tem quantidade Multipla de "+cvaltochar(SBZ->BZ_YQBOP )+" "+ cUm+cEol

            FWAlertError( cMsg, "Delpi -PCP")

            lRet := .f.
        endif
    endif
Return lRet
