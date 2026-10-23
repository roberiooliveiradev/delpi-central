#Include "Rwmake.ch"
#Include "Ap5mail.ch"
#Include "Tbicode.ch"
#Include "Tbiconn.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "PROTHEUS.CH"
#Include "totvs.ch"
#INCLUDE "APWIZARD.CH"
#INCLUDE "FILEIO.CH"
#INCLUDE "RPTDEF.CH"
#INCLUDE "FWPrintSetup.CH"
#INCLUDE "TOTVS.CH"
#INCLUDE "PARMTYPE.CH"


User Function DLP05F03( cEmpJob,cFilJob,xParam )

	Local cCodEmp	    := ""
	Local cCodFil	    := ""
	Local oProcess
	Local cLockNameZ	:=	"DLP05F03"
	Default xParam      := .F.

	Private cEol        := CHR(10)

	Private lJanela     := .F.
	Private lJob        := .F.
	Private lTimer      := xParam

	DEFAULT cEmpJob	:= "01"
	DEFAULT cFilJob	:= "02"
	CONOUT("Chamou o Job DLP05F03")

	If Select("SX6") == 0
		CONOUT("ENTROU NO X6 - Preparando ambiente")
		RpcSetType(3)
		PREPARE ENVIRONMENT EMPRESA cEmpJob FILIAL cFilJob MODULO "FAT"
		lJob := .t.
	EndIf

	CONOUT("EMPRESA " + CEMPANT)
	CONOUT("FILIAL  " + CFILANT)

	//If !LockByName(cLockNameZ,.T.,.T.)
	//	ConOut("["+cvaltochar(ThreadID())+"] ["+DTOC(DATE())+" "+Time()+" ]"+Procname()+": Rotina já está sendo executada por outro usuário")
	//	Return .F.
	//EndIf

	lJanela := .T.
	cCodEmp := cEmpAnt
	cCodFil := cFilAnt

	PrintDanfe()

	//UnLockByName(cLockNameZ,.T.,.T.)

Return

Static Function PrintDanfe( oProcess, lEnd )

	Local oDanfe
	Local cFilePrint := ""
	//Local aIndArq    := {}
	Local aDevice    := {}
	Local lCustom    := .f. // flag para indicar a rotina padrao de impressao que perguta será especificada pela customização
	Local cSession   := GetPrinterSession()
	Local lUsaColab	 := UsaColaboracao("1")
	//Local cNomPrint  := Alltrim(getMv("DP_PRINTER",,"UES_DCP-L2540DW"))//"Hewlett-Packard HP LaserJet P2035"
	Local cNomPrint  := StrTran(Alltrim(supergetMv("DP_PRINTER",.f.,"UES_BROTHER_HL_L5102DW")),'"','')

	Private cIdEnt   := ""
	Private aNFList  := {}
	Private lAdjustToLegacy := .F. // Inibe legado de resoluï¿½ï¿½o com a TMSPrinter
	CONOUT("IMPRESSORA ["+cNomPrint+"]")
	cIdEnt := RetIdEnti()
	cFilePrint := "DANFE_"+cIdEnt+Dtos(MSDate())+StrTran(Time(),":","")

	AADD(aDevice,"DISCO") // 1
	AADD(aDevice,"SPOOL") // 2
	AADD(aDevice,"EMAIL") // 3
	AADD(aDevice,"EXCEL") // 4
	AADD(aDevice,"HTML" ) // 5
	AADD(aDevice,"PDF"  ) // 6


	//nLocal       	:= If(fwGetProfString(cSession,"LOCAL","SERVER",.T.)=="SERVER",1,2 )
	//nOrientation 	:= If(fwGetProfString(cSession,"ORIENTATION","PORTRAIT",.T.)=="PORTRAIT",1,2)
	//cDevice     	:= If(Empty(fwGetProfString(cSession,"PRINTTYPE","SPOOL",.T.)),"PDF",fwGetProfString(cSession,"PRINTTYPE","SPOOL",.T.))
	//nPrintType      := aScan(aDevice,{|x| x == cDevice })


	if CTIsReady(,,,lUsaColab)
		dbSelectArea("SF2")
		RetIndex("SF2")
		dbClearFilter()

		cQRYTMP := fGetQuery()

		If Select('TMPQRY') <> 0
			TMPQRY->(dbCloseArea())
		Endif

		TCQuery cQRYTMP Alias TMPQRY New
		nFlags := PD_ISTOTVSPRINTER + PD_DISABLEPAPERSIZE + PD_DISABLEPREVIEW + PD_DISABLEMARGIN
		WHILE  TMPQRY->(!eof())
			//	oSetup:=FWPrintSetup():New(nFlags, "DANFE")
			//oSetup:SetProperty(PD_DESTINATION , 2)
			//oSetup:SetProperty(PD_PRINTTYPE , 2  )
			//oSetup:SetProperty(PD_ORIENTATION , 1)

			//oSetup:SetProperty(PD_MARGIN , {60,60,60,60})
			//oSetup:SetProperty(PD_PAPERSIZE , 2)
			//oSetup:CQTDCOPIA := "01"
			//		oSetup:aOptions[PD_VALUETYPE]:=cCaminho
			conout("Imprimindo NF: " +TMPQRY->CB7_NOTA + " Serie: " +TMPQRY->CB7_SERIE + ". Aguarde...")
			oDanfe := FWMSPrinter():New(cFilePrint,IMP_SPOOL, .F., /*cStartPath*/, .T./*lDisabeSetup*/, /*lTReport*/,@oDanfe, cNomPrint, .T./*lServer*/)
			//	oDANFE:SetCopies( Val(oSetup:CQTDCOPIA) )
			//INICIO - TSC959- Thiago.Zoppi (Força a danfe se sempre A4)
			oDanfe:SetResolution(78) //Tamanho estipulado para a Danfe
			oDanfe:SetPortrait()
			oDanfe:SetPaperSize(DMPAPER_A4)
			oDanfe:SetMargin(60,60,60,60)

			//oDanfe:lserver:=.f.
			oDanfe:linjob:=.T.
			oDanfe:cPrinter:=cNomPrint //nome da impressora

			//FIM - TSC959-Thiago.Zoppi (Força a danfe se sempre A4)
			// ----------------------------------------------------------------------------------
			// Cria e exibe tela de Setup Customizavel - OBS: Utilizar include "FWPrintSetup.ch"
			// ----------------------------------------------------------------------------------


			// Salva os Parametros no Profile
			//	fwWriteProfString( cSession, "LOCAL"      , "CLIENT"  , .T. )
			//	fwWriteProfString( cSession, "PRINTTYPE"  , "SPOOL"   , .T. )
			//	fwWriteProfString( cSession, "ORIENTATION", "PORTRAIT", .T. )
			//
			// Configura o objeto de impressão com o que foi configurado na interface.
			//	oDanfe:setCopies( val( "01" ) )
			Pergunte("NFSIGW",.F.)
			SetMvValue("NFSIGW","MV_PAR01",TMPQRY->CB7_NOTA)
			SetMvValue("NFSIGW","MV_PAR02",TMPQRY->CB7_NOTA)
			SetMvValue("NFSIGW","MV_PAR03", TMPQRY->CB7_SERIE	)
			SetMvValue("NFSIGW","MV_PAR04",2)
			SetMvValue("NFSIGW","MV_PAR05",1)
			SetMvValue("NFSIGW","MV_PAR06",2)
			//	SetMvValue("NFSIGW","MV_PAR05",DTQ->DTQ_DATINI)
			//	SetMvValue("NFSIGW","MV_PAR06",DTQ->DTQ_DATINI)
			//
			// Atualiza os parametros no Profile
			//
			//FwWriteProfString( cSession, "LOCAL"      , If(oSetup:GetProperty(PD_DESTINATION)==1 ,"SERVER"    ,"CLIENT"    ), .T. )
			//FwWriteProfString( cSession, "PRINTTYPE"  , If(oSetup:GetProperty(PD_PRINTTYPE)==2   ,"SPOOL"     ,"PDF"       ), .T. )
			//FwWriteProfString( cSession, "ORIENTATION", If(oSetup:GetProperty(PD_ORIENTATION)==1 ,"PORTRAIT"  ,"LANDSCAPE" ), .T. )
			// Inicializo perguntas da impressão de DANFE para setar parametros
			//Pergunte("NFSIGW",.F.)
			//MV_PAR01 := TMPQRY->CB7_NOTA	// Nr NF Inicial
			//MV_PAR02 := TMPQRY->CB7_NOTA	// Nr NF Final
			//MV_PAR03 := TMPQRY->CB7_SERIE	// Nr Serie NF
			//MV_PAR04 := 2				// Tipo de Operacao
			// Salva os Parametros no Profile
			//	fwWriteProfString( cSession, "LOCAL"      , "CLIENT"  , .T. )
			//	fwWriteProfString( cSession, "PRINTTYPE"  , "SPOOL"   , .T. )
			//	fwWriteProfString( cSession, "ORIENTATION", "PORTRAIT", .T. )
			oDanfe:setCopies( val( "01" ) )

			// Inicializo perguntas da impressão de DANFE para setar parametros
			Pergunte("NFSIGW",.F.)
			MV_PAR01 :=  TMPQRY->CB7_NOTA // Nr NF Inicial
			MV_PAR02 :=  TMPQRY->CB7_NOTA // Nr NF Final
			MV_PAR03 := TMPQRY->CB7_SERIE 	// Nr Serie NF
			MV_PAR04 := 2
			conout("va NF: " + TMPQRY->CB7_NOTA + " Serie: " + TMPQRY->CB7_SERIE + " (u_PrtNfeSef) ")
			conout("Chave "+xFilial("CB7")+TMPQRY->CB7_ORDSEP)
			u_PrtNfeSef(cIdEnt,,,oDanfe, /*oSetup*/, cFilePrint,lCustom,0)
			if CB7->(DbSeek(xFilial("CB7")+TMPQRY->CB7_ORDSEP ))
				conout("vai alterar")
				CB7->(RecLock("CB7"))
				CB7->CB7_STATUS := "9"  // nao iniciado
				CB7->(MsUnlock())
			endif
			//conout("Imprimindo NF: " + TMPQRY->CB7_NOTA + " Serie: " + TMPQRY->CB7_SERIE + " (u_PrtNfeSef) ")

			TMPQRY->(dbSkip())

		EndDo

		TMPQRY->(dbCloseArea())

	EndIf

Return

Static Function fGetQuery()

	Local cFilImp := '02'
	Local cStatus := '2'
	Local cNota := '009167'

	Local cRetQry := ""

	cRetQry := " SELECT * " + cEol
	cRetQry += "   FROM dbo."+RetSqlName("CB7") + "(NOLOCK) CB7 " + cEol
	cRetQry += "  WHERE CB7.D_E_L_E_T_= '' " + cEol
	cRetQry += "    AND CB7_FILIAL = " 	+ valtosql( cFilAnt ) + cEol
	cRetQry += "    AND CB7_DTFIMS >= " 	+ valtosql( "20230921" ) + cEol
	cRetQry += "    AND CB7_STATUS = " 	+ valtosql( cStatus )   + cEol
	CONOUT(cRetQry)
Return cRetQry

