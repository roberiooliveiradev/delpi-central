#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#Include 'FWMVCDef.ch'

#DEFINE COR_AZUL              'rgb(0,0,165)'
#DEFINE COR_VERMELHO          'rgb(241,143,136)'
#DEFINE COR_AZUL_CLARO        'rgb(0,255,255)'
#DEFINE COR_CINZA             'rgb(128,128,128)'
#DEFINE COR_AMARELO           'rgb(255,255,0)'
#DEFINE COR_VERDE             'rgb(126,226,148)'
#DEFINE COR_ROXO              'rgb(153,0,153)'
#DEFINE COR_ROSA              'rgb(255,51,153)'
#DEFINE COR_BRANCO            'rgb(255,255,255)'
#DEFINE COR_LARANJA           'rgb(255,128,0)'
#DEFINE COR_VERDE_FORTE       'rgb(38,186,65)'
#DEFINE COR_VERMELHO_FORTE    'rgb(245,0,49)'
#DEFINE COR_AMARELO_ESCURO    'rgb(255,207,1)'
#DEFINE COR_PRETO             'rgb(0,0,0)'
#DEFINE COR_AMARELO_QUEIMADO  'rgb(238,173,45)'

Class DlpFaturamento FROM LongNameClass
    Static Method BuscaDados(oFiltros, cTipo, cSubTipo)
    Static Method BuscaDetalhes(oFiltros, nPagina)
    Static Method ValidaPropriedades(oFiltros)
EndClass



/*/{Protheus.doc} BuscaDados DLP10F12
Responsável por realizar a busca dos dados que serão exibidos no monitor
@type Class
@author
@since
@version
@param  oFiltros  , objeto Json, Contém as propriedades do monitor usadas para filtrar a query de busca
@param  cTipo     , caracter   , Tipo chart/info
@param  cSubTipo  , caracter   , Tipo de grafico pie/bar/column
@return cJsonDados, caracter   , Retorna um novo Json em formato texto, pronto para conversão e exibição no front
/*/
Method BuscaDados(oFiltros, cTipo, cSubTipo) Class DlpFaturamento
    Local oJsonRet   := JsonObject():New()
    Local oGauge     := PCPMonitorGauge():New()
    Local oStylePrc  := JsonObject():New()
    Local cAliasQry  := GetNextAlias()
    Local cAliasSZC  := GetNextAlias()
    Local cEol := chr(10)
    //Propriedades que devem ser retornadas para monitores do tipo gráfico      //Propriedades que devem ser retornadas para monitores do tipo gráfico
    oJsonRet["corTitulo"]          := "black" //Cor do título do monitor. Se não for informada, assumirá o valor #2590aa
    oJsonRet["alturaMinimaWidget"] := "350px" //Altura mínima do monitor. Se não for informada, assumirá o valor 350px
    oJsonRet["alturaMaximaWidget"] := "350px" //500 Altura máxima do monitor. Se não for informada, assumirá o valor 350px
    oJsonRet["tags"]               := {}      //Array de objetos json com as tags que serão visualizadas no monitor
    oJsonRet["series"]             := {}      //Array de objetos json com as séries do gráfico. Será apenas inicializado para o gráfico do tipo velocímetro.
    oJsonRet["categorias"]         := {}      //Array de strings com as categorias do gráfico. Será apenas inicializado para o gráfico do tipo velocímetro.
    oJsonRet["linhas"] :={}
    //Especifica as propriedades do gráfico tipo velocímetro
    IF VALTYPE(oFiltros["01_EMPRESA"]) =="A"
        if len(oFiltros["01_EMPRESA"]) >0
            cCodEmp := oFiltros["01_EMPRESA"][1]
        endif
    ELSE
        cCodEmp := oFiltros["01_EMPRESA"]
    ENDIF

    IF VALTYPE(oFiltros["02_FILIAL"]) =="A"
        if len(oFiltros["02_FILIAL"]) >0
            cCodFil := oFiltros["02_FILIAL"][1]
        endif
    ELSE
        cCodFil := oFiltros["02_FILIAL"]
    ENDIF

    IF VALTYPE(oFiltros["03_TIPOMETA"]) =="A"
        if len(oFiltros["03_TIPOMETA"]) >0
            cTpMeta := oFiltros["03_TIPOMETA"][1]
        endif
    ELSE
        cTpMeta := oFiltros["03_TIPOMETA"]
    ENDIF
    //1 - WEG
    //2 - Novos Negocios
    //3 - Geral


    IF VALTYPE(oFiltros["04_PERIODO"]) =="A"
        if len(oFiltros["04_PERIODO"]) >0
            cTPData := oFiltros["04_PERIODO"][1]
        endif
    ELSE
        cTPData := oFiltros["04_PERIODO"]
    ENDIF



    cAnoMes := substr(dtos(ddatabase),1,6)
    // if cCodEmp != cEmpAnt
    //     cEmpAnt := cCodEmp
    //     cFilAnt := cCodFil
    //     FWSM0Util():setSM0PositionBycFilAnt()
    // endif

    // cCodFil  := cFilAnt
    // cCodFil  := cFilAnt
    cProdDe  := Space(TamSx3('B1_COD')[1])
    cProdAte := REPLICATE("Z",GETSX3CACHE("B1_COD","X3_TAMANHO"))
    if cTPData == 'M'
        cEmisDe  := FirstDate(DATE())
        cEmisAte := LastDate(DATE())
    ELSE
        cEmisDe  :=  FirstYDate(DATE())
        cEmisAte :=  LastYDate(DATE())
    ENDIF
    IF cTpMeta == '1' //Weg

        cCliDe   := '000001'
        cCliAte  := '000001'

    ELSEIF cTpMeta == '2' //Novos Negocios
        cCliDe   := '000002'
        cCliAte  := REPLICATE("Z",GETSX3CACHE("A1_COD","X3_TAMANHO"))
    ELSE
        cCliDe  :=  Space(TamSx3('A1_COD')[1])
        cCliAte := REPLICATE("Z",GETSX3CACHE("A1_COD","X3_TAMANHO"))
    ENDIF
    cLojaDe := Space(TamSx3('A1_LOJA')[1])
    cLojaAte := REPLICATE("Z",GETSX3CACHE("A1_LOJA","X3_TAMANHO"))

    cSql := "EXEC STP_DELPI_FATURAMENTO_"+cCodEmp+" "
    cSql +=  valtosql(cCodFil   ) +" , " //@FILIALDE
    cSql +=  valtosql(cCodFil   ) +" , " //@FILIALATE
    cSql +=  valtosql(cProdDe   ) +" , " //@PRODUTODE
    cSql +=  valtosql(cProdAte  ) +" , " //@PRODUTOATE
    cSql +=  valtosql(cEmisDe   ) +" , " //@EMISSAODE
    cSql +=  valtosql(cEmisAte  ) +" , " //@EMISSAOATE
    cSql +=  valtosql(cCliDe    ) +" , " //@CLIENTEDE
    cSql +=  valtosql(cCliAte   ) +" , " //@CLIENTEATE
    cSql +=  valtosql(cLojaDe   ) +" , " //@LOJADE
    cSql +=  valtosql(cLojaAte  ) +" , " //@LOJAATE
    IF cCodEmp == '01'
        cSql +=  valtosql('A') +" , " //@ESTOQUE
    ELSE
        cSql +=  valtosql('S') +" , " //@ESTOQUE
    ENDIF
    cSql +=  valtosql('S') //@DUPLICATA

    dbUseArea(.T.,"TOPCONN",TcGenQry(,,cSql),cAliasQry,.F.,.F.)
    nVlrFat :=  0.00
    WHILE  (cAliasQry)->(!Eof())

        nVlrFat +=   (cAliasQry)->LIQUIVENDA
        nVlrFat +=   (cAliasQry)->LIQDEV    *-1

        (cAliasQry)->(dbSkip())

    ENDDO
    (cAliasQry)->(dbCloseArea())

    cQuery := "SELECT sum(ZC_ORCFAT) ZC_ORCFAT  " + cEol
    cQuery += "FROM dbo.SZC010  (NOLOCK) SZC   " + cEol
    cQuery += "WHERE SZC.D_E_L_E_T_ = ''  " + cEol
    cQuery += "AND ZC_FILIAL =  ' ' "+ cEol
    cQuery += "AND ZC_FIL    =  "+VALTOSQL(cCodFil) + cEol
    cQuery += "AND ZC_EMP    =  "+VALTOSQL(cCodEmp) + cEol

    if cTpMeta != '3'

        cQuery += "AND ZC_TIPO   =  "+VALTOSQL(cTpMeta) + cEol
    endif
    if cTPData == 'M'
        cQuery += "AND ZC_ANOMES =  "+VALTOSQL(cAnoMes) + cEol
    else

        cQuery += "AND substring(ZC_ANOMES,1,4) =  "+VALTOSQL(substr(cAnoMes,1,4)) + cEol
    endif

    dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQuery),cAliasSZC,.F.,.F.)


    if  (cAliasSZC)->(!Eof())
        nVlrMeta :=   (cAliasSZC)->ZC_ORCFAT
    endif
    (cAliasSZC)->(dbCloseArea())
    //nValorFim := 25000 //Valor Maximo da Meta
    nPerMeta := round((nVlrFat /nVlrMeta )*100,2)
    cType :="arch" //Especifica o tipo do velocímetro. "semi","arch","full"
    nValSemaf1 := 70
    nValSemaf2 := 90
    nValorFim := 100
    cValSemaf1 := "70"
    cValSemaf2 := "90"
    cValorFim := "100"
    nThick:= 20//Especifica a espessura da barra do velocímetro.
    cClrRed := "rgb(198, 72, 64)"
    cClrLar := "rgb(234, 155, 62)"
    cClrGre := "rgb(0, 178, 142)"
    cHxGre:="#00b28e"
    cHxRed:="#c64940"
    if cTPData == 'M'
        cEmisDe  := FirstDate(DATE())
        cEmisAte := LastDate(DATE())
    ELSE
        cEmisDe  :=  FirstYDate(DATE())
        cEmisAte :=  LastYDate(DATE())
    ENDIF
    /*
        M - como abreviação para "thousand" (mil, em português)
        MM - como abreviação para "million" (milhão, em português)
    */
    //Dias úteis Abril 2020 sem considerar fim de semana  e feriados como dia útil.
    lSaturday  := .F.
    lSunday    := .F.
    lHoliday   := .F.
    nRetMes := DateWorkDay(cEmisDe,cEmisAte,lSaturday,lSunday ,lHoliday )
    nRetAtu := DateWorkDay(cEmisDe,date(),lSaturday,lSunday ,lHoliday )
    nVlrPrev :=( (nVlrFat/nRetAtu)*nRetMes)
    cLabel := "% Atingido"
    cLabel += "<br>Meta: R$ "+Transform(nVlrMeta,"@E 999,999,999.99")
    cLabel += "<br>Realizado: R$ "+Transform(nVlrFat,"@E 999,999,999.99")
    // if nVlrPrev <  nVlrMeta
    //     //vermelho
    //     cLabel += '<br><p style="color:'+cHxRed+'"; >Previsto: R$ '+Transform(nVlrPrev,"@E 999,999,999.99")+"</p>"
    // else
    //     //verde
    //     cLabel += '<br><p style="color:'+cHxGre+'"; >Previsto: R$ '+Transform(nVlrPrev,"@E 999,999,999.99")+"</p>"
    // endif
    cLabel1 := '<br>Previsto: R$ '+Transform(nVlrPrev,"@E 999,999,999.99")
    //cLabel2 := 'Previsto: R$ '+Transform(nVlrPrev,"@E 999,999,999.99")
    aCateg :={}
    aadd(aCateg,"Categoria1")
    aadd(aCateg,"Categoria2")
    aadd(aCateg,"Categoria3")
    //cPrepend :="TESTE PREPEND"
    //  oGauge:SetPrepend(cPrepend)
    oGauge:SetMaxValue(nValorFim)
    oGauge:SetValue(nPerMeta)
    oGauge:SetMargin(10)
    oGauge:SetType(cType)
    oGauge:SetThick(nThick)
    // oGauge:SetValueStyle("color",IIF(nPerMeta < nValSemaf1,cClrRed,IIF(nPerMeta < nValSemaf2,cClrLar,COR_VERDE_FORTE)))
    oGauge:SetValueStyle("color",IIF(nPerMeta < nValSemaf1,COR_VERMELHO_FORTE,IIF(nPerMeta < nValSemaf2,COR_AMARELO_QUEIMADO,COR_VERDE_FORTE)))
    oGauge:SetValueStyle("text-align","center")
    oGauge:SetValueStyle("font-weight","bold")
    oGauge:SetValueStyle("font-size","30px")
    //oGauge:SetValueStyle("line-height","0px")

    oGauge:SetLabelStyle("font-weight","bold")
    oGauge:SetLabelStyle("text-align","center")
    oGauge:SetLabelStyle("font-size","15px")
    oGauge:SetLabelStyle("line-height","1")
    oGauge:SetLabel(cLabel)
    oGauge:SetAppendStyle("color",IIF(nVlrPrev <  nVlrMeta,COR_VERMELHO_FORTE,COR_VERDE_FORTE))
    oGauge:SetAppendStyle("text-align","center")
    oGauge:SetAppendStyle("font-weight","bold")
    oGauge:SetAppendStyle("font-size","15px")
    oGauge:SetAppendStyle("line-height","5.5")
    oGauge:SetAppend(cLabel1)

    oGauge:SetThreshold("0",COR_VERMELHO_FORTE)
    oGauge:SetThreshold(cValSemaf1,COR_AMARELO_QUEIMADO)
    oGauge:SetThreshold(cValSemaf2,COR_VERDE_FORTE)
    If Val(cValSemaf1) > 0
        oGauge:SetMarker("0")
    Endif
    oGauge:SetMarker(cValSemaf1)
    oGauge:SetMarker(cValSemaf2)
    oGauge:SetMarker(cValorFim)
    //Atribui o objeto json do velocímetro ao objeto json de retorno do método
    oJsonRet["gauge"]      := oGauge:GetJsonObject()


    oStylePrc["color"] := "red"
    nIndLinha := 0
    cStylePO := "po-font-text-large po-text-center po-sm-4 po-pt-3"
    PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,"teste 1 Previsto: R$ "+Transform(nVlrPrev,"@E 999,999,999.99")   ,cStylePO,oStylePrc:ToJson(),.f.,)
    ////PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,"teste 222",cStylePO,oStylePrc:ToJson(),.f.,)
    ////PCPMonitorUtils():AdicionaLinhaInformacao(oJsonRet["linhas"],@nIndLinha,"teste 333",cStylePO,oStylePrc:ToJson(),.f.,)
    // PCPMonitorUtils():AdicionaCategoriasGraficoMonitor(oJsonRet["categorias"], aCateg)
    //Adiciona tags ao monitor
    if   cTPData  =='A'
        cAnoMes :="Ano: " + substr(dtos(ddatabase),1,4)
    ELSE
        cAnoMes :="Ano/Mes: " +substr(dtos(ddatabase),1,4)+'/'+substr(dtos(ddatabase),5,2)
    ENDIF
    nPos := 0
    PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-calendar",  cAnoMes)

    if cTpMeta == '1'

        PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-bar-manufacture","WEG")

    endif
    if cTpMeta == '2'

        PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-bar-manufacture","Novos Negocios")

    endif

    if cTpMeta == '3'

        PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-bar-manufacture","Geral")

    endif

    // PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-calendar",cValToChar(ddatabase) + " - " + cValToChar(dFilterDat))
    // PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-bar-code",cCodProd)
    // If cTipo == "chart"
    //     PCPMonitorUtils():AdicionaTagMonitor(oJsonRet["tags"],@nPos,"po-icon-star-filled",IIF(oFiltros["04_TIPOSEMAFORO"] == "L",cValToChar(nSaldo) + " " + cUnMedida,cValToChar(nLotes) + IIF(nLotes > 1, " Lotes", " Lote")))
    // EndIf
    cJsonDados :=  oJsonRet:toJson()


    FreeObj(oGauge)
    FreeObj(oJsonRet)
Return cJsonDados


/*/{Protheus.doc} BuscaDetalhes
Responsável por realizar a busca dos dados que serão exibidos no detalhamento do monitor
@type Class
@author
@since
@version
@param  oFiltros  , objeto Json , Contém as propriedades do monitor usadas para filtrar a query de busca
@param  nPagina   , numerico    , Número da página desejada para busca
@return cJsonDados, caracter    , Retorna um novo Json em formato texto, pronto para conversão e exibição no front
/*/
Method BuscaDetalhes(oFiltros, nPagina) Class DlpFaturamento
    Local cAliasQry  := GetNextAlias()
    Local cJsonDados := ""
    Local cQuery     := ""
    Local cOp        := ""
    Local cStatusOp  := ""
    Local dDataIni   := dDataBase
    Local dDataFin   := dDataBase
    Local lExpResult := .F.
    Local nIndice    := 0
    Local nPos       := 0
    Local nPosTag   := 0
    Local nStart     := 0
    Local oDados     := JsonObject():New()
    Local cEol := chr(10)
    Local nStepLog := 0
    Default nPagina    := 1
    Default nTamPagina := 10
    //FWLogMsg("DEBUG", /*cTransactionId*/, "DlpFaturamento - BuscaDetalhes", ;
    //    /*cCategory*/, /*cStep nStepLog */, /*cMsgId*/, "Inicio", /*nMensure*/, /*nElapseTime*/, /*aMessage*/)

    If nPagina == 0
        lExpResult := .T.
    EndIf


    IF VALTYPE(oFiltros["01_EMPRESA"]) =="A"
        if len(oFiltros["01_EMPRESA"]) >0
            cCodEmp := oFiltros["01_EMPRESA"][1]
        endif
    ELSE
        cCodEmp := oFiltros["01_EMPRESA"]
    ENDIF

    IF VALTYPE(oFiltros["02_FILIAL"]) =="A"
        if len(oFiltros["02_FILIAL"]) >0
            cCodFil := oFiltros["02_FILIAL"][1]
        endif
    ELSE
        cCodFil := oFiltros["02_FILIAL"]
    ENDIF

    IF VALTYPE(oFiltros["03_TIPOMETA"]) =="A"
        if len(oFiltros["03_TIPOMETA"]) >0
            cTpMeta := oFiltros["03_TIPOMETA"][1]
        endif
    ELSE
        cTpMeta := oFiltros["03_TIPOMETA"]
    ENDIF
    //1 - WEG
    //2 - Novos Negocios
    //3 - Geral


    IF VALTYPE(oFiltros["04_PERIODO"]) =="A"
        if len(oFiltros["04_PERIODO"]) >0
            cTPData := oFiltros["04_PERIODO"][1]
        endif
    ELSE
        cTPData := oFiltros["04_PERIODO"]
    ENDIF



    cAnoMes := substr(dtos(ddatabase),1,6)
    if cCodEmp != cEmpAnt
        cEmpAnt := cCodEmp
        cFilAnt := cCodFil
        FWSM0Util():setSM0PositionBycFilAnt()
    endif

    cCodFil  := cFilAnt
    cCodFil  := cFilAnt
    cProdDe  := Space(TamSx3('B1_COD')[1])
    cProdAte := REPLICATE("Z",GETSX3CACHE("B1_COD","X3_TAMANHO"))
    if cTPData == 'M'
        cEmisDe  := FirstDate(DATE())
        cEmisAte := LastDate(DATE())
    ELSE
        cEmisDe  :=  FirstYDate(DATE())
        cEmisAte :=  LastYDate(DATE())
    ENDIF
    IF cTpMeta == '1'
        cCliDe   := '000001'
        cCliAte  := '000001'
    ELSEIF  cTpMeta == '2'
        cCliDe   := '000002'
        cCliAte  := REPLICATE("Z",GETSX3CACHE("A1_COD","X3_TAMANHO"))
    ELSE
        cCliDe  :=  Space(TamSx3('A1_COD')[1])
        cCliAte := REPLICATE("Z",GETSX3CACHE("A1_COD","X3_TAMANHO"))
    ENDIF
    cLojaDe := Space(TamSx3('A1_LOJA')[1])
    cLojaAte := REPLICATE("Z",GETSX3CACHE("A1_LOJA","X3_TAMANHO"))


    cSql := "EXEC STP_DELPI_FATURAMENTO_"+cCodEmp+" "
    cSql +=  valtosql(cCodFil   ) +" , " //@FILIALDE
    cSql +=  valtosql(cCodFil   ) +" , " //@FILIALATE
    cSql +=  valtosql(cProdDe   ) +" , " //@PRODUTODE
    cSql +=  valtosql(cProdAte  ) +" , " //@PRODUTOATE
    cSql +=  valtosql(cEmisDe   ) +" , " //@EMISSAODE
    cSql +=  valtosql(cEmisAte  ) +" , " //@EMISSAOATE
    cSql +=  valtosql(cCliDe    ) +" , " //@CLIENTEDE
    cSql +=  valtosql(cCliAte   ) +" , " //@CLIENTEATE
    cSql +=  valtosql(cLojaDe   ) +" , " //@LOJADE
    cSql +=  valtosql(cLojaAte  ) +" , " //@LOJAATE
    IF cCodEmp == '01'
        cSql +=  valtosql('A') +" , " //@ESTOQUE
    ELSE
        cSql +=  valtosql('S') +" , " //@ESTOQUE
    ENDIF
    cSql +=  valtosql('S') //@DUPLICATA
    // nStepLog++
    // aMessage := {}
    // aAdd(aMessage, {"Query", cSql})
    // FWLogMsg("DEBUG", /*cTransactionId*/, "DlpFaturamento - BuscaDetalhes", ;
    //     /*cCategory*/, nStepLog/*cStep  */, /*cMsgId*/ STRZERO(nStepLog,4) , "Query", /*nMensure*/, /*nElapseTime*/,aMessage /*aMessage*/)
    //conout(cSql)
    dbUseArea(.T.,"TOPCONN",TcGenQry(,,cSql),cAliasQry,.F.,.F.)

    oDados["items"]   := {}
    oDados["columns"] := montaColun(lExpResult)
    oDados["headers"] := {}
    oDados["tags"] := {}
    oDados["canExportCSV"] := .T.


    If nPagina > 1
        nStart := ( (nPagina-1) * nTamPagina )
        If nStart > 0
            (cAliasQry)->(DbSkip(nStart))
        EndIf
    EndIf

    nPos := 0
    While (cAliasQry)->(!Eof())
        aAdd(oDados["items"], JsonObject():New())
        nPos++


        cNMCli :=alltrim(posicione("SA1",1, xfilial("SA1")+ (cAliasQry)->CLIENTE+(cAliasQry)->LOJA,"A1_NOME"))
        cNMCli := (cAliasQry)->CLIENTE+"-"+(cAliasQry)->LOJA+cNMCli
        // nStepLog++
        // aMessage := {}
        // aAdd(aMessage, {"Cliente", cNMCli})
        // FWLogMsg("DEBUG", /*cTransactionId*/, "DlpFaturamento - BuscaDetalhes", ;
        //     /*cCategory*/, nStepLog/*cStep  */, /*cMsgId*/ STRZERO(nStepLog,4) , "items", /*nMensure*/, /*nElapseTime*/,aMessage /*aMessage*/)


        oDados["items"][nPos]["F2_FILIAL"]  := (cAliasQry)->FILIAL
        oDados["items"][nPos]["CLIENTE"]    := cNMCli
        oDados["items"][nPos]["DTDE"]       := PCPMonitorUtils():FormataData(dToS(cEmisDe), 5)
        oDados["items"][nPos]["DT_ATE"]      := PCPMonitorUtils():FormataData(dToS(cEmisAte), 5)
        oDados["items"][nPos]["QTD_NF"]     :=(cAliasQry)->QTDNF
        oDados["items"][nPos]["QTD_ITENS"]  :=(cAliasQry)->QTDPRDVEN
        oDados["items"][nPos]["QTD_VEND"]   :=(cAliasQry)->D2_QUANT
        oDados["items"][nPos]["VALFAT"]     := (cAliasQry)->LIQUIVENDA
        oDados["items"][nPos]["VALDEV"]     := (cAliasQry)->LIQDEV *-1
        oDados["items"][nPos]["VALLIQ"]     := (cAliasQry)->LIQUIVENDA  + ((cAliasQry)->LIQDEV *-1)


        (cAliasQry)->(dbSkip())

        If !lExpResult .And. nPos >= nTamPagina
            Exit
        EndIf
    End
    oDados["hasNext"] := (cAliasQry)->(!Eof())
    (cAliasQry)->(dbCloseArea())
    cJsonDados := oDados:toJson()
    FreeObj(oDados)
Return cJsonDados

/*/{Protheus.doc} montaColun
Realiza a criação de objeto Json que define as colunas utilizadas na grid de detalhamento do monitor
@type Static Function
@author
@since
@version
@param  lExpResult, logico, Indica se trata todas as colunas como visible
@return aColumns, array objetos, Contém as definições das colunas da grid do monitor
/*/
Static Function montaColun(lExpResult)
    Local aColunas   := {}
    Local aLabels    := {}
    Local nIndice    := 0
    Local nIndLabels := 0


    cCPOX3:="F2_FILIAL"
    cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
    PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,cCPOX3,cTitX3,"string",.T.)
    //cCPOX3:="F2_EMISSAO"
    //cTitX3 := ALLTRIM( GETSX3CACHE(cCPOX3,"X3_TITULO"))
    PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,'CLIENTE','Cliente',"string",.T.)
    PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,'DTDE','Emissao de',"date",.T.)
    PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,'DT_ATE','Emissao Ate',"date",.T.)

    PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"QTD_NF"/*cCPOX3*/,'Total Notas'/*cTitX3*/,"number",.T.)
    PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"QTD_ITENS"/*cCPOX3*/,'Total Itens'/*cTitX3*/,"number",.T.)
    PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"QTD_VEND"/*cCPOX3*/,'Qtd Vendida'/*cTitX3*/,"number",.T.)
    PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"VALFAT"  /*cCPOX3*/,'Valor Venda'/*cTitX3*/,"number",.T.)
    PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"VALDEV"  /*cCPOX3*/,'Valor Devolucao R$'/*cTitX3*/,"number",.T.)
    PCPMonitorUtils():AdicionaColunaTabela(aColunas,@nIndice,"VALLIQ"/*cCPOX3*/,'Valor Total R$'/*cTitX3*/,"number",.T.)


Return aColunas

/*/{Protheus.doc} ValidaPropriedades
Valida os dados informados nas propriedades do Monitor
@type Method
@author
@since
@version
@param  oFiltros, objeto json, Objeto json com os filtros para a consulta dos dados
@return aRetorno, array      , [1] logico - indica se os dados são válidos [2] caracter - mensagem de erro
/*/
Method ValidaPropriedades(oFiltros) Class DlpFaturamento
    Local aRetorno := {.T.,""}

    //PCPMonitorUtils():ValidaPropriedadeFilial(oFiltros["01_EMPRESA"],aRetorno)
    //PCPMonitorUtils():ValidaPropriedadeFilial(oFiltros["02_FILIAL"],aRetorno)

    //If aRetorno[1] .And. oFiltros["TIPOPERIODO"] == "X"
    //    If !oFiltros:HasProperty("PERIODO") .Or. oFiltros["PERIODO"] == Nil .Or. Empty(oFiltros["PERIODO"])
    //        aRetorno[1] := .F.
    //        aRetorno[2] := "Deve ser informada a quantidade de dias para o período personalizado."
    //    EndIf
    //EndIf
Return aRetorno
