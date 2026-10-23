#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#Include 'FWMVCDef.ch'




WSRESTFUL DelpiProduto DESCRIPTION "Api REST para Tratativa de produtos" FORMAT "application/json"


    // WSDATA cSalesOrder AS STRING OPTIONAL
    //WSDATA cSearchKey AS STRING OPTIONAL

    //  WSMETHOD GET  salesOrder     DESCRIPTION 'Consulta pedidos de venda'    WSSYNTAX '/api/v3/salesorder' PRODUCES APPLICATION_JSON
    WSMETHOD POST incProd  DESCRIPTION 'Insere Produto'  PATH '/v1/IncProduto/incluir'  WSSYNTAX '/v1/IncProduto/incluir'  TTALK "v1"
    WSMETHOD PUT incProd  DESCRIPTION 'Altera Produto'  PATH '/v1/IncProduto/alterar'  WSSYNTAX '/v1/IncProduto/alterar'  TTALK "v1"
    //PRODUCES APPLICATION_JSON
    //WSMETHOD POST   APONTAPRODUCAO 	 DESCRIPTION 'Apontar Producao' PATH '/v1/apontaproducao/'  TTALK "v1"  WSSYNTAX '/v1/apontaproducao/'
    //  WSMETHOD PUT  editSalesOrder DESCRIPTION 'Edita pedidos de venda'       WSSYNTAX '/api/v3/salesorder' PRODUCES APPLICATION_JSON
END WSRESTFUL




/*/{Protheus.doc} User Function incSalesOrder
    (Verbo POST para adição de pedidos de venda)
    @type  Function
    @author Leandro Lemos
    @since 20/09/2020
    @version P12
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)

/*/

WSMETHOD POST incProd WSRECEIVE WSRESTFUL DelpiProduto



Local aArea         := GetArea()
Local lRet		    := .T.
Local cErro         := ""
Local cJsonRet      := ""
Local cJSON         := Self:GetContent()
Local oJson         := JsonObject():New()
//Local oLog          := ALFXLOG():New()
Local cIdtoken      := "gda" //oLog:idtoken
Local cCodVend      := ''
Local cMun      	:= ''
Local aDados 	    := {}
Local n1		    := 0
Local nY		    := 0
Local cErroBlk      := ''
Local cCodFor       := ''
Local cCodLoj       := ''
Local aSB1 := {}
Local cEol := chr(10)
Local lOk := .t. //Gabriel Para posteriores Tratativas
Local oException    := ErrorBlock({|e| cErroBlk := + e:Description + e:ErrorStack, Break(e) })
Local oDados	 	:= JsonObject():New()
Local aErro 	 	:= {}
Local oJsonRet 	:= JsonObject():New()

PRIVATE aErro		:= {}
PRIVATE lMsErroAuto := .F.
Private lMsHelpAuto	:= .T.
Private lAutoErrNoFile  := .T.


//Self:SetContentType("application/json")
//cJSON := fJsontext(cJSON)
// oDados:FromJson(cJSON)
Self:SetContentType("application/json")
oDados:FromJson(cJSON)
Begin Sequence

    /* exemplo de erro
    IF !AddForn(oDados["a3_cgc"], oDados["a3_nome"], oDados["a3_dddtel"], oDados["a3_tel"], oDados["a3_email"], oDados["a2_end"], oDados["a2_bairro"], oDados["a2_cep"], oDados["a2_est"], oDados["a2_cod_mun"], oDados["a2_pais"], oDados["a2_codpais"], oDados["a2_inscr"], oDados["a2_conta"], oDados["a2_mun"], @cCodFor, @cCodLoj)
        lRet := .F.
        cErro := "Erro ao adicionar Fornecedor: "+cCodVend+" "
        oJsonRet := RETOBJ(oJsonRet,"400","Erro",cErro,cIdtoken)
        oLog:GRAVALOG("C006",cIdtoken,"Erro - Fornecedor/Vendedor",cErro,cvaltochar(cJson),oJsonRet:toJson(),"2")
    ENDIF
    */
    cFlNmLog := cEmpAnt+"_"+ALLTRIM(oJson:GetJSonObject( "B1_COD"	  ))+;
        "_"+DTOS(DATE())+"_"+STRTRAN(TIME(),":","")

    aadd(aSB1,{"B1_GRUPO"	,  oDados["B1_GRUPO"  ]     ,Nil})
    aadd(aSB1,{"B1_COD"		,  oDados["B1_COD"	  ]     ,Nil})
    aadd(aSB1,{"B1_DESC"	,  oDados["B1_DESC"	  ]     ,Nil})
    aadd(aSB1,{"B1_REFEREN"	,  oDados["B1_REFEREN" ]    ,Nil})
    aadd(aSB1,{"B1_REFCANT"	,  oDados["B1_REFCANT" ]    ,Nil})
    aadd(aSB1,{"B1_CODDES"	,  oDados["B1_CODDES"  ]    ,Nil})
    aadd(aSB1,{"B1_TIPO"	,  oDados["B1_TIPO"	  ]     ,Nil})
    aadd(aSB1,{"B1_YHOHS"	,  oDados["B1_YHOHS"	  ] ,Nil})
    aadd(aSB1,{"B1_POSIPI"	,  oDados["B1_POSIPI"  ]    ,Nil})
    aadd(aSB1,{"B1_LOCPAD"	,  oDados["B1_LOCPAD"  ]    ,Nil})
    aadd(aSB1,{"B1_UM"		,  oDados["B1_UM"	  ]     ,Nil})
    aadd(aSB1,{"B1_SEGUM"	,  oDados["B1_SEGUM"	  ] ,Nil})
    aadd(aSB1,{"B1_TE"		,  oDados["B1_TE"	  ]     ,Nil})
    aadd(aSB1,{"B1_TS"		,  oDados["B1_TS"	  ]     ,Nil})
    aadd(aSB1,{"B1_PICMRET"	, VAL( oDados["B1_PICMRET" ]  )  ,Nil})
    aadd(aSB1,{"B1_CONV"	,  VAL(oDados["B1_CONV"	  ]  )   ,Nil})
    aadd(aSB1,{"B1_TIPCONV"	,  oDados["B1_TIPCONV" ]    ,Nil})
    aadd(aSB1,{"B1_TPMAT"	,  oDados["B1_TPMAT"	  ] ,Nil})
    aadd(aSB1,{"B1_ESPECIE"	,  oDados["B1_ESPECIE" ]    ,Nil})
    aadd(aSB1,{"B1_EX_NCM"	,  oDados["B1_EX_NCM"  ]    ,Nil})
    aadd(aSB1,{"B1_EX_NBM"	,  oDados["B1_EX_NBM"  ]    ,Nil})
    aadd(aSB1,{"B1_ORIGEM"	,  oDados["B1_ORIGEM"  ]    ,Nil})


    cMsgLog :=PADR("CAMPO",10)+" | CONTEUDO" + cEol


    //FwLogMsg("INFO", /*cTransactionId*/, "REST", FunName(), "", "01", "JSON successfully parsed to Object", 0, (nStart - Seconds()), {}) // nStart é declarada no inicio da função
    FWLogMsg("INFO", /*cTransactionId*/, "MeuGrupo - GABRIEL", /*cCategory*/, /*cStep*/, /*cMsgId*/, "Minha primeira mensagem", /*nMensure*/, /*nElapseTime*/, /*aMessage*/)

    //FwLogMsg("INFO", /*cTransactionId*/, "REST", FunName(), "", "01", "JSON successfully parsed to Object", 0, (nStart - Seconds()), {}) // nStart é declarada no inicio da função

    conout("DLP04I01 - CEMPANT "+ CEMPANT)
    //  fGravaLog(cFlNmLog+"_01.txt",cMsgLog)
    MSExecAuto({|x,y| Mata010(x,y)},aSB1,3)
    // lMsErroAuto := .T.

    If lMsErroAuto
        lRet := .F.
        aLogAuto    := GetAutoGrLog()

        For nY := 1 To Len(aLogAuto)
            cErro += aLogAuto[nY] + CRLF
        Next nY

        oJsonRet := RETOBJ(oJsonRet,"400","Erro",cErro,cIdtoken )
        //     oLog:GRAVALOG("C006",cIdtoken,cErro,oJsonRet:toJson(),cvaltochar(cJson),cvaltochar(cJSONRet),"2")
        //     RollbackSxE()
    Else
        oJsonRet := RETOBJ(oJsonRet,"200","OK","Registro integrado com sucesso!",cIdtoken)
        //   oLog:GRAVALOG("C006",cIdtoken,"","",cvaltochar(cJson),oJsonRet:toJson(),"1")
        // ConfirmSx8()
    EndIf


    Recover
    ErrorBlock(oException)
    lRet := .F.
    oJsonRet := RETOBJ(oJsonRet,"400","Erro Log",cErroBlk,cIdtoken)
    //    oLog:GRAVALOG("C006",cIdtoken,"Erro Log",cErroBlk,cvaltochar(cJson),oJsonRet:toJson(),"2")
    FreeObj(oJson)
End sequence

cReturn	:= oJsonRet:toJson()

If lRet
    self:setStatus(200)
Else
    self:setStatus(400)
EndIf

self:setResponse(cReturn)

FreeObj(oJson)
//FreeObj(oLog)
FreeObj(oJsonRet)
FreeObj(oDados)
RestArea(aArea)

Return .T.


WSMETHOD PUT incProd WSRECEIVE WSRESTFUL DelpiProduto



Local aArea         := GetArea()
Local lRet		    := .T.
Local cErro         := ""
Local cJsonRet      := ""
Local cJSON         := Self:GetContent()
Local oJson         := JsonObject():New()
//Local oLog          := ALFXLOG():New()
Local cIdtoken      := "gda" //oLog:idtoken
Local cCodVend      := ''
Local cMun      	:= ''
Local aDados 	    := {}
Local n1		    := 0
Local nY		    := 0
Local cErroBlk      := ''
Local cCodFor       := ''
Local cCodLoj       := ''
Local aSB1 := {}
Local cEol := chr(10)
Local lOk := .t. //Gabriel Para posteriores Tratativas
Local oException    := ErrorBlock({|e| cErroBlk := + e:Description + e:ErrorStack, Break(e) })
Local oDados	 	:= JsonObject():New()
Local aErro 	 	:= {}
Local oJsonRet 	:= JsonObject():New()

PRIVATE aErro		:= {}
PRIVATE lMsErroAuto := .F.
Private lMsHelpAuto	:= .T.
Private lAutoErrNoFile  := .T.


//Self:SetContentType("application/json")
//cJSON := fJsontext(cJSON)
// oDados:FromJson(cJSON)
Self:SetContentType("application/json")
oDados:FromJson(cJSON)
Begin Sequence

    /* exemplo de erro
    IF !AddForn(oDados["a3_cgc"], oDados["a3_nome"], oDados["a3_dddtel"], oDados["a3_tel"], oDados["a3_email"], oDados["a2_end"], oDados["a2_bairro"], oDados["a2_cep"], oDados["a2_est"], oDados["a2_cod_mun"], oDados["a2_pais"], oDados["a2_codpais"], oDados["a2_inscr"], oDados["a2_conta"], oDados["a2_mun"], @cCodFor, @cCodLoj)
        lRet := .F.
        cErro := "Erro ao adicionar Fornecedor: "+cCodVend+" "
        oJsonRet := RETOBJ(oJsonRet,"400","Erro",cErro,cIdtoken)
        oLog:GRAVALOG("C006",cIdtoken,"Erro - Fornecedor/Vendedor",cErro,cvaltochar(cJson),oJsonRet:toJson(),"2")
    ENDIF
    */
    cFlNmLog := cEmpAnt+"_"+ALLTRIM(oJson:GetJSonObject( "B1_COD"	  ))+;
        "_"+DTOS(DATE())+"_"+STRTRAN(TIME(),":","")

    aadd(aSB1,{"B1_GRUPO"	,  oDados["B1_GRUPO"  ]     ,Nil})
    aadd(aSB1,{"B1_COD"		,  oDados["B1_COD"	  ]     ,Nil})
    aadd(aSB1,{"B1_DESC"	,  oDados["B1_DESC"	  ]     ,Nil})
    aadd(aSB1,{"B1_REFEREN"	,  oDados["B1_REFEREN" ]    ,Nil})
    aadd(aSB1,{"B1_REFCANT"	,  oDados["B1_REFCANT" ]    ,Nil})
    aadd(aSB1,{"B1_CODDES"	,  oDados["B1_CODDES"  ]    ,Nil})
    aadd(aSB1,{"B1_TIPO"	,  oDados["B1_TIPO"	   ]     ,Nil})
    aadd(aSB1,{"B1_YHOHS"	,  oDados["B1_YHOHS"   ] ,Nil})
    aadd(aSB1,{"B1_POSIPI"	,  oDados["B1_POSIPI"  ]    ,Nil})
    aadd(aSB1,{"B1_LOCPAD"	,  oDados["B1_LOCPAD"  ]    ,Nil})
    aadd(aSB1,{"B1_UM"		,  oDados["B1_UM"	  ]     ,Nil})
    aadd(aSB1,{"B1_SEGUM"	,  oDados["B1_SEGUM"  ] ,Nil})
    aadd(aSB1,{"B1_TE"		,  oDados["B1_TE"	  ]     ,Nil})
    aadd(aSB1,{"B1_TS"		,  oDados["B1_TS"	  ]     ,Nil})
    aadd(aSB1,{"B1_PICMRET"	, VAL( oDados["B1_PICMRET" ]  )  ,Nil})
    aadd(aSB1,{"B1_CONV"	,  VAL(oDados["B1_CONV"	  ]  )   ,Nil})
    aadd(aSB1,{"B1_TIPCONV"	,  oDados["B1_TIPCONV" ]    ,Nil})
    aadd(aSB1,{"B1_TPMAT"	,  oDados["B1_TPMAT"	  ] ,Nil})
    aadd(aSB1,{"B1_ESPECIE"	,  oDados["B1_ESPECIE" ]    ,Nil})
    aadd(aSB1,{"B1_EX_NCM"	,  oDados["B1_EX_NCM"  ]    ,Nil})
    aadd(aSB1,{"B1_EX_NBM"	,  oDados["B1_EX_NBM"  ]    ,Nil})
    aadd(aSB1,{"B1_ORIGEM"	,  oDados["B1_ORIGEM"  ]    ,Nil})


    cMsgLog :=PADR("CAMPO",10)+" | CONTEUDO" + cEol


    //FwLogMsg("INFO", /*cTransactionId*/, "REST", FunName(), "", "01", "JSON successfully parsed to Object", 0, (nStart - Seconds()), {}) // nStart é declarada no inicio da função
    FWLogMsg("INFO", /*cTransactionId*/, "MeuGrupo - GABRIEL", /*cCategory*/, /*cStep*/, /*cMsgId*/, "Minha primeira mensagem", /*nMensure*/, /*nElapseTime*/, /*aMessage*/)

    //FwLogMsg("INFO", /*cTransactionId*/, "REST", FunName(), "", "01", "JSON successfully parsed to Object", 0, (nStart - Seconds()), {}) // nStart é declarada no inicio da função

    conout("DLP04I01 - CEMPANT "+ CEMPANT)
    //  fGravaLog(cFlNmLog+"_01.txt",cMsgLog)
    MSExecAuto({|x,y| Mata010(x,y)},aSB1,4)
    // lMsErroAuto := .T.

    If lMsErroAuto
        lRet := .F.
        aLogAuto    := GetAutoGrLog()

        For nY := 1 To Len(aLogAuto)
            cErro += aLogAuto[nY] + CRLF
        Next nY

        oJsonRet := RETOBJ(oJsonRet,"400","Erro",cErro,cIdtoken )
        //     oLog:GRAVALOG("C006",cIdtoken,cErro,oJsonRet:toJson(),cvaltochar(cJson),cvaltochar(cJSONRet),"2")
        //     RollbackSxE()
    Else
        oJsonRet := RETOBJ(oJsonRet,"200","OK","Registro integrado com sucesso!",cIdtoken)
        //   oLog:GRAVALOG("C006",cIdtoken,"","",cvaltochar(cJson),oJsonRet:toJson(),"1")
        // ConfirmSx8()
    EndIf


    Recover
    ErrorBlock(oException)
    lRet := .F.
    oJsonRet := RETOBJ(oJsonRet,"400","Erro Log",cErroBlk,cIdtoken)
    //    oLog:GRAVALOG("C006",cIdtoken,"Erro Log",cErroBlk,cvaltochar(cJson),oJsonRet:toJson(),"2")
    FreeObj(oJson)
End sequence

cReturn	:= oJsonRet:toJson()

If lRet
    self:setStatus(200)
Else
    self:setStatus(400)
EndIf

self:setResponse(cReturn)

FreeObj(oJson)
//FreeObj(oLog)
FreeObj(oJsonRet)
FreeObj(oDados)
RestArea(aArea)

Return .T.
static Function fJsontext(cJson)

    Local oJsonContent := JsonObject():new()
    Local aNome        := {}
    Local nCount       := 0

    oJsonContent:FromJson(cJson)
    aNome	:= oJsonContent:getnames()

    For nCount := 1 to Len(aNome)
        cJson  := StrTran( cJson, aNome[nCount], LOWER(aNome[nCount]) )
    Next nCount

    FreeObj(oJsonContent)

Return cJson

//-------------------------------------------------------------------
/*/{Protheus.doc} ALF43I04
	Método para padronizar retorno da API - Alfa
	@version ${12.1.27}
	@author  Rodrigues.Lucas
	@Since   "17/08/2021"
/*/
//-------------------------------------------------------------------
Static Function RETOBJ(oObj,cCode,cMsg,cDetMsg,cIdToken )
    Default cCode   := ""
    Default cMsg    := ""
    Default cDetMsg := ""
    Default cDetMsg := ""

    oObj['code']            := cCode
    oObj['message']         := FwCutOff(cMsg,.T.)
    oObj['detailedMessage'] := FwCutOff(cDetMsg,.T.)
    oObj['id']              := cIdToken

Return oObj





//função para gravar o Log
static function fGravaLog(cNmFile,cLog)
    lOCAL cPath := "F:\SISTEMAS\Totvs\Totvs_Data_12\"
    Local oFile := FWFileWriter():new(cPath+cNmFile)
    conout("DLP04I01 fGravaLog - cNmFile "+ cNmFile)
    //--------------- Se o arquivo já existe, apaga -------------------
    If oFile:Exists()
        conout("DLP04I01 fGravaLog - Exists")
        oFile:Erase()
    EndIf

    //-------------- Cria o arquivo --------------
    If (oFile:Create())
        conout("DLP04I01 fGravaLog - Create")
        //-------------- Se criou com sucesso, escreve ------------------------------
        oFile:Write("Teste de escrita!")

        //-------------- Fecha o arquivo -----------
        oFile:Close()
    ELSE
        conout("DLP04I01 fGravaLog - NAO CRIOU")
    Endif


Return
