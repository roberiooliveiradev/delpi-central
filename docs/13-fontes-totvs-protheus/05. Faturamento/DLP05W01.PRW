#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#Include 'FWMVCDef.ch'

/*/{Protheus.doc} DelpiFaturamento
    API REST Delpi — Faturamento (geração de Documento de Saída via MATA460).

    Rascunho para compilação no TST01 — padrão idêntico ao DLP04I01
    (delpiproduto). Fluxo: recebe JSON -> monta arrays ExecAuto ->
    MSExecAuto(MATA460) -> RETOBJ 200/400.

    CONTRATO DO EXECAUTO — validar em homologação (POC no TST01):
    - MATA460 fatura itens de pedidos de venda LIBERADOS (SC9 sem bloqueio
      de crédito/estoque). Pedido não liberado é rejeitado pela rotina.
    - aItens: um sub-array por item a faturar, campos D2_* apontando o
      pedido de origem (D2_PEDIDO/D2_ITEMPV/D2_QUANT). Omitir D2_QUANT
      fatura o saldo do item — confirmar comportamento desejado.
    - aCabec: cabeçalho SF2. F2_DOC/F2_SERIE vazios => rotina numera pela
      série padrão configurada; F2_FORMUL "N" = NF normal.
    - aParam: "perguntas" da tela do MATA460 (MV_PAR01..n). Os índices e
      valores abaixo seguem o padrão documentado; VALIDAR contra o dicionário
      do ambiente antes de produção (perguntas variam por release/customizações).
    - Sem aglutinação entre pedidos diferentes nesta v1 (1 NF por chamada).

    @type Class
    @author Devin (rascunho para revisão/compilação)
    @since 18/11/2026
    @version P12
/*/

WSRESTFUL DelpiFaturamento DESCRIPTION "Api REST para Faturamento Delpi" FORMAT "application/json"

    WSMETHOD POST faturar DESCRIPTION 'Fatura itens de pedido de venda (MATA460)' PATH '/v1/faturar' WSSYNTAX '/v1/faturar' TTALK "v1"

END WSRESTFUL


WSMETHOD POST faturar WSRECEIVE WSRESTFUL DelpiFaturamento

Local aArea         := GetArea()
Local lRet          := .T.
Local cErro         := ""
Local cJsonRet      := ""
Local cJSON         := Self:GetContent()
Local oJson         := JsonObject():New()
Local cIdtoken      := "gda"
Local aDados        := {}
Local nY            := 0
Local cErroBlk      := ''
Local aCabec        := {}
Local aItens        := {}
Local aLinha        := {}
Local aParam        := {}
Local aLogAuto      := {}
Local cEol          := chr(10)
Local oException    := ErrorBlock({|e| cErroBlk := e:Description + e:ErrorStack, Break(e) })
Local oDados        := JsonObject():New()
Local oJsonRet      := JsonObject():New()
Local aPedidos      := {}
Local oItem         := Nil

PRIVATE aErro       := {}
PRIVATE lMsErroAuto := .F.
Private lMsHelpAuto := .T.
Private lAutoErrNoFile  := .T.


Self:SetContentType("application/json")
oDados:FromJson(cJSON)

Begin Sequence

    //====================================================================
    // 1) Cabeçalho SF2 — dados da NF
    //====================================================================
    aadd(aCabec, {"F2_CLIENTE", oDados["F2_CLIENTE"], Nil})
    aadd(aCabec, {"F2_LOJA"   , oDados["F2_LOJA"   ], Nil})
    aadd(aCabec, {"F2_FORMUL" , "N"                 , Nil})  // NF normal
    aadd(aCabec, {"F2_DOC"    , oDados["F2_DOC"    ], Nil})  // vazio => numeração da rotina
    aadd(aCabec, {"F2_SERIE"  , oDados["F2_SERIE"  ], Nil})
    aadd(aCabec, {"F2_EMISSAO", STOD(oDados["F2_EMISSAO"]), Nil}) // "AAAAMMDD"

    //====================================================================
    // 2) Itens — cada entrada aponta pedido+item de origem (SC9 liberado)
    //    Entrada JSON esperada: "itens":[{"pedido":"000123","itempv":"01","quant":5}, ...]
    //====================================================================
    aPedidos := oDados["itens"]

    If Empty(aPedidos)
        lRet  := .F.
        cErro := "JSON sem array 'itens' (pedido/itempv/quant)."
        oJsonRet := RETOBJ(oJsonRet,"400","Erro",cErro,cIdtoken)
        Break()
    EndIf

    For nY := 1 To Len(aPedidos)
        oItem  := aPedidos[nY]
        aLinha := {}
        aadd(aLinha, {"D2_PEDIDO" , oItem["pedido" ], Nil})
        aadd(aLinha, {"D2_ITEMPV" , oItem["itempv" ], Nil})
        aadd(aLinha, {"D2_QUANT"  , Val(oItem["quant"]), Nil})
        aadd(aItens, aLinha)
    Next nY

    //====================================================================
    // 3) Perguntas da rotina (equivalente às respostas da tela do MATA460)
    //    VALIDAR NO TST01 — ajustar ao dicionário do ambiente.
    //====================================================================
    aadd(aParam, {"MV_PAR01", 2})  // Mostra lançamentos contábeis? (2=Não)
    aadd(aParam, {"MV_PAR02", 1})  // Aglutina pedidos?            (1=Sim/2=Não — confirmar)
    aadd(aParam, {"MV_PAR03", 2})  // Aglutina duplicatas?
    aadd(aParam, {"MV_PAR04", STOD(oDados["F2_EMISSAO"])})  // Data emissão
    aadd(aParam, {"MV_PAR05", 1})  // Atualiza pedido de venda?   (1=Sim)
    aadd(aParam, {"MV_PAR06", 1})  // Permite faturar pedidos com saldo de estoque? (regra ambiente)

    //====================================================================
    // 4) ExecAuto — rotina oficial de faturamento
    //====================================================================
    MSExecAuto({|x,y,z| MATA460(x,y,z)}, aItens, aCabec, aParam)

    If lMsErroAuto
        lRet     := .F.
        aLogAuto := GetAutoGrLog()
        For nY := 1 To Len(aLogAuto)
            cErro += aLogAuto[nY] + CRLF
        Next nY
        oJsonRet := RETOBJ(oJsonRet,"400","Erro",cErro,cIdtoken)
    Else
        oJsonRet := RETOBJ(oJsonRet,"200","OK","Nota fiscal gerada com sucesso!",cIdtoken)
    EndIf

    Recover
    ErrorBlock(oException)
    lRet := .F.
    oJsonRet := RETOBJ(oJsonRet,"400","Erro Log",cErroBlk,cIdtoken)
    FreeObj(oJson)

End sequence

cJsonRet := oJsonRet:toJson()

If lRet
    Self:setStatus(200)
Else
    Self:setStatus(400)
EndIf

Self:setResponse(cJsonRet)

FreeObj(oJson)
FreeObj(oJsonRet)
FreeObj(oDados)
RestArea(aArea)

Return .T.
