#include 'protheus.ch'
#include 'parmtype.ch'


/***************************************************
* Adicionado por Gabriel Araujo - Totvs SC 2020/01 *
* Validação Centro de Custo de Despesas            *
* Pedido de Compras                                *
***************************************************/



user function MT120LOK()

	Local lRet    := .T.
	Local cMsg    := ""
	Local cEol    := chr(10)+chr(13)
	Local cProd   := Acols[n, AScan(aHeader, { |x| Alltrim(x[2]) == 'C7_PRODUTO'})]
	Local cTPPrd  := POSICIONE("SB1",1,xFilial("SB1")+cProd,"B1_TIPO")
	Local lVldCC  := superGetMv("MV_DVLDCC",.F.,IIF(cEmpAnt $ "01",.T.,.F.))
	Local cDlpPrd := superGetMv("MV_DLPTPPR",.F.,IIF(cEmpAnt $ "01","MP_PI_PA",""))
	Local cTpProd := ""
	Local cCCust  :=  GdFieldGet('C7_CC')
	Local lVldPC  := .t.
    Local aArea      := FWGetArea()
    Local aParamBox := {}
    Local aRet := {}

	//INDICE 1 A5_FILIAL, A5_FORNECE, A5_LOJA, A5_PRODUTO, A5_FABR, A5_FALOJA, R_E_C_N_O_, D_E_L_E_T_
	if !GDDeleted()
		IF alltrim(cEmpAnt) $"01_05" .AND. (cTPPrd $ "MP")
			dbSelectArea("SA5")
			dbSetOrder(1)
			IF !(dbSeek(xFilial("SA5") + cA120Forn + cA120Loj+cProd))

				lRet := .f.

				cMsg +="Fornecedor sem Amarração no Item"+cEol
				cMsg +="O Produto: "+cProd +cEol
				cMsg +="Não Pode ser comprado para o Fornecedor : "+ cA120Forn  + "/" + cA120Loj +cEol
				cMsg += AllTrim(POSICIONE('SA2', 1, xFilial('SA2') +  cA120Forn + cA120Loj , 'A2_NOME'))

				AVISO( "DELPI", cMsg,  {"OK"}, 2 ,"ATENÇÃO")



			ENDIF
			//SBD->BD_PRODUTO+SBD->BD_LOCAL+nSeq)
		ENDIF
		if  alltrim(cEmpAnt) $"01_05" .AND.  lRet
			dbSelectArea("SA5")
			SA5->(dbSetOrder(1))
			if SA5->(dbSeek(xFilial("SA5") + cA120Forn + cA120Loj+cProd))
				if SA5->A5_MSBLQL  == "1"
					lRet := .f.
					cMsg +="Fornecedor com  Item Bloqueado"+cEol
					cMsg +="O Produto: "+cProd +cEol
					cMsg +="Não Pode ser comprado para o Fornecedor : "+ cA120Forn  + "/" + cA120Loj +cEol
					cMsg += AllTrim(POSICIONE('SA2', 1, xFilial('SA2') +  cA120Forn + cA120Loj , 'A2_NOME'))

					AVISO( "DELPI", cMsg,  {"OK"}, 2 ,"ATENÇÃO")

				endif
			endif
		endif
		if lRet .AND. lVldCC

			sCod    := GdFieldGet('C7_PRODUTO')
			cTpProd := ALLTRIM(posicione("SB1",1,XFILIAL("SB1")+sCod,"B1_TIPO"))
			lVldPC := iif( ALLTRIM(posicione("SB1",1,XFILIAL("SB1")+sCod,"B1_YPC")) =="1",.t.,.f.  )
			//	if lVldCC .AND. !( cTpProd $ cDlpPrd) .and. empty(cCCust) .AND. !GDDeleted()
			If  lVldCC .AND.  ( !(cTpProd $ cDlpPrd) .And. lVldPC ) .and. empty(cCCust)
				ApMsgAlert('Centro de Custo Obrigatorio!')
				lRet := .f.
			endif

		endif
	endif

	dDATPRF := GDFIELDGET("C7_DATPRF") // original
	dZDATPRF := GDFIELDGET("C7_ZDATPR") // primeiro
	cHISTDT := iif(empty(GDFIELDGET("C7_ZHISTDT")),"",GDFIELDGET("C7_ZHISTDT")) // historico
	dDtant := GDFIELDGET("C7_ZCONTDT") // anterior

	If ! GDDeleted()
		IF Empty(dZDATPRF)
			GDFieldPut("C7_ZDATPR", dDATPRF)
			GDFieldPut("C7_ZCONTDT", dDATPRF)
		else
			If dDATPRF <> dDtant .and. dDATPRF > dDtant
				aAdd(aParamBox,{11,"Informe o motivo","",".T.",".T.",.T.})
					If ParamBox(aParamBox,"Motivo",@aRet)
						//A operação abaixo de atualizar com GDFieldPut, é o mesmo que: aCols[nLinha][nPosDatEnt] := Date()
						cHISTDT+= "Usuário: "+UsrRetName(RetCodUsr())+" / Dt Alt:"+ dtoc(Date())+ " / Anterior: "+ dtoc(dDtant)+ " / Novo: "+dtoc(dDATPRF)+" / Motivo: " +MV_PAR01 + CRLF 
						GDFieldPut("C7_ZHISTDT", cHISTDT)
					Endif
			Endif
			GDFieldPut("C7_ZCONTDT", dDATPRF)
		Endif
	EndIf   
	GetDRefresh()
	FWRestArea(aArea)

return lRet
