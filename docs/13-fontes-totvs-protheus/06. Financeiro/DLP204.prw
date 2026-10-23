#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE "FILEIO.CH"
#INCLUDE 'TOPCONN.CH'
#INCLUDE "TBICONN.CH"

//
/*/{Protheus.doc} DLP204

tabelas envolvidas SB1 SBZ SD2 SF4 SHI SG2
@author Gabriel
@since 03/07/2019
@version 1.0
@return ${return}, ${return_description}

@type function
/*/
user function DLP204()
	Private aFils
	Private aProdMOD := {} // Ascan(aHeader,{|x| AllTrim(x[2]) == "N0_CHAVE" })

	Private cEol := chr(10)
	Private cHT := chr(9)
	Private aPars := {}
	Private aProd
	Private aEstExc
	Private aColsExc :={}
	Private NESTRU := 1
	Private oExcelApp := Nil
	Private cPath		:= AllTrim(GetTempPath())
	Private cDirDocs	:= MsDocPath()
	Private cArquivo	:= CriaTrab(,.F.)+".xml"
	Private oExcel	:= FWMSEXCEL():New()
	Private nTCUnit := 0
	Private nTCTot := 0
	Private nThrs := 0

	If !ApOleClient('MsExcel')
		ApMsgAlert('MsExcel nao instalado')
		Return
	EndIf

	//Definiùao do Padrao do Excel
	// TSC 10/10/2018: Inicio: Diego Kerstner: Formatar as linhas
	oExcel:SetFrGeneralColor("#000000") // Cor das Letras no Documento
	oExcel:SetBgGeneralColor("#FFFFFF") // Cor de Fundo no Documento
	oExcel:SetFont("CALIBRI") 		// Fonte no Documento
	oExcel:SetFontSize(11)				// Tamanho da Fonte no Documento

	oExcel:SetHeaderBold(.T.) // Define Negrito para Cabeùalho
	oExcel:SetLineBold(.t.)
	If	!Pergunte('DLP204',.T.)

		msgstop("Cancelado pelo Usuario","Delpi")

		Return

	EndIf
	aadd(aPars,MV_PAR01) //DATA DE
	aadd(aPars,MV_PAR02) //DATA ATE
	aadd(aPars,MV_PAR03) //pRODUTO DE
	aadd(aPars,MV_PAR04) //PRODUTO ATE
	aadd(aPars,MV_PAR05) //GRUPO DE
	aadd(aPars,MV_PAR06) //GRUPO ATE
	aadd(aPars,MV_PAR07) //TIPO DE
	aadd(aPars,MV_PAR08) //TIPO ATE
	aadd(aPars,MV_PAR09) //ROTEIRO
	aadd(aPars,MV_PAR10) //Seleciona Filiais
	aadd(aPars,MV_PAR11) //Exibe PA Sim / Nao

	aadd(aColsExc,{"PA"				,1,1,.F.})
	aadd(aColsExc,{"Seq Comp"		,1,1,.F.})
	aadd(aColsExc,{"Cod Produto"	,1,1,.F.})
	aadd(aColsExc,{"Desc Produto"	,1,1,.F.})
	aadd(aColsExc,{"Qtd Fat."		,1,2,.F.})
	aadd(aColsExc,{"UM"				,1,1,.F.})
	aadd(aColsExc,{"Quantidade"		,1,2,.F.})
	aadd(aColsExc,{"Custo Unitario" ,1,2,.F.})
	aadd(aColsExc,{"Custo Total"	,1,2,.T.})
	aadd(aColsExc,{"Custo Produto"	,1,2,.T.})
	aadd(aColsExc,{"Horas"			,1,3,.T.})



	if MV_PAR10 ==1

		aFils := 	AdmGetFil(.F.,.t.,"SG1",.T.,.T.)

	else

		aFils := {cFilAnt}

	endif
	//	ENDIF

	LjMsgrun(OemToAnsi("Aguarde Gerando Estrutura de Custos do Produto "),"Formacao de Custos",{|| fProc() })

return

Static Function fProc()

	//Percorro as filiais selecionadas
	//Retorno os Produtos com base nos parametros e filial corrente
	fExcFil()

return

//seleciona os produtos conforme parametros informados
User Function fGetProds(xFil)

	Local cSql := ""
	Local aRetPrd := {}
	Local nQtdFat

	Local aEst01 :={}
	Local aEst02 :={}
	Local aEst04 :={}
	//zero array de produtos
	aProd := {}

	cSql :="SELECT 	B1_COD 									                                     						" + cEol
	cSql +="		FROM dbo." + RETSQLNAME("SB1") + " SB1 (NOLOCK)                              						" + cEol
	cSql +="WHERE SB1.D_E_L_E_T_ = ''															 						" + cEol
	cSql +="      AND SB1.B1_COD	BETWEEN " + VALTOSQL(aPars[3]) + "  AND " + VALTOSQL(aPars[4]) 						  + cEol
	cSql +="      AND SB1.B1_GRUPO	BETWEEN " + VALTOSQL(aPars[5]) + "  AND " + VALTOSQL(aPars[6]) 						  + cEol
	cSql +="      AND SB1.B1_TIPO	BETWEEN " + VALTOSQL(aPars[7]) + "  AND " + VALTOSQL(aPars[8]) 						  + cEol
	cSql +="      AND SB1.B1_COD IN( SELECT A.D2_COD  											 						" + cEol
	cSql +="							FROM dbo." + RETSQLNAME("SD2") + "  A (NOLOCK) 			 						" + cEol
	cSql +="					 WHERE  A.D_E_L_E_T_ = '' 									     						" + cEol
	cSql +="							AND A.D2_FILIAL = " + VALTOSQL(xFil)        			 						  + cEol
	cSql +="							AND A.D2_EMISSAO BETWEEN " + VALTOSQL(aPars[1]) + "  AND " + VALTOSQL(aPars[2])   + cEol
	cSql +="							AND EXISTS( SELECT  NULL                		       							" + cEol
	cSql +="												FROM dbo." + RETSQLNAME("SF4") + "  SF4 (NOLOCK) 			" + cEol
	cSql +="										WHERE SF4.D_E_L_E_T_ = '' 											" + cEol
	cSql +="										AND SF4.F4_CODIGO = A.D2_TES 										" + cEol
	cSql +="										AND SF4.F4_DUPLIC = 'S')); "

	conout(cSql)
	conout("Fim " + Funname() + " fProc360")
	If (Select("TRBPRD") <> 0)

		dbSelectArea("TRBPRD")
		dbCloseArea()

	Endif

	conout("fGetProds Query para produtos")
	conout(cSql)

	TCQuery cSql NEW ALIAS "TRBPRD"

	while TRBPRD->(!Eof())

		nThrs 	:= 0

		aRetPrd := fGPrdMod({ TRBPRD->B1_COD,xFil,'0',0,TRBPRD->B1_COD })
		//Adiciona PA / MOD
		nQtdFat := aRetPrd[1][5]


		For nX := 1 To Len(aRetPrd)

			oExcel:AddRow("Fl" +xFil,"Estrutura Filial " + xFil ,aRetPrd[nX])

			nThrs += val(StrTran(aRetPrd[nX][11],',','.'))
			oExcel:SetLineBold(.f.)
			//	oExcel:Set2LineBold(.f.)
		next nX

		//
		aEst01 :=Estrut(TRBPRD->B1_COD)


		For n1 := 1 To Len(aEst01)
			cUM  := Posicione("SB1",1,XFILIAL("SB1")+aEst01[n1][3],"B1_UM" )
			cDesc  := Posicione("SB1",1,XFILIAL("SB1")+aEst01[n1][3],"B1_DESC" )
			nCustd := Posicione("SBZ",1,xFil + aEst01[ n1 ][ 3 ],"BZ_CUSTD" )

			if aPars[11] == 1

				oExcel:AddRow("Fl" +xFil,"Estrutura Filial " + xFil , ;
					{TRBPRD->B1_COD,;
					'03',;
					aEst01[n1][3],;
					cDesc,;
					nQtdFat,;
					cUM,;
					StrTran(cvaltochar(aEst01[n1][4]),'.',','),;
					StrTran(cvaltochar(nCustd),'.',','),;
					StrTran( cvaltochar(aEst01[n1][4] * nCustd),'.',','),;
					StrTran(cvaltochar(nCustd *val(nQtdFat)),'.',','),;
					"0,00"})

			endif

			//mod pi
			aEst03 := fGPrdMod	({ aEst01[n1][3],xFil,'1' ,nQtdFat,TRBPRD->B1_COD})
			//estrutura pi
			aEst04 :=Estrut(aEst01[n1][3])

			For n3 := 1 To Len(aEst03)
				nThrs += val(StrTran(aEst03[n3][11],',','.'))
				oExcel:AddRow("Fl" +xFil,"Estrutura Filial " + xFil ,aEst03[n3])

			next n3

			For n4 := 1 To Len(aEst04)


				cUM  := Posicione("SB1",1,XFILIAL("SB1")+aEst04[n4][3],"B1_UM" )
				cDesc  := Posicione("SB1",1,XFILIAL("SB1")+aEst04[n4][3],"B1_DESC" )
				nCustd := Posicione("SBZ",1,xFil + aEst04[ n4 ][ 3 ],"BZ_CUSTD" )
				if aPars[11] == 1
					oExcel:AddRow("Fl" +xFil,"Estrutura Filial " + xFil , ;
						{TRBPRD->B1_COD,;
						'05',;
						aEst04[n4][3],;
						cDesc,;
						nQtdFat,;
						cUM,;
						StrTran(cvaltochar(aEst04[n4][4]),'.',','),;
						StrTran(cvaltochar(nCustd),'.',','),;
						StrTran(cvaltochar(aEst04[n4][4] * nCustd),'.',','),;
						StrTran(cvaltochar(nCustd *val(nQtdFat)),'.',','),;
						"0,00"})
				endif

				//gdanew
				//mod pi
				aEst05 := fGPrdMod	({ 	aEst04[n4][3],xFil,'2' ,nQtdFat,TRBPRD->B1_COD})
				//estrutura pi
				aEst06 :=Estrut(aEst01[n1][3])

				For n5 := 1 To Len(aEst05)

					nThrs += 	val(StrTran(aEst05[n5][11],',','.'))
					oExcel:AddRow("Fl" +xFil,"Estrutura Filial " + xFil ,aEst05[n5])

				next n5

				For n6 := 1 To Len(aEst06)

					cUM  := Posicione("SB1",1,XFILIAL("SB1")+aEst06[n6][3],"B1_UM" )
					cDesc  := Posicione("SB1",1,XFILIAL("SB1")+aEst06[n6][3],"B1_DESC" )
					nCustd := Posicione("SBZ",1,xFil + aEst06[ n6 ][ 3 ],"BZ_CUSTD" )

					if aPars[11] == 1
						oExcel:AddRow("Fl" +xFil,"Estrutura Filial " + xFil , ;
							{TRBPRD->B1_COD,;
							'07',;
							aEst06[n6][3],;
							cDesc,;
							nQtdFat,;
							cUM,;
							StrTran(cvaltochar(aEst06[n6][4]),'.',','),;
							StrTran(cvaltochar(nCustd),'.',','),;
							StrTran(cvaltochar(aEst06[n6][4] * nCustd),'.',','),;
							StrTran(cvaltochar(nCustd *val(nQtdFat)),'.',','),;
							"0,00"})
					endif

				next n6


			next n4

		next n1
		oExcel:AddRow("Fl" +xFil,"Estrutura Filial " + xFil ,{"","","","Total Produto ---->","","","","","","",StrTran(cvaltochar(nThrs),'.',',')})
		oExcel:AddRow("Fl" +xFil,"Estrutura Filial " + xFil ,{"","","","","","","","","","",""})

		TRBPRD->( DbSkip())

	EndDo

Return




Static Function fExcFil()

	//Percorro as filiais selecionadas
	For nI := 1 To Len(aFils)

		//Cria as abas conforme tamanho das filiais selecionadas
		oExcel:AddworkSheet("Fl" + aFils[ nI] )
		oExcel:AddTable("Fl" + aFils[ nI] ,"Estrutura Filial " + aFils[ nI] )

		For nX := 1 To Len(aColsExc)

			oExcel:AddColumn("Fl" + aFils[ nI] ,"Estrutura Filial " + aFils[ nI] ,aColsExc[ nX,1], ,aColsExc[ nX,2], ,aColsExc[ nX,3], ,aColsExc[ nX,4]	)

		next nX
		//Retorno os Produtos com base nos parametros e filial corrente
		U_fGetProds( aFils[ nI] )



	next nI

	If !Empty(oExcel:aWorkSheet)
		oExcel:Activate()
		//oExcel:GetXMLFile("GDA.XML")
		oExcel:GetXMLFile(cDirDocs+"\"+cArquivo)

		CpyS2T(cDirDocs+"\"+cArquivo,cPath)

		oExcelApp := MsExcel():New()
		oExcelApp:WorkBooks:Open(cPath+cArquivo) // Abre uma planilha
		oExcelApp:SetVisible(.T.)
		oExcelApp:Destroy()
	Else
		ApMgAlert("Nao ha valores para exportacao.")
	EndIf


Return





Static Function Estrut(cProduto,nQuant,lOneLevel,lPreEstru)
	LOCAL nRegi
	LOCAL nQuantItem:=0
	LOCAL cCodigo,cComponente,cTrt,cGrOpc,cOpc
	Local  NESTRU := 1
	Local AESTRUTURA :={}
	DEFAULT lOneLevel := .F.
	DEFAULT lPreEstru := .F.

	nQuant:=IF(nQuant == NIL,1,nQuant)
	nEstru++
	If nEstru == 1
		aEstrutura:={}
	EndIf
	dbSelectArea(If(lPreEstru,"SGG","SG1"))
	dbSetOrder(1)
	dbSeek(xFilial()+cProduto)
	While !Eof() .And. If(lPreEstru,GG_FILIAL+GG_COD,G1_FILIAL+G1_COD) == xFilial()+cProduto
		nRegi:=Recno()
		cCodigo    :=If(lPreEstru,GG_COD,G1_COD)
		cComponente:=If(lPreEstru,GG_COMP,G1_COMP)
		cTrt       :=If(lPreEstru,GG_TRT,G1_TRT)
		cGrOpc     :=If(lPreEstru,GG_GROPC,G1_GROPC)
		cOpc       :=If(lPreEstru,GG_OPC,G1_OPC)
		If cCodigo != cComponente
			nProcura:=aScan(aEstrutura,{|x| x[1] == nEstru .And. x[2] == cCodigo .And. x[3] == cComponente .And. x[5] == cTrt})
			If nProcura  = 0
				nQuantItem:=ExplEstr(nQuant,nil,nil,nil,nil,lPreEstru)

				IF nQuantItem >0
					AADD(aEstrutura,{nEstru,cCodigo,cComponente,nQuantItem,cTrt,cGrOpc,cOpc,Recno()})
				ENDIF

			EndIf

			If !lOneLevel
				nRecno:=Recno()
				dbSeek(xFilial()+cComponente)
				IF Found()
					cCodigo:=If(lPreEstru,GG_COD,G1_COD)
					Estrut(cCodigo,nQuantItem,nil,lPreEstru)
					nEstru --
				Else
					MsGoto(nRecno)
					nProcura:=aScan(aEstrutura,{|x| x[1] == nEstru .And. x[2] == cCodigo .And. x[3] == cComponente .And. x[5] == cTrt})
					If nProcura  = 0

						nQuantItem:=ExplEstr(nQuant,nil,nil,nil,nil,lPreEstru)
						IF nQuantItem >0
							AADD(aEstrutura,{nEstru,cCodigo,cComponente,nQuantItem,cTrt,cGrOPc,cOpc,Recno()})
						ENDIF

					EndIf
				Endif
			EndIf
		EndIf
		MsGoto(nRegi)
		dbSkip()
	Enddo
Return(aEstrutura)

//retorna PA ou PI / MOD
Static Function fGPrdMod(aModPar)

	Local aRet := {}
	lOCAl cSql := ""


	If (Select("TRBMOD") <> 0)

		dbSelectArea("TRBMOD")
		dbCloseArea()

	Endif
	cSql := "EXEC STP_DELPI_FORMA_PRECO_"+cempant+" "+valtosql(aModPar[1]) +","+valtosql(aModPar[2]) +"," +  valtosql( aPars[9])  +"," +  valtosql( aPars[1])  +"," +  valtosql( aPars[2]) +"," +  valtosql( aModPar[3]) +"," +  valtosql( aModPar[5])


	conout(cSql)

	TCQuery cSql NEW ALIAS "TRBMOD"

	while TRBMOD->(!Eof())

		TRBPRD->B1_COD
		//Adiciona PA / MOD

		StrTran( cvaltochar(TRBMOD->QTDFAT),'.',',')
		AADD(ARET,{TRBMOD->PA	,TRBMOD->COMP	,TRBMOD->B1_COD	,TRBMOD->B1_DESC	, ;
			iif(TRBMOD->QTDFAT == 0 ,	StrTran( cvaltochar(aModPar[4]),'.',',') ,	StrTran( cvaltochar(TRBMOD->QTDFAT),'.',',') ),;
			TRBMOD->B1_UM	, StrTran(cvaltochar(TRBMOD->G2_TEMPAD),'.',',')	,StrTran( cvaltochar(TRBMOD->CUSTO_UNIT),'.',',')	,StrTran(cvaltochar(TRBMOD->CUSTO_TOTAL),'.',','),	StrTran(cvaltochar(TRBMOD->CUSTOPROD),'.',',')	,StrTran(cvaltochar(TRBMOD->HORAS),'.',',')})

		TRBMOD->( DbSkip())

	EndDo


Return aRet
