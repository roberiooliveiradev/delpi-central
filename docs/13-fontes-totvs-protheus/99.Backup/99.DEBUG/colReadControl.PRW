#INCLUDE "PROTHEUS.CH" 
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"  
#INCLUDE "PARMTYPE.CH"

#DEFINE FT_NAME	1 
#DEFINE FT_DATE	3
#DEFINE FT_TIME	4

Static __cDirIn		:= ""
Static __cDirLido	:= ""
Static __cDirOut	:= ""
Static __lGeraLog	:= .F.
Static lSOWin		:= !isSrvUnix() //Se é SO Windows
Static lCkoRepro  := CKO->(FieldPos("CKO_DOC")) > 0 .And. CKO->(FieldPos("CKO_SERIE")) > 0 .And. CKO->(FieldPos("CKO_NOMFOR")) > 0 .And. !Empty(SDS->(IndexKey(4)))
//------------------------------------------------------------------
/*/{Protheus.doc} colReadDocs
Raliza o controle de leitura dos documentos.

@author  Rafael Iaquinto
@since   30/01/2014
@version 12
/*/
//------------------------------------------------------------------
function colReadDocs()

local cBarra		:= If(!lSOWin,"/","\")
local cProcesso	:= "colabautoread"
local cLockFile 	:= ""
local cDirIn		:= Alltrim( GetNewPar("MV_NGINN","\Neogrid\bin\IN") )
local cDirOut		:= Alltrim( GetNewPar("MV_NGOUT","\Neogrid\bin\OUT") )
local cDirLido	:= Alltrim( GetNewPar("MV_NGLIDOS","\Neogrid\bin\LIDOS") )

local nX			:= 0
local nHdlJob		:= 0

__lGeraLog	:= getSrvProfString( "COLAUTOREAD_DEBUG" , "0" ) == "1" 

// Valida parametro MV_NGINN e MV_NGLIDOS
if Empty( Alltrim( cDirIn ) ) .Or. !ExistDir(cDirIn) 
	
	ColReadMsg( 'Parametro [ MV_NGINN ] nao configurado ou diretorio configurado nao existe.' )

elseif Empty( Alltrim( cDirLido ) ) .Or. !ExistDir( cDirLido )
	
	ColReadMsg( 'Parametro [ MV_NGLIDOS ] nao configurado ou diretorio configurado nao existe.'  )
	
else
	
	//-------------------------------------------
	// Inicializacao das variaveis
	//-------------------------------------------
	
	//Verifica os diretórios
	if SubStr( cDirIn, Len(cDirIn) )<> cBarra
		__cDirIn := cDirIn+cBarra
	Else
		__cDirIn := cDirIn
	endif
	if SubStr( cDirLido, Len(cDirLido) )<> cBarra
		__cDirLido := cDirLido+cBarra
	else
		__cDirLido := cDirLido
	endif
	
	if SubStr( cDirOut, Len(cDirOut) )<> cBarra
		__cDirOut := cDirOut+cBarra
	else
		__cDirOut := cDirOut
	endif
	
	cProcName	:= cProcesso
	cLockFile 	:= ""	
	
	//-------------------------------------------
	// Montagem do arquivo do job principal
	//-------------------------------------------
	cLockFile := lower( cProcName ) + ".lck"
	
	//---------------------------------------------
	// Verifica se a thread principal esta rodando
	//---------------------------------------------
	for nX := 1 To 2
	
		nHdlJob := JobSetRunning( cLockFile, .T. )

		If ( nHdlJob > 0 )
	
			ColReadMsg( "Iniciando o processo principal de " + cProcName ) 	
			colReadControl()
			
			//-------------------------------------------
			// Libera o Lock
			//-------------------------------------------

			JobSetRunning( cLockFile, .F., nHdlJob )		
			ColReadMsg( "Finalizando o processo principal de " + cProcName ) 
			
			Exit
				
		Else
			
			//-------------------------------------------
			// Thread principal em Lock
			//-------------------------------------------

			ColReadMsg( "Falha na inicialização do processo de " + cProcName + ", outro processo já iniciado." ) 			
			sleep( 3000 )
			
		Endif
	
	next
	
endif

return

//-------------------------------------------------------------------
/*/{Protheus.doc} colReadControl
Funcao que controla a execucao dos jobs dos processos do Schedule do 
TOTVS Colaboração.
  

@author  Rafael Iaquinto
@since   24/07/2014
@version 11.8
/*/
//-------------------------------------------------------------------
static function colReadControl( )

local aDocs		:= {}
Local aCodEdi	:= {"ALL"}
local nX		:= 0
local ny		:= 0
local cMsgProc	:= ""
Local lImpXML	:= SuperGetMv("MV_IMPXML",.F.,.F.) .And. CKO->(FieldPos("CKO_ARQXML")) > 0 .And. !Empty(CKO->(IndexKey(5)))

ColReadMsg( "JOB Iniciado" )
for nX := 1 to len(aCodEdi)
	
	aDocs	:= {}
	cMsgProc := ""
	// Executa o filtro no diretório
	aDocs := executeFilter( aCodEdi[nX] )
		
	if len( aDocs ) > 0 
		
		ColReadMsg( "Iniciando processamento dos arquivos - " + aCodEdi[nX] )
		for ny := 1 to len( aDocs )
			ColReadMsg( "Adicionando arquivo ["+ aDocs[ny][1] +"] a base de dados( Contagem: "+allTrim(str(ny))+" )" )
			
			if processaarquivo( aDocs[nY] ,@cMsgProc )
				ColReadMsg( "Arquivo ["+ aDocs[ny][1] +"] adicionado com sucesso." )
				
				ColReadMsg( "Movendo arquivo ["+ aDocs[ny][1] +"] para diretorio de arquivos lidos." )
				
				if (movearquivo(Iif(lImpXML,Iif(lSOWin,aDocs[nY][6],aDocs[nY][7]),aDocs[nY][FT_NAME]) , @cMsgProc))
					ColReadMsg( "Arquivo ["+ Iif(lImpXML,Iif(lSOWin,aDocs[nY][6],aDocs[nY][7]),aDocs[nY][FT_NAME]) +"] movido!"  )
				else
					ColReadMsg( "Arquivo ["+ Iif(lImpXML,Iif(lSOWin,aDocs[nY][6],aDocs[nY][7]),aDocs[nY][FT_NAME]) +"] não foi movido! " + cMsgProc )
				endif
			else
				ColReadMsg( "Arquivo ["+ aDocs[ny][1] +"] não foi adicionado - "+ cMsgProc  )
			endIf
		next ny
		
		ColReadMsg( "Finalizado processamento dos arquivos - "+ aCodEdi[nX]  )
	else
		ColReadMsg( "Sem documentos a serem processados!"  )	
	endif
	
next nx	
	
ColReadMsg( "JOB Finalizado" )

return

//-----------------------------------------------------------------------
/*/{Protheus.doc} executeFilter
Funcao Converte arquivo XML em String

@author  Rafael Iaquinto
@since   24.07.2014
@version 11.9

@param	cCodEdi	Codigo iniical do documento da neogrid, se for passado
					'ALL' será considerado todos e o fitro será *.xml.

@return aDocs 
/*/
//-----------------------------------------------------------------------
static function executeFilter( cCodEdi )

local cFiltro	:= ""
local aDocs		:= {}

If cCodEdi == "ALL"
	cFiltro := "*.xml"
Endif

aDocs := RetFileDir(__cDirIn, cFiltro, cCodEdi)

aSort(aDocs,,,{|x,y| DToC(x[3])+x[4] < DToC(y[3])+y[4]})

return aDocs
//-------------------------------------------------------------------
/*/{Protheus.doc} processaarquivo
Processa o arquivo passado, gravando na tabela CKO 

TOTVS Colaboração.

@param	 aDadosArq		Dados do arquivo retornado da função Directory.  
@param	 cMsg			Mensagem para retornar o erro caso ocorra algum.  

@return lOk			.T. se conseguir processar o arquivo.

@author  Rafael Iaquinto
@since   24/07/2014
@version 11.8
/*/
//-------------------------------------------------------------------
static function processaarquivo( aDadosArq, cMsg )

local lOk	:= .T.
local lNewReg	:= .T.
Local lGrvCKO	:= .T.
Local cEDI		:= ""
local nOrder1	:= 0
local nRecno1	:= 0
Local aCKODados	:= {}
Local aCodEdi	:= &(GetNewPar("MV_COLEDI",'{}'))
Local aExcEdi   := &(GetNewPar("MV_EXCEDI",'{}'))
Local aEdiCOM	:= {"109","214","273","319"}
Local cXMl		:= ""
Local cNameArq	:= ""
Local lImpXML	:= SuperGetMv("MV_IMPXML",.F.,.F.) .And. CKO->(FieldPos("CKO_ARQXML")) > 0 .And. !Empty(CKO->(IndexKey(5)))
Local lEdiCOM	:= .F.

if convfile( @cXMl, aDadosArq[FT_NAME],__cDirIn, @cMsg )
	nOrder1	:= CKO->( indexOrd() )
	nRecno1	:= CKO->( recno() )

	//Utilizando o Importador XML é realizada a conversão da nomenclatura do nome
	//do arquivo para que seja interpretado igual ao Totvs Colaboração.	
	If lImpXML
		aDadosArq := COLIMPXML(cXMl,@aDadosArq) 
	Endif

	cNameArq := PadR(Lower(aDadosArq[1]),Len(CKO->CKO_ARQUIV)) 
	
	If SubStr(cNameArq,Len(cNameArq)-3,4) <> ".xml"
		cNameArq := PadR(lower(SubStr(aDadosArq[1],1,26)+".xml"),LEN(CKO->CKO_ARQUIV))
	Endif
		
	CKO->(dbSetorder(1))
	if CKO->(dbseek(cNameArq))
		lNewReg	:= .F.
		lGrvCKO := Iif(CKO->CKO_FLAG<>'1',.T.,.F.)	
	Endif
	
	If lImpXML .And. Empty(aCodEdi)
		aCodEdi := {"109","214","273","005","252","203"}
	Endif
	// Verifica se tipo de XML está configurado para ser importado
	If !Empty(aCodEdi)
		If aScan(aCodEdi,{|x| AllTrim(x) == AllTrim(SubStr(cNameArq,1,3))}) == 0
			lGrvCKO := .F.
		Endif
	Endif
	// Verifica se tipo de XML não está configurado como excessão de importação
	If !Empty(aExcEdi)
		If aScan(aExcEdi,{|x| AllTrim(x) == AllTrim(SubStr(cNameArq,1,3))}) > 0
			lGrvCKO := .F.
			lOk     := .F.
			cMsg    := "Tipo de arquivo configurado para não ser processado (MV_EXCEDI)."
		EndIf
	EndIf

	If lGrvCKO
		cEDI := SubStr(cNameArq,1,3) 
		Begin Transaction
			
			reclock("CKO",lNewReg)
			CKO->CKO_ARQUIV	:= cNameArq
			CKO->CKO_CODEDI	:= cEDI
			CKO->CKO_XMLRET	:= cXMl
			CKO->CKO_DT_RET	:= aDadosArq[FT_DATE] //Data do arquivo
			CKO->CKO_HR_RET	:= aDadosArq[FT_TIME] //Hora do arquivo
			CKO->CKO_DT_IMP	:= Date() //Data da importacao pelo Schedule
			CKO->CKO_HR_IMP	:= Time() //Hora da importacao pelo Schedule
			CKO->CKO_STATUS	:= ColCKOStatus()[2][1]
			CKO->CKO_DESSTA	:= ColCKOStatus()[2][2]
			CKO->CKO_FLAG	:= "0"
			
			If lImpXML //Gravação do nome do arquivo original pelo Importador XML
				CKO->CKO_ARQXML := aDadosArq[6] 
			Endif

			lEdiCOM := (aScan(aEDICOM,{|x| x == cEDI}) > 0)

			If lCkoRepro .And. lEdiCOM
				aCKODados := COLGRVDADOS(cXML,1)
				If Len(aCKODados) > 0
					CKO->CKO_DOC	:= aCKODados[1]
					CKO->CKO_SERIE	:= aCKODados[2]
					CKO->CKO_NOMFOR	:= aCKODados[3]
				Endif
			Endif

			If lEdiCOM
				//Gravação Empresa/Filial
				aCKODados := COLGRVDADOS(cXML,2)
				If Len(aCKODados) > 0
					CKO->CKO_EMPPRO	:= aCKODados[1]
					CKO->CKO_FILPRO	:= aCKODados[2]
				Endif
			Endif
			CKO->( msUnlock() )
						
		End Transaction
	Endif	
	
	CKQ->( dbSetOrder( nOrder1 ) )
	CKQ->( dbGoTo( nRecno1 ) )
	
	MsUnLockAll()
else
	lOk := .F.
endif

return ( lOk )

//-------------------------------------------------------------------
/*/{Protheus.doc} COLIMPXML
Função para conversão do nome do arquivo XML para interpretar igual
ao Totvs Colaboração  

@param	cXML		Conteudo do XML
@param	aDadosArq	Dados do arquivo XML

@author  Rodrigo M Pontes
@since   24/04/19
@version 12.1.23
/*/
//-------------------------------------------------------------------

Static Function COLIMPXML(cXml,aDadosArq)

Local nPosPesq	:= 0
Local cXMLEncod	:= ""
Local cError	:= ""
Local cWarning	:= ""
Local cCodEdi	:= ""
Local aArea		:= GetArea()
local oFullXML	:= Nil
Local oXml252   := Nil
Local cXML252   := Nil
Local nTag      := 0
Local aEdiColab	:= {"203_"}
Local nEdiColab	:= 0

nEdiColab := aScan(aEdiColab,{|x| AllTrim(SubStr(aDadosArq[1],1,4)) == AllTrim(x)})

If nEdiColab == 0
	If SubStr(cXml,1,1) != "<"
		nPosPesq := At("<",cXml)
		cXml  := SubStr(cXml,nPosPesq,Len(cXml))		// Remove caracteres estranhos antes da abertura da tag inicial do arquivo
	EndIf

	cXMLEncod := EncodeUtf8(cXml)

	If Empty(cXMLEncod)
		cXMLEncod 	:= cXml
		cXml 		:= A140IRemASC(cXMLEncod)
		cXMLEncod 	:= EncodeUtf8(cXml)
	EndIf

	If !Empty(cXMLEncod)
		oFullXML := XmlParser(cXMLEncod,"_",@cError,@cWarning)
	EndIf

	//Verifica se estar importando uma NFE ou CTE
	If ValType(oFullXML) == "O"
		Do Case
			Case ValType(XmlChildEx(oFullXML,"_NFEPROC")) == "O" //-- Nota normal, devolucao, beneficiamento, bonificacao
				cCodEdi := "109_NFE_"
			Case ValType(XmlChildEx(oFullXML,"_CTE")) == "O" //-- Nota de transporte
				cCodEdi := "214_CTE_"		
			Case ValType(XmlChildEx(oFullXML,"_CTEPROC")) == "O" //-- Nota de transporte
				cCodEdi := "214_CTE_"
			Case ValType(XmlChildEx(oFullXML,"_CTEOSPROC")) == "O" //-- Nota de transporte CTEOS
				cCodEdi := "273_CTE_
			Case !Empty(AScan(ClassDataArr(oFullXML), {|Att| AllTrim(Upper(Att[1])) == "_BUSINESSCONTENT"})) .And. ValType(XmlChildEx(oFullXML:_BUSINESSCONTENT,"_CUSTOMERGOVINFO")) == "O" .And. ValType(XmlChildEx(oFullXML:_BUSINESSCONTENT,"_ORDERID")) == "O" //-- Pedido de Vendas
				cCodEdi := "005_PVD_"
			Case !Empty(AScan(ClassDataArr(oFullXML), {|Att| AllTrim(Upper(Att[1])) == "_BUSINESSCONTENT"})) .And. ValType(XmlChildEx(oFullXML:_BUSINESSCONTENT,"_FUNCMSGPROG")) == "O" //-- Programacao de Entrega
				cCodEdi := "252_PET_"
			Case !Empty(AScan(ClassDataArr(oFullXML), {|Att| AllTrim(Upper(Att[1])) == "_BUSINESSEVENT"}))
				cXml252 := cXMLEncod
				nTag := At('</BusinessEvent>',cXml252)
				If nTag <> 0
					cXml252 := SubStr(cXml252,nTag+16)
				EndIf
				oXML := XMLParser( cXml252, "_", @cError, @cWarning )
				If oXML <> Nil .And. ;
				Empty(cError) .And. ;
				Empty(cWarning) .And. ;
				!Empty(AScan(ClassDataArr(oXML), {|Att| AllTrim(Upper(Att[1])) == "_BUSINESSCONTENT"})) .And. ;
				ValType(XmlChildEx(oXML:_BUSINESSCONTENT,"_FUNCMSGPROG")) == "O" //-- Programacao de Entrega
					cCodEdi := "252_PET_"
				EndIf
		EndCase
	Endif

	//Busca pelo arquivo original, verificando se ja foi importado
	CKO->(DbSetOrder(5))
	If CKO->(dbseek(PadR(lower(aDadosArq[1]),LEN(CKO->CKO_ARQXML)))) .Or. CKO->(dbseek(PadR(upper(aDadosArq[1]),LEN(CKO->CKO_ARQXML)))) .Or. ;
		CKO->(dbseek(PadR(aDadosArq[1],LEN(CKO->CKO_ARQXML))))
		aAdd(aDadosArq,PadR(lower(aDadosArq[1]),LEN(CKO->CKO_ARQXML)))
		aAdd(aDadosArq,PadR((aDadosArq[1]),LEN(CKO->CKO_ARQXML)))	
		aDadosArq[1] := CKO->CKO_ARQUIV
	Else
		aAdd(aDadosArq,PadR(lower(aDadosArq[1]),LEN(CKO->CKO_ARQXML)))
		aAdd(aDadosArq,PadR((aDadosArq[1]),LEN(CKO->CKO_ARQXML)))	
		aDadosArq[1] := COLNUMSEQ(cCodEdi)
	Endif
Else
	aAdd(aDadosArq,PadR(lower(aDadosArq[1]),LEN(CKO->CKO_ARQXML)))
	aAdd(aDadosArq,PadR((aDadosArq[1]),LEN(CKO->CKO_ARQXML)))
Endif

RestArea(aArea)

oFullXML := Nil
oXML252  := Nil
DelClassIntF()

Return aDadosArq

//-------------------------------------------------------------------
/*/{Protheus.doc} COLNUMSEQ
Função para gerar nomenclatura do arquivo origem para nomenclatura
que seja interpretada igual ao Totvs Colaboração. 

@param	cCodEdi		Identificador do XML

@author  Rodrigo M Pontes
@since   24/04/19
@version 12.1.23
/*/
//-------------------------------------------------------------------

Static Function COLNUMSEQ(cCodEdi)

Local aArea		:= GetArea()
Local cAliasImp	:= GetNextAlias()
Local cNumSeq	:= "000000000000000001"
Local cArq		:= cCodEdi + cNumSeq + ".xml"
Local cQry		:= ""
Local cEdiQry	:= SubStr(cCodEdi,1,3)

cQry := " SELECT MAX(CKO_ARQUIV) AS ULT"
cQry += " FROM " + RetSqlName("CKO")
cQry += " WHERE CKO_CODEDI = '" + cEdiQry + "'"
cQry += " AND CKO_ARQXML <> '" + Space(TamSX3("CKO_ARQXML")[1]) + "'"
cQry += " AND D_E_L_E_T_ = ' '"

cQry := ChangeQuery(cQry)

dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQry),cAliasImp,.T.,.T.)

If (cAliasImp)->(!EOF()) .And. !Empty((cAliasImp)->ULT)
	cNumSeq := StrTran(Upper((cAliasImp)->ULT),".XML","")
	cNumSeq := StrTran(cNumSeq,cCodEdi,"")
	cNumSeq := Soma1(cNumSeq)
Endif

cArq := cCodEdi + cNumSeq + ".xml"

(cAliasImp)->(DbCloseArea())

RestArea(aArea)

Return cArq

//-----------------------------------------------------------------------
/*/{Protheus.doc} convfile
Funcao Converte arquivo XML em String

@author  Rafael Iaquinto
@since   24.07.2014
@version 11.9
/*/
//-----------------------------------------------------------------------
Static Function convfile(cXml,cFile,cDir,cMsg)

Local lRet	:= .T.
Local cLine	:= ""

PARAMTYPE 0 VAR cXml  AS CHARACTER
PARAMTYPE 1 VAR cDir  AS CHARACTER
PARAMTYPE 2 VAR cFile AS CHARACTER
PARAMTYPE 3 VAR cMsg  AS CHARACTER

If FT_FUse( cDir + cFile ) >= 0 

	cLine	:= ""
	cXml	:= ""
		
	While !FT_FEof() 
		cLine := FT_FReadLn()
		If ( Len(cLine) < 1023 )
			cXml += Alltrim(cLine)
		Else
			cLine := ""
			While .T.
				If ( Len(FT_fReadLn()) < 1023 )
					cLine	+= FT_FReadLn()
					cXml	+= cLine
					Exit
				Else
					cLine += FT_FReadLn()				
					FT_FSkip()
				Endif
			Enddo
		Endif
		FT_FSkip()
	Enddo
	
	//-- Fecha o arquivo aberto
	FT_FUSE()
	
	If "ObsContxCampo" $ cXML
		cXml := StrTran(cXml,"ObsContxCampo","ObsCont xCampo")
	Endif
	 	 
	If "ReferenceURI" $ cXml
		cXml := StrTran(cXml,"ReferenceURI","Reference URI") 
	Endif
				
Else
	
	lRet := .F.
	cMsg := "Nao foi possível ralizar a abertura do arquivo."
	
Endif
	
Return( lRet )

//-------------------------------------------------------------------
/*/{Protheus.doc} movearquivo
Move o arquivo passado, para a pasta de arquivos lidos. 

@param	 cNomeArq		Nome do arquivo.  
@param	 cMsg			Mensagem para retornar o erro caso ocorra algum.

@return lOk			.T. se conseguir processar o arquivo.

@author  Rafael Iaquinto
@since   24/07/2014
@version 11.8
/*/
//-------------------------------------------------------------------
static function movearquivo(cNomeArq , cMsg)

local lOk	:= .T.

if ( __CopyFile(__cDirIn+cNomeArq, __cDirLido+cNomeArq,,,lSOWin))
	Ferase( __cDirIn+cNomeArq,,lSOWin)
	
else
	lOk	:= .F.
	cMsg := "Não foi possível mover o arquivo.)	
endif

return lOk

//-------------------------------------------------------------------
/*/{Protheus.doc} ColReadMsg
Funcao que executa conout

@param cMessage		Mensagem que sera apresentada no conout

@author  Rafael Iaquinto
@since   25/07/2014
@version 11.8
/*/
//-------------------------------------------------------------------
function ColReadMsg( cMessage )

if ( __lGeraLog )
	
	conout( "[COLABORACAO " + DtoC( date() ) + " - " + time() + " ] " + allTrim(cMessage) + CRLF )		

endif 

return

//-------------------------------------------------------------------
/*/{Protheus.doc} RetFileDir
Função responsavel por retornar array com os arquivos encontrados no
diretorio.
Obs.: Foi realziado tratamento para linux para pegar maiuscula e 
minusculas

@param		cDiretorio	Diretorio com os arquivos
			cArquivo	Extensão dos arquivos
			cCodEdi		Prefixo ou tipo de arquivo a ser selecionado

@author		Felipe Sales Martinez
@since		10/03/2020
@version	12
@return		Lista de arquvios dentro do diretorio
/*/
//-------------------------------------------------------------------
Static Function RetFileDir(cDiretorio, cArquivo, cCodEdi )
Local aDocs		:= {}
Local aDocsSens	:= {}
Local lArqUp	:= .F.
Local lArqLow	:= .F.

cArquivo := AllTrim(cArquivo)

aDocs := Directory( cDiretorio+cArquivo ,,, lSOWin )

//Tratamento para Linux, case sensitive para a extensão
If !lSOWin .And. cCodEdi == "ALL"
	lArqUp	:= Upper(cArquivo) == cArquivo
	lArqLow	:= Lower(cArquivo) == cArquivo
	If lArqUp .Or. lArqLow
		cArquivo := iif(lArqUp,Lower(cArquivo),Upper(cArquivo))
		aDocsSens := Directory( __cDirIn+cArquivo ,,,lSOWin )
		//Copiando array para outro
		AEval( aDocsSens, {|x| aAdd(aDocs,aClone(x)) })
		//Limpando memoria
		AEval( aDocsSens, {|x| aSize(x,0) })
		aSize(aDocsSens, 0)
		aDocsSens := Nil
	EndIf
EndIf

Return aDocs

//-------------------------------------------------------------------
/*/{Protheus.doc} COLGRVDADOS
Pega informação de documento, serie e nome do fornecedor no XML

@param cMessage		XML
@param nOpc			1 (Doc/Serie/Fornecedor) / 2 (Empresa/Filial)

@author  Rodrigo.mpontes
@since   25/02/2020
@version 11.8
/*/
//-------------------------------------------------------------------

Function COLGRVDADOS(cXML,nOpc)

Local aArea		:= GetArea()
Local aRet		:= {}
Local oFullXML	:= Nil
Local cError	:= ""
Local cWarning	:= ""
Local cXMLEncod	:= ""
Local cDocXML	:= ""
Local cSerXML	:= ""
Local cForXML	:= ""
Local cCGC		:= ""
Local cIE		:= ""
Local cEmpCKO	:= ""
Local cFilCKO	:= ""
Local oXML		:= Nil
Local cTagToma3	:= ""
Local cTgTom3	:= ""
Local cTagRem  	:= ""
Local cTagDest 	:= ""
Local cIERem   	:= ""
Local cIEDest  	:= ""
Local cTagToma4	:= ""
Local cTagRec	:= ""
Local cTagExp	:= ""
Local cTagCGC	:= ""
Local aSM0      := {}
Local nX		:= 0
Local nQtdCNPJ	:= 0
Local nFilImp	:= 0
Local aFilInsc	:= {}
Local lInscDup	:= .F.
Local lCOLFILDUP:= ExistBlock("COLFILDUP")
Local lNFS		:= .F.

If !Empty(cXML)
	If SubStr(cXML,1,1) != "<"
		nPosPesq := At("<",cXML)
		cXML  := SubStr(cXML,nPosPesq,Len(cXML))
	EndIf

	cXMLEncod := EncodeUtf8(cXML)
	// Verifica se o encode ocorreu com sucesso, pois alguns caracteres especiais provocam erro na funcao de encode, neste caso e feito o tratamento pela funcao A140IRemASC
	If Empty(cXMLEncod)
		cXML 		:= A140IRemASC(cXML)
		cXMLEncod 	:= EncodeUtf8(cXML)
	EndIf

	If Empty(cXMLEncod)
		cXMLEncod := cXML
	EndIf
	
	If !Empty(cXMLEncod)
		oFullXML := XmlParser(cXMLEncod,"_",@cError,@cWarning)
	EndIf

	If nOpc == 1
		If Empty(cError) .And. !Empty(oFullXML)
			If ValType(XmlChildEx(oFullXML,"_INVOIC_NFE_COMPL")) == "O"
				cDocXML := oFullXML:_INVOIC_NFE_COMPL:_NFE_SEFAZ:_NFE:_INFNFE:_IDE:_NNF:Text
				cSerXML	:= oFullXML:_INVOIC_NFE_COMPL:_NFE_SEFAZ:_NFE:_INFNFE:_IDE:_SERIE:Text
				cForXML := oFullXML:_INVOIC_NFE_COMPL:_NFE_SEFAZ:_NFE:_INFNFE:_EMIT:_XNOME:Text
			Elseif ValType(XmlChildEx(oFullXML,"_NFEPROC")) == "O"
				cDocXML := oFullXML:_NFeProc:_NFe:_InfNfe:_Ide:_nNF:Text
				cSerXML	:= oFullXML:_NFeProc:_NFe:_InfNfe:_Ide:_Serie:Text
				cForXML := oFullXML:_NFeProc:_NFe:_InfNfe:_Emit:_xNome:Text
			Elseif ValType(XmlChildEx(oFullXML,"_CTEPROC")) == "O"
				cDocXML := oFullXML:_CteProc:_CTe:_InfCte:_Ide:_nCt:Text
				cSerXML	:= oFullXML:_CteProc:_CTe:_InfCte:_Ide:_Serie:Text
				cForXML := oFullXML:_CteProc:_CTe:_InfCte:_Emit:_xNome:Text
			Elseif ValType(XmlChildEx(oFullXML,"_CTEOSPROC")) == "O"
				cDocXML := oFullXML:_CteOsProc:_CTeOs:_InfCte:_Ide:_nCt:Text
				cSerXML	:= oFullXML:_CteOsProc:_CTeOs:_InfCte:_Ide:_Serie:Text
				cForXML := oFullXML:_CteOsProc:_CTeOs:_InfCte:_Emit:_xNome:Text
			Elseif ValType(XmlChildEx(oFullXML,"_PROCNEOGRIDNFSE")) == "O"
				cDocXML := oFullXML:_PROCNEOGRIDNFSE:_NEOGRID:_RETNEOGRIDNFSE:_NNFSE:TEXT
				cSerXML	:= ""
				cForXML := oFullXML:_PROCNEOGRIDNFSE:_NEOGRID:_NEOGRIDRPS:_RPS:_PRESTADOR:_RSOCIALPREST:TEXT
			Endif
 			aAdd(aRet,cDocXML)
			aAdd(aRet,cSerXML)
			aAdd(aRet,ALLTRIM(Upper(cForXML)))
		Endif
	Elseif nOpc == 2 //Empresa / Filial
		If Empty(cError) .And. !Empty(oFullXML)
			If ValType(XmlChildEx(oFullXML,"_INVOIC_NFE_COMPL")) == "O"
				If XmlChildEx(oFullXML:_INVOIC_NFE_COMPL:_NFE_SEFAZ:_NFE:_INFNFE:_DEST,"_CNPJ") # NIL
					cCGC := oFullXML:_INVOIC_NFE_COMPL:_NFE_SEFAZ:_NFE:_INFNFE:_DEST:_CNPJ:TEXT
				Elseif XmlChildEx(oFullXML:_INVOIC_NFE_COMPL:_NFE_SEFAZ:_NFE:_INFNFE:_DEST,"_CPF") # NIL
					cCGC := oFullXML:_INVOIC_NFE_COMPL:_NFE_SEFAZ:_NFE:_INFNFE:_DEST:_CPF:TEXT
				EndIf

				If XmlChildEx(oFullXML:_INVOIC_NFE_COMPL:_NFE_SEFAZ:_NFE:_INFNFE:_DEST,"_IE") # NIL
					cIE := oFullXML:_INVOIC_NFE_COMPL:_NFE_SEFAZ:_NFE:_INFNFE:_DEST:_IE:TEXT					
				EndIf
			Elseif ValType(XmlChildEx(oFullXML,"_NFEPROC")) == "O"
				
				If XmlChildEx(oFullXML:_NFeProc:_NFe:_InfNfe:_DEST,"_CNPJ") # NIL
					cCGC := oFullXML:_NFeProc:_NFe:_InfNfe:_DEST:_CNPJ:TEXT
				Elseif XmlChildEx(oFullXML:_NFeProc:_NFe:_InfNfe:_DEST,"_CPF") # NIL
					cCGC := oFullXML:_NFeProc:_NFe:_InfNfe:_DEST:_CPF:TEXT
				EndIf

				If XmlChildEx(oFullXML:_NFeProc:_NFe:_InfNfe:_DEST,"_IE") # NIL
					cIE := oFullXML:_NFeProc:_NFe:_InfNfe:_DEST:_IE:TEXT					
				EndIf

			Elseif ValType(XmlChildEx(oFullXML,"_CTEPROC")) == "O" .Or. ValType(XmlChildEx(oFullXML,"_CTEOSPROC")) == "O"
				If ValType(XmlChildEx(oFullXML,"_CTEPROC")) == "O"
					oXML := oFullXML:_CteProc:_CTe
				Elseif ValType(XmlChildEx(oFullXML,"_CTEOSPROC")) == "O"
					oXML := oFullXML:_CteOsProc:_CTeOs
				Endif

				cTagRem  	:= If(ValType(XmlChildEx(oXML:_InfCte,"_REM")) == "O", If(ValType(XmlChildEx(oXML:_InfCte:_Rem,"_CNPJ")) == "O","_CNPJ","_CPF"),"")
				cTagDest 	:= If(ValType(XmlChildEx(oXML:_InfCte,"_DEST")) == "O",If(ValType(XmlChildEx(oXML:_InfCte:_Dest,"_CNPJ")) == "O","_CNPJ","_CPF"),"")
				cIERem   	:= If(ValType(XmlChildEx(oXML:_InfCte,"_REM")) == "O", If(ValType(XmlChildEx(oXML:_InfCte:_Rem,"_IE")) == "O","_IE",""),"")
				cIEDest  	:= If(ValType(XmlChildEx(oXML:_InfCte,"_DEST")) == "O",If(ValType(XmlChildEx(oXML:_InfCte:_Dest,"_IE")) == "O","_IE",""),"")

				If ValType(XmlChildEx(oXML:_InfCte:_Ide,"_TOMA03")) <> "U"
					cTagToma3	:= AllTrim(oXML:_InfCte:_Ide:_Toma03:_TOMA:Text)
					cTgTom3	:= "_TOMA03"
				Elseif ValType(XmlChildEx(oXML:_InfCte:_Ide,"_TOMA3")) <> "U"
					cTagToma3	:= AllTrim(oXML:_InfCte:_Ide:_Toma3:_TOMA:Text)
					cTgTom3	:= "_TOMA3"
				Endif

				If ValType(XmlChildEx(oXML:_InfCte:_Ide,cTgTom3)) <> "U" 
					If cTagToma3 == "0" //Remetente
						If ValType(XmlChildEx(oXML:_InfCte:_Rem,cTagRem)) == "O"
							cCGC 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Rem,cTagRem):Text)
						EndIf
						
						If ValType(XmlChildEx(oXML:_InfCte:_Rem,cIERem)) == "O"
							cIE 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Rem,cIERem):Text)
						EndIf
					ElseIf cTagToma3 == "1" //Expedidor
						cTagExp := If(ValType(XmlChildEx(oXML:_InfCte:_Exped,"_CNPJ")) == "O","_CNPJ","_CPF")
						
						If ValType(XmlChildEx(oXML:_InfCte:_Exped,cTagExp)) == "O"
							cCGC 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Exped,cTagExp):Text)
						EndIf
						
						If ValType(XmlChildEx(oXML:_InfCte:_Exped,"_IE")) == "O"
							cIE 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Exped,"_IE"):Text)
						EndIf
					ElseIf cTagToma3 == "2" //Recebedor
						cTagRec := If(ValType(XmlChildEx(oXML:_InfCte:_Receb,"_CNPJ")) == "O","_CNPJ","_CPF")
						
						If ValType(XmlChildEx(oXML:_InfCte:_Receb,cTagRec)) == "O"
							cCGC 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Receb,cTagRec):Text)
						EndIf
						
						If ValType(XmlChildEx(oXML:_InfCte:_Receb,"_IE")) == "O"
							cIE 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Receb,"_IE"):Text)
						EndIf
					ElseIf cTagToma3 == "3" //Destinatario
						If ValType(XmlChildEx(oXML:_InfCte:_Dest,cTagDest)) == "O"
							cCGC 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Dest,cTagDest):Text)
						EndIF
						
						If ValType(XmlChildEx(oXML:_InfCte:_Dest,cIEDest)) == "O"
							cIE 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Dest,cIEDest):Text)			
						EndIF
					EndIf
				ElseIf ValType(XmlChildEx(oXML:_InfCte:_Ide,"_TOMA4")) <> "U"
					If AllTrim(oXML:_InfCte:_Ide:_Toma4:_TOMA:Text) == "4"
						cTagToma4 := If(ValType(XmlChildEx(oXML:_InfCte:_Ide:_Toma4,"_CNPJ")) == "O","_CNPJ","_CPF")
						
						If ValType(XmlChildEx(oXML:_InfCte:_Ide:_Toma4,cTagToma4)) == "O"
							cCGC 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Ide:_Toma4,cTagToma4):Text)
						EndIf
						
						If ValType(XmlChildEx(oXML:_InfCte:_Ide:_Toma4,"_IE")) == "O"
							cIE 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Ide:_Toma4,"_IE"):Text)
						EndIf
					EndIf
				Elseif ValType(XmlChildEx(oXML:_InfCte,"_TOMA")) <> "U"
					cTagCGC := If(ValType(XmlChildEx(oXML:_InfCte:_Toma,"_CNPJ")) == "O","_CNPJ","_CPF")
						
					If ValType(XmlChildEx(oXML:_InfCte:_Toma,cTagCGC)) == "O"
						cCGC 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Toma,cTagCGC):Text)
					EndIf
					
					If ValType(XmlChildEx(oXML:_InfCte:_Toma,"_IE")) == "O"
						cIE 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Toma,"_IE"):Text)
					EndIf
				Else //Se o xml não possui as tags Toma3 e Toma4, o documento será processado na filial do destinatario
					If ValType(XmlChildEx(oXML:_InfCte,"_DEST")) == "O" .And. ValType(XmlChildEx(oXML:_InfCte:_Dest,cTagDest)) == "O"
						cCGC 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Dest,cTagDest):Text)
					EndIF
					
					If ValType(XmlChildEx(oXML:_InfCte,"_DEST")) == "O" .And. ValType(XmlChildEx(oXML:_InfCte:_Dest,cIEDest)) == "O"
						cIE 	:= AllTrim(XmlChildEx(oXML:_InfCte:_Dest,cIEDest):Text)			
					EndIF
				EndIf
			Elseif ValType(XmlChildEx(oFullXML,"_PROCNEOGRIDNFSE")) == "O" 
				cCGC := oFullXML:_PROCNEOGRIDNFSE:_NEOGRID:_NEOGRIDRPS:_RPS:_TOMADOR:_CNPJTOM:TEXT
				lNFS := .T.
			Endif

			If !Empty(cCGC)
				aSM0       := FWLoadSM0()

				For nX := 1 To Len(aSM0)
					If cCGC $ aSM0[nX][SM0_CGC]
						nQtdCNPJ++
					EndIf
				Next nX

				If nQtdCNPJ == 1
					If (nFilImp := (ASCan(aSM0,{|x| AllTrim(x[SM0_CGC]) == cCgc }))) > 0
						cEmpCKO := AllTrim(aSM0[nFilImp][SM0_GRPEMP])				
						cFilCKO := AllTrim(aSM0[nFilImp][SM0_CODFIL])	
					Endif
				Elseif nQtdCNPJ > 1

					If !Empty(AllTrim(cIE))
						//FORCA O CONTEUDO ISENTO
						If "ISENT" $ cIE
							cIE := "ISENTO"
						EndIf  
					Else
						If !lNFS
							cIE := "ISENTO"
						Endif 
					EndIf
						
					aFilInsc := InscEstSM0(cCgc,cIE,@lInscDup)
					
					If !Empty(aFilInsc)
						cEmpCKO := aFilInsc[1]				
						cFilCKO := aFilInsc[2]
					Elseif Empty(aFilInsc) .And. lInscDup .And. lCOLFILDUP
						aFilInsc := ExecBlock("COLFILDUP",.F.,.F.,{cCgc,cIE})
						If ValType(aFilInsc) == "A" .And. Len(aFilInsc) == 2
							cEmpCKO := aFilInsc[1]				
							cFilCKO := aFilInsc[2] 
						Endif
					Endif
				Endif
			Endif

			aAdd(aRet,cEmpCKO)
			aAdd(aRet,cFilCKO)
		Endif
	Endif
Endif

RestArea(aArea)

oFullXML := Nil
DelClassIntF()

Return aRet
