#INCLUDE "PROTHEUS.CH"

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³DLP018    ºAutor  ³Microsiga           º Data ³  07/01/16   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ Gatilho a ser executado para preencher o campo de codigo   º±±
±±º          ³ de produto automaticamente ao informar o grupo de produto  º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ AP                                                        º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

User Function DLP018()

	//Local aArea   := SB1->(GetArea())
	Local aResult := {}
	Local cVar    := AllTrim(M->B1_GRUPO)
	Local nTam    := Len(cVar)
	Local cCod	  := Space(TamSx3('B1_COD')[1])

	/*If 	TCSPExist("RetCodPro") == .F.
		Conout('Erro nao foi localizado a Stored Procedure RetCodPro')
		Return cCod
	EndIF*/

	aResult := TCSPExec("RetCodPro"+cEmpAnt, nTam, cVar)

	IF Empty(aResult)
		Conout('Erro na execução da Consulta de Codigo de Produto Disponivel : '+TcSqlError())
		Alert('Erro na execução da Consulta de Codigo de Produto Disponivel : '+TcSqlError())
	ElseIf	ValType(aResult) == 'A'
		cCod := PadR(aResult[1],TamSx3('B1_COD')[1])
	EndIf
	CONOUT("teste")
	/*If	!Empty(cCod)
		SB1->(MsSeek(xFilial('SB1')+cCod))
	EndIf*/

	//RestArea(aArea)

Return cCod
