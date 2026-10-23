#INCLUDE "PROTHEUS.CH"

User Function A460TUNI()
    Local cCod     := ParamIXB[1] //-- Codigo do Produto
    Local cLocOrig := ParamIXB[2] //-- Conteúdo do parâmetro MV_ALMTERC
    Local dDataFech := ParamIXB[3] //-- Data de Fechamento
    Local cArqTemp := ParamIXB[4]
    //-- Nome do Arquivo de Trabalho utilizado no Relatorio
    Local nTotal   := 0
    Local nVlrUnit := 0
    Local nQuant   := 0
    //-- Ajustes realizados pelo cliente para os campos TOTAL, VALOR_UNIT e QUANTIDADE, que serão utilizado na composição do relatorio.TOTAL := nTotalVALOR_UNIT  :=  nVlrUnitQUANTIDADE  := nQuant

    conout( cCod+  cvaltochar((cArqTemp)->TOTAL	))

Return Nil
