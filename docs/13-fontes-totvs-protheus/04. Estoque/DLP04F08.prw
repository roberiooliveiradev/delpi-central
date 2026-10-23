#include 'rwmake.ch'
#include 'topconn.ch'
#INCLUDE 'SET.CH'
#INCLUDE 'protheus.CH'
#Include 'FWMVCDef.ch'

/*/{Protheus.doc} DLP04F08
@Description
@Author 	 TSC - Gabriel Araujo
@Since  	 06/11/2025
@Cliente	 DELPI
/*/
User Function DLP04F08()
	Local aCab        := {}
	Local cCodigo    := ""
	Local n1 := 0
	Local cLogFile := ""
	Local cErro := ""
	lOCAL nTMB5 := GETSX3CACHE("B5_CEME","X3_TAMANHO")
	lOCAL nTMB1 := GETSX3CACHE("B1_COD","X3_TAMANHO")
	Private lMsErroAuto := .F.
	aProd := fGetProd(cFilAnt)

	// Cria arquivo de log (FCreate + FClose para garantir persistencia)
	cLogFile := GetTempPath() + "DLP04F08_LOG.txt"
	FClose(FCreate(cLogFile))
	fLogWrite(cLogFile, "=== DLP04F08 - Log de Processamento ===")
	fLogWrite(cLogFile, "Data/Hora: " + DtoC(Date()) + " " + Time())
	fLogWrite(cLogFile, "Filial: " + cFilAnt)
	fLogWrite(cLogFile, "Total de produtos: " + cValToChar(Len(aProd)))
	fLogWrite(cLogFile, Replicate("-", 60))

	For n1 := 1 to Len(aProd)
		// define o codigo do produto a ser utilizado
		cCodigo    := PADR(aProd[n1],nTMB1)
		lMsErroAuto := .F.
		//
		// Para incluir um registro na SB5, obrigatoriamente o codigo do produto deve estar previamente cadastrado na tabela SB1
		//
		dbSelectArea("SB1")
		dbSetOrder(1)
		If DbSeek(xFilial("SB1")+cCodigo)

			aCab:= {     {"B5_FILIAL"  ,"02"  ,Nil},;
				{"B5_COD"  ,cCodigo  ,Nil},;            // Codigo identificador do produto
			{"B5_CEME"  ,PADR(SB1->B1_DESC,nTMB5)  ,Nil},;
				{"B5_TIPUNIT"  ,"0"  ,Nil},;
				{"B5_QEI"  ,1 ,Nil},;
				{"B5_QTDVAR"  ,"2"  ,Nil},;
				{"B5_QEL"  ,1  ,Nil} }
			// Nome cientifico do produto
			MSExecAuto({|x,y| Mata180(x,y)},aCab,3) //Inclusao
			conout("Acabou de executar a opcao Incluir na rotina automatica do Cadastro de Complemento do Produto")

			//-- Retorno de erro na execucao da rotina
			If lMsErroAuto
				conout("erro ao incluir o produto")
				cErro:=MostraErro()
				fLogWrite(cLogFile, AllTrim(cCodigo) + " | ERRO | " + cErro)
			Else
				conout("Incluido com sucesso")
				fLogWrite(cLogFile, AllTrim(cCodigo) + " | INCLUIDO")
			Endif
		Else
			conout("Produto nao foi encontrado na tabela SB1.")
		EndIf
	Next n1

	fLogWrite(cLogFile, Replicate("-", 60))
	fLogWrite(cLogFile, "Processamento finalizado: " + DtoC(Date()) + " " + Time())
	conout("Log gerado em: " + cLogFile)

Return


/*/{Protheus.doc} fGetProd
@Description
@Type
@Author 	 TSC - Gabriel Araujo
@Since  	 06/11/2025
/*/
Static Function fGetProd(cCodFil)
	lOCAL cSql :=""
	Local cEol:=chr(10)
	lOCAL aProdRet :={}
	// PLSQuery(cQryDados, 'QRYDADTMP')
	cSql+= "SELECT TOP 25000 B1_COD" + cEol
	cSql+= "FROM   "+RetSQLName("SB1")+" (NOLOCK) SB1  "  + cEol
	cSql+= "WHERE D_E_L_E_T_ = '' "  + cEol
	cSql+= "AND B1_MSBLQL != '1' "  + cEol
	cSql+= "AND NOT EXISTS ( "  + cEol
	cSql+= " SELECT NULL "  + cEol
	cSql+= " FROM "+RetSQLName("SB5")+" (NOLOCK) SB5  "   + cEol
	cSql+= " WHERE SB5.D_E_L_E_T_ = '' "   + cEol
	// cSql+= "   AND B5_FILIAL = " +valtosql(cCodFil)  + cEol
	cSql+= "   AND B5_FILIAL = " +valtosql("01")  + cEol
	cSql+= "   AND B5_COD = B1_COD    ) "   + cEol

	If Select('QRYSB1') <> 0
		QRYSB1->(dbCloseArea())
	Endif
	TCQuery cSql New Alias QRYSB1
	While ! QRYSB1->(EoF())
		aadd(aProdRet,QRYSB1->B1_COD)
		QRYSB1->(DbSkip())
	EndDo
	QRYSB1->(DbCloseArea())
Return aProdRet


/*/{Protheus.doc} fLogWrite
@Description Grava uma linha no arquivo de log (abre, grava e fecha a cada chamada para garantir persistencia)
@Author TSC
@Since 10/03/2026
/*/
Static Function fLogWrite(cFile, cText)
	Local nHdl := FOpen(cFile, 2) // 2 = leitura/escrita
	FSeek(nHdl, 0, 2)
	FWrite(nHdl, cText + CRLF)
	FClose(nHdl)
Return
