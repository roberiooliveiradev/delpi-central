#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"


user Function DLP02J03(cEmpJob,cFilJob,nOpc)

    Local cHoraIni  := ""
    Local cHoraFim  := ""
    Local cHoraUlt  := "00:00:01"
    Local cHora     := cHoraUlt
    Local cAtivo    := "ON"

    Local nIntervalo:= 0

    DEFAULT cEmpJob	:= "01"
    DEFAULT cFilJob	:= "01"
    DEFAULT nOpc	:= "1"
    CONOUT("Chamou o Job DLP02J01")
    //-- Evita que se consuma licenca
    // RpcSetType( 3 )
    //
    // PREPARE ENVIRONMENT EMPRESA cEmpJob FILIAL cFilJob MODULO "FAT"

    CONOUT("EMPRESA " + CEMPANT)
    CONOUT("FILIAL  " + CFILANT)

    if nOpc == '1' //	"210200" //confirmacao

        fProcMani()

    elseif nOpc == '2'  // download

    endif

    //GetMDeSinc(2)
    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³Espera                                                             ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
    Sleep(3000)

    //  If KillApp()
    //      Exit
    //  EndIf

    //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
    //³Finalisando o ambiente para execucao                                    ³
    //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
    RESET ENVIRONMENT

Return

Static Function fProcMani()
    Local cEol := chr(10)
    Local cIdEnt		:= RetIdEnti()
    Local cURL			:= PadR(GetNewPar("MV_SPEDURL","http://"),250)
    cSql :="SELECT	R_E_C_N_O_ RECC00,C00.* FROM		dbo.C00010 C00 (NOLOCK) " + cEol
    cSql +="	WHERE		C00.D_E_L_E_T_ = '' " + cEol
    cSql +="	 AND	C00.C00_FILIAL = '01' " + cEol
    cSql +="	 AND	C00.C00_ANONFE = '2022' " + cEol
    cSql +="	 AND	C00.C00_MESNFE >= '02' " + cEol
    cSql +="	 AND	C00.C00_STATUS = '0'   " + cEol
    cSql +="	 AND	C00.C00_CODEVE = '1'   " + cEol
    cSql +="	 AND	C00.C00_SITDOC = '1'   "

    If Select('TMPC00') <> 0
        TMPC00->(dbCloseArea())
    Endif
    CONOUT(cSql)
    CMSGERRO := ""
    TCQuery cSql Alias TMPC00 New

    DBSELECTAREA("C00")
    C00->(dbSetOrder(1))
    While TMPC00->(!eof())
        C00->(dbGoTo(TMPC00->RECC00))
        nRecNOC00 := TMPC00->RECC00
        cTSSAmbi := ""
        //Chama rotina para efetuar a manifestação do destinatário
        //para posterior conseguir efetuar o download da nota fiscal
        cRetorno	:=	""
        cJustific	:=	""
        cCbCpo		:=	"210200" //confirmacao
        cChv := TMPC00->C00_CHVNFE
        lEnvOk :=   GerXmlManif(cCbCpo,cChv,@cRetorno,cJustific,@cTSSAmbi)
        IF ! lEnvOk
            CMSGERRO += "Chave "+ cChv +" | Deu erro na rotina GerXmlManif"
            TMPC00->(dbskip())
            Loop
        else
            lEnvOk :=   ManiMonSl(cChv,cTSSAmbi,cIdEnt,cURL,nRecNOC00)

        ENDIF

        if !lEnvOk
            CMSGERRO += "Chave "+ cChv +" | Deu erro na rotina ManiMonSl"
            TMPC00->(dbskip())
            Loop
        else

        endif

        TMPC00->(dbskip())

    Enddo

    TMPC00->(dbCloseArea())
Return




/*/{Protheus.doc} MontaXmlManif

Monta Manifesto

@author charlesT
@since 03/05/2017
@version undefined
@param cCbCpo, characters, descricao
@param aMontXml, array, descricao
@param cRetorno, characters, descricao
@param cJustific, characters, descricao
@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
Static Function GerXmlManif(cCbCpo,cChaveNFE,cRetorno,cJustific)
    Local aRet			:={}
    Local cAmbiente		:= ""
    Local cXml			:= ""
    Local cTpEvento		:=  SubStr(cCbCpo,1,6)
    Local cIdEnt		:= RetIdEnti()
    Local cURL			:= PadR(GetNewPar("MV_SPEDURL","http://"),250)
    Local cChavesMsg	:= ""
    Local cMsgManif		:= ""
    Local lRetOk		:= .F.
    Local nX 			:= 0

    Local nZ 			:= 0
    Local oWs			:= Nil
    Default cJustific 	:= ""
    Private lUsaColab		:= UsaColaboracao("4")

    Begin Sequence

        If !RetRdTSS()
            Aviso(procname(),"Execute o módulo de configuração do serviço, antes de utilizar esta opção!!!",{"OK"},3) //"Execute o módulo de configuração do serviço, antes de utilizar esta opção!!!"
            Break
        EndIf

        //Atualiza o status na rotina de manifestacao padrao
        dbSelectArea("C00")
        C00->(DbSetOrder(1))
        If C00->(!DBSEEK(xFilial("C00")+Alltrim(cChaveNFE)))
            MsgStop("Falha ao localizar a manifestação (C00)","Atenção - "+ProcName())
            Break
        EndIf
        nRecNOC00	:=	C00->(RecNo())
        oWs :=WSMANIFESTACAODESTINATARIO():New()
        oWs:cUserToken   	:= "TOTVS"
        oWs:cIDENT	     	:= cIdEnt
        oWs:cAMBIENTE	 	:= ""
        oWs:cVERSAO      	:= ""
        oWs:_URL         	:= AllTrim(cURL)+"/MANIFESTACAODESTINATARIO.apw"

        If !oWs:CONFIGURARPARAMETROS()
            MsgStop(IIf(Empty(GetWscError(3)),GetWscError(1),GetWscError(3)),"Atenção - "+ProcName())
            Break
        EndIf
        cAmbiente		 := oWs:OWSCONFIGURARPARAMETROSRESULT:CAMBIENTE
        cTSSAmbi		 := oWs:OWSCONFIGURARPARAMETROSRESULT:CAMBIENTE

        cXml:=	""
        cXml+='<envEvento>'
        cXml+='<eventos>'
        cXml+='<detEvento>'
        cXml+='<tpEvento>'+cTpEvento+'</tpEvento>'
        cXml+='<chNFe>'+Alltrim(cChaveNFE)+'</chNFe>'
        cXml+='<ambiente>'+cAmbiente+'</ambiente>'
        //If '210240' $ cTpEvento .and. !Empty(cJustific)
        //	cXml+='<xJust>'+Alltrim(cJustific)+'</xJust>'
        //EndIf
        cXml+='</detEvento>'
        cXml+='</eventos>'
        cXml+='</envEvento>'

        oWs:= WsNFeSBra():New()
        oWs:cUserToken	:= "TOTVS"
        oWs:cID_ENT		:= cIdEnt
        oWs:cXML_LOTE	:= cXml
        oWS:_URL		:= AllTrim(cURL)+"/NFeSBRA.apw"

        If !oWs:RemessaEvento()
            MsgStop(IIf(Empty(GetWscError(3)),GetWscError(1),GetWscError(3)),"Atenção - "+ProcName())
            Break
        EndIf

        If Type("oWS:oWsRemessaEventoResult:cString") <> "U"
            If Type("oWS:oWsRemessaEventoResult:cString") <> "A"
                aRetorno:={oWS:oWsRemessaEventoResult:cString}
            Else
                aRetorno:=oWS:oWsRemessaEventoResult:cString
            EndIf
        EndIf

        dbSelectArea("C00")
        C00->(RecLock("C00"),.F.)
        C00->C00_STATUS := "1" //Confirmacao de operacao
        C00->C00_CODEVE := "2"
        C00->(MsUnlock())

        //ENVIADO MANIFESTACAO
        //C00_STATUS = 1
        //C00_SITDOC = 1
        //C00_CODEVE = 2
        //APOS MONITOR
        //C00_CODEVE = 3
        //Monitor altera os campos

        cMsgManif := "Transmissão da Manifestação concluída com sucesso!"+ Chr(10) + Chr(13)//"Transmissão da Manifestação concluída com sucesso!"
        cMsgManif += cCbCpo + Chr(10) + Chr(13)
        cMsgManif += "Chave(s): "+ Chr(10) + Chr(13)
        cMsgManif += cChaveNFE

        //Chama rotina para fazer o omonitoramento e pegar o resultado do sefaz.
        //   FWMsgRun( ,{|| lRetOk	:=	ManiMonSl(cChaveNFE,cAmbiente,cIdEnt,cURL,nRecNOC00)},"Aguardando autorização SEFAZ...")

        //  If !lRetOk
        //      Break
        //  EndIf

        //sleep(20000) //espera  30 segundos para o sefaz atualizar e liberar o download


        lRetOk	:=	.T.

    End Sequence

Return lRetOk




/*/{Protheus.doc} AtuSA5XSA2

Monitora autorizacao do sefaz,
C00 precisa estar posicioanada

@author charlesT
@since 19/05/2017
@version undefined
@param cFornece, characters, description
@param cLoja, characters, description
@param cProduto, characters, description
@param cProdCodF, characters, description
@param cProdDesF, characters, description
@return return, return_description
@example
(examples)
@see (links_or_references)
/*/
Static Function ManiMonSl(cChaveNFE,cAmbiente,cIdEnt,cURL,nRecNoC00)
    Local lRet		:=	.F.
    Local nTimeWait	:=	2000
    Local nQtdTent	:=	10
    Begin Sequence

        C00->(dbGoTo(nRecNoC00))


        For nIO := 1 To nQtdTent
            Sleep(nTimeWait)
            //MonitoraManif({cChaveNFE}, cAmbiente, cIdEnt, GetNewPar("MV_SPEDURL","http://")+"/MANIFESTACAODESTINATARIO.apw")
            MonitoraManif({cChaveNFE}, cAmbiente, cIdEnt, GetNewPar("MV_SPEDURL","http://")+"/MANIFESTACAODESTINATARIO.apw")
            C00->(dbGoTo(nRecNoC00))
            If C00->C00_STATUS=='1' .and. alltrim(C00->C00_CODEVE)=='3' .AND. alltrim(C00->C00_SITDOC) = '1'
                //     Sleep(2000)
                Exit
            EndIf

            //Caso chego ao seu limite, sai sem finalizar
            If nIO == nQtdTent
                MsgStop("Não conseguimos recuperar o retorno do sefaz, efetue o processo de monitor do Manifesto do Destinatário e tente novamente.","Atenção - "+Procname())
                Break
            EndIf

        Next

        lRet	:=	.T.
    End Sequence


Return lRet
