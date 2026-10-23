#Include "Protheus.ch"
#Include "RwMake.ch"
#Include "TbiConn.ch"
#Include "totvs.ch"
#INCLUDE "TOPCONN.CH"
/*Gabriel Araujo 01/2022
nao estava na versao 12.25*/
User Function MT120APV()

    Local ExpC1 := Nil
    Local ExpC2 := Nil
    Local cGrp  := "000002" //Grupo de aprovação


    // Local aDoc:= PARAMIXB[1]
    // Local nXOpc := PARAMIXB[3]
    Local  lVldPC := supergetmv("MV_DLPALC",.F.,.T.)
    Local cMsg := "Bloqueia Pedido de Compra ???"
    Local lRet := .f.
    lOCAL cSql :=""
    Local cEol := chr(10)
    lOCAL cGrp:= SUPERGETMV("MV_PCAPROV",.F.,"000001")
    Local aGrp :={}
    lOCAL cGrpRet:=""

    if lVldPC //.and. (nXOpc == 1 .or.   nXOpc == 3) .and. aDoc[2] $ "PC"

        cSql :="SELECT DISTINCT C7_CC, DBL.DBL_GRUPO,SUM(C7_TOTAL)C7_TOTAL  " + cEol
        cSql +="FROM " + RETSQLNAME("SC7")  + " SC7 (NOLOCK) " + cEol
        cSql +="JOIN " + RETSQLNAME("DBL")  + " DBL (NOLOCK) ON DBL.D_E_L_E_T_ ='' AND DBL.DBL_CC = SC7.C7_CC AND DBL.DBL_FILIAL =" + VALTOSQL(XFILIAL("DBL")) + cEol
        cSql +="JOIN " + RETSQLNAME("SB1")  + " SB1 (NOLOCK) ON SB1.D_E_L_E_T_ ='' AND SB1.B1_COD = SC7.C7_PRODUTO AND SB1.B1_FILIAL =" + VALTOSQL(XFILIAL("SB1")) + cEol
        cSql +="WHERE SC7.D_E_L_E_T_     = ''   " + cEol
        cSql +="      AND SC7.C7_FILIAL  = " + valtosql(SC7->C7_FILIAL  ) + cEol
        cSql +="      AND SC7.C7_NUM     = " + valtosql(SC7->C7_NUM     ) + cEol
        cSql +="	  AND SC7.C7_FORNECE = " + valtosql(SC7->C7_FORNECE ) + cEol
        cSql +="	  AND SC7.C7_LOJA    = " + valtosql(SC7->C7_LOJA    ) + cEol
        cSql +="	  AND SB1.B1_YVLPC   = 'S' "
        cSql +="GROUP BY C7_CC, DBL.DBL_GRUPO "

        cQuery := cSql

        conout(cQuery)



        If ( Select ( "TRBSC7" ) <> 0 )
            dbSelectArea ( "TRBSC7" )
            dbCloseArea ()
        Endif
        TCQuery cQuery NEW ALIAS "TRBSC7"


        While  TRBSC7->(!Eof())


            aadd(aGrp,TRBSC7->DBL_GRUPO)


            TRBSC7->(DbSkip())
        EndDo
        TRBSC7->(DbCloseArea())


    endif
    cGrpRet:=iif(len(aGrp) >1 ,cGrp, aGrp[1] )
    //  MSGALERT( cGrpRet,"Grupo" )
Return cGrpRet
