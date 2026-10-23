#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"


/*/{Protheus.doc}  MT116TOK
    Ponto de Entrada, para validar a TES utilizada para entrada do Conhecimento de
    Transporte X a Tes da Nota fiscal Original

    Ambas tem que ter a configuracao de estoque iguais
05/2021 - Gabriel Araujo
/*/


USER FUNCTION MT116TOK()
	lOCAL lRet := .t.
	lOCAL aArea := getarea()
	Local aAreaSF4   := SF4->(GetArea())
	Local aAreaSD1   := SD1->(GetArea())
	lOCAL cTESPar := aParametros[12]
	Local N1 := 0
	conout("gda")
	dbSelectArea("SF4")
	dbSetOrder(1)
	SF4->(DbSeek(xFilial('SF4')+cTESPar))
	IF EMPTY(aInfAdic[10]) .OR. EMPTY(aInfAdic[11]) .OR. EMPTY(aInfAdic[12]) .OR. EMPTY(aInfAdic[13]) .AND. !(ALLTRIM(cEspecie) $ "CTE_CTEOS")
		MSGINFO("Gentileza Revisar os Campos de Origem/Destino Transporte na aba INFORMAÇÕES ADICIONAIS")
		lRet := .f.
	ENDIF
	if lRet .AND. !(ALLTRIM(cEspecie) $ "CTE_CTEOS")
		If	SF4->(Found())
			cTParEst :=  SF4->F4_ESTOQUE //f4_estoque da tes do parametro
		endif
		For N1 := 1 to Len(aCols)
			cTesAtu  := ""
			cTAtuEst :=  ""
			if !GDDeleted(N1) .and. lRet
				//verifico se a conta contabil está no pedido de venda
				cTESPar  := GDFieldGet("D1_TES",N1)
				cNfOri   := GDFieldGet("D1_NFORI",N1)
				cSerOri  := GDFieldGet("D1_SERIORI",N1)
				cItemOri := GDFieldGet("D1_ITEMORI",N1)

				SF4->(DbSeek(xFilial('SF4')+cTESPar))

				If	SF4->(Found())
					cTParEst :=  SF4->F4_ESTOQUE //f4_estoque da tes do acols
				endif


				//1 - D1_FILIAL, D1_DOC, D1_SERIE, D1_FORNECE, D1_LOJA, D1_COD, D1_ITEM, R_E_C_N_O_, D_E_L_E_T_
				dbSelectArea("SD1")
				dbSetOrder(1)

				SD1->(DbSeek(xFilial('SD1')+cNfOri+cSerOri+cFornOri+cLojaOri+ GDFieldGet("D1_COD",N1)+cItemOri ))

				If	SF4->(Found())
					cTesAtu  := SD1->D1_TES
				endif

				SF4->(DbSeek(xFilial('SF4')+cTesAtu))

				If	SF4->(Found())
					cTAtuEst :=  SF4->F4_ESTOQUE //f4_estoque da tes do acols
				endif

				cMsg := "Gentileza revisar a TES do Item/Produto "
				cMsg += ALLTRIM(GDFieldGet("D1_ITEM",N1))+"/"+ALLTRIM(GDFieldGet("D1_COD",N1)) + chr(10)
				cMsg += "Pois existem divergencias no Controle de Estoque"
				if  cTAtuEst != cTParEst
					lRet := .f.
					msgstop(cMsg,"Atenção")
				endif

			endif

		Next N1
	endif

	//IF IsInCallStack("ImpXML_Cte")
	IF (ALLTRIM(cEspecie) $ "CTE_CTEOS")
		dbSelectArea("SDS")
		dbSetorder(1)
		If msSeek(xFilial("SDS")+padl(alltrim(cNFiscal),9,'0')+cSerie+cA100For+cLoja)
			conout("gda ACHOU NA SDS")
			aNfeDanfe[14] :=  SDS->DS_TPFRETE
			//		lRet := .T.
		ENDIF
	ENDIF
//	ENDIF
	conout("gda")
	restarea(aArea)
	restarea(aAreaSF4)
	restarea(aAreaSD1)
Return lRet
