#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

User Function CRIASXE()
    // o retorno desse ponto de entrada precisa ser nil para tabelas que não serão tratadas
    Local cNum := NIL

    Local _aArea := FwGetArea()
    Local cAlias    := paramixb[1]
    Local cCpoSx8   := paramixb[2]
    Local cAliasSx8 := paramixb[3]
    Local nOrdSX8   := paramixb[4]
    Local cUsa := "SC7"
    Local cEol := chr(10)
    // colocar os alias que irão permitir a execução do P.E.
    if cAlias $ "SC7"

        cSql :="SELECT C7_FILIAL,MAX(C7_NUM)C7_NUM " +cEol
        cSql +="    FROM  dbo."+ RetSqlName("SC7") + "  (NOLOCK) SC7 "  +cEol
        cSql +="WHERE SC7.D_E_L_E_T_ = ''  " +cEol
        cSql +="    AND LEN(LTRIM(RTRIM(C7_NUM))) = 6  " +cEol
        cSql +="    and C7_FILIAL ="+valtosql(xfilial("SC7"))  +cEol
        cSql +="    GROUP BY C7_FILIAL  " +cEol

        If Select('TMPQRY') <> 0
            TMPQRY->(dbCloseArea())
        Endif
        TCQuery cSql Alias TMPQRY New
        if  TMPQRY->(!eof())
            cNum := SOMA1(TMPQRY->C7_NUM)
        ENDIF
    ELSEif cAlias $ "SA2"

        cSql :="SELECT MAX(A2_COD)A2_COD " +cEol
        cSql +="    FROM  dbo."+ RetSqlName("SA2") + "  (NOLOCK) SA2 "  +cEol
        cSql +="WHERE SA2.D_E_L_E_T_ = ''  " +cEol
        cSql +="    AND LEN(LTRIM(RTRIM(A2_COD))) = 6  " +cEol
        cSql +="    AND A2_COD NOT IN('VIAGF3','VIAGF2','VIAGEY','VIAGEM','ESTADO','CONSUM','CONFRA' ) " +cEol
        cSql +="    and A2_FILIAL ="+valtosql(xfilial("SA2"))  +cEol
        cSql +="    GROUP BY A2_FILIAL  " +cEol

        If Select('TMPQRY') <> 0
            TMPQRY->(dbCloseArea())
        Endif
        TCQuery cSql Alias TMPQRY New
        if  TMPQRY->(!eof())
            cNum := SOMA1(TMPQRY->A2_COD)
        ENDIF
    ELSEif cAlias $ "SA1"

        cSql :="SELECT MAX(A1_COD)A1_COD " +cEol
        cSql +="    FROM  dbo."+ RetSqlName("SA1") + "  (NOLOCK) SA1 "  +cEol
        cSql +="WHERE SA1.D_E_L_E_T_ = ''  " +cEol
        cSql +="    AND LEN(LTRIM(RTRIM(A1_COD))) = 6  " +cEol

        cSql +="    and A1_FILIAL ="+valtosql(xfilial("SA1"))  +cEol
        cSql +="    GROUP BY A1_FILIAL  " +cEol

        If Select('TMPQRY') <> 0
            TMPQRY->(dbCloseArea())
        Endif
        TCQuery cSql Alias TMPQRY New
        if  TMPQRY->(!eof())
            cNum := SOMA1(TMPQRY->A1_COD)
        ENDIF


    EndIf

    FwRestArea(_aArea)
Return cNum
