#Include 'Protheus.ch'  
#Include 'TopConn.ch'
#Include 'RwMake.ch'
#Include 'TbiConn.ch'
#INCLUDE "FILEIO.CH"
#INCLUDE "FWEVENTVIEWCONSTS.CH"
#INCLUDE "SCHEDCOMCOL.CH"

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
ฑฑษออออออออออัอออออออออออหอออออออัออออออออออออออออออออหออออออัอออออออออออออปฑฑ
ฑฑบPrograma  ณSchedComColบAutor  ณSchedComCol         บ Data ณ  08/06/12   บฑฑ
ฑฑฬออออออออออุอออออออออออสอออออออฯออออออออออออออออออออสออออออฯอออออออออออออนฑฑ
ฑฑบDescricao ณ Funcao para ser schedulada e processar a importacao dos     บฑฑ
ฑฑบ          ณ arquivos TOTVS Colaboracao.                                 บฑฑ
ฑฑฬออออออออออุอออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออนฑฑ
ฑฑบParametrosณ aParam: array de parametros recebidos do schedule Protheus. บฑฑ
ฑฑฬออออออออออุอออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออนฑฑ
ฑฑบUso       ณ SIGACOM                                                     บฑฑ
ฑฑศออออออออออฯอออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออผฑฑ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿
*/
Function SchedComCol(aParam)
Local aProc		:= {}
Local aErros	:= {}
Local aXMLs		:= {}
Local aErroERP	:= {}
Local aEnvErros	:= {}
Local aDocs		:= &(GetNewPar("MV_COLEDI",'{}')) //Recebimento- NF-e, NFS-e, CT-e, AV-e, CTEOS
Local lAtdtBase := SuperGetMV("MV_COMCOL3",.F.,.T.) 	// atualiza a database antes do processamento 
Local nZ		:= 1
Local nW		:= 1
Local nMsgCol	:= 0
Local nPosMsg	:= 0
Local nCount	:= 0
Local nPos		:= 0
Local nPosErp	:= 0
Local lOk		:= .F.
Local lChanFil	:= .F.
Local cXml		:= ""
Local oColab	:= NIL
Local cEventID	:= "" 
Local cMensagem	:= ""
Local aMsgErr	:= Iif(FindFunction("COLERPERR"),COLERPERR(),{})

If Empty(aDocs)
	aDocs := {"109","214","273","319"}
Endif

//Atualiza dDataBase
IF dDataBase <> DATE() .and. lAtdtBase
	dDataBase := DATE()
ENDIF

//Atualiza Empresa/Filial em arquivos na CKO com flag = 0
SCHEDATUEMP()

nMsgCol := SuperGetMV("MV_MSGCOL",.F.,10) 	// Quantidade maxima de mensagens por e-mail

oColab 			:= ColaboracaoDocumentos():New() 
oColab:cQueue 	:= aDocs[1]
oColab:aQueue 	:= aDocs
oColab:cModelo 	:= ""
oColab:cTipoMov := '2'
oColab:cFlag 	:= '0'
oColab:cEmpProc := cEmpAnt
oColab:cFilProc := cFilAnt

//-- Busca na tabela CKO os documentos disponํveis para a filial
oColab:buscaDocumentosFilial()

If !Empty(oColab:aNomeArq)
	aXMLs 	:= oColab:aNomeArq
	nFiles	:= Len(aXMLs)

	While !Empty(nFiles)
		nMsgCol := If(nFiles < nMsgCol, nFiles, nMsgCol)
		
		//-- Processa os XML encontrados para a filial		
		For nZ := 1 To nMsgCol
			aErroERP 	:= {}
			aErros		:= {}
			
			oColab:cNomeArq := aXMLs[nCount+nZ][1]
			oColab:cFlag := '0'
			oColab:Consultar()
			cXml := oColab:cXmlRet
			oColab:cNomeArq := aXMLs[nCount+nZ][1]
			SCHEDATUCKO(oColab:cNomeArq,oColab:cXmlRet)
			lOk := ImportCol(aXMLs[nCount+nZ][1],.T.,@aProc,@aErros,cXml,@aErroERP)
			If lOk
				//-- Marca XML como 1-Processado e limpa os dados de erros
				oColab:cFlag := '1'
				If !Empty(oColab:cCodErrErp)
					oColab:cCodErrErp := ""
					oColab:gravaErroErp()
				Endif
			Else
				If Len(aErroErp) > 0
					If Len(aErroErp[1]) > 0
						If AllTrim(aErroErp[1][2]) == "COM002"	// Se o XML pertencer a outra filial deve deixar o Flag = 0 para deixar o schedule processar na filial correta
							oColab:cFlag := '0'
							lChanFil := .T.
						EndIf
					EndIf
				EndIf

				If !Empty(aErros) .And. !lChanFil
					For nW:=1 to Len(aErros)
						Aadd(aEnvErros,aErros[nW])
					Next nW
					//-- Marca XML com erro de processamento
					oColab:cFlag := '2'
				ElseIf !lChanFil
					//-- Marca XML como nใo processado e limpa os dados de erros
					oColab:cFlag := '0'
					oColab:cCodErrErp := ""
					oColab:gravaErroErp()
				Endif
				
				If !Empty(aErroERP)
					//-- Grava erro de Processamento
					If !(aErroERP[1][2] == "COM002" .and. !EMPTY(CKO->CKO_FILPRO))
						oColab:cCodErrErp := aErroERP[1][2]
						
						nPosErp := aScan(aMsgErr,{|x| AllTrim(x) == aErroERP[1][2]})
						
						If nPosErp > 0
							nPos := aScan(aErros,{|x| aMsgErr[nPosErp] == SubSTr(AllTrim(x[2]),1,6)})
							If nPos > 0
								oColab:cMsgErr024 := aErros[nPos,2]
							Endif
						Endif 
						oColab:gravaErroErp()
					Endif
				Endif
			Endif
			//-- Efetiva marca็ใo
			oColab:FlegaDocumento()
			nPosMsg++
			lChanFil := .F.
		Next nZ
		
		//-- Dispara M-Messenger para erros (evento 052)
		If !Empty(aEnvErros)
			dbSelectarea("SXI")
			dbsetorder(2)
			cEventID := "052" // Evento de Inconsistencia da importa็ใo NF-e/CT-e [TOTVS COLABORAวรO]
		
			If MsSeek ('002' + '001' + cEventID)
				cMensagem := MSGTOTCOL(cEventID,aEnvErros)
				EventInsert(FW_EV_CHANEL_ENVIRONMENT, FW_EV_CATEGORY_MODULES, cEventID,FW_EV_LEVEL_INFO,""/*cCargo*/,STR0001,cMensagem,.T./*lPublic*/) //"Evento de Inconsistencia da importa็ใo NF-e/CT-e [TOTVS COLABORAวรO]"
			Else
				MEnviaMail("052",aEnvErros)
			Endif
			aEnvErros	:= {}
		EndIf
		
		//-- Dispara M-Messenger para docs disponiveis (evento 053)
		If !Empty(aProc)
			dbSelectarea("SXI")
			dbsetorder(2)
			cEventID := "053" // Evento de Inconsistencia da importa็ใo NF-e/CT-e [TOTVS COLABORAวรO]
		
			If MsSeek ('002' + '001' + cEventID)
				cMensagem := MSGTOTCOL(cEventID,aProc)
				EventInsert(FW_EV_CHANEL_ENVIRONMENT, FW_EV_CATEGORY_MODULES, cEventID,FW_EV_LEVEL_INFO,""/*cCargo*/,STR0002,cMensagem,.T./*lPublic*/) //"Evento de documentos NF-e/CT-e procesados [TOTVS COLABORAวรO]"
			Else
				MEnviaMail("053",aProc)
			Endif
			aProc	:= {}
		EndIf
		nCount  += nPosMsg
		nPosMsg := 0
		nFiles  -= nMsgCol
	Enddo
Endif

Return .T.

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
ฑฑษออออออออออัอออออออออออหอออออออัออออออออออออออออออออหออออออัอออออออออออออปฑฑ
ฑฑบPrograma  ณ Scheddef  บAutor  ณRodrigo M Pontes    บ Data ณ  05/04/16   บฑฑ
ฑฑฬออออออออออุอออออออออออสอออออออฯออออออออออออออออออออสออออออฯอออออออออออออนฑฑ
ฑฑบDescricao ณ Tratativa da chamada via scheddef para controle de transa็ใoบฑฑ
ฑฑบ          ณ via framework                                               บฑฑ
ฑฑฬออออออออออุอออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออนฑฑ
ฑฑบUso       ณ SIGACOM                                                     บฑฑ
ฑฑศออออออออออฯอออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออผฑฑ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿
*/

Static Function Scheddef()

Local aParam  := {}

aParam := { "P",;			//Tipo R para relatorio P para processo
            "",;	//Pergunte do relatorio, caso nao use passar ParamDef
            ,;			//Alias
            ,;			//Array de ordens
            }				//Titulo

Return aParam

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
ฑฑษออออออออออัอออออออออออหอออออออัออออออออออออออออออออหออออออัอออออออออออออปฑฑ
ฑฑบPrograma  ณ MSGTOTCOL บAutor  ณRodrigo M Pontes    บ Data ณ  05/04/16   บฑฑ
ฑฑฬออออออออออุอออออออออออสอออออออฯออออออออออออออออออออสออออออฯอออออออออออออนฑฑ
ฑฑบDescricao ณ Tratatica para enviar mensagem via event viewer dos         บฑฑ
ฑฑบ          ณ documentos totvs colabora็ใo                                บฑฑ
ฑฑฬออออออออออุอออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออนฑฑ
ฑฑบUso       ณ SIGACOM                                                     บฑฑ
ฑฑศออออออออออฯอออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออผฑฑ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿
*/

Static Function MSGTOTCOL(cEventID,aDados)

Local cRetMsg		:= ""
Local cExecBlock	:= ""
Local cBkpMsg		:= ""
Local nI			:= 0
Local lEditMsg	:= ExistBlock("EVCOL"+Substr(cEventID,1,3))

If cEventId == "052" //Inconsistencias
	cRetMsg := '<html>'
	cRetMsg += '	<body>'
	cRetMsg += '		<h3>'
	cRetMsg += '			<strong style="font-weight: bold; color: gray;">'
	cRetMsg += STR0003 //"Aviso de inconsist๊ncias da importa็ใo NF-e/CT-e [TOTVS Colabora็ใo]"
	cRetMsg += '			</strong>'
	cRetMsg += '		</h3>'
	cRetMsg += '		<p>'
	cRetMsg += STR0004 + FWEmpName(FWCodEmp()) //"Empresa: " 
	cRetMsg += '			<br>'
	cRetMsg += STR0005 + FWFilialName() //"Filial: "
	cRetMsg += '			<br>'
	cRetMsg += STR0006 + DtoC(Date()) //"Data: "
	cRetMsg += '			<br>'
	cRetMsg += STR0007 + Time() //"Hora: "
	cRetMsg += '		</p>'
	cRetMsg += '		<hr/>'
	cRetMsg += '		<p>'
	cRetMsg += STR0008 //"Um ou mais arquivos de NF-e recebidos via TOTVS Colabora็ใo apresentaram inconsist๊ncias durante o processamento."
	cRetMsg += STR0009 //"Tais arquivos foram marcados como inconsistentes e deixarใo de ser processados."
	cRetMsg += '			<br>'
	
	If IsInCallStack("MATA140I")
		cRetMsg += STR0010 //"Corrija as ocorr๊ncias listadas abaixo e providencie o reprocessamento destes arquivos atrav้s da rotina Pr้-nota, op็ใo Entrada Nf-e."
	Else
		cRetMsg += STR0011 //"Corrija as ocorr๊ncias listadas abaixo e providencie o reprocessamento destes arquivos no monitor TOTVS Colabora็ใo."
	Endif
	
	cRetMsg += '			<br><br>'
	cRetMsg += STR0012 //"* Estes arquivos nใo serใo reprocessados automaticamente."  
	cRetMsg += '		</p>'
	cRetMsg += '		<table style="text-align: left; width: 100%;" border="0" cellpadding="2" cellspacing="1">'
	cRetMsg += '			<thead>'
	cRetMsg += '				<tr>'
	cRetMsg += '					<th scope="col" style="background-color: gray; font-weight: bold; color: white" >'
	cRetMsg += STR0013 //"Arquivo"
	cRetMsg += '					</th>'
	cRetMsg += '					<th scope="col" style="background-color: gray; font-weight: bold; color: white" >'
	cRetMsg += STR0014 //"Ocorrencia"
	cRetMsg += '					</th>'
	cRetMsg += '					<th scope="col" style="background-color: gray; font-weight: bold; color: white" >'
	cRetMsg += STR0015 //"Solu็ใo"
	cRetMsg += '					</th>'
	cRetMsg += '				</tr>'
	cRetMsg += '			</thead>'
	cRetMsg += '			<tbody>'
	
	For nI := 1 To Len(aDados)
		cRetMsg += '				<tr>'
		cRetMsg += '					<td valign="center">'
		cRetMsg += 						aDados[nI,1]
		cRetMsg += '					</td>
		cRetMsg += '					<td valign="center">'
		cRetMsg += 						aDados[nI,2]
		cRetMsg += '					</td>
		cRetMsg += '					<td valign="center">'
		cRetMsg += 						aDados[nI,3]
		cRetMsg += '					</td>
		cRetMsg += '				</tr>'
	Next nI
	
	cRetMsg += '			</tbody>'
	cRetMsg += '		</table>'
	cRetMsg += '	</body>'
	cRetMsg += '</html>'

Elseif cEventId == "053" //Documento Processados
	cRetMsg := '<html>'
	cRetMsg += '	<body>'
	cRetMsg += '		<h3>'
	cRetMsg += '			<strong style="font-weight: bold; color: gray;">'
	cRetMsg += STR0016 //"NF-e disponํveis [TOTVS Colabora็ใo]"
	cRetMsg += '			</strong>'
	cRetMsg += '		</h3>'
	cRetMsg += '		<p>'
	cRetMsg += STR0004 + FWEmpName(FWCodEmp()) //"Empresa: " 
	cRetMsg += '			<br>'
	cRetMsg += STR0005 + FWFilialName() //"Filial: "
	cRetMsg += '			<br>'
	cRetMsg += STR0006 + DtoC(Date()) //"Data: "
	cRetMsg += '			<br>'
	cRetMsg += STR0007 + Time() //"Hora: "
	cRetMsg += '		</p>'
	cRetMsg += '		<hr/>'
	cRetMsg += '		<p>'
	
	If IsInCallStack("MATA140I")
		cRetMsg += STR0017 //"Um ou mais arquivos de NF-e foram recebidos via TOTVS Colabora็ใo e estใo disponํveis para gera็ใo de documento fiscal atrav้s da rotina Pr้-Nota op็ใo Entrada NF-e."
	Else
		cRetMsg += STR0018 //"Um ou mais arquivos de NF-e foram recebidos via TOTVS Colabora็ใo e estใo disponํveis para gera็ใo de documento fiscal no monitor TOTVS Colabora็ใo."
	Endif
	
	cRetMsg += '			<br><br>'
	cRetMsg += STR0012 //"* Estes arquivos nใo serใo reprocessados automaticamente."
	cRetMsg += '		</p>'
	cRetMsg += '		<table style="text-align: left; width: 100%;" border="0" cellpadding="2" cellspacing="1">'
	cRetMsg += '			<thead>'
	cRetMsg += '				<tr>'
	cRetMsg += '					<th scope="col" style="background-color: gray; font-weight: bold; color: white" >'
	cRetMsg += STR0019 //"Documento"
	cRetMsg += '					</th>'
	cRetMsg += '					<th scope="col" style="background-color: gray; font-weight: bold; color: white" >'
	cRetMsg += STR0020 //"Serie"
	cRetMsg += '					</th>'
	cRetMsg += '					<th scope="col" style="background-color: gray; font-weight: bold; color: white" >'
	cRetMsg += STR0021 //"Fornecedor"
	cRetMsg += '					</th>'
	cRetMsg += '					<th scope="col" style="background-color: gray; font-weight: bold; color: white" >'
	cRetMsg += STR0022 //"Filial"
	cRetMsg += '					</th>'
	cRetMsg += '				</tr>'
	cRetMsg += '			</thead>'
	cRetMsg += '			<tbody>'
	
	For nI := 1 To Len(aDados)
		cRetMsg += '				<tr>'
		cRetMsg += '					<td valign="center">'
		cRetMsg += 						aDados[nI,1]
		cRetMsg += '					</td>
		cRetMsg += '					<td valign="center">'
		cRetMsg += 						aDados[nI,2]
		cRetMsg += '					</td>
		cRetMsg += '					<td valign="center">'
		cRetMsg += 						aDados[nI,3]
		cRetMsg += '					</td>'
		If Len(aDados[nI]) > 3
			cRetMsg += '					<td valign="center">'
			cRetMsg += 						aDados[nI,4]
			cRetMsg += '					</td>
		Endif
		cRetMsg += '				</tr>'
	Next nI
	
	cRetMsg += '			</tbody>'
	cRetMsg += '		</table>'
	cRetMsg += '	</body>'
	cRetMsg += '</html>'
Endif

If lEditMsg
	cBkpMsg := cRetMsg
	
	cExecBlock:= "EVCOL"+Substr(cEventId,1,3)
	
	cRetMsg := ExecBlock(cExecBlock,.F.,.F.,{aDados,cRetMsg})
	
	If Valtype(cRetMsg) <> "C"
		cRetMsg := cBkpMsg
	EndIf
EndIf

Return cRetMsg

//-------------------------------------------------------------------
/*/{Protheus.doc} SCHEDREP
Chamada para reprocessar arquivos da CKO ao finalizar a tela do
reprocessar

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//------------------------------------------------------------------- 

Function SCHEDREP()

Local aEmpPro	:= {}
Local cQry		:= ""
Local cAliasQry	:= GetNextAlias()

cQry := " SELECT CKO_EMPPRO, CKO_FILPRO"
cQry += " FROM " + RetSqlName("CKO")
cQry += " WHERE CKO_FLAG = '0'"
cQry += " AND CKO_EMPPRO <> ' '"
cQry += " AND D_E_L_E_T_ = ' '"
cQry += " GROUP  BY CKO_EMPPRO,CKO_FILPRO"

cQry := ChangeQuery(cQry)

dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQry),cAliasQry,.T.,.T.)

While (cAliasQry)->(!Eof())
	aAdd(aEmpPro,{AllTrim((cAliasQry)->CKO_EMPPRO),AllTrim((cAliasQry)->CKO_FILPRO)})
	(cAliasQry)->(DbSkip())
Enddo

(cAliasQry)->(DbCloseArea())

If Len(aEmpPro) > 0
	StartJob("SCHEDEMP",GetEnvServer(),.F.,aEmpPro)
Endif

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} SCHEDEMP
Chamada para reprocessar arquivos da CKO por empresa/filial

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//------------------------------------------------------------------- 

Function SCHEDEMP(aParametro)

Local nI := 1

For nI := 1 To len(aParametro)
	RpcSetType(3)
	RpcSetEnv(aParametro[nI,1],aParametro[nI,2],,,'COM')
	
	SchedComCol()

	RpcClearEnv()
Next nI

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} SCHEDATUCKO
Atualiza novos campos da CKO (Doc, Serie, Nome Fornecedor)

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//------------------------------------------------------------------- 

Static Function SCHEDATUCKO(cFileAtu,cXmlAtu)

Local lCkoRepro		:= CKO->(FieldPos("CKO_DOC")) > 0 .And. CKO->(FieldPos("CKO_SERIE")) > 0 .And. CKO->(FieldPos("CKO_NOMFOR")) > 0 .And. !Empty(SDS->(IndexKey(4)))
Local lCkoEmp		:= CKO->(FieldPos("CKO_EMPPRO")) > 0 .And. CKO->(FieldPos("CKO_FILPRO")) > 0
Local lColGrvDados	:= FindFunction("COLGRVDADOS")
Local nTamCKOARQ	:= TamSX3("CKO_ARQUIV")[1]
Local aCkoDados		:= {}

cFileAtu := Padr(cFileAtu,nTamCKOARQ) 

If lCkoRepro .And. lColGrvDados
	aCkoDados := GetAdvFVal("CKO",{"CKO_DOC","CKO_SERIE","CKO_NOMFOR"},cFileAtu,1)
	If Len(aCkoDados) > 0 .And. (Empty(aCkoDados[1]) .Or. Empty(aCkoDados[2]) .Or. Empty(aCkoDados[3]))
		aCkoDados := COLGRVDADOS(cXmlAtu,1)
		If Len(aCkoDados) > 0
			CKO->(dbSetorder(1))
			If CKO->(DbSeek(cFileAtu))
				If RecLock("CKO",.F.)
					CKO->CKO_DOC	:= aCKODados[1]
					CKO->CKO_SERIE	:= aCKODados[2]
					CKO->CKO_NOMFOR	:= aCKODados[3]
					CKO->(MsUnlock())
				Endif
			Endif
		Endif
	Endif
Endif

If lCkoEmp .And. lColGrvDados
	aCkoDados := COLGRVDADOS(cXmlAtu,2)
	If Len(aCkoDados) > 0
		CKO->(dbSetorder(1))
		If CKO->(DbSeek(cFileAtu))
			If Empty(CKO->CKO_EMPPRO) .AND. Empty(CKO->CKO_FILPRO)
				If RecLock("CKO",.F.)
					CKO->CKO_EMPPRO	:= aCKODados[1]
					CKO->CKO_FILPRO	:= aCKODados[2]
					CKO->(MsUnlock())
				Endif
			Endif
		Endif
	Endif
Endif

Return

//-------------------------------------------------------------------
/*/{Protheus.doc} SCHEDATUEMP
Atualiza campos da CKO (Empresa / Filial)

@author	rodrigo.mpontes
@since		22/03/2019
@version	12.1.17
/*/
//------------------------------------------------------------------- 

Static Function SCHEDATUEMP()

Local cQry		:= ""
Local cXmlRet	:= ""
Local cTmpQry	:= GetNextAlias()

cQry := " SELECT CKO_ARQUIV"
cQry += " FROM " + RetSqlName("CKO")
cQry += " WHERE CKO_EMPPRO = ''"
cQry += " AND CKO_FILPRO = ''"
cQry += " AND CKO_FLAG = '0'"
cQry += " AND CKO_CODEDI IN ('109','214','273','319')"
cQry += " AND D_E_L_E_T_ = ' '"

cQry := ChangeQuery(cQry)
																			
dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQry),cTmpQry,.T.,.T.) 

If (cTmpQry)->(!EOF())
	While (cTmpQry)->(!EOF())
		cXmlRet := ""
		cXmlRet	:= GetAdvFVal("CKO","CKO_XMLRET",(cTmpQry)->CKO_ARQUIV,1)

		If !Empty(cXmlRet)
			SCHEDATUCKO((cTmpQry)->CKO_ARQUIV,cXmlRet)
		Endif
		(cTmpQry)->(DbSkip())
	Enddo
Endif

Return
