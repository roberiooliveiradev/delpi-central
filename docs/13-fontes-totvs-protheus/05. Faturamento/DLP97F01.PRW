#INCLUDE "PROTHEUS.CH"
#INCLUDE "SPEDNFE.CH"
#INCLUDE "APWIZARD.CH"

/*DLP97F01 - FUNÇÃO PARA LISTAR OS DOCUMENTOS EXISTENTES NA SEFAZ*/
USER FUNCTION DLP97F01()


    MsgRun("Aguarde Sincronização","Processando",{|| SincDados( .T.,.T.)})
    //  MsgRun("Aguarde Sincronização","Processando",{|| SincDados( .f.,.f.)})

RETURN


Static Function SincDados(lProcAll,lRefazSinc)

    Local aChave	:= {}
    Local aDocs		:= {}
    Local aProc		:= {}

    Local cURL		:= PadR(GetNewPar("MV_SPEDURL","http://"),250)
    local lUsaColab	:= UsaColaboracao("4")
    Local cIdEnt	:= RetIdEnti(lUsaColab)
    Local cChave	:= ""
    Local cCancNSU	:= ""
    Local cAlert	:= ""
    Local cSitConf	:= ""
    Local cCodEvento	:= ""
    Local cAmbiente	:= ""
    Local lContinua	:= .T.

    Local dData		:= CtoD("  /  /    ")

    Local lOk		:= .F.
    Local lDestcnpj	:= .T.

    Local nX		:= 0
    Local nZ		:= 0

    Private oWs		:= Nil
    Private oInfdoc	:= Nil

    Default lProcAll    := .t. //"Sincronizar até finalizar todos os documentos."
    Default lRefazSinc	:= .t. // "Refaz a sincronização dos documentos."

    If CTIsReady(cURL,1,.t.,lUsaColab)

        oWs :=WSMANIFESTACAODESTINATARIO():New()
        oWs:cUserToken   := "TOTVS"
        oWs:cIDENT	     := cIdEnt
        oWs:cINDNFE		 := "0"
        oWs:cINDEMI      := "0"
        oWs:_URL         := AllTrim(cURL)+"/MANIFESTACAODESTINATARIO.apw"

        cAmbiente		 :=  getAmbMde()

        // Refaz a sincronização de todos os documentos disponiveis na SEFAZ
        If lRefazSinc
            oWs:cUltNSU	:= "0"
            oWs:CONFIGURARPARAMETROS()
        Endif

        //Tratamento para solicitar a sincronização enaquanto o IDCONT não retornar zero.

        While lContinua

            lOk		:= .F.
            aChave	:= {}
            aProc	:= {}

            If oWs:SINCRONIZARDOCUMENTOS()
                conout("break")
                If Type ("oWs:OWSSINCRONIZARDOCUMENTOSRESULT:OWSDOCUMENTOS:OWSSINCDOCUMENTOINFO") <> "U"
                    If Type("oWs:OWSSINCRONIZARDOCUMENTOSRESULT:OWSDOCUMENTOS:OWSSINCDOCUMENTOINFO")=="A"
                        aDocs := oWs:OWSSINCRONIZARDOCUMENTOSRESULT:OWSDOCUMENTOS:OWSSINCDOCUMENTOINFO
                    Else
                        aDocs := {oWs:OWSSINCRONIZARDOCUMENTOSRESULT:OWSDOCUMENTOS:OWSSINCDOCUMENTOINFO}
                    EndIf
                    For nX := 1 To Len(aDocs)
                        oInfdoc := aDocs[nx]
                        conout("Chave "+ oInfdoc:CCHAVE)
                    next nX
                    /*  For nX := 1 To Len(aDocs)
                        lDestcnpj:=.T.
                        oInfdoc := aDocs[nx]
                        If Type("oInfdoc:CCHAVE") <> "U" .and. Type("oInfdoc:CSITCONF") <> "U"
                            cSitConf  := oInfdoc:CSITCONF
                            cChave    := oInfdoc:CCHAVE
                            cCancNSU  := oInfdoc:CCANCNSU
                            If Type("oInfdoc:CCODEVENTO") <> "U"
                                cCodEvento:= oInfdoc:CCODEVENTO
                            Else
                                CodEvento:= ""
                            EndIf
                            If Type("oInfdoc:cDESTCNPJ") <> "U" .AND. !empty(oInfdoc:cDESTCNPJ)
                                If SM0->M0_CGC <> oInfdoc:cDESTCNPJ
                                    lDestcnpj:= .F.
                                EndIf
                            EndIf

                            // Caso o doc sincronizado tenha TPEVENTO não deve ir pra tabela C00
                            If !cCodEvento $ "411500|411501|411502|411503" .and. lDestcnpj
                                if SincAtuDados(cChave,cSitConf,cCancNSU)
                                    aadd(aChave, cChave)
                                    lOk := .T.
                                endif
                            EndIf
                        EndIf
                    Next

                    If lOk
                        For nZ := 1 To Len( aChave )

                            AADD( aProc, aChave[nZ] )

                            If Len( aProc ) >= 30
                                MonitoraManif(aProc,cAmbiente,cIdEnt,cUrl)
                                aProc := {}
                            Endif

                        Next
                        If Len( aProc ) > 0
                            MonitoraManif(aProc,cAmbiente,cIdEnt,cUrl)
                        Endif
                    EndIf

                    If Type("oWs:OWSSINCRONIZARDOCUMENTOSRESULT:CINDCONT") <> "U"

                        If oWs:OWSSINCRONIZARDOCUMENTOSRESULT:CINDCONT == "0"
                            lContinua := .F.
                        endif
                    else
                        lContinua := .F.
                    endif

                    If Empty(aDocs) .And. !lContinua .And. !lOk
                        cAlert:= STR0437 //"Não há documentos para serem sincronizados"
                        Aviso("Sincronização",cAlert,{"OK"},3)
                    EndIF

                    if lContinua .And. !lProcAll .And. !lRefazSinc
                        lContinua := MsgYesNo("Ainda existem documentos na SEFAZ a serem sincronizados, deseja solicitar novamente a sincronização ?")
                    endif
                    Sleep(2000)*/
                EndIf
            Else
                Aviso("SPED",IIf(Empty(GetWscError(3)),GetWscError(1),GetWscError(3)),{"OK"},3)
                lContinua := .F.
            EndIf
        ENDDO
    EndIf
RETURN


//-------------------------------------------------------------------------------------------
/*/{Protheus.doc} getAmbMde()

retorna ambiente de configuração do Md-e

@param

@return cAmbiente		Ambiente
/*/
//-------------------------------------------------------------------------------------------
static function getAmbMde()

    local cAmbiente := ""
    local cURL		:= PadR(GetNewPar("MV_SPEDURL","http://"),250)
    local oWs
    local lUsacolab := UsaColaboracao("4")

    if !lUsacolab .and. CTIsReady(cURL,1,.t.,lUsacolab)
        oWs :=WSMANIFESTACAODESTINATARIO():New()
        oWs:cUserToken   := "TOTVS"
        oWs:cIDENT	     := retIdEnti(lUsacolab)
        oWs:cAMBIENTE	 := ""
        oWs:cVERSAO      := ""
        oWs:_URL         := AllTrim(cURL)+"/MANIFESTACAODESTINATARIO.apw"
        oWs:CONFIGURARPARAMETROS()
        cAmbiente		 := oWs:OWSCONFIGURARPARAMETROSRESULT:CAMBIENTE

        freeObj(oWs)
        oWs := nil

    endif

return cAmbiente
