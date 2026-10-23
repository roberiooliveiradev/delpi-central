#Include 'Protheus.ch'
#Include 'TOPConn.ch'
#Include 'COMXCOL.ch'
#Include "FILEIO.CH"
#Include "TbiConn.ch"
#Include 'RwMake.ch'
#Include "FWEVENTVIEWCONSTS.CH"
#INCLUDE 'FWLIBVERSION.CH'

Static oColOK   := LoadBitmap(,'LBOK')
Static oColNO   := LoadBitmap(,'LBNO')
Static oGreen   := LoadBitmap(,'BR_VERDE')
Static oRed	    := LoadBitmap(,'BR_VERMELHO')
Static lLGPDCOL	:= FindFunction("SuprLGPD") .And. SuprLGPD()

//-------------------------------------------------------------------
/*/{Protheus.doc} COMXCOL
Fonte com as funcoes do monitor e engines de Compras para
TOTVS Colaboracao ou Importador XML

@author	Andre Anjos
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function COMXCOL()

	Local aCores  	:= {}
	Local aCoresNew	:= {}
	Local lRet    	:= .T.
	Local lInverte  := .F.
	Local lCOMXACOR	:= ExistBlock("COMXACOR")
	Local cFilBrw 	:= ""
	Local lMVImpXML	:= SuperGetMv("MV_IMPXML",.F.,.F.) .And. CKO->(FieldPos("CKO_ARQXML")) > 0 .And. !Empty(CKO->(IndexKey(5)))
	Local lCkoRepro := CKO->(FieldPos("CKO_DOC")) > 0 .And. CKO->(FieldPos("CKO_SERIE")) > 0 .And. CKO->(FieldPos("CKO_NOMFOR")) > 0 .And. !Empty(SDS->(IndexKey(4))) .And. COLX1COLREP()

	Private aRotina	  := MenuDef()
	Private cMarca	  := GetMark()
	Private cCadastro := Iif(lMVImpXML,STR0190,STR0001) //-- "Importador XML" ## Monitor TOTVS Colaboração
	Private aRegMark  := {}
	Private lToma4NFOri	:= .T.
	Private cFilQry     := ''

	//³ mv_par01: Documento de 					³
	//³ mv_par02: Documento ate 				³
	//³ mv_par03: Serie de 						³
	//³ mv_par04: Serie ate 					³
	//³ mv_par05: Fornecedor de 				³
	//³ mv_par06: Fornecedor ate 				³
	//³ mv_par07: Emissao de 					³
	//³ mv_par08: Emissao ate 					³
	//³ mv_par09: Importacao de 				³
	//³ mv_par10: Importacao ate 				³
	//³ mv_par11: Mostra gerados: 1=Sim ; 2=Nao	³
	//³ mv_par12: Quanto ao PC					³

	If lRet .And. Pergunte("MTA140I",.T.)
		aAdd(aCores,{'DS_STATUS == "P"','BR_VERMELHO'})	// -- "Documento Gerado"
		aAdd(aCores,{'DS_STATUS == "E"','BR_PRETO'})	// -- "Documento c/ Ocorrência"
		aAdd(aCores,{'DS_TIPO $ "NF"','BR_VERDE'})		// -- "Documento Normal, F = Documento em Processamento (Status retirado em 24/06/2020)"
		aAdd(aCores,{'DS_TIPO == "O"','BR_AZUL'})		// -- "Docto. de Bonificação"
		aAdd(aCores,{'DS_TIPO == "D"','BR_AMARELO'})	// -- "Docto. de Devolução"
		aAdd(aCores,{'DS_TIPO == "B"','BR_CINZA'})		// -- "Docto. de Beneficiamento"
		aAdd(aCores,{'DS_TIPO == "C"','BR_PINK'})		// -- "Docto. de Compl. Preço/Qtde"
		aAdd(aCores,{'DS_TIPO == "T"','BR_LARANJA'})	// -- "Docto. de Transporte"

		//Ponto de Entrada para incluir/alterar opcoes de cores de legenda no Browse
		If lCOMXACOR
			aCoresNew := ExecBlock("COMXACOR",.F.,.F.,{aCores})
			If ValType(aCoresNew) == "A"
				aCores := aCoresNew
			EndIf
		EndIf

		//-- Monta filtro ISAM
		cFilBrw := 'DS_DOC >= "' +mv_par01 +'" .And. DS_DOC <= "' +mv_par02 +'" .And. '
		cFilBrw += SerieNfId("SDS",3,"DS_SERIE") + ' >= "' +mv_par03 +'" .And. ' + SerieNFId("SDS",3,"DS_SERIE") + '<= "' +mv_par04 +'" .And. '
		cFilBrw += 'DS_FORNEC >= "' +mv_par05 +'" .And. DS_FORNEC <= "' +mv_par06 +'" .And. '
		cFilBrw += 'DToS(DS_EMISSA) >= "'  +DToS(mv_par07) +'" .And. DToS(DS_EMISSA) <= "'  +DToS(mv_par08) +'" .And. '
		cFilBrw += 'DToS(DS_DATAIMP) >= "'  +DToS(mv_par09) +'" .And. DToS(DS_DATAIMP) <= "'  +DToS(mv_par10) +'"'

		If mv_par11 == 2
			cFilBrw += ' .And. DS_STATUS <> "P"'
		EndIf

		// ATENCAO:
		// Filtro identico ao feito acima, mas em sintaxe SQL. Quando alterar o filtro acima,
		// incluir o mesmo criterio na query abaixo.
		cFilQry := "DS_DOC >= '" + mv_par01 + "' AND DS_DOC <= '" + mv_par02 + "' AND "
		cFilQry += SerieNfId("SDS",3,"DS_SERIE") + " >= '" + mv_par03 + "' AND " + SerieNfId("SDS",3,"DS_SERIE") + " <= '" + mv_par04 + "' AND "
		cFilQry += "DS_FORNEC >= '" + mv_par05 + "' AND DS_FORNEC <= '" + mv_par06 + "' AND "
		cFilQry += "DS_EMISSA >= '" + DToS(mv_par07) + "' AND DS_EMISSA <= '" + DToS(mv_par08) + "' AND "
		cFilQry += "DS_DATAIMP >= '" + DToS(mv_par09) + "' AND DS_DATAIMP <= '" + DToS(mv_par10) + "'"

		If MV_PAR11 == 2
			cFilQry += " AND DS_STATUS <> 'P'"
		EndIf

		If lCkoRepro
			SetKey(VK_F9,{|| COLATUBRW()})
			SetKey(VK_F10,{|| Pergunte("COLREP",.T.)})
		Endif

		MsgRun(STR0002,STR0003,{|| CursorWait(),CursorArrow(),MarkBrow("SDS","DS_OK",'DS_STATUS == "P"',,lInverte,cMarca,'COLREPCLICK()',,,,'COLREPCLICK(7)',,,,aCores,,,cFilBrw)}) //-- Aplicando filtros e preparando inferface... # Aguarde

		//Limpando a marca ao sair da tela
		COLREPCLICK(6)
	EndIf

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} COLATUBRW
Atualiza browse

@author	rodrigo.mpontes
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function COLATUBRW()

	Local oObjMBrw := Nil

	oObjMBrw := GetMarkBrow()

	If ValType(oObjMBrw) <> 'U'
		oObjMBrw:oBrowse:GoTop()
		oObjMBrw:oBrowse:Refresh()
	Endif

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} MenuDef
Menu Totvs Colaboração / Importador XML

@author	Andre Anjos
@since 05/06/12
/*/
//-------------------------------------------------------------------

Static Function MenuDef()

	Local aRotAlt	:= {}
	Local lCOMCOLRT	:= ExistBlock("COMCOLRT")

	PRIVATE aRotina	:= {}

	aAdd(aRotina,{STR0039	,"PesqBrw"	,0,1,0,.F.}) 	// Pesquisar
	aAdd(aRotina,{STR0052	,"COMCOLVIS",0,2,0,NIL})	// Visualizar
	aAdd(aRotina,{STR0193	,"COMCOLVIN",0,4,0,nil})	// Alterar/Vinc. Docto
	aAdd(aRotina,{STR0054	,"COMCOLGER",0,4,0,nil}) 	// Gerar Docto
	aAdd(aRotina,{STR0056	,"COMCOLEXC",0,4,0,nil})   	// Excluir
	aAdd(aRotina,{STR0057	,"COMCOLREP",0,3,0,nil})	// Reprocessar
	aAdd(aRotina,{STR0051	,"COMCOLLEG",0,5,0,.F.})	// Legenda

	//Ponto de entrada para inclusão de novos itens no menu aRotina
	If lCOMCOLRT
		aRotAlt := ExecBlock("COMCOLRT",.F.,.F.,{aRotina})
		If ValType(aRotAlt) == 'A'
			aRotina := aRotAlt
		Endif
	Endif

Return aRotina

//-------------------------------------------------------------------
/*/{Protheus.doc} COMCOLVIS
Visualizar documento do monitor.

@author	Andre Anjos
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function COMCOLVIS()
Return MontaTela(2)

//-------------------------------------------------------------------
/*/{Protheus.doc} COMCOLVIN
Alterar/Vincular documento com pedidos/nf de origem.

@author	Andre Anjos
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function COMCOLVIN()

	Local lRet := .T.

	If SDS->DS_STATUS == "P"
		Aviso(STR0004,STR0005,{"OK"}) //-- Atenção # Esta ação não pode ser executada para documentos já gerados.
		lRet := .F.
	EndIf

	If lRet
		lRet := MontaTela(4)
	EndIf

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} COMITIG
Busca por produto iguais em itens diferentes na NF original

@author	Rodrigo M Pontes
@since 09/02/17
/*/
//-------------------------------------------------------------------

Static Function COMITIG(cForDel,cLojDel,cDocDel,cSerDel,cFil)

	Local cQuery	:= ""
	Local cITIG		:= GetNextAlias()
	Local cIGIT		:= GetNextAlias()
	Local aRet		:= {}

	cQuery := " SELECT DT_COD,"
	cQuery += "        Count(*) AS QTD_PRD"
	cQuery += " FROM " + RetSqlName("SDT")
	cQuery += " WHERE DT_FILIAL = '" + cFil + "'"
	cQuery += " AND DT_FORNEC = '" +cForDel + "' AND DT_LOJA = '" +cLojDel + "'"
	cQuery += " AND DT_DOC = '" +cDocDel + "' AND DT_SERIE = '" +cSerDel + "'"
	cQuery += " AND DT_ORIGIN = '1'"
	cQuery += " AND D_E_L_E_T_ = '*'"
	cQuery += " GROUP  BY DT_COD"
	cQuery += " HAVING Count(*) > 1"

	cQuery := ChangeQuery(cQuery)

	dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQuery),cITIG,.T.,.T.)

	While (cITIG)->(!EOF())
		aAdd(aRet,(cITIG)->DT_COD)
		(cITIG)->(DbSkip())
	Enddo

	(cITIG)->(DbCloseArea())

	If Len(aRet) == 0
		cQuery := " SELECT DT_COD,"
		cQuery += "        Count(*) AS QTD_PRD"
		cQuery += " FROM " + RetSqlName("SDT")
		cQuery += " WHERE DT_FILIAL = '" + cFil + "'"
		cQuery += " AND DT_FORNEC = '" +cForDel + "' AND DT_LOJA = '" +cLojDel + "'"
		cQuery += " AND DT_DOC = '" +cDocDel + "' AND DT_SERIE = '" +cSerDel + "'"
		cQuery += " AND DT_ORIGIN = ' '"
		cQuery += " AND D_E_L_E_T_ = ' '"
		cQuery += " GROUP  BY DT_COD"
		cQuery += " HAVING Count(*) > 1"

		cQuery := ChangeQuery(cQuery)

		dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQuery),cIGIT,.T.,.T.)

		While (cIGIT)->(!EOF())
			aAdd(aRet,(cIGIT)->DT_COD)
			(cIGIT)->(DbSkip())
		Enddo

		(cIGIT)->(DbCloseArea())
	Endif

Return aRet

//-------------------------------------------------------------------
/*/{Protheus.doc} GDNFORIG
Busca pelo NF original, quando foi importada.

@author	Rodrigo M Pontes
@since 09/02/17
/*/
//-------------------------------------------------------------------

Static Function GDNFORIG(aNoFields,cForDel,cLojDel,cDocDel,cSerDel,nTNF)

	Local cQuery		:= ""
	Local nX			:= 0
	Local aColsNFORIG	:= {}

	Default nTNF := 0

	If Select("GDNF") > 0
		GDNF->(DbCloseArea())
	Endif

	If Len(aHeader) == 0
		aHeader := COMXHDCO("SDT",,aNoFields)
	Endif

	For nX := 1 To Len(aHeader)
		If aHeader[nX,10] <> "V"
			If Empty(cQuery)
				cQuery := " SELECT DISTINCT " + AllTrim(aHeader[nX,2])
			Else
				cQuery += " , " + AllTrim(aHeader[nX,2])
			Endif
		Endif
	Next nX

	cQuery += " FROM " + RetSqlName("SDT")
	cQuery += " WHERE DT_FILIAL = '" +xFilial("SDT") + "' "
	cQuery += " AND DT_FORNEC = '" +cForDel + "' AND DT_LOJA = '" +cLojDel + "'"
	cQuery += " AND DT_DOC = '" +cDocDel + "' AND DT_SERIE = '" +cSerDel + "'"
	cQuery += " AND DT_ORIGIN = '1' AND D_E_L_E_T_ = '*' "
	cQuery := ChangeQuery(cQuery)

	dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQuery),"GDNF",.T.,.T.)

	DbSelectArea("GDNF")
	If GDNF->(!EOF())
		While GDNF->(!EOF())
			AAdd(aColsNFORIG,Array(Len(aHeader)+1))

			For nX := 1 to Len(aHeader)
				If aHeader[nX,10] <> "V"
					If IsHeadRec(aHeader[nX][2])
						aColsNFORIG[Len(aColsNFORIG)][nX] := 0
					ElseIf IsHeadAlias(aHeader[nX][2])
						aColsNFORIG[Len(aColsNFORIG)][nX] := "SDT"
					Else
						aColsNFORIG[Len(aColsNFORIG)][nX] := &("GDNF->"+aHeader[nX][2])
					EndIf
					aColsNFORIG[Len(aColsNFORIG)][Len(aHeader)+1] := .F.
				Endif
			Next nX

			GDNF->(DbSkip())
		Enddo
	Endif

	GDNF->(DbCloseArea())

	If Len(aColsNFORIG) == 0
		If Select("NFGD") > 0
			NFGD->(DbCloseArea())
		Endif

		cQuery := ""
		For nX := 1 To Len(aHeader)
			If aHeader[nX,10] <> "V"
				If Empty(cQuery)
					cQuery := " SELECT DISTINCT " + AllTrim(aHeader[nX,2])
				Else
					cQuery += " , " + AllTrim(aHeader[nX,2])
				Endif
			Endif
		Next nX

		cQuery += " FROM " + RetSqlName("SDT")
		cQuery += " WHERE DT_FILIAL = '" +xFilial("SDT") + "' "
		cQuery += " AND DT_FORNEC = '" +cForDel + "' AND DT_LOJA = '" +cLojDel + "'"
		cQuery += " AND DT_DOC = '" +cDocDel + "' AND DT_SERIE = '" +cSerDel + "'"
		cQuery += " AND DT_ORIGIN = ' ' AND D_E_L_E_T_ = ' ' "
		cQuery := ChangeQuery(cQuery)

		dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQuery),"NFGD",.T.,.T.)

		DbSelectArea("NFGD")
		If NFGD->(!EOF())
			While NFGD->(!EOF())
				AAdd(aColsNFORIG,Array(Len(aHeader)+1))

				For nX := 1 to Len(aHeader)
					If aHeader[nX,10] <> "V"
						If IsHeadRec(aHeader[nX][2])
							aColsNFORIG[Len(aColsNFORIG)][nX] := 0
						ElseIf IsHeadAlias(aHeader[nX][2])
							aColsNFORIG[Len(aColsNFORIG)][nX] := "SDT"
						Else
							aColsNFORIG[Len(aColsNFORIG)][nX] := &("NFGD->"+aHeader[nX][2])
						EndIf
						aColsNFORIG[Len(aColsNFORIG)][Len(aHeader)+1] := .F.
					Endif
				Next nX

				NFGD->(DbSkip())
			Enddo
		Endif

		NFGD->(DbCloseArea())
	Endif

Return aColsNFORIG

//-------------------------------------------------------------------
/*/{Protheus.doc} MontaTela
Monta interface de visualização e vinculo do documeto.

@author	Microsiga
@since 05/06/12
/*/
//-------------------------------------------------------------------

Static Function MontaTela(nOpc)

	Local lRet   		:= .F.
	Local lCOMCOLSD		:= ExistBlock("COMCOLSD")
	Local oDlg      	:= NIL
	Local oEnchoice 	:= NIL
	Local oFolder		:= NIL
	Local oComboFrt 	:= NIL
	Local oSize     	:= FwDefSize():New()
	Local aCpsAlt		:= If(nOpc == 4,{"DT_NFORI","DT_SERIORI","DT_ITEMORI","DT_TES","DT_QTSEGUM","DT_LOCAL"},{})
	Local aUsrCpo		:= {}
	Local aNoFields 	:= {}
	Local aButtons  	:= {}
	Local aPosCab   	:= {}
	Local aPosIts   	:= {}
	Local aPosRdp		:= {}
	Local aFolders  	:= {STR0007,STR0008,STR0009,STR0010,STR0011,STR0012,STR0184} //-- Totais # Dados DANFE # Dados da NF-e # Dados da Importação # Dados da Geração # Ocorrência # Impostos
	Local cSeek	    	:= ""
	Local bWhile		:= {|| SDT->(DT_FILIAL+DT_FORNEC+DT_LOJA+DT_DOC+DT_SERIE)}
	Local nTotDoc		:= IF(SDS->(FieldPos("DS_TOTAL")) > 0, SDS->DS_TOTAL,Iif(SDS->DS_TIPO<>"T",SDS->(DS_VALMERC+DS_DESPESA+DS_FRETE+DS_SEGURO-DS_DESCONT),SDS->(DS_VALMERC+DS_DESPESA+DS_SEGURO-DS_DESCONT)))
	Local nX			:= 0
	Local nY			:= 0
	Local nMultPC		:= 0
	Local nPosPed		:= 0
	Local nPosItPC		:= 0
	Local nPDTITEM		:= 0
	Local nPDTDESC		:= 0
	Local nPDTCOD		:= 0
	Local nTB1COD		:= 0
	Local nPDTNFORI 	:= 0
	Local nPDTSERIORI	:= 0
	Local nPDTITEMORI	:= 0
	Local nPDTTES		:= 0
	Local nPDTTESIPI	:= 0
	Local nPDTTESICM	:= 0
	Local nPDTTESISS	:= 0
	Local nPDTTESPIS	:= 0
	Local nPDTTESCOF	:= 0
	Local nPDTTESICST	:= 0
	Local nPDTALIQIPI	:= 0
	Local nPDTALIQICM	:= 0
	Local nPDTALIQISS	:= 0
	Local nPDTALIQPIS	:= 0
	Local nPDTALIQCOF	:= 0
	Local nPDTALIICST	:= 0
	Local aColsAnt  := {}
	Local cFilBkp   := cFilAnt
	Local lRemet	:= .F.
	Local lGrava	:= .T.
	Local cFilSDT	:= xFilial("SDT")
	Local nPosDTPED	:= 0
	Local nPosDTItPC := 0

	Private aHeader		:= {}
	Private aCols		:= {}
	Private aHeadImp	:= {}
	Private aColsImp	:= {}
	Private oGetDados	:= NIL
	Private oNewGet		:= NIL

	//-- Se filial diferente, troca
	If PadR(cFilAnt,Len(AllTrim(SDS->DS_FILIAL))) # AllTrim(SDS->DS_FILIAL)
		Do Case
			Case FWModeAccess("SB2",3) == "E"
				cFilAnt := SDS->DS_FILIAL
			Case FWModeAccess("SB2",2) == "E" .Or. FWModeAccess("SB2",1) == "E"
				SM0->(dbSetOrder(1))
				SM0->(dbSeek(cEmpAnt+SDS->DS_FILIAL))
				cFilAnt := SM0->M0_CODFIL
		EndCase
	EndIf

	cSeek := cFilSDT+SDS->(DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)

	oSize:AddObject("CABEC",100,20,.T.,.T.) // Totalmente dimensionavel
	oSize:AddObject("ITENS",100,40,.T.,.T.) // Totalmente dimensionavel
	oSize:AddObject("RODAP",100,40,.T.,.T.) // Totalmente dimensionavel
	oSize:lProp := .T. 						 // Proporcional
	oSize:aMargins := {0,0,0,3}			  	 // Espaco ao lado dos objetos 0, entre eles 3
	oSize:Process() 	   					 // Dispara os calculos de coordenadas

	aPosCab := {oSize:GetDimension("CABEC","LININI"),oSize:GetDimension("CABEC","COLINI"),;
		oSize:GetDimension("CABEC","LINEND"),oSize:GetDimension("CABEC","COLEND")}
	aPosIts := {oSize:GetDimension("ITENS","LININI"),oSize:GetDimension("ITENS","COLINI"),;
		oSize:GetDimension("ITENS","LINEND"),oSize:GetDimension("ITENS","COLEND")}
	aPosRdp := {oSize:GetDimension("RODAP","LININI"),oSize:GetDimension("RODAP","COLINI"),;
		oSize:GetDimension("RODAP","LINEND"),oSize:GetDimension("RODAP","COLEND")}

	//-- Tratamento para que seja possivel alterar os campos da nota origem
	If nOpc == 4 .And. SDS->DS_TIPO $ "DC"
		aRotina[2,4] := 6
	EndIf

	// Verifica se e CT-e e se e remetente da mercadoria (saida), neste caso deve exibir os campos para vinculo com pedido
	If SDS->DS_TIPO == "T" .And. SDS->DS_TPFRETE == "C"
		lRemet := .T.
	EndIf

	//-- Retira campos que nao sao usados pelo tipo de documento
	If SDS->DS_TIPO $ "DC"
		aNoFields := {"DT_PEDIDO","DT_ITEMPC"}
	ElseIf SDS->DS_TIPO == "N"
		aNoFields := {"DT_NFORI","DT_SERIORI","DT_ITEMORI"}
	ElseIf SDS->DS_TIPO == "T"
		If lRemet
			aNoFields := {"DT_PRODFOR","DT_DESCFOR","DT_NFORI","DT_SERIORI","DT_ITEMORI"}
		Else
			aNoFields := {"DT_PRODFOR","DT_DESCFOR","DT_PEDIDO","DT_ITEMPC","DT_NFORI","DT_SERIORI","DT_ITEMORI"}
		EndIf
	Else
		aNoFields := {"DT_PEDIDO","DT_ITEMPC","DT_NFORI","DT_SERIORI","DT_ITEMORI"}
	EndIf

	RegToMemory("SDS",.F.,.T.)

	//nOpc = 6 ->Nota Original
	If nOpc <> 6
		FillGetDados(2,"SDT",3,cSeek,bWhile,,aNoFields,,,,,.F.,@aHeader,@aCols,{||ColAtuLeg(@aHeader,@aCols)})
	Else
		aCols := GDNFORIG(aNoFields,SDS->DS_FORNEC,SDS->DS_LOJA,SDS->DS_DOC,SDS->DS_SERIE)
	Endif

	//-- Limpa descrição do campo para ajustar tamanho na tela.
	If (nPosLeg:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_LEGENDA"})) > 0
		aHeader[nPosLeg][1] := ""
	Endif

	nPDTITEM	:= GDFieldPos("DT_ITEM",aHeader)
	nPDTDESC	:= GdFieldPos("DT_DESC",aHeader)
	nPDTCOD		:= GdFieldPos("DT_COD",aHeader)
	nTB1COD		:= TamSx3("B1_COD")[1]

	aSort(aCols,,,{|x,y| x[nPDTITEM] < y[nPDTITEM]}) //-- Ordena por item

	For nX := 1 To Len(aCols)
		If nPDTDESC > 0 .And. Empty(AllTrim(aCols[nX][nPDTDESC]))
			aCols[nX][nPDTDESC] := Posicione("SB1",1,xFilial("SB1") + PadR(aCols[nX][nPDTCOD],nTB1COD),"B1_DESC")
		Endif
	Next nX

	aUsrCpo := ComxUsrCpo(@aCpsAlt) // -- Validar campos de usuário na SDT
	aColsAnt := aClone(aCols)

	Define MsDialog oDlg From oSize:aWindSize[1],oSize:aWindSize[2] To oSize:aWindSize[3],oSize:aWindSize[4];
		Title STR0001 +" - " +If(nOpc == 2,STR0013,STR0014) Of oMainWnd Pixel //-- Monitor TOTVS Colaboração # Visualização # Vincular Documento

	oEnchoice := MsMGet():New("SDS",,2,,,,,aPosCab,,,,,,oDlg)
	oGetDados := MsNewGetDados():New(aPosIts[1],aPosIts[2],aPosIts[3],aPosIts[4],If(nOpc==4 .Or. nOpc==2 .Or. nOpc == 6,2,4),,,,aCpsAlt,,Len(aCols)/*9999*/,,,,oDlg,@aHeader,@aCols)
	oFolder   := TFolder():New(aPosRdp[1],aPosRdp[2],aFolders,,oDlg,,,,.T.,,aPosRdp[4]-aPosRdp[2],aPosRdp[3]-aPosRdp[1])

	//-- Montagem dos campos do rodape
	//-- Vlr. Mercadoria
	TSay():New(10,10,{|| RetTitle("DS_VALMERC")},oFolder:aDialogs[1],,,,,,.T.,,,50,10)
	TGet():New(08,70,{|| SDS->DS_VALMERC},oFolder:aDialogs[1],50,10,PesqPict("SDS","DS_VALMERC"),,,,,,,.T.,,,,,,,.T.,,,"DS_VALMERC")
	//-- Vlr. Frete
	TSay():New(30,10,{|| RetTitle("DS_FRETE")},oFolder:aDialogs[1],,,,,,.T.,,,50,10)
	TGet():New(28,70,{|| Iif(SDS->DS_TIPO<>"T",SDS->DS_FRETE,0)},oFolder:aDialogs[1],50,10,PesqPict("SDS","DS_FRETE"),,,,,,,.T.,,,,,,,.T.,,,"DS_FRETE")
	//-- Vlr. Seguro
	TSay():New(10,180,{|| RetTitle("DS_SEGURO")},oFolder:aDialogs[1],,,,,,.T.,,,50,10)
	TGet():New(08,250,{|| SDS->DS_SEGURO},oFolder:aDialogs[1],50,10,PesqPict("SDS","DS_SEGURO"),,,,,,,.T.,,,,,,,.T.,,,"DS_SEGURO")
	//-- Vlr. Despesas
	TSay():New(30,180,{|| RetTitle("DS_DESPESA")},oFolder:aDialogs[1],,,,,,.T.,,,50,10)
	TGet():New(28,250,{|| SDS->DS_DESPESA},oFolder:aDialogs[1],50,10,PesqPict("SDS","DS_DESPESA"),,,,,,,.T.,,,,,,,.T.,,,"DS_DESPESA")
	//-- Descontos
	TSay():New(10,350,{|| RetTitle("DS_DESCONT")},oFolder:aDialogs[1],,,,,,.T.,,,50,10)
	TGet():New(08,430,{|| SDS->DS_DESCONT},oFolder:aDialogs[1],50,10,PesqPict("SDS","DS_DESCONT"),,,,,,,.T.,,,,,,,.T.,,,"DS_DESCONT")
	//-- Total do documento
	TSay():New(70,10,{|| "Total do documento"},oFolder:aDialogs[1],,,,,,.T.,,,50,10)
	TGet():New(68,70,{|| nTotDoc},oFolder:aDialogs[1],50,10,PesqPict("SDS","DS_VALMERC"),,,,,,,.T.,,,,,,,.T.,,,"nTotDoc")

	//-- Transportadora
	TSay():New(10,10,{|| RetTitle("DS_TRANSP")},oFolder:aDialogs[2],,,,,,.T.,,,40,10)
	TGet():New(08,50,{|| SDS->DS_TRANSP},oFolder:aDialogs[2],40,10,PesqPict("SDS","DS_TRANSP"),,,,,,,.T.,,,,,,,.T.,,,"DS_TRANSP")
	//-- Placa
	TSay():New(30,10,{|| RetTitle("DS_PLACA")},oFolder:aDialogs[2],,,,,,.T.,,,40,10)
	TGet():New(28,50,{|| SDS->DS_PLACA},oFolder:aDialogs[2],40,10,PesqPict("SDS","DS_PLACA"),,,,,,,.T.,,,,,,,.T.,,,"DS_PLACA")
	//-- Peso Liquido
	TSay():New(10,110,{|| RetTitle("DS_PLIQUI")},oFolder:aDialogs[2],,,,,,.T.,,,40,10)
	TGet():New(08,160,{|| SDS->DS_PLIQUI},oFolder:aDialogs[2],70,10,PesqPict("SDS","DS_PLIQUI"),,,,,,,.T.,,,,,,,.T.,,,"DS_PLIQUI")
	//-- Peso Bruto
	TSay():New(30,110,{|| RetTitle("DS_PBRUTO")},oFolder:aDialogs[2],,,,,,.T.,,,5400,10)
	TGet():New(28,160,{|| SDS->DS_PBRUTO},oFolder:aDialogs[2],70,10,PesqPict("SDS","DS_PBRUTO"),,,,,,,.T.,,,,,,,.T.,,,"DS_PBRUTO")
	//-- Tipo de frete
	TSay():New(50,10,{|| RetTitle("DS_TPFRETE")},oFolder:aDialogs[2],,,,,,.T.,,,5400,10)
	oComboFrt := TComboBox():New(48,50,{|| SDS->DS_TPFRETE},{"C=CIF","F=FOB","T=Por Terceiros","S=Sem Frete","D=Por Destinatario"},70,10,oFolder:aDialogs[2],,,,,,.T.,,,,,,,,,"DS_TPFRETE")
	oComboFrt:Disable()
	//-- Especie 1
	TSay():New(10,290,{|| RetTitle("DS_ESPECI1")},oFolder:aDialogs[2],,,,,,.T.,,,40,10)
	TGet():New(08,330,{|| SDS->DS_ESPECI1},oFolder:aDialogs[2],90,10,PesqPict("SDS","DS_ESPECI1"),,,,,,,.T.,,,,,,,.T.,,,"DS_ESPECI1")
	//-- Especie 2
	TSay():New(30,290,{|| RetTitle("DS_ESPECI2")},oFolder:aDialogs[2],,,,,,.T.,,,40,10)
	TGet():New(28,330,{|| SDS->DS_ESPECI2},oFolder:aDialogs[2],90,10,PesqPict("SDS","DS_ESPECI2"),,,,,,,.T.,,,,,,,.T.,,,"DS_ESPECI2")
	//-- Especie 3
	TSay():New(50,290,{|| RetTitle("DS_ESPECI3")},oFolder:aDialogs[2],,,,,,.T.,,,40,10)
	TGet():New(48,330,{|| SDS->DS_ESPECI3},oFolder:aDialogs[2],90,10,PesqPict("SDS","DS_ESPECI3"),,,,,,,.T.,,,,,,,.T.,,,"DS_ESPECI3")
	//-- Especie 4
	TSay():New(70,290,{|| RetTitle("DS_ESPECI4")},oFolder:aDialogs[2],,,,,,.T.,,,40,10)
	TGet():New(68,330,{|| SDS->DS_ESPECI4},oFolder:aDialogs[2],90,10,PesqPict("SDS","DS_ESPECI4"),,,,,,,.T.,,,,,,,.T.,,,"DS_ESPECI4")
	//-- Volume 1
	TSay():New(10,440,{|| RetTitle("DS_VOLUME1")},oFolder:aDialogs[2],,,,,,.T.,,,40,10)
	TGet():New(08,480,{|| SDS->DS_VOLUME1},oFolder:aDialogs[2],50,10,PesqPict("SDS","DS_VOLUME1"),,,,,,,.T.,,,,,,,.T.,,,"DS_VOLUME1")
	//-- Volume 2
	TSay():New(30,440,{|| RetTitle("DS_VOLUME2")},oFolder:aDialogs[2],,,,,,.T.,,,40,10)
	TGet():New(28,480,{|| SDS->DS_VOLUME2},oFolder:aDialogs[2],50,10,PesqPict("SDS","DS_VOLUME2"),,,,,,,.T.,,,,,,,.T.,,,"DS_VOLUME2")
	//-- Volume 3
	TSay():New(50,440,{|| RetTitle("DS_VOLUME3")},oFolder:aDialogs[2],,,,,,.T.,,,40,10)
	TGet():New(48,480,{|| SDS->DS_VOLUME3},oFolder:aDialogs[2],50,10,PesqPict("SDS","DS_VOLUME3"),,,,,,,.T.,,,,,,,.T.,,,"DS_VOLUME3")
	//-- Volume 4
	TSay():New(70,440,{|| RetTitle("DS_VOLUME4")},oFolder:aDialogs[2],,,,,,.T.,,,40,10)
	TGet():New(68,480,{|| SDS->DS_VOLUME4},oFolder:aDialogs[2],50,10,PesqPict("SDS","DS_VOLUME4"),,,,,,,.T.,,,,,,,.T.,,,"DS_VOLUME4")

	//-- Chave NF-e
	TSay():New(10,10,{|| RetTitle("DS_CHAVENF")},oFolder:aDialogs[3],,,,,,.T.,,,50,10)
	TGet():New(08,70,{|| SDS->DS_CHAVENF},oFolder:aDialogs[3],230,10,PesqPict("SDS","DS_CHAVENF"),,,,,,,.T.,,,,,,,.T.,,,"DS_CHAVENF")
	//-- Versao NF-e
	TSay():New(30,10,{|| RetTitle("DS_VERSAO")},oFolder:aDialogs[3],,,,,,.T.,,,50,10)
	TGet():New(28,70,{|| SDS->DS_VERSAO},oFolder:aDialogs[3],50,10,PesqPict("SDS","DS_VERSAO"),,,,,,,.T.,,,,,,,.T.,,,"DS_VERSAO")
	//-- Nome do arquivo
	TSay():New(50,10,{|| RetTitle("DS_ARQUIVO")},oFolder:aDialogs[3],,,,,,.T.,,,50,10)
	TGet():New(48,70,{|| SDS->DS_ARQUIVO},oFolder:aDialogs[3],230,10,PesqPict("SDS","DS_ARQUIVO"),,,,,,,.T.,,,,,,,.T.,,,"DS_ARQUIVO")

	//-- Usuario
	TSay():New(10,10,{|| RetTitle("DS_USERIMP")},oFolder:aDialogs[4],,,,,,.T.,,,50,10)
	TGet():New(08,70,{|| SDS->DS_USERIMP},oFolder:aDialogs[4],100,10,PesqPict("SDS","DS_USERIMP"),,,,,,,.T.,,,,,,,.T.,,,"DS_USERIMP")
	//-- Data
	TSay():New(30,10,{|| RetTitle("DS_DATAIMP")},oFolder:aDialogs[4],,,,,,.T.,,,50,10)
	TGet():New(28,70,{|| SDS->DS_DATAIMP},oFolder:aDialogs[4],50,10,PesqPict("SDS","DS_DATAIMP"),,,,,,,.T.,,,,,,,.T.,,,"DS_DATAIMP")
	//-- Hora
	TSay():New(50,10,{|| RetTitle("DS_HORAIMP")},oFolder:aDialogs[4],,,,,,.T.,,,50,10)
	TGet():New(48,70,{|| SDS->DS_HORAIMP},oFolder:aDialogs[4],50,10,PesqPict("SDS","DS_HORAIMP"),,,,,,,.T.,,,,,,,.T.,,,"DS_HORAIMP")

	//-- Usuario
	TSay():New(10,10,{|| RetTitle("DS_USERPRE")},oFolder:aDialogs[5],,,,,,.T.,,,50,10)
	TGet():New(08,70,{|| SDS->DS_USERPRE},oFolder:aDialogs[5],100,10,PesqPict("SDS","DS_USERPRE"),,,,,,,.T.,,,,,,,.T.,,,"DS_USERPRE")
	//-- Data
	TSay():New(30,10,{|| RetTitle("DS_DATAPRE")},oFolder:aDialogs[5],,,,,,.T.,,,50,10)
	TGet():New(28,70,{|| SDS->DS_DATAPRE},oFolder:aDialogs[5],50,10,PesqPict("SDS","DS_DATAPRE"),,,,,,,.T.,,,,,,,.T.,,,"DS_DATAPRE")
	//-- Hora
	TSay():New(50,10,{|| RetTitle("DS_HORAPRE")},oFolder:aDialogs[5],,,,,,.T.,,,50,10)
	TGet():New(48,70,{|| SDS->DS_HORAPRE},oFolder:aDialogs[5],50,10,PesqPict("SDS","DS_HORAPRE"),,,,,,,.T.,,,,,,,.T.,,,"DS_HORAPRE")

	//-- Ocorrencia
	TMultiGet():New(10,10,{|| SDS->DS_DOCLOG},oFolder:aDialogs[6],aPosRdp[4]*0.96,oFolder:nHeight*0.35,,,,,,.T.,,,,,,.T.)

	//-- Impostos
	Aadd(aHeadImp, {" "					,"LEGENDA","@BMP"			  ,02,0,			 ,,'C',,'V'})
	Aadd(aHeadImp, {AllTrim("Imposto")	,"IMPOSTO","@!"				  ,25,0,			 ,,'C',,'R'})
	Aadd(aHeadImp, {AllTrim("Valor TES"),"VALORT" ,"@E 999,999,999.99",14,2,"ColVAImp(1)",,'N',,'R'})
	Aadd(aHeadImp, {AllTrim("Valor XML"),"VALORX" ,"@E 999,999,999.99",14,2,			 ,,'N',,'R'})
	Aadd(aHeadImp, {AllTrim("Aliq. TES"),"ALIQT"  ,"@E 999,999,999.99",14,2,"ColVAImp(2)",,'N',,'R'})
	Aadd(aHeadImp, {AllTrim("Aliq. XML"),"ALIQX"  ,"@E 999,999,999.99",14,2,			 ,,'N',,'R'})

	TSay():New(10,10,{|| "Impostos:"},oFolder:aDialogs[7],,,,,,.T.,,,50,10)
	oNewGet := MsNewGetDados():New(10,45,90,385,If(nOpc==4,2,4), "AllwaysTrue", "AllwaysTrue", /*cIniCpos*/, {"VALORT","ALIQT"},, 999, "AllwaysTrue", "", "AllwaysTrue", oFolder:aDialogs[7],@aHeadImp,@aColsImp)
	ColLoadImp(@oNewGet)

	oGetDados:oBrowse:bChange := {|| ColImpRefresh()}
	oGetDados:Refresh()

	If nOpc == 4 .And. ( SDS->DS_TIPO $ "DCN" .Or. lRemet )
		aAdd(aButtons, {"PEDIDO", {|| Documentos(oGetDados:aCols[oGetDados:nAt,nPDTCOD],.F.,nMultPC:=1,aColsAnt)}, If(SDS->DS_TIPO $ "NT",STR0015,STR0016),If(SDS->DS_TIPO $ "NT",STR0017,STR0018)}) //-- Pedido de Compra (Item) # Documento Origem # PC (Item) # Origem
		If SDS->DS_TIPO $ "NT"
			aAdd(aButtons, {"SOLICITA", {|| Documentos(oGetDados:aCols[oGetDados:nAt,nPDTCOD],.T.,nMultPC:=2,aColsAnt)},STR0019,STR0020}) //-- Pedido de Compra (Doc.) # PC (Doc.)
		EndIf

		If SDS->DS_TIPO $ "DCN" .Or. (SDS->DS_TIPO == "T" .And. lRemet)
			aAdd(aButtons, {"DESVINC",{|| Documentos(oGetDados:aCols[oGetDados:nAt,nPDTCOD],.T.,nMultPC:=3,aColsAnt)},"Desvincular"})
		Endif
	EndIf

	aAdd(aButtons,{'LEGENDA',{|| COLLegIt()},STR0051,STR0051}) //Legenda

	Activate MsDialog oDlg On Init(EnchoiceBar(oDlg,{|| lRet := .T.,IIF(IIF(SDS->DS_TIPO=="D",ComXTudoOk(),.T.),oDlg:End(),)}, {|| IIF(SDS->DS_TIPO=="D",ComXGetAnt(aColsAnt),),oDlg:End()},,aButtons))

	//-- Restaura aCols para Getdados principal
	aCols:= oGetDados:aCols

	// Verifica se houve vinculo com pedido de compra
	If lRet .And. nOpc == 4 .And. (SDS->DS_TIPO $ "N" .Or. (SDS->DS_TIPO $ "T" .And. lRemet))
		// Verifica se o aCols esta igual ao aColsAnt para nao gravar registros novamente sem necessidade
		nPosPed  := GdFieldPos("DT_PEDIDO",aHeader)
		nPosItPC := GdFieldPos("DT_ITEMPC",aHeader)
		nPosTES	 := GdFieldPos("DT_TES",aHeader)

		If Len(aColsAnt) == Len(aCols)
			For nX := 1 To Len(aColsAnt)
				If aColsAnt[nX][nPosPed]!=aCols[nX][nPosPed] .Or. aColsAnt[nX][nPosItPC]!=aCols[nX][nPosItPC]
					nOpc := 5
					lGrava := .T.
					Exit
				Elseif aColsAnt[nX][nPosTES]!=aCols[nX][nPosTES] //Alterou TES
					lGrava := .T.
					Exit
				Else
					lGrava := .F.
				EndIf
			Next nX
		Else
			nOpc := 5
		EndIf
	EndIf

	If lRet .And. nOpc == 4 //-- Caso tenha processado o vinculo
		If lGrava
			nPDTNFORI 	:= GDFieldPos("DT_NFORI",aHeader)
			nPDTSERIORI	:= GDFieldPos("DT_SERIORI",aHeader)
			nPDTITEMORI	:= GDFieldPos("DT_ITEMORI",aHeader)
			nPDTTES		:= GdFieldPos("DT_TES",aHeader)
			nPDTTESIPI	:= GdFieldPos("DT_TESIPI",aHeader)
			nPDTTESICM	:= GdFieldPos("DT_TESICM",aHeader)
			nPDTTESISS	:= GdFieldPos("DT_TESISS",aHeader)
			nPDTTESPIS	:= GdFieldPos("DT_TESPIS",aHeader)
			nPDTTESCOF	:= GdFieldPos("DT_TESCOF",aHeader)
			nPDTTESICST	:= GdFieldPos("DT_TESICST",aHeader)
			nPDTALIQIPI	:= GdFieldPos("DT_ALIQIPI",aHeader)
			nPDTALIQICM	:= GdFieldPos("DT_ALIQICM",aHeader)
			nPDTALIQISS	:= GdFieldPos("DT_ALIQISS",aHeader)
			nPDTALIQPIS	:= GdFieldPos("DT_ALIQPIS",aHeader)
			nPDTALIQCOF	:= GdFieldPos("DT_ALIQCOF",aHeader)
			nPDTALIICST	:= GdFieldPos("DT_ALIICST",aHeader)
			nPosDTItem	:= GdFieldPos("DT_ITEM",aHeader)
			nPosDTPED	:= GdFieldPos("DT_PEDIDO",aHeader)
			nPosDTItPC	:= GdFieldPos("DT_ITEMPC",aHeader)

			For nX := 1 To Len(aCols)
				SDT->(DbSetOrder(8))
				If SDT->(DbSeek(xFilial("SDT")+SDS->DS_FORNEC+SDS->DS_LOJA+SDS->DS_DOC+SDS->DS_SERIE+aCols[nX,nPosDTItem]))
					lNovo := .F.
				Else
					lNovo := .T.
				EndIf
				If (!(SDS->DS_TIPO $ "N" .Or. lRemet)) .And. nPDTNFORI > 0	//-- Grava pedido e item
					//-- Grava nota, serie e item origem
					RecLock("SDT",lNovo)
					SDT->DT_NFORI   := aCols[nX,nPDTNFORI]
					SDT->DT_SERIORI := aCols[nX,nPDTSERIORI]
					SDT->DT_ITEMORI := aCols[nX,nPDTITEMORI]
					SDT->(MsUnLock())
				EndIf
				IF nPosDtPed > 0 .And. nPosDTItPC > 0
					RecLock("SDT",lNovo)
					SDT->DT_PEDIDO   := aCols[nX,nPosDTPED]
					SDT->DT_ITEMPC   := aCols[nX,nPosDTItPC]
					SDT->(MsUnLock())
				Endif
			Next nX

			//-- Grava Impostos e Tes
			For nX := 1 To Len(aCols)
				SDT->(DbSetOrder(8))
				If SDT->(DbSeek(xFilial("SDT")+SDS->DS_FORNEC+SDS->DS_LOJA+SDS->DS_DOC+SDS->DS_SERIE+aCols[nX,nPosDTItem]))
					lNovo := .F.
				Else
					lNovo := .T.
				EndIf
				RecLock("SDT",lNovo)
				SDT->DT_TES		:= aCols[nX][nPDTTES]
				SDT->DT_TESIPI	:= aCols[nX][nPDTTESIPI]
				SDT->DT_TESICM	:= aCols[nX][nPDTTESICM]
				SDT->DT_TESISS	:= aCols[nX][nPDTTESISS]
				SDT->DT_TESPIS	:= aCols[nX][nPDTTESPIS]
				SDT->DT_TESCOF	:= aCols[nX][nPDTTESCOF]
				SDT->DT_TESICST	:= aCols[nX][nPDTTESICST]
				SDT->DT_ALIQIPI	:= aCols[nX][nPDTALIQIPI]
				SDT->DT_ALIQICM	:= aCols[nX][nPDTALIQICM]
				SDT->DT_ALIQISS	:= aCols[nX][nPDTALIQISS]
				SDT->DT_ALIQPIS	:= aCols[nX][nPDTALIQPIS]
				SDT->DT_ALIQCOF	:= aCols[nX][nPDTALIQCOF]
				SDT->DT_ALIICST	:= aCols[nX][nPDTALIICST]
				For nY	:= 1 To Len(aUsrCpo)
					SDT->&("DT_"+SUBSTR(aUsrCpo[nY],4)) := aCols[nX][GdFieldPos("DT_"+SUBSTR(aUsrCpo[nY],4))]
				Next nY
				SDT->(MsUnlock())
			Next nX
		EndIf
	ElseIf lRet .And. nOpc == 5		//-- Opcao por vinculo de multiplos pedidos
		For nX := 1 To Len(aColsAnt)
			SDT->(dbGoTo(aColsAnt[nX,Len(aHeader)]))
			// Marca item original para que possa ser recuperado ao desvincular os pedidos
			RecLock("SDT",.F.)
			SDT->DT_ORIGIN := Iif(Empty(SDT->DT_ORIGIN),"1","2")
			SDT->(MsUnLock())

			// Deleta item
			RecLock("SDT",.F.)
			SDT->(dbDelete())
			SDT->(MsUnLock())
		Next nX

		//--Grava novos itens
		nPosDTItem := nPDTITEM

		For nX := 1 To Len(aCols)
			SDT->(DbSetOrder(8))
			If SDT->(DbSeek(xFilial("SDT")+SDS->DS_FORNEC+SDS->DS_LOJA+SDS->DS_DOC+SDS->DS_SERIE+aCols[nX,nPosDTItem]))
				lNovo := .F.
			Else
				lNovo := .T.
			EndIf

			RecLock("SDT",lNovo)
			SDT->DT_FILIAL	:= xFilial("SDT")
			SDT->DT_FORNEC	:= SDS->DS_FORNEC
			SDT->DT_LOJA	:= SDS->DS_LOJA
			SDT->DT_DOC		:= SDS->DS_DOC
			SDT->DT_SERIE	:= SDS->DS_SERIE
			SDT->DT_CNPJ	:= SDS->DS_CNPJ
			For nY := 1 To Len(aHeader)
				SDT->(FieldPut(SDT->(FieldPos(aHeader[nY][2])),aCols[nX][nY]))
			Next nY
			//2-Novo registro com pedido vinculado, 3-Novo registro sem pedido vinculado
			SDT->DT_ORIGIN	:= Iif(!Empty(aCols[nX][nPosPed]),"2","3")
			For nY	:= 1 To Len(aUsrCpo)
				SDT->&("DT_"+SUBSTR(aUsrCpo[nY],4)) := aCols[nX][GdFieldPos("DT_"+SUBSTR(aUsrCpo[nY],4))]
			Next nY
			SDT->(MsUnlock())
		Next nX
	EndIf

	If lCOMCOLSD
		ExecBlock("COMCOLSD",.F.,.F.,{aCols,aHeader})
	EndIf

	cFilAnt := cFilBkp

	aRotina[2,4] := 2

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} ColImpRefresh
TOTVS COLABORAÇAO 2.0
Atualiza grid de impostos.
@author		Flavio Lopes Rasta
@since		06/04/2015
@version	P11
/*/
//-------------------------------------------------------------------
Function ColImpRefresh()

	ColLoadImp(@oNewGet)

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} ColVAImp
Atualiza Valor/Aliquota de impostos

@author	Totvs
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function ColVAImp(nOpc)

	Local n 	:= oGetDados:nAt
	Local nImp	:= oNewGet:nAt

	If nOpc == 1 //Valor
		oGetDados:aCols[n][aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_TESIPI"})]	:= If(nImp ==1,M->VALORT,aCols[1][3])
		oGetDados:aCols[n][aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_TESICM"})]	:= If(nImp ==2,M->VALORT,aCols[2][3])
		oGetDados:aCols[n][aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_TESISS"})]	:= If(nImp ==3,M->VALORT,aCols[3][3])
		oGetDados:aCols[n][aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_TESPIS"})]	:= If(nImp ==4,M->VALORT,aCols[4][3])
		oGetDados:aCols[n][aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_TESCOF"})]	:= If(nImp ==5,M->VALORT,aCols[5][3])
		oGetDados:aCols[n][aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_TESICST"})]	:= If(nImp ==6,M->VALORT,aCols[6][3])

		//-- Atualiza leganda da linha
		If(M->VALORT == aCols[nImp][4] .And. aCols[nImp][5] == aCols[nImp][6])
			aCols[nImp][1] := oGreen
		Else
			aCols[nImp][1] := oRed
		Endif
	Elseif nOpc == 2 //Aliquota
		oGetDados:aCols[n][aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_ALIQIPI"})]	:= If(nImp ==1,M->ALIQT,aCols[1][5])
		oGetDados:aCols[n][aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_ALIQICM"})]	:= If(nImp ==2,M->ALIQT,aCols[2][5])
		oGetDados:aCols[n][aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_ALIQISS"})]	:= If(nImp ==3,M->ALIQT,aCols[3][5])
		oGetDados:aCols[n][aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_ALIQPIS"})]	:= If(nImp ==4,M->ALIQT,aCols[4][5])
		oGetDados:aCols[n][aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_ALIQCOF"})]	:= If(nImp ==5,M->ALIQT,aCols[5][5])
		oGetDados:aCols[n][aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_ALIICST"})]	:= If(nImp ==6,M->ALIQT,aCols[6][5])

		//-- Atualiza leganda da linha
		If(aCols[nImp][3] == aCols[nImp][4] .And. M->ALIQT == aCols[nImp][6])
			aCols[nImp][1] := oGreen
		Else
			aCols[nImp][1] := oRed
		Endif
	Endif

	oGetDados:Refresh()
	oNewGet:Refresh()

Return .T.

//-------------------------------------------------------------------
/*/{Protheus.doc} ColLoadImp
Carrega Grid de impostos no monitor.

@param		oBrowse, object, Objeto do browse.<br><b>Obrigatório

@author		Flavio Lopes Rasta
@since		06/04/2015
@version	P11
/*/
//-------------------------------------------------------------------
Function ColLoadImp(oNewGet)

	Local aImpostos		:= {"IPI","ICMS","ISS","PIS","COFINS","ICMS ST"}
	Local nPosValTes	:= 0
	Local nPosValXml	:= 0
	Local nPosAlqTes	:= 0
	Local nPosAlqXml	:= 0
	Local nX			:= 1
	Local nAt			:= oGetDados:nAt
	Local nValorTes 	:= 0
	Local nAliqTes		:= 0
	Local lMVDiviZer	:= SuperGetMv("MV_DIVIZER",.F.,.F.)
	Local lCOLDVIMP		:= ExistBlock("COLDVIMP")

	aColsImp:= {}

	For nX:=1 To Len(aImpostos)
		If aImpostos[nX] == "ICMS ST"
			nPosValTes := aScan(aHeader,{|x| AllTrim(x[2]) == "DT_TESICST"})
			nPosAlqTes := aScan(aHeader,{|x| AllTrim(x[2]) == "DT_ALIICST"})
			nPosValXml := aScan(aHeader,{|x| AllTrim(x[2]) == "DT_XMLICST"})
			nPosAlqXml := aScan(aHeader,{|x| AllTrim(x[2]) == "DT_XALICST"})
		Else
			nPosValTes := aScan(aHeader,{|x| AllTrim(x[2]) == "DT_TES"+SubStr(aImpostos[nX],1,3)})
			nPosAlqTes := aScan(aHeader,{|x| AllTrim(x[2]) == "DT_ALIQ"+SubStr(aImpostos[nX],1,3)})
			nPosValXml := aScan(aHeader,{|x| AllTrim(x[2]) == "DT_XML"+SubStr(aImpostos[nX],1,3)})
			nPosAlqXml := aScan(aHeader,{|x| AllTrim(x[2]) == "DT_XALQ"+SubStr(aImpostos[nX],1,3)})
		Endif

		nPosLegend := aScan(aHeader,{|x| AllTrim(x[2]) == "DT_LEGENDA"})

		nValorTes	:= oGetDados:aCols[nAt][nPosValTes]
		nAliqTes	:= If(lMVDiviZer .And. (nValorTes == 0),0,oGetDados:aCols[nAt][nPosAlqTes])

		aAdd(aColsImp,{})
		aAdd(aTail(aColsImp),If(nValorTes == oGetDados:aCols[nAt][nPosValXml] .And. nAliqTes == oGetDados:aCols[nAt][nPosAlqXml],oGreen,oRed))
		aAdd(aTail(aColsImp),aImpostos[nX])
		aAdd(aTail(aColsImp),nValorTes)
		aAdd(aTail(aColsImp),oGetDados:aCols[nAt][nPosValXml])
		aAdd(aTail(aColsImp),nAliqTes)
		aAdd(aTail(aColsImp),oGetDados:aCols[nAt][nPosAlqXml])
		aAdd(aTail(aColsImp),.F.)
	Next nX

	If lCOLDVIMP
		aColsImp := ExecBlock("COLDVIMP",.F.,.F.,{"COMXCOL",aColsImp})
	Endif

	If ValType(oNewGet) <> "U"
		oNewGet:SetArray(@aColsImp)
	EndIf

	If nPosLegend > 0
		If (nPos:=aScan(aColsImp,{|x| x[1]:cName == "BR_VERMELHO"})) > 0
			oGetDados:aCols[nAt][nPosLegend] := aColsImp[nPos][1]:cName
		Else
			oGetDados:aCols[nAt][nPosLegend] := aColsImp[1][1]:cName
		Endif
	Endif

	oGetDados:Refresh()

	If ValType(oNewGet) <> "U"
		oNewGet:Refresh()
	EndIf

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} COMCOLGER
Processa a geracao dos documentos fiscais.

@author	Andre Anjos
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function COMCOLGER()

	Local nQtdNF	:= 0
	Local nX 		:= 1
	Local aDivFis	:= {}
	Local nProcOpc	:= 2
	Local lProcessa := .T.
	Local lCAuto	:= .F.
	Local aDivNFPed	:= {}
	Local nQtdPC	:= 0
	Local nPrcPC	:= 0
	Local nPos		:= 0
	Local nY		:= 0
	Local cMsg		:= ""
	Local cAliqICMS	:= GetMV("MV_ALIQICM")
	Local aAliqICMS	:= StrTokArr(cAliqICMS, "/")
	Local lVldICMS	:= .T.
	Local aDadosPC	:= {}
	Local aCancel	:= {}
	Local aTransmite:= {}
	Local lCkoTra	:= CKO->(FieldPos("CKO_CHVDOC")) > 0 .And. CKO->(FieldPos("CKO_ORIGEM")) > 0 .And. CKO->(FieldPos("CKO_STRAN")) > 0

	nQtdNF := Len(aRegMark)

	If nQtdNF > 0 .And. (lProcessa := MsgYesNo(STR0021,STR0022)) //-- Confirma a geração de documento para os itens selecionados? # Atenção

		SDT->(DbSetOrder(1))
		For nX:=1 To nQtdNF
			SDS->(dbGoTo(aRegMark[nX]))
			SDT->(DbSeek(xFilial("SDT")+SDS->(DS_CNPJ+DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)))
			While !SDT->(Eof()) .And. SDT->(DT_CNPJ+DT_FORNEC+DT_LOJA+DT_DOC+DT_SERIE) == SDS->(DS_CNPJ+DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)
				If 	Len(aDivFis) == 0 .And. (SDT->DT_TESIPI <> SDT->DT_XMLIPI	.Or.;
						SDT->DT_TESICM <> SDT->DT_XMLICM	.Or.;
						SDT->DT_TESISS <> SDT->DT_XMLISS	.Or.;
						SDT->DT_TESPIS <> SDT->DT_XMLPIS	.Or.;
						SDT->DT_TESCOF <> SDT->DT_XMLCOF	.Or.;
						SDT->DT_TESICST <> SDT->DT_XMLICST	.Or.;
						SDT->DT_ALIQIPI <> SDT->DT_XALQIPI .Or.;
						SDT->DT_ALIQICM	<> SDT->DT_XALQICM .Or.;
						SDT->DT_ALIQISS	<> SDT->DT_XALQISS .Or.;
						SDT->DT_ALIQPIS	<> SDT->DT_XALQPIS .Or.;
						SDT->DT_ALIQCOF	<> SDT->DT_XALQCOF .Or.;
						SDT->DT_ALIICST <> SDT->DT_XALICST)

					If SDT->DT_ALIQICM <> SDT->DT_XALQICM
						lVldICMS := (Ascan(aAliqICMS,cValToChar(SDT->DT_XALQICM)) > 0)
					EndIf

					aAdd(aDivFis,SDS->(Recno()))
				Endif

				If !Empty(SDT->DT_PEDIDO) .And. !Empty(SDT->DT_ITEMPC)
					aDadosPC := GetAdvFval("SC7",{"C7_QUANT","C7_PRECO","C7_MOEDA","C7_TXMOEDA"},xFilial("SC7") + PadR(SDT->DT_PEDIDO,TamSx3("C7_NUM")[1]) + PadR(SDT->DT_ITEMPC,TamSx3("C7_ITEM")[1]),1)

					nQtdPC := aDadosPC[1]
					If aDadosPC[3] <> 1 //Não é moeda Real
						nPrcPC := xMoeda(aDadosPC[2],aDadosPC[3],1,,2,aDadosPC[4],1)
					Else
						nPrcPC := aDadosPC[2]
					Endif

					If nQtdPC <> SDT->DT_QUANT .Or. nPrcPc <> SDT->DT_VUNIT
						nPos := aScan(aDivNFPed,{|x| x[1]+x[2] == SDT->DT_DOC+SDT->DT_SERIE})
						If nPos == 0
							aAdd(aDivNFPed,{SDT->DT_DOC,SDT->DT_SERIE,{SDT->DT_ITEM}})
						Else
							aAdd(aDivNFPed[nPos,3],SDT->DT_ITEM)
						Endif
					Endif
				Endif
				SDT->(DbSkip())
			EndDo
		Next nX

		If !lVldICMS //Valida ICMS mas apenas informa que aliquota não esta cadastrada no parametro
			Aviso(STR0120, STR0182, {STR0077}) // "Divergência Fiscal"##"A alíquota informada no XML não condiz com as alíquotas configuradas no parâmetro MV_ALIQICM, a nota não será gerada."##"OK"
			lProcessa := .T.
		Endif

		If lProcessa .And. Len(aDivFis) > 0
			nProcOpc := Aviso(STR0120, STR0121 + CRLF + STR0122 + CRLF + STR0123 + CRLF + STR0124,{STR0125, STR0126, STR0127}, 2) //"Divergência Fiscal"##"Existem itens com divergência fiscal, qual opção deseja executar?"##"Cancelar - Para sair."##" Ignorar - Para importar mesmo com divergencia."##"Conformes - Apenas os documentos que não tem divergência."## "Cancelar"##"Ignorar"##"Conformes"
			If nProcOpc == 1
				lProcessa := .F.
			ElseIf nProcOpc == 2
				lProcessa := .T.
				lCAuto	:= .T.
			ElseIf nProcOpc == 3
				For nX:=1 To Len(aDivFis)
					aDel(aRegMark,Ascan(aRegMark,{|x| x == aDivFis[nX]}))
				Next nX

				aSize(aRegMark,Len(aRegMark) - Len(aDivFis))

				If Len(aRegMark) > 0
					nQtdNF	:= Len(aRegMark)
					lCAuto	:= .T.
				Else
					lProcessa := .F.
				Endif
			Endif
		Endif

		If lProcessa .And. Len(aDivNFPed) > 0
			cMsg += STR0128 + CRLF //"Existem divergências entre o valor unitário e/ou quantidade da(s) NF(s) com o(s) Pedido(s) relacionado(s)"

			For nX := 1 To Len(aDivNFPed)
				cMsg += STR0129 + aDivNFPed[nX,1] + STR0130 + aDivNFPed[nX,2] + STR0131 //"NF: "##Serie:##Item(ns) NF: (
				For nY := 1 To Len(aDivNFPed[nX,3])
					If nY == 1
						cMsg += aDivNFPed[nX,3,nY]
					Else
						cMsg += ", " + aDivNFPed[nX,3,nY]
					Endif
				Next nY
				cMsg += ")" + CRLF
			Next nX

			cMsg += CRLF + STR0132 + CRLF + STR0133 + CRLF + ; //"Qual opção deseja executar?"##"OK - Gerar documento com as divergências. "
				STR0134 //"Cancelar - Realizar o ajuste manualmente."

			nProcOpc := Aviso(STR0135,cMsg, {STR0077,STR0125},3) //"Divergência NF - Pedido"## "Ok"##Cancelar
			If nProcOpc == 1
				lProcessa := .T.
				lCAuto	:= .T.
			Elseif nProcOpc == 2
				lProcessa := .F.
			Endif
		Endif
	Else
		lProcessa := .F.
	Endif

	If lProcessa
		Processa({|| ProcDocs(nQtdNF,.F.,lCAuto),STR0001 +" - " +STR0023}) //-- Monitor TOTVS Colaboração # Geração de Documentos
		//Verifica se usuario não abortou geração do documento
		//Assim o registro tem que continuar marcado no browse
		For nX := 1 To Len(aRegMark)
			SDS->(DbGoto(aRegMark[nX]))
			If SDS->DS_STATUS == "P" .Or. SDS->DS_STATUS == "E"
				aAdd(aCancel,aRegMark[nX])
			Endif
			If lCkoTra .And. SDS->DS_STATUS == "P"
				aAdd(aTransmite,SDS->DS_ARQUIVO)
			Endif
		Next nX

		For nX := 1 To Len(aCancel)
			nPos := aScan(aRegMark,{|x| x == aCancel[nX] })
			If nPos > 0
				ADEL( aRegMark, nPos)
				ASIZE( aRegMark, Len(aRegMark)-1 )
			Endif
		Next nX

		If lCkoTra .And. Len(aTransmite) > 0 .And. FindFunction("COMATUTRANS")
			COMATUTRANS(aTransmite,1)
		Endif
	Endif

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} ProcDocs
Processa a geracao dos documentos a partir de SDS/SDT

@param	nRegs		total de registros a serem processados.
@param	lNFeAut		indica se gera automaticamenteo documentos classificados

@author	Andre Anjos
@since 05/06/12
/*/
//-------------------------------------------------------------------

Static Function ProcDocs(nRegs,lNFeAut,lCAuto,lJob)
	Local aCabec 	:= {}
	Local aItens 	:= {}
	Local aErro  	:= {}
	Local aRetPARA	:= {}
	Local cErro  	:= ""
	Local cFilBkp	:= cFilAnt
	Local nX	 	:= 0
	Local nY		:= 0
	Local nCount 	:= 0
	Local lRet		:= .F.
	Local lProcessa	:= .T.
	Local lImpXML	:= .T.	// Esta variavel fara com que a nota seja gerada com os valores de impostos do XML, quando a nota for gerada de forma automatica
	Local lClass	:= .F.
	Local lNFImpMan := .F.
	Local nComCol1	:= SuperGetMV("MV_COMCOL1",.F.,0)
	Local cComCol2	:= SuperGetMV("MV_COMCOL2",.F.,"NDCOTB")
	Local lCteClass := SuperGetMV("MV_CTECLAS",.F.,.F.)
	Local lComxProc	:= ExistBlock("COMXPROC")
	Local lCOMXPARA := ExistBlock("COMXPARA")
	Local lCOLF1D1	:= ExistBlock("COLF1D1")
	Local lCOLSTTS	:= ExistBlock("COLSTTS")
	Local lClaTodos	:= .F.
	Local lPreTodos	:= .F.
	Local lDevComNF	:= .F.
	Local aItCSD	:= {}
	Local lCsdXML 		:= SuperGetMV( 'MV_CSDXML', .F., .F. ) .and. SDT->(FieldPos("DT_ITXML")) > 0 .and. SDT->(FieldPos("DT_UMXML")) > 0 .and. SDT->(FieldPos("DT_QTDXML")) > 0;
		.and. SDT->(FieldPos("DT_FATOR")) > 0 .and. FWSX3Util():GetFieldType( "D1_ITXML" ) == "C" .and. ChkFile("DKA");
		.and. ChkFile("DKB") .and. ChkFile("DKC") .and. ChkFile("D3Q")

	Default lNFeAut := .F.
	Default lCAuto	:= .F.	// Esta variavel determina se sera gerada Pre Nota (.F.) ou documento classificado (.T.)
	Default lJob    := .F.

	Private lMSErroAuto		:= .F.
	Private lAutoErrNoFile	:= .T.

	ProcRegua(nRegs)
	For nY := 1 To nRegs
		If !lNFeAut
			SDS->(dbGoTo(aRegMark[nY]))
		EndIf

		lProcessa := .T.

		// Verifica se o tipo da NF esta contido no paramentro para geracao automatica
		If lNFeAut .And. !(SDS->DS_TIPO $ cComCol2)
			lProcessa := .F.
		EndIf

		//Valida processamento do documento
		If lProcessa .And. lComxProc
			lProcessa := ExecBlock("COMXPROC",.F.,.F.)
		EndIf

		If lProcessa .And. lCOMXPARA
			aRetPARA := ExecBlock("COMXPARA",.F.,.F.,{ nComCol1, lCteClass })

			If ValType(aRetPARA) == "A" .And. Len(aRetPARA) > 0
				If ValType(aRetPARA[1]) == "N"
					nComCol1  := aRetPARA[1]
				EndIf
				If ValType(aRetPARA[2]) == "L"
					lCteClass := aRetPARA[2]
				EndIf
			EndIf
		EndIf

		If lProcessa
			If lNFeAut .And. SDS->DS_TIPO != "C"
				aCabec := MontaSF1(lCteClass,nComCol1)
				aItens := MontaSD1(lImpXML,lCteClass,nComCol1)
				aItens := aSort(aItens,,,{|x,y| x[1,2] < y[1,2]})

				aCabec := COMCONDPG(aCabec,aItens,1)

				If lCOLF1D1
					aRetPe := ExecBlock("COLF1D1",.F.,.F.,{aCabec,aItens})
					If ValType(aRetPe) == "A" .And. Len(aRetPe) >0
						If ValType(aRetPe[1]) == "A"
							aCabec := aClone(aRetPe[1])
						EndIf
						If ValType(aRetPe[2]) == "A"
							aItens := aClone(aRetPe[2])
						EndIf
					EndIf
				EndIf

				aCabec := COMCONDPG(aCabec,aItens,2)

				//Verifica se NF ja foi importada/incluida manualmente.
				lNFImpMan := COLIMPMAN(aCabec)

				If !lNFImpMan
					lClass := .F.
					lClass := ColVerTes(aItens)
					If (lRet := (SDS->DS_STATUS <> "E"))
						If nComCol1 == 1 .And. !(SDS->DS_TIPO $ "OC") .And. !lCteClass .And. !lClass
							lRet := .T.
							MSExecAuto({|x,y,z| MATA140(x,y,z)},aCabec,aItens,3)
						ElseIf (SDS->DS_TIPO $ "OCT") .Or. (lClass .And. lCAuto) .Or. (SDS->DS_TIPO $ "N" .And. lClass)
							lRet   := IIf(SDS->DS_TIPO $ "OCT",.T.,COLNfeAut(aCabec,aItens))
							If lRet
								MSExecAuto({|x,y,z| MATA103(x,y,z)},aCabec,aItens,3)
							EndIf
						Else
							lRet := .F.
						EndIf
					EndIf
				Else
					lRet := .F.
					aErro := GetHlpSoluc("EXISTNF")
					cErro := "EXISTNF" + CRLF
					For nX := 1 To Len(aErro)
						cErro += aErro[nX] + CRLF
					Next nX
					RecLock("SDS",.F.)
					Replace SDS->DS_DOCLOG With cErro
					Replace SDS->DS_STATUS With 'P'
					SDS->(MsUnLock())
				EndIf
			ElseIf lJob .Or. (SDS->DS_OK == cMarca)
				lRet := .T.
				nCount++
				IncProc(STR0024 +AllTrim(SDS->DS_DOC) +"/" +SerieNfId("SDS",2,"DS_SERIE") +"(" +StrZero(nCount,2) +STR0025 +StrZero(nRegs,2) +")") //-- Processando documento # de

				//-- Se filial diferente, troca
				If PadR(cFilAnt,Len(AllTrim(SDS->DS_FILIAL))) # AllTrim(SDS->DS_FILIAL)
					Do Case
						Case FWModeAccess("SB2",3) == "E"
							cFilAnt := SDS->DS_FILIAL
						Case FWModeAccess("SB2",2) == "E" .Or. FWModeAccess("SB2",1) == "E"
							SM0->(dbSetOrder(1))
							SM0->(dbSeek(cEmpAnt+SDS->DS_FILIAL))
							cFilAnt := SM0->M0_CODFIL
					EndCase
				EndIf

				//-- Esvazia log
				RecLock("SDS",.F.)
				SDS->DS_DOCLOG := CriaVar("DS_DOCLOG",.F.)
				SDS->(MsUnLock())

				aCabec := MontaSF1(lCteClass)
				aItens := MontaSD1(lCAuto,lCteClass,nComCol1,@aItCSD)

				aItens := aSort(aItens,,,{|x,y| x[1,2] < y[1,2]})

				aCabec := COMCONDPG(aCabec,aItens,1)

				If lCOLF1D1
					aRetPe := ExecBlock("COLF1D1",.F.,.F.,{aCabec,aItens})
					If ValType(aRetPe) == "A" .And. Len(aRetPe) >0
						If ValType(aRetPe[1]) == "A"
							aCabec := aClone(aRetPe[1])
						EndIf
						If ValType(aRetPe[2]) == "A"
							aItens := aClone(aRetPe[2])
						EndIf
					EndIf
				EndIf

				aCabec := COMCONDPG(aCabec,aItens,2)

				//Verifica se NF ja foi importada/incluida manualmente.
				lNFImpMan := COLIMPMAN(aCabec)

				If !lNFImpMan
					lClass 	  := .F.
					lClass 	  := ColVerTes(aItens)
					lDevComNF := .F.
					lDevComNF := ColVerDev(aItens,aCabec,@lClass)
					If Empty(SDS->DS_DOCLOG) //-- Se nao houve erro na montagem dos dados, continua
						lMSErroAuto := .F.
						If (SDS->DS_TIPO == "D" .And. lDevComNF .And. lClass) .Or. (SDS->DS_TIPO == "O") .Or. (SDS->DS_TIPO == "C" .And. lClass) .Or. (lClass .And. lCAuto) .Or. (lCAuto .And. COLNfeAut(aCabec,aItens) .And. lClass) .Or. (SDS->DS_TIPO == "T" .And. (lCteClass .Or. lClass)) .Or. (lClass .And. SDS->DS_TIPO == "N")
							//Mensagem para decidir a geração do documento (classificado ou pré-nota)
							If !lPreTodos .And. !lClaTodos
								nOpc := Aviso(STR0137,STR0141 + CRLF + AllTrim(SDS->DS_DOC)+"|"+AllTrim(SDS->DS_SERIE),{STR0142,STR0185,STR0143,STR0186,STR0144},2) //Atenção#Documento possui TES nos itens, deseja gerar o documento classificado ou pré-nota?#Classificado#Clas p/ todos#Pre-nota#Pre p/ todos#Abortar
							Elseif lPreTodos
								nOpc := 3
							Elseif lClaTodos
								nOpc := 1
							Endif

							If nOpc <> 5
								If nOpc == 3 .Or. nOpc == 4 //Pré-Nota
									If nOpc == 4
										lPreTodos := .T.
									Endif

									For nX := 1 To Len(aItens)
										nPosTes := aScan(aItens[nX],{|x| x[1] == "D1_TES"})
										If nPosTes > 0
											aItens[nX,nPosTes,1] := "D1_TESACLA"
										Endif
									Next nX

									MSExecAuto({|x,y,z| MATA140(x,y,z)},aCabec,aItens,3)
								Else
									If nOpc == 2
										lClaTodos := .T.
									Endif

									if lCsdXml
										if !empty(aItCSD)
											MSExecAuto({|x,y,z,b,a| MATA103(x,y,z,b,,,,,,,,,,,a)},aCabec,aItens,3,.F.,aItCSD)
										else
											MSExecAuto({|x,y,z| MATA103(x,y,z)},aCabec,aItens,3)
										endif
									else
										MSExecAuto({|x,y,z| MATA103(x,y,z)},aCabec,aItens,3)
									endif
								Endif
							Else
								lRet := .F.
								Exit
							Endif
						Else
							For nX := 1 To Len(aItens)
								nPosTes := aScan(aItens[nX],{|x| x[1] == "D1_TES"})
								If nPosTes > 0
									aItens[nX,nPosTes,1] := "D1_TESACLA"
								Endif
							Next nX

							MSExecAuto({|x,y,z| MATA140(x,y,z)},aCabec,aItens,3)
						EndIf
					Else
						lRet := .F.
					EndIf
				Else
					lRet := .F.
					aErro := GetHlpSoluc("EXISTNF")
					cErro := "EXISTNF" + CRLF
					For nX := 1 To Len(aErro)
						cErro += aErro[nX] + CRLF
					Next nX
					RecLock("SDS",.F.)
					Replace SDS->DS_DOCLOG With cErro
					Replace SDS->DS_STATUS With 'P'
					SDS->(MsUnLock())
				EndIf
			Else
				lRet := .F.
			EndIf

			If lRet
				//-- Grava resultado do processamento na SDS
				RecLock("SDS",.F.)
				Replace SDS->DS_OK	With ''
				If !lMsErroAuto
					Replace SDS->DS_USERPRE	With cUserName
					Replace SDS->DS_DATAPRE	With dDataBase
					Replace SDS->DS_HORAPRE	With Time()
					Replace SDS->DS_STATUS	With 'P'
					Replace SDS->DS_DOCLOG	With ''
				Else
					aErro := GetAutoGRLog()
					cErro := ""
					For nX := 1 To Len(aErro)
						cErro += aErro[nX] +CRLF
					Next nX
					Replace SDS->DS_DOCLOG With cErro
					Replace SDS->DS_STATUS With 'E'
				EndIf

				If lCOLSTTS
					ExecBlock("COLSTTS",.F.,.F.,)
				Endif

				SDS->(MsUnLock())
			EndIf

			If lNFeAut
				Exit
			EndIf
			cFilAnt := cFilBkp
		EndIf
	Next nY

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} COMCONDPG
Verifica se documento ja possui condição de pagamento, porem, não
tem informação de TES ou TES a classificar.

@author	Totvs
@since 05/06/12
/*/
//-------------------------------------------------------------------

Static Function COMCONDPG(aCab,aIt,nOpc)

	Local nX			:= 0
	Local nPosCond		:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_COND"})
	Local nPosTpNF 		:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_TIPO"})
	Local nPosFor  		:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_FORNECE"})
	Local nPosLoj  		:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_LOJA"})
	Local nPosTpCp   	:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_TPCOMPL"})
	Local nPosEsp    	:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_ESPECIE"})
	Local nPosDoc    	:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_DOC"})
	Local nPosSerie    	:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_SERIE"})
	Local nPosFil		:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_FILIAL"})
	// posição para os itens, não sendo necessariamente a mesma para todos os registros.
	Local nPNFOri		:= 0
	Local nPSerOri		:= 0
	Local nPForOri		:= 0
	Local nPLojOri		:= 0
	Local nPPedido		:= 0
	Local nPItemPC		:= 0
	Local nPosTES		:= 0
	Local nPosTESCLA	:= 0
	Local lTes			:= .F.
	Local lGerDupl		:= .F.
	Local lConFrete		:= .F.
	Local lA140ICOND	:= ExistBlock("A140ICOND")
	Local cFilSF4		:= xFilial("SF4")
	Local cFilSE4		:= xFilial("SE4")
	Local cFilSA1		:= xFilial("SA1")
	Local cFilSA2		:= xFilial("SA2")
	Local cFilSF1		:= xFilial("SF1")
	Local cFilSF2		:= xFilial("SF2")
	Local cFilSC7		:= xFilial("SC7")
	Local cCondPg		:= ""
	Local cCondPgPE		:= ""
	Local cAliasF1F2	:= ""
	Local cFilF1F2		:= ""
	Local aAreaSF4 		:= SF4->(GetArea())
	Local aAreaSE4 		:= SE4->(GetArea())
	Local aAreaSA1 		:= SA1->(GetArea())
	Local aAreaSA2 		:= SA2->(GetArea())
	Local aAreaSF1		:= SF1->(GetArea())
	Local aAreaSC7		:= SC7->(GetArea())
	Local aAreaSF2		:= SF2->(GetArea())
	Local oXMLPE		:= Nil

	SF4->(dbSetOrder(1))
	For nX := 1 To Len(aIt)

		nPNFOri			:= aScan(aIt[nX],{|x| AllTrim(x[1]) == "D1_NFORI"})
		nPSerOri		:= aScan(aIt[nX],{|x| AllTrim(x[1]) == "D1_SERIORI"})
		nPForOri		:= aScan(aIt[nX],{|x| AllTrim(x[1]) == "D1_FORNECE"})
		nPLojOri		:= aScan(aIt[nX],{|x| AllTrim(x[1]) == "D1_LOJA"})
		nPPedido		:= aScan(aIt[nX],{|x| AllTrim(x[1]) == "D1_PEDIDO"})
		nPItemPC		:= aScan(aIt[nX],{|x| AllTrim(x[1]) == "D1_ITEMPC"})
		nPosTES			:= aScan(aIt[nX],{|x| AllTrim(x[1]) == "D1_TES"})
		nPosTESCLA		:= aScan(aIt[nX],{|x| AllTrim(x[1]) == "D1_TESACLA"})

		If nPosTes > 0
			lTes := .T.
			If SF4->(dbSeek(cFilSF4 + aIt[nX][nPosTes][2])) .And. SF4->F4_DUPLIC == "S"
				lGerDupl := .T.
				Exit
			EndIf
		Endif

		If nPosTESCLA > 0
			lTes := .T.
			If SF4->(dbSeek(cFilSF4 + aIt[nX][nPosTESCLA][2])) .And. SF4->F4_DUPLIC == "S"
				lGerDupl := .T.
				Exit
			EndIf
		Endif

		If !lTes
			Exit
		Endif
	Next nX

	If nOpc == 1
		If lTes .And. lGerDupl
			SE4->(dbSetOrder(1))

			lConFrete := (nPosTpCp > 0 .And. aCab[nPosTpNF,2] == "C" .And. aCab[nPosTpCp,2] == "3") .Or. (nPosEsp > 0 .And. aCab[nPosTpNF,2] == "N" .And. (AllTrim(aCab[nPosEsp,2]) == "CTE" .Or. AllTrim(aCab[nPosEsp,2]) == "CTEOS"))

			If aCab[nPosTpNF,2] == "C"
				If aCab[nPosTpNF,2] == "C"
					cAliasF1F2	:= "SF1"
					cFilF1F2	:= cFilSF1
				Endif

				SF1->(dbSetOrder(1))

				If nPNFOri > 0 .And. nPSerOri > 0 .And. nPosFor > 0 .And. nPosLoj > 0
					For nX := 1 To Len(aIt)
						If SF1->(dbSeek(cFilSF1 + aIt[nX,nPNFOri,2] + aIt[nX,nPSerOri,2] + aCab[nPosFor,2] + aCab[nPosLoj,2]  )) .And. !Empty(SF1->F1_COND)
							cCondPg := SF1->F1_COND
							Exit
						EndIf
					Next nX
				Endif

				cCondPg := if(empty(cCondPg),GetAdvFVal("SA2","A2_COND",cFilSA2+aCab[nPosFor,2]+aCab[nPosLoj,2],1),cCondPg)

				If lConFrete .And. Empty(cCondPg)
					oXMLPE := COMCOLXML(aCab[nPosFil,2],aCab[nPosDoc,2],aCab[nPosSerie,2],aCab[nPosFor,2],aCab[nPosLoj,2])
					CTe_RetTES(oXMLPE,NIL,@cCondPg,2)
				Endif
			Elseif aCab[nPosTpNF,2] == "N"
				If lConFrete
					oXMLPE := COMCOLXML(aCab[nPosFil,2],aCab[nPosDoc,2],aCab[nPosSerie,2],aCab[nPosFor,2],aCab[nPosLoj,2])
					CTe_RetTES(oXMLPE,NIL,@cCondPg,2)
				Else
					SC7->(DbSetOrder(1))
					If nPPedido > 0 .And. nPItemPC > 0
						For nX := 1 To Len(aIt)
							If SC7->(dbSeek(cFilSC7 + aIt[nX,nPPedido,2] + aIt[nX,nPItemPC,2] )) .And. !Empty(SC7->C7_COND)
								cCondPg := SC7->C7_COND
								Exit
							EndIf
						Next nX
					Else
						If Type("aHeader") == "A" .And. Len(aHeader) > 0
							nPPedido := GdFieldPos("DT_PEDIDO",aHeader)
							nPItemPC := GdFieldPos("DT_ITEMPC",aHeader)
							If nPPedido > 0 .And. nPItemPC > 0
								For nX := 1 To Len(aCols)
									If SC7->(dbSeek(cFilSC7 + aCols[nX,nPPedido] + aCols[nX,nPItemPC] )) .And. !Empty(SC7->C7_COND)
										cCondPg := SC7->C7_COND
										Exit
									EndIf
								Next nX
							Endif
						Endif
					Endif

					If Empty(cCondPg)
						SA2->(dbSetOrder(1))
						If SA2->(dbSeek(cFilSA2+aCab[nPosFor,2]+aCab[nPosLoj,2]))
							cCondPg := SA2->A2_COND
						EndIf
					Endif
				Endif
			ElseIf aCab[nPosTpNF,2] == "B"
				SA1->(dbSetOrder(1))
				If SA1->(dbSeek(cFilSA1+aCab[nPosFor,2]+aCab[nPosLoj,2]))
					cCondPg	:= SA1->A1_COND
				EndIf
			ElseIf aCab[nPosTpNF,2] == "D"

				SF2->(dbSetOrder(1))//F2_FILIAL+F2_DOC+F2_SERIE+F2_CLIENTE+F2_LOJA

				If nPNFOri > 0 .And. nPSerOri > 0 .And. nPosFor > 0 .And. nPosLoj > 0
					For nX := 1 To Len(aIt)
						If SF2->(dbSeek(cFilSF2 + aIt[nX,nPNFOri,2] + aIt[nX,nPSerOri,2] + aCab[nPosFor,2] + aCab[nPosLoj,2]  )) .And. !Empty(SF2->F2_COND)
							cCondPg := SF2->F2_COND
							Exit
						EndIf
					Next nX
				Endif
			EndIf

			If lA140ICOND .And. aCab[nPosTpNF,2] <> "D"
				cCondPgPE := ExecBlock("A140ICOND",.F.,.F.,{aCab[nPosFor,2],aCab[nPosLoj,2],cCondPg})
				If ValType(cCondPgPE) == "C" .And. SE4->(dbSeek(cFilSE4 + cCondPgPE))
					cCondPg := cCondPgPE
				EndIf
			EndIf

			If !Empty(cCondPg)
				If nPosCond > 0
					aCab[nPosCond][2] := cCondPg
				Else
					aAdd(aCab,{"F1_COND",cCondPg, NIL})
				Endif
			Endif
		Endif
	Elseif nOpc == 2
		If (!lTes .And. nPosCond > 0) .Or. (lTes .And. !lGerDupl .And. nPosCond > 0) .Or. (nPosCond > 0 .And. aCab[nPosTpNF,2] == "D")
			aDel(aCab,nPosCond)
			aSize(aCab,Len(aCab)-1)
		Endif
	Endif

	RestArea(aAreaSF4)
	RestArea(aAreaSE4)
	RestArea(aAreaSA1)
	RestArea(aAreaSA2)
	RestArea(aAreaSF1)
	RestArea(aAreaSF2)
	RestArea(aAreaSC7)

Return aCab

//-------------------------------------------------------------------
/*/{Protheus.doc} COMCOLTES
Busca pela TES para o documento

@author	rodrigo.mpontes
@since 22/4/20
/*/
//-------------------------------------------------------------------

Static Function COMCOLTES(cTipoDoc,nComCol1,lCteClass,cFilSA5,cFilSB1,cFilSF4,cFilSDS)

	Local aArea		:= GetArea()
	Local aAreaSB1 	:= SB1->(GetArea())
	Local aAreaSF4 	:= SF4->(GetArea())
	Local aAreaSE4 	:= SE4->(GetArea())
	Local aAreaSA5 	:= SA1->(GetArea())
	Local cCodTes	:= ""
	Local cCodTesPE	:= ""
	Local cCpo		:= ""
	Local aRet		:= {}
	Local lFindTes	:= .F.
	Local lErroTes	:= .F.
	Local lCOMCOLF4	:= ExistBlock("COMCOLF4")
	Local lDupl		:= .F.
	Local lCpoGer	:= SuperGetMV("MV_COLTEG",.F.,.F.)
	Local lRet		:= .T.
	Local oXMLPE	:= Nil
	Local lErrCTeg	:= SuperGetMV("MV_ERRCTEG",.F.,.F.)

	If nComCol1 == 2 .Or. lCteClass
		cCpo := "D1_TES"
	Elseif nComCol1 == 1
		cCpo := "D1_TESACLA"
	Else
		If lCpoGer //MV_COLTEG
			cCpo := "D1_TES"
		Else
			cCpo := "D1_TESACLA"
		Endif
	Endif

	If cTipoDoc == "C"
		If !Empty(SDT->DT_TES)
			cCodTes := SDT->DT_TES
			cCpo := "D1_TES"
			aRet := {.T.,cCpo,cCodTes}
			lFindTes := .T.
		Endif

		If !lFindTes
			SA5->(dbSetOrder(1))
			If SA5->(dbSeek(cFilSA5+SDT->(DT_FORNEC+DT_LOJA+DT_COD))) .And. Empty(SA5->A5_TESCP)
				If cCpo == "D1_TES"
					lErroTes := .T.
				Endif
			Else
				cCodTes := SA5->A5_TESCP
				aRet := {.T.,cCpo,cCodTes}
				lFindTes := .T.
			Endif
		Endif

		If !lFindTes
			cCodTes := GetAdvFVal("SB1","B1_TE",cFilSB1 + SDT->DT_COD,1)
			If !Empty(cCodTes)
				aRet := {.T.,cCpo,cCodTes}
				lFindTes := .T.
			Endif
		Endif

	Elseif cTipoDoc == "T"
		If !Empty(SDT->DT_TES)
			cCodTes := SDT->DT_TES
			cCpo := "D1_TES"
			aRet := {.T.,cCpo,cCodTes}
			lFindTes := .T.
		Endif

		If !lFindTes
			oXMLPE := COMCOLXML(cFilSDS,SDT->DT_DOC,SDT->DT_SERIE,SDT->DT_FORNEC,SDT->DT_LOJA)
			CTe_RetTES(oXMLPE,@cCodTes,NIL,3)
			If Empty(cCodTes)
				If cCpo == "D1_TES"
					lErroTes := .T.
				Endif
			Else
				aRet := {.T.,cCpo,cCodTes}
				lFindTes := .T.
			Endif
		Endif

		If !lFindTes
			cCodTes := GetAdvFVal("SB1","B1_TE",cFilSB1 + SDT->DT_COD,1)
			If !Empty(cCodTes)
				aRet := {.T.,cCpo,cCodTes}
				lFindTes := .T.
			Endif
		Endif
	Elseif cTipoDoc == "O"
		If !Empty(SDT->DT_TES)
			cCodTes := SDT->DT_TES
			cCpo := "D1_TES"
			aRet := {.T.,cCpo,cCodTes}
			lFindTes := .T.
		Endif

		If !lFindTes
			SA5->(dbSetOrder(1))
			If SA5->(dbSeek(cFilSA5+SDT->(DT_FORNEC+DT_LOJA+DT_COD))) .And. Empty(SA5->A5_TESBP)
				If cCpo == "D1_TES"
					lErroTes := .T.
				Endif
			Else
				cCodTes := SA5->A5_TESBP
				aRet := {.T.,cCpo,cCodTes}
				lFindTes := .T.
			Endif
		Endif

		If !lFindTes
			cCodTes := GetAdvFVal("SB1","B1_TE",cFilSB1 + SDT->DT_COD,1)
			If !Empty(cCodTes)
				aRet := {.T.,cCpo,cCodTes}
				lFindTes := .T.
			Endif
		Endif
	Elseif !(cTipoDoc $ "COT")
		If !Empty(SDT->DT_TES)
			cCodTes := SDT->DT_TES
			cCpo := "D1_TES"
			aRet := {.T.,cCpo,cCodTes}
			lFindTes := .T.
		Endif

		If !lFindTes .And. cTipoDoc == "D"
			SD2->(DbSetOrder(3))	// D2_FILIAL + D2_DOC + D2_SERIE + D2_D2_CLIENTE + D2_LOJA + D2_COD + D2_ITEM
			If SD2->(MsSeek(xFilial("SD2")+SDT->DT_NFORI+SDT->DT_SERIORI+SDS->DS_FORNEC+SDS->DS_LOJA+SDT->DT_COD+SDT->DT_ITEMORI))
				DbSelectArea("SF4")
				SF4->(DbSetOrder(1))

				cCodTes := GetAdvFVal("SF4","F4_TESDV",xFilial("SF4")+SD2->D2_TES,1)
				If !Empty(cCodTes)
					aRet := {.T.,cCpo,cCodTes}
					lFindTes := .T.
				Endif
			EndIf
		Endif

		If !lFindTes
			SC7->(DbSetOrder(14))
			If !Empty(SDT->DT_PEDIDO) .And. !Empty(SDT->DT_ITEMPC)
				If SC7->(DbSeek(xFilial("SC7")+SDT->DT_PEDIDO+SDT->DT_ITEMPC)) .And. !Empty(SC7->C7_TES)
					cCodTes := SC7->C7_TES
					aRet := {.T.,cCpo,cCodTes}
					lFindTes := .T.
				EndIf
			Endif
		Endif

		If !lFindTes
			cCodTes := MaTESInt(1,ColConDHJ(SDT->DT_CODCFOP),SDS->DS_FORNEC,SDS->DS_LOJA,If(cTipoDoc $ "DB","C","F"),SDT->DT_COD)
			If !Empty(cCodTes)
				aRet := {.T.,cCpo,cCodTes}
				lFindTes := .T.
			Endif
		Endif

		If !lFindTes
			cCodTes := GetAdvFVal("SB1","B1_TE",cFilSB1 + SDT->DT_COD,1)
			If !Empty(cCodTes)
				aRet := {.T.,cCpo,cCodTes}
				lFindTes := .T.
			Endif
		Endif
	Endif

	//Ponto de entrada para obter o codigo da TES
	If lCOMCOLF4
		cCodTesPE := ExecBlock("COMCOLF4",.F.,.F.,{SDT->DT_FORNEC,SDT->DT_LOJA,SDT->DT_COD,cCodTes})
		If ValType(cCodTesPE) == "C" .And. SF4->(dbSeek(cFilSF4 + cCodTesPE))
			cCodTes := cCodTesPE
			aRet := {.T.,cCpo,cCodTes}
			lFindTes := .T.
		EndIf
	EndIf

	If cTipoDoc == "C"
		If !lFindTes .And. lErroTes
			If !lErrCTeg
				aRet := {.F.,STR0028 + AllTrim(SDT->DT_COD) + STR0029 + AllTrim(SDS->DS_FORNEC) + '/' + AllTrim(SDS->DS_LOJA) + STR0030}
			Else
				aRet := {.T.,""}
			Endif
		Endif

	ElseIf cTipoDoc == "T"
		If !lFindTes .And. lErroTes
			If !lErrCTeg
				aRet := {.F.,STR0031}
			Else
				aRet := {.T.,""}
			Endif
		Elseif lFindTes .And. cCpo == "DT_TES" .And. SDS->DS_FRETE > 0
			lDupl := GetAdvFVal("SF4","F4_DUPLIC",cFilSF4 + Padr(cCodTes,TamSx3("F4_CODIGO")[1]),1) <> "N"
			If lDupl
				aRet := {.F.,"Por tratar-se de um CT-e onde não sera pago o valor de frete a TES não deve gerar duplicata."}
			Endif
		Endif

	Elseif cTipoDoc == "O"
		If !lFindTes .And. lErroTes
			If !lErrCTeg
				aRet := {.F.,STR0032 +AllTrim(SDT->DT_COD) +STR0029 +AllTrim(SDS->DS_FORNEC) +'/' +AllTrim(SDS->DS_LOJA) +STR0033}
			Else
				aRet := {.T.,""}
			Endif
		Endif

	Elseif !(cTipoDoc $ "COT") .And. lFindTes
		lQtdZero := GetAdvFVal("SF4","F4_QTDZERO",cFilSF4+cCodTes,1) == "1"
		lVlrZero := GetAdvFVal("SF4","F4_VLRZERO",cFilSF4+cCodTes,1) == "1"

		If SDT->DT_QUANT == 0 .And. SDT->DT_VUNIT == 0 //TES precisa ser Vlr Zero e Qtd Zero
			lRet := lQtdZero .And. lVlrZero
		Elseif SDT->DT_QUANT > 0 .And. SDT->DT_VUNIT == 0 //TES precisa ser Vlr Zero
			lRet := lVlrZero
		Elseif SDT->DT_QUANT == 0 .And. SDT->DT_VUNIT > 0 //TES precisa ser Qtd Zero
			lRet := lQtdZero
		Endif

		If !lRet
			aRet := {.F.,STR0063 + AllTrim(SDT->DT_ITEM) + STR0189}
		Endif
	Endif

	RestArea(aArea)
	RestArea(aAreaSB1)
	RestArea(aAreaSF4)
	RestArea(aAreaSE4)
	RestArea(aAreaSA5)

Return aRet

//-------------------------------------------------------------------
/*/{Protheus.doc} COLIMPMAN
Verifica se documento ja foi incluido de forma manual

@author	Totvs
@since 05/06/12
/*/
//-------------------------------------------------------------------

Static Function COLIMPMAN(aCabec)

	Local aArea	:= GetArea()
	Local nPFil	:= aScan(aCabec,{|x| AllTrim(x[1]) == "F1_FILIAL"})
	Local nPDoc	:= aScan(aCabec,{|x| AllTrim(x[1]) == "F1_DOC"})
	Local nPSer	:= aScan(aCabec,{|x| AllTrim(x[1]) == "F1_SERIE"})
	Local nPFor	:= aScan(aCabec,{|x| AllTrim(x[1]) == "F1_FORNECE"})
	Local nPLoj	:= aScan(aCabec,{|x| AllTrim(x[1]) == "F1_LOJA"})
	Local nPTip	:= aScan(aCabec,{|x| AllTrim(x[1]) == "F1_TIPO"})
	Local nPChv	:= aScan(aCabec,{|x| AllTrim(x[1]) == "F1_CHVNFE"})
	Local nTFil	:= TamSx3("F1_FILIAL")[1]
	Local nTDoc	:= TamSx3("F1_DOC")[1]
	Local nTSer	:= TamSx3("F1_SERIE")[1]
	Local nTFor	:= TamSx3("F1_FORNECE")[1]
	Local nTLoj	:= TamSx3("F1_LOJA")[1]
	Local nTTip	:= TamSx3("F1_TIPO")[1]
	Local nTChv	:= TamSx3("F1_CHVNFE")[1]
	Local cFil	:= ""
	Local cDoc	:= ""
	Local cSer	:= ""
	Local cFor	:= ""
	Local cLoj	:= ""
	Local cTip	:= ""
	Local cChv	:= ""
	Local lRet	:= .F.

	//Busca pela chave do documento
	If nPFil > 0 .And. nPChv > 0
		cFil		:= PadR(aCabec[nPFil,2],nTFil)
		cChv		:= PadR(aCabec[nPChv,2],nTChv)

		DbSelectArea("SF1")
		SF1->(DbSetOrder(8))
		If SF1->(DbSeek(cFil+cChv))
			lRet := .T.
		Endif
	Endif

	//Busca pelo numero+serie+fornecedor+loja+tipo
	If !lRet .And. nPFil > 0 .And. nPDoc > 0 .And. nPSer > 0 .And. nPFor > 0 .And. nPLoj > 0 .And. nPTip > 0
		cFil		:= PadR(aCabec[nPFil,2],nTFil)
		cDoc		:= PadR(aCabec[nPDoc,2],nTDoc)
		cSer		:= PadR(aCabec[nPSer,2],nTSer)
		cFor		:= PadR(aCabec[nPFor,2],nTFor)
		cLoj		:= PadR(aCabec[nPLoj,2],nTLoj)
		cTip		:= PadR(aCabec[nPTip,2],nTTip)

		DbSelectArea("SF1")
		SF1->(DbSetOrder(1))
		If SF1->(DbSeek(cFil+cDoc+cSer+cFor+cLoj+cTip))
			lRet := .T.
		Endif
	Endif

	RestArea(aArea)

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} MontaSF1
Monta cabecalho para rotina automatica com os dados do SDS posicionado.

@author	Totvs
@since 05/06/12
/*/
//-------------------------------------------------------------------

Static Function MontaSF1(lCteClass,nComCol1,lAtuImp)
	Local aRet	 	 	:= {}
	Local cTipoNF	 	:= ""
	Local aAreaSDS		:= SDS->(GetArea())
	Local lRemet		:= .F.
	Local cFilSDT 		:= xFilial("SDT")
	Local cHoraRMT 		:= SuperGetMv("MV_HORARMT",.F.,"2")
	Local lvldFret 		:= SuperGetMV("MV_VALFRET",.F.,.F.)
	Local lHoraNfe		:= SuperGetMv("MV_HORANFE",.F.,.F.)
	Local aHorario 		:= {}
	Local lNfOri   		:= .F.
	Local lF1CteOD   	:= SF1->(FieldPos("F1_UFORITR")) > 0 .And. SF1->(FieldPos("F1_MUORITR")) > 0 .And. SF1->(FieldPos("F1_UFDESTR")) > 0 .And. SF1->(FieldPos("F1_MUDESTR")) > 0
	Local lDSCteOD   	:= SDS->(FieldPos("DS_UFORITR")) > 0 .And. SDS->(FieldPos("DS_MUORITR")) > 0 .And. SDS->(FieldPos("DS_UFDESTR")) > 0 .And. SDS->(FieldPos("DS_MUDESTR")) > 0
	Local lPtoEnt		:= ExistBlock("A116ICOMP") .Or. ExistBlock("A116PRDF") .Or. ExistBlock("A116ITPCT") .Or. ExistBlock("A116ICTEN")

	Default lCteClass	:= .F.
	Default nComCol1	:= 0
	Default lAtuImp		:= .F.

	If SDS->DS_TIPO == "T"
		cTipoNF := "C"
	Elseif SDS->DS_TIPO == "O"
		cTipoNF := "N"
	Else
		cTipoNF := SDS->DS_TIPO
	Endif

	// Quando a empresa for remetente da mercadoria (FOB) nao deve passar F1_TPFRETE na rotina automatica, caso contrario vai cair na validacao A103FRETE que nao permite vincular pedido de compra a documentos com TPFRETE preenchido
	If SDS->DS_TIPO == "T" .And. SDS->DS_TPFRETE == "C"
		lRemet := .T.
	EndIf

	aAdd(aRet,{"F1_FILIAL",  SDS->DS_FILIAL,	Nil})

	If AllTrim(SDS->DS_ESPECI) == "CTE"
		SDT->(dbSetOrder(2))
		lNfOri := SDT->(dbSeek(cFilSDT+SDS->(DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)))
		If lNfOri .And. (AllTrim(SDT->DT_COD) $ AllTrim(SuperGetMV("MV_XMLPFCT",.F.,"")) .Or. (empty(SDT->DT_NFORI) .and. lPtoEnt ))

			If Empty(SDT->DT_CHVNFO)//Não possui nota fiscal de entrada origem
				cTipoNF := "N"
			Else
				cTipoNF := "C"
			EndIf

			// Verifica a TAG <TpCte> para analisar se a nota eh complementar.
			If SDS->DS_TPCTE == 'C' // CT-e de Complemento de Valores
				cTipoNF := "C"
			EndIf
			aAdd(aRet,{"F1_TIPO",cTipoNF,Nil})
		Else
			aAdd(aRet,{"F1_TIPO",cTipoNF,Nil})
		EndIf
	Elseif AllTrim(SDS->DS_ESPECI) == "CTEOS"
		SDT->(dbSetOrder(2))
		lNfOri := SDT->(dbSeek(cFilSDT+SDS->(DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)))
		If lNfOri .And. (AllTrim(SDT->DT_COD) $ AllTrim(SuperGetMV("MV_XMLPFCT",.F.,"")) .Or. (empty(SDT->DT_NFORI) .and. (ExistBlock("A116ICOMP") .Or. ExistBlock("A116PRDF") .Or. ExistBlock("A116ITPCT"))))
			cTipoNF := "N"
		Endif
		aAdd(aRet,{"F1_TIPO",  cTipoNF,			Nil})
	Else
		aAdd(aRet,{"F1_TIPO",  cTipoNF,			Nil})
	EndIf

	// Quando a empresa for remetente da mercadoria (FOB) e tiver Pedido nao deve passar F1_TPFRETE na rotina automatica, caso contrario vai cair na validacao A103FRETE que nao permite vincular pedido de compra a documentos com TPFRETE preenchido
	If lRemet
		SDT->(dbSetOrder(2))
		SDT->(MsSeek(xFilial("SDT")+SDS->(DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)))
		lRemet := !EMPTY(SDT->DT_PEDIDO) .And. !lvldFret
	EndIf

	aAdd(aRet,{"F1_FORMUL",  SDS->DS_FORMUL,	Nil})
	aAdd(aRet,{"F1_DOC",     SDS->DS_DOC,		Nil})
	aAdd(aRet,{"F1_SERIE",   SDS->DS_SERIE,		Nil})
	aAdd(aRet,{"F1_EMISSAO", SDS->DS_EMISSA,	Nil})
	aAdd(aRet,{"F1_FORNECE", SDS->DS_FORNEC,	Nil})
	aAdd(aRet,{"F1_LOJA",    SDS->DS_LOJA,		Nil})
	aAdd(aRet,{"F1_ESPECIE", SDS->DS_ESPECI,	Nil})
	aAdd(aRet,{"F1_DTDIGIT", dDataBase,			Nil})
	aAdd(aRet,{"F1_EST",     SDS->DS_EST,		Nil})

	If !lAtuImp
		aAdd(aRet,{"F1_CHVNFE",  SDS->DS_CHAVENF,	Nil})
	Endif

	If SDS->DS_TIPO <> "T"
		If !lAtuImp
			aAdd(aRet,{"F1_FRETE",   SDS->DS_FRETE,		Nil})
		Endif
	EndIf

	If !lAtuImp
		aAdd(aRet,{"F1_DESPESA", SDS->DS_DESPESA,	Nil})
		aAdd(aRet,{"F1_DESCONT", SDS->DS_DESCONT,	Nil})
		aAdd(aRet,{"F1_SEGURO",  SDS->DS_SEGURO,	Nil})
	Endif

	If !Empty(SDS->DS_TRANSP) .And. !lAtuImp
		aAdd(aRet,{"F1_TRANSP",SDS->DS_TRANSP,	Nil})
	EndIf

	If !lAtuImp
		aAdd(aRet,{"F1_PLACA",   SDS->DS_PLACA,		Nil})
		aAdd(aRet,{"F1_PLIQUI",  SDS->DS_PLIQUI	,	Nil})
		aAdd(aRet,{"F1_PBRUTO",  SDS->DS_PBRUTO	,	Nil})
		aAdd(aRet,{"F1_ESPECI1", SDS->DS_ESPECI1,	Nil})
		aAdd(aRet,{"F1_VOLUME1", SDS->DS_VOLUME1,	Nil})
		aAdd(aRet,{"F1_ESPECI2", SDS->DS_ESPECI2,	Nil})
		aAdd(aRet,{"F1_VOLUME2", SDS->DS_VOLUME2,	Nil})
		aAdd(aRet,{"F1_ESPECI3", SDS->DS_ESPECI3,	Nil})
		aAdd(aRet,{"F1_VOLUME3", SDS->DS_VOLUME3,	Nil})
		aAdd(aRet,{"F1_ESPECI4", SDS->DS_ESPECI4,	Nil})
		aAdd(aRet,{"F1_VOLUME4", SDS->DS_VOLUME4,	Nil})
		aAdd(aRet,{"F1_TPCTE"  , SDS->DS_TPCTE  ,	Nil})

		If !lRemet	// Nao deve passar TPFRETE quando for CT-e com pedido e a empresa for remetente da mercadoria (FOB). Para os outros casos deve passar,
			aAdd(aRet,{"F1_TPFRETE", SDS->DS_TPFRETE,	Nil})
		EndIf
	Endif

	If SDS->DS_BASEICM > 0
		aAdd(aRet,{"F1_BASEICM"	, SDS->DS_BASEICM	, Nil})
	EndIf

	If !lAtuImp
		aAdd(aRet,{"F1_CODNFE"	, SDS->DS_CODNFE	, Nil})
		aAdd(aRet,{"F1_NUMRPS"	, SDS->DS_NUMRPS	, Nil})
		aAdd(aRet,{"F1_NFELETR"	, SDS->DS_DOC		, Nil})
		aAdd(aRet,{"F1_EMINFE"	, SDS->DS_EMISSA	, Nil})
		aAdd(aRet,{"F1_HORNFE"	, SDS->DS_HORNFE	, Nil})
		aAdd(aRet,{"F1_ORIGEM"	, "COMXCOL"			, Nil})
	Endif

	If !lAtuImp .And. lHoraNfe
		//Parametro MV_HORARMT habilitado pega a hora do smartclient, caso contrario a hora do servidor
		If cHoraRMT == '1' //Horario do SmartClient
			aAdd(aRet,{"F1_HORA",GetRmtTime(), Nil})
		ElseIf cHoraRMT == '2' //Horario do servidor
			aAdd(aRet,{"F1_HORA",Time(), Nil})
		ElseIf cHoraRMT =='3' //Horario de acordo com o estado da filial corrente
			aHorario := A103HORA()
			If !Empty(aHorario[2])
				aAdd(aRet,{"F1_HORA",aHorario[2], Nil})
			EndIf
		Endif
	Endif

	//Modalidade transporte - CTe
	If !lAtuImp .And. SDS->DS_TIPO == "T" .And. SDS->(ColumnPos("DS_MODAL")) > 0
		aAdd(aRet,{"F1_MODAL"	, SDS->DS_MODAL	, Nil})
	Endif

	//-- Preenche condicao de pagamento para tipos de documento que geram NF
	Do Case
		Case SDS->DS_TIPO == "T" //-- Conhecimento de transporte
			//CTE com UF/Municipio de Origem e Destino
			If lF1CteOD .And. lDSCteOD .And. !Empty(SDS->DS_UFORITR) .And. !Empty(SDS->DS_MUORITR) .And. !Empty(SDS->DS_UFDESTR) .And. !Empty(SDS->DS_MUDESTR)
				aAdd(aRet,{"F1_UFORITR",SDS->DS_UFORITR,Nil})
				aAdd(aRet,{"F1_MUORITR",SDS->DS_MUORITR,Nil})
				aAdd(aRet,{"F1_UFDESTR",SDS->DS_UFDESTR,Nil})
				aAdd(aRet,{"F1_MUDESTR",SDS->DS_MUDESTR,Nil})
			Endif
	EndCase

	//Tipo de Complemento
	If cTipoNF == "C"
		If SDS->DS_TIPO == "T" //CTE
			aAdd(aRet,{"F1_TPCOMPL","3", Nil })
		ElseIf SDS->DS_TIPO == "C" //Complemento
			SDT->(dbSetOrder(2))
			SDT->(MsSeek(xFilial("SDT")+SDS->(DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)))
			If SDT->DT_QUANT > 0
				aAdd(aRet,{"F1_TPCOMPL","2", Nil })	// Complemento de Quantidade
			Else
				aAdd(aRet,{"F1_TPCOMPL","1", Nil })	// Complemento de Preco
			EndIf
		EndIf
	EndIf

	//-- Flag colab para tratamentos especificos
	aAdd(aRet,{"COLAB","S",NIL})

	RestArea(aAreaSDS)

Return aRet

//-------------------------------------------------------------------
/*/{Protheus.doc} MontaSD1
Monta itens para rotina automatica com os dados do SDS posicionado

@author	Totvs
@since 05/06/12
/*/
//-------------------------------------------------------------------

Static Function MontaSD1(lImposto,lCteClass,nComCol1,aItCSD)

	Local aRet	    := {}
	Local aSd1Dados	:= {}
	Local aAreaSDS	:= SDS->(GetArea())
	Local cFilSA5	:= xFilial("SA5")
	Local cFilSB1	:= xFilial("SB1")
	Local cFilSF4	:= xFilial("SF4")
	Local cFilSDT	:= xFilial("SDT")
	Local cOper		:= ""
	Local lTpCte  	:= .T.
	Local cFornOri	:= ""
	Local cLojaOri	:= ""
	Local lDTClasFis:= SDT->(FieldPos("DT_CLASFIS")) > 0
	Local lICMSSTRet:= SDT->(FieldPos("DT_ICMNDES")) > 0 .And. SDT->(FieldPos("DT_BASNDES")) > 0 .And. SDT->(FieldPos("DT_ALQNDES")) > 0
	Local lUnidMed  := SDT->(FieldPos("DT_UM")) > 0 .And. SDT->(FieldPos("DT_SEGUM")) > 0 .And. SDT->(FieldPos("DT_QTSEGUM")) > 0
	Local lDFabric  := SDT->(FieldPos("DT_DFABRIC")) > 0
	Local lMVLOTCOL	:= SuperGetMv("MV_LOTCOL",.F.,.F.)
	Local aAuxCSD 	:= {}
	Local aAux 		:= {}
	Local nPosCSD   := {}
	Local nX 		:= 1
	Local lTES 		:= .F.
	Local lCsdXML 		:= SuperGetMV( 'MV_CSDXML', .F., .F. ) .and. SDT->(FieldPos("DT_ITXML")) > 0 .and. SDT->(FieldPos("DT_UMXML")) > 0 .and. SDT->(FieldPos("DT_QTDXML")) > 0;
		.and. SDT->(FieldPos("DT_FATOR")) > 0 .and. FWSX3Util():GetFieldType( "D1_ITXML" ) == "C" .and. ChkFile("DKA");
		.and. ChkFile("DKB") .and. ChkFile("DKC") .and. ChkFile("D3Q")

	Default lImposto	:= .F.
	Default lCteClass	:= .F.
	Default nComCol1	:= 0
	Default aItCSD		:= {}

	SDT->(dbSetOrder(2))
	SDT->(dbSeek(cFilSDT+SDS->(DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)))
	While SDT->(!EOF()) .AND. SDT->(DT_FILIAL+DT_FORNEC+DT_LOJA+DT_DOC+DT_SERIE) == cFilSDT+SDS->(DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)
		aAdd(aRet,{})

		aAdd(aTail(aRet),{"D1_FILIAL", SDT->DT_FILIAL, 	 NIL})
		aAdd(aTail(aRet),{"D1_ITEM",   SDT->DT_ITEM, 	 NIL})
		aAdd(aTail(aRet),{"D1_COD",    SDT->DT_COD,	 NIL})

		//Local
		If !Empty(SDT->DT_LOCAL)
			aAdd(aTail(aRet),{"D1_LOCAL",    SDT->DT_LOCAL,	 NIL})
		Endif

		If !Empty(SDT->DT_PEDIDO)
			aAdd(aTail(aRet),{"D1_PEDIDO", SDT->DT_PEDIDO,	 NIL})
			aAdd(aTail(aRet),{"D1_ITEMPC", SDT->DT_ITEMPC,	 NIL})
		EndIf

		If !Empty(SDT->DT_NFORI)
			aAdd(aTail(aRet),{"D1_NFORI",  SDT->DT_NFORI,	 NIL})
			aAdd(aTail(aRet),{"D1_SERIORI",SDT->DT_SERIORI, NIL})
			aAdd(aTail(aRet),{"D1_ITEMORI",SDT->DT_ITEMORI, NIL})
		EndIf

		If lUnidMed
			aAdd(aTail(aRet),{"D1_UM"		, 	SDT->DT_UM,  NIL})
			If !Empty(SDT->DT_SEGUM)
				aAdd(aTail(aRet),{"D1_SEGUM"	, 	SDT->DT_SEGUM,  NIL})
				aAdd(aTail(aRet),{"D1_QTSEGUM"	, 	SDT->DT_QTSEGUM,  NIL})
			EndIf
		Endif

		If !SDS->DS_TIPO $ "C"
			If SDS->DS_TIPO == "T"
				// Verifica a TAG <TpCte> para analisar se a nota eh complementar.
				lTpCte := .T.

				If SDS->DS_TPCTE == 'C' .Or. (SDS->DS_TPCTE == 'N' .And. !Empty(SDT->DT_NFORI)) // CT-e de Complemento de Valores
					lTpCte := .F.
				EndIf

				If lTpCte
					aAdd(aTail(aRet),{"D1_QUANT",  SDT->DT_QUANT, 	 NIL})
					aAdd(aTail(aRet),{"D1_SLDEXP",  SDT->DT_QUANT, 	 NIL})
				EndIf

				cFornOri := Posicione("SF1",8,xFilial("SF1") + SDT->DT_CHVNFO,"F1_FORNECE")
				cLojaOri := Posicione("SF1",8,xFilial("SF1") + SDT->DT_CHVNFO,"F1_LOJA")
				aSd1Dados:= GetAdvFval("SD1",{"D1_CONTA","D1_CC"},xFilial('SD1') + SDT->DT_NFORI + SDT->DT_SERIORI + cFornOri + cLojaOri + SDT->DT_COD + SDT->DT_ITEMORI,1)

				If Len(aSd1Dados) > 0 .And. (!Empty(aSd1Dados[1]) .Or. !Empty(aSd1Dados[2]))
					aAdd(aTail(aRet),{"D1_CONTA",aSd1Dados[1], NIL})
					aAdd(aTail(aRet),{"D1_CC",aSd1Dados[2], NIL})
				EndIf
			Else
				aAdd(aTail(aRet),{"D1_QUANT",  SDT->DT_QUANT, 	 NIL})
				aAdd(aTail(aRet),{"D1_SLDEXP",  SDT->DT_QUANT, 	 NIL})
			EndIf
		Elseif SDS->DS_TIPO == "C" .And. SDT->DT_QUANT > 0 //Complemento de Quantidade
			aAdd(aTail(aRet),{"D1_QUANT",  SDT->DT_QUANT, 	 NIL})
			aAdd(aTail(aRet),{"D1_SLDEXP",  SDT->DT_QUANT, 	 NIL})
		EndIf

		aAdd(aTail(aRet),{"D1_VUNIT",  SDT->DT_VUNIT, 	 NIL})

		If SDS->DS_TIPO $ "CT"
			aAdd(aTail(aRet),{"D1_TOTAL",SDT->DT_VUNIT,NIL})
		Else
			aAdd(aTail(aRet),{"D1_TOTAL",SDT->DT_TOTAL,NIL})
		EndIf

		cOper := ColConDHJ(SDT->DT_CODCFOP)

		If !Empty(cOper)
			aAdd(aTail(aRet),{"D1_OPER", cOper, NIL})
		EndIf

		aAdd(aTail(aRet),{"D1_VALFRE",	SDT->DT_VALFRE,	 NIL})
		aAdd(aTail(aRet),{"D1_SEGURO",	SDT->DT_SEGURO,	 NIL})
		aAdd(aTail(aRet),{"D1_DESPESA",	SDT->DT_DESPESA, NIL})
		aAdd(aTail(aRet),{"D1_VALDESC", SDT->DT_VALDESC, NIL})

		If SDT->DT_PICM > 0
			aAdd(aTail(aRet),{"D1_PICM", SDT->DT_PICM, Nil })
		EndIf

		aAdd(aTail(aRet),{"CFOP", SDT->DT_CFOP, Nil }) //-- "CFOP" Variável ao qual armazena o valor do campo DT_CFOP

		If !Empty(SDT->DT_FCICOD)
			aAdd(aTail(aRet),{"D1_FCICOD", SDT->DT_FCICOD, Nil}) // Armazena o valor do campo DT_FCICOD
		EndIf

		If Rastro(SDT->DT_COD) .And. !Empty(SDT->DT_LOTE) .And. !Empty(SDT->DT_DTVALID) .And. (Rastro(SDT->DT_COD))
			If !lMVLOTCOL
				aAdd(aTail(aRet),{"D1_LOTECTL", SDT->DT_LOTE   , Nil})
			Else
				aAdd(aTail(aRet),{"D1_LOTECTL","", Nil})
				aAdd(aTail(aRet),{"D1_LOTEFOR",SDT->DT_LOTE, Nil})
			Endif

			aAdd(aTail(aRet),{"D1_DTVALID", SDT->DT_DTVALID, Nil})

			If lDFabric
				aAdd(aTail(aRet),{"D1_DFABRIC", SDT->DT_DFABRIC, Nil})
			Endif
		EndIf

		//-- Realiza validacoes pertinentes e preenche TES
		aTes := COMCOLTES(SDS->DS_TIPO,nComCol1,lCteClass,cFilSA5,cFilSB1,cFilSF4,SDS->DS_FILIAL)

		If Len(aTes) > 0
			If !aTes[1]
				RecLock("SDS",.F.)
				Replace SDS->DS_DOCLOG With SDS->DS_DOCLOG + CRLF+CRLF + aTes[2]
				Replace SDS->DS_STATUS With 'E'
				SDS->(MsUnlock())
			Else
				If Len(aTes) > 2
					aAdd(aTail(aRet),{aTes[2],aTes[3], Nil })
					lTES := .T.
				Endif
			Endif
		Endif

		Do Case
			Case SDS->DS_TIPO == "C" //-- Complemento de preco
				//-- Valida vinculo com documento origem
				If Empty(SDT->DT_NFORI)
					RecLock("SDS",.F.)
					Replace SDS->DS_DOCLOG With SDS->DS_DOCLOG +CRLF+CRLF +STR0026 +SDT->DT_ITEM +STR0027 //-- Por tratar-se de um documento de complemento de preço, deverá ser realizado o vínculo com o documento origem para o item # deste documento.
					Replace SDS->DS_STATUS With 'E'
					SDS->(MsUnlock())
				EndIf
			Case SDS->DS_TIPO == "T" //-- Conhecimento de transporte
				aAdd(aTail(aRet),{"D1_ORIGLAN","FR", Nil })
		EndCase

		If lDTClasFis .And. !Empty(SDT->DT_CLASFIS)
			aAdd(aTail(aRet),{"D1_CLASFIS", 	SDT->DT_CLASFIS,  NIL})
		Endif

		If lICMSSTRet .And. SDS->DS_TIPO <> "T"
			aAdd(aTail(aRet),{"D1_BASNDES", 	SDT->DT_BASNDES,  NIL})
			aAdd(aTail(aRet),{"D1_ICMNDES", 	SDT->DT_ICMNDES,  NIL})
			aAdd(aTail(aRet),{"D1_ALQNDES", 	SDT->DT_ALQNDES,  NIL})
		Endif

		if lCsdXml .and. SDS->DS_TIPO == "N" .and. lTES
			aAdd(aTail(aRet),{"D1_ITXML", 	SDT->DT_ITXML,  NIL})

			nPosCSD := aScan(aAuxCSD, {|x|AllTrim(x[1])== SDT->DT_ITXML })
			if nPosCSD == 0
				aAdd(aAuxCSD,{;
					SDT->DT_ITXML,;
					SDT->DT_QUANT,;
					SDT->DT_FATOR,;
					Alltrim(SDT->DT_DESCFOR),;
					})
			else
				aAuxCSD[nPosCSD][2] += SDT->DT_QUANT
			endif

		endif

		SDT->(dbSkip())
	EndDo

	if !empty(aAuxCSD)
		for nX := 1 to len(aAuxCSD)
			aAux := {}
			aadd(aAux,{"DKA_ITXML" 	 ,aAuxCSD[nX][1] ,NIL})
			aadd(aAux,{"DKA_QTDXML"  ,aAuxCSD[nX][2] ,NIL})
			aadd(aAux,{"DKA_FATOR"   ,aAuxCSD[nX][3] ,NIL})
			aadd(aAux,{"DKA_DESCFO"  ,aAuxCSD[nX][4] ,NIL})
			aAdd(aItCSD,aAux)
		next nX
	endif

	RestArea(aAreaSDS)

Return aRet

//-------------------------------------------------------------------
/*/{Protheus.doc} COLNfeAut
Validacao das tabelas SE4/SF4 para geracao automatica dos documentos

@param	aCabec		Cabecalho documento de entrada
@param	aItens		Itens documento de entrada

@author	Rodrigo Toledo
@since 04/10/12
/*/
//-------------------------------------------------------------------

Static Function COLNfeAut(aCabec,aItens)

	Local lRet     	:= .T.
	Local nPosTpNF 	:= aScan(aCabec,{|x| AllTrim(x[1]) == "F1_TIPO"})
	Local lCOMCOL2	:= ExistBlock("COMCOL2")

	//Verifica se o tipo NF esta contido no paramentro para geracao automatica
	If aCabec[nPosTpNF,2] == "N" .And. lCOMCOL2
		lRet := ExecBlock("COMCOL2",.F.,.F.,{aCabec,aItens})
		If ValType(lRet) <> "L"
			lRet := .F.
		EndIf
	EndIf

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} COMCOLREP
Reprocessar documentos

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Function COMCOLREP()

	Local oDlgRep	:= NIL
	Local oBrwErEx	:= NIL
	Local oSize		:= Nil
	Local aPosObj 	:= {}
	Local aHeadCols := {" ",RetTitle("DS_ARQUIVO"),RetTitle("DS_DOC"),SerieNfId("SDS",7,"DS_SERIE"),RetTitle("DS_NOMEFOR"),STR0145,STR0146,STR0147,STR0148}
	Local aRadio	:= {"Erro","Excluidos"}
	Local aParam	:= {}
	Local aAux		:= {}
	Local cCodEdi	:= ""
	Local cCodErro	:= ""
	Local nI		:= 0
	Local nRadio	:= 1
	Local lOk 		:= .F.
	Local lCkoCnpjIM:= CKO->(FieldPos("CKO_CNPJIM")) > 0
	Local lCkoRepro := CKO->(FieldPos("CKO_DOC")) > 0 .And. CKO->(FieldPos("CKO_SERIE")) > 0 .And. CKO->(FieldPos("CKO_NOMFOR")) > 0 .And. !Empty(SDS->(IndexKey(4))) .And. COLX1COLREP()

	Private cErroCol	:= "Detalhe da inconsistência...."

	If lCkoRepro
		Pergunte("COLREP",.F.)
		aAdd(aParam,Iif(MV_PAR01==2,.T.,.F.))
		aAdd(aParam,MV_PAR02)
		aAdd(aParam,MV_PAR03)

		aAux		:= Separa(AllTrim(MV_PAR04),";")
		For nI := 1 To Len(aAux)
			If Empty(cCodEdi)
				cCodEdi := "'" + aAux[nI] + "'"
			Else
				cCodEdi += ",'" + aAux[nI] + "'"
			Endif
		Next nI

		aAdd(aParam,cCodEdi)

		aAux		:= Separa(AllTrim(MV_PAR05),";")
		For nI := 1 To Len(aAux)
			If Empty(cCodErro)
				cCodErro := "'" + aAux[nI] + "'"
			Else
				cCodErro += ",'" + aAux[nI] + "'"
			Endif
		Next nI

		aAdd(aParam,cCodErro)
	Endif

	If lCkoCnpjIM
		aAdd(aHeadCols,RetTitle("CKO_CNPJIM"))
	EndIf

	oSize := FwDefSize():New(.F.)

	oSize:AddObject('GRID'	,100,90,.T.,.T.)
	oSize:AddObject('DETAIL',100,10,.T.,.T.)

	oSize:aMargins 	:= { 3, 3, 3, 3 }
	oSize:Process()

	aPosObj := { 3, 3, oSize:GetDimension("GRID","COLEND")-86,oSize:GetDimension("GRID","LINEND")+45}

	Define MsDialog oDlgRep Title STR0035 From oSize:aWindSize[1],oSize:aWindSize[2] To oSize:aWindSize[3],oSize:aWindSize[4] Pixel //-- Reprocessar Documentos

	oBrwErEx := TWBrowse():New(aPosObj[1],aPosObj[2],aPosObj[3],aPosObj[4],,aHeadCols,,oDlgRep,,,,,,,,,,,,.F.,,.T.,,.F.,,,)
	oBrwErEx:bLDblClick   := {|| COLREPCLICK(1,oBrwErEx:aArray,nRadio,oBrwErEx)}
	oBrwErEx:bHeaderClick := {|| COLREPCLICK(2,oBrwErEx:aArray,nRadio,oBrwErEx)}
	oBrwErEx:bDrawSelect  := {|| Iif(nRadio == 2,cErroCol := "",cErroCol := oBrwErEx:aArray[oBrwErEx:nAt,11]), oErro:Refresh() }
	oBrwErEx:bChange  	  := {|| Iif(nRadio == 2,cErroCol := "",cErroCol := oBrwErEx:aArray[oBrwErEx:nAt,11]), oErro:Refresh() }

	oErro 	:= tMultiget():new(oSize:GetDimension("DETAIL","LININI")+55,oSize:GetDimension("DETAIL","COLINI"),{|u| if(pCount()>0,cErroCol:=u,cErroCol)},oDlgRep,oSize:GetDimension("DETAIL","COLEND")-86,oSize:GetDimension("GRID","LINEND")-60,,,,,,.T.,,,{||.F.})

	oRadio := TRadMenu():New (oSize:GetDimension("GRID","LININI")+005,oSize:GetDimension("GRID","COLEND")-75,aRadio,,oDlgRep,,,,,,,,70,25,,,,.T.)
	oRadio:bSetGet := {|u| Iif (PCount()==0,nRadio,nRadio:=u)}
	oRadio:bChange := {|u| COLATUREP(@oBrwErEx,oErro,nRadio,aParam)}

	oRepOk	:= TButton():New(oSize:GetDimension("GRID","LININI")+045,oSize:GetDimension("GRID","COLEND")-75,"Ok",oDlgRep,{|| COLREPARQ(.T.,.F.,oBrwErEx), lOk := .T., oDlgRep:End()}, 70,12,,,.F.,.T.,.F.,,.F.,,,.F. )
	oRepEx	:= TButton():New(oSize:GetDimension("GRID","LININI")+065,oSize:GetDimension("GRID","COLEND")-75,"Excluir",oDlgRep,{|| Iif(COLREPARQ(.T.,.T.,oBrwErEx),oDlgRep:End(),.T.)}, 70,12,,,.F.,.T.,.F.,,.F.,,,.F. )
	oRepPq	:= TButton():New(oSize:GetDimension("GRID","LININI")+085,oSize:GetDimension("GRID","COLEND")-75,"Pesquisar",oDlgRep,{|| PesquiArq(oBrwErEx)}, 70,12,,,.F.,.T.,.F.,,.F.,,,.F. )
	oRepSa	:= TButton():New(oSize:GetDimension("GRID","LININI")+105,oSize:GetDimension("GRID","COLEND")-75,"Sair",oDlgRep,{|| oDlgRep:End()}, 70,12,,,.F.,.T.,.F.,,.F.,,,.F. )

	COLATUREP(@oBrwErEx,oErro,1,aParam)

	Activate MsDialog oDlgRep Centered

	If lOk .And. FindFunction("SCHEDREP")
		SCHEDREP()
	Endif

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} COLATUREP
Pesquisa arquivo na tela de reprocessar

@param	oBrwErEx	Objeto para pesquisa
@param	oErro		Objeto para mensagem de erro
@param	nOpc		1-Erro / 2-Excluido
@param	aParam		Parametros para filtro

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Static Function COLATUREP(oBrwErEx,oErro,nOpc,aParam)

	Carga(@oBrwErEx,nOpc,aParam)

	If nOpc == 1
		cErroCol := oBrwErEx:aArray[oBrwErEx:nAt,11]
	Elseif nOpc == 2
		cErroCol:=""
	Endif
	oErro:Refresh()
	oBrwErEx:Refresh()

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} PesquiArq
Pesquisa arquivo na tela de reprocessar

@param	oBrowse	Objeto para pesquisa

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Static Function PesquiArq(oBrowse)

	Local lProc      := .F.
	Local cCpoPesq   := Space(100)
	Local cOrdem     := "Arquivo"
	Local nSeek      := 0
	Local nOrdem     := 1
	Local lCkoCnpjIM := CKO->(FieldPos("CKO_CNPJIM")) > 0

	Define MSDialog oDlgPesq Title STR0039 From 00,00 To 100,490 Pixel //-- Pesquisar

	If lCkoCnpjIM
		@05,05 ComboBox oCbo1 Var cOrdem Items {RetTitle("DS_ARQUIVO"),RetTitle("DS_DOC"),;
			SerieNfId("SDS",7,"DS_SERIE"),RetTitle("DS_NOMEFOR"),RetTitle("CKO_CNPJIM")} Size 206,36 Pixel Of oDlgPesq On Change (nOrdem := oCbo1:nAT)
	Else
		@05,05 ComboBox oCbo1 Var cOrdem Items {RetTitle("DS_ARQUIVO"),RetTitle("DS_DOC"),;
			SerieNfId("SDS",7,"DS_SERIE"),RetTitle("DS_NOMEFOR")} Size 206,36 Pixel Of oDlgPesq On Change (nOrdem := oCbo1:nAT)
	EndIf
	@22,05 MSGet oGet Var cCpoPesq Size 206,10 Pixel Of oDlgPesq
	Define SButton From 05,215 Type 1 Of oDlgPesq Enable Action (lProc := .T., oDlgPesq:End())
	Define SButton From 20,215 Type 2 Of oDlgPesq Enable Action oDlgPesq:End()

	Activate MSDialog oDlgPesq Center

	If lProc
		cCpoPesq := Upper(AllTrim(cCpoPesq))
		If nOrdem == 1 //-- Arquivo
			aSort(oBrowse:aArray,,,{|x,y| x[2] < y[2]})
			nSeek := aScan(oBrowse:aArray,{|x| Upper(AllTrim(x[2])) == cCpoPesq})
		ElseIf nOrdem == 2 //-- Documento
			aSort(oBrowse:aArray,,,{|x,y| x[3] < y[3]})
			nSeek := aScan(oBrowse:aArray,{|x| Upper(Left(x[3],Len(cCpoPesq))) == cCpoPesq})
		ElseIf nOrdem == 3 //-- Serie
			aSort(oBrowse:aArray,,,{|x,y| x[4] < y[4]})
			nSeek := aScan(oBrowse:aArray,{|x| Upper(AllTrim(x[4])) == cCpoPesq})
		ElseIf nOrdem == 4 //-- Razao Social
			aSort(oBrowse:aArray,,,{|x,y| x[5] < y[5]} )
			nSeek := aScan(oBrowse:aArray,{|x| Upper(AllTrim(x[5])) == cCpoPesq})
		ElseIf nOrdem == 5 //-- CNPJ Importado
			aSort(oBrowse:aArray,,,{|x,y| x[10] < y[10]} )
			nSeek := aScan(oBrowse:aArray,{|x| Upper(AllTrim(x[10])) == cCpoPesq})
		EndIf
		If nSeek > 0
			oBrowse:nAT := nSeek
			oBrowse:Refresh()
			oBrowse:SetFocus()
		Else
			Aviso(STR0004,STR0041,{"OK"}) //-- Atenção # A busca não encontrou resultados.
		EndIf
	EndIf

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} COLREPARQ
Atualiza Flag do arquivo para reprocessar

@param	lProc		Reprocessar arquivos (.T.)
@param	lExcArq		Excluir arquivos (.T.)
@param	oBrwErEx	oBrowse dos arquivos de erro / excluidos

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Static Function COLREPARQ(lProc,lExcArq,oBrwErEx)

	Local nI		:= 0
	Local lAviso	:= .F.
	Local lExcluido	:= .F.
	Local lMVImpXML := SuperGetMv("MV_IMPXML",.F.,.F.) .And. CKO->(FieldPos("CKO_ARQXML")) > 0 .And. !Empty(CKO->(IndexKey(5)))

	If lExcArq
		If !MsgYesNo("Deseja excluir arquivos do reprocessar.","Excluir")
			lProc := .F.
		Endif
	Endif

	If lProc
		For nI := 1 To Len(oBrwErEx:aArray)
			If oBrwErEx:aArray[nI,1]
				If !lExcArq //Reprocessar arquivos
					ColGrvFil(oBrwErEx:aArray[nI,2],"2",oBrwErEx:aArray[nI,6],oBrwErEx:aArray[nI,7],oBrwErEx:aArray[nI,10])
					lAviso          := .T. //Exibe o Aviso se pelo menos um arquivo for selecionado
					COLREPATU(SubStr(oBrwErEx:aArray[nI,2],1,3),"2",oBrwErEx:aArray[nI,2],"0")
				Else
					lExcluido := .T.
					COLATUFLAG(oBrwErEx:aArray[nI,2],"4")
				Endif
			Endif
		Next nI

		If lAviso
			Aviso(STR0004,Iif(lMVImpXML,STR0191,STR0040),{"OK"}) //-- Atenção # Os arquivos selecionados foram movidos para a fila de reprocessamento. Quando disponíveis, os documentos serão apresentados no Monitor TOTVS Colaboração.
		Endif

		If lExcluido
			Aviso(STR0004,"Os arquivos selecionados foram excluidos do reprocessar.",{"OK"})
		Endif
	Endif

Return lProc

//-------------------------------------------------------------------
/*/{Protheus.doc} COLREPATU
Atualiza Flag do arquivo para reprocessar

@param	cQueue		Nomenclatura do arquivo (109/214/319/273)
@param	cFlag		Flag do arquivo
@param	cArq		Arquivo a ser atualizado

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Static Function COLREPATU(cQueue,cFlag,cArq,cNewFlag)
	oColab 			:= ColaboracaoDocumentos():New()
	oColab:cQueue   := cQueue
	oColab:cModelo  := ""
	oColab:cTipoMov := "2"
	oColab:cFlag    := cFlag
	oColab:cNomeArq := cArq
	oColab:Consultar()
	oColab:cFlag    := cNewFlag
	oColab:FlegaDocumento()
Return

//-------------------------------------------------------------------
/*/{Protheus.doc} COLATUFLAG
Atualiza Flag do arquivo

@param	cArq		Arquivo a ser atualizado
@param	cFlag		Flag para atualização (3-Duplicado/4-Excluido)

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Static Function COLATUFLAG(cArq,cFlag)

	Local aArea		:= GetArea()
	Local nTamCKO	:= TamSx3("CKO_ARQUIV")[1]
	Local cArqCKO	:= PadR(cArq,nTamCKO)

	DbSelectArea("CKO")
	CKO->(DbSetOrder(1))
	If CKO->(DbSeek(cArqCKO))
		If Reclock("CKO",.F.)
			CKO->CKO_FLAG := cFlag
			CKO->(MsUnlock())
		ENDIF
	Endif

	RestArea(aArea)

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} Carga
Carga de arquivos com erros e excluidos para reprocessar

@param	oBrowse		Objeto oBrowse (Erro/Excluidos)
@param	nCombo		1-Erro / 2-Excluidos
@param	aParam		Parametro pergunte COLREP

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Static Function Carga(oBrowse,nCombo,aParam)

	Local aArea			:= SDS->(GetArea())
	Local aArquivo		:= {}
	Local aDocs			:= {}
	Local lVldImport	:= Iif(nCombo==1,.F.,.T.) //Erro = .F. / Excluido = .T.
	Local lAddArq		:= .T.
	Local oColab		:= NIL
	Local nX			:= 1
	Local cQry			:= ""
	Local aCkoDados		:= {}
	Local cAliasExc		:= GetNextAlias()
	Local lFilRep		:= SuperGetMV("MV_FILREP",.F.,.T.)
	Local nTamCKOARQ	:= TamSX3("CKO_ARQUIV")[1]
	Local lUsaFiltro	:= .F.
	Local dDtDE			:= CtoD("//")
	Local dDtATE		:= CtoD("//")
	Local cCodEdi		:= ""
	Local cCodErro		:= ""
	Local aCodEdi		:= {}
	Local aAux			:= {}
	Local lCkoCnpjIM 	:= CKO->(FieldPos("CKO_CNPJIM")) > 0
	Local lCkoRepro  	:= CKO->(FieldPos("CKO_DOC")) > 0 .And. CKO->(FieldPos("CKO_SERIE")) > 0 .And. CKO->(FieldPos("CKO_NOMFOR")) > 0 .And. !Empty(SDS->(IndexKey(4))) .And. COLX1COLREP()

	If Len(aParam) > 0
		lUsaFiltro	:= aParam[1]
		dDtDE		:= aParam[2]
		dDtATE		:= aParam[3]
		cCodEdi		:= aParam[4]
		cCodErro	:= aParam[5]
		aCodEdi		:= Separa(StrTran(cCodEdi,"'",""),",")
	Endif

	If nCombo == 1
		oColab 				:= ColaboracaoDocumentos():New()
		oColab:cModelo 		:= ""
		oColab:cTipoMov 	:= '2'
		oColab:cFlag 		:= '2'
		oColab:cEmpProc 	:= cEmpAnt
		oColab:cFilProc 	:= cFilAnt
		oColab:aQueue 		:= Iif(lUsaFiltro .And. Len(aCodEdi) > 0,aCodEdi,{"109","319","214","273"})
		oColab:cQueue 		:= "109"

		If lUsaFiltro
			oColab:aParamMonitor:= {lUsaFiltro,dDtDE,dDtATE,cCodEdi,cCodErro}
		Endif

		oColab:buscaDocumentosFilial()

		If Len(oColab:aNomeArq)
			For nX := 1 To Len(oColab:aNomeArq)
				oColab:cNomeArq := oColab:aNomeArq[nX,1]
				oColab:cFlag := '2'
				oColab:Consultar()

				If lCkoRepro
					aCkoDados := GetAdvFVal("CKO",{"CKO_CODEDI","CKO_DOC","CKO_SERIE","CKO_NOMFOR"},Padr(oColab:aNomeArq[nX,1],nTamCKOARQ),1)
				Else
					aCkoDados := GetAdvFVal("CKO",{"CKO_CODEDI","CKO_XMLRET","",""},Padr(oColab:aNomeArq[nX,1],nTamCKOARQ),1)
					aAux	  := COLGRVDADOS(aCkoDados[2])
					If Len(aAux) > 0
						aCkoDados[2] := aAux[1]
						aCkoDados[3] := aAux[2]
						aCkoDados[4] := aAux[3]
					Endif
				Endif

				aAdd(aDocs,{oColab:aNomeArq[nX,1],;
					aCkoDados[2],;
					aCkoDados[3],;
					aCkoDados[4],;
					oColab:cEmpProc,;
					oColab:cFilProc,;
					oColab:cCodErrErp,;
					oColab:cMsgErrErp,;
					oColab:cCnpjImp,;
					oColab:cMsgErr024,;
					aCkoDados[1],;
					""})
			Next nX
		Endif
	Elseif nCombo == 2
		cQry := " SELECT DS_ARQUIVO, DS_DOC, DS_SERIE, DS_CHAVENF"
		cQry += " FROM " + RetSqlName("SDS") + " DS"
		cQry += "    , " + RetSqlName("CKO") + " CKO"
		cQry += " WHERE DS.D_E_L_E_T_ = '*'"

		If lFilRep
			cQry += " AND DS.DS_FILIAL = '" + cFilAnt + "'"
		Endif

		If lUsaFiltro
			If !Empty(dDtDE) .And. !Empty(dDtATE)
				cQry += " AND DS.DS_DATAIMP BETWEEN '" + DtoS(dDtDE) + "' AND '" + DtoS(dDtATE) + "'"
			EndIf
		Endif

		cQry += " AND DS.DS_ARQUIVO = CKO.CKO_ARQUIV"
		cQry += " AND CKO.CKO_FLAG = '1'"

		If lUsaFiltro
			If !Empty(cCodEdi)
				cQry += "             AND CKO.CKO_CODEDI IN (" + cCodEdi + ")"
			Endif
		Endif

		cQry += " AND CKO.D_E_L_E_T_ = ' '"
		cQry += " GROUP BY DS_FILIAL, DS_ARQUIVO, DS_DOC, DS_SERIE, DS_CHAVENF"

		dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQry),cAliasExc,.T.,.T.)

		While (cAliasExc)->(!Eof())
			If lCkoRepro
				aCkoDados := GetAdvFVal("CKO",{"CKO_CODEDI","CKO_EMPPRO","CKO_FILPRO",;
					"CKO_CODERR","CKO_MSGERR","CKO_CNPJIM","CKO_NOMFOR"},Padr((cAliasExc)->DS_ARQUIVO,nTamCKOARQ),1)
			Else
				aCkoDados := GetAdvFVal("CKO",{"CKO_CODEDI","CKO_EMPPRO","CKO_FILPRO",;
					"CKO_CODERR","CKO_MSGERR","CKO_CNPJIM","CKO_XMLRET"},Padr((cAliasExc)->DS_ARQUIVO,nTamCKOARQ),1)
				aAux	  := COLGRVDADOS(aCkoDados[7])
				If Len(aAux) > 0
					aCkoDados[7] := aAux[3]
				Endif
			Endif

			aAdd(aDocs,{(cAliasExc)->DS_ARQUIVO,;
				(cAliasExc)->DS_DOC,;
				(cAliasExc)->DS_SERIE,;
				aCkoDados[7],;
				aCkoDados[2],;
				aCkoDados[3],;
				aCkoDados[4],;
				Iif(!Empty(aCkoDados[4]),ColErroErp(aCkoDados[4]),""),;
				aCkoDados[6],;
				aCkoDados[5],;
				aCkoDados[1],;
				(cAliasExc)->DS_CHAVENF})
			(cAliasExc)->(DbSkip())
		Enddo

		(cAliasExc)->(DbCloseArea())
	Endif

	For nX := 1 To Len(aDocs)
		lAddArq := .T.

		If lVldImport
			If aDocs[nX,11] == "319" //NFS
				lAddArq := COLFINSDS(1,aDocs[nX,12])
			Else
				lAddArq := COLFINSDS(2,aDocs[nX,12])
			Endif
		Endif

		If lAddArq
			aAdd(aArquivo,{})
			aAdd(aTail(aArquivo),.F.)
			aAdd(aTail(aArquivo),aDocs[nX,01]) //-- Nome do arquivo
			aAdd(aTail(aArquivo),aDocs[nX,02]) //-- Numero do Doc.
			aAdd(aTail(aArquivo),aDocs[nX,03]) //-- Serie Doc.
			aAdd(aTail(aArquivo),If(lLGPDCOL,RetTxtLGPD(aDocs[nX,04],"A2_NOME"),aDocs[nX,04])) //-- Razao Social do fornecedor
			aAdd(aTail(aArquivo),aDocs[nX,05]) //-- Empresa
			aAdd(aTail(aArquivo),aDocs[nX,06]) //-- Filial
			aAdd(aTail(aArquivo),aDocs[nX,07]) //-- Codigo Erro
			aAdd(aTail(aArquivo),aDocs[nX,08]) //-- Mensagem Erro
			aAdd(aTail(aArquivo),If(lLGPDCOL,RetTxtLGPD(aDocs[nX,09],"A2_CGC"),aDocs[nX,09]))  //-- CNPJ Importação
			aAdd(aTail(aArquivo),If(lLGPDCOL,RetTxtLGPD(aDocs[nX,10],"A2_NOME"),aDocs[nX,10]))  //-- Detalhe Mensagem de Erro
		Endif
	Next nX

	If Len(aArquivo) > 0 .And. nCombo == 1
		aArquivo := COMXCOLDUP(aArquivo)
	Endif

	If Len(aArquivo) == 0
		aAdd(aArquivo,{})
		aAdd(aTail(aArquivo),.F.)
		aAdd(aTail(aArquivo),"")
		aAdd(aTail(aArquivo),"")
		aAdd(aTail(aArquivo),"")
		aAdd(aTail(aArquivo),"")
		aAdd(aTail(aArquivo),"")
		aAdd(aTail(aArquivo),"")
		aAdd(aTail(aArquivo),"")
		aAdd(aTail(aArquivo),"")
		aAdd(aTail(aArquivo),"")
		aAdd(aTail(aArquivo),"")
	EndIf

	oBrowse:SetArray(aArquivo)
	oBrowse:nAt := 1
	If lCkoCnpjIM
		oBrowse:bLine := {|| {If(aArquivo[oBrowse:nAT,1],oColOK,oColNo),aArquivo[oBrowse:nAt,02],aArquivo[oBrowse:nAt,03],aArquivo[oBrowse:nAt,04],aArquivo[oBrowse:nAt,05],aArquivo[oBrowse:nAt,06],aArquivo[oBrowse:nAt,07],aArquivo[oBrowse:nAt,08],aArquivo[oBrowse:nAt,09],aArquivo[oBrowse:nAt,10]}}
	Else
		oBrowse:bLine := {|| {If(aArquivo[oBrowse:nAT,1],oColOK,oColNo),aArquivo[oBrowse:nAt,02],aArquivo[oBrowse:nAt,03],aArquivo[oBrowse:nAt,04],aArquivo[oBrowse:nAt,05],aArquivo[oBrowse:nAt,06],aArquivo[oBrowse:nAt,07],aArquivo[oBrowse:nAt,08],aArquivo[oBrowse:nAt,09]}}
	EndIf
	oBrowse:Refresh()
	SDS->(RestArea(aArea))

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} COLREPCLICK
Função para selecionar arquivos a serem reprocessados

@param	nOpc		1 ou 3-Linha / 2 ou 4-Header / 5 - Header Monitor / 6 - Limpa Marca (Fechar Monitor) / 7 - Seleciona Monitor
@param	aArquivo	Array com os arquivos
@param	nCombo		1-Erro / 2-Excluidos / 3 ou 4-Edi e Erros
@param	oBrowse		Objeto Browse

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Function COLREPCLICK(nOpc,aArquivo,nCombo,oBrowse)

	Local nI		:= 0
	Local nRecno	:= 0
	Local nPosReg	:= 0
	Local cUpd		:= ""
	Local lCkoCnpjIM:= CKO->(FieldPos("CKO_CNPJIM")) > 0

	Default nOpc := 5

	If nOpc == 1 .Or. nOpc == 3 //Click linha
		aArquivo[oBrowse:nAt,1] := !aArquivo[oBrowse:nAt,1]
		If nOpc == 1
			If aArquivo[oBrowse:nAt,1] .And. Alltrim(aArquivo[oBrowse:nAt,8]) == 'COM042'
				aArquivo[oBrowse:nAt,1] := ColChanFil(@aArquivo,@oBrowse)
			Endif
		Endif
	Elseif nOpc == 2 .Or. nOpc == 4//Click Header
		For nI := 1 To Len(aArquivo)
			aArquivo[nI,1] := !aArquivo[nI,1]
			If nOpc == 2
				If aArquivo[nI,1] .And. Alltrim(aArquivo[nI,8]) == 'COM042'
					aArquivo[nI,1] := ColChanFil(@aArquivo,@oBrowse)
				Endif
			Endif
		Next nI
	Elseif nOpc == 5 //Click Header (Monitor)
		SDS->(DbGotop())
		nRecno		:= SDS->(Recno())

		While SDS->(!EOF())
			If SDS->DS_STATUS <> 'P'
				Reclock("SDS",.F.)
				SDS->DS_OK := If(SDS->DS_OK == cMarca,"",cMarca)
				SDS->(MsUnlock())

				nPosReg := aScan(aRegMark,{|x| x == SDS->(Recno())})

				//Armazena ou exclui os registros de aRegMark conforme a marcacao.
				If IsMark("DS_OK",cMarca)
					If nPosReg == 0
						aAdd(aRegMark,SDS->(Recno()))
					EndIf
				Else
					If nPosReg > 0
						aDel(aRegMark,nPosReg)
						aSize(aRegMark,(Len(aRegMark)-1))
					EndIf
				EndIf
			Endif
			SDS->(dbSkip())
		EndDo

		SDS->(dbGotop())
	Elseif nOpc == 6 //Limpa click (Monitor)
		cUpd := " UPDATE " + RetSqlName("SDS")
		cUpd += " SET DS_OK = ' '"
		cUpd += " WHERE DS_STATUS <> 'P'"
		cUpd += " AND DS_OK = '" + cMarca + "'"
		cUpd += " AND D_E_L_E_T_ = ' '"

		TCSqlExec(cUpd)
	Elseif nOpc == 7 //Seleção tela Monitor
		nRecno  := SDS->(Recno())
		nPosReg := aScan(aRegMark,{|x| x == nRecno})

		//Codigo para tratamento da marcacao de registros na MarkBrowse.
		RecLock("SDS",.F.)
		SDS->DS_OK := Iif( IsMark("DS_OK",cMarca) , Space(Len(SDS->DS_OK)) , cMarca )
		SDS->(MsUnlock())

		//Armazena ou exclui os registros de aRegMark conforme a marcacao.
		If IsMark("DS_OK",cMarca)
			If nPosReg == 0
				aAdd(aRegMark,SDS->(Recno()))
			EndIf
		Else
			If nPosReg > 0
				aDel(aRegMark,nPosReg)
				aSize(aRegMark,(Len(aRegMark)-1))
			EndIf
		EndIf
		MarkBRefresh()
	ElseIf nOpc == 8 //Header - Desvincular todos os pedidos - marca/desmarca todos
		For nI := 1 To Len(aArquivo)
			aArquivo[nI,1] := !aArquivo[nI,1]
		Next nI
		oBrowse:Refresh()
	Endif

	If nOpc == 1 .Or. nOpc == 2
		oBrowse:SetArray(aArquivo)
		If lCkoCnpjIM
			oBrowse:bLine := {|| {If(aArquivo[oBrowse:nAT,1],oColOK,oColNo),aArquivo[oBrowse:nAt,02],aArquivo[oBrowse:nAt,03],aArquivo[oBrowse:nAt,04],aArquivo[oBrowse:nAt,05],aArquivo[oBrowse:nAt,06],aArquivo[oBrowse:nAt,07],aArquivo[oBrowse:nAt,08],aArquivo[oBrowse:nAt,09],aArquivo[oBrowse:nAt,10]}}
		Else
			oBrowse:bLine := {|| {If(aArquivo[oBrowse:nAT,1],oColOK,oColNo),aArquivo[oBrowse:nAt,02],aArquivo[oBrowse:nAt,03],aArquivo[oBrowse:nAt,04],aArquivo[oBrowse:nAt,05],aArquivo[oBrowse:nAt,06],aArquivo[oBrowse:nAt,07],aArquivo[oBrowse:nAt,08],aArquivo[oBrowse:nAt,09]}}
		EndIf
		oBrowse:Refresh()
	Elseif nOpc == 3 .Or. nOpc == 4
		oBrowse:SetArray(aArquivo)
		oBrowse:bLine := {|| {If(aArquivo[oBrowse:nAT,1],oColOK,oColNo),aArquivo[oBrowse:nAt,02],aArquivo[oBrowse:nAt,03]}}
		oBrowse:Refresh()
	Endif

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} COMXCOLDUP
TOTVS COLABORAÇAO 2.0
Função para retirar documento duplicados ao reprocessar

@param		aArquivo, array, Documentos carregados

@author	Rodrigo M Pontes
@since		18/07/16
@version	12.7
/*/
//-------------------------------------------------------------------

Static Function COMXCOLDUP(aArquivo)

	Local aArea			:= GetArea()
	Local aRet			:= {}
	Local aAux			:= {}
	Local nI			:= 0
	Local aCodErroExc	:= {"COM005","COM006","COM019"}
	Local lCkoMsgErr 	:= CKO->(FieldPos("CKO_MSGERR")) > 0

	DbSelectArea("CKO")
	CKO->(DbSetOrder(1))

	//Verifica duplicidade
	For nI := 1 To Len(aArquivo)
		If !Empty(aArquivo[nI,3]) .And. !Empty(aArquivo[nI,4]) .And. !Empty(aArquivo[nI,5])
			nPos := aScan(aRet,{|x| AllTrim(x[3])+AllTrim(x[4])+AllTrim(x[5])+AllTrim(x[6])+AllTrim(x[7]) == AllTrim(aArquivo[nI,3])+AllTrim(aArquivo[nI,4])+AllTrim(aArquivo[nI,5])+AllTrim(aArquivo[nI,6])+AllTrim(aArquivo[nI,7])})
			If nPos == 0
				aAdd(aRet,{aArquivo[nI,1],AllTrim(aArquivo[nI,2]),AllTrim(aArquivo[nI,3]),AllTrim(aArquivo[nI,4]),AllTrim(aArquivo[nI,5]),AllTrim(aArquivo[nI,6]),AllTrim(aArquivo[nI,7]),AllTrim(aArquivo[nI,8]),AllTrim(aArquivo[nI,9]),AllTrim(aArquivo[nI,10]),AllTrim(aArquivo[nI,11])})
			Else
				COLATUFLAG(aRet[nPos,2],"3")

				aRet[nPos,2] := aArquivo[nI,2]
				aRet[nPos,3] := aArquivo[nI,3]
				aRet[nPos,4] := aArquivo[nI,4]
				aRet[nPos,5] := aArquivo[nI,5]
				aRet[nPos,6] := aArquivo[nI,6]
				aRet[nPos,7] := aArquivo[nI,7]
				aRet[nPos,8] := aArquivo[nI,8]
				aRet[nPos,9] := aArquivo[nI,9]
				aRet[nPos,10]:= aArquivo[nI,10]

				If lCkoMsgErr
					aRet[nPos,11]:= aArquivo[nI,11]
				Endif
			Endif
		Else
			aAdd(aRet,{aArquivo[nI,1],AllTrim(aArquivo[nI,2]),AllTrim(aArquivo[nI,3]),AllTrim(aArquivo[nI,4]),AllTrim(aArquivo[nI,5]),AllTrim(aArquivo[nI,6]),AllTrim(aArquivo[nI,7]),AllTrim(aArquivo[nI,8]),AllTrim(aArquivo[nI,9]),AllTrim(aArquivo[nI,10]),AllTrim(aArquivo[nI,11])})
		Endif
	Next nI

	//Retira os arquivos com os codigo de erro:
	For nI := 1 To Len(aRet)
		If aScan(aCodErroExc,AllTrim(aRet[nI,8])) == 0
			aAdd(aAux,{aRet[nI,1],AllTrim(aRet[nI,2]),AllTrim(aRet[nI,3]),AllTrim(aRet[nI,4]),AllTrim(aRet[nI,5]),AllTrim(aRet[nI,6]),AllTrim(aRet[nI,7]),AllTrim(aRet[nI,8]),AllTrim(aRet[nI,9]),AllTrim(aRet[nI,10]),AllTrim(aRet[nI,11])})
		Else
			COLATUFLAG(aRet[nI,2],"3")
		Endif
	Next nI

	//Atualiza aRet
	aRet := aClone(aAux)

	RestArea(aArea)

Return aRet

//-------------------------------------------------------------------
/*/{Protheus.doc} ColChanFil
TOTVS COLABORAÇAO 2.0
Função para selecionar a filial de processamento do documento.

@param		aArquivo, array, Documentos carregados. Obrigatório
@param		oBrowse, object, Objeto do browse.      Obrigatório

@author	Geovani.Figueira
@since		05/12/2017
@version	12.1.17
/*/
//-------------------------------------------------------------------
Function ColChanFil(aArquivo,oBrowFile)

	Local aFilDest	:= {}
	Local aHeadCols	:= {" ",STR0174,STR0176,STR0175,STR0181} // Filial / Nome / CNPJ / Inscrição Est.
	Local aSize		:= MsAdvSize()
	Local aSM0      := FwLoadSM0()
	Local oDlg		:= NIL
	Local oBrowse	:= NIL
	Local lProc		:= .F.
	Local lRet      := .F.
	Local nX		:= 0

	Define MsDialog oDlg Title STR0108 From aSize[1],aSize[2] To aSize[1]+250,aSize[2]+650 Pixel //-- Selecao de filial destinataria

	oBrowse := TCBrowse():New(01,01,326,105,,aHeadCols,,oDlg,,,,,{|| MarcaFilial(@aFilDest,oBrowse:nAt,@oBrowse),oBrowse:Refresh()},,,,,,,.F.,,.T.,,.F.,,.T.,.T.)

	For nX := 1 To Len(aSM0)
		If AllTrim(aSm0[nX,SM0_GRPEMP]) == AllTrim(SM0->M0_CODIGO) .And. (allTrim(aSM0[nX,SM0_CGC]) == aArquivo[oBrowFile:nAt,10] .Or. Empty(aArquivo[oBrowFile:nAt,10]) )
			aAdd(aFilDest,{})
			aAdd(aTail(aFilDest),(aArquivo[oBrowFile:nAt,7] == aSM0[nX,SM0_CODFIL])) //-- Flag de marcacao
			aAdd(aTail(aFilDest),aSM0[nX,SM0_CODFIL])                               //-- Codigo filial
			aAdd(aTail(aFilDest),aSM0[nX,SM0_NOMRED])                              //-- Nome filial
			aAdd(aTail(aFilDest),aSM0[nX,SM0_CGC])                                //-- CNPJ filial
			aAdd(aTail(aFilDest),IIF(Len(aSM0[nX])>21,StrTran(SUBSTR(aSM0[nX,22],At('_',aSM0[nX,22])+1),'_'),"")) //-- Incrição Estadual
		EndIf
	Next nX

	If Len(aFilDest) == 0
		AVISO(STR0004,STR0177+chr(13)+chr(10)+STR0178,{STR0077},3) //"Os CNPJs dos arquivos selecionados não pertencem ao grupo de empresas logado."#"Efetue logon no grupo de empresas correto para solucionar os conflitos."
	Else
		oBrowse:SetArray(aFilDest)
		oBrowse:bLine := {|| {If(aFilDest[oBrowse:nAT,01],oColOK,oColNo),aFilDest[oBrowse:nAt,02],aFilDest[oBrowse:nAt,03],;
			aFilDest[oBrowse:nAt,04],aFilDest[oBrowse:nAt,05]}}
		oBrowse:Refresh()

		If !Empty(aFilDest[1][2])
			Define SButton From aSize[1]+110,aSize[2]+235 Type 1 Action (lProc := .T., oDlg:End()) Enable Of oDlg
		EndIf
		Define SButton From aSize[1]+110,aSize[2]+265 Type 2 Action oDlg:End() Enable Of oDlg

		Activate MsDialog oDlg Centered

		If lProc
			For nX := 1 To Len(aFilDest)
				If aFilDest[nX][1]
					aArquivo[oBrowFile:nAt,6] := SM0->M0_CODIGO
					aArquivo[oBrowFile:nAt,7] := aFilDest[nX][2]
					lRet := .T.
					ColGrvFil(aArquivo[oBrowFile:nAt,2],"0",aArquivo[oBrowFile:nAt,6],aArquivo[oBrowFile:nAt,7],aArquivo[oBrowFile:nAt,10], .T.)
					Exit
				EndIf
			Next nX
			oBrowFile:Refresh()
		Endif
	EndIf

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} ColGrvFil
TOTVS COLABORAÇAO 2.0
Função que grava a filial de processamento no documento informado

@param		cNomeArq, string, Nome do arquivo<br><b>Obrigatório
@param		cFlag, string, Flag do arquivo.<br><b>Obrigatório
@param		cFilProc, string, Filial de processamento do arquivo.<br><b>Obrigatório

@author	Flavio Lopes Rasta
@since		10/10/2014
@version	11.8
/*/
//-------------------------------------------------------------------
Function ColGrvFil(cNomeArq,cFlag,cEmpProc,cFilProc,cCnpjImp, lLimpErr)

	Local oColab

	Default lLimpErr := .F.

	If !Empty(cNomeArq)
		oColab 			:= ColaboracaoDocumentos():New()
		oColab:cModelo 	:= ""
		oColab:cTipoMov := '2'
		oColab:cFlag 	:= cFlag
		oColab:cQueue 	:= SubStr(cNomeArq,1,3)
		oColab:cNomeArq := cNomeArq

		If oColab:Consultar()
			oColab:cEmpProc := cEmpProc
			oColab:cFilProc := cFilProc
			oColab:cCnpjImp := cCnpjImp
			oColab:gravaFilialDeProcessamento()

			if lLimpErr  //Limpa o campo CKO_CODERR - utilizado em reprocessar qdo 2 filiais tem o mesmo CNPJ.
				oColab:cFlag := '0'
				oColab:cCodErrErp := ""
				oColab:gravaErroErp()
			endif
		Endif
	Endif

	oColab := NIL

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} COMCOLEXC
Exclui os documentos marcados.

@author	Andre Anjos
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function COMCOLEXC()

	Local lRet 		:= .F.
	Local nPos		:= 0
	Local cSDSTMP	:= GetNextAlias()

	lRet := MsgYesNo(STR0042,STR0004) //-- Confirma a exclusão dos documentos marcados? # Atenção

	If lRet
		//Traz documentos marcados
		BeginSQL Alias cSDSTMP
			SELECT
				SDS.DS_FILIAL,
				SDS.DS_DOC,
				SDS.DS_SERIE,
				SDS.DS_FORNEC,
				SDS.DS_LOJA,
				SDS.DS_ARQUIVO
			FROM
				%Table:SDS% SDS
			WHERE
				SDS.DS_OK = %Exp:cMarca%
				AND SDS.DS_STATUS != 'P'
				AND SDS.%NotDel%
		EndSQL

		SDT->(dbSetOrder(3))
		SDS->(dbSetorder(1))

		While !(cSDSTMP)->(EOF())
			//-- Deleta itens do documento
			If SDT->(dbSeek((cSDSTMP)->(DS_FILIAL+DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)))
				While !SDT->(EOF()) .And. SDT->(DT_FILIAL+DT_FORNEC+DT_LOJA+DT_DOC+DT_SERIE) == (cSDSTMP)->(DS_FILIAL+DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE)
					RecLock("SDT",.F.)
					SDT->(dbDelete())
					SDT->(MsUnLock())
					SDT->(dbSkip())
				End
			EndIf

			COLREPATU(SubStr((cSDSTMP)->DS_ARQUIVO,1,3),"1",(cSDSTMP)->DS_ARQUIVO,"1")

			//-- Deleta cabecalho do documento
			If SDS->(dbSeek((cSDSTMP)->(DS_FILIAL+DS_DOC+DS_SERIE+DS_FORNEC+DS_LOJA)))
				nPos := aScan(aRegMark,SDS->(RECNO()))
				If nPos > 0
					aDel(aRegMark,nPos)
					aSize(aRegMark,Len(aRegMark)-1)
				Endif

				RecLock("SDS",.F.)
				SDS->(dbDelete())
				SDS->(MsUnLock())
			EndIf

			(cSDSTMP)->(dbSkip())
		End

		(cSDSTMP)->(dbCloseArea())
		SDS->(dbGoTop())
	EndIf

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} COMCOLLEG
Exibe uma janela contendo a legenda da browse.

@author	Andre Anjos
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function COMCOLLEG()

	Local aCores	:= {}
	Local aCoresNew	:= {}
	Local lCOMXLEG	:= ExistBlock("COMXLEG")

	aAdd(aCores,{'BR_VERMELHO',STR0043})	//-- "Documento Gerado"
	aAdd(aCores,{'BR_VERDE',STR0044})		//-- "Documento Normal"
	aAdd(aCores,{'BR_AZUL',STR0045})		//-- "Docto. de Bonificação"
	aAdd(aCores,{'BR_AMARELO',STR0046})		//-- "Docto. de Devolução"
	aAdd(aCores,{'BR_CINZA',STR0047})		//-- "Docto. de Beneficiamento"
	aAdd(aCores,{'BR_PINK',STR0048})	 	//-- "Docto. de Compl. Preço/Qtde"
	aAdd(aCores,{'BR_LARANJA',STR0049})		//-- "Docto. de Transporte"
	aAdd(aCores,{'BR_PRETO',STR0050})		//-- "Documento c/ Ocorrência"

	//Ponto de Entrada para incluir/alterar opcoes de legenda
	If lCOMXLEG
		aCoresNew := ExecBlock("COMXLEG",.F.,.F.,{aCores})
		If ValType(aCoresNew) == "A"
			aCores := aCoresNew
		EndIf
	EndIf

	BrwLegenda(STR0001,STR0051,aCores) //-- Legenda

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} Documentos
Funcao procura possiveis pedidos de compra relacionados a NF

@param	cProduto	codigo do produto posicionado.
@param	lPedDoc		indica se a pequisa e por documento ou item.

@author	Rodrigo de Toledo
@since 30/10/09
/*/
//-------------------------------------------------------------------

Static Function Documentos(cProduto,lPedDoc,nMultPC,aColsAnt,cForn,cLoja,aPedidos,oBrowse)

	Local aArea      := GetArea()
	Local aCampos    := {}
	Local aColsPcDoc := {}
	Local aProdutos  := {}
	Local cAliasTmp  := "SC7TMP"
	Local cQuery     := ""
	Local cFilSC7    := xFilEnt(xFilial("SC7"),"SC7")
	Local cRestNFE	 := SuperGetMV("MV_RESTNFE")
	Local nRecSDT    := 0
	Local nX         := 0
	Local nY         := 0
	Local nPNFORI	 := GDFieldPos("DT_NFORI")
	Local nPSERIORI	 := GDFieldPos("DT_SERIORI")
	Local nPCOD		 := GDFieldPos("DT_COD")
	Local nPITEMORI	 := GDFieldPos("DT_ITEMORI")
	Local nPTES		 := GDFieldPos("DT_TES")
	Local nTNFORI	 := TamSx3("DT_NFORI")[1]
	Local nTSERIORI	 := TamSx3("DT_SERIORI")[1]
	Local nTITEMORI	 := TamSx3("DT_ITEMORI")[1]
	Local nPosProd   := aScan(aHeader,{|x| AllTrim(x[2]) == "DT_COD"})
	Local lRet       := .F.
	Local lRetXPC    := .T.
	Local lA140IPed  := ExistBlock("A140IPED")
	Local lRemet     := .F.
	Local lConsLoja  := Nil 	// Considera loja na pesquisa de pedidos
	Local lRetPed    := (aPedidos == Nil)
	Local lForPCNF   := (SuperGetMV("MV_FORPCNF",,.F.) == .T.)
	Local lContinua  := .T.

	Default nMultPC  := 0
	Default cForn    := SDS->DS_FORNEC
	Default cLoja    := SDS->DS_LOJA

	If SDS->DS_TIPO == "C"
		Private n := oGetDados:nAt
	EndIf

	//Posicionar no pergunte correto para validação se consulta loja.
	Pergunte("MTA140I",.F.)
	lConsLoja := (mv_par12 == 1)

	// Verifica se e CT-e e se e remetente da mercadoria (saida), neste caso deve permitir vinculo com pedido
	If SDS->DS_TIPO == "T" .And. SDS->DS_TPFRETE == "C"
		lRemet := .T.
	EndIf

	// Verifica se utiliza funcionalidade de vinculo de multiplos pedidos
	lRetXPC := ValidXPC(lRemet,nMultPC,aColsAnt)

	If ( SDS->DS_TIPO $ "N" .Or. lRemet ) .And. lRetXPC	//-- NF Normal (Compra) ou CT-e de saida

		If lPedDoc
			If nMultPC == 0
				aColsPcDoc := aClone(aCols)
			Else
				aColsPcDoc := aClone(aColsAnt)
			Endif

			For nY := 1 To Len(aColsPcDoc)
				If aScan(aProdutos,{|x| x == aColsPcDoc[nY][nPosProd]} ) == 0
					aAdd(aProdutos,aColsPcDoc[nY][nPosProd])
				EndIf
			Next nY
		Endif

		cQuery += "SELECT " +If(lPedDoc,"DISTINCT C7_LOJA, ","") +"C7_NUM, C7_EMISSAO, C7_FILIAL"

		If !lPedDoc
			cQuery += ", C7_ITEM, C7_QUANT, C7_PRECO, C7_TOTAL, C7_QTDACLA, C7_LOJA, C7_PRODUTO, C7_QUJE"
		EndIf

		//Ponto de entrada utilizado para adicionar campos na interface de visualização de pedidos
		If lA140IPed
			aCampos := ExecBlock("A140IPED",.F.,.F.,{1,{},{}})
			If ValType(aCampos[1]) == "A"
				For nX:=1 to Len(aCampos[1])
					cQuery += " , " + aCampos[1][nX]
				Next nX
			EndIf
		EndIf

		cQuery += " FROM " +RetSqlName("SC7") +" SC7"
		cQuery += " WHERE C7_FILENT = '" + cFilSC7 + "' AND D_E_L_E_T_ = ' '"
		cQuery += " AND C7_FORNECE = '" +cForn + "'"

		If lConsLoja
			cQuery += " AND C7_LOJA = '" +cLoja + "'"
		EndIf

		If !lPedDoc
			cQuery += " AND C7_PRODUTO = '" +cProduto +"'"
		Else
			If Len(aProdutos) > 0
				cQuery += " AND C7_PRODUTO IN ("
				For nY := 1 To Len(aProdutos)
					cQuery += "'" + aProdutos[nY] + "'"
					If nY <> Len(aProdutos)
						cQuery += ","
					EndIf
				Next nY
				cQuery += ")"
			Endif
		Endif

		cQuery += " AND (C7_QUANT - C7_QUJE - C7_QTDACLA) > 0"
		cQuery += " AND C7_ENCER = ' ' AND C7_RESIDUO <> 'S'"

		If cRestNFE == "S"
			cQuery += " AND C7_CONAPRO <> 'B'"
		EndIf

		cQuery += " ORDER BY C7_NUM"

		If !lPedDoc
			cQuery += " , C7_ITEM"
		EndIf

		cQuery := ChangeQuery(cQuery)

		If !lRetPed .And. Select(cAliasTmp) > 0
			(cAliasTmp)->(dbCloseArea())
		EndIf

		dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQuery),cAliasTmp,.T.,.T.)

		(cAliasTmp)->(dbGoTop())
		If (cAliasTmp)->(!EOF()) .Or. lForPCNF
			lRet := Pedidos(cProduto,lPedDoc,cAliasTmp,lConsLoja,nMultPC,aColsAnt,cForn,cLoja,@aPedidos,@oBrowse)
		Else
			Aviso(STR0004,(STR0058 +AllTrim(cProduto) +STR0059 +AllTrim(SDS->DS_DOC)+"/"+SerieNfId("SDS",2,"DS_SERIE") +"."),{"OK"}) //-- Atenção # Não há pedidos de compra para o produto # do documento #.
		EndIf

		If Select(cAliasTmp) > 0
			(cAliasTmp)->(dbCloseArea())
		EndIf
	Else
		n := oGetDados:nAt
		aCols := oGetDados:aCols

		If nMultPC <> 3
			If SDS->DS_TIPO $ "D"
				lRet := F4NFORI(,,"M->DT_NFORI",SDS->DS_FORNEC,SDS->DS_LOJA,cProduto,"A140I",,@nRecSDT) .And. nRecSDT <> 0
			ElseIf SDS->DS_TIPO == "C"
				lRet := F4COMPL(,,,SDS->DS_FORNEC,SDS->DS_LOJA,cProduto,"A140I",@nRecSDT,"M->DT_NFORI") .And. nRecSDT <> 0
			EndIf

			If lRet
				// Tratamento para carregar a TES de devolucao automaticamente
				If lContinua
					SD2->(DbSetOrder(3))	// D2_FILIAL + D2_DOC + D2_SERIE + D2_D2_CLIENTE + D2_LOJA + D2_COD + D2_ITEM
					If SD2->(MsSeek(xFilial("SD2")+oGetDados:aCols[oGetDados:nAt,nPNFORI]+oGetDados:aCols[oGetDados:nAt,nPSERIORI]+SDS->DS_FORNEC+SDS->DS_LOJA+oGetDados:aCols[oGetDados:nAt,nPCOD]+oGetDados:aCols[oGetDados:nAt,nPITEMORI]))
						DbSelectArea("SF4")
						SF4->(DbSetOrder(1))

						cTesDev := GetAdvFVal("SF4","F4_TESDV",xFilial("SF4")+SD2->D2_TES,1)

						If !Empty(cTesDev)
							If SF4->(DbSeek(xFilial("SF4")+cTesDev))
								aCols[oGetDados:nAt][nPTES] := cTesDev
								oGetDados:aCols[oGetDados:nAt,nPTES] := cTesDev

								// Atualiza impostos
								lContinua := ColAtuImp(oGetDados:aCols[oGetDados:nAt,nPTES],oGetDados:nAt)
							EndIf
						EndIf
					EndIf
				Endif

				oGetDados:aCols := aClone(aCols)
				oGetDados:Refresh()
			Endif
		Else //Desvincular NF Origem
			If Empty(oGetDados:aCols[oGetDados:nAt,nPNFORI])
				Aviso(STR0137,STR0183, {"Ok"}, 2) //"Não há nota de origem para realizar o desvinculo."
				lRet := .F.
			Else
				oGetDados:aCols[oGetDados:nAt,nPNFORI]	:= Space(nTNFORI)
				oGetDados:aCols[oGetDados:nAt,nPSERIORI]:= Space(nTSERIORI)
				oGetDados:aCols[oGetDados:nAt,nPITEMORI]:= Space(nTITEMORI)

				aCols		:= aClone(oGetDados:aCols)
				oGetDados:Refresh()
			Endif
		Endif
	EndIf

	RestArea(aArea)
Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} Pedidos
Funcao responsavel por criar o browse de selecao para que o usuario
escolha os pedidos de compra referentes aos itens na NF

@param	cProduto	codigo do produto posicionado.
@param	lPedDoc		indica se a selecao e por documento.
@param	cAliasTmp	alias com o resultado da query dos documentos

@author	Rodrigo de Toledo
@since 30/10/09
/*/
//-------------------------------------------------------------------

Static Function Pedidos(cProduto,lPedDoc,cAliasTmp,lConsLoja,nMultPC,aColsAnt,cForn,cLoja,aPedidos,oBrowse)

	Local lRet 		 := .F.
	Local oDlg		 := NIL
	Local oComboBox  := Nil
	Local aArea		 := GetArea()
	Local aCampos    := {}
	Local oSize
	Local nX		 := 0
	Local nY		 := 0
	Local nP       	 := 0
	Local lContinua	 := .T.
	Local lA140IPed  := ExistBlock("A140IPED")
	Local aRetPE     := {}
	Local nZ         := 0
	Local cCampoUsr  := ""
	Local cComboFor	 := ''
	Local cItem		 := StrZero(1,Len(SDT->DT_ITEM))
	Local cLine		 := ''
	Local aCampoUsr  := {}
	Local nPosCpo    := 0
	Local nSldPed    := 0
	Local nCont		 := 1
	Local nTamCpos	 := 0
	Local nMarcado	 := 0
	Local nTotPed	 := 0
	Local nSaldo   	 := 0
	Local n			 := oGetDados:nAt
	Local nPedSel	 := 0
	Local nPosCodPc	 := 0
	Local cFilBak	 := cFilAnt
	Local cSavCadast := cCadastro
	Local lForPCNF	 := (SuperGetMV("MV_FORPCNF",,.F.) == .T.)
	Local lRetPed	 := (aPedidos == Nil)
	Local nBkpN	     := 0
	Local cProdAten  := ''
	Local nPPrd		 := 0
	Local aPrds		 := {}
	Local lPrdIgual  := .F.
	Local nPedIgual	 := 0
	Local cPedIgual	 := 0
	Local cPrdIgual  := ""
	Local aProdBkp	 := {}
	Local aPedItBkp	 := {}
	Local nQtdNF	 := 0
	Local lPedOri	 := .T.
	Local lOriTemPed := .F.
	Local nPPEDIDO	:= GDFieldPos("DT_PEDIDO")
	Local nPITEMPC	:= GDFieldPos("DT_ITEMPC")
	Local nPCOD		:= GdFieldPos("DT_COD")
	Local nPQUANT	:= GDFieldPos("DT_QUANT")
	Local nPVUNIT	:= GDFieldPos("DT_VUNIT")
	Local nPITEM	:= GDFieldPos("DT_ITEM")
	Local nPTOTAL	:= GdFieldPos("DT_TOTAL")
	Local nPTES		:= GDFieldPos("DT_TES")
	Local nPDESC	:= GDFieldPos("DT_DESC")
	Local nTPEDIDO	:= TamSx3("DT_PEDIDO")[1]
	Local nTITEMPC	:= TamSx3("DT_ITEMPC")[1]
	Local nTITEM	:= TamSx3("DT_ITEM")[1]
	Local nTB1COD	:= TamSx3("B1_COD")[1]
	Local cCodLoj	:= ""
	Local cCbmLoj	:= ""
	Local cCbmFor	:= ""
	Local nTCOD		:= TamSx3("A2_COD")[1]
	Local nTLOJA	:= TamSx3("A2_LOJA")[1]
	Local aDadosOri	:= {}
	Local nPosOri	:= 0

	Default nMultPC	:= 0
	Default cForn	:= SDS->DS_FORNEC
	Default cLoja	:= SDS->DS_LOJA
	Default aPedidos:= {}

	// Foi necessario criar essas variaveis para que fosse possivel usar a funcao padrao do sistema A120Pedido()
	Private INCLUI  := .F.
	Private ALTERA  := .F.
	Private nTipoPed:= 1
	Private l120Auto:= .F.

	n := oGetDados:nAt

	If !lPedDoc
		aCampos := {"",RetTitle("C7_LOJA"),RetTitle("C7_NUM"),RetTitle("C7_ITEM"),RetTitle("C7_PRODUTO"),RetTitle("C7_EMISSAO"),STR0060,RetTitle("C7_PRECO")} //-- Saldo
		bLine := {|| {	If(aPedidos[oBrowse:nAt,1],oColOK,oColNo),;								//-- Marca
			aPedidos[oBrowse:nAt,2],;											//-- Loja
			aPedidos[oBrowse:nAt,3],;											//-- Pedido
			aPedidos[oBrowse:nAt,4],;											//-- Item
			aPedidos[oBrowse:nAt,5],;											//-- Produto
			aPedidos[oBrowse:nAt,6],;											//-- Emissao
			Transform(aPedidos[oBrowse:nAt,7],PesqPict("SC7","C7_QUANT")),;//-- Saldo
			Transform(aPedidos[oBrowse:nAt,8],PesqPict("SC7","C7_PRECO"))}} //-- Preço

		//Ponto de entrada utilizado para adicionar campos na interface de visualização de pedidos
		If lA140IPed
			nTamCpos := Len(aCampos)
			aRetPE := ExecBlock("A140IPED",.F.,.F.,{2,aCampos,aCampos})
			If ValType(aRetPE[1]) == "A"
				For nZ:=1 to Len(aRetPe[1])
					Aadd(aCampoUsr,aRetPE[3][1][nZ+nTamCpos])
				Next nZ
			EndIf
		EndIf

		&(cAliasTmp+"->(dbGoTop())")
		While &(cAliasTmp+"->(!EOF())")
			aAdd(aPedidos, {.F.,;															//-- Marca
				&(cAliasTmp+"->C7_LOJA"),;										//-- Loja
				&(cAliasTmp+"->C7_NUM"),;										//-- Pedido
				&(cAliasTmp+"->C7_ITEM"),;										//-- Item
				&(cAliasTmp+"->C7_PRODUTO"),;									//-- Produto
				StoD(&(cAliasTmp+"->C7_EMISSAO")),;								//-- Emissao
				&(cAliasTmp+"->C7_QUANT") - &(cAliasTmp+"->C7_QTDACLA") - &(cAliasTmp+"->C7_QUJE"),;		//-- Saldo
				&(cAliasTmp+"->C7_PRECO")})

			If lA140IPed
				If ValType(aRetPE[1]) == "A"
					For nZ:=1 to Len(aRetPe[1])
						cCampoUsr := "CAMPO"+AllTrim(Str(nZ))
						nPosCpo := AScan( aCampoUsr, {|x| AllTrim(x[1]) == cCampoUsr } )
						If nPosCpo > 0
							If nCont==1
								Aadd(aCampos,aCampoUsr[nPosCpo][3])
							EndIf
							If aRetPE[2][1][nZ+nTamCpos][2]=="D"										// Se campo tipo Data
								Aadd(aPedidos[Len(aPedidos)],(StoD(&(cAliasTmp+"->"+aRetPE[1][nZ]))))	// Converte para data
							Else
								Aadd(aPedidos[Len(aPedidos)],((&(cAliasTmp+"->"+aRetPE[1][nZ]))))		// Caso contrário não converte
							EndIf
						Else
							Aadd(aPedidos[Len(aPedidos)],((&(cAliasTmp+"->"+aRetPE[1][nZ]))))
						EndIf
					Next nZ
				EndIf
				nCont++
			EndIf

			Aadd(aPedidos[Len(aPedidos)],.F.)

			//-- Se o pedido ja esta no aCols, marca como usado
			If !Empty(oGetDados:aCols[oGetDados:nAt,nPPEDIDO]) .And.;
					oGetDados:aCols[oGetDados:nAt,nPPEDIDO] == &(cAliasTmp+"->C7_NUM") .And.;
					oGetDados:aCols[oGetDados:nAt,nPITEMPC] == &(cAliasTmp+"->C7_ITEM")
				aTail(aPedidos)[1] := .T.
				aTail(aPedidos)[Len(aPedidos[1])] := .T.
			EndIf

			&(cAliasTmp)->(dbSkip())
		EndDo

		If lA140IPed
			If ValType(aRetPE[1]) == "A"
				cLine := '{|| { If(aPedidos[oBrowse:nAt,1],oColOK,oColNo),'								//-- Marca
				cLine += '		   aPedidos[oBrowse:nAt,2],'										//-- Loja
				cLine += '   	   aPedidos[oBrowse:nAt,3],'										//-- Pedido
				cLine += '	 	   aPedidos[oBrowse:nAt,4],'										//-- Item
				cLine += '	 	   aPedidos[oBrowse:nAt,5],'										//-- Produto
				cLine += '	 	   aPedidos[oBrowse:nAt,6],'										//-- Emissao
				cLine += '	 	   Transform(aPedidos[oBrowse:nAt,7],PesqPict("SC7","C7_QUANT")),'//-- Saldo
				cLine += '	 	   Transform(aPedidos[oBrowse:nAt,8],PesqPict("SC7","C7_PRECO"))'

				For nZ := 1 To Len(aRetPE[1])
					cLine += ' , aPedidos[oBrowse:nAt,' + AllTrim(Str(nZ+nTamCpos)) + ']'
				Next nZ

				cLine += ' }}'

				bLine := &cLine
			EndIf
		EndIf

	Else
		aCampos := {"",RetTitle("C7_LOJA"),RetTitle("C7_NUM"),RetTitle("C7_EMISSAO")}
		bLine := {|| {	If(aPedidos[oBrowse:nAt,1],oColOK,oColNo),;	//-- Marca
			aPedidos[oBrowse:nAt,2],;				//-- Loja
			aPedidos[oBrowse:nAt,3],;				//-- Pedido
			aPedidos[oBrowse:nAt,4]	}	}			//-- Emissao

		If nMultPc < 3
			&(cAliasTmp+"->(dbGoTop())")
			While &(cAliasTmp+"->(!EOF())")
				aAdd(aPedidos, {.F.,;															//-- Marca
					&(cAliasTmp+"->C7_LOJA"),;										//-- Loja
					&(cAliasTmp+"->C7_NUM"),;										//-- Pedido
					StoD(&(cAliasTmp+"->C7_EMISSAO")),;							//-- Emissao
					.F.	})

				//-- Se o pedido ja esta no aCols, marca como usado
				If !Empty(oGetDados:aCols[n,nPPEDIDO]) .And.;
						oGetDados:aCols[n,nPPEDIDO] == &(cAliasTmp+"->C7_NUM")
					aTail(aPedidos)[1] := .T.
					aTail(aPedidos)[Len(aPedidos[1])] := .T.
				EndIf

				//-- Vínculo por múltiplos pedidos
				If nMultPC > 0
					For nX := 1 To Len(oGetDados:aCols)
						If !Empty(oGetDados:aCols[nX,nPPEDIDO]) .And.;
								oGetDados:aCols[nX,nPPEDIDO] == &(cAliasTmp+"->C7_NUM")
							aTail(aPedidos)[1] := .T.
							aTail(aPedidos)[Len(aPedidos[1])] := .T.
						EndIf
					Next nX
				EndIf
				&(cAliasTmp)->(dbSkip())
			EndDo
		Else
			aCampos := {"",RetTitle("C7_NUM"),AllTrim(RetTitle("C7_ITEM"))+ " PC",AllTrim(RetTitle("DT_ITEM"))+" NF"}
			bLine := {|| {	If(aPedidos[oBrowse:nAt,1],oColOK,oColNo),;	//-- Marca
				aPedidos[oBrowse:nAt,2],;				//-- PC
				aPedidos[oBrowse:nAt,3],;				//-- Item PC
				aPedidos[oBrowse:nAt,4]}}				//-- Item NF

			For nX := 1 To Len(oGetDados:aCols)
				If !Empty(oGetDados:aCols[nX,nPPEDIDO]) .And. !Empty(oGetDados:aCols[nX,nPITEMPC])
					aAdd(aPedidos, {.F.,;															//-- Marca
						oGetDados:aCols[nX,nPPEDIDO],;				//-- PC
						oGetDados:aCols[nX,nPITEMPC],;
						StrZero(nX,nTITEM),;
						.F.})				//-- Item PC
				EndIf
			Next nX

			If Len(aPedidos) == 0
				lRetPed := .F.
				lRet := .T.
			Endif
		Endif
	EndIf

	If lRetPed
		//-- Monta interface para selecao do pedido

		Define MsDialog oDlg Title Iif(nMultPC<>3,STR0061,"Desvincular") From 000,000 To 330,480 Pixel //-- Vínculo com Pedido de Compra

		//Calcula dimensões
		oSize := FwDefSize():New(.F.,,,oDlg)
		oSize:AddObject( "CABECALHO",  100, 15, .T., .T. ) // Totalmente dimensionavel
		oSize:AddObject( "GETDADOS" ,  100, 75, .T., .T. ) // Totalmente dimensionavel
		oSize:AddObject( "RODAPE"   ,  100, 10, .T., .T. ) // Totalmente dimensionavel

		oSize:lProp 	:= .T. // Proporcional
		oSize:aMargins 	:= { 3, 3, 3, 3 } // Espaco ao lado dos objetos 0, entre eles 3
		oSize:Process() 	   // Dispara os calculos

		//-- Cabecalho
		If !lPedDoc
			@oSize:GetDimension("CABECALHO","LININI"),oSize:GetDimension("CABECALHO","COLINI") Say STR0062 +SDS->DS_DOC +" - " +STR0063 +AllTrim(oGetDados:aCols[oGetDados:nAt,GDFieldPos("DT_ITEM")]) +" / " +AllTrim(cProduto) + " - " + Posicione("SB1",1,xFilial("SB1")+cProduto,"B1_DESC") Pixel Of oDlg //-- Doc: # Item:
		Else
			@oSize:GetDimension("CABECALHO","LININI"),oSize:GetDimension("CABECALHO","COLINI") Say STR0062 +SDS->DS_DOC +" - " +STR0064 +SDS->DS_FORNEC +"/" +SDS->DS_LOJA +" - " +Posicione("SA2",1,xFilial("SA2")+SDS->(DS_FORNEC+DS_LOJA),"A2_NOME") Pixel Of oDlg //-- Doc: # Fornecedor
		EndIf

		//-- Itens
		If lForPCNF
			@ oSize:GetDimension("CABECALHO","LININI")+12,oSize:GetDimension("CABECALHO","COLINI") SAY OemToAnsi('Fornecedor:') Of oDlg PIXEL SIZE 120 ,9 //"Fornecedor:"
			@ oSize:GetDimension("CABECALHO","LININI")+12,oSize:GetDimension("CABECALHO","COLINI")+34 MSCOMBOBOX oComboBox VAR cComboFor ITEMS MTGetForRl(SDS->DS_FORNEC,SDS->DS_LOJA) SIZE 160,10 OF oDlg PIXEL ON CHANGE LoadItens(cProduto,lPedDoc,nMultPC,aColsAnt,cComboFor,@oBrowse,aCampos,@aPedidos)

			oBrowse := TCBrowse():New( oSize:GetDimension("GETDADOS","LININI"),oSize:GetDimension("GETDADOS","COLINI"),;
				oSize:GetDimension("GETDADOS","XSIZE"),oSize:GetDimension("GETDADOS","YSIZE"),;
				,aCampos,,oDlg,,,,,{|| MarcaPC(@aPedidos,oBrowse:nAt,lPedDoc,nMultPC,oBrowse),oBrowse:Refresh()},,,,,,,,,.T.)
			oBrowse:SetArray(aPedidos)
			If !Empty(aPedidos)
				oBrowse:bLine := bLine
			Else
				cLine			:= Replicate("'',",Len(aCampos)-1)
				oBrowse:bLine := &( "{ ||{ If(Empty(aPedidos),oColNo,oColOK)," +Substr(cLine,1,Rat(',',cLine)-1 ) +"} }"  )
			EndIf

			//-- Botoes
			TButton():New(oSize:GetDimension("RODAPE","LININI"),oSize:GetDimension("RODAPE","COLINI"),;
				STR0065,oDlg,{|| MsgRun(STR0066 +AllTrim(aPedidos[oBrowse:nAt,3]) +"...",STR0003, {|| GetC7Recno(aPedidos[oBrowse:nAt,Iif(nMultPc==3,2,3)]), cFilAnt := cFilBak, cCadastro := cSavCadast } )},055,012,,,,.T.) //-- Visualizar pedido # Carregando visualização do pedido

			Define SButton From oSize:GetDimension("RODAPE","LININI"),oSize:GetDimension("RODAPE","COLINI")+150 Type 1 Action Eval({|| If(lRet := ValidPC(cProduto,lPedDoc,aPedidos,oBrowse:nAt,nMultPC,lConsLoja),oDlg:End(),)}) Enable Of oDlg
			Define SButton From oSize:GetDimension("RODAPE","LININI"),oSize:GetDimension("RODAPE","COLINI")+180 Type 2 Action oDlg:End() Enable Of oDlg

		Else
			//-- Itens
			oBrowse := TCBrowse():New(oSize:GetDimension("GETDADOS","LININI"),oSize:GetDimension("GETDADOS","COLINI"),;
				oSize:GetDimension("GETDADOS","XSIZE"),oSize:GetDimension("GETDADOS","YSIZE"),;
				,aCampos,,oDlg,,,,,{|| MarcaPC(@aPedidos,oBrowse:nAt,lPedDoc,nMultPC,oBrowse),oBrowse:Refresh()},,,,,,,,,.T.)
			oBrowse:SetArray(aPedidos)
			oBrowse:bLine := bLine
			oBrowse:bHeaderClick := {|| COLREPCLICK(8,aPedidos,,oBrowse)}

			//-- Botoes
			TButton():New(oSize:GetDimension("RODAPE","LININI"),oSize:GetDimension("RODAPE","COLINI"),;
				STR0065,oDlg,{|| MsgRun(STR0066 +AllTrim(aPedidos[oBrowse:nAt,3]) +"...",STR0003, {|| nBkpN := N, GetC7Recno(aPedidos[oBrowse:nAt,Iif(nMultPc==3,2,3)]), cFilAnt := cFilBak, cCadastro := cSavCadast } )},055,012,,,,.T.) //-- Visualizar pedido # Carregando visualização do pedido

			Define SButton From oSize:GetDimension("RODAPE","LININI"),oSize:GetDimension("RODAPE","COLINI")+180 Type 1 Action Eval({|| If(lRet := ValidPC(cProduto,lPedDoc,aPedidos,oBrowse:nAt,nMultPC,lConsLoja),oDlg:End(),), nPedSel := oBrowse:nAt }) Enable Of oDlg
			Define SButton From oSize:GetDimension("RODAPE","LININI"),oSize:GetDimension("RODAPE","COLINI")+210 Type 2 Action oDlg:End() Enable Of oDlg
		EndIf

		Activate Dialog oDlg Centered
	Else
		If nMultPc <> 3
			If !Empty(aPedidos)
				oBrowse:bLine := bLine
			Else
				cLine			:= Replicate("'',",Len(aCampos)-1)
				oBrowse:bLine := &( "{ ||{ If(Empty(aPedidos),oColNo,oColOK)," +Substr(cLine,1,Rat(',',cLine)-1 ) +"} }"  )
			EndIf
		Endif
	EndIf

	//se pedido foi visualizado, restaura variavel N (Controle de posiçao do aCols)
	If lRet .And. nBkpN > 0
		N 		:= nBkpN
		nBkpN 	:= 0
	EndIf

	If lForPCNF
		cCodLoj := SubStr(cComboFor, At(' | ',cComboFor)+3, Len(cComboFor))
		cCodLoj := SubStr(cCodLoj,1, At(' - ',cCodLoj)-1)
		cCbmFor := SubStr(cCodLoj, 1, At('/',cCodLoj)-1)
		cCbmLoj := SubStr(cCodLoj, At('/',cCodLoj)+1, Len(cCodLoj))
		cCbmFor := Padr(cCbmFor,nTCOD)
		cCbmLoj := Padr(cCbmLoj,nTLOJA)

		If cForn <> cCbmFor
			cForn := cCbmFor
			cLoja := cCbmLoj
		Elseif cForn == cCbmFor .And. cCbmLoj <> cLoja
			cLoja := cCbmLoj
		Endif
	Endif

	If lRet .And. nMultPC == 1 //Item
		aColsBkp	:= aClone(oGetDados:aCols)
		aCols		:= aClone(oGetDados:aCols)
		cItem		:= StrZero(Len(aColsBkp)+1,nTITEM)

		//Produto a ser vinculado
		cProdAten	:= oGetDados:aCols[oGetDados:nAt,nPCOD]

		//Quantidade do produto
		nProdQtd	:= oGetDados:aCols[oGetDados:nAt,nPQUANT]

		//aPedItBkp	- Busca os pedidos ja vinculados
		For nX := 1 To Len(aColsBkp)
			If !Empty(aColsBkp[nX][nPPEDIDO])
				If aScan(aPedItBkp,{|x| x[1] == aColsBkp[nX][nPPEDIDO] .And. x[2] == aColsBkp[nX][nPITEMPC]}) == 0
					aAdd(aPedItBkp,{aColsBkp[nX][nPPEDIDO],aColsBkp[nX][nPITEMPC]})
				Endif
			Endif
		Next nX

		//Verifica se esta vinculando algum pedido pela 1º vez
		//Verifica saldo do pedido, se pode ou não continuar sendo utilizado.
		For nX := 1 To Len(aPedidos)
			If aPedidos[nX][1] .And. !aPedidos[nX][Len(aPedidos[1])]
				nPosPc := aScan(oGetDados:aCols,{|x| x[nPPEDIDO] == aPedidos[nX][3] .And. x[nPITEMPC] == aPedidos[nX][4]})
				If nPosPC > 0
					nQuant	:= Posicione("SC7",14,xFilEnt(xFilial("SC7"),"SC7") + aPedidos[nX][3] + aPedidos[nX][4],"C7_QUANT")
					nQuje	:= Posicione("SC7",14,xFilEnt(xFilial("SC7"),"SC7") + aPedidos[nX][3] + aPedidos[nX][4],"C7_QUJE")
					nQtdCla	:= Posicione("SC7",14,xFilEnt(xFilial("SC7"),"SC7") + aPedidos[nX][3] + aPedidos[nX][4],"C7_QTDACLA")

					//Calcular saldo do pedido
					For nY := 1 To Len(oGetDados:aCols)
						If aPedidos[nX][3]+aPedidos[nX][4] == oGetDados:aCols[nY,nPPEDIDO]+oGetDados:aCols[nY,nPITEMPC]
							nQtdNF += oGetDados:aCols[nY,nPQUANT]
						Endif
					Next nY

					nTotPed := nQuant - nQuje - nQtdCla - nQtdNF

					If nTotPed == 0
						Aviso(STR0137,STR0152 + AllTrim(aPedidos[nX][3])+"|"+AllTrim(aPedidos[nX][4]) + STR0153, {"Ok"}, 2) //"Não é possivel vincular o pedido: "#", pois o saldo ja foi atendido"
						lRet := .F.
					Else
						//Retira o pedido do array, para que ainda possa ser utilzado para vinculo
						//pois o pedido ainda possue saldo
						nPosPc := aScan(aPedItBkp,{|x| x[1] == aPedidos[nX][3] .And. x[2] == aPedidos[nX][4]})
						If nPosPc > 0
							aDel(aPedItBkp,nPosPc)
							aSize(aPedItBkp,Len(aPedItBkp)-1)
						Endif
					Endif
				Endif
			Endif
		Next nX

		//Processo de vincular pedidos (parcial ou total)
		If lRet
			For nX := 1 To Len(aPedidos)
				If aPedidos[nX][1] .And. !aPedidos[nX][Len(aPedidos[1])]
					If Select("PCMULT") > 0
						PCMULT->(DbCloseArea())
					Endif

					cQry := " SELECT C7_FILENT, C7_ITEM, C7_NUM, C7_PRODUTO, C7_QUANT-C7_QUJE-C7_QTDACLA AS QTDDISP, R_E_C_N_O_ AS RECNO"
					cQry += " FROM " + RetSqlName("SC7")
					cQry += " WHERE D_E_L_E_T_ = ' '"
					cQry += " AND C7_NUM = '" + aPedidos[nX][3] + "'"
					cQry += " AND C7_FORNECE = '" + cForn + "'"

					If lConsLoja
						cQry += " AND C7_LOJA = '" + cLoja + "'"
					Endif

					cQry += " AND C7_FILENT = '"+xFilEnt(xFilial("SC7"),"SC7")+"'"
					cQry += " AND C7_RESIDUO = ' '"
					cQry += " AND D_E_L_E_T_ = ' '"

					//Busca produto
					//1 - Pedidos apenas com o item (produto) igual ao item posicionado
					cQry += " AND C7_PRODUTO IN ('" + cProdAten + "')"
					cQry += " AND C7_ITEM = '" + aPedidos[nX][4] + "'"

					//Retira item ja vinculado
					For nY := 1 To Len(aPedItBkp)
						If aPedItBkp[nY,1] == aPedidos[nX][3]
							If !("C7_ITEM NOT IN" $ cQry)
								cQry += " AND C7_ITEM NOT IN ('" + aPedItBkp[nY,2] + "'"
							Else
								cQry += " ,'" + aPedItBkp[nY,2] + "'"
							Endif
						Endif
					Next nY

					If "C7_ITEM NOT IN" $ cQry
						cQry += ")"
					Endif

					cQry := ChangeQuery(cQry)
					dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQry),"PCMULT",.T.,.T.)

					DbSelectArea("PCMULT")
					While PCMULT->(!EOF())
						//Saldo disponivel - saldo ja utilizado na NF
						nSldPed := PCMULT->QTDDISP - nQtdNF
						If nSldPed > 0

							SC7->(DbGoto(PCMULT->RECNO))

							n := oGetDados:nAt

							// Calcula quantidade total dos pedidos utilizados.
							nSaldo := nProdQtd

							If nSldPed > nSaldo
								nSldPed := nSaldo
							EndIf

							If nSldPed == nSaldo // Caso a quantidade da NF seja igual ao do pedido de compra.
								If nSaldo > 0
									oGetDados:aCols[oGetDados:nAt, nPPEDIDO] := PCMULT->C7_NUM
									oGetDados:aCols[oGetDados:nAt, nPITEMPC] := PCMULT->C7_ITEM

									aCols[n, nPPEDIDO] := PCMULT->C7_NUM
									aCols[n, nPITEMPC] := PCMULT->C7_ITEM

									nProdQtd := 0
								Endif
							ElseIf nSldPed < nSaldo // Caso o saldo do pedido seja menor do que a quantidade restante no item da NF.

								If MsgYesNo(STR0154 + AllTrim(PCMULT->C7_NUM)+"|"+AllTrim(PCMULT->C7_ITEM) + STR0155 + StrZero(oGetDados:nAt,nTITEM) + STR0156) //"Quantidade do pedido|item: "#" é inferior ao item da NF: "#". Deseja incluir o saldo em um nova linha?"
									If nSaldo - nSldPed > 0
										// Altera linha atual do aCols para subtrair a quantidade do pedido de compra.
										// Para casos onde o saldo do pedido seja menor do que a quantidade da nota fiscal.
										VincMultPC(aPedidos,nSaldo - nSldPed,aColsBkp,oGetDados:aCols[oGetDados:nAt,nPITEM],nMultPC,.T.,n,.F.)

										nProdQtd := nSaldo - nSldPed
									EndIf

									// Inclui linha nova com o saldo do pedido de compra.
									VincMultPC(aPedidos,nSldPed,aColsBkp,cItem,nMultPC)
								Else
									oGetDados:aCols[oGetDados:nAt, nPPEDIDO] := PCMULT->C7_NUM
									oGetDados:aCols[oGetDados:nAt, nPITEMPC] := PCMULT->C7_ITEM

									aCols[n, nPPEDIDO] := PCMULT->C7_NUM
									aCols[n, nPITEMPC] := PCMULT->C7_ITEM

									nProdQtd := 0
								Endif
							EndIf

							cItem := SomaIt(cItem)
							oGetDados:aCols := aCols
						EndIf
						PCMULT->(DbSkip())
					Enddo
					PCMULT->(DbCloseArea())
				Endif
			Next nX
		Endif
	Elseif lRet .And. nMultPc == 2 //Pedido
		aColsBkp	:= aClone(oGetDados:aCols)
		aCols		:= aClone(oGetDados:aCols)
		cItem		:= StrZero(Len(aColsBkp)+1,nTITEM)

		aProdBkp	:= {}
		aPedItBkp	:= {}

		//aProdBkp		- Busca produto que não tem vinculo com pedido
		//aPedItBkp	- Busca os pedidos ja vinculados
		For nX := 1 To Len(aColsBkp)
			If aScan(aProdBkp,{|x| x[1] == aColsBkp[nX][nPCOD]}) == 0 .And. Empty(aColsBkp[nX][nPPEDIDO])
				aAdd(aProdBkp,{aColsBkp[nX][nPCOD],aColsBkp[nX][nPQUANT],aColsBkp[nX][nPITEM]})
			Endif

			If !Empty(aColsBkp[nX][nPPEDIDO])
				If aScan(aPedItBkp,{|x| x[1] == aColsBkp[nX][nPPEDIDO] .And. x[2] == aColsBkp[nX][nPITEMPC]}) == 0
					aAdd(aPedItBkp,{aColsBkp[nX][nPPEDIDO],aColsBkp[nX][nPITEMPC]})
				Endif
			Endif
		Next nX

		//Busca por itens iguais
		aPrds := COMITIG(cForn,cLoja,SDS->DS_DOC,SDS->DS_SERIE,SDS->DS_FILIAL)
		If Len(aPrds) > 0
			//Busca por itens iguais sem vinculo.
			//Apagado do aProdBkp para não vincular item
			For nX := 1 To Len(aPrds)
				//O mesmo produto em itens diferentes na NF
				For nY := 1 To Len(aProdBkp)
					If nY > Len(aProdBkp)
						Exit
					Endif

					If aProdBkp[nY,1] == aPrds[nX]
						aDel(aProdBkp,nY)
						aSize(aProdBkp,Len(aProdBkp)-1)
						lPrdIgual := .T.
						If Empty(cPrdIgual)
							cPrdIgual := STR0187 + AllTrim(aPrds[nX]) //"Os Produto(s): "
						Else
							cPrdIgual += "|" + AllTrim(aPrds[nX])
						Endif
					Endif
				Next nY
			Next nX
		Endif

		If lPrdIgual
			Aviso(STR0137,cPrdIgual + STR0157, {"Ok"}, 2) //" são iguais em mais de 1 item, por esse motivo o mesmo deve ser vinculado por ITEM"
		Endif

		//Verifica se esta vinculando algum pedido pela 1º vez
		//Valida que todos os itens ja foram atendidos.
		For nX := 1 To Len(aPedidos)
			If aPedidos[nX][1] .And. !aPedidos[nX][Len(aPedidos[1])] .And. Len(aProdBkp) == 0
				If !lPrdIgual
					Aviso(STR0137,STR0158, {"Ok"}, 2) //"Não é possivel mais vincular pedidos, pois o saldo ja foi atendidos pelos pedidos de compras."
				Endif
				lRet := .F.
			Endif
		Next nX

		//Verifica se esta vinculando algum pedido pela 1º vez
		//Valida se o pedido possui o mesmo produto em diferentes itens,
		//se possuir o pedido sera ignorado e alertado para vincular por ITEM
		If lRet
			For nX := 1 To Len(aPedidos)
				If aPedidos[nX][1] .And. !aPedidos[nX][Len(aPedidos[1])]
					nPedIgual := COMPCPRDUP(aPedidos[nX][3])

					If nPedIgual == 1
						If Empty(cPedIgual)
							cPedIgual := STR0188 + AllTrim(aPedidos[nX][3]) //"Pedido(s): "
						Else
							cPedIgual += "|" + AllTrim(aPedidos[nX][3])
						Endif

						aPedidos[nX][1] := .F.
					Endif
				Endif
			Next nX

			If !Empty(cPedIgual)
				Aviso(STR0137,cPedIgual + STR0159, {"Ok"}, 2) //" não serão utilizados, pois possuem produto iguais em itens diferentes no PEDIDO. O mesmo deve ser utilizado vinculo por ITEM."
			Endif
		Endif

		//Processo de vincular pedidos (parcial ou total)
		If lRet
			For nX := 1 To Len(aPedidos)
				If aPedidos[nX][1] .And. !aPedidos[nX][Len(aPedidos[1])]
					If Select("PCMULT") > 0
						PCMULT->(DbCloseArea())
					Endif

					cQry := " SELECT C7_FILENT, C7_ITEM, C7_NUM, C7_PRODUTO, C7_QUANT-C7_QUJE-C7_QTDACLA AS QTDDISP, R_E_C_N_O_ AS RECNO"
					cQry += " FROM " + RetSqlName("SC7")
					cQry += " WHERE D_E_L_E_T_ = ' '"
					cQry += " AND C7_NUM = '" + aPedidos[nX][3] + "'"
					cQry += " AND C7_FORNECE = '" + cForn + "'"

					If lConsLoja
						cQry += " AND C7_LOJA = '" + cLoja + "'"
					Endif

					cQry += " AND C7_FILENT = '"+xFilEnt(xFilial("SC7"),"SC7")+"'"
					cQry += " AND C7_RESIDUO = ' '"
					cQry += " AND D_E_L_E_T_ = ' '"

					//Busca produto

					//2 - Busca pedidos com os itens que não possuem vinculo com pedidos
					For nY := 1 To Len(aProdBkp)
						If nY == 1
							cQry += " AND C7_PRODUTO IN ('" + aProdBkp[nY,1] + "'"
							If nY == Len(aProdBkp)
								cQry += ")"
							Endif
						Else
							cQry += " ,'" + aProdBkp[nY,1] + "'"
							If nY == Len(aProdBkp)
								cQry += ")"
							Endif
						Endif
					Next nY

					//Retira item ja vinculado
					For nY := 1 To Len(aPedItBkp)
						If aPedItBkp[nY,1] == aPedidos[nX][3]
							If !("C7_ITEM NOT IN" $ cQry)
								cQry += " AND C7_ITEM NOT IN ('" + aPedItBkp[nY,2] + "'"
							Else
								cQry += " ,'" + aPedItBkp[nY,2] + "'"
							Endif
						Endif
					Next nY

					If "C7_ITEM NOT IN" $ cQry
						cQry += ")"
					Endif

					cQry := ChangeQuery(cQry)
					dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQry),"PCMULT",.T.,.T.)

					nTotPed := 0

					DbSelectArea("PCMULT")
					While PCMULT->(!EOF())
						nSldPed := PCMULT->QTDDISP
						If nSldPed > 0

							SC7->(DbGoto(PCMULT->RECNO))

							nPPrdBkp := aScan(aProdBkp,{|x| x[1] == PCMULT->C7_PRODUTO})

							n				:= Val(aProdBkp[nPPrdBkp,3])
							oGetDados:nAt	:= Val(aProdBkp[nPPrdBkp,3])

							// Calcula quantidade total dos pedidos utilizados.
							nSaldo := aProdBkp[nPPrdBkp,2]

							If nPPrdBkp > 0

								// Calcula quantidade total dos pedidos utilizados.
								If nSldPed > nSaldo
									nSldPed := nSaldo
								EndIf

								If nSldPed == nSaldo // Caso a quantidade da NF seja igual ao do pedido de compra.
									oGetDados:aCols[oGetDados:nAt, nPPEDIDO] := PCMULT->C7_NUM
									oGetDados:aCols[oGetDados:nAt, nPITEMPC] := PCMULT->C7_ITEM

									aCols[n, nPPEDIDO] := PCMULT->C7_NUM
									aCols[n, nPITEMPC] := PCMULT->C7_ITEM

									aProdBkp[nPPrdBkp,2] := 0

								ElseIf nSldPed < nSaldo // Caso o saldo do pedido seja menor do que a quantidade restante no item da NF.

									If nSaldo - nSldPed > 0

										// Altera linha atual do aCols para subtrair a quantidade do pedido de compra.
										// Para casos onde o saldo do pedido seja menor do que a quantidade da nota fiscal.
										VincMultPC(aPedidos,nSaldo - nSldPed,aColsBkp,aProdBkp[nPPrdBkp,3],nMultPC,.T.,n,.F.)

										aProdBkp[nPPrdBkp,2] := nSaldo - nSldPed
									EndIf

									// Inclui linha nova com o saldo do pedido de compra.
									VincMultPC(aPedidos,nSldPed,aColsBkp,cItem,nMultPC)

								EndIf

								cItem := SomaIt(cItem)
								oGetDados:aCols := aClone(aCols)
							Endif
						EndIf
						PCMULT->(DbSkip())
					Enddo
					PCMULT->(DbCloseArea())
				Endif
			Next nX
		Endif
	Elseif lRet .And. nMultPc == 3 //Desvincular

		If !lRetPed
			Aviso(STR0137,STR0160, {"Ok"}, 2) //"Não há pedidos para realizar o desvinculo."
			lRet := .F.
		Else
			aCols		:= oGetDados:aCols
			aColsBkp	:= aClone(oGetDados:aCols)

			For nX := 1 To Len(aPedidos)
				If aPedidos[nX][1]
					nMarcado++
				Endif
			Next nX

			If nMarcado == Len(aPedidos)
				lPedOri := ComXItOri(aColsAnt, .T.)
				lOriTemPed := lPedOri
			Endif

			IF lPedOri // Tem pedido no SDT original ou nMarcado != Len(aPedidos)
				For nX := 1 To Len(aPedidos)
					If aPedidos[nX][1]
						nPosItem := AScan(oGetDados:aCols, {|x| AllTrim(x[nPITEM]) == AllTrim(aPedidos[nX,4])})

						If nPosItem > 0
							nQtdItem := oGetDados:aCols[nPosItem,nPQUANT]
							cCodItem := oGetDados:aCols[nPosItem,nPCOD]

							//Busca por itens iguais
							aPrds := COMITIG(SDS->DS_FORNEC,SDS->DS_LOJA,SDS->DS_DOC,SDS->DS_SERIE,SDS->DS_FILIAL)
							If Len(aPrds) > 0
								nPPrd := aScan(aPrds,{|x| x == cCodItem})
								If nPPrd > 0
									ComXItOri(aColsAnt, .F., @aDadosOri)
									nPosOri := 0
									nPosOri := AScan(aDadosOri, {|x| AllTrim(x[nPITEM]) == AllTrim(aPedidos[nX,4])})
									For nP := 1 To Len(oGetDados:aCols)
										If cCodItem == oGetDados:aCols[nP,nPCOD] .And. Empty(oGetDados:aCols[nP,nPPEDIDO]) .And. nPosOri == 0
											nCont++
										Endif
									Next nP

									If nCont > 1
										lPrdIgual := .T.
									Endif
								Endif
							Endif

							//Ser for desvincular um produto que esta em mais de um item da NF
							//Sera apresentada um tela para que o usuario defina em qual item deseja desvincular,
							//Caso contrario sera feito o desvinculo normalmente.
							If lOriTemPed
								nPosCodPc := 0
							ElseIf !lPrdIgual
								nPosCodPc := AScan(oGetDados:aCols, {|x|  Val(x[nPITEM]) == nPosItem .And. AllTrim(x[nPCOD]) == AllTrim(cCodItem) .And. Empty(AllTrim(x[nPPEDIDO]))})
							Else
								nPosCodPc := COMITDESV(cCodItem,nPosItem,oGetDados:aCols[nPosItem,nPPEDIDO],oGetDados:aCols[nPosItem,nPITEMPC])
								If nPosCodPc == nPosItem
									nPosCodPc := 0
								Endif
							Endif

							If nPosCodPc > 0
								oGetDados:aCols[nPosCodPc,nPQUANT] += nQtdItem
								oGetDados:aCols[nPosCodPc,nPTOTAL] := oGetDados:aCols[nPosCodPc,nPQUANT]*oGetDados:aCols[nPosCodPc,nPVUNIT]

								aDel(oGetDados:aCols,nPosItem)
								aSize(oGetDados:aCols,Len(oGetDados:aCols)-1)
							Elseif nPosCodPc == 0
								oGetDados:aCols[nPosItem,nPPEDIDO] := Space(nTPEDIDO)
								oGetDados:aCols[nPosItem,nPITEMPC] := Space(nTITEMPC)
							Endif

							aCols := aClone(oGetDados:aCols)

						Endif
					Endif
				Next nX

				If lPrdIgual
					//Valor da NF Original
					aCols	:= GDNFORIG({},SDS->DS_FORNEC,SDS->DS_LOJA,SDS->DS_DOC,SDS->DS_SERIE,1)
					nTotNF := 0

					For nX := 1 to Len(aCols)
						nTotNF += aCols[nX,nPTOTAL]
					Next nX

					//Valor da NF atualizada
					nTotNFAtu	:= 0

					For nX := 1 to Len(oGetDados:aCols)
						nTotNFAtu += oGetDados:aCols[nX,nPTOTAL]
					Next nX

					If nTotNF <> nTotNFAtu
						if Abs( nTotNF - nTotNFAtu ) == 0.01
							aCols := aClone(oGetDados:aCols)
						else
							Aviso(STR0137,STR0161,{"Ok"}) //"Atencao"#"Valor da NF original diferente do valor da NF alterada. Sera desfeito o desvinculo."
							oGetDados:aCols	:= aClone(aColsBkp)
							aCols := aClone(aColsBkp)
						endif
					Else
						aCols := aClone(oGetDados:aCols)
					Endif
				Endif
			Endif
		Endif
	Endif

	// Atualiza TES e Impostos
	If lRet
		lContinua := .T.
		SC7->(DbSetOrder(14))
		For nX := 1 To Len(oGetDados:aCols)
			If lContinua
				If SC7->(DbSeek(xFilial("SC7")+oGetDados:aCols[nX,nPPEDIDO]+oGetDados:aCols[nX,nPITEMPC]))
					If !Empty(SC7->C7_TES)
						aCols := oGetDados:aCols
						oGetDados:aCols[nX,nPTES] := SC7->C7_TES
						aCols[nX][nPTES] := SC7->C7_TES // Preenche aCols tambem, pois nas linhas abaixo o objeto sobrescreve o array.

						lContinua := ColAtuImp(oGetDados:aCols[nX,nPTES],nX)
					EndIf
				EndIf
			Else
				Exit
			EndIf
		Next nX
	EndIf

	If lRet
		n := Len(aCols)
		//Ajuste numeração do item, e descrição do produto
		For nX := 1 To Len(oGetDados:aCols)
			oGetDados:aCols[nX,nPITEM] := StrZero(nX,nTITEM)

			If Empty(AllTrim(oGetDados:aCols[nX,nPDESC]))
				oGetDados:aCols[nX,nPDESC] := Posicione("SB1",1,xFilial("SB1") + PadR(oGetDados:aCols[nX][nPCOD],nTB1COD),"B1_DESC")
			Endif
		Next nX

		oGetDados:oBrowse:Refresh()
	Endif
	RestArea(aArea)

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} COMITDESV
Tela para que o usuario informe em qual item deseja retornar a
quantidade desvinculada.

@author rodrigo m pontes
@since 09/02/17
@version 1.0
@Return lRet
/*/
//-------------------------------------------------------------------

Static Function COMITDESV(cCodItem,nPosItem,cPedDesv,cItPCDesv)

	Local nRet		:= 0
	Local nX		:= 0
	Local nTela		:= 0
	Local nPCOD		:= GdFieldPos("DT_COD")
	Local nPPEDIDO	:= GDFieldPos("DT_PEDIDO")
	Local nPITEM	:= GDFieldPos("DT_ITEM")
	Local nTITEM	:= TamSx3("DT_ITEM")[1]
	Local aItDesv	:= {}
	Local aCampos	:= {}
	Local bLine		:= Nil
	Local aSize		:= MsAdvSize()
	Local nlTl1		:= aSize[1]
	Local nlTl2		:= aSize[2]-20
	Local nlTl3		:= aSize[1]+300
	Local nlTl4		:= aSize[2]+480

	For nX := 1 To Len(oGetDados:aCols)
		If oGetDados:aCols[nX,nPCOD] == cCodItem .And. Empty(oGetDados:aCols[nX,nPPEDIDO])
			aAdd(aItDesv,{.F.,cCodItem,oGetDados:aCols[nX,nPITEM],.F.})
		Endif
	Next nX

	nPos := aScan(aItDesv,{|x| x[3] == StrZero(nPosItem,nTITEM)})
	If nPos == 0
		aAdd(aItDesv,{.F.,cCodItem,StrZero(nPosItem,nTITEM),.F.})
	Endif

	aCampos := {"",RetTitle("DT_COD"),RetTitle("DT_ITEM")}
	bLine := {|| {If(aItDesv[oBrowseIT:nAt,1],oColOK,oColNo),;
		aItDesv[oBrowseIT:nAt,2],;
		aItDesv[oBrowseIT:nAt,3]}}

	Define MsDialog oDlgIT Title STR0165 From nlTl1,nlTl2 To nlTl3,nlTl4 Pixel //"Item a ser restituido"

	//-- Cabecalho
	@(nlTl1+10),nlTl2 To (nlTl1+22),(nlTl2+240) Pixel Of oDlgIT

	@(nlTl1+12),(nlTl2+8) Say STR0162 + AllTrim(cPedDesv) + STR0163 + cItPCDesv  Pixel Of oDlgIT //"Definir em qual item a quantidade deve ser restituido do Pedido: "#" Item PC: "

	oBrowseIT := TCBrowse():New(nlTl1+30,nlTl2,nlTl4-245,nlTl3-200,,aCampos,,oDlgIT,,,,,{|| MarcaPC(@aItDesv,oBrowseIT:nAt,,,oBrowseIT),oBrowseIT:Refresh()},,,,,,,,,.T.)
	oBrowseIT:SetArray(aItDesv)
	oBrowseIT:bLine := bLine

	//-- Botoes
	TButton():New(nlTl1+134,nlTl2+3,STR0164,oDlgIT,{|| MontaTela(6)},055,012,,,,.T.) //"NF Original"

	Define SButton From nlTl1+134,nlTl2+167 Type 1 Action Iif(ValidIT(aItDesv),(nTela := 1,oDlgIT:End()),) Enable Of oDlgIT
	Define SButton From nlTl1+134,nlTl2+202 Type 2 Action oDlgIT:End() Enable Of oDlgIT

	Activate Dialog oDlgIT Centered

	If nTela == 0
		nRet := -1
	Else
		nRet := Val(aItDesv[aScan(aItDesv,{|x| x[1] == .T.}),3])
	Endif

Return nRet

//-------------------------------------------------------------------
/*/{Protheus.doc} ValidIT
Valida se foi selecionado apenas 1 item para realizar o desvinculo

@author rodrigo m pontes
@since 09/02/17
@version 1.0
@Return lRet
/*/
//-------------------------------------------------------------------

Static Function ValidIT(aItDesv)

	Local nX		:= 0
	Local lRet		:= .T.
	Local nCount	:= 0

	For nX := 1 To Len(aItDesv)
		If aItDesv[nX,1]
			nCount++
		Endif
	Next nX

	If nCount > 1
		Aviso(STR0137,STR0166,{"Ok"}) //"Atencao"#"Selecione apenas 1 item."
		lRet := .F.
	Elseif nCount == 0
		Aviso(STR0137,STR0167,{"Ok"}) //"Atencao"#"Selecionar 1 item para que o desvinculo ocorra."
		lRet := .F.
	Endif

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} COMPCPRDUP
Valida se o pedido possui um produto e mais de um item.

@author rodrigo m pontes
@since 09/02/17
@version 1.0
@Return lRet
/*/
//-------------------------------------------------------------------

Static Function COMPCPRDUP(cPedido)

	Local nRet		:= 0
	Local aPrd		:= {}
	Local nPrd		:= 0
	Local aArea	:= GetArea()

	DbSelectArea("SC7")
	SC7->(DbSetOrder(14))
	If SC7->(DbSeek(xFilEnt(xFilial("SC7"),"SC7") + cPedido))
		While SC7->(!EOF()) .And. SC7->C7_NUM == cPedido
			nPrd := aScan(aPrd,{|x| x[1] == SC7->C7_PRODUTO})
			If nPrd == 0
				aAdd(aPrd,{SC7->C7_PRODUTO,1})
			Else
				aPrd[nPrd,2] += 1
			Endif
			SC7->(DbSkip())
		Enddo

		nPrd := aScan(aPrd,{|x| x[2] > 1})
		If nPrd > 0
			nRet := 1
		Endif
	Endif

	RestArea(aArea)

Return nRet

//-------------------------------------------------------------------
/*/{Protheus.doc} LoadItens
Carregamento de Itens de pedido de fornecedores diferentes

@author guilherme.pimentel
@since 01/09/2014
@version 1.0
@Return lRet
/*/
//-------------------------------------------------------------------

Function LoadItens(cProduto,lPedDoc,nMultPC,aColsAnt,cComboFor,oBrowse,aCampos,aPedidos)

	Local lRet 		:= .T.
	Local cCodLoj	:= ""
	Local cCbmFor	:= ""
	Local cCbmLoj	:= ""
	Local nTCOD		:= TamSX3("A2_COD")[1]
	Local nTLOJA	:= TamSX3("A2_LOJA")[1]

	aPedidos := {}

	cCodLoj := SubStr(cComboFor, At(' | ',cComboFor)+3, Len(cComboFor))
	cCodLoj := SubStr(cCodLoj,1, At(' - ',cCodLoj)-1)
	cCbmFor := SubStr(cCodLoj, 1, At('/',cCodLoj)-1)
	cCbmLoj := SubStr(cCodLoj, At('/',cCodLoj)+1, Len(cCodLoj))
	cCbmFor := Padr(cCbmFor,nTCOD)
	cCbmLoj := Padr(cCbmLoj,nTLOJA)

	Documentos(cProduto,lPedDoc,nMultPC,aColsAnt,cCbmFor,cCbmLoj,@aPedidos,@oBrowse)

	bLine := oBrowse:bLine

	oBrowse:SetArray(aPedidos)
	oBrowse:bLine := bLine

	oBrowse:Refresh()

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} ValidPC
Validacao dos campos qtde e preco Unit. do pedido de compra com
o documento NFe

@param	cCodProd	codigo do produto
@param	lPedDoc		indica se a busca e por documento ou item
@param	aPedidos	array com os pedidos exibidos na tela de vinculo
@param	nLinha		indica a linha do browse de pedidos que foi marcada

@author	Rodrigo de Toledo Silva
@since 01/07/11
/*/
//-------------------------------------------------------------------

Static Function ValidPC(cCodProd,lPedDoc,aPedidos,nLinha,nMultPC,lConsLoja)

	Local lRet		:= .T.
	Local lAchou	:= .F.
	Local lMarcado	:= .F.
	Local aArea		:= SDT->(GetArea())
	Local aAreaSC7	:= SC7->(GetArea())
	Local aProds	:= {}
	Local nPosCod	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_COD"})
	Local nPosQtde	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_QUANT"})
	Local nX		:= 0
	Local nY		:= 0
	Local nSldPed	:= 0
	Local nTotQtd	:= 0
	Local nTotPed	:= 0
	Local n			:= oGetDados:nAt
	Local lCOMCOLPC	:= ExistBlock("COMCOLPC")
	Local lForPCNF  := SuperGetMV("MV_FORPCNF",,.F.)

	// Ponto de entrada para validacao do pedido selecionado
	If lCOMCOLPC
		lRet := ExecBlock("COMCOLPC",.F.,.F.,{aCols,"TMP"})
	ElseIf nMultPC > 0	// Validacao para vinculo de multiplos pedidos
		If nMultPc == 3
			lRet := .T.
		Else
			For nX := 1 To Len(oGetDados:aCols)
				AADD(aProds,AllTrim(aCols[nX][nPosCod]))
				nTotQtd += oGetDados:aCols[nX][nPosQtde]
			Next nX

			// Verifica se ha pedidos marcados
			For nX := 1 To Len(aPedidos)
				If aPedidos[nX][1] .And. !aPedidos[nX][Len(aPedidos[1])]
					lMarcado := .T.
					Exit
				EndIf
			Next nX

			If nMultPC == 1			// Vinculo de multiplos pedidos por item
				nTotQtd := aCols[N][nPosQtde]
			EndIf

			If lRet
				DbSelectArea("SC7")
				SC7->(DbSetOrder(14))
				For nY := 1 To Len(aPedidos)
					If aPedidos[nY][1] .And. !aPedidos[nY][Len(aPedidos[1])]
						//Posiciona Pedido de Compra
						cSeek := xFilial("SC7")+aPedidos[nY][3]
						SC7->(dbSeek(cSeek))

						While ( !Eof() .And. SC7->C7_FILENT+SC7->C7_NUM==cSeek )
							// Verifica se o fornecedor esta correto
							If C7_FORNECE+If(lConsLoja,C7_LOJA,"") == SDS->DS_FORNEC+If(lConsLoja,SDS->DS_LOJA,"") .Or. lForPCNF
								If aScan(aProds,{|x| x == AllTrim(SC7->C7_PRODUTO)}) > 0
									lAchou := .T.
								EndIf

								nSldPed := SC7->C7_QUANT-SC7->C7_QUJE-SC7->C7_QTDACLA
								If nSldPed > 0 .And. Empty(SC7->C7_RESIDUO) .And. If(nMultPC == 1,SC7->C7_ITEM==aPedidos[nY][4],.T.)
									nTotPed += nSldPed
								EndIf
							EndIf
							SC7->(dbSkip())
						EndDo
					EndIf
				Next nY

				If lMarcado
					// Se nenhum produto dos pedidos selecionados corresponde a nenhum dos produtos da nota, nao efetua o vinculo
					If !lAchou
						Aviso(STR0004,STR0091,{STR0077})	// Nenhum produto dos pedidos selecionados confere com o(s) produtos da nota/item nota. Vínculo não será efetuado.
						lRet := .F.
					EndIf
				EndIf
			EndIf
		Endif
	EndIf

	SC7->(RestArea(aAreaSC7))
	SDT->(RestArea(aArea))

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} ValidXPC
Validacao para utilizacao da funcionalidade de vinculo de multiplos pedidos

@param	cCodProd	codigo do produto
@param	lPedDoc		indica se a busca e por documento ou item
@param	aPedidos	array com os pedidos exibidos na tela de vinculo
@param	nLinha		indica a linha do browse de pedidos que foi marcada

@author	TOTVS
@since 19/05/14
/*/
//-------------------------------------------------------------------

Static Function ValidXPC(lRemet,nMultPC,aColsAnt)

	Local lRet		:= .T.

	If SDS->DS_TIPO $ "N" .Or. lRemet	//-- NF Normal (Compra) ou CT-e de saida
		// Posiciona no primeir item da nota
		DbSelectArea("SDT")
		DbSetOrder(2)
		MsSeek(xFilial("SDT")+SDS->(DS_FORNEC+DS_LOJA+DS_DOC+DS_SERIE))

		// Verifica se foi selecionada opcao Vinc Mult PC
		If lRet .And. (nMultPC == 1 .Or. nMultPC == 2)
			If lRet
				If !Empty(AllTrim(oGetDados:aCols[oGetDados:nAt,GdFieldPos("DT_PEDIDO")]))
					Aviso(STR0004,STR0168,{STR0077}) //"Este item ja possui vinculo com pedido, favor utilizar um item que não possua vinculo com nenhum pedido."
					lRet := .F.
				Endif
			Endif
		EndIf

	EndIf

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} MarcaPC
Executada quando o registro e marcado para desmarcar os demais

@param	aPedidos	array com os pedidos exibidos em tela
@param	nLinha		linha do pedido que foi marcado.
@param	lPedDoc		indica se e selecao por documento.

@author	Rodrigo de Toledo
@since 30/10/09
/*/
//-------------------------------------------------------------------

Static Function MarcaPC(aPedidos,nLinha,lPedDoc,nMultPC,oBrowse)

	If !Empty(aPedidos)
		//-- Desmarca o item que ja estava marcado
		If !aPedidos[nLinha,Len(aPedidos[1])]
			aPedidos[nLinha,1] := !aPedidos[nLinha,1]
		Endif

		oBrowse:Refresh()
	EndIf

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} GetC7Recno
Funcao para retornar o recno do pedido

@param	cPedido		numero do pedido de compra

@author	Rodrigo de Toledo
@since 30/10/09
/*/
//-------------------------------------------------------------------

Static Function GetC7Recno(cPedido)

	SC7->(dbSetOrder(14))
	If SC7->(dbSeek(xFilial("SC7")+cPedido))
		If Type("n") <> "N"
			n := oGetDados:nAt
		Endif

		A103VisuPC(SC7->(Recno()))
	EndIf

Return .T.

//-------------------------------------------------------------------
/*/{Protheus.doc} NOMEFORIni
Busca o nome do cliente quando o tipo da nota for devolucao ou
beneficiamento caso contrario busca o nome do fornecedor

@author	Rodrigo de Toledo
@since 09/05/12
/*/
//-------------------------------------------------------------------

Function NOMEFORIni()

	Local cNomeFC := ""
	Local cFilSA1 := xFilial("SA1",SDS->DS_FILIAL)
	Local cFilSA2 := xFilial("SA2",SDS->DS_FILIAL)

	If SDS->DS_TIPO $ "DB"
		cNomeFC := Posicione("SA1",1,cFilSA1+SDS->(DS_FORNEC+DS_LOJA),"A1_NOME")
	Else
		cNomeFC := Posicione("SA2",1,cFilSA2+SDS->(DS_FORNEC+DS_LOJA),"A2_NOME")
	EndIf

Return(cNomeFC)

//-------------------------------------------------------------------
/*/{Protheus.doc} CPNJPict
Retorna a picture de acordo com o tipo do fornecedor/cliente

@author	Rodrigo de Toledo
@since 20/07/11
/*/
//-------------------------------------------------------------------

Function CPNJPict()

	Local cAlias := If(SDS->DS_TIPO $ "DB","SA1","SA2")

Return PicPes(Posicione(cAlias,1,xFilial(cAlias)+M->(DS_FORNEC+DS_LOJA),Substr(cAlias,2)+"_TIPO"))

//-------------------------------------------------------------------
/*/{Protheus.doc} NFORIValid
Valida o preenchimento da NF de Origem quando a nota for Dev/Comp

@author	Rodrigo de Toledo
@since 02/06/12
/*/
//-------------------------------------------------------------------

Function NFORIValid()

	Local lRet 	   	:= .T.
	Local cCampo   	:= ReadVar()
	Local aAreaSF2	:= SF2->(GetArea())
	Local aAreaSD2	:= SD2->(GetArea())
	Local aAreaSF1	:= SF1->(GetArea())
	Local aAreaSD1	:= SD1->(GetArea())
	Local cFilSD1	:= xFilial("SD1")
	Local cFilSD2	:= xFilial("SD2")
	Local cFilSF1	:= xFilial("SF1")
	Local cFilSF2	:= xFilial("SF2")
	Local nPNFORI	:= GDFieldPos("DT_NFORI")
	Local nPSERIORI := GDFieldPos("DT_SERIORI")
	Local nPITEMORI := GDFieldPos("DT_ITEMORI")
	Local nPCOD		:= GDFieldPos("DT_COD")

	If SDS->DS_TIPO == "D"
		SF2->(dbSetOrder(1))
		If cCampo == "M->DT_NFORI" .And. !Empty(AllTrim(M->DT_NFORI))
			If !SF2->(dbSeek(cFilSF2+M->DT_NFORI))
				Aviso(STR0004,STR0078,{STR0077})
				lRet := .F.
			Else
				aCols[n,nPSERIORI] := CriaVar("DT_SERIORI",.F.)
				aCols[n,nPITEMORI] := CriaVar("DT_ITEMORI",.F.)
			EndIf
		ElseIf cCampo == "M->DT_SERIORI"
			If !Empty(AllTrim(M->DT_SERIORI))
				If Empty(AllTrim(aCols[n,nPNFORI]))
					Aviso(STR0004,STR0080,{STR0077})
					lRet := .F.
				ElseIf !Empty(AllTrim(aCols[n,nPNFORI]))
					If !SF2->(dbSeek(cFilSF2+aCols[n,nPNFORI]+M->DT_SERIORI))
						Aviso(STR0004,STR0078,{STR0077})
						lRet := .F.
					EndIf
				EndIf
			EndIf
		ElseIf cCampo == "M->DT_ITEMORI"
			If !Empty(AllTrim(M->DT_ITEMORI))
				If Val(M->DT_ITEMORI) > 0
					M->DT_ITEMORI := PADL(Val(M->DT_ITEMORI),2,"0")
				EndIf
				If Empty(AllTrim(aCols[n,nPNFORI]))
					Aviso(STR0004,STR0078,{STR0077})
					lRet := .F.
				ElseIf !Empty(AllTrim(aCols[n,nPNFORI]))
					DbSelectArea("SF2")
					DbSetOrder(1)
					MsSeek(cFilSF2+aCols[n,nPNFORI]+aCols[n,nPSERIORI] )

					dbSelectArea("SD2")
					dbSetOrder(3)
					If !MsSeek(cFilSD2+aCols[n,nPNFORI]+aCols[n,nPSERIORI]+SF2->F2_CLIENTE+SF2->F2_LOJA+aCols[n,nPCOD]+M->DT_ITEMORI)
						Aviso(STR0004,STR0078,{STR0077})
						lRet := .F.
					EndIf
				EndIf
			EndIf
		EndIf
	ElseIf SDS->DS_TIPO == "C"
		SF1->(dbSetOrder(1))
		If cCampo == "M->DT_NFORI" .And. !Empty(AllTrim(M->DT_NFORI))
			If !SF1->(dbSeek(cFilSF1+M->DT_NFORI))
				Aviso(STR0004,STR0078,{STR0077})
				lRet := .F.
			Else
				aCols[n,nPNFORI] := CriaVar("DT_SERIORI",.F.)
				aCols[n,nPSERIORI] := CriaVar("DT_ITEMORI",.F.)
			EndIf
		ElseIf cCampo == "M->DT_SERIORI"
			If !Empty(AllTrim(M->DT_SERIORI))
				If Empty(AllTrim(aCols[n,nPNFORI]))
					Aviso(STR0004,STR0080,{STR0077})
					lRet := .F.
				ElseIf !Empty(AllTrim(aCols[n,nPNFORI]))
					If !SF1->(dbSeek(cFilSF1+aCols[n,nPNFORI]+M->DT_SERIORI))
						Aviso(STR0004,STR0078,{STR0077})
						lRet := .F.
					EndIf
				EndIf
			EndIf
		ElseIf cCampo == "M->DT_ITEMORI"
			If !Empty(AllTrim(M->DT_ITEMORI))
				If Empty(AllTrim(aCols[n,nPNFORI]))
					Aviso(STR0004,STR0078,{STR0077})
					lRet := .F.
				ElseIf !Empty(AllTrim(aCols[n,nPNFORI]))
					DbSelectArea("SF1")
					DbSetOrder(1)
					MsSeek(cFilSF1+aCols[n,nPNFORI]+aCols[n,nPSERIORI] )

					dbSelectArea("SD1")
					dbSetOrder(1)
					If !MsSeek(cFilSD1+aCols[n,nPNFORI]+aCols[n,nPSERIORI]+SF1->F1_FORNECE+SF1->F1_LOJA+aCols[n,nPCOD]+M->DT_ITEMORI)
						Aviso(STR0004,STR0078,{STR0077})
						lRet := .F.
					EndIf
				EndIf
			EndIf
		EndIf
	EndIf

	RestArea(aAreaSD1)
	RestArea(aAreaSF1)
	RestArea(aAreaSD2)
	RestArea(aAreaSF2)

Return (lRet)

//-------------------------------------------------------------------
/*/{Protheus.doc} DirFilial
Função que direciona os documentos do TOTVS Colaboração
para sua devida filial de processamento

@author	Flavio Lopes Rasta
@since 08/10/14
/*/
//-------------------------------------------------------------------

Function DirFilial(cFile,cCgc,cInscEst,lJob)

	Local oColab     := NIL
	Local aSM0       := FWLoadSM0()
	Local aFilInsc   := {}
	Local nX         := 1
	Local nQtdCNPJ	 := 0
	Local lRet       := .F.
	Local lChanFil	 := .F.
	Local lInscDup   := .F.
	Local lCGCNotEx	 := .F.
	Local nFilImp    := 0
	Local cGrpEmpImp := ""
	Local cCodFilImp := ""
	Local aFilEmp	 := {}
	Local lCOLFILDUP := ExistBlock("COLFILDUP")

	oColab          := ColaboracaoDocumentos():New()
	oColab:cModelo	:= ""
	oColab:cTipoMov := '2'
	oColab:cFlag	:= '0'
	oColab:cQueue	:= SubStr(cFile,1,3)
	oColab:cNomeArq := cFile

	If oColab:Consultar()
		If AllTrim(oColab:cEmpProc) == AllTrim(cEmpAnt) .And. AllTrim(oColab:cFilProc) == AllTrim(cFilAnt)
			cGrpEmpImp := cEmpAnt
			cCodFilImp := cFilAnt
			lRet       := .T.
		ElseIf !Empty(oColab:cEmpProc) .And. !Empty(oColab:cFilProc)
			cGrpEmpImp        := oColab:cEmpProc
			cCodFilImp        := oColab:cFilProc
			oColab:cCodErrErp := "COM002"
			oColab:gravaErroErp()
		Endif
	Endif

	If !lRet .And. Empty(cGrpEmpImp)
		For nX := 1 To Len(aSm0)
			If cCGC $ aSm0[nX][SM0_CGC]
				nQtdCNPJ++
			EndIf
		Next nX

		If nQtdCNPJ == 0
			lCGCNotEx := .T.
		Elseif nQtdCNPJ == 1
			If (nFilImp := (ASCan(aSm0,{|x| AllTrim(x[SM0_CGC]) == cCgc }))) > 0
				cGrpEmpImp := AllTrim(aSm0[nFilImp][SM0_GRPEMP])
				cCodFilImp := AllTrim(aSm0[nFilImp][SM0_CODFIL])
				If AllTrim(cGrpEmpImp) == AllTrim(cEmpAnt) .And. AllTrim(cCodFilImp) == AllTrim(cFilAnt)
					lRet:= .T.
				Else
					lRet := .F.
					lChanFil := .T.
				Endif
			Endif
		ElseIf nQtdCNPJ > 1
			If !Empty(AllTrim(cInscEst))
				//FORCA O CONTEUDO ISENTO
				If "ISENT" $ cInscEst
					cInscEst := "ISENTO"
				EndIf
			Else
				If !FwIsInCallStack("ImpXML_NFs")
					cInscEst := "ISENTO"
				Endif
			EndIf

			aFilInsc := InscEstSM0(cCgc,cInscEst,@lInscDup)

			If !Empty(aFilInsc)
				cGrpEmpImp := aFilInsc[1]
				cCodFilImp := aFilInsc[2]
				If AllTrim(cGrpEmpImp) == AllTrim(cEmpAnt) .And. AllTrim(cCodFilImp) == AllTrim(cFilAnt)
					lRet:= .T.
				Else
					lRet := .F.
					lChanFil := .T.
				Endif
			Endif
		Endif

		If !lRet .And. !lChanFil
			oColab          := ColaboracaoDocumentos():New()
			oColab:cModelo  := ""
			oColab:cTipoMov := '2'
			oColab:cFlag    := '0'
			oColab:cQueue   := SubStr(cFile,1,3)
			oColab:cNomeArq := cFile

			If oColab:Consultar()
				If lCGCNotEx
					oColab:cCodErrErp := "COM052"
					oColab:gravaErroErp()
				ElseIf AllTrim(oColab:cEmpProc) == AllTrim(cEmpAnt) .And. AllTrim(oColab:cFilProc) == AllTrim(cFilAnt)
					lRet := .T.
					cGrpEmpImp := cEmpAnt
					cCodFilImp := cFilAnt
				ElseIf lInscDup
					If lCOLFILDUP
						aFilEmp := ExecBlock("COLFILDUP",.F.,.F.,{cCgc,cInscEst})
						If ValType(aFilEmp) == "A" .And. Len(aFilEmp) == 2
							cGrpEmpImp := aFilEmp[1]
							cCodFilImp := aFilEmp[2]
						Endif
					Endif

					If Empty(cGrpEmpImp) .And. Empty(cCodFilImp)
						oColab:cCodErrErp := "COM042"
						oColab:gravaErroErp()
					Else
						If cGrpEmpImp == cEmpAnt .And. cCodFilImp == cFilAnt
							lRet := .T.
						Else
							lChanFil := .T.
						Endif
					Endif
				Else
					oColab:cCodErrErp := "COM002"
					oColab:gravaErroErp()
				Endif
			Endif
		Endif
	Endif

	ColGrvFil(cFile,"0",cGrpEmpImp,cCodFilImp,cCgc)
	oColab := Nil

Return {lRet,lChanFil,lInscDup,lCGCNotEx}

//-------------------------------------------------------------------
/*/{Protheus.doc} ImportCol
Funcao que realiza a importacao de um arquivo XML do TOTVS colaboracao

@param	cFile		caminho do arquivo que esta sendo importado
@param	lJob		indica se o processamento esta sendo fendo em job
@param	aProc		array para guardar os arquivos processados (M-Mess)
@param	aErros		array para guardar os arquivos com erros (M-Mess)

@author	Andre Anjos
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function ImportCol(cFile,lJob,aProc,aErros,cXMLOri,aErroERP)

	Local lRet 	   	:= .F.
	Local cError   	:= ""
	Local cWarning 	:= ""
	Local oFullXml 	:= NIL
	Local cXMLEncod	:= ""
	Local nNFeAut  	:= SuperGetMV("MV_COMCOL1",.F.,0)
	Local lIntGfe  	:= SuperGetMV("MV_INTGFE",.F.,.F.) .And. SuperGetMv("MV_INTGFE2",.F.,"2") == "1"
	Local lCteClas 	:= SuperGetMV("MV_CTECLAS",.F.,.F.)
	Local lCte     	:= .F.
	Local lGfexcol  := .F.
	Local lMVImpXML	:= SuperGetMv("MV_IMPXML",.F.,.F.) .And. CKO->(FieldPos("CKO_ARQXML")) > 0 .And. !Empty(CKO->(IndexKey(5)))
	Local cImport	:= Iif(lMVImpXML,"-import","-colab")
	Local cTpDoc	:= ""
	Local cComCol1	:= Iif(nNFeAut==0,"-monit",Iif(nNFeAut==1,"-prenota","-classif"))

	If Type("LTOMA4NFORI") <> "L"
		LTOMA4NFORI := .T.
	Endif

	If !Empty(cXMLOri)
		If SubStr(cXMLOri,1,1) != "<"
			nPosPesq := At("<",cXMLOri)
			cXMLOri  := SubStr(cXMLOri,nPosPesq,Len(cXMLOri))		// Remove caracteres estranhos antes da abertura da tag inicial do arquivo
		EndIf
	EndIf

	cXMLEncod := EncodeUtf8(cXMLOri)

	If Empty(cXMLEncod)
		cXMLEncod 	:= cXMLOri
		cXMLOri 	:= A140IRemASC(cXMLEncod)
		cXMLEncod 	:= EncodeUtf8(cXMLOri)
	EndIf

	If !Empty(cXMLEncod)
		oFullXML := XmlParser(cXMLEncod,"_",@cError,@cWarning)
	EndIf

	//Verificar com Transmite sobre UTF16(somente NFS está vindo com problema)
	If ValType(oFullXML) <> "O" .and. !Empty(cError)
		cError 		:= ""
		cXMLEncod 	:= cXMLOri
		cXMLOri 	:= A140IRemASC(cXMLEncod)
		cXMLEncod 	:= EncodeUtf16(cXMLOri)

		If !Empty(cXMLEncod)
			oFullXML := XmlParser(cXMLEncod,"_",@cError,@cWarning)
		Endif
	Endif

	If !Empty(cError) //-- Erro na sintaxe do XML
		If lJob
			aAdd(aErros,{cFile,"COM001 - " + STR0073 +cError,STR0074}) //-- Erro de sintaxe no arquivo XML: # Entre em contato com o emissor do documento e comunique a ocorrência.
		Else
			Aviso(STR0070,cError,{"OK"},2,"COMXCOMImp") //-- Erro
		EndIf
		aAdd(aErroErp,{cFile,"COM001"})
		lRet := .F.
	Else //-- Direciona processamento conforme tipo de documento
		If ValType(oFullXML)=="O"
			Do Case
				Case ValType(XmlChildEx(oFullXML,"_NFEPROC")) == "O" //-- Nota normal, devolucao, beneficiamento, bonificacao
					lRet := ImpXML_NFe(cFile,lJob,@aProc,@aErros,.F.,oFullXml:_NFeProc:_NFe,,cXmlOri,@aErroErp)
					cTpDoc := "-nfe"
				Case ValType(XmlChildEx(oFullXML,"_CTE")) == "O" //-- Nota de transporte
					lCte := .T.
					//Verifica se há integração com o Frete Embarcador
					If lIntGfe
						lRet := GFEA118XML(cFile,,,@aProc,@aErros,oFullXml:_CTe,.T.,oFullXML:_CTeProc:_ProtCte, @aErroERP,@lGfexcol)
						// XML não importado pelo GFE devido configuração de exceção de CFOP no GFE.
						If lRet .And. lGfexcol
							lRet := ImpXML_CTe(cFile,lJob,@aProc,@aErros,oFullXml:_CTe,@aErroERP,oFullXML:_CTeProc:_ProtCte)
							cTpDoc := "-cte"
						EndIf
					Else
						lRet := ImpXML_CTe(cFile,lJob,@aProc,@aErros,oFullXml:_CTe,@aErroERP,oFullXML:_CTe:_ProtCte)
						cTpDoc := "-cte"
					EndIf
				Case ValType(XmlChildEx(oFullXML,"_CTEPROC")) == "O" //-- Nota de transporte
					lCte := .T.
					//Verifica se há integração com o Frete Embarcador
					If lIntGfe
						lRet := GFEA118XML(cFile,,,@aProc,@aErros,oFullXml:_CTeProc:_Cte,.T.,oFullXML:_CTeProc:_ProtCte,@aErroERP,@lGfexcol)
						// XML não importado pelo GFE devido configuração de exceção de CFOP no GFE.
						If lRet .And. lGfexcol
							lRet := ImpXML_CTe(cFile,lJob,@aProc,@aErros,oFullXml:_CTeProc:_Cte,@aErroErp,oFullXML:_CTeProc:_ProtCte)
							cTpDoc := "-cte"
						EndIf
					Else
						lRet := ImpXML_CTe(cFile,lJob,@aProc,@aErros,oFullXml:_CTeProc:_Cte,@aErroErp,oFullXML:_CTeProc:_ProtCte)
						cTpDoc := "-cte"
					EndIf
				Case ValType(XmlChildEx(oFullXML,"_CTEOSPROC")) == "O" //-- Nota de transporte - CTEOS
					lCte := .T.
					//Verifica se há integração com o Frete Embarcador
					lRet := ImpXMLCTeOS(cFile,lJob,@aProc,@aErros,oFullXml:_CTeOsProc:_CteOS,@aErroErp,oFullXML:_CTeOsProc:_ProtCte)
					cTpDoc := "-cteos"
				Case FindFunction("ImpXML_Ave") .And. ValType(XmlChildEx(oFullXML,"_INVOIC_NFE_COMPL")) == "O" //-- Nota Fiscal Complementar
					lRet := ImpXML_Ave(cFile,lJob,@aProc,@aErros,oFullXml:_INVOIC_NFE_COMPL,cXMLOri,@aErroErp)
				Case ValType(XmlChildEx(oFullXML,"_TOTVSMESSAGE")) == "O" .And. ValType(XmlChildEx(oFullXML:_TOTVSMESSAGE:_BUSINESSMESSAGE:_BUSINESSCONTENT,"_PROCNEOGRIDNFSE")) == "O" // Nota de Servico
					lRet := ImpXML_NFs(cFile,lJob,@aProc,@aErros,oFullXml:_TOTVSMESSAGE:_BUSINESSMESSAGE:_BUSINESSCONTENT,@aErroErp)
					cTpDoc := "-nfs"
				Case ValType(XmlChildEx(oFullXML,"_PROCNEOGRIDNFSE")) == "O" // Nota de Servico
					lRet := ImpXML_NFs(cFile,lJob,@aProc,@aErros,oFullXml,@aErroErp)
					cTpDoc := "-nfs"
				Case ValType(XmlChildEx(oFullXML,"_PROCTRANSMITENFSE")) == "O"
					lRet := ImpXMLNFsT(cFile,lJob,@aProc,@aErros,oFullXml,@aErroErp)
					cTpDoc := "-nfs"
				Otherwise
					aAdd(aErros,{cFile,STR0169,""}) //"XML não está de acordo com nenhum tipo de documento"
					lRet:= .F.
			EndCase
		EndIf
		If lRet .And. (nNFeAut == 1 .Or. nNFeAut == 2 .Or. (nNFeAut == 0 .And. Iif(lCte,lCteClas,.F.))) .And. Iif( lCte, (!lIntGfe .Or. (lIntGfe .And. lGfexcol)), .T. )
			ProcDocs(1,.T.,,lJob)
		EndIf
	EndIf

	If lRet
		ComMetric("-inc",cImport,cTpDoc,cComCol1)
	Endif

	oFullXML := Nil
	DelClassIntF()

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} ComXTudoOk
Rotina de avaliacao TudOk

@author	Andre Anjos
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function ComXTudoOk()

	Local nPosNfOri	:= aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_NFORI"})
	Local nPosSerOri:= aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_SERIORI"})
	Local nPosItOri	:= aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_ITEMORI"})
	Local nPosCod	:= aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_COD"})
	Local nPosQtd	:= aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_QUANT"})
	Local nPosItem	:= aScan(oGetDados:aHeader,{|x| AllTrim(x[2])=="DT_ITEM"})
	Local aAreaSF2	:= SF2->(GetArea())
	Local aAreaSD2	:= SD2->(GetArea())
	Local aAreaSF1	:= SF1->(GetArea())
	Local aAreaSD1	:= SD1->(GetArea())
	Local lRet		:= .T.
	Local nX		:= 0
	Local nCont		:= 0
	Local cFilSD2	:= xFilial("SD2")
	Local cFilSF2	:= xFilial("SF2")

	If SDS->DS_TIPO == "D"		// Nota de Devolução
		For nX := 1 To Len(oGetDados:aCols)
			If !Empty(AllTrim(oGetDados:aCols[nX][nPosNfOri]))
				If Empty(AllTrim(oGetDados:aCols[nX][nPosItOri]))
					Aviso(STR0004,STR0063+oGetDados:aCols[nX][nPosItem]+STR0078,{STR0077})
					lRet := .F.
					nCont++
					Exit
				Else
					DbSelectArea("SF2")
					DbSetOrder(1)
					MsSeek(cFilSF2+oGetDados:aCols[nX][nPosNfOri]+oGetDados:aCols[nX][nPosSerOri] )

					dbSelectArea("SD2")
					dbSetOrder(3)
					If MsSeek(cFilSD2+oGetDados:aCols[nX][nPosNfOri]+oGetDados:aCols[nX][nPosSerOri]+SF2->F2_CLIENTE+SF2->F2_LOJA+oGetDados:aCols[nX][nPosCod]+oGetDados:aCols[nX][nPosItOri])
						If SD2->D2_QUANT < oGetDados:aCols[nX][nPosQtd]
							Aviso(STR0004,STR0063+oGetDados:aCols[nX][nPosItem]+STR0079,{STR0077})
							lRet := .F.
							nCont++
							Exit
						EndIf
					Else
						Aviso(STR0004,STR0063+oGetDados:aCols[nX][nPosItem]+STR0078,{STR0077})
						lRet := .F.
						nCont++
						Exit
					EndIf
				EndIf
				nCont++
			ElseIf !Empty(AllTrim(oGetDados:aCols[nX][nPosSerOri])) .Or. !Empty(AllTrim(oGetDados:aCols[nX][nPosItOri]))
				Aviso(STR0004,STR0063+oGetDados:aCols[nX][nPosItem]+STR0078,{STR0077})
			EndIf
		Next nX
	EndIf

	RestArea(aAreaSD1)
	RestArea(aAreaSF1)
	RestArea(aAreaSD2)
	RestArea(aAreaSF2)

Return(lRet)

//-------------------------------------------------------------------
/*/{Protheus.doc} VincMultPC
Vincula multiplos PC

@author	TOTVS
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function VincMultPC(aPedidos,nSldPed,aColsBkp,cItem,nMultPC,lLastIt,nPosicao,lNewLine)

	Local aAreaSDS	:= SDS->(GetArea())
	Local nPosCod	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_COD"})
	Local nPosProdF	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_PRODFOR"})
	Local nPosDescF	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_DESCFOR"})
	Local nPosSerie	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_SERIE"})
	Local nPosValor	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_VUNIT"})
	Local nPosFrete	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_VALFRE"})
	Local nPosSegur	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_SEGURO"})
	Local nPosDesp	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_DESPESA"})
	Local nPosDesc	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_VALDESC"})
	Local nPosTot	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_TOTAL"})
	Local nPosFCI	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_FCICOD"})
	Local nPosItem	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_ITEM"})
	Local nPosQtde	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_QUANT"})
	Local aCpoImp	:= {"DT_XMLICST","DT_XMLIPI","DT_XMLICM","DT_XMLISS","DT_XMLPIS","DT_XMLCOF","DT_XBFCPAN","DT_XBFCPST","DT_XVFCPAN","DT_XVFCPST","DT_ICMDES","DT_BASNDES","DT_ICMNDES"}
	Local aAliImp	:= {"DT_PICM","DT_ALIQIPI","DT_ALIQICM","DT_ALIQISS","DT_ALIQPIS","DT_ALIQCOF","DT_XALQIPI","DT_XALQICM","DT_XALQISS","DT_XALQPIS","DT_XALQCOF","DT_ALIICST","DT_XALICST","DT_XAFCPAN","DT_XAFCPST","DT_ALQNDES"}
	Local nPosAliImp:= 0
	Local nPosUM	:= 0
	Local nPosSEGUM	:= 0
	Local nPosQtSEG := 0
	Local nTamItem	:= TamSx3("DT_ITEM")[1]
	Local nFrete	:= 0
	Local nSeguro	:= 0
	Local nDespesa	:= 0
	Local nDesconto	:= 0
	Local nValTotal	:= 0
	Local nTotalNf	:= 0
	Local nD		:= 0
	Local nE		:= 0
	Local n			:= oGetDados:nAt
	Local nPrdDup	:= 0
	Local nPosImp	:= 0
	Local lUnidMed  := SDT->(FieldPos("DT_UM")) > 0 .And. SDT->(FieldPos("DT_SEGUM")) > 0 .And. SDT->(FieldPos("DT_QTSEGUM")) > 0
	Local cPrdSegUM := ""
	Local cSegUM	:= ""

	Default lLastIt  := .F.
	Default nPosicao := 1
	Default lNewLine := .T.

	If lUnidMed
		nPosUM		:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_UM"})
		nPosSEGUM	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_SEGUM"})
		nPosQtSEG	:= aScan(aHeader,{|x| AllTrim(x[2]) == "DT_QTSEGUM"})
	Endif

	//Posiciona corretamente a variavel N de
	//acordo com os dados do array aColsBkp.
	If lLastIt
		If ValType(nMultPc)=='N' .And. nMultPc==2
			n:= nPosicao
		Elseif ValType(nMultPc)=='N' .And. nMultPc==1
			n := Iif(nMultPc==1,n,Iif(nMultPc==2 .And. n <> Val(cItem),Val(cItem),n))

			n := aScan(aColsBkp,{|x| AllTrim(x[nPosCod]) == AllTrim(SC7->C7_PRODUTO) .And. AllTrim(x[nPosItem]) == StrZero(n,nTamItem)})
		EndIf
	Else
		For nD := 1 To Len(aColsBkp)
			If AllTrim(aColsBkp[nD,nPosCod]) == AllTrim(SC7->C7_PRODUTO)
				nPrdDup++
			EndIf
		Next nD

		If nPrdDup > 1
			n := Iif(nMultPc==1,n,Iif(nMultPc==2 .And. n <> Val(cItem),Val(cItem),n))
			n := aScan(aColsBkp,{|x| AllTrim(x[nPosCod]) == AllTrim(SC7->C7_PRODUTO) .And. AllTrim(x[nPosItem]) == StrZero(n,nTamItem)})
		Else
			n := aScan(aColsBkp,{|x| AllTrim(x[nPosCod]) == AllTrim(SC7->C7_PRODUTO)})
		Endif
	EndIf

	//Protecao para variavel N
	If n <= 0
		n := oGetDados:nAt
	Endif

	If lNewLine
		//Cria aCols recebendo a quantidade dos pedidos
		aadd(aCols,Array(Len(aHeader)+1))
		For nD := 1 to Len(aHeader)
			If IsHeadRec(aHeader[nD][2])
				aCols[Len(aCols)][nD] := 0
			ElseIf IsHeadAlias(aHeader[nD][2])
				aCols[Len(aCols)][nD] := "SDT"
			ElseIf Trim(aHeader[nD][2]) == "DT_ITEM"
				aCols[Len(aCols)][nD] 	:= IIF(cItem<>Nil,cItem,StrZero(1,Len(SDT->DT_ITEM)))
			Else
				aCols[Len(aCols)][nD] := CriaVar(aHeader[nD][2], (aHeader[nD][10] <> "V") )
			EndIf
			aCols[Len(aCols)][Len(aHeader)+1] := .F.
		Next nD

		nItem := Len(aCols)
	Else
		nItem := nPosicao
	EndIf

	//Apura valor das despesas acessorias para ratear entre os itens
	If nMultPC == 1		// Vinculo por item, retorna o valor somente do item
		nFrete		:= aColsBkp[N][nPosFrete]
		nSeguro		:= aColsBkp[N][nPosSegur]
		nDespesa	:= aColsBkp[N][nPosDesp]
		nDesconto	:= aColsBkp[N][nPosDesc]
		nTotalNf	:= aColsBkp[N][nPosTot]
	ElseIf nMultPC == 2	// Vinculo por documento, retorna o valor total
		For nD := 1 To Len(aColsBkp)
			nFrete		+= aColsBkp[nD][nPosFrete]
			nSeguro		+= aColsBkp[nD][nPosSegur]
			nDespesa	+= aColsBkp[nD][nPosDesp]
			nDesconto	+= aColsBkp[nD][nPosDesc]
		Next nD
		nTotalNf  := SDS->DS_VALMERC
	EndIf

	//Calculo do valor total
	nValTotal := NoRound((aColsBkp[N][nPosValor]*nSldPed),TamSX3("DT_TOTAL")[2])

	//Atualiza o acols com base no pedido de compras
	For nE := 1 To Len(aHeader)
		nPosImp := aScan(aCpoImp,{|x| AllTrim(x) == Trim(aHeader[nE,2])})
		If nPosImp > 0
			nPosImp := nE
		Endif

		nPosAliImp := aScan(aAliImp,{|x| AllTrim(x) == Trim(aHeader[nE,2])})
		If nPosAliImp > 0
			nPosAliImp := nE
		Endif

		Do Case
			Case Trim(aHeader[nE,2]) == "DT_COD"
				cPrdSegUM := If(lLastIt,aColsBkp[n][nPosCod],SC7->C7_PRODUTO)
				aCols[nItem,nE] := cPrdSegUM
			Case Trim(aHeader[nE,2]) == "DT_DESC"
				aCols[nItem,nE] := If(lLastIt,Posicione("SB1",1,xFilial("SB1")+aColsBkp[n][nPosCod],"B1_DESC"),SC7->C7_DESCRI)
			Case Trim(aHeader[nE,2]) == "DT_PRODFOR"
				aCols[nItem,nE] := aColsBkp[n][nPosProdF]
			Case Trim(aHeader[nE,2]) == "DT_DESCFOR"
				aCols[nItem,nE] := aColsBkp[n][nPosDescF]
			Case Trim(aHeader[nE,2]) == "DT_SERIE"
				aCols[nItem,nE] := aColsBkp[n][nPosSerie]
			Case Trim(aHeader[nE,2]) == "DT_QUANT"
				aCols[nItem,nE] := nSldPed
			Case Trim(aHeader[nE,2]) == "DT_VUNIT"
				aCols[nItem,nE] := aColsBkp[n][nPosValor]
			Case Trim(aHeader[nE,2]) == "DT_TOTAL"
				aCols[nItem,nE] := nValTotal
			Case Trim(aHeader[nE,2]) == "DT_PEDIDO"
				aCols[nItem,nE] := If(lLastIt,CriaVar("DT_PEDIDO",.F.),SC7->C7_NUM)
			Case Trim(aHeader[nE,2]) == "DT_ITEMPC"
				aCols[nItem,nE] := If(lLastIt,CriaVar("DT_ITEMPC",.F.),SC7->C7_ITEM)
			Case Trim(aHeader[nE,2]) == "DT_VALFRE"
				aCols[nItem,nE] := (nFrete / nTotalNf) * nValTotal
			Case Trim(aHeader[nE,2]) == "DT_SEGURO"
				aCols[nItem,nE] := (nSeguro / nTotalNf) * nValTotal
			Case Trim(aHeader[nE,2]) == "DT_DESPESA"
				aCols[nItem,nE] := (nDespesa / nTotalNf) * nValTotal
			Case Trim(aHeader[nE,2]) == "DT_VALDESC"
				aCols[nItem,nE] := (nDesconto / nTotalNf) * nValTotal
			Case Trim(aHeader[nE,2]) == "DT_FCICOD"
				aCols[nItem,nE] := aColsBkp[n][nPosFCI]
			Case nPosImp > 0
				aCols[nItem,nE] := (aColsBkp[n][nPosImp]*nSldPed)/aColsBkp[n][nPosQtde]
			Case nPosAliImp > 0
				aCols[nItem,nE] := aColsBkp[n][nPosAliImp]
			Case lUnidMed
				If Trim(aHeader[nE,2]) == "DT_UM"
					aCols[nItem,nE] := aColsBkp[n][nPosUM]
				Elseif Trim(aHeader[nE,2]) == "DT_SEGUM"
					cSegUM := aColsBkp[n][nPosSEGUM]
					aCols[nItem,nE] := cSegUM
				Elseif Trim(aHeader[nE,2]) == "DT_QTSEGUM" .And. !Empty(cSegUM)
					aCols[nItem,nE] := Iif(COLVLSEGUM(cPrdSegUM,cSegUM),ConvUM(cPrdSegUM,nSldPed,nSldPed,2),0)
				Endif
		EndCase
	Next nE

	oGetDados:aCols := aCols
	oGetDados:oBrowse:Refresh()

	//Restaura posição Variavel N
	n := oGetDados:nAt

	RestArea(aAreaSDS)

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} ComXGetAnt
Retorna backup aCols (Devolução)

@author	TOTVS
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function ComXGetAnt(aColsAnt)

	If SDS->DS_TIPO == "D"		// Nota de Devolução
		aCols := aClone(aColsAnt)
	EndIf

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} ComXItOri
Esta rotina tem como objetivo retornar os itens originais do documento

@author	TOTVS
@since 05/06/12
/*/
//-------------------------------------------------------------------

Function ComXItOri(aColsAnt, lReplace, aDadosOri)

	Local cQuery 	:= ""
	Local cAliasTmp	:= "SDTTMP"
	Local aColsOri 	:= {}
	Local nX 		:= 0
	Local nPPEDIDO	:= GDFieldPos("DT_PEDIDO")
	Local cItem		:= ""

	If Len(aHeader) == 0
		aHeader := COMXHDCO("SDT",,aNoFields)
	Endif

	// Pesquisa pelos itens originais que estejam deletados e marcados com o campo DT_ORIGEM,
	//  pois podem ter sido substituidos na confirmacao do vinculo por multiplos pedidos
	// Caso a operacao de vinculo por multiplos pedidos nao tenha sido concluida e nao encontre registros deletados,
	//  retorna o aColsAnt
	For nX := 1 To Len(aHeader)
		If SDT->(FieldPos(aHeader[nX,2])) > 0
			If Empty(cQuery)
				cQuery := " SELECT DISTINCT " + AllTrim(aHeader[nX,2])
			Else
				cQuery += " , " + AllTrim(aHeader[nX,2])
			Endif
		Endif
	Next nX

	cQuery += " FROM " +RetSqlName("SDT") +" SDT"
	cQuery += " WHERE DT_FILIAL = '" +xFilial("SDT") + "' "
	cQuery += " AND DT_FORNEC = '" +SDS->DS_FORNEC + "' AND DT_LOJA = '" +SDS->DS_LOJA + "'"
	cQuery += " AND DT_DOC = '" +SDS->DS_DOC + "' AND DT_SERIE = '" +SDS->DS_SERIE + "'"
	cQuery += " AND DT_ORIGIN = '1' AND D_E_L_E_T_ = '*' "
	cQuery := ChangeQuery(cQuery)

	dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQuery),cAliasTmp,.T.,.T.)

	// Se nao encontrou itens originais como deletados, retorna array aColsAnt
	(cAliasTmp)->(dbGoTop())
	If (cAliasTmp)->(Eof())
		FOR nX := 1 TO Len(aColsAnt)
			IF !Empty(aColsAnt[nX][nPPEDIDO])
				(cAliasTmp)->(dbCloseArea())
				RETURN .T.
			ENDIF
		NEXT nX

		if lReplace
			aCols := aClone(aColsAnt)
			oGetDados:aCols := aCols
		else
			aDadosOri := aClone(aColsAnt)
		endif
	Else
		While (cAliasTmp)->(!Eof())
			IF !Empty((cAliasTmp)->DT_PEDIDO)
				(cAliasTmp)->(dbCloseArea())
				RETURN .T.
			ENDIF

			If Empty(cItem)
				cItem := (cAliasTmp)->DT_ITEM
			Else
				If cItem == (cAliasTmp)->DT_ITEM
					(cAliasTmp)->(dbSkip())
					Loop
				Else
					cItem := (cAliasTmp)->DT_ITEM
				Endif
			Endif

			// Cria aColsOri para receber os itens originais
			aadd(aColsOri,Array(Len(aHeader)+1))
			For nX := 1 to Len(aHeader)
				If IsHeadRec(aHeader[nX][2])
					aColsOri[Len(aColsOri)][nX] := 0
				ElseIf IsHeadAlias(aHeader[nX][2])
					aColsOri[Len(aColsOri)][nX] := "SDT"
				Else
					If SDT->(FieldPos(aHeader[nX,2])) > 0
						aColsOri[Len(aColsOri)][nX] := &((cAliasTmp)+"->"+aHeader[nX][2])
					Endif
				EndIf
				aColsOri[Len(aColsOri)][Len(aHeader)+1] := .F.
			Next nX
			(cAliasTmp)->(dbSkip())
		EndDo

		If Len(aColsOri) > 0
			if lReplace
				aCols := aClone(aColsOri)
				oGetDados:aCols := aColsOri
			else
				aDadosOri := aClone(aColsOri)
			endif
		EndIf
	EndIf

	(cAliasTmp)->(dbCloseArea())

Return .F.

//-------------------------------------------------------------------
/*/{Protheus.doc} ConvASC()
Função para conversão de caracteres com acento.
@author jose.delmondes
@since 14/07/2014
@version P11.8
@return cStrXML - Xml com caracteres substituidos
/*/
//-------------------------------------------------------------------

Function ConvASC(cStrXML)

	cStrXML := StrTran(cStrXML, CHR(199), CHR(67)) 	//Substitui Ç por C
	cStrXML := StrTran(cStrXML, CHR(231), CHR(99))	//Substitui ç por c
	cStrXML := StrTran(cStrXML, CHR(195), CHR(65))	//Substitui Ã por A
	cStrXML := StrTran(cStrXML, CHR(192), CHR(65))	//Substitui À por A
	cStrXML := StrTran(cStrXML, CHR(193), CHR(65))	//Substitui Á por A
	cStrXML := StrTran(cStrXML, CHR(227), CHR(97))	//Substitui ã por a
	cStrXML := StrTran(cStrXML, CHR(225), CHR(97))	//Substitui á por a
	cStrXML := StrTran(cStrXML, CHR(224), CHR(97))  //Substitui à por a
	cStrXML := StrTran(cStrXML, CHR(201), CHR(69))	//Substitui É por E
	cStrXML := StrTran(cStrXML, CHR(233), CHR(101))	//Substitui é por e
	cStrXML := StrTran(cStrXML, CHR(205), CHR(73))	//Substitui Í por Í
	cStrXML := StrTran(cStrXML, CHR(237), CHR(105))	//Substitui í por í
	cStrXML := StrTran(cStrXML, CHR(211), CHR(79))	//Substitui Ó por O
	cStrXML := StrTran(cStrXML, CHR(213), CHR(79))	//Substitui Õ por O
	cStrXML := StrTran(cStrXML, CHR(245), CHR(111))	//Substitui õ por o
	cStrXML := StrTran(cStrXML, CHR(243), CHR(111))	//Substitui ó por o
	cStrXML := StrTran(cStrXML, CHR(218), CHR(85))	//Substitui Ú por U
	cStrXML := StrTran(cStrXML, CHR(250), CHR(117))	//Substitui ú por u

Return cStrXML

//-------------------------------------------------------------------
/*/{Protheus.doc} COMXCOLNEO
Funcao que estabelece comunicacao com o Client NeoGrid para
realizar a baixa ou remessa de arquivo

@author	Flavio Lopes Rasta
@since 08/08/14
/*/
//-------------------------------------------------------------------

Function COMXCOLNEO(cNumDoc,cXML,cIDErp,cQueue)

	Local lOk		:= .T.
	Local oColab	:= Nil

	If !Empty(cXml)
		oColab := ColaboracaoDocumentos():New()

		oColab:cModelo 		:= "EDI"	// Fixo para DI de Compras
		oColab:cNumero		:= cNumDoc	// Numero do Documento
		oColab:cIdErp 		:= cIdErp	// ID Erp
		oColab:cXml			:= cXml		// XML
		oColab:cTipoMov		:= '1'		// Tipo de Movimento 1-Saida / 2-Recebimento
		oColab:cQueue		:= cQueue		// Codigo Queue (170 - Emissão de NF-e)

		If oColab:cCdStatDoc <> "1" 		// 1 - 'Enviado'
			lOk := oColab:transmitir()
		Else
			lOk := .F.
			cErro := STR0180+CRLF+CRLF 	//"As notas abaixo foram recusadas, verifique a rotina 'Monitor' para saber os motivos."
		EndIf
	EndIf

Return lOk

//-------------------------------------------------------------------
/*/{Protheus.doc}InscEstSM0
Valida filial pela inscrição estadual

@author Flavio Lopes Rasta
@since 24/02/2015
@version P12
/*/
//-------------------------------------------------------------------
Function InscEstSM0(cCgc,cInscEst,lInscDup)

	Local aRetEmp	:= {}
	Local aAreaSM0	:= SM0->(GetArea())
	Local nQtdINSC	:= 0
	Local lImpNFS	:= FwIsInCallStack("ImpXML_NFs")

	Default lInscDup := .F.

	DbSelectArea('SM0')
	SM0->(DbGoTop())
	While !SM0->(Eof())
		If AllTrim(SM0->M0_CGC) == cCgc .And. Iif(!lImpNFS,A140INSC(cInscEst,SM0->M0_INSC),.T.)
			aAdd(aRetEmp,SM0->M0_CODIGO)
			aAdd(aRetEmp,SM0->M0_CODFIL)
			nQtdINSC++
		EndIf
		SM0->(DbSkip())
	EndDo

	// Caso tenha mais de um registro com mesmo CNPJ e Insc.Estadual nao sera possivel determinar a filial de importacao
	If nQtdINSC > 1
		aRetEmp  := {}
		lInscDup := .T.
	EndIf

	RestArea(aAreaSM0)

Return aRetEmp

//-------------------------------------------------------------------
/*/{Protheus.doc} ColZerImp
Zera impostos ao limpar campo DT_TES

@author rodrigo.mpontes
@since 12/01/2021
@version P12
/*/
//-------------------------------------------------------------------

Function ColZerImp()

	Local nLin	:= oGetDados:nAt

	oGetDados:aCols[nLin][GdFieldPos("DT_TESIPI")] 	:= 0
	oGetDados:aCols[nLin][GdFieldPos("DT_TESICM")]  := 0
	oGetDados:aCols[nLin][GdFieldPos("DT_TESISS")]  := 0
	oGetDados:aCols[nLin][GdFieldPos("DT_TESPIS")]  := 0
	oGetDados:aCols[nLin][GdFieldPos("DT_TESCOF")]  := 0
	oGetDados:aCols[nLin][GdFieldPos("DT_TESICST")]	:= 0
	oGetDados:aCols[nLin][GdFieldPos("DT_ALIQIPI")] := 0
	oGetDados:aCols[nLin][GdFieldPos("DT_ALIQICM")] := 0
	oGetDados:aCols[nLin][GdFieldPos("DT_ALIQISS")] := 0
	oGetDados:aCols[nLin][GdFieldPos("DT_ALIQPIS")] := 0
	oGetDados:aCols[nLin][GdFieldPos("DT_ALIQCOF")] := 0
	oGetDados:aCols[nLin][GdFieldPos("DT_ALIICST")]	:= 0

	ColAtuLeg(aHeader,oGetDados:aCols)

	oGetDados:oBrowse:Refresh()
	ColImpRefresh()

Return .T.

//-------------------------------------------------------------------
/*/{Protheus.doc}ColAtuImp
Valid do campo DT_TES.
Atualiza impostos de acordo com a TES

@author Flavio Lopes Rasta
@since 30/03/2015
@version P12
/*/
//-------------------------------------------------------------------

Function ColAtuImp(cTes,nLine,lImp,nRecDT)

	Local aAreaSDS   := SDS->(GetArea())
	Local aAreaSDT   := SDT->(GetArea())
	Local aCabec     := MontaSF1(,,.T.)
	Local aItem      := {}
	Local nPosTpNF   := aScan(aCabec,{|x| AllTrim(x[1]) == "F1_TIPO"})
	Local nPosCPg    := aScan(aCabec,{|x| AllTrim(x[1]) == "F1_COND"})
	Local nPosTpCp   := aScan(aCabec,{|x| AllTrim(x[1]) == "F1_TPCOMPL"})
	Local nPosEsp    := aScan(aCabec,{|x| AllTrim(x[1]) == "F1_ESPECIE"})
	Local nPosForn   := aScan(aCabec,{|x| AllTrim(x[1]) == "F1_FORNECE"})
	Local nPosLoja   := aScan(aCabec,{|x| AllTrim(x[1]) == "F1_LOJA"})
	Local nPosAnt    := 0
	Local lGerDupl   := .F.
	Local lRet       := .T.
	Local lConFrete	 := .F.

	Default cTes     := ""
	Default nLine    := 0
	Default lImp	 := .F.
	Default nRecDT	 := 0

	Private aImpVal  := {}

	If !lImp
		nPosAnt := oGetDados:nAt
		If Empty(cTes)
			cTes := M->DT_TES
		EndIf

		If nLine > 0
			n := nLine
		EndIf
	Else
		SDT->(DbGoto(nRecDT))
	Endif

	aAdd(aItem,{})
	aAdd(aTail(aItem),{"D1_ITEM",   IIf(!lImp,aCols[1][GdFieldPos("DT_ITEM")],StrZero(1,TamSX3("DT_ITEM")[1])) , 	 NIL})
	aAdd(aTail(aItem),{"D1_COD",    IIf(!lImp,aCols[n][GdFieldPos("DT_COD")],SDT->DT_COD),	 NIL})

	If !(SDS->DS_TIPO $ "CT")
		aAdd(aTail(aItem),{"D1_QUANT",  IIf(!lImp,aCols[n][GdFieldPos("DT_QUANT")],SDT->DT_QUANT), 	 NIL})
	Endif

	aAdd(aTail(aItem),{"D1_VUNIT",  IIf(!lImp,aCols[n][GdFieldPos("DT_VUNIT")],SDT->DT_VUNIT), 	 NIL})

	If SDS->DS_TIPO $ "CT"
		aAdd(aTail(aItem),{"D1_TOTAL",IIf(!lImp,aCols[n][GdFieldPos("DT_VUNIT")],SDT->DT_TOTAL),NIL})
	Else
		aAdd(aTail(aItem),{"D1_TOTAL",IIf(!lImp,Round(aCols[n][GdFieldPos("DT_VUNIT")] * aCols[n][GdFieldPos("DT_QUANT")],TamSX3("D1_TOTAL")[2]),SDT->DT_TOTAL),NIL})
	EndIf

	aAdd(aTail(aItem),{"D1_VALFRE",	IIf(!lImp,aCols[n][GdFieldPos("DT_VALFRE")],SDT->DT_VALFRE),	 NIL})
	aAdd(aTail(aItem),{"D1_SEGURO",	IIf(!lImp,aCols[n][GdFieldPos("DT_SEGURO")],SDT->DT_SEGURO),	 NIL})
	aAdd(aTail(aItem),{"D1_DESPESA",IIf(!lImp,aCols[n][GdFieldPos("DT_DESPESA")],SDT->DT_DESPESA), NIL})
	aAdd(aTail(aItem),{"D1_VALDESC",IIf(!lImp,aCols[n][GdFieldPos("DT_VALDESC")],SDT->DT_VALDESC), NIL})
	aAdd(aTail(aItem),{"D1_TES"	   ,IIf(!lImp,cTes,SDT->DT_TES),  NIL})

	If aCabec[nPosTpNF,2] $ "D|C" //Devolução ou complemento
		aAdd(aTail(aItem),{"D1_NFORI"  ,	IIf(!lImp .And. GdFieldPos("DT_NFORI") > 0 ,aCols[n][GdFieldPos("DT_NFORI")],SDT->DT_NFORI),	 NIL})
		aAdd(aTail(aItem),{"D1_SERIORI",	IIf(!lImp .And. GdFieldPos("DT_SERIORI") > 0,aCols[n][GdFieldPos("DT_SERIORI")],SDT->DT_SERIORI),	 NIL})
		aAdd(aTail(aItem),{"D1_FORNECE",	IIf(!lImp,aCabec[nPosForn,2],SDT->DT_FORNEC),	 NIL})
		aAdd(aTail(aItem),{"D1_LOJA"   ,	IIf(!lImp,aCabec[nPosLoja,2],SDT->DT_LOJA),	 NIL})
	Endif

	If !lImp
		aCabec 	:= COMCONDPG(aCabec,aItem,1)
		nPosCPg := aScan(aCabec,{|x| AllTrim(x[1]) == "F1_COND"})

		//-- Adiciona condicao de pagamento ao cabecalho
		SF4->(dbSetOrder(1))
		If SF4->(dbSeek(xFilial("SF4")+cTes)) .And. SF4->F4_DUPLIC == "S"
			lGerDupl := .T.
		EndIf

		If lGerDupl .And. nPosCPg == 0
			lConFrete	:= (nPosTpCp > 0 .And. aCabec[nPosTpNF,2] == "C" .And. aCabec[nPosTpCp,2] == "3") .Or. (nPosEsp > 0 .And. aCabec[nPosTpNF,2] == "N" .And. (AllTrim(aCabec[nPosEsp,2]) == "CTE" .Or. AllTrim(aCabec[nPosEsp,2]) == "CTEOS"))
			lRet		:= .F.
		Endif
	Endif

	If lRet
		lMsErroAuto    := .F.
		lAutoErrNoFile := .T.

		MSExecAuto({|x,y,z,k| MATA103(x,y,z,,,,,,k)},aCabec,aItem,3,.F.)

		If !lMsErroAuto
			If nLine > 0
				n := nLine
			EndIf
			If Len(aImpVal) > 0
				If !lImp
					oGetDados:aCols[n][GdFieldPos("DT_TESIPI")] 	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALIPI"})][3]
					oGetDados:aCols[n][GdFieldPos("DT_TESICM")]  	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALICM"})][3]
					oGetDados:aCols[n][GdFieldPos("DT_TESISS")]  	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALISS"})][3]
					oGetDados:aCols[n][GdFieldPos("DT_TESPIS")]  	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALIMP6"})][3]
					oGetDados:aCols[n][GdFieldPos("DT_TESCOF")]  	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALIMP5"})][3]
					oGetDados:aCols[n][GdFieldPos("DT_TESICST")]	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_ICMSRET"})][3]
					oGetDados:aCols[n][GdFieldPos("DT_ALIQIPI")] 	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2]=="D1_IPI"})][3]
					oGetDados:aCols[n][GdFieldPos("DT_ALIQICM")] 	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2]=="D1_PICM"})][3]
					oGetDados:aCols[n][GdFieldPos("DT_ALIQISS")] 	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2]=="D1_ALIQISS"})][3]
					oGetDados:aCols[n][GdFieldPos("DT_ALIQPIS")] 	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2]=="D1_ALQIMP6"})][3]
					oGetDados:aCols[n][GdFieldPos("DT_ALIQCOF")] 	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2]=="D1_ALQIMP5"})][3]
					oGetDados:aCols[n][GdFieldPos("DT_ALIICST")]	:= IIf((oGetDados:aCols[n][GdFieldPos("DT_TESICST")]) > 0,aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2]=="D1_ALIQSOL"})][3],0)
				Else
					SDT->(DbGoto(nRecDT))
					If RecLock("SDT",.F.)
						SDT->DT_TESIPI 	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALIPI"})][3]
						SDT->DT_TESICM 	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALICM"})][3]
						SDT->DT_TESISS 	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALISS"})][3]
						SDT->DT_TESPIS 	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALIMP6"})][3]
						SDT->DT_TESCOF 	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_VALIMP5"})][3]
						SDT->DT_TESICST	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_ICMSRET"})][3]
						SDT->DT_ALIQIPI	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_IPI"})][3]
						SDT->DT_ALIQICM	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_PICM"})][3]
						SDT->DT_ALIQISS	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_ALIQISS"})][3]
						SDT->DT_ALIQPIS	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_ALQIMP6"})][3]
						SDT->DT_ALIQCOF	:= aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_ALQIMP5"})][3]
						SDT->DT_ALIICST	:= IIf(SDT->DT_TESICST > 0,aImpVal[1][2][aScan(aImpVal[1][2],{|x| x[2] == "D1_ALIQSOL"})][3],0)
						SDT->(MsUnlock())
					Endif
				Endif
			EndIf
			If !lImp
				oGetDados:oBrowse:Refresh()
				ColImpRefresh()
			Endif
		Else
			lRet := .F.
		EndIf

	Else
		If !lConFrete
			Aviso(STR0004,STR0140,{STR0077}) //-- Atencao # A TES gera Duplicata e nao foi encontrada condicao de pagamento no cadastro do fornecedor/cliente.
		Else
			Aviso(STR0004,STR0194,{STR0077}) //-- Atencao # A TES gera Duplicata e nao foi encontrada condicao de pagamento no parametro MV_XMLCPCT.
		Endif
	EndIf
	RollBackSX8()

	If !lImp
		n := nPosAnt
	Endif

	RestArea(aAreaSDT)
	RestArea(aAreaSDS)

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc}ColVerTes
Verifica se todos os itens possuem TES

@author Flavio Lopes Rasta
@since 22/04/2015
@version P12
/*/
//-------------------------------------------------------------------

Function ColVerTes(aItens)

	Local nPosTes	:= 0
	Local nX		:= 1
	Local lRet		:= .T.

	For nX:=1 To Len(aItens)
		nPosTes := aScan(aItens[nX], {|x| x[1]=="D1_TES"})
		If !(nPosTes > 0) .Or. Empty(aItens[nX][nPosTes][2])
			lRet := .F.
			Exit
		Endif
	Next nX

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc}ColVerDev
Verifica se todos os itens possuem NF de Origem para NF de Devolução

@author Rodrigo M.Pontes
@since 22/04/2019
@version P12
/*/
//-------------------------------------------------------------------

Function ColVerDev(aItens,aCabec,lClass)
	Local aArea		:= GetArea()
	Local nPosNFOri	:= 0
	Local nPosSEOri	:= 0
	Local nPosITOri	:= 0
	Local nX		:= 1
	Local lRet		:= .T.
	Local nPosTipo	:= aScan(aCabec, {|x| x[1]=="F1_TIPO"})
	Local nPosForn	:= aScan(aCabec, {|x| x[1]=="F1_FORNECE"})
	Local nPosLoja	:= aScan(aCabec, {|x| x[1]=="F1_LOJA"})
	Local nPosCod	:= 0
	Local cQry		:= ""
	Local cAliasDev	:= ""
	Local cDocOri	:= ""
	Local cDocDev	:= ""
	Local nSldQtdDev:= 0
	Local nPosQtd	:= 0
	Local nQtdDev	:= 0

	If nPosTipo > 0 .And. aCabec[nPosTipo,2] == "D" .And. Len(aItens) > 0

		For nX:=1 To Len(aItens)

			nPosNFOri := aScan(aItens[nx], {|x| x[1]=="D1_NFORI"})
			nPosSEOri := aScan(aItens[nx], {|x| x[1]=="D1_SERIORI"})
			nPosITOri := aScan(aItens[nx], {|x| x[1]=="D1_ITEMORI"})
			nPosCod	  := aScan(aItens[nx], {|x| x[1]=="D1_COD"})
			nPosQtd	  := aScan(aItens[nx], {|x| x[1]=="D1_QUANT"})

			If nPosNFOri > 0 .And. nPosSEOri > 0 .And. nPosITOri > 0

				cAliasDev := GetNextAlias()

				cQry := " SELECT DISTINCT D1_DOC, D1_SERIE, D1_ITEM "
				cQry += " FROM " + RetSqlName("SD1")
				cQry += " WHERE D1_NFORI = '" + aItens[nX][nPosNFOri][2] + "'"
				cQry += " AND D1_SERIORI = '" + aItens[nX][nPosSEOri][2] + "'"
				cQry += " AND D1_ITEMORI = '" + aItens[nX][nPosITOri][2] + "'"
				cQry += " AND D1_FORNECE = '" + aCabec[nPosForn,2] + "'"
				cQry += " AND D1_LOJA    = '" + aCabec[nPosLoja,2] + "'"
				cQry += " AND D_E_L_E_T_ = ' '"
				cQry := ChangeQuery(cQry)

				dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQry),cAliasDev,.T.,.T.)

				If (cAliasDev)->(!EOF())
					DbSelectArea("SD2")
					SD2->(DbSetOrder(3))
					If MsSeek(xFilial("SD2")+aItens[nX][nPosNFOri][2]+aItens[nX][nPosSEOri][2]+aCabec[nPosForn,2]+aCabec[nPosLoja,2]+aItens[nX][nPosCod][2]+aItens[nX][nPosITOri][2])
						nSldQtdDev := SD2->D2_QUANT-SD2->D2_QTDEDEV
					Endif

					nQtdDev := aItens[nX][nPosQtd][2]

					If nSldQtdDev == 0
						lRet := .F.
						cDocOri	:= aItens[nX][nPosNFOri][2] + "|" + aItens[nX][nPosSEOri][2] + "|" + aItens[nX][nPosITOri][2]
						cDocDev	:= (cAliasDev)->D1_DOC + "|" + (cAliasDev)->D1_SERIE + "|" + (cAliasDev)->D1_ITEM
						RecLock("SDS",.F.)
						Replace SDS->DS_DOCLOG With STR0196 + cDocOri + STR0197 + cDocDev //"Documento Origem: " ##" ja foi devolvido atraves do documento: "
						Replace SDS->DS_STATUS With 'E'
						SDS->(MsUnlock())
						Exit
					Else
						//Se saldo for diferente da quantidade do documento
						//Gera pre-nota para corrigir saldo ao classificar documento
						If nSldQtdDev <> nQtdDev
							lRet := .F.
							lClass := .F.
						Endif
					Endif
				Endif

				(cAliasDev)->(DbCloseArea())
			Endif
		Next nX
	Endif

	RestArea(aArea)

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc}ColConDHJ
Consulta OP pelo CFOP
@param  cCfop - CFOP para realizar busca
@param  cTypeOper - Tipo de operação Entrada("E" Padrão) ou Saida("S")
@author Flavio Lopes Rasta
@since 22/04/2015
@version P12
/*/
//-------------------------------------------------------------------
Function ColConDHJ(cCfop,cTypeOper)

	Local cOp 	   := ""
	Local lTPOPSA  := DHJ->(FieldPos( "DHJ_TPOPSA" )) > 0

	Default cTypeOper := "E"

	If cPaisLoc == "BRA"
		DHJ->(DbSetOrder(2))
		If DHJ->(DbSeek(xFilial("DHJ")+cCfop))
			If AllTrim(cTypeOper) == "S"
				If lTPOPSA
					cOp := AllTrim(DHJ->DHJ_TPOPSA)
				EndIf
			Else
				cOp := AllTrim(DHJ->DHJ_TPOP)
			EndIf
		EndIf
	EndIf

Return cOp

//-------------------------------------------------------------------
/*/{Protheus.doc}COLFINSDS
Verifica se documento existe na base de dados

@author Rodrigo Machado Pontes
@since 22/10/2015
@version P11
/*/
//-------------------------------------------------------------------

Function COLFINSDS(nOrdem,cColabDoc,nConhecto)

	Local lRet		:= .T.
	Local cQry		:= ""

	Default nConhecto := 0

	If Select("TMPSDS") > 0
		TMPSDS->(DbCloseArea())
	Endif

	cQry	:= " SELECT DS_DOC"
	cQry	+= " FROM " + RetSqlName("SDS")
	If nOrdem == 1 //Doc + Serie + Forn + Loja
		cQry	+= " WHERE DS_DOC||DS_SERIE||DS_FORNEC||DS_LOJA  = '" + cColabDoc + "'"
	Elseif nOrdem == 2 //Chave NF
		cQry	+= " WHERE DS_CHAVENF = '" + cColabDoc + "'"
	Endif

	If nConhecto == 1 //Busca por documento do tipo Transporte (CTE)
		cQry	+= " AND DS_TIPO = 'T'"
	EndIf

	cQry	+= " AND D_E_L_E_T_ = ' '"

	cQry := ChangeQuery(cQry)

	dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQry),"TMPSDS",.T.,.T.)

	DbSelectArea("TMPSDS")
	TMPSDS->(dbGoTop())
	If !TMPSDS->(Eof())
		lRet := .F.
	EndIf

	TMPSDS->(dbCloseArea())

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} COLLegIt()
Exibe uma janela contendo a legenda da classificação no item do
documento no Totvs Colaboração

@author Flavio Lopes Rasta
@since 20/06/2016
@version 11
/*/
//-------------------------------------------------------------------
Function COLLegIt()

	Local aCores     := {}

	aAdd(aCores,{"BR_BRANCO","Sem Classificação"})
	aAdd(aCores,{"BR_VERDE","Sem Divergência de Impostos"})
	aAdd(aCores,{"BR_VERMELHO","Com Divergência de Impostos"})

	BrwLegenda("Monitor","Legenda da Classificação",aCores)

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} ColAtuLeg()

@author Flavio Lopes Rasta
@since 20/06/2016
@version 11
/*/
//-------------------------------------------------------------------

Function ColAtuLeg(aHeader,aCols)

	Local nItem		:= Len(aCols)
	Local nX		:= 1
	Local aImpostos	:= {}
	Local cLegenda	:= "BR_VERDE"
	Local aColsImp	:= {}
	Local nValorTes := 0
	Local nAliqTes	:= 0
	Local lMVDiviZer:= SuperGetMv("MV_DIVIZER",.F.,.F.)
	Local lCOLDVIMP := ExistBlock("COLDVIMP")

	aAdd(aImpostos,{"IPI"		,"DT_TESIPI"	,"DT_XMLIPI"	,"DT_ALIQIPI"	,"DT_XALQIPI"})
	aAdd(aImpostos,{"ICMS"		,"DT_TESICM"	,"DT_XMLICM"	,"DT_ALIQICM"	,"DT_XALQICM"})
	aAdd(aImpostos,{"ISS"		,"DT_TESISS"	,"DT_XMLISS"	,"DT_ALIQISS"	,"DT_XALQISS"})
	aAdd(aImpostos,{"PIS"		,"DT_TESPIS"	,"DT_XMLPIS" 	,"DT_ALIQPIS"	,"DT_XALQPIS"})
	aAdd(aImpostos,{"COFINS"	,"DT_TESCOF"	,"DT_XMLCOF"	,"DT_ALIQCOF"	,"DT_XALQCOF"})
	aAdd(aImpostos,{"ICMS ST"	,"DT_TESICST"	,"DT_XMLICST"	,"DT_ALIICST"	,"DT_XALICST"})

	If lCOLDVIMP
		For nX:=1 To Len(aImpostos)
			nValorTes := aCols[nItem,GDFieldPos(aImpostos[nX][2])]
			nAliqTes  := If(lMVDiviZer .And. (nValorTes == 0),0,aCols[nItem,GDFieldPos(aImpostos[nX][4])])

			aAdd(aColsImp,{})
			aAdd(aTail(aColsImp),If(nValorTes == aCols[nItem,GDFieldPos(aImpostos[nX][3])] .And. nAliqTes == aCols[nItem,GDFieldPos(aImpostos[nX][5])],oGreen,oRed))
			aAdd(aTail(aColsImp),aImpostos[nX][1])
			aAdd(aTail(aColsImp),nValorTes)
			aAdd(aTail(aColsImp),aCols[nItem,GDFieldPos(aImpostos[nX][3])])
			aAdd(aTail(aColsImp),nAliqTes)
			aAdd(aTail(aColsImp),aCols[nItem,GDFieldPos(aImpostos[nX][5])])
			aAdd(aTail(aColsImp),.F.)
		Next nX

		aColsImp := ExecBlock("COLDVIMP",.F.,.F.,{"COMXCOL",aColsImp})

		If aScan(aColsImp,{|x| x[1]:cName == "BR_VERMELHO"}) > 0
			cLegenda := "BR_VERMELHO"
		Endif

	Else
		For nX:=1 To Len(aImpostos)
			nValorTes	:= aCols[nItem,GDFieldPos(aImpostos[nX][2])]
			nAliqTes	:= If(lMVDiviZer .And. (nValorTes == 0),0,aCols[nItem,GDFieldPos(aImpostos[nX][4])])
			If nValorTes <> aCols[nItem,GDFieldPos(aImpostos[nX][3])] .Or. nAliqTes <> aCols[nItem,GDFieldPos(aImpostos[nX][5])]
				cLegenda	:= "BR_VERMELHO"
				Exit
			Endif
		Next nX
	Endif

	aCols[nItem,GDFieldPos("DT_LEGENDA")] := cLegenda

Return .T.

//-------------------------------------------------------------------
/*/{Protheus.doc} MarcaFilial
TOTVS COLABORAÇAO 2.0
Função para marcar somente uma filial de processamento do documento.

@param	aFiliais, array , Filiais carregados.
@param	nLinha  , num   , Linha selecionada.
@param	oBrowse , object, Objeto do browse.

@author	Geovani.Figueira
@since		05/12/2017
@version	12.1.17
/*/
//-------------------------------------------------------------------

Static Function MarcaFilial(aFiliais,nLinha,oBrowse)
	Local nX := 0

	If !Empty(aFiliais)
		For nX := 1 To Len(aFiliais)
			IIF(nX == nLinha,aFiliais[nLinha,1] := !aFiliais[nLinha,1],aFiliais[nX,1] := .F. )
		Next nX

		oBrowse:Refresh()
	EndIf

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} COLXCQ
TOTVS COLABORAÇAO 2.0 x Controle CQ
Função para buscar numeração de CQ para o conhecimento de frete
gerado via totvs colaboração

@author	Rodrigo M Pontes
@since		05/12/2017
@version	12.1.17
/*/
//-------------------------------------------------------------------

Function COLXCQ(cDocComp,cSerComp,cForComp,cLojComp,cProd,cItemComp,cDocOri,cSerOri,cItemOri)

	Local aArea		:= GetArea()
	Local aRet 		:= {.F.,"","","","",0}
	Local cDTChvAux := ""

	DbSelectArea("SDS")
	SDS->(DbSetOrder(1))

	DbSelectArea("SDT")
	SDT->(DbSetOrder(1))

	cDTChvAux := Space(GetSX3Cache("DT_CHVNFO","X3_TAMANHO"))

	DbSelectArea("SF1")

	DbSelectArea("SD1")

	//Verifica se é originado pelo totvs colaboração
	If SDS->(DbSeek(xFilial("SDS") + cDocComp + cSerComp + cForComp + cLojComp))
		//Busca Chave na NF de origem
		BeginSql alias 'DTIT'
			SELECT
				DT.DT_CHVNFO
			FROM
				%table:SDT% DT
			WHERE
				DT.DT_FILIAL = %xfilial:SDT%
				AND DT.DT_DOC = %exp:cDocComp%
				AND DT.DT_SERIE = %exp:cSerComp%
				AND DT.DT_FORNEC = %exp:cForComp%
				AND DT.DT_LOJA = %exp:cLojComp%
				AND DT.DT_NFORI = %exp:cDocOri%
				AND DT.DT_SERIORI = %exp:cSerOri%
				AND DT.DT_ITEMORI = %exp:cItemOri%
				AND DT.DT_CHVNFO <> %exp:cDTChvAux%
				AND DT.%notDel%
			ORDER BY
				%Order:SDT%
		EndSql

		DbSelectArea("DTIT")
		If DTIT->(!EOF())
			//Posiciona na NF de origem
			SF1->(DbSetOrder(8))
			If !Empty(DTIT->DT_CHVNFO) .And. SF1->(DbSeek(xFilial("SF1") + DTIT->DT_CHVNFO))
				aRet[6] := SF1->(Recno()) //Recno da NF de origem
				SD1->(DbSetOrder(1))
				If SD1->(DbSeek(xFilial("SD1") + SF1->F1_DOC + SF1->F1_SERIE + SF1->F1_FORNECE + SF1->F1_LOJA + cProd + cItemOri))
					//Pega numero CQ
					aRet[2] := SD1->D1_NUMCQ
				Endif
				aRet[1] := .T.
				aRet[3] := ""
				aRet[4] := ""
				aRet[5] := ""
			Endif
		Endif

		DTIT->(DbCloseArea())
	Endif

	RestArea(aArea)

Return aRet

//-------------------------------------------------------------------
/*/{Protheus.doc} COMXIMPVLD
Função para validar aliquotas de icms/pis/cofins

@author	Rodrigo M Pontes
@since		05/12/2017
@version	12.1.17
/*/
//-------------------------------------------------------------------

Function COMXIMPVLD(aVldImp)

	Local nI	:= 1
	Local cVld	:= ""
	Local lRet	:= .F.

	For nI := 1 To Len(aVldImp)
		cVld := AllTrim(Str(aVldImp[nI,1])) + aVldImp[nI,2]

		lRet := &(cVld)

		If lRet
			Exit
		Endif
	Next nI

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} ComxUsrCpo
Função para validar existência de campos de usuário.

@author	Romulo Batista
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------
Function ComxUsrCpo(aCpsAlt)

	Local nX		:= 0
	Local aStru		:= FWFormStruct(3,"SDT")[1]
	Local aUsrCpo	:= {}

	Default aCpsAlt	:= {}

	For nX := 1 To Len(aStru)
		If GetSx3Cache(aStru[nX][3],"X3_PROPRI") == "U" .And. X3Uso(GetSx3Cache(aStru[nX][3],'X3_USADO'))
			Aadd(aCpsAlt,aStru[nX][3])
			Aadd(aUsrCpo,aStru[nX][3])
		EndIf
	Next nX

Return aUsrCpo

//-------------------------------------------------------------------
/*/{Protheus.doc} COLERPERR
Função para retornar todos os codigos de erro do Totvs Colaboração
ou Importador XML

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Function COLERPERR()

	Local aRet	:= {"COM001","COM002","COM003","COM004","COM005","COM006","COM007","COM008","COM009","COM010",;
		"COM011","COM012","COM013","COM014","COM015","COM016","COM017","COM018","COM019","COM020",;
		"COM021","COM022","COM023","COM024","COM025","COM026","COM027","COM028","COM029","COM030",;
		"COM031","COM032","COM033","COM034","COM035","COM036","COM037","COM038","COM039","COM040",;
		"COM041","COM042","COM043","COM044","COM045","COM046","COM047","COM048","COM049","COM050",;
		"COM051","COM052","COM053"}

Return aRet

//-------------------------------------------------------------------
/*/{Protheus.doc} COLFILEDI
Consulta especifica para codigos edi

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Function COLFILEDI(nOpc)

	Local lOk	:= .T.
	Local lTela	:= .T.
	Local aEdi	:= {{.F.,"109","NFe"},{.F.,"214","CTe"},{.F.,"273","CTeOS"},{.F.,"319","NFs"}}
	Local cRet	:= ""
	Local nI	:= 0

	If nOpc == 1
		lTela := COLFILTELA(@aEdi)
		If lTela
			For nI := 1 To Len(aEdi)
				If aEdi[nI,1]
					If Empty(cRet)
						cRet := aEdi[nI,2]
					Else
						cRet += ";"+aEdi[nI,2]
					Endif
				Endif
			Next nI
		Endif

		If !Empty(cRet)
			MV_PAR04 := cRet
		Endif
	Elseif nOpc == 2
		cRet := MV_PAR04
	Endif

Return Iif(nOpc==1,lOk,cRet)

//-------------------------------------------------------------------
/*/{Protheus.doc} COLFILERR
Consulta especifica para codigos de erro

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Function COLFILERR(nOpc)

	Local lOk		:= .T.
	Local lTela		:= .T.
	Local aCod		:= COLERPERR()
	Local aCodErr	:= {}
	Local nI		:= 0
	Local cRet		:= ""
	Local aAux		:= {}

	For nI := 1 To Len(aCod)
		aAdd(aCodErr,{.F.,aCod[nI],ColErroErp(aCod[nI])})
	Next nI

	If nOpc == 1
		lTela := COLFILTELA(@aCodErr)
		If lTela
			For nI := 1 To Len(aCodErr)
				If aCodErr[nI,1]
					If Empty(cRet)
						cRet := aCodErr[nI,2]
					Else
						cRet += ";"+aCodErr[nI,2]
					Endif
				Endif
			Next nI
		Endif

		If !Empty(cRet)
			aAux := Separa(cRet,";")
			cRet := ""
			For nI := 1 To Len(aAux)
				If nI <= 14
					If Empty(cRet)
						cRet := aAux[nI]
					Else
						cRet += ";" + aAux[nI]
					Endif
				Endif
			Next nI

			MV_PAR05 := cRet
		Endif
	Elseif nOpc == 2
		cRet := MV_PAR05
	Endif

Return Iif(nOpc==1,lOk,cRet)

//-------------------------------------------------------------------
/*/{Protheus.doc} COLFILTELA
Tela da consulta especifica (edi / erros)

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Static Function COLFILTELA(aInfo)

	Local aHdr	   := {"","Codigo","Descrição"}

	DEFINE MSDIALOG oDlgFil FROM 00,00 TO 290,490 PIXEL TITLE "Filtro"

	oListBox := TWBrowse():New(03,03,250,125,,aHdr,,oDlgFil,,,,,,,,,,,,.F.,,.T.,,.F.,,,)
	oListBox:SetArray(aInfo)
	oListBox:bLine := { ||{ Iif(aInfo[oListBox:nAT][1],oColOK,oColNo),aInfo[oListBox:nAT][2],aInfo[oListBox:nAT][3]}}
	oListBox:bLDblClick := { || COLREPCLICK(3,aInfo,3,oListBox)}
	oListBox:bHeaderClick := {|| COLREPCLICK(4,aInfo,4,oListBox)}

	@ 130,05 BUTTON oConf Prompt "Confirma" SIZE 45 ,10   FONT oDlgFil:oFont ACTION (lOk:=.T.,aInfo := aClone(oListBox:aArray),oDlgFil:End())  OF oDlgFil PIXEL //'Confirma'
	@ 130,55 BUTTON oCanc Prompt "Cancela" SIZE 45 ,10   FONT oDlgFil:oFont ACTION (lOk:=.F.,oDlgFil:End())  OF oDlgFil PIXEL //'Cancela'

	ACTIVATE MSDIALOG oDlgFil CENTERED

Return lOk

//-------------------------------------------------------------------
/*/{Protheus.doc} COLX1COLREP
Verifica se Pergunte COLREP existe

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//-------------------------------------------------------------------

Static Function COLX1COLREP()

	Local lRet := .F.
	Local oColRep	:= FWSX1Util():New()

	oColRep:AddGroup("COLREP")
	oColRep:SearchGroup()

	If Len(oColRep:aGrupo[1,2]) > 0
		lRet := .T.
	Endif

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} COLVLSEGUM
Valida se campo Qtd. Segunda unidade de medida pode ser editada.
Obs: Somente quando fator de conversão for 0

@author	rodrigo.mpontes
@since		08/07/2020
@version	12.1.17
/*/
//-------------------------------------------------------------------

Function COLVLSEGUM(cPrd,cPrdSegum)

	Local nPrd		:= 0
	Local nSegum	:= 0
	Local nLin 		:= 0
	Local nConv		:= 0
	Local nTamB1COD	:= TamSX3("B1_COD")[1]
	Local cSegum	:= ""
	Local lEdit		:= .F.
	Local lFatConv	:= .F.

	Default cPrd		:= ""
	Default cPrdSegum	:= ""

	If Empty(cPrd) //Validação para saber se pode editar o campo DT_QTSEGUM
		nPrd	:= GdFieldPos("DT_COD",oGetDados:aHeader)
		nSegum	:= GdFieldPos("DT_SEGUM",oGetDados:aHeader)
		nLin 	:= oGetDados:nAt

		If nPrd > 0 .And. nSegum > 0
			cSegum	:= AllTrim(oGetDados:aCols[nLin,nSegum])
			nConv	:= GetAdvFval("SB1","B1_CONV",xFilial("SB1") + PadR(oGetDados:aCols[nLin,nPrd],nTamB1COD),1)

			If Empty(cSegum)
				Aviso(STR0004,STR0198,{"OK"}) //"Produto não possui segunda unidade de medida. Não há necessidade de informar a quantidade da segunda unidade."
			Else
				If nConv <> 0
					Aviso(STR0004,STR0195,{"OK"}) //"Conversão ja realizada. Edição somente quando fator de conversão estiver zerado."
				Elseif nConv == 0
					lEdit := .T.
				Endif
			Endif
		Endif
	Else
		//Validação se produto possui fator de conversão
		If Empty(cPrdSegum)
			cPrdSegum := GetAdvFval("SB1","B1_SEGUM",xFilial("SB1") + PadR(cPrd,nTamB1COD),1)
		Endif
		nConv	:= GetAdvFval("SB1","B1_CONV",xFilial("SB1") + PadR(cPrd,nTamB1COD),1)
		If nConv <> 0 .And. !Empty(cPrdSegum)
			lFatConv := .T.
		Endif
	Endif

Return Iif(Empty(cPrd),lEdit,lFatConv)

//-------------------------------------------------------------------
/*/{Protheus.doc} COMCOLXML
Busca XML do documento a ser importado

@author	rodrigo.mpontes
@since		18/05/2021
@version	12.1.17
/*/
//-------------------------------------------------------------------

Static Function COMCOLXML(cFilSDS,cDoc,cSerie,cFornece,cLoja)

	Local oXMLCKO	:= Nil
	Local aArea		:= GetArea()
	Local cQry		:= ""
	Local cQXML		:= GetNextAlias()
	Local cXML		:= ""
	Local cXMLEncod	:= ""
	Local cError	:= ""
	Local cWarning	:= ""
	Local nPosPesq	:= 0

	cQry	:= " SELECT DS_ARQUIVO"
	cQry 	+= " FROM " + RetSqlName("SDS") + " SDS"
	cQry	+= " WHERE SDS.DS_FILIAL = '" + cFilSDS + "' "
	cQry	+= " AND SDS.DS_DOC = '" + cDoc + "' "
	cQry	+= " AND SDS.DS_SERIE = '" + cSerie + "' "
	cQry	+= " AND SDS.DS_FORNEC = '" + cFornece + "' "
	cQry	+= " AND SDS.DS_LOJA = '" + cLoja + "' "
	cQry	+= " AND SDS.D_E_L_E_T_ = ' '"

	cQry := ChangeQuery(cQry)

	dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQry),cQXML,.T.,.T.)

	If (cQXML)->(!EOF())
		cXML := GetAdvFval("CKO","CKO_XMLRET",Alltrim((cQXML)->DS_ARQUIVO),1)

		If !Empty(cXML)
			If !Empty(cXML)
				If SubStr(cXML,1,1) != "<"
					nPosPesq := At("<",cXML)
					cXML  := SubStr(cXML,nPosPesq,Len(cXML))		// Remove caracteres estranhos antes da abertura da tag inicial do arquivo
				EndIf
			EndIf

			cXMLEncod := EncodeUtf8(cXML)

			If Empty(cXMLEncod)
				cXMLEncod 	:= cXML
				cXML 		:= A140IRemASC(cXMLEncod)
				cXMLEncod 	:= EncodeUtf8(cXML)
			EndIf

			If !Empty(cXMLEncod)
				oXMLCKO := XmlParser(cXMLEncod,"_",@cError,@cWarning)
			EndIf
		Endif
	Endif

	(cQXML)->(DbCloseArea())

	RestArea(aArea)

Return oXMLCKO

/*/{Protheus.doc} ComMetric
Quantidade de inclusão de documento pelo Importador/Colaboração

@Param cOper	inc (Inclusão)
@Param cImport	import (Importador XML) / colab (Totvs Colaboração)
@Param cTpDoc	nfe (NFe/Dev/Ben/Compl) / cte (Conhecimento Frete) / cteos / nfs (nota fiscal serviço)
@Param cComCol1	monit (COMCOL1=0) / prenota (COMCOL1=1) / classif (COMCOL1=2)

@author rodrigo.mpontes
@since 25/05/2021
@return Nil, indefinido
/*/
Static Function ComMetric(cOper,cImport,cTpDoc,cComCol1)

	Local cIdMetric		:= "compras-protheus_colaboracao-mvcomcol1_total"
	Local cRotina		:= "comxcol"
	Local cSubRoutine	:= cRotina+cOper+cImport+cTpDoc+cComCol1+"-total"
	Local lContinua		:= (FWLibVersion() >= "20210517") .And. FindClass('FWCustomMetrics')

	If lContinua
		FWCustomMetrics():setSumMetric(cSubRoutine, cIdMetric, 1, /*dDateSend*/, /*nLapTime*/,cRotina)
	Endif

Return
