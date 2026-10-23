#include 'protheus.ch'
#include 'parmtype.ch'


User Function A010TOK()
	Local aArea 	:= GetArea()
	Local cEol 		:= chr(10)
	Local lRet 		:= .t.
	Local cDscPrd 	:= ""
	Local cDscB1 	:= ""
	Local cCodPrd 	:= ""
	Local cTipo 	:= ""
	Local cRohs 	:=""
	Local oModel
	Local n1
	Local nLTF01 	:= 30
	Local nLTF02 	:= 37
	Local nLELMAPS  := 0.010
	Local nLELM 	:= 0.001
	Local cUsMpLib  := SuperGetMV("MV_ZUSMPLB",.F.," ")

	oModel := FwModelActive()

	cTipo := oModel:GetValue("SB1MASTER","B1_TIPO")

	if (INCLUI .Or. ALTERA) .And. cTipo == "MP" .And. lRet
		if !(RetCodUsr() $ AllTrim(cUsMpLib))
			lRet := .f.
			FWAlertWarning("Usuário sem permissão para cadastrar/alterar produtos do tipo MP.", "Delpi")
		endif
	endif

	If ALLTRIM(cEmpAnt) $ "03_04"



		cCodPrd := oModel:GetValue("SB1MASTER","B1_COD")
		cDscB1 := oModel:GetValue("SB1MASTER","B1_DESC")
		cDscPrd := U_DL04A02(cCodPrd)

		if !Empty(cDscPrd)
			oModel:SetValue("SB1MASTER","B1_YDLPDSC",cDscPrd)
		Else
			oModel:SetValue("SB1MASTER","B1_YDLPDSC",cDscB1)
		endif

	Endif
	If ALLTRIM(cEmpAnt) $ "01_05"
		cRohs := oModel:GetValue("SB1MASTER","B1_YHOHS")

		IF cTipo $ "MP"  .and. empty(cRohs)

			lRet := .f.
			msgstop("Tipo de Produto MP | Gentileza Preencher o campo Rohs!")

		ENDIF
		cApro := oModel:GetValue("SB1MASTER","B1_APROPRI")
		IF cTipo $ "MP"  .and. cApro != 'I'
			msgstop("Tipo de Produto MP | Deve ser Apropriação -> Indireta!")
		ENDIF

	ENDIF

	IF (INCLUI)

		IF cTipo == "MP"

			oModel:SetValue("SB1MASTER","B1_APROPRI","I")

		Else //cTipo <> ''

			oModel:SetValue("SB1MASTER","B1_APROPRI","D")

		Endif

	ENDIF

	// validações APS
	// SE O TIPO DE PRODUTO FOR MP / PI / PA
	IF (INCLUI .OR. ALTERA) .and. ALLTRIM(cEmpAnt) $ "01" .and. cTipo $"MP_PI_PA" .and. lRet
		aFilial := FWAllFilial("","01")

		if cTipo $"PA" .and. Empty(oModel:GetValue("SB1MASTER","B1_ZDLPSEG"))
			cErro := "Atenção !  Produtos do tipo PA é necessario preencher a Categoria"
			FWAlertWarning(cErro ,"Delpi" )
			Return .f.

		endif
		//	oModel := FwModelActive()
		oMdlSBZ := oModel:Getmodel("SBZDETAIL")

		/*01 - Vld Campo BZ_MRP
			01 - Quando Materia Prima tem que estar nas duas filiais

			02 - quando PI ou PA
			Tem que estar preenchido
		*/
		cErro := ""
		For  n1 := 1 to Len(aFilial)
			// Na ALTERACAO trata so a filial corrente; as demais vao pro MT010ALT (evita commit multi-filial que estoura SB5010_UNQ)
			If ALTERA .And. aFilial[n1] != cFilAnt
				Loop
			EndIf
			lAPSFil := ALLTRIM(SUPERGETMV( "MV_APS", .F., "",aFilial[N1] )) $"TOTVS"
			IF lRet // validações BZ_MRP
				if !oMdlSBZ:SeekLine({{"BZ_FILIAL",aFilial[n1]} })
					/*		lRet := .f.
					cErro := "Não existe cadastro na Aba INDICADOR DE PRODUTO para a Filial "+aFilial[n1]
					*/
				else
					/*if oMdlSBZ:GetValue("BZ_MRP") != "S" .AND. cTipo =="MP"
						lRet := .f.
						cErro := "Por se tratar de MP, por gentileza corrigir o conteu?do do campo 'Entra MRP'  "
						cErro+= "para a Filial "+aFilial[n1]+" o Conteudo deve ficar S-SIM"

					ENDIF

					if EMPTY( oMdlSBZ:GetValue("BZ_MRP") ) .AND. cTipo $"PI_PA"
						lRet := .f.
						cErro := "Preenchimento do campo  'Entra MRP'  é obrigatorio para este tipo de produto."+cEol
						cErro += "para a Filial "+aFilial[n1]

					ENDIF*/
				ENDIF

			ENDIF

			IF oModel:GetValue("SB1MASTER","B1_TIPO") $ "PC_RL_UN"
				nLELMAPS := 1
				nLELM := 1
			ENDIF
			IF oModel:GetValue("SB1MASTER","B1_TIPO") $ "PI_PA_MP"
				if !oMdlSBZ:SeekLine({{"BZ_FILIAL",aFilial[n1]} })

					if  EMPTY(oMdlSBZ:GetValue("BZ_FILIAL"))
						oMdlSBZ:SetValue("BZ_FILIAL",aFilial[n1])
					else
						oMdlSBZ:AddLine()
						oMdlSBZ:SetValue("BZ_FILIAL",aFilial[n1])
					ENDIF

				ENDIF
				if  oMdlSBZ:GetValue("BZ_MRP") != "S"  .AND. cTipo $"MP"
					oMdlSBZ:SetValue("BZ_MRP","S")
				ENDIF

				IF lAPSFil .AND.  oMdlSBZ:GetValue("BZ_MRP") != "S"  .AND. cTipo $"PI_PA"
					IF EMPTY(oMdlSBZ:GetValue("BZ_LOCPAD")) .or. oMdlSBZ:GetValue("BZ_LOCPAD") !="01"
						oMdlSBZ:SetValue("BZ_LOCPAD","01")
					ENDIF
				ENDIF
			ENDIF
			IF lRet // validações BZ_PE / BZ_TIPE


				IF aFilial[N1] =="01" .AND.  cTipo =="MP" .AND.  EMPTY( oMdlSBZ:GetValue("BZ_PE") ) //.AND. oMdlSBZ:SeekLine({{"BZ_FILIAL",aFilial[n1]} })
					oMdlSBZ:SetValue("BZ_PE", nLTF01)
				ENDIF
				IF aFilial[N1] =="02" .AND.  cTipo =="MP" .AND.  EMPTY( oMdlSBZ:GetValue("BZ_PE") ) //.AND. oMdlSBZ:SeekLine({{"BZ_FILIAL",aFilial[n1]} })
					oMdlSBZ:SetValue("BZ_PE", nLTF02)
				ENDIF
				IF aFilial[N1] =="01" .AND.  cTipo =="MP" .AND.  EMPTY( oMdlSBZ:GetValue("BZ_TIPE") )// .AND. oMdlSBZ:SeekLine({{"BZ_FILIAL",aFilial[n1]} })
					oMdlSBZ:SetValue("BZ_TIPE", "D")
				ENDIF
				IF aFilial[N1] =="02" .AND.  cTipo =="MP" .AND.  EMPTY( oMdlSBZ:GetValue("BZ_TIPE") ) //.AND. oMdlSBZ:SeekLine({{"BZ_FILIAL",aFilial[n1]} })
					oMdlSBZ:SetValue("BZ_TIPE", "D")
				ENDIF
			ENDIF

			IF lRet // validações BZ_LM / BZ_LE
				oMdlSBZ:SeekLine({{"BZ_FILIAL",aFilial[n1]} })
				IF 	 cTipo $"PI_PA"  .AND. ( EMPTY( oMdlSBZ:GetValue("BZ_LM") ) )
					IF lAPSFil
						oMdlSBZ:SetValue("BZ_LM", nLELMAPS)
					ELSE
						oMdlSBZ:SetValue("BZ_LM", nLELM)
					ENDIF
				ENDIF
				IF 	 cTipo $"PI_PA"  .AND. ( EMPTY( oMdlSBZ:GetValue("BZ_LE") ) )
					IF lAPSFil
						oMdlSBZ:SetValue("BZ_LE", nLELMAPS)
					ELSE
						oMdlSBZ:SetValue("BZ_LE", nLELM)
					ENDIF
				ENDIF

			ENDIF
			if !lRet
				FWAlertWarning(cErro ,"Delpi" )
			endif
		Next n1


	ENDIF

	RestArea(aArea)

Return lRet
