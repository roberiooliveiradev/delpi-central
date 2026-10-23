#INCLUDE 'TOTVS.CH'

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 05/12/2024
/*/
User Function COMCOLRT()
	Local aRotina := ParamIxb[1]

	aAdd(aRotina,{"Env Divergencia Compras","u_fEnvWfCom()",0,3,0,Nil})

Return aRotina

/*/{Protheus.doc} nomeFunction
  (long_description)
  @type  Function
  @author Pedro Lindenberg
  @since 05/12/2024
  /*/
User Function fEnvWfCom()
	Local cZWFXML1 :=  SuperGetMV('MV_ZWFXML1', .F., 'gabriel.araujo@totvs.com.br')
	Local cZWFXML2 :=  SuperGetMV('MV_ZWFXML2', .F., 'joici@delpi.com.br')
	Local cEnvMsg  := ""
	Local aPergs   := {}
	Local cMsgEnv  := IF(EMPTY(MV_PAR01),Space(99),MV_PAR01)
	Local cAssun 	 := ''
	Local cAnex 	 := SuperGetMV('MV_NGLIDOS', .F., ' ')

	aadd(aPergs, {1, "Mensagem", cMsgEnv, "", ".T.", "", ".T.", 99, .F.})

	IF ParamBox(aPergs, "Informe os parâmetros do documento inconsistente:",,,,,,,,"",.F.,.F.)

		cEnvMsg := "Foram encontradas inconsistencias ou divergencia no momento de importar o documento. Gentileza revisar o Pedido de Compra. " + MV_PAR01

		Dbselectarea("SDS")
		SDS->(DbSetOrder(1))
		If SDS->(DbSeek(xFilial("SDS")+SDS->DS_DOC+SDS->DS_SERIE+SDS->DS_FORNEC+SDS->DS_LOJA))

			cAssun := '[Divergencias no Recebimento] [EMP:'+cEmpAnt+'] [Filial:'+SDS->DS_FILIAL+'] [DOCUMENTO:'+SDS->DS_DOC+"/"+SDS->DS_SERIE+'] [FORNECEDOR:'+SA2->A2_NOME+']'

			If RecLock('SDS',.F.)

				SDS->DS_YMSGWF := MV_PAR01
				SDS->DS_YHRWF := time()
				SDS->DS_YDTWF := date()

				SDS->(MsUnlock())

			EndIf
			cArqXML := GetAdvFVal("CKO","CKO_ARQXML",Padr((cQXML)->DS_ARQUIVO,TamSX3("CKO_ARQUIV")[1]),1)
			cAnex += "\"+ALLTRIM(cArqXML)

			EnvWF(cZWFXML1,cZWFXML2,cAssun,cAnex,cEnvMsg,SDS->DS_DOC,SDS->DS_SERIE,SDS->DS_FORNEC,SDS->DS_LOJA)

		EndIf

	Else

		Return .F.

	ENDIF

Return

Static function EnvWF(cToC,cBCC,cSubj,cAnex,cMsg,cDoc,cSerie,cFornec,cLoja)
	Local oProcess := Nil

	oProcess := TWFProcess():New("DLP02W01","WFDELPICOMPRAS" )

	oProcess:NewTask("DLP02W01","\WF\DelpiDivPedDeCompra.html")
	oProcess:cSubject := cSubj
	oProcess:cTo      := cToC
	oProcess:cBCC := cBCC
	oProcess:AttachFile(cAnex)

	oProcess:oHtml:ValByName("numDoc" ,cDoc)
	oProcess:oHtml:ValByName("serie" ,cSerie)
	oProcess:oHtml:ValByName("fornece" ,cFornec)
	oProcess:oHtml:ValByName("loja" ,cLoja )
	oProcess:oHtml:ValByName("msgEnv" ,cMsg)

	oProcess:Start()
	oProcess:Finish()

return
