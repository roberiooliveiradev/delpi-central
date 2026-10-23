#INCLUDE "PROTHEUS.CH"
#INCLUDE "FWMVCDEF.CH"

User Function FT300CANVWEACT()

    Local oView := PARAMIXB[1]
    Local lRetorno := .T.

//旼컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴커
//� Remove o formulario continuo da Oportunidade de Venda. �
//컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴컴켸
//oView:SetContinuousForm(.F.)

    MsgAlert("Ponto de Entrada FT300CANVWEACT.")

Return(lRetorno)