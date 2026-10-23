#Include "Protheus.ch"
#Include "RwMake.ch"
#Include "TbiConn.ch"
#Include "totvs.ch"
#INCLUDE "TOPCONN.CH"

/*nao estava compilado*/

USER FUNcTION dlp02W01(xEmp,xFil)
    Local cSql :=""
    Local cEol := chr(10)

    DEFAULT xEmp := cEmpAnt
    DEFAULT xFil := cFilAnt
    If Select("SX6") == 0
        CONOUT("ENTROU NO X6")
        RpcSetType(3)

        RpcSetEnv(xEmp,xFil)
        lJob := .t.
    EndIf

    cSql+=" SELECT SCR.CR_NUM,SCR.CR_USER,C7_EMISSAO,SCR.R_E_C_N_O_ [RECSCR],SC7.C7_CC,CTT.CTT_DESC01,SCR.CR_TOTAL,SC7.C7_NUMSC,ISNULL(SC1.C1_USER, '') C1_USER ,SC7.C7_FORNECE,SC7.C7_LOJA,SA2.A2_NREDUZ" + cEol
    cSql+=" FROM dbo." + RETSQLNAME("SCR")  + " SCR (NOLOCK)      " + cEol
    cSql+="     JOIN dbo." + RETSQLNAME("SC7")  + " SC7 (NOLOCK)  " + cEol
    cSql+="         ON SC7.D_E_L_E_T_ = '' AND SC7.C7_FILIAL = SCR.CR_FILIAL  AND SC7.C7_NUM = SCR.CR_NUM " + cEol
    cSql+="     LEFT JOIN dbo." + RETSQLNAME("SC1")  + " SC1 (NOLOCK) " + cEol
    cSql+="         ON SC1.D_E_L_E_T_ = '' AND SC1.C1_FILIAL = SC7.C7_FILIAL  AND SC1.C1_NUM = SC7.C7_NUMSC  AND SC1.C1_ITEM = SC7.C7_ITEMSC " + cEol
    cSql+="         AND SC1.C1_PRODUTO = SC7.C7_PRODUTO " + cEol
    cSql+="    JOIN dbo." + RETSQLNAME("CTT")  + " CTT ON CTT.D_E_L_E_T_ ='' AND CTT.CTT_FILIAL ='' AND CTT.CTT_CUSTO = SC7.C7_CC " + cEol
    cSql+="   JOIN dbo." + RETSQLNAME("SA2")  + " SA2 ON SA2.D_E_L_E_T_= '' AND SA2.A2_COD = SC7.C7_FORNECE AND SA2.A2_LOJA = SC7.C7_LOJA   " + cEol
    cSql+=" WHERE SCR.D_E_L_E_T_    = ''      " + cEol
    cSql+="       AND SCR.CR_STATUS = '02'    " + cEol
    cSql+="       AND SCR.CR_ENFWF  = ''      " + cEol
    cSql+="       AND SCR.CR_TIPO   = 'PC'    "




    cQuery := cSql

    conout(cQuery)



    If ( Select ( "TRBSCR" ) <> 0 )
        dbSelectArea ( "TRBSCR" )
        dbCloseArea ()
    Endif
    TCQuery cQuery NEW ALIAS "TRBSCR"


    While  TRBSCR->(!Eof())

        xMailApv := UsrRetMail(TRBSCR->CR_USER)
        xCusto   := TRBSCR->C7_CC +  TRBSCR->CTT_DESC01
        xFl      := xFil
        xSolict  := ALLTRIM(TRBSCR->C7_NUMSC)+" / "+ UPPER(UsrFullName(TRBSCR->C1_USER))
        xDt      := TRBSCR->C7_EMISSAO
        xPedido  := TRBSCR->CR_NUM
        xFornece := ALLTRIM(TRBSCR->C7_FORNECE)+"/"+ALLTRIM(TRBSCR->C7_LOJA)+ ' - '+ ALLTRIM(TRBSCR->A2_NREDUZ)
        xTotal   :=  TRBSCR->CR_TOTAL

        EnvWF(xMailApv ,xCusto   ,xFl      ,xSolict  ,xDt      ,xPedido  ,xFornece ,xTotal   )
        TRBSCR->(DbSkip())
    EndDo
    TRBSCR->(DbCloseArea())

Return

Static function EnvWF(xMailApv ,xCusto   ,xFl      ,xSolict  ,xDt      ,xPedido  ,xFornece ,xTotal   )

    Local oProcess := Nil
    Local cNewArq := ""


    oProcess := TWFProcess():New("DLP02W01","WFDELPICOMPRAS" )

    oProcess:NewTask("DLP02W01","\WF\DelpiPedidodeCompra.html")
    oProcess:cSubject := "WF Aprovacao Pedido de Compra - Filial " + xFl + " Pedido " + xPedido
    oProcess:cTo      := xMailApv
    oProcess:cBCC :="gabriel.araujo@totvs.com.br"

    oProcess:oHtml:ValByName("cCCusGestor"  ,xCusto)
    oProcess:oHtml:ValByName("cFil"         ,xFl)
    oProcess:oHtml:ValByName("cSolicit"     ,xSolict)
    oProcess:oHtml:ValByName("dDtPed"       ,DTOC(STOD(xDt))  )
    oProcess:oHtml:ValByName("cPedido"      ,xPedido)
    oProcess:oHtml:ValByName("cFornece"     ,xFornece)
    oProcess:oHtml:ValByName("Total"        ,Transform(xTotal,"@E 999,999,999.9999"))


    oProcess:Start()
    oProcess:Finish()

return
