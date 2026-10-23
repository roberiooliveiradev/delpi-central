/*/{Protheus.doc} OS010END
  Solicitacao da Joici, para que apos alteracao da
  tabela de preco seja chamado a rotina de reajuste

    OS010END - Inclui ou Altera Tabela de Preço
    Descrição:
    Ponto de entrada após a inclusão ou alteração da tabela de preço.
    Programa Fonte | OMSA010.PRW
    @type  OS010END
    @author Gabriel Araujo
    @since 02/12/2020

    ProcLogAtu(cType,cMsg,cDetalhes,cBatchProc,lCabec)
    Fonte Pardao CTBXLOG.PRW
    Possiveis Tipos

    Default INICIO
        cType == "FIM" // Final do Processamento
        Case cType == "ALERTA" // Alerta
        Case cType == "ERRO" // Erro
        Case cType == "CANCEL" // Cancelado pelo usuario
        Case cType == "MENSAGEM" // Mensagem
/*/


USER FUNCTION OS010END()
    //nTipo,nOpcao
    Local xTipo     := paramixb[1]
    Local xOpcao    := paramixb[2]
    Local cProcLog  :="OMSA010_DLP"
    Local cIdPrc    :=""
    Local lRetPer   := .f.
    Local cMsgTmp := ""
    Local cMsg := "Informações"
    //ProcLogView(,__cProcPrinc) -- Para ver no GEral

    conout("gda")
    IF xOpcao == 4
        lRetPer :=  Pergunte("OMS011",.T.)




        if lRetPer // se deu ok
          
            ProcLogIni( {},cProcLog,,@cIdPrc)
            ProcLogAtu( "INICIO", "Log Processamento Rotina de Ajuste de Preço",,,.T.) //"Log de processamento de Imp. CSV"
            cMsgTmp := "Tabela sendo Alterada => "+alltrim(DA1->DA1_CODTAB)
            ProcLogAtu("MENSAGEM",cMsg,cMsgTmp)
            cMsgTmp :="Parametros"
            ProcLogAtu("MENSAGEM",cMsg,cMsgTmp)
            cMsgTmp :="Produto De "+alltrim(MV_PAR01)
            ProcLogAtu("MENSAGEM",cMsg,cMsgTmp)
            cMsgTmp :="Produto Ate "+alltrim(MV_PAR02)
            ProcLogAtu("MENSAGEM",cMsg,cMsgTmp)
            cMsgTmp :="Grupo De "+alltrim(MV_PAR03)
            ProcLogAtu("MENSAGEM",cMsg,cMsgTmp)
            cMsgTmp :="Grupo Ate "+alltrim(MV_PAR04)
            ProcLogAtu("MENSAGEM",cMsg,cMsgTmp)
            cMsgTmp :="Tabela De "+alltrim(MV_PAR07)
            ProcLogAtu("MENSAGEM",cMsg,cMsgTmp)
            cMsgTmp :="Tabela Ate "+alltrim(MV_PAR08)
            ProcLogAtu("MENSAGEM",cMsg,cMsgTmp)
            cMsgTmp :="Processa Tabela "+ iif(MV_PAR11== 1, "Sim","Não")

            ProcLogAtu("MENSAGEM",cMsg,cMsgTmp)

            Processa({|| Oms010Proc()})

            ProcLogAtu( "FIM",,,,.T. )
        else // se cancelou

            msgalert("Processamento Cancelado pelo Usuario","Delpi OMSA010")
            ProcLogIni( {},cProcLog,,@cIdPrc)
            ProcLogAtu( "INICIO", "Informacoes","Log Processamento Rotina de Ajuste de Preço",,.T.) //"Log de processamento de Imp. CSV"
            ProcLogAtu( "CANCEL", "Cancelado pelo usuario",,,.T.) //"Log de processamento de Imp. CSV"
            ProcLogAtu( "FIM",,,,.T. )
        endif

    ENDIF
    //Pergunte("OMS011",.T.)
    //	Processa({|| Oms010Proc()})

    //  ProcLogIni( {},__cProcPrinc+"Imp",,@cIdPrc)
    //  ProcLogAtu( "INICIO", STR0125,,,.T.) //"Log de processamento de Imp. CSV"
    //  ProcLogAtu( "ERRO", STR0138+ Alltrim(__aEtapa[nX][1]) + STR0139 + Alltrim(__aEtapa[nX][2]) ,cDetalhe,,.T.)//"Classificacao do Codigo "##" Item:"
    //  ProcLogAtu( "FIM",,,,.T. )
    //  ProcLogView(cFilAnt,'AF010Imp',,cIdCV8 )
RETURN
