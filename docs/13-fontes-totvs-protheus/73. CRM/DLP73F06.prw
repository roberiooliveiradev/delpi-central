#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"

/**Funcao Responsavel pela LMP */



/*/{Protheus.doc} User Function DLP73F06
    (long_description)
    @type  Function
    @author user
    @since 22/08/2022
    @version version
    @param param_name, param_type, param_descr
    @return return_var, return_type, return_description
    @example
    (examples)
    @see (links_or_references)
    0012602 = 90263603 mais ñ está pronto ainda!!
80012601 ñ foi feito ainda!
80011558 = 90263602 esse já foi finalizado!!
Tarefas
01 -SB1 CADASTRO
01.01 - Inserção da SB1
01.02 - Exibição da View


Ponto de Atenção: Travar se tem B1_ORIGEM EM BRANCO
/*/
User Function D73F06A()

    cCodOpor := "80011838       "
    cCodRet  := "90270041       "
    fPutEst(cCodOpor,cCodRet)

RETURN
User Function DLP73F06(lCRM)

    Local oModelOld     := FWMODELACTIVE()
    Local oViewOld      := FwViewActive()
    DEFAULT lCRM := .f.

    oModelOld:DeActivate()
    IF lCrm
        U_DLP73F01(IIf(AllTrim(AD1->AD1_CODCLI)$"000001","orcamentos@delpi.com.br","orcamentos3@delpi.com.br"))
    endif

    FWMsgRun(, {|| fCpySB1(lCRM) }, "Delpi LMP", "Aguarde Gerando Produtos...")
    oModelOld:Activate()
    oViewOld:Refresh()

Return


Static Function fCpySB1(lCRM)
    //43317
    lOCAL  aArea    := getarea()
    lOCAL  aAreaSB1 := SB1->(GetArea())
    lOCAL  aAreaADJ := ADJ->(GetArea())
    lOCAL  aAreaAD1 := AD1->(GetArea())
    Local cEol := chr(10)


    // if!Pergunte("DLP73F06")
    //     FWAlertWarning("Cancelado pelo Usuario", "Delpi LMP")
    //     rETURN
    // Endif

    cQry := "SELECT * FROM ADJ010 ADJ" +cEol
    cQry += "WHERE  ADJ.D_E_L_E_T_ = ' '"  +cEol
    cQry += "AND ADJ_FILIAL = " + VALTOSQL(AD1->AD1_FILIAL)  +cEol
    cQry += "AND ADJ_NROPOR = " + VALTOSQL(AD1->AD1_NROPOR)
    cQry += "ORDER BY ADJ_ITEM"


    If Select('TMPAD1') <> 0
        TMPAD1->(dbCloseArea())
    Endif

    TCQuery cQry Alias TMPAD1 New

    While TMPAD1->(!eof())
        cCodOpor :=  TMPAD1->ADJ_PROD
        cGrpPA :=  TMPAD1->ADJ_GRPPA

        SB1->(dbSelectArea( "SB1" ))
        SB1->(dbSetOrder(19))
        IF !(SB1->(dbSeek(xfilial("SB1")+cCodOpor)))

            //     cRevOri := B1_REVATU
            //  cGrpPA   := MV_PAR02
            //  cCodOpor := MV_PAR01
            cItemOpor := "01"

            SB1->(dbSelectArea( "SB1" ))
            SB1->(dbSetOrder(1))
            SB1->(dbSeek(xfilial("SB1")+cCodOpor))

            // cCodBas := SB1->B1_COD
            //A010Copia()
            cCodRet :=   fPutSB1(cCodOpor,cGrpPA )
            //cCodRet := ""
            if !Empty(cCodRet )
                SB1->(dbSelectArea( "SB1" ))
                SB1->(dbSetOrder(1))
                if SB1->(dbSeek(xfilial("SB1")+cCodRet))
                    if SB1->(Found())
                        nReg	:= SB1->(RecNo())
                        cAlias := "SB1"
                        nOpc := 4
                        MA010Alter(cAlias,nReg,nOpc)
                    endif
                endif
            endif
            dbSelectArea( "SG1" )
            SG1->( DbSetOrder(1) )
            if SG1->(dbSeek(xfilial("SG1")+cCodOpor))

                SB1->(dbSelectArea( "SB1" ))
                SB1->(dbSetOrder(1))
                SB1->(dbSeek(xfilial("SB1")+cCodOpor))

                fPutEst(cCodOpor,cCodRet)
            ELSE
                FWAlertWarning("Produto: "+alltrim(cCodOpor)+" não possui estrutura", "Delpi LMP - Estrutura PCPA200")
            ENDIF
            dbSelectArea( "SG2" )
            SG2->( DbSetOrder(1) )
            if SG2->(dbSeek(xfilial("SG2")+cCodOpor))
                //    cCodRet :=   "90263618"
                fCpyRot(cCodRet)
            ELSE
                FWAlertWarning("Produto: "+alltrim(cCodOpor)+" não possui roteiro", "Delpi LMP - Estrutura PCPA124")
            ENDIF
        ENDIF

        TMPAD1->(dbskip())
    Enddo
    TMPAD1->(dbCloseArea())
    RESTAREA( aArea)
    RESTAREA(aAreaSB1 )
    RESTAREA(aAreaADJ )
    RESTAREA(aAreaAD1 )
    // //Desabilita o F4
    //  SET KEY VK_F4 TO
    //  nOK := (FWExecView (STR0006, "MATA010",  MODEL_OPERATION_UPDATE,,{||.T.},,,,,,,))
Return


Static Function fPutEst(cCodBas,cCodRet)
    lOCAL  aArea    := getarea()
    lOCAL  aAreaSB1 := SB1->(GetArea())
    lOCAL  aAreaSG1 := SG1->(GetArea())


    local aRotBKP := aRotina

    Local oModelAux   := FWLoadModel("PCPA200")
    Local oEvent      := gtMdlEvent(oModelAux,"PCPA200EVDEF")
    Local nOk := .T.
    aRotina := FWMVCMenu( 'PCPA200' )
    Private cProdFiltro := "MV_PAR01"
    dbSelectArea("SG1")
    SG1->( DbSetOrder(1) )
    if   SG1->(dbSeek(xfilial("SG1")+cCodBas))

        If ExistePerg('PCPA200C')
            // oModelAux:SetOperation(3)
            // INCLUI :=.T.
            // ALTERA := .F.
            // nopc := 3
            //  conout("INCLUI "+ cvaltochar(INCLUI))
            //  conout("ALTERA "+ cvaltochar(ALTERA))
            //  conout("nopc "+ cvaltochar(nopc))
            Pergunte("PCPA200C",.F.)
            SetMVValue("PCPA200C","MV_PAR01",cCodBas)
            SetMVValue("PCPA200C","MV_PAR02", P200IniRev(cCodBas))
            SetMVValue("PCPA200C","MV_PAR03",cCodRet)
            SetMVValue("PCPA200C","MV_PAR04",IIF(EMPTY(P200IniRev(cCodRet)),"001",P200IniRev(cCodRet)))

            //Chama Pergunte PCPA200C
            oEvent := Iif(oEvent == Nil, PCPA200EVDEF():New(), oEvent)
            SetMVValue("PCPA200C","MV_PAR01",cCodBas)
            SetMVValue("PCPA200C","MV_PAR02", P200IniRev(cCodBas))
            SetMVValue("PCPA200C","MV_PAR03",cCodRet)
            SetMVValue("PCPA200C","MV_PAR04",IIF(EMPTY(P200IniRev(cCodRet)),"001",P200IniRev(cCodRet)))
            oEvent:lCopia := .T.
            oEvent:mvcEstruturaOrigem := cCodBas
            oEvent:mvcRevisaoOrigem   :=  P200IniRev(cCodBas)
            oEvent:mvcProdutoDestino  := cCodRet
            oEvent:mvcRevProdDestino  := IIF(EMPTY(P200IniRev(cCodRet)),"001",P200IniRev(cCodRet))
            oEvent:lCopia := .T.
            conout("stop")
            // If !oEvent:PergPCPA200C(.t.)
            //     Return
            // EndIf

            //oModel:LoadValue("PCPA124_CAB","G2_PRODUTO",cCodRet)
            //cRet := Posicione("SB1",1,xFilial("SB1")+cCodRet,"B1_DESC")
            //oModel:LoadValue("PCPA124_CAB","CDESCPROD",cRet)
            //  oModelAux:GetModel("SG1_MASTER"):LoadValue("G1_COD", Padr(oEvent:mvcProdutoDestino, GetSX3Cache("G1_COD","X3_TAMANHO")))
            P200FcPesq(.T.)

            nOk := 	FWExecView("ESTRUTURA PRODUTO", "PCPA200", MODEL_OPERATION_INSERT,,,{|| P200AvaRev()},,,,,,oModelAux) //"Estrutura Similar"
            oEvent:lCopia := .F.


        EndIf
    EndIf
    if oModelAux:isActive()
        oModelAux:DeActivate()
        oModelAux:Destroy()
    endif


    aRotina :=  aRotBKP
    RESTAREA(aArea    )
    RESTAREA(aAreaSB1 )
    RESTAREA(aAreaSG1 )
Return nOk


Static Function fPutSB1(cCodBase,cGrpPA)

    Local cEol := chr(10)
    Local cCodProd := ""
    Local aArea := GetArea()
    cSql1:= "SELECT * " + cEol
    cSql1+= "FROM dbo." + RetSqlName("SB1") + " SB1 (NOLOCK) " + cEol
    cSql1+= "WHERE SB1.D_E_L_E_T_ ='' " + cEol
    cSql1+= "AND  SB1.B1_FILIAL = "+VALTOSQL(XFILIAL("SB1")) + cEol
    cSql1+= "AND  SB1.B1_COD = "+VALTOSQL(cCodBase) + cEol

    If (Select("QRY1") <> 0)
        dbSelectArea("QRY1")
        dbCloseArea()
    Endif

    CONOUT("cSql1"+cEol+cSql1)

    TCQuery cSql1 NEW  ALIAS "QRY1"

    IF  QRY1->(!Eof())

        oModel := FWLoadModel("MATA010")
        oModel:SetOperation(3)
        if !(oModel:isActive())
            oModel:Activate()
        endif
        //Pegando o model e setando os campos
        oSB1Mod := oModel:GetModel("SB1MASTER")
        oSB1Mod:SetValue("B1_GRUPO"      , cGrpPA        )
        oSB1Mod:SetValue("B1_DESC"       , QRY1->B1_DESC         )
        oSB1Mod:SetValue("B1_REFEREN"    , QRY1->B1_REFEREN      )
        oSB1Mod:SetValue("B1_REFCANT"    , QRY1->B1_REFCANT      )
        oSB1Mod:SetValue("B1_CODDES"     , QRY1->B1_CODDES       )
        oSB1Mod:SetValue("B1_TIPO"       , QRY1->B1_TIPO         )
        oSB1Mod:SetValue('B1_YHOHS'      ,	QRY1->B1_YHOHS    )
        oSB1Mod:SetValue('B1_POSIPI'    ,	QRY1->B1_POSIPI   )
        oSB1Mod:SetValue('B1_LOCPAD'    ,	QRY1->B1_LOCPAD   )
        oSB1Mod:SetValue('B1_UM'        ,		QRY1->B1_UM       )
        oSB1Mod:SetValue('B1_SEGUM',	QRY1->B1_SEGUM    )
        oSB1Mod:SetValue('B1_ORIGEM',	QRY1->B1_ORIGEM    )
        oSB1Mod:SetValue('B1_TE',		QRY1->B1_TE       )
        oSB1Mod:SetValue('B1_TS',		QRY1->B1_TS       )
        oSB1Mod:SetValue('B1_PICMRET',	QRY1->B1_PICMRET )
        oSB1Mod:SetValue('B1_CONV',		QRY1->B1_CONV    )
        oSB1Mod:SetValue('B1_TIPCONV',	QRY1->B1_TIPCONV )
        oSB1Mod:SetValue('B1_TPMAT',	QRY1->B1_TPMAT   )
        oSB1Mod:SetValue('B1_ESPECIE',	QRY1->B1_ESPECIE )
        oSB1Mod:SetValue('B1_EX_NCM',	QRY1->B1_EX_NCM  )
        oSB1Mod:SetValue('B1_EX_NBM',	QRY1->B1_EX_NBM  )
        oSB1Mod:LoadValue('B1_CONTA',	QRY1->B1_CONTA  )
        oSB1Mod:SetValue('B1_CODOPOR',	cCodOpor  )
        oSB1Mod:SetValue('B1_ITOPOR',	cItemOpor  )
        oSB1Mod:SetValue('B1_CODCRM',	cCodBase )


        //Se conseguir validar as informações
        If oModel:VldData()

            //Tenta realizar o Commit
            If oModel:CommitData()
                lOk := .T.
                cCodProd := SB1->B1_COD
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
            EEcView(cMessage, "LMP - Cadastro de Produto")
            //Mostra mensagem de erro
            lRet := .F.
            //    ConOut("Erro: " + cMessage)
        Else
            lRet := .T.

            ConOut("Produto incluido!")
        EndIf

        //Desativa o modelo de dados
        oModel:DeActivate()
        oModel:Destroy()

    ELSE
        FWAlertError("LMP - CADASTRO DE PRODUTO", "Produto nao encontrado!")
    ENDIF
    RestArea(aArea)

reTURN cCodProd



/*/{Protheus.doc} gtMdlEvent
Recupera a referência do objeto dos Eventos do modelo.

@type  Static Function
@author lucas.franca
@since 04/02/2019
@version P12
@param oModel  , Object   , Modelo de dados
@param cIdEvent, Character, ID do evento que se deseja recuperar.
@return oEvent , Object   , Referência do evento do modelo de dados.
/*/
Static Function gtMdlEvent(oModel, cIdEvent)
    Local nIndex  := 0
    Local oEvent  := Nil
    Local oMdlPai := Nil

    If oModel != Nil
        oMdlPai := oModel:GetModel()
    EndIf

    If oMdlPai != Nil .And. AttIsMemberOf(oMdlPai, "oEventHandler", .T.) .And. oMdlPai:oEventHandler != NIL
        For nIndex := 1 To Len(oMdlPai:oEventHandler:aEvents)
            If oMdlPai:oEventHandler:aEvents[nIndex]:cIdEvent == cIdEvent
                oEvent := oMdlPai:oEventHandler:aEvents[nIndex]
                Exit
            EndIf
        Next nIndex
    EndIf

Return oEvent



/*/{Protheus.doc} ExistePerg
Verifica se a Pergunte existe na SX1
@author marcelo.neumann
@since 25/06/2019
@version 1.0
@param cPergunte, caracter, código da Pergunte a ser pesquisada
@return lExiste, lógico, indica se a Pergunte enviada existe na SX1
/*/
Static Function ExistePerg(cPergunte)

    Local oPergunta := NIL
    Local aDadosPer := {}

    oPergunta := FWSX1Util():New()
    oPergunta:AddGroup(cPergunte)
    oPergunta:SearchGroup()
    aDadosPer := oPergunta:GetGroup(cPergunte)

Return !Empty(aDadosPer[2])






Static Function fCpyRot(cCodRet)

    Local oStruSG2
    Local oStruSH3R
    Local oStruSH3F
    Local oStruSGR
    Local oStruSHJ
    Local aStructSG2    := {}
    Local aStructSH3    := {}
    Local aStructSGR    := {}
    Local aStructSHJ    := {}
    Local nI            := 1
    Local nSH3_R        := 1
    Local nSH3_F        := 1
    Local nSGR          := 1
    Local nSHJ          := 1
    Local nCampoTam     := 0
    Local lMvChkOper    := SuperGetMV("MV_CHKOPER",.F.,.F.)
    Local lUniLin		:= SuperGetMv("MV_UNILIN",.F.,.F.)
    Local nRet

    Local oModel        := FwLoadModel("PCPA124")
    Local lSoMontaModel := .F.

    Private Inclui := .t.

    oStruSG2 	:= oModel:Getmodel("PCPA124_SG2")
    oStruSH3R	:= oModel:GetModel("PCPA124_SH3_R")
    oStruSH3F	:= oModel:GetModel("PCPA124_SH3_F")
    oStruSGR	:= oModel:GetModel("PCPA124_SGR")
    oStruSHJ	:= oModel:GetModel("PCPA124_SHJ")

    oModel:SetOperation(MODEL_OPERATION_INSERT)
    oModel:Activate()

    cProdAux := SG2->G2_PRODUTO
    cCodAux := SG2->G2_CODIGO

    oModel:LoadValue("PCPA124_CAB","G2_PRODUTO",cCodRet)
    cRet := Posicione("SB1",1,xFilial("SB1")+cCodRet,"B1_DESC")
    oModel:LoadValue("PCPA124_CAB","CDESCPROD",cRet)

    //Pega estrutura da tabela Filho
    aStructSG2 := SG2->(dbStruct())
    aStructSH3 := SH3->(dbStruct())
    aStructSGR := SGR->(dbStruct())
    aStructSHJ := SHJ->(dbStruct())

    //Faz a consulta na tabela filho
    dbSelectArea( "SG2" )

    if MatGrdPrrf(cProdAux) //Verifica se o produto é referência grade
        SG2->( DbSetOrder(7) )
        nCampoTam := GetSx3Cache("G2_REFGRD","X3_TAMANHO")
    else
        SG2->( DbSetOrder(1) )
        nCampoTam := GetSx3Cache("G2_PRODUTO","X3_TAMANHO")
    EndIf

    If SG2->( dbSeek( xFilial( "SG2" )+PadR(cProdAux,nCampoTam)+cCodAux))

        //Carrega SH3 - recursos e ferramentas alternativos
        dbSelectArea( "SH3" )
        SH3->( DbSetOrder(1) )

        //Enquanto houver registros filhos, vai adicionando no grid
        While SG2->(!Eof()) .and. xFilial("SG2") == SG2->G2_FILIAL .and. (cProdAux == SG2->G2_PRODUTO .Or. PadR(cProdAux,nCampoTam) == SG2->G2_REFGRD) .and. cCodAux == SG2->G2_CODIGO
            //Verifica se precisa gerar mais um linha(se for a primeira não precisa)
            If !Empty(oStruSG2:GetValue('G2_OPERAC')) .OR. oStruSG2:IsDeleted()
                oStruSG2:AddLine()
            EndIf

            //Adiciona o valor pra cada campo do grid
            For nI := 1 To Len(aStructSG2)
                If !( A124FormVa(aStructSG2[nI][1]) $ "|G2_FILIAL|G2_PRODUTO|G2_CODIGO|G2_REVIPRD|" ) .And. oStruSG2:HasField(aStructSG2[nI][1])
                    oStruSG2:LoadValue(aStructSG2[nI][1],SG2->&(aStructSG2[nI][1]))
                EndIf
                //  if   ( A124FormVa(aStructSG2[nI][1]) $ "|G2_PRODUTO|" ) //.And. oStruSG2:HasField(aStructSG2[nI][1])
                //      oStruSG2:SetValue(aStructSG2[nI][1],cCodRet)
                //  endif
                //  If ( A124FormVa(aStructSG2[nI][1]) $ "|G2_ROTALT|" )
                //      oStruSG2:LoadValue(aStructSG2[nI][1],SG2->&(aStructSG2[nI][1]))
                //  EndIf
            Next

            If !oStruSG2:VldLineData()
                MsgStop("Não foi possível incluir a operação. Motivo: "+oModel:GetErrorMessage()[6],'') //'Não foi possível incluir a operação. Motivo: '
                Exit
            EndIf

            nSH3_R := 1
            nSH3_F := 1

            If SH3->( dbSeek( xFilial( "SH3" )+cProdAux+cCodAux+SG2->G2_OPERAC))
                //Enquanto houver registros filhos, vai adicionando no grid
                While SH3->(!Eof()) .and. xFilial("SH3") == SH3->H3_FILIAL .and. cProdAux == SH3->H3_PRODUTO .and. cCodAux == SH3->H3_CODIGO .and. SG2->G2_OPERAC == SH3->H3_OPERAC
                    If Empty(SH3->H3_FERRAM)
                        //Verifica se precisa gerar mais um linha(se for a primeira não precisa)
                        If nSH3_R != 1
                            oStruSH3R:AddLine()
                        EndIf

                        //Adiciona o valor pra cada campo do grid
                        For nI := 1 To Len(aStructSH3)
                            If !( A124FormVa(aStructSH3[nI][1]) $ "|H3_FILIAL|H3_PRODUTO|H3_CODIGO|H3_OPERAC|H3_FERRAM|H3_DESCFER|H3_RECPRIN|" )
                                oStruSH3R:LoadValue(aStructSH3[nI][1],SH3->&(aStructSH3[nI][1]))
                            EndIf
                        Next

                        //Carrega descrição do recurso
                        oStruSH3R:SetValue("H3_DESC",PadR(Posicione("SH1",1,xFilial("SH1")+FwFldGet("H3_RECALTE"),"H1_DESCRI"),GetSx3Cache("H3_DESC","X3_TAMANHO")))
                        nSH3_R++
                    Else
                        //Verifica se precisa gerar mais um linha(se for a primeira não precisa)
                        If nSH3_F != 1
                            oStruSH3F:AddLine()
                        EndIf

                        //Adiciona o valor pra cada campo do grid
                        For nI := 1 To Len(aStructSH3)
                            If !( A124FormVa(aStructSH3[nI][1]) $ "|H3_FILIAL|H3_PRODUTO|H3_CODIGO|H3_OPERAC|H3_RECPRIN|H3_RECALTE|H3_TIPO|H3_EFICIEN|H3_DESC|")
                                oStruSH3F:LoadValue(aStructSH3[nI][1],SH3->&(aStructSH3[nI][1]))
                            EndIf
                        Next

                        //Carrega descrição da ferramenta
                        oStruSH3F:SetValue("H3_DESCFER",PadR(Posicione("SH4",1,xFilial("SH4")+FwFldGet("H3_FERRAM"),"H4_DESCRI"),GetSx3Cache("H3_DESCFER","X3_TAMANHO")))
                        nSH3_F++
                    endif
                    //Pula pro próximo registro filho
                    SH3->(DbSkip())
                EndDo
            EndIf

            //Carrega SGR - Checklist das operações
            If lMvChkOper
                SGR->( DbSetOrder(1) )

                nSGR := 1

                If SGR->( dbSeek( xFilial( "SGR" )+cProdAux+cCodAux+SG2->G2_OPERAC))
                    //Enquanto houver registros filhos, vai adicionando no grid
                    While SGR->(!Eof()) .and. xFilial("SGR") == SGR->GR_FILIAL .and. cProdAux == SGR->GR_PRODUTO .and. cCodAux == SGR->GR_ROTEIRO .and. SG2->G2_OPERAC == SGR->GR_OPERAC
                        //Verifica se precisa gerar mais um linha(se for a primeira não precisa)
                        If nSGR != 1
                            oStruSGR:AddLine()
                        EndIf
                        //Adiciona o valor pra cada campo do grid
                        For nI := 1 To Len(aStructSGR)
                            If !( A124FormVa(aStructSGR[nI][1]) $ "|GR_FILIAL|GR_ROTEIRO|GR_PRODUTO|GR_OPERAC|GR_DESCOP|" )
                                oStruSGR:LoadValue(aStructSGR[nI][1],SGR->&(aStructSGR[nI][1]))
                            EndIf
                        Next
                        nSGR++
                        //Pula pro próximo registro filho
                        SGR->(DbSkip())
                    EndDo
                EndIf
            EndIf

            //Carrega SHJ - Integração com o Drummer
            If TipoAps(.F.,"DRUMMER")
                SHJ->( DbSetOrder(1) )

                nSHJ := 1

                If SHJ->( dbSeek( xFilial( "SHJ" )+cCodAux+cProdAux+SG2->G2_OPERAC))
                    //Enquanto houver registros filhos, vai adicionando no grid
                    While SHJ->(!Eof()) .and. xFilial("SHJ") == SHJ->HJ_FILIAL .and. cProdAux == SHJ->HJ_PRODUTO .and. cCodAux == SHJ->HJ_ROTEIRO .and. SG2->G2_OPERAC == SHJ->HJ_OPERAC
                        //Verifica se precisa gerar mais um linha(se for a primeira não precisa)
                        If nSHJ != 1
                            oStruSHJ:AddLine()
                        EndIf
                        //Adiciona o valor pra cada campo do grid
                        For nI := 1 To Len(aStructSHJ)
                            If !( A124FormVa(aStructSHJ[nI][1]) $ "|HJ_FILIAL|HJ_ROTEIRO|HJ_PRODUTO|HJ_OPERAC|HJ_CTRAB|" )
                                oStruSHJ:LoadValue(aStructSHJ[nI][1],SHJ->&(aStructSHJ[nI][1]))
                                oStruSHJ:SetValue("HJ_DESCREC",PadR(Posicione("SH1",1,xFilial("SH1")+FwFldGet("HJ_RECURSO"),"H1_DESCRI"),TamSX3("HJ_DESCREC")[1]))
                            EndIf
                        Next
                        nSHJ++
                        //Pula pro próximo registro filho
                        SHJ->(DbSkip())
                    EndDo
                EndIf
            EndIf

            //Pula pro próximo registro filho
            SG2->(DbSkip())
        EndDo
        If lUniLin
            oModel:GetModel("PCPA124_CAB"):LoadValue("G2_LINHAPR",oModel:GetModel("PCPA124_SG2"):GetValue("G2_LINHAPR",1))
            oModel:GetModel("PCPA124_CAB"):LoadValue("G2_TPLINHA",oModel:GetModel("PCPA124_SG2"):GetValue("G2_TPLINHA",1))
        EndIf
    EndIf

    oStruSG2:GoLine(1)

    If !lSoMontaModel
        nRet := FWExecView("ROTEIRO OPERACAO", "PCPA124", OP_INCLUIR, /*oDlg*/, {|| .T. }, /*bOk*/ , /*nPercReducao*/, /*aEnableButtons*/, /*bCancel*/ , /*cOperatId*/, /*cToolBar*/, oModel)
    EndIf
Return oModel



/*/{Protheus.doc} A124FormVa
Função para formatar a variável para utilização do operador $
@author Marcelo Neumann
@since 07/06/2018
@version 1.0
/*/
Static Function A124FormVa(cVar)

    cVar := "|" + AlLTrim(cVar) + "|"
Return cVar
