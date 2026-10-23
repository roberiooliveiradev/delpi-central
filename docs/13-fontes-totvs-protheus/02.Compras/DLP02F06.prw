#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"

/*
01  - Desenvolver caixa de perguntas com base no parambox
    - DA1 - Unica
    - Produto De/Ate
    - ID Calculo
    - Atualiza Tabela de Venda Sim/Nao
02  Desenvolver query para listar os produtos
03  Desenvolver Rotina para chamar o MVC
*/


user function DLP02F06()

    /*/{Protheus.doc} fParam

    Responsavel por carregar as perguntas  de processamento da formação de preco

    /*/

    /*
    aAdd(aPergs, {1, "Produto De",  cProdDe,  "", ".T.", "SB1", ".T.", 80,  .F.})
    aAdd(aPergs, {1, "Produto Até", cProdAt,  "", ".T.", "SB1", ".T.", 80,  .T.})
    Exemplo 4- ParamBox com parâmetros do tipo Combo:
    aAdd(aPergs, {2, "Tipo Importação",               nTipo, {"1=Pré Nota",              "2=Classificação em Documento de Entrada"},     122, ".T.", .F.})
    aAdd(aPergs, {2, "Vincula Pedido de Compra",      nVinc, {"1=Sim (Automaticamente)", "2=Não"},                                       090, ".T.", .F.})
    aAdd(aPergs, {1, "Qtde",  nQuant,  "@E 9,999",     "Positivo()", "", ".T.", 80,  .F.})
    aAdd(aPergs, {1, "Valor", nValor,  "@E 99,999.99", "Positivo()", "", ".T.", 80,  .F.})

Local nVinc    := 1

aAdd(aPergs, {2, "Tipo Importação",               nTipo, {"1=Pré Nota",              "2=Classificação em Documento de Entrada"},     122, ".T.", .F.})
aAdd(aPergs, {2, "Vincula Pedido de Compra",      nVinc, {"1=Sim (Automaticamente)", "2=Não"},                                       090, ".T.", .F.})


    */
    Local aPergs   := {}
    Local aRetPro   := {}
    Local aMvPar   := {}
    Local aRet     := {}
    Local cTabVen  := space(getsx3cache("DA0_CODTAB","X3_TAMANHO" ))
    Local cProdDe  := space(getsx3cache("B1_COD" ,"X3_TAMANHO" ))
    Local cProdAte := space(getsx3cache("B1_COD" ,"X3_TAMANHO" ))
    Local cIDSZ7   := space(getsx3cache("Z7_ID" ,"X3_TAMANHO"  ))
    Local cAtual   := "N"
    Local cVldPrc   := "N"
    Local nMv      := 0
    Local aArea    := getarea()
    Local aTam     := {20,60,60,60,60}
    Local n1 := 0
    Private aRetBox     := {}



    /*VARIAVEIS PRIVATE LEGADO*/

    Private aFiles    :={}
    Private cEol      := chr(10)
    PRIVATE lLibField := .f.
    PRIVATE lRetCx    := .f.
    Private cBox1     := "1PRD01"
    Private cBox2     := "2OPE01"
    Private  cBox3    := "3IMP01"
    Private nTmIt     := getsx3cache("Z9_ITEM","X3_TAMANHO")
    Private nTotMP    := 0 // Variavel que totaliza a Materia Prima
    Private nTotMOD   := 0 // Variavel que totaliza a Mao de Obra
    Private nTotBen   := 0 // Variavel que totaliza a Beneficiamento
    Private nTotGG    := 0 // Variavel que totaliza Gastos Gerais
    Private nQtdBas   := 1 // Variavel Quantidade Basica
    Private nTotUnit  := 0
    Private NTOTESTR  := 0
    Private LucroOper := 0
    Private nPVOper   := 0
    Private nVlFre    := 0
    Private nCoefOper := 0
    Private nCoefImp  := 0
    Private lRecal    := .f.
    Private cTabPV    := space(3)
    //Variaveis da aba impostos
    Private nICMS    :=0  // ICMS
    Private nPisCof  :=0  // PIS E COFINS
    Private nComiss  :=0  // COMISSÃO
    Private nISS     :=0  // ISS
    Private nCoef    :=0  // COEFICIENTE
    Private nPVVenda :=0  // PV VENDA
    Private nIRCSLL  :=0  // IR E CSLL
    Private nCusPrd  :=0 // Custo produto
    Private lCanAlt := .F.
    Private lVldCpos := .f.
    Private aPrdQtBas := {}
    Private aCusLiq := {0,0,0} //icms - pis cof - frete
    Private nQtdEst := 0
    /****************************/
    /****************************/
    // Private lBrowse := .T.
    Private aRotina		:= MenuDef()
    Private aLogProc := {} // ID |CODIGO PRODUTO | erro
    Private lAuto := .t.
    Private lVldPrcVd := .f.

    if RetCodUsr() == '000000'
        cTabVen := "160"
        cProdDe  := padr("",getsx3cache("B1_COD" ,"X3_TAMANHO" ))
        cProdAte := padr("TERCEIROS",getsx3cache("B1_COD" ,"X3_TAMANHO" ))
        cIDSZ7 := "000002"
        cAtual := "S"
    endif

    /*Armazena o conteudo do MV_PARXX*/
    For nMv := 1 To 40
        aAdd( aMvPar, &( "MV_PAR" + StrZero( nMv, 2, 0 ) ) )
    Next nMv

    conout("gabriel")

    //Box de Perguntas
    aAdd(aPergs, {1, "Tabela de Venda"     ,  cTabVen  ,  getsx3cache("DA0_CODTAB","X3_PICTURE" ),     '(ExistCpo("DA0") .AND. U_D02F6TAB('+cTabVen+') )', "DA0", ".T.",aTam[1] ,  .F.})
    aAdd(aPergs, {1, "Produto De"          ,  cProdDe  ,  getsx3cache("B1_COD","X3_PICTURE" ),     'Vazio() .or. ExistCpo("SB1")', "SB1", ".T.", aTam[2],  .F.})
    aAdd(aPergs, {1, "Produto Ate"         ,  cProdAte ,  getsx3cache("B1_COD","X3_PICTURE" ),     'ExistCpo("SB1")', "SB1", ".T.", aTam[3],  .T.})
    aAdd(aPergs, {1, "Planilha Calculo"    ,  cIDSZ7   , "",      'ExistCpo("SZ7")', "SZ7SX1", ".T.", aTam[4],  .F.})
    aAdd(aPergs, {2, "Valida Preco Venda",  cAtual   ,  {"S=Sim","N=Não"},     aTam[5], ".T.", .T.})
    // aAdd(aPergs, {2, "Valida Preco",  cVldPrc   ,  {"S=Sim","N=Não"},     aTam[5], ".T.", .T.})

    aRetBox := ARRAY(LEN(aPergs))

    If ParamBox(aPergs, "Informe os parâmetros",@aRetBox)

        //GUARDA AS OPCOES ESCOLHIDAS
        cTabVen  := MV_PAR01
        cProdDe  := MV_PAR02
        cProdAte := MV_PAR03
        cIDSZ7   := MV_PAR04
        cAtual   := MV_PAR05

        if cAtual == 'S'
            lVldPrcVd := .t.
        endif
        //   cVldPrc   := MV_PAR05

        For nMv := 1 To Len( aMvPar )
            &( "MV_PAR" + StrZero( nMv, 2, 0 ) ) := aMvPar[ nMv ]
        Next nMv

        FWMsgRun( ,{||  fGetProd(cTabVen,cProdDe,cProdAte,cIDSZ7,cAtual,@aRetPro)}," Buscando os Produtos para calculo...")
        aLogProc :={}
        For n1 := 1 to Len(aRetPro)

            lAuto := .t.
            //nOper    :=  iif(empty(aRetPro[n1][3]), 3,4) //// 3 - Inclusao, 4 - Alteração, 5 - Exclusão
            nOper    :=  3 //iif(empty(aRetPro[n1][3]), 3,4) //// 3 - Inclusao, 4 - Alteração, 5 - Exclusão
            cPrdProc :=  aRetPro[n1][1]
            //   cIDSZ7   :=  iif(!empty(aRetPro[n1][2]),aRetPro[n1][2],cIDSZ7)

            FWMsgRun( ,{|| fProc(cTabVen,nOper,cPrdProc,cIDSZ7,aRetPro[n1][3])}," Processando Produto "+cPrdProc+"...")

        Next n1


    ELSE
        FWAlertError("Cancelado pelo Usuario", "Formação Preco")
        For nMv := 1 To Len( aMvPar )
            &( "MV_PAR" + StrZero( nMv, 2, 0 ) ) := aMvPar[ nMv ]
        Next nMv
    ENDIF
    //EEcView(cMsg, "Itens Não Processados")
    if len(aLogProc) > 0
        cMsg := ""
        cEol := chr(10)
        For n1 := 1 to Len(aLogProc)
            cMsg +=trim( aLogProc[n1][1])+" | "+trim( aLogProc[n1][2])+" | "+trim( aLogProc[n1][3]) + cEol
        Next n1
        EEcView(cMsg, "Itens Não Processados")
    endif

    /*Retorna o conteudo do MV_PARXX*/


    RestArea(aArea)
Return
/*/{Protheus.doc} fGetProd
REtorna os Produtos elegiveis se é necessario incluir ou alterar
@author Gabriel
@since 09/12/2021
@param cTabVen,cProdDe,cProdAte,cIDSZ7,cAtual
@return return_var, return_type, return_description
/*/
static Function fGetProd(cTabVen,cProdDe,cProdAte,cIDSZ7,cAtual,aRetPro)
    Local aRet := {}
    Local cEol := chr(10)

    /*
" + retsqlname("") + " SB1 (NOLOCK) " + cEol
    */
    cSql := " SELECT DISTINCT SBZ.BZ_FILIAL, B1_COD, B1_DESC, SBZ.BZ_YIDSZ7, ISNULL('', SPACE(6)) Z8_ID, ISNULL(SZ8.Z8_IDSZ7, SPACE(6)) Z8_IDSZ7 " + cEol
    cSql += "   FROM dbo." + retsqlname("SB1") + " SB1  (NOLOCK) "      + cEol
    cSql += "       JOIN dbo." + retsqlname("SBZ") + " SBZ (NOLOCK) "   + cEol
    cSql += "             ON  SBZ.D_E_L_E_T_  = '' "                    + cEol
    cSql += "             AND SBZ.BZ_FILIAL   = "+VALTOSQL(XFILIAL("SBZ"))                + cEol
    cSql += "             AND SB1.B1_COD      = SBZ.BZ_COD  "           + cEol
    cSql += "       JOIN dbo." + retsqlname("DA1") + " DA1 (NOLOCK) "   + cEol
    cSql += "             ON  DA1.D_E_L_E_T_  = '' AND DA1_ATIVO = '1' "           + cEol
    cSql += "             AND DA1.DA1_FILIAL   = "+VALTOSQL(XFILIAL("DA1"))        + cEol
    cSql += "             AND SB1.B1_COD      = DA1.DA1_CODPRO  "           + cEol
    cSql += "             AND DA1.DA1_CODTAB   = "+VALTOSQL(cTabVen)                + cEol
    cSql += "       LEFT JOIN " + retsqlname("SZ8") + " SZ8 (NOLOCK) "  + cEol
    cSql += "             ON  SZ8.D_E_L_E_T_ = ''"                      + cEol
    cSql += "             AND SZ8.Z8_FILIAL  = "+VALTOSQL(XFILIAL("SZ8"))                      + cEol
    cSql += "             AND SB1.B1_COD     = SZ8.Z8_COD"              + cEol
    cSql += " WHERE SB1.D_E_L_E_T_ = ''"   + cEol
    cSql += "       AND SB1.B1_COD BETWEEN  " + VALTOSQL(cProdDe) + "  AND  " + VALTOSQL(cProdAte) + "  "  + cEol
    cSql += "AND SB1.B1_MSBLQL != '1'"  + cEol
    cSql += "ORDER BY 1,2 "

    If Select('TMPSB1') <> 0
        TMPSB1->(dbCloseArea())
    Endif

    CONOUT("TESTE")
    TCQuery cSql Alias TMPSB1 New
    While TMPSB1->(!eof())

        aTmp :={}

        aadd(aTmp,TMPSB1->B1_COD       ) /*01 - PRODUTO*/
        aadd(aTmp,TMPSB1->BZ_YIDSZ7    ) /*02 - BZ_YIDSZ7*/
        aadd(aTmp,TMPSB1->Z8_ID        ) /*03 - Z8_ID*/

        aadd(aRet,aTmp)
        TMPSB1->(dbskip())

    Enddo
    aRetPro := aRet
    TMPSB1->(dbCloseArea())
Return

/*USER FUNCTION D02F6SZ7()
    lOCAL lRet := .t.

    conout('stop')

Return lRet*/
//Função para validar a tabela de preco vigente
USER FUNCTION D02F6TAB()

    Local lRet := MaVldTabPrc(MV_PAR01)

    conout("gabriel")

return lRet


Static Function fProc(cTabVen,nOper,cPrdProc,cIDSZ7,cIDSZ8)
    DBSELECTAREA("SZ9")
    SZ9->(dbSetOrder(1))
    if nOPer == 3
        cDesc :=  PADR("INSERT AUTOMATICO",GETSX3CACHE("Z8_DESC","X3_TAMANHO")      )
    ELSE
        cDesc :=  PADR("UPDATE AUTOMATICO",GETSX3CACHE("Z8_DESC","X3_TAMANHO")      )

        DBSELECTAREA("SZ8")
        SZ8->(dbSetOrder(1))
        SZ8->(MsSeek(xFilial("SZ8")+cIDSZ8))


    ENDIF
    conout("stop")
    oModel := FWLoadModel("DLP02F02")
    oModel:SetOperation(nOper)
    oModel:Activate()


    cDesc :=  PADR("GERADO VIA ROTINA AUTOMATICA",GETSX3CACHE("Z8_DESC","X3_TAMANHO")      )
    oMDSZ8Cab := oModel:GetModel("SZ8MASTER")
    oMDSZ901 := oModel:GetModel("SZ9DETAIL01")
    oMDSZ902 := oModel:GetModel("SZ9DETAIL02")
    oMDSZ903 := oModel:GetModel("SZ9DETAIL03")

    CONOUT("STOP")
    // oModel:SetOperation(MODEL_OPERATION_INSERT)
    // oSZ8Cab:Activate()
    // oSZ901:Activate()
    // oSZ902:Activate()
    // oSZ903:Activate()

    IF   oMDSZ8Cab:GetValue("Z8_COD") !=  cPrdProc
        conout("teste")
    ENDIF
    if nOper != 4
        oMDSZ8Cab:SetValue("Z8_IDSZ7"    , cIDSZ7      )
    endif
    oMDSZ8Cab:SetValue("Z8_COD"      , cPrdProc      )
    oMDSZ8Cab:SetValue("Z8_DESC"     ,cDesc )
    oMDSZ8Cab:SetValue("Z8_CDTABVN"  , cTabVen      )

    CONOUT("STOP")
    U_D02fPDados()
    CONOUT("STOP")
    //  Z8_IDSZ7 000002
    //  Z8_COD 90262780
    //  Z8_DSCPRD CHICOTE DE LIGACAO
    //  Z8_CDTABVN 109
    lOk := .T.

    If oModel:VldData()
        If oModel:CommitData()
            lOk := .T.

            //Se não deu certo, altera a variável para false
        Else
            lOk := .F.
        EndIf

        //Se não conseguir validar as informações, altera a variável para false
    Else
        lOk := .F.
    EndIf

    If ! lOk
        //Busca o Erro do Modelo de Dados
        aErro := oModel:GetErrorMessage()

        //Monta o Texto que será mostrado na tela
        cMessage := "Id do formulário de origem:"  + ' [' + cValToChar(aErro[01]) + '], '
        cMessage += "Id do campo de origem: "      + ' [' + cValToChar(aErro[02]) + '], '
        cMessage += "Id do formulário de erro: "   + ' [' + cValToChar(aErro[03]) + '], '
        cMessage += "Id do campo de erro: "        + ' [' + cValToChar(aErro[04]) + '], '
        cMessage += "Id do erro: "                 + ' [' + cValToChar(aErro[05]) + '], '
        cMessage += "Mensagem do erro: "           + ' [' + cValToChar(aErro[06]) + '], '
        cMessage += "Mensagem da solução: "        + ' [' + cValToChar(aErro[07]) + '], '
        cMessage += "Valor atribuído: "            + ' [' + cValToChar(aErro[08]) + '], '
        cMessage += "Valor anterior: "             + ' [' + cValToChar(aErro[09]) + ']'

        //Mostra mensagem de erro
        //   lRet := .F.
        ConOut("Erro: " + cMessage)
        // Else
        //     //  lRet := .T.
        //     ConOut("Produto incluido!")
    EndIf
    //Desativa o modelo de dados
    oModel:DeActivate()
Return

/*//Pegando o modelo de dados, setando a operação de inclusão
oModel := FWLoadModel("MATA010")
oModel:SetOperation(3)
oModel:Activate()

//Pegando o model e setando os campos
oSB1Mod := oModel:GetModel("SB1MASTER")
oSB1Mod:SetValue("B1_COD"    , cCod      )
oSB1Mod:SetValue("B1_DESC"   , cDesc     )
oSB1Mod:SetValue("B1_TIPO"   , cTipo     )
oSB1Mod:SetValue("B1_UM"     , cUM       )
oSB1Mod:SetValue("B1_LOCPAD" , cLocPad   )

//Setando o complemento do produto
oSB5Mod := oModel:GetModel("SB5DETAIL")
If oSB5Mod != Nil
    oSB5Mod:SetValue("B5_CEME"   , cCEME     )
EndIf

//Se conseguir validar as informações
If oModel:VldData()

    //Tenta realizar o Commit
    If oModel:CommitData()
        lOk := .T.

    //Se não deu certo, altera a variável para false
    Else
        lOk := .F.
    EndIf

//Se não conseguir validar as informações, altera a variável para false
Else
    lOk := .F.
EndIf

//Se não deu certo a inclusão, mostra a mensagem de erro
If ! lOk
    //Busca o Erro do Modelo de Dados
    aErro := oModel:GetErrorMessage()

    //Monta o Texto que será mostrado na tela
    cMessage := "Id do formulário de origem:"  + ' [' + cValToChar(aErro[01]) + '], '
    cMessage += "Id do campo de origem: "      + ' [' + cValToChar(aErro[02]) + '], '
    cMessage += "Id do formulário de erro: "   + ' [' + cValToChar(aErro[03]) + '], '
    cMessage += "Id do campo de erro: "        + ' [' + cValToChar(aErro[04]) + '], '
    cMessage += "Id do erro: "                 + ' [' + cValToChar(aErro[05]) + '], '
    cMessage += "Mensagem do erro: "           + ' [' + cValToChar(aErro[06]) + '], '
    cMessage += "Mensagem da solução: "        + ' [' + cValToChar(aErro[07]) + '], '
    cMessage += "Valor atribuído: "            + ' [' + cValToChar(aErro[08]) + '], '
    cMessage += "Valor anterior: "             + ' [' + cValToChar(aErro[09]) + ']'

    //Mostra mensagem de erro
    lRet := .F.
    ConOut("Erro: " + cMessage)
Else
    lRet := .T.
    ConOut("Produto incluido!")
EndIf

//Desativa o modelo de dados
oModel:DeActivate()*/
