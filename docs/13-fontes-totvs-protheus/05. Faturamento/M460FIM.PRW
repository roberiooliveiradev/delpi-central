#INCLUDE "RWMAKE.CH"
#INCLUDE "PROTHEUS.CH"
#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³M460FIM    ºAutor  ³Microsiga           º Data ³  03/11/03   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ P.E. GERACAO DO DOCUMENTO DE SAIDA                         º±±
±±º          ³                                                            º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ AP                                                        º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

User Function M460FIM()

	lOCAL aArea 	:= getarea()
	lOCAL aAreaSA1 :=SA1->(GetArea())
	lOCAL aAreaSF2 :=SF2->(GetArea())


	Private 	CVOLUME1,CESPECI1,NPBRUTO,NPLIQUI,cAlmox,cont
	Private cDOC,cSERIE,cCLIENTE,cLOJA,aCOLS,aHEADER,cCHAVE,cAlmox


	//dbSelectArea("SF2")
	//SF2->(dbGOTO(130713))

	If	cEmpAnt == '03'
		Return
	EndIf

	If	cEmpAnt == '04'
		Return
	EndIf

	cVOLUME1 := SF2->F2_VOLUME1
	cESPECI1 := SF2->F2_ESPECI1
	nPLIQUI  := SF2->F2_PLIQUI
	nPBRUTO  := SF2->F2_PBRUTO
	cDOC     := SF2->F2_DOC             // Numero
	cSERIE   := SF2->F2_SERIE           // Serie
	cCLIENTE := SF2->F2_CLIENTE
	cLOJA	 := SF2->F2_LOJA
	cChave 	 := cDOC+cSERIE+cCLIENTE+cLOJA
	aHeader  := {}
	aCols    := {}
	nUsado   := 0
	if SF2->F2_TIPO =='N'
		GeraOSepNota(cDOC+cSERIE)
	ENDIF
	AlteraCampos()

	dbSelectArea("SA1")
	SA1->(dbSetOrder(1))



	If   SA1->(dBSeek(xFilial("SA1")+cCLIENTE+cLOJA))
		IF SA1->A1_BLEMAIL =="1"
			CONOUT("VAI GERAR BORDERO")
			/* fPutBol() */

		ENDIF
	ENDIF

	restarea(aArea)
	restarea(aAreaSA1)
	restarea(aAreaSF2)

Return


static function fPutBol()

	Local cTmp := "TMPBOR"
	Local cFiltro := ""
	Local aTit := {}
	Local aBor := {}

	Local cBanco := "001"
	Local cAgencia := "31631"
	Local cConta := "5156X     "

	Local cSituaca := "1"
	Local cNumBor := ""
	Local dDataMov := ""

	Local cEspecie := '2'

	Local cSubconta := '001'



	//-- Variáveis utilizadas para o controle de erro da rotina automática
	Local aErroAuto :={}
	Local cErroRet :=""
	lOCAL cEol := chr(10)
	Local nCntErr :=0
	Private lMsErroAuto := .F.
	Private lMsHelpAuto := .T.
	Private lAutoErrNoFile := .T.



	// Filtro SQL para para adicionar os titulos no borderô

	cQrySE1 := "SELECT * FROM  dbo."+ RetSqlName("SE1") + cEol
	cQrySE1 += "WHERE D_E_L_E_T_ =''  " + cEol
	cQrySE1 += "AND  E1_FILIAL   =  "+VALTOSQL(XFILIAL("SE1")) + cEol
	cQrySE1 += "AND  E1_NUM      =  "+VALTOSQL(SF2->F2_DOC     ) + cEol
	cQrySE1 += "AND  E1_PREFIXO  =  "+VALTOSQL(SF2->F2_SERIE ) + cEol
	cQrySE1 += "AND  E1_CLIENTE  =  "+VALTOSQL(SF2->F2_CLIENTE) + cEol
	cQrySE1 += "AND  E1_LOJA     =  "+VALTOSQL(SF2->F2_LOJA) + cEol


	If Select('TMPSE1') <> 0
		TMPSE1->(dbCloseArea())
	Endif
	TCQuery cQrySE1 Alias TMPSE1 New

	//Adiciona os títulos no array
	While TMPSE1->(!eof())

		aAdd(aTit,	{{"E1_FILIAL" ,TMPSE1->E1_FILIAL },;
			{"E1_PREFIXO" ,TMPSE1->E1_PREFIXO },;
			{"E1_NUM" ,TMPSE1->E1_NUM },;
			{"E1_PARCELA" ,TMPSE1->E1_PARCELA },;
			{"E1_TIPO" ,TMPSE1->E1_TIPO };
			})
		TMPSE1->(dbSkip())

	EndDo

	TMPSE1->(dbCloseArea()) //Fecho a tabela temporária

	If Empty(aTit) .OR. cSituaca == "0" //Caso não encontre títulos ou situação 0 deve sair da rotina.

		RETURN(.F.)

	EndIf

	//Informações bacárias para o borderô
	aAdd(aBor, {"AUTBANCO" , PadR(cBanco ,TamSX3("A6_COD")[1]) })
	aAdd(aBor, {"AUTAGENCIA" , PadR(cAgencia ,TamSX3("A6_AGENCIA")[1]) })
	aAdd(aBor, {"AUTCONTA" , PadR(cConta ,TamSX3("A6_NUMCON")[1]) })
	aAdd(aBor, {"AUTSITUACA" , PadR(cSituaca ,TamSX3("E1_SITUACA")[1]) })
	aAdd(aBor, {"AUTNUMBOR" , PadR(cNumBor ,TamSX3("E1_NUMBOR")[1]) }) // Caso não seja passado o número será obtido o próximo pelo padrão do sistema
	aAdd(aBor, {"AUTSUBCONTA" , PadR(cSubconta,TamSX3("EA_SUBCTA")[1]) })
	aAdd(aBor, {"AUTESPECIE" , PadR(cEspecie,TamSX3("EA_ESPECIE")[1]) })
	aAdd(aBor, {"AUTBOLAPI" , .T. })
	CONOUT("EXECAUTO FINA060")
	MSExecAuto({|a, b| FINA060(a, b)}, 3,{aBor,aTit})

	If lMsErroAuto

		aErroAuto := GetAutoGRLog()
		For nCntErr := 1 To Len(aErroAuto)

			cErroRet += aErroAuto[nCntErr]

		Next

		Conout(cErroRet)

	EndIf

Return


Static Function AlteraCampos()

	DbSelectArea("SD2")
	DbSetOrder(3)
	DbGotop()

	aHeader  := {}
	nOpc     := 3

	cont:=0
	DbSelectArea("SX3")
	DbSetOrder(1)
	DbGotop()
	DbSeek("SD2",.T.)
	While !Eof() .And. (SX3->X3_arquivo == "SD2")
		If (Alltrim(SX3->X3_CAMPO) == "D2_ITEM"  .Or.;
				Alltrim(SX3->X3_CAMPO) == "D2_COD"	 .Or.;
				Alltrim(SX3->X3_CAMPO) == "D2_UM"  	 .Or.;
				Alltrim(SX3->X3_CAMPO) == "D2_QUANT" .Or.;
				Alltrim(SX3->X3_CAMPO) == "D2_ALMOX")
			If X3USO(SX3->X3_USADO)
				nUsado++
				Aadd(aHeader,{Trim(SX3->X3_TITULO),SX3->X3_CAMPO,SX3->X3_PICTURE,;
					SX3->X3_TAMANHO,SX3->X3_DECIMAL,SX3->X3_VLDUSER,;
					SX3->X3_USADO,SX3->X3_TIPO,SX3->X3_ARQUIVO,SX3->X3_CONTEXT,SX3->X3_F3,SX3->X3_VALID})
				cont++
				If SX3->X3_CAMPO == "D2_ALMOX"
					cAlmox := cont
				EndIf
			Endif
		EndIf

		DbSelectArea("SX3")
		DbSkip()
	Enddo

	aGetQtd := {}
	Aadd(aGetQtd ,"D2_ALMOX")
	aCols := {}

	DbSelectArea("SA7")
	SA7->(dbSetOrder(1))
	//	SB1->(MsSeek(xFilial("SB1")+aArray[nCntFor][1]))

	DbSelectArea("SD2")
	DbSetOrder(3)
	DbGotop()
	dbSeek(xFilial()+cChave,.t.)
	While !EOF() .And. D2_FILIAL+D2_DOC+D2_SERIE+D2_CLIENTE+D2_LOJA == xFilial()+cChave


		cUm  := SD2->D2_UM
		nQtd :=	SD2->D2_QUANT
		// Gabriel
		//A7_FILIAL, A7_CLIENTE, A7_LOJA, A7_PRODUTO, R_E_C_N_O_, D_E_L_E_T_
		IF 	SA7->(MsSeek(xFilial("SA7")+SF2->F2_CLIENTE + SF2->F2_LOJA+SD2->D2_COD))

			if ALLTRIM(SA7->A7_NF3UM) $ "S"

				cUm := SA7->A7_UM3

				IF ALLTRIM(SA7->A7_TPCONV) $ "D"

					nQtd := SD2->D2_QUANT / SA7->A7_CONV3

				ELSE

					nQtd := SD2->D2_QUANT * SA7->A7_CONV3

				ENDIF

			ENDIF
		ENDIF
		//Aadd(aCols,{SD2->D2_ITEM,;
		//	SD2->D2_COD,;
		//	SD2->D2_UM,;
		//	SD2->D2_QUANT,;
		//	SD2->D2_ALMOX,.F.})
		Aadd(aCols,{SD2->D2_ITEM,;
			SD2->D2_COD,;
			cUm,;
			nQtd,;
			SD2->D2_ALMOX,.F.})

		DbSelectArea("SD2")
		SD2->(DbSkip())
	End

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Titulo da Janela                                             ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	cTitulo:="Informações Complementares Nota Fiscal Nº "+cDOC+"/"+cSERIE

	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³ Chamada do comando browse                                    ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

	@ 000,000 TO 400,800 DIALOG oDlgQtd TITLE cTitulo

	@ 001,002 Say "Volume/Caixa:"
	@ 001,007 Get cVOLUME1 SIZE 40,10 pict "@E 999999"

	@ 01,015 Say "Especie  :"
	@ 01,020 Get cESPECI1   SIZE 40,10 pict "@!"

	@ 02,002 Say "Peso Liquido:"
	@ 02,007 Get nPLIQUI  SIZE 40,10  pict "@E 9999.9999"

	@ 02,015 Say "Peso Bruto  :"
	@ 02,020 Get nPBRUTO  SIZE 40,10 pict "@E 9999.9999"
	@ 02,015 Say "Peso Bruto  :"
	@ 02,020 Get nPBRUTO  SIZE 40,10 pict "@E 9999.9999"

	oBrowQtd := MsGetDados():New(043,005,170,390,nOpc,"AllwaysTrue","AllwaysTrue",,.T.,aGetQtd,,,999)
	oBrowQtd:oBrowse:bWhen := {||(Len(aCols),.T.)}
	oBrowQtd:oBrowse:Refresh()

	@ 0017,005 BUTTON "_Gravar" SIZE 38,12 ACTION oGrava()
	@ 017,015 BUTTON "_Sair"   SIZE 38,12 ACTION Close(oDlgQtd)

	ACTIVATE DIALOG oDlgQtd CENTERED

Return

Static Function oGrava()

	dbSelectArea("SF2")
	reclock("SF2",.f.)

	sf2->f2_volume1 := cVOLUME1
	sf2->f2_especi1 := cESPECI1
	sf2->f2_PLIQUI  := nPLIQUI
	sf2->f2_PBRUTO  := nPBRUTO

	msunlock("SF2")

	dbSelectArea("SD2")                // * Itens de Venda da N.F.
	dbSetOrder(3)
	dbSeek(xFilial()+cCHAVE)
	While !EOF() .And. D2_FILIAL+D2_DOC+D2_SERIE+D2_CLIENTE+D2_LOJA == xFilial()+cChave
		For _q := 1 to Len(aCols)
			If SD2->D2_ITEM == aCols[_q][1]
				RecLock("SD2",.f.)
				SD2->D2_ALMOX := aCols[_q][5]
				MsUnlock("SD2")
				exit
			EndIf
		Next
		dbSelectArea("SD2")
		dbSkip()
	End

	Close(oDlgQtd)

Return




STATIC Function GeraOSepNota(  cNotaSerie )
	Local cChaveDB
	Local cTipExp
	Local nI
	Local cCodOpe
	Local aRecSD2 := {}
	Local aOrdSep := {}
	Local lFilItens  := ExistBlock("ACDA100I")  //Ponto de Entrada para filtrar o processamento dos itens selecionados
	Local lA100CABE := ExistBlock("A100CABE")
	Local lACD100GI := ExistBlock("ACD100GI")
	Local lACDA100F := ExistBlock("ACDA100F")

	Private aLogOS:= {}

	Default cNotaSerie	:= Nil
	nEmbSimuNF := 2
	nEmbalagNF := 2
	nEmbalagem := 2
	nImpNotaNF := 1
	nImpVolNF  := 2
	nEmbarqNF  := 2
	// analisar a pergunta '00-Separcao,01-Separacao/Embalagem,02-Embalagem,03-Gera Nota,04-Imp.Nota,05-Imp.Volume,06-embarque'
	If nEmbSimuNF == 1
		cTipExp := "01*"
	Else
		cTipExp := "00*"
	EndIF
	If nEmbalagNF == 1
		cTipExp += "02*"
	EndIF
	If nImpNotaNF == 1
		cTipExp += "04*"
	EndIF
	If nImpVolNF == 1
		cTipExp += "05*"
	EndIF
	If nEmbarqNF == 1
		cTipExp += "06*"
	EndIF
	/*Ponto de entrada, permite que o usuário realize o processamento conforme suas particularidades.*/
	If	ExistBlock("ACD100VG")
		If ! ExecBlock("ACD100VG",.F.,.F.,)
			Return
		EndIf
	EndIf

	SF2->(DbSetOrder(1))
	SD2->(DbSetOrder(3))
	SD2->( dbGoTop() )
	cSeparador := " "
	If cNotaSerie == Nil
		ProcRegua( SD2->( LastRec() ), "oook" )
		cCodOpe	 := cSeparador
	Else
		SD2->(DbSetOrder(3))
		SD2->(DbSeek(xFilial("SD2")+cNotaSerie))
		cCodOpe := Space(06)
	EndIf

	ProcRegua( SD2->( LastRec() ), "oook" )
	cCodOpe := cSeparador

	While !SD2->( Eof() ) .and. ( cNotaSerie == Nil .Or. cNotaSerie == SD2->( D2_DOC + D2_SERIE ) )
		If ( cNotaSerie == NIL )
			SD2->( dbSkip() ) ; Loop
		EndIf

		If lFilItens
			If !ExecBlock("ACDA100I",.F.,.F.)
				SD2->( dbSkip() ) ; Loop
			Endif
		Endif

		cChaveDB :=xFilial("SDB")+SD2->(D2_COD+D2_LOCAL+D2_NUMSEQ+D2_DOC+D2_SERIE+D2_CLIENTE+D2_LOJA)
		If Localiza(SD2->D2_COD)
			SDB->(dbSetOrder(1))
			If ! SDB->(dbSeek( cChaveDB ))
				// neste caso nao existe composicao de empenho
				//Grava o historico das geracoes:
				//aadd(aLogOS,{"2",STR0046,SD2->D2_DOC,SD2->D2_SERIE,SD2->D2_CLIENTE,SD2->D2_LOJA,STR0120,"NAO_GEROU_OS"})				 //"Nota"###"Inconsistencia de base, nao existe registro de movimento (SDB)"
				SD2->(DbSkip())
				If cNotaSerie == Nil
					IncProc()
				EndIf
				Loop
			EndIf
		EndIf

		CB7->(DbSetOrder(4))
		If ! CB7->(DbSeek(xFilial("CB7")+SD2->D2_DOC+SD2->D2_SERIE+SD2->D2_LOCAL+" "))
			CB7->(RecLock( "CB7", .T. ))
			CB7->CB7_FILIAL := xFilial( "CB7" )
			CB7->CB7_ORDSEP := GetSX8Num( "CB7", "CB7_ORDSEP" )
			CB7->CB7_NOTA   := SD2->D2_DOC
			//CB7->CB7_SERIE  := SD2->D2_SERIE
			SerieNfId ("CB7",1,"CB7_SERIE",,,,SD2->D2_SERIE)
			CB7->CB7_CLIENT := SD2->D2_CLIENTE
			CB7->CB7_LOJA   := SD2->D2_LOJA
			CB7->CB7_LOCAL  := SD2->D2_LOCAL
			CB7->CB7_DTEMIS := dDataBase
			CB7->CB7_HREMIS := Time()
			CB7->CB7_STATUS := " "   // gravar STATUS de nao iniciada somente depois do processo
			CB7->CB7_CODOPE := cCodOpe
			CB7->CB7_PRIORI := "1"
			CB7->CB7_ORIGEM := "2"
			CB7->CB7_TIPEXP := cTipExp
			If SF2->(DbSeek(xFilial("SF2")+SD2->(D2_DOC+D2_SERIE+D2_CLIENTE+D2_LOJA)))
				CB7->CB7_TRANSP := SF2->F2_TRANSP
			EndIf
			If	lA100CABE
				ExecBlock("A100CABE",.F.,.F.)
			EndIf
			CB7->(MsUnLock())
			ConfirmSX8()
			//Grava o historico das geracoes:
			//	aadd(aLogOS,{"1",STR0046,SD2->D2_DOC,SD2->D2_SERIE,SD2->D2_CLIENTE,SD2->D2_LOJA,"",CB7->CB7_ORDSEP})
			aadd(aOrdSep,CB7->CB7_ORDSEP)
		EndIf
		If Localiza(SD2->D2_COD)
			While SDB->(!Eof() .And. cChaveDB == DB_FILIAL+DB_PRODUTO+DB_LOCAL+DB_NUMSEQ+DB_DOC+DB_SERIE+DB_CLIFOR+DB_LOJA)
				If SDB->DB_ESTORNO == "S"
					SDB->(dbSkip())
					Loop
				EndIf
				CB8->(DbSetorder(4))
				If ! CB8->(DbSeek(xFilial("CB8")+CB7->CB7_ORDSEP+SD2->(D2_ITEM+D2_COD+D2_LOCAL+SDB->DB_LOCALIZ+D2_LOTECTL+D2_NUMLOTE+D2_NUMSERI)))
					CB8->(RecLock( "CB8", .T. ))
					CB8->CB8_FILIAL := xFilial( "CB8" )
					CB8->CB8_ORDSEP := CB7->CB7_ORDSEP
					CB8->CB8_ITEM   := SD2->D2_ITEM
					CB8->CB8_PEDIDO := SD2->D2_PEDIDO
					CB8->CB8_NOTA   := SD2->D2_DOC
					//CB8->CB8_SERIE  := SD2->D2_SERIE
					SerieNfId ("CB8",1,"CB8_SERIE",,,,SD2->D2_SERIE)
					CB8->CB8_PROD   := SD2->D2_COD
					CB8->CB8_LOCAL  := SD2->D2_LOCAL
					CB8->CB8_LCALIZ := SDB->DB_LOCALIZ
					CB8->CB8_SEQUEN := SDB->DB_ITEM
					CB8->CB8_LOTECT := SD2->D2_LOTECTL
					CB8->CB8_NUMLOT := SD2->D2_NUMLOTE
					CB8->CB8_NUMSER := SD2->D2_NUMSERI
					CB8->CB8_CFLOTE := "1"
					aadd(aRecSD2,{SD2->(Recno()),CB7->CB7_ORDSEP})
				Else
					CB8->(RecLock( "CB8", .f. ))
				EndIf
				CB8->CB8_QTDORI += SDB->DB_QUANT
				CB8->CB8_SALDOS += SDB->DB_QUANT
				If nEmbalagem == 1
					CB8->CB8_SALDOE += SDB->DB_QUANT
				EndIf
				If	lACD100GI
					ExecBlock("ACD100GI",.F.,.F.)
				EndIf
				CB8->(MsUnLock())
				SDB->(dbSkip())
			Enddo
		Else
			CB8->(DbSetorder(4))
			If ! CB8->(DbSeek(xFilial("CB8")+CB7->CB7_ORDSEP+SD2->(D2_ITEM+D2_COD+D2_LOCAL+Space(15)+D2_LOTECTL+D2_NUMLOTE+D2_NUMSERI)))
				CB8->(RecLock( "CB8", .T. ))
				CB8->CB8_FILIAL := xFilial( "CB8" )
				CB8->CB8_ORDSEP := CB7->CB7_ORDSEP
				CB8->CB8_ITEM   := SD2->D2_ITEM
				CB8->CB8_PEDIDO := SD2->D2_PEDIDO
				CB8->CB8_NOTA   := SD2->D2_DOC
				//CB8->CB8_SERIE  := SD2->D2_SERIE
				SerieNfId ("CB8",1,"CB8_SERIE",,,,SD2->D2_SERIE)
				CB8->CB8_PROD   := SD2->D2_COD
				CB8->CB8_LOCAL  := SD2->D2_LOCAL
				CB8->CB8_LCALIZ := Space(15)
				CB8->CB8_SEQUEN := SD2->D2_ITEM
				CB8->CB8_LOTECT := SD2->D2_LOTECTL
				CB8->CB8_NUMLOT := SD2->D2_NUMLOTE
				CB8->CB8_NUMSER := SD2->D2_NUMSERI
				CB8->CB8_CFLOTE := "1"
				aadd(aRecSD2,{SD2->(Recno()),CB7->CB7_ORDSEP})
			Else
				CB8->(RecLock( "CB8", .f. ))
			EndIf
			// Ticket 00016296 (DELPI): removido multiplicador *1000 indevido que estourava CBB_SALDOS na filial 01.
			// A quantidade da OS deve ser igual a do pedido/nota (D2_QUANT), sem distincao de empresa/filial.
			CB8->CB8_QTDORI += SD2->D2_QUANT
			CB8->CB8_SALDOS += SD2->D2_QUANT
			If nEmbalagem == 1
				CB8->CB8_SALDOE += SD2->D2_QUANT
			EndIf

			If	lACD100GI
				ExecBlock("ACD100GI",.F.,.F.)
			EndIf
			CB8->(MsUnLock())

			If cNotaSerie==Nil
				IncProc()
			EndIf
		Endif
		SD2->( dbSkip() )
	EndDo

	CB7->(DbSetOrder(1))
	For nI := 1 to len(aOrdSep)
		CB7->(DbSeek(xFilial("CB7")+aOrdSep[nI]))
		CB7->(RecLock("CB7"))
		CB7->CB7_STATUS := "0"  // nao iniciado
		CB7->(MsUnlock())
		If	lACDA100F
			ExecBlock("ACDA100F",.F.,.F.,{aOrdSep[nI]})
		EndIf
	Next
	For nI := 1 to len(aRecSD2)
		SD2->(DbGoto(aRecSD2[nI,1]))
		SD2->(RecLock("SD2",.F.))
		SD2->D2_ORDSEP := aRecSD2[nI,2]
		SD2->(MsUnlock())
	Next
	If len(aRecSD2) >=1
		//aRecSD2[1,2]
		FWAlertSuccess("Ordem de Separação Gerada "+aRecSD2[1,2],"Delpi")
	Endif
Return
