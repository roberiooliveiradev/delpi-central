#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TOTVS.CH"
#INCLUDE "RESTFUL.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"
#Include 'FWMVCDef.ch'


user function MT120USR()
    Local lRet := .t.
    Local cEol := chr(10)
    Local lVazio := ParamIxb[1]
    if lVazio
        cMsg := "Prezado Comprador!"+cEol
        cMsg += "Não é possivel inserir Pedido de Compra sem Solicitação de Compras. "+cEol
        cMsg += "Gentileza revisar o Pedido"+cEol
        if dA120Emis >= STOD('20250206')
            lRet := .f.
            cMsg += "Pedidos com Emissão Posterior a 05/02/2025 é obrigatorio o Preenchimento da Solicitação no Pedido"
        Endif
        FWAlertError(cMsg, "Delpi Compras")

    Endif

Return lRet
