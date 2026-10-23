#INCLUDE 'TOTVS.CH'

/*/{Protheus.doc} PCPA200
    (Ponto de Entrada em MVC para a rotina PCPA200)
    @type user function
    @author Luan Woichechoscki
    @since 21/11/2024
/*/
User Function PCPA200()

    Local aParam   := PARAMIXB
    Local xRet     := .T.
    Local oObj     := Nil
    Local cIdPonto := ""
    Local cIdModel := ""
    Local cPCPTo  := SuperGetMV("MV_ZPCPTO", .F., 'pcp_ues@delpi.com.br')
    Local oProcess := Nil

    //Se tiver parâmetros
    If aParam <> NIL .AND. FUNNAME() == 'PCPA200' .and. cEmpAnt =="01"

        //Pega informações dos parâmetros
        oObj           := aParam[1]
        cIdPonto       := aParam[2]
        cIdModel       := aParam[3]

        If cIdPonto == "MODELCOMMITTTS"
            IF ALTERA .OR. oObj:GetOperation() == 4

                oProcess := TWFProcess():New("PCPA200", "WFPCPA200")

                oProcess:NewTask("WFPCPA200", "\WF\PCPA200.html")
                oProcess:cSubject := "Notificação de alteração de Estrutura:" + Alltrim(SG1->G1_COD)
                oProcess:cTo      := cPCPTo
                oProcess:cBCC     := "gabriel.araujo@totvs.com.br"

                oProcess:oHtml:ValByName("CODIGO"   , Alltrim(SG1->G1_COD))
                oProcess:oHtml:ValByName("DESCRI"   , Alltrim(SG1->G1_OBSERV))

                oProcess:Start()
                oProcess:Finish()
            EndIF
        EndIf
    EndIf

Return xRet
