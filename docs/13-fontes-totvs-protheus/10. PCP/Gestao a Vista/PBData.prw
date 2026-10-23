#INCLUDE "Protheus.ch"
#INCLUDE "RESTFUL.CH"
#INCLUDE "PCPMONITOR.CH"

User Function PBData()
	Local nCodVisao := PARAMIXB[1] //Código da visão
	Local cCodMon   := PARAMIXB[2] //Código do monitor
	Local nSeqVisao := PARAMIXB[3] //Sequencia do monitor na visão
	Local oJson     := PARAMIXB[4] //Estrutura do monitor

	//oJson["corfundo"]  := "RGB(124,124,124)"
	//oJson["cortitulo"] := "RGB(0,0,0)"
	//oJson["color"] := "RGB(0,0,0)"
	////oJsonRet["corTitulo"] := "RGB(0,0,0)"
	//oJson["titulo"] := "GDA"
	If nCodVisao == 1 //Verifica se está na visão correta
		If cCodMon == "000000000002" .And. nSeqVisao == 4 //Verifica se é o monitor correto
			CONOUT("STOP GDA")
		EndIf
	EndIf
	//      If cCodMon == "000000000002" .And. nSeqVisao == 1 //Verifica se é o monitor correto
	//          //Altera uma categoria do monitor
	//          oJson["series"][1]["color"]   := "red"
	//
	//          //Adiciona uma tag customizada
	//          aAdd(oJson["tags"], JsonObject():New())
	//          oJson["tags"][6]["icone"] := "po-icon-bar-code"
	//          oJson["tags"][6]["texto"] := "Tag customizada"
	//          oJson["tags"][6]["colorTexto"] := "green"
	//      EndIf
	//nSeqVisao
	//      If cCodMon == "000000000010" .And.  == 2 //Verifica se é o monitor correto
	//          //Altera uma categoria do monitor
	//          oJson["series"][1]["label"]   := "Prevista"
	//          oJson["series"][1]["color"]   := "rgb(0,0,255)"
	//          oJson["series"][1]["tooltip"] := "Ordens Previstas"
	//
	//          //Altera a cor das categorias
	//          oJson["series"][2]["color"] := "green"
	//          oJson["series"][3]["color"] := "yellow"
	//          oJson["series"][4]["color"] := "red"
	//          oJson["series"][5]["color"] := "black"
	//
	//          //Adiciona uma tag customizada
	//          aAdd(oJson["tags"], JsonObject():New())
	//          oJson["tags"][4]["icone"] := "po-icon-bar-code"
	//          oJson["tags"][4]["texto"] := "Tag customizada"
	//          oJson["tags"][4]["colorTexto"] := "green"
	//      EndIf
	//  EndIf

Return Nil
