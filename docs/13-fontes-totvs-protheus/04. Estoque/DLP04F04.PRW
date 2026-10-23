#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"

/*/{Protheus.doc} User Function ASCRZC2
    Relatório ZC2 - Importação Repasse
    @type  Function
    @author Luan Woichechoscki
    @since 19/09/2022
/*/
User Function DLP04F04()
    Local dDataFec:= superGETMV("MV_ULMES",.f.,"",cFilAnt)
    Local cAno := Year2Str(MonthSum(dDataFec,1))
    Local cMes := Month2Str(MonthSum(dDataFec,1))
    Local cPerg :="DLP04F04"
    Private aParBox := {}
    aPergs :={}
    aAdd(aPergs, {1, "Filial "    , cFilAnt,  "", ".T.", "SM0", ".T.", 80,  .T.})
    aAdd(aPergs, {1, "Ano"    ,   cAno,  "@E 9999", ".T.", "", ".T.", 80,  .T.})
    aAdd(aPergs, {1, "Mes"    ,   cMes,  "@E 99", ".T.", "", ".T.", 80,  .T.})
    //IF !ParamBox(aPergs, "Pos Cta Receber - Importadoras ",@aRet,,,,,,,cPerg,.t.,.t.)
    IF !ParamBox(aPergs, "Informe os parâmetros",@aParBox,,,,,,,cPerg,.t.,.t.)

        MsgStop("Cancelado pelo usuario", "Delpi")
        return
    ENDIF
    FWMsgRun(, {|| fProc() }, "DELPI","Aguarde Processando" )
Return


Static Function fProc()

    cUpd := "EXEC dbo.STP_PROTHEUS_DELPI_AJUSTA_OP "
    cUpd += "   @FILIAL = "+valtosql(MV_PAR01)
    cUpd += "   , @ANOMES = "+valtosql(MV_PAR02+MV_PAR03)

    CONOUT(cUpd)

    TCSqlExec(cUpd)
Return
