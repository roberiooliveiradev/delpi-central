#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

/***************************************************
* Adicionado por Gabriel Araujo - Totvs SC 2019/08 *
* Validação para não permitir que o estoque fique  *
* negativo pois o MV_ESTNEG foi desabilitado       *
* Documento de Entrada                             *
***************************************************/


User Function MT100LOK()        // incluido pelo assistente de conversao do AP5 IDE em 25/08/01

	Local tVolta   := .T.
	Local lPodTer  := ""
	Local cTESPCNF := GetMv("MV_TESPCNF")
	Local lVldCC   := superGetMv("MV_DVLDCC",.F.,IIF(cEmpAnt $ "01",.T.,.F.))
	Local cCFOP    := superGetMv("MV_DCFOP",.F.,"5902_6902")
	Local cDlpPrd  := superGetMv("MV_DLPTPPR",.F.,IIF(cEmpAnt $ "01","MP_PI_PA",""))
	Local cTpProd  :=""
	Local lVldNFE  := .t.
	Local cCCust   :=  GdFieldGet('D1_CC')
	Local nPosVicm  := GetPosSD1("D1_VALICM")   //DT_XMLICM

	If cTipo=='N' .and. !GDDeleted()

		sPedido := GdFieldGet('D1_PEDIDO')
		sItemPc := GdFieldGet('D1_ITEMPC')
		sCod    := GdFieldGet('D1_COD')
		sCFOP   := GdFieldGet('D1_CF')
		sLocal  := GdFieldGet('D1_LOCAL')
		sIPI    := GdFieldGet('D1_IPI')
		sICMS   := GdFieldGet('D1_PICM')
		sTes    := GdFieldGet('D1_TES')


		lPodTer := AllTrim(POSICIONE("SF4",1, xFilial("SF4") + sTes, "F4_PODER3"))
		lFin    := AllTrim(POSICIONE("SF4",1, xFilial("SF4") + sTes, "F4_DUPLIC"))
		DbSelectArea("SF4")
		SF4->(dbSetOrder(1))
		SF4->(DbSeek(xFilial("SF4")+sTes))
		If 	sLocal != '01' .and. FWIsAdmin()
			ApMsgAlert('Somente Pode Emitir Notas Para o Armazem 01!')
			Return (tVolta := .F.)
		ElseIf 	!Empty(sPedido)
			SC7->(dbSetOrder(1))
			SC7->(dbSeek(xFilial("SC7")+sPedido+sItemPc))
			If !xFilial("SC7")+sPedido+sItemPc == SC7->(C7_FILIAL+C7_NUM+C7_ITEM)
				ApMsgAlert('Nota Sem Pedido Ou Pedido Nao Autorizado a Gerar Nf.!')
				Return (tVolta := .F.)
			elseif  sTes != SC7->C7_TES // tes
				ApMsgAlert('Divergencia entre a TES do Documento X Pedido de Compra')
				Return (tVolta := .F.)
			elseif  sIPI != SC7->C7_IPI .and. SF4->F4_IPI == 'S'  // C7_IPI  x D1_IPI
				ApMsgAlert('Divergencia entre a Aliquota de IPI do Documento X Pedido de Compra')
				Return (tVolta := .F.)
			elseif sICMS != SC7->C7_PICM .and. SF4->F4_ICM == 'S' // C7_PICM x D1_PICM
				ApMsgAlert('Divergencia entre a Aliquota de ICMS do Documento X Pedido de Compra')
				Return (tVolta := .F.)
			Else
				//If 	dTos(dDataBase) < dtos(SC7->C7_DATPRF)
				If 	dTos(dDataBase) < dtos(SC7->C7_DATPRF - 6) // TSC: Delpi: 19/10/2018: Diego Kerstner: adicionada tolerancia de 5 dias, conforme solicitação da Joici.
					ApMsgAlert('Data de Previsão de Entrega (' + Dtoc(SC7->C7_DATPRF) + ') é Maior que a Data da Entrada da Nota !!!')
					Return (tVolta := .F.)
				EndIf
			EndIf
		ElseIf ((lPodTer <> "D") .and. !(sTes $ cTESPCNF)) //.and. !l103Auto
			IF !l103Auto
				ApMsgAlert('Pedido De Compra Obrigatorio!')
			ENDIF
			Return (tVolta := .F.)
		EndIf
		if lVldCC .AND. lFin == "S" //.and. !l103Auto

			cTpProd := ALLTRIM(posicione("SB1",1,XFILIAL("SB1")+sCod,"B1_TIPO"))
			lVldNFE := iif( ALLTRIM(posicione("SB1",1,XFILIAL("SB1")+sCod,"B1_YNFE")) =="1",.t.,.f.  )
			//		If  lVldCC .AND.  ( !(cTpProd $ cDlpPrd) .And. lVldPC ) .and. empty(cCCust)
			If lVldCC .and.    ( !(cTpProd $ cDlpPrd) .and. lVldNFE ) .and. empty(cCCust)

				IF !l103Auto
					ApMsgAlert('Centro de Custo Obrigatorio!')
				Endif
				Return (tVolta := .F.)

			ENDIF

		ENDIF
	EndIf
	//nVlrIcms := 1370.9
	//conout("gabriel")
	//aCols[1,nPosVicm] := nVlrIcms
	//GDFieldPut("D1_VALICM",nVlrIcms,1)
Return(tVolta)
