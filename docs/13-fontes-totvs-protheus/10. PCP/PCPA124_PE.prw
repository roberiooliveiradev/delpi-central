#INCLUDE 'TOTVS.CH'

/*/{Protheus.doc} PCPA124
    (Ponto de Entrada em MVC para a rotina PCPA124)
    @type user function
    @author Luan Woichechoscki
    @since 21/11/2024
/*/
User Function PCPA124()

    Local aParam   := PARAMIXB
    Local xRet     := .T.
    Local oObj     := Nil
    Local cIdPonto := ""
    Local cIdModel := ""
    Local cP124To  := SuperGetMV("MV_ZPCPTO", .F., 'pcp_ues@delpi.com.br')
    Local oProcess := Nil

    //Se tiver parâmetros
    If aParam <> NIL .AND. FUNNAME() == 'PCPA124'

        //Pega informações dos parâmetros
        oObj           := aParam[1]
        cIdPonto       := aParam[2]
        cIdModel       := aParam[3]

        If cIdPonto == "MODELCOMMITTTS"
            IF ALTERA .OR. oObj:GetOperation() == 4

                oProcess := TWFProcess():New("PCPA124","WFPCPA124" )

                oProcess:NewTask("PCPA124", "\WF\PCPA124.html")
                oProcess:cSubject := "Notificação de alteração de Roteiro:" + Alltrim(SG2->G2_CODIGO) + "/Produto:" + Alltrim(SG2->G2_PRODUTO)
                oProcess:cTo      := cP124To
                oProcess:cBCC     := "gabriel.araujo@totvs.com.br"

                oProcess:oHtml:ValByName("CODIGO"   , Alltrim(SG2->G2_CODIGO))
                oProcess:oHtml:ValByName("PRODUTO"  , Alltrim(SG2->G2_PRODUTO))

                oProcess:Start()
                oProcess:Finish()
            EndIF
        EndIf
    EndIf

Return xRet
