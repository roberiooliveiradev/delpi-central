
#INCLUDE "PROTHEUS.CH"
#INCLUDE "APWIZARD.CH"
#INCLUDE "FWADAPTEREAI.CH"
#INCLUDE 'FWMVCDEF.CH'


USER FUNCTION DLP04F02()
    Local oModal
    Local oContainer


    oModal  := FWDialogModal():New()
    oModal:SetEscClose(.T.)
    oModal:setTitle("Atualização de Produtos")
    oModal:setSubTitle("Está rotina ira atualizar o cadastro de produto na empresa escolhida com base no Produto Posicionado")

    //Seta a largura e altura da janela em pixel
    aTmBox1 := {200,140}

    conout("teste teste")

    oModal:setSize(aTmBox1[1], aTmBox1[2])

    oModal:createDialog()
    oModal:addCloseButton(nil, "Fechar")
    oContainer := TPanel():New( ,,, oModal:getPanelMain() )
    oContainer:SetCss("TPanel{background-color : lightgray;}")

    oContainer:Align := CONTROL_ALIGN_ALLCLIENT
    aTmBox2 := {30,20}
    oSay1:=   TSay():New(1,1,{|| "Produto Escolhido: "},oContainer,,,,,,.T.,,,aTmBox2[1],aTmBox2[2],,,,,,.T.)
    oSay1:lTransparent = .T.
    oModal:Activate()
Return
