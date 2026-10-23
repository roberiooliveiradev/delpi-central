#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE "rwmake.ch"
#INCLUDE "topconn.ch"
#INCLUDE "colors.ch"

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma ³ MT097GRV ºAutor ³ Gabriel Araujo         º Data³    07/2020 º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ Rotina para validar se o pedido de compra tem saldo        º±±
±±º          ³                                                            º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/
user function MT097GRV()
    // Local aDoc:= PARAMIXB[1]
    // Local nXOpc := PARAMIXB[3]
    // Local  lVldPC := supergetmv("MV_DLPALC",.F.,.T.)
    //  Local cMsg := "Bloqueia Pedido de Compra ???"
    Local lRet := .t.
    //  lOCAL cSql :=""
    //  Local cEol := chr(10)
    //
    //  if lVldPC .and. (nXOpc == 1 .or.   nXOpc == 3) .and. aDoc[2] $ "PC"
    //
    //      cSql :="SELECT DISTINCT C7_CC, DBL.DBL_GRUPO,SUM(C7_TOTAL)C7_TOTAL  " + cEol
    //      cSql +="FROM " + RETSQLNAME("SC7")  + " SC7 (NOLOCK) " + cEol
    //      cSql +="JOIN " + RETSQLNAME("DBL")  + " DBL (NOLOCK) ON DBL.D_E_L_E_T_ ='' AND DBL.DBL_CC = SC7.C7_CC AND DBL.DBL_FILIAL =" + VALTOSQL(XFILIAL("DBL")) + cEol
    //      cSql +="JOIN " + RETSQLNAME("SB1")  + " SB1 (NOLOCK) ON SB1.D_E_L_E_T_ ='' AND SB1.B1_COD = SC7.C7_PRODUTO AND SB1.B1_FILIAL =" + VALTOSQL(XFILIAL("SB1")) + cEol
    //      cSql +="WHERE SC7.D_E_L_E_T_     = ''   " + cEol
    //      cSql +="      AND SC7.C7_FILIAL  = " + valtosql(SC7->C7_FILIAL  ) + cEol
    //      cSql +="      AND SC7.C7_NUM     = " + valtosql(SC7->C7_NUM     ) + cEol
    //      cSql +="	  AND SC7.C7_FORNECE = " + valtosql(SC7->C7_FORNECE ) + cEol
    //      cSql +="	  AND SC7.C7_LOJA    = " + valtosql(SC7->C7_LOJA    ) + cEol
    //      cSql +="	  AND SB1.B1_YVLPC   = 'S' "
    //      cSql +="GROUP BY C7_CC, DBL.DBL_GRUPO, "
    //
    //      cQuery := cSql
    //
    //      conout(cQuery)
    //
    //      If (Select("_SC7") <> 0)
    //
    //          dbSelectArea("_SC7")
    //          dbCloseArea()
    //
    //      Endif
    //
    //      TCQuery cQuery NEW ALIAS "_SC7"
    //
    //
    //      While  _SC7->(!Eof())
    //
    //
    //
    //          dbSkip()
    //
    //      Enddo
    //  endif
    //
    //   lRet := MsgYesNo(cMsg,"ATENCAO")



return (lRet )