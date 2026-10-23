#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

/*/{Protheus.doc}  M116ACOL
    Ponto de Entrada, Preencher o documento de origem no item

    Para validar a TES utilizada para entrada do Conhecimento de Transporte X a Tes da Nota fiscal Original
    Ambas tem que ter a configuracao de estoque iguais
05/2021 - Gabriel Araujo
/*/
USER FUNCTION M116ACOL()
	Local cAliasSD1 := PARAMIXB[1]   //-- Alias arq. NF Entrada itens
	Local nX        := PARAMIXB[2]    //-- Número da linha do aCols correspondente
	Local aDoc      := PARAMIXB[3]    //-- Vetor contendo o documento, série, fornecedor, loja e itens do documento//-- Processamento de usuário
	Local nPNfOri   := GdFieldPos("D1_NFORI",aHeader)
	Local nPSeriOri := GdFieldPos("D1_SERIORI",aHeader)
	Local nPItemOri := GdFieldPos("D1_ITEMORI",aHeader)
	Local nTmIte := getsx3cache("D1_ITEMORI","X3_TAMANHO")
	aCols[nX,nPNfOri]   :=  aDoc[1]
	aCols[nX,nPSeriOri] :=  aDoc[2]
	aCols[nX,nPItemOri] :=  (cAliasSD1)->D1_ITEM
	CONOUT("M116ACOL GDA")

Return
