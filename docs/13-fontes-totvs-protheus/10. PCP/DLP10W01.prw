#INCLUDE "TOTVS.CH"
#INCLUDE 'FWMVCDEF.CH'
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWPrintSetup.ch"
#Include 'TopConn.ch'
#Include "RPTDef.ch"

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 09/01/2025
/*/
User Function DLP10W01()

	Local cZWFXML1 :=  SuperGetMV("MV_WFCOMTO", .F., 'pcp_delpi@delpi.com.br; compras@delpi.com.br; compras1@delpi.com.br; suprimentos@delpi.com.br')
	Local cZWFXML2 :=  "gabriel.araujo@totvs.com.br"//SuperGetMV('MV_ZWFXML2', .F., 'joici@delpi.com.br')
	Local cEnvMsg  := ""
	Local cAssun 	 := "Itens com Prazo de Entrega não preenchidos"
	Local cTitWf := "Segue a lista de produtos que precisam de ajustes no indicador de Produto"
	// Local cAnex 	 := SuperGetMV('MV_NGLIDOS', .F., ' ')

	cEnvMsg := "Prezados,"+CRLF+;
		"Segue rela&#231;&#227;o de Produtos que necessitam ajuste de cadastro no Indicador de Produto"+CRLF+;
		"Prazo de Entrega:"

	EnvWF(cZWFXML1,cZWFXML2,cAssun,cTitWf,cEnvMsg)



Return

Static function EnvWF(cToC,cBCC,cSubj,cTitWf,cMsg)
	Local oProcess //:= Nil
	Local oHtml
	Local nTotal := 0
	Local cQry := ""

	cQry := "SELECT  BZ_FILIAL, BZ_COD, B1_DESC, BZ_PE"+CRLF
	cQry += "FROM dbo.SB1010 (NOLOCK) TBL1"+CRLF
	cQry += "JOIN "+RetSqlName("SBZ")+" (NOLOCK) SBZ ON SBZ.D_E_L_E_T_ =''  AND BZ_COD = B1_COD"+CRLF
	cQry += "WHERE TBL1.D_E_L_E_T_ = ''"+CRLF
	cQry += "AND TBL1.B1_TIPO = 'MP'"+CRLF
	cQry += "AND B1_MSBLQL !='1'"+CRLF
	cQry += "AND(( BZ_PE < 7 and BZ_FILIAL = '01' )"+CRLF
	cQry += "OR ( BZ_PE < 14 and BZ_FILIAL = '02')) "+CRLF
	TCQuery cQry New Alias "QRY_SBZ"

	oProcess := TWFProcess():New("DLP10W01","WFDELPIPCP")

	oProcess:NewTask("DLP10W01","\WF\dlp10wf01.html")
	oProcess:cSubject := cSubj
	oProcess:cTo      := cToC
	oProcess:cBCC := cBCC
	// oProcess:AttachFile(cAnex)

	oHtml := oProcess:oHtml

	oHtml:ValByName('titulowf', cTitWf)

	QRY_SBZ->(DbGoTop())

	//Enquanto houver registros
	While !QRY_SBZ->(EoF())

		nTotal++

		aAdd(oHtml:ValByName("it.filnum"), AllTrim(QRY_SBZ->(BZ_FILIAL)))
		aAdd(oHtml:ValByName("it.codprod"), AllTrim(QRY_SBZ->(BZ_COD)))
		aAdd(oHtml:ValByName("it.descprod"), AllTrim(QRY_SBZ->(B1_DESC)))
		aAdd(oHtml:ValByName("it.leadtime"), AllTrim(CVALTOCHAR(QRY_SBZ->(BZ_PE))))

		QRY_SBZ->(DbSkip())

	EndDo

	oHtml:ValByName('totalitens', ALLTRIM(STR(nTotal)))

	oProcess:Start()
	oProcess:Finish()

	QRY_SBZ->(DbCloseArea())

return
