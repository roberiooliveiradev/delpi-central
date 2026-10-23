#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

/*/{Protheus.doc} DLP02G01
    (long_description)
    @type  Function
    @author user
    @since 11/12/2019
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
/*/
user Function DLP02G01(cRotina)
    Local aArea := getarea()
    Local xRet := ""
    Default cRotina := ALLTRIM(FUNNAME())

    if cRotina $ "MATA103" //DOCUMENTO DE ENTRADA

        sCod    :=  GdFieldGet('D1_COD')
        cCCust  := 	ALLTRIM(posicione("SBZ",1,XFILIAL("SBZ")+sCod,"BZ_CUSTO"))
        conout("Rotina -> "+cRotina +" Centro de Custo -> "+alltrim(cCCust))
        xRet    :=  cCCust
    ELSEif cRotina $ "MATA110" //SOLICITACAO DE COMPRA

        sCod    :=  GdFieldGet('C1_PRODUTO')
        cCCust  := 	ALLTRIM(posicione("SBZ",1,XFILIAL("SBZ")+sCod,"BZ_CUSTO"))
        conout("Rotina -> "+cRotina +" Centro de Custo -> "+alltrim(cCCust))
        xRet    :=  cCCust

    ELSEif cRotina $ "MATA240" // MOV INTERNA MULTIPLA
        sCod     :=  M->D3_COD // GdFieldGet('C1_PRODUTO')
        cCCust   :=  posicione("SBZ",1,XFILIAL("SBZ")+sCod,"BZ_CUSTO")
        //   M->D3_CC :=  cCCust
        xRet    :=  cCCust
        //conout("Rotina -> "+cRotina +" Centro de Custo -> "+alltrim(cCCust))
        //xRet    :=  cCCust

        // ELSEif cRotina $ "MATA241" //MOV INTERNA MULTIPLA
        //     sCod    :=   &(readvar())// GdFieldGet("D3_COD") // GdFieldGet('C1_PRODUTO')
        //     cCCust  := 	posicione("SBZ",1,XFILIAL("SBZ")+sCod,"BZ_CUSTO")
        //     cCC:=cCCust
        //     //   GdFieldput("D3_CC",cCCust,n)
        //     //   conout("Rotina -> "+cRotina +" Centro de Custo -> "+alltrim(cCCust))
        //     //   IF !EMPTY(CCC)
        //     //       CCC:=cCCust
        //     //   ENDIF
        //     xRet    :=  .t.//  &(ReadVar())
    ELSEif cRotina $ "MATA410" //SOLICITACAO DE COMPRA

        sCod    :=  GdFieldGet('C6_PRODUTO')
        cCCust  := 	ALLTRIM(posicione("SBZ",1,XFILIAL("SBZ")+sCod,"BZ_CUSTO"))
        conout("Rotina -> "+cRotina +" Centro de Custo -> "+alltrim(cCCust))
        xRet    :=  cCCust
    ENDIF

    RestArea(aArea)
Return xRet
