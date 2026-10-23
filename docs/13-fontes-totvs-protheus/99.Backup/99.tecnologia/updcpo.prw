#include 'Totvs.ch'

/*/
{Protheus.doc} UPDCPO
Programa para atualização de campos de tipo numerico do Protheus.
Função similar à executada pelo compatibilizador UPDTAMCPO descontinuada pela Totvs a partir da versão 12.1.23.
Para utilização da rotina o usuário deverá executar em modo exclusivo.
Será solicitado que o usuário selecione a pasta com os arquivos para atualização de campos de valor unitario e campos de quantidade.
Após selecionar os arquivos o usuário deverá informar o tamanho, a quanti
dade de decimais e a mascara para os campos de valor unitario e, em seguida,
para os de quantidade.
@history 23/09/2019, Klaus Wolfgram, Construção inicial do fonte.
@history 25/01/2020, Thiago.Zoppi - Melhorias na rotinas, executar direto do smart, redefinir mascaras automaticas, validação dos valores.
/*/

Static _cArqVlr     := Space(200)
Static _cArqQtd     := Space(200)
Static _nTamVlr     := 16
Static _nDecVlr     := 6
Static _cPicVlr     := PADR('@E 999,999,999.999999',40)
Static _nTamQtd     := 16
Static _nDecQtd     := 6
Static _cPicQtd     := PADR('@E 999,999,999.999999',40)

//-------------------------------------------------------------------
/*/{Protheus.doc} function
Adicionado Execução sem interface
@author  Thiago.Zoppi
@Since   25/01/2020
/*/
//-------------------------------------------------------------------
User Function UPDCPO() //Altera o nome da user function
    
    Default cModulo :=  "SIGAESP"
    Default cNameFunction :=  "u_UPDCPOA" 

    if !empty(cModulo) .and. !empty(cNameFunction) 
        cModulo 	:=  cModulo 
        MsApp():New(cModulo) 
        oApp:cInternet := NIL     
        oApp:CreateEnv()
        PtSetTheme("OCEAN")
        oApp:cStartProg    	:= cNameFunction 
        oApp:lMessageBar	:= .T. 
        oApp:cModDesc		:= cModulo
        __lInternet 		:= .T.
        lMsFinalAuto 		:= .F.
        oApp:lMessageBar	:= .T. 
        oApp:Activate()
    endif

Return


User Function UPDCPOA()

	Local aBotoes[0]
	Local aTexto[0]
	Local bValid       :={|| fValid()}
	Local cTitulo      := 'Atualização de campos numéricos'
	Local nAltura      := 300
	Local nLargura     := 600
	Private oGetPicQtd := Nil
	Private oGetPicQtd := Nil
	Private oMainWnd   := NIL
	Private oProcess   := NIL

	//-- Definição do texto padrão para exibição na janela
	aadd(aTexto,'Programa personalizado para alteração de campos de valor unitário e quantidade.'           )
	aadd(aTexto,'Para utilização deste programa, clique no botão "Parâmetros" para indicar o arquivo'       )
	aadd(aTexto,'com a lista dos campos que serão atualizados e, Após isso, inidicar os ajustes'            )
	aadd(aTexto,'referentes a tamanho, quantidade de casas decimais e mascara para os campos de valor'      )
	aadd(aTexto,'e depois para os campos de quantidade.'                                                    )
	aadd(aTexto,'Clique no botão para confirmar assim que as demais opções forem parametrizadas e aguarde.' )

	//-- Definição dos botões
	aadd(aBotoes,{5, .T., {|| fParametros()}})
	aadd(aBotoes,{1, .T., {|| fProcessa(),FechaBatch()}})
	aadd(aBotoes,{2, .T., {|| FechaBatch()}})

	//-- Definição da tela principal
	FormBatch(cTitulo, aTexto, aBotoes, bValid, nAltura, nLargura)

Return

/*/
	Função auxiliar de validação.
	> Verifica se o usuário está no módulo configurador.
	> Verifica se o sistema está em modo exclusivo
/*/
Static Function fValid

    /*IF nModulo <> 99
        MsgStop('Essa funcionalidade só pode ser executada a partir do módulo configurador','fValid()')
        Return .F.
EndIF*/

Return .T.

/*/
Função auxiliar para preenchimento dos parâmetros da rotina
/*/
Static Function fParametros

    Local cMascara  := 'Arquivos ini|*.ini'
    Local cTitulo   := 'Escolha a pasta com os *.INI'
    Local cDirIni   := 'C:\'
    Local lSalvar   := .T.
    Local lArvore   := .F.
    Local lKeepCase := .T.
    Local nMascara  := 1
    Local nOpcao    := nOR( GETF_LOCALHARD, GETF_RETDIRECTORY)
    Local cTarget   := AllTrim(cGetFile(cMascara, cTitulo, nMascara, cDirIni, lSalvar, nOpcao, lArvore, lKeepCase))
    Local aFiles    := Directory(IIF(Substr(cTarget,Len(cTarget),1) = '\',cTarget + '*.ini',cTarget + '\*.ini'))
    Local x

    Local lVlrUni   := fVlrUnit()
    Local lQtd      := fVlrQtd()

	IF .Not. lVlrUni
        Return
	EndIF

	IF .Not. lQtd
        Return
	EndIF

	For x := 1 To Len(aFiles)

		IF 'campos_vunit.ini' $ Lower(aFiles[x,1])
            _cArqVlr := cTarget + aFiles[x,1]
		ElseIF 'campos_quant.ini' $ Lower(aFiles[x,1])
            _cArqQtd := cTarget + aFiles[x,1]
		EndIF

	Next

Return

/*/
Função auxiliar para exibir a janela de parametrização dos campos de valor unitario
/*/
Static Function fVlrUnit

    Local oDlg, oGrp, oSay, oGet, oBtn, nOpca := 0

    oDlg            := TDialog():New(001,001,250,300,"Campos de Valor Unitário",,,,,CLR_BLACK,CLR_WHITE,,,.T.)
    oGrp            := TGroup():New(005,005,095,145,'',oDlg,CLR_BLACK,CLR_WHITE,.T.)
    
    oSay            := TSay():New(015,010,{|| 'Tamanho' },oGrp,,,,,,.T.)
    oSay            := TSay():New(040,010,{|| 'Decimais'},oGrp,,,,,,.T.)
    oSay            := TSay():New(065,010,{|| 'Mascara' },oGrp,,,,,,.T.) 

    oGet            := TGet():New(025,010,{|u|if(Pcount()>0, _nTamVlr := u,_nTamVlr)}  ,oGrp,100,010,,{||.Not. Empty(_nTamVlr) .AND. valdPict('valor')  },,,,,,.T.,,,,,.T.,,,,,'_nTamVlr' ,,,,.T.)
    oGet            := TGet():New(050,010,{|u|if(Pcount()>0, _nDecVlr := u,_nDecVlr)}  ,oGrp,100,010,,{||.Not. Empty(_nDecVlr) .AND. valdPict('valor')},,,,,,.T.,,,,,.T.,,,,,'_nDecVlr' ,,,,.T.)
    oGetPicVal      := TGet():New(075,010,{|u|if(Pcount()>0, _cPicVlr := u,_cPicVlr)},oGrp,100,010,,{||.Not. Empty(_cPicVlr)},,,,,,.T.,,,,,.T.,,,,,'_cPicVlr' ,,,,.T.)

    oBtn            := TButton():New(100,010,"Confirmar", oDlg ,{|| IIF(valid('valor') ,(nOpca := 1,oDlg:end()),Nil)},45,12,,,,.T.,,'Confirmar')
    
    oBtn            := TButton():New(100,060,"Cancelar" , oDlg ,{|| IIF(.T.            ,(nOpca := 0,oDlg:end()),Nil)},45,12,,,,.T.,,'Cancelar' )

    
  ACTIVATE MSDIALOG oDlg CENTERED

Return .T.

/*/
Função auxiliar para exibir a janela de parametrização dos campos de quantidade
/*/
Static Function fVlrQtd

    Local oDlg, oGrp, oSay, oGet, oBtn, nOpca := 0

    oDlg            := TDialog():New(001,001,250,300,"Campos de Quantidade",,,,,CLR_BLACK,CLR_WHITE,,,.T.)
    oGrp            := TGroup():New(005,005,095,145,'',oDlg,CLR_BLACK,CLR_WHITE,.T.)
    
    oSay            := TSay():New(015,010,{|| 'Tamanho' },oGrp,,,,,,.T.)
    oSay            := TSay():New(040,010,{|| 'Decimais'},oGrp,,,,,,.T.)
    oSay            := TSay():New(065,010,{|| 'Mascara' },oGrp,,,,,,.T.) 

    oGet            := TGet():New(025,010,{|u|if(Pcount()>0, _nTamQtd := u,_nTamQtd)},oGrp,100,010,,{||.Not. Empty(_nTamQtd) .AND. valdPict('quantidade')},,,,,,.T.,,,,,.T.,,,,,'_nTamQtd' ,,,,.T.)
    oGet            := TGet():New(050,010,{|u|if(Pcount()>0, _nDecQtd := u,_nDecQtd)},oGrp,100,010,,{||.Not. Empty(_nDecQtd) .AND. valdPict('quantidade')},,,,,,.T.,,,,,.T.,,,,,'_nDecQtd' ,,,,.T.)
    oGetPicQtd      := TGet():New(075,010,{|u|if(Pcount()>0, _cPicQtd := u,_cPicQtd)},oGrp,100,010,,{||.Not. Empty(_cPicQtd)},,,,,,.T.,,,,,.T.,,,,,'_cPicQtd' ,,,,.T.)

    oBtn            := TButton():New(100,010,"Confirmar", oDlg ,{|| IIF(valid('quantidade') ,(nOpca := 1,oDlg:end()),Nil)},45,12,,,,.T.,,'Confirmar')
    oBtn            := TButton():New(100,060,"Cancelar" , oDlg ,{|| IIF(.T.                 ,(nOpca := 0,oDlg:end()),Nil)},45,12,,,,.T.,,'Cancelar' )
    
	 ACTIVATE MSDIALOG oDlg CENTERED

Return .T.

/*/
Função auxiliar para validação dos campos das janelas de parametrização
/*/
Static Function valid(cParam)

	IF cParam == 'valor'

		IF _nTamVlr = 0 .Or. _nDecvlr = 0 .Or. Empty(_cPicVlr)
            MSgStop('É necessário informar todos os campos.')
            Return .F.
		EndIF

	ElseIF cParam = 'quantidade'

		IF _nTamQtd = 0 .Or. _nDecQtd = 0 .Or. Empty(_cPicQtd)
            MSgStop('É necessário informar todos os campos.')
            Return .F.
		EndIF

	EndIF

Return .T.

/*/
Função auxiliar para processamento dos ajustes nos campos
/*/
Static Function fProcessa

    Private oProc := MsNewProcess():New({||fProcDic()},"Ajustando campos","Aguarde...",.F.)
    oProc:Activate()
    
Return

Static Function Mascara(cParam)
	Local aRet := ""
	IF cParam == 'valor'

		IF _nTamVlr = 0 .Or. _nDecvlr = 0 .Or. Empty(_cPicVlr)
           
		EndIF

	ElseIF cParam = 'quantidade'

		IF _nTamQtd = 0 .Or. _nDecQtd = 0 .Or. Empty(_cPicQtd)
            MSgStop('É necessário informar todos os campos.')
            Return .F.
		EndIF

	EndIF
    
Return .T. 


/*/
Função auxiliar para uso na regua de processamento
/*/
Static Function fProcDic

    Local lret := .T.

	IF Empty(_cArqQtd) .And. Empty(_cArqVlr)
        fParametros()
	EndIF

    lret := fCamposVlr(oProc)
    
	IF .Not. lret
        Return .F.
	EndIF

    lret := fCamposQtd(oProc)
    
	IF .Not. lret
        Return .F.
	EndIF

    MsgInfo('Fim do Processamento')

Return .T.

/*/
Função auxiliar para processamento dos ajustes nos campos de valor unitário
/*/
Static Function fCamposVlr(oProc)

    Local lret := .T.
    Local nHdl := 0
    Local nCampos := 0
    Local aCampos[0]
    Local x
    Local cCampo := ''

	IF Empty(_cArqVlr)
        Return .F.
	EndIF

	IF .Not. File(_cArqVlr)
        Return .F.
	EndIF

    nHdl := FT_FUSE(_cArqVlr)   

	IF nHdl <= 0
        Return .F.
	EndIF

    nCampos := FT_FLASTREC()

	While .Not. FT_FEOF()
        aadd(aCampos,FT_FREADLN())
        FT_FSKIP()
	Enddo

    FT_FUSE()    

    oProc:setRegua1(Len(aCampos))

	For x := 1 To Len(aCampos)

        oProc:incRegua1('Processando registro ' + cValToChar(x) + ' de ' + cValToChar(Len(aCampos)))

        cCampo := aCampos[x]
        lret := fAtualiza(cCampo,'valor')

		IF .Not. lret
            Return .F.
		EndIF

	Next

Return lret 

/*/
Função auxiliar para processamento dos campos de quantidade
/*/
Static Function fCamposQtd(oProc)

    Local lret := .T.
    Local nHdl := 0
    Local nCampos := 0
    Local aCampos[0]
    Local x

	IF Empty(_cArqQtd)
        Return .F.
	EndIF

	IF .Not. File(_cArqQtd)
        Return .F.
	EndIF

    nHdl := FT_FUSE(_cArqQtd)   

	IF nHdl <= 0
        Return .F.
	EndIF

    nCampos := FT_FLASTREC()

	While .Not. FT_FEOF()
        aadd(aCampos,FT_FREADLN())
        FT_FSKIP()
	Enddo

    FT_FUSE()   

    oProc:setRegua2(Len(aCampos))         

	For x := 1 To Len(aCampos)

        oProc:incRegua2('Processando registro ' + cValToChar(x) + ' de ' + cValToChar(Len(aCampos)))

        cCampo := aCampos[x]
        lret := fAtualiza(cCampo,'quantidade')

		IF .Not. lret
            Return .F.
		EndIF

	Next x

Return lret

/*/
Funcao auxiliar para atualização de campo
/*/
Static Function fAtualiza(cCampo,cTipo)

    Local nTam := 0
    Local nDec := 0
    Local cPic := ''

    Local nTamAux := 0
    Local nDecAux := 0
    Local cPicAux := ''

    Local cTabela := ''

    Default cCampo := ''
    Default cTipo := ''

    cTabela := Substr(cCampo,1,AT('_',cCampo) - 1)        
    cTabela := IF(Len(cTabela) = 2,'S' + cTabela, cTabela)

    SX3->(dbSetOrder(2))
    
	IF ! SX3->(dbSeek(cCampo))
        Return .T.
	EndIF

	IF cTipo == 'quantidade'
        nTam := _nTamQtd
        nDec := _nDecQtd
        cPic := _cPicQtd
	ElseIF cTipo == 'valor'
        nTam := _nTamVlr
        nDec := _nDecVlr
        cPic := _cPicVlr
	EndIF

	IF SX3->X3_TAMANHO = nTam .And. SX3->X3_DECIMAL = nDec
        Return .T.
	EndIF

    //Bloqueia alterações no Dicionário
	__SetX31Mode(.F.)   

	IF Select(cTabela) > 0
        (cTabela)->(dbCloseArea())
	EndIF

    nTamAux := SX3->X3_TAMANHO
    nDecAux := SX3->X3_DECIMAL
    cPicAux := SX3->X3_PICTURE

    SX3->(reclock('SX3',.F.))
        SX3->X3_TAMANHO := nTam
        SX3->X3_DECIMAL := nDec
        SX3->X3_PICTURE := cPic
    SX3->(msunlock())

    //Atualiza o Dicionário
	X31UpdTable(cTabela)  

    //Se houve Erro na Rotina
	If __GetX31Error()

        SX3->(reclock('SX3',.F.))
            SX3->X3_TAMANHO := nTamAux
            SX3->X3_DECIMAL := nDecAux
            SX3->X3_PICTURE := cPicAux
        SX3->(msunlock())

		cMsgAux := "Erro na atualização da tabela " + cTabela + CRLF
	    cMsgAux += __GetX31Trace()
		
        Aviso('Atenção', cMsgAux, {'OK'}, 3)

        Return .F.

	EndIf

    dbSelectArea(cTabela) 

    //Desbloqueia alterações no Dicionário
	__SetX31Mode(.T.)            

Return .T.

//-------------------------------------------------------------------
/*/{Protheus.doc} valdPict
Valida e altera Picture
@author  Thiago.Zoppi
date: "05/03/2021"
/*/
//-------------------------------------------------------------------
Static Function valdPict(cParam)
	Local aPict := {}
	Local lRet  := .F.

	IF cParam == 'valor'
		aPict := GeraPict(_nTamVlr,_nDecVlr,.F.)
	elseif cParam == 'quantidade'
		aPict := GeraPict(_nTamQtd,_nDecQtd,.F.)
	endif

	lRet  := aPict[1]

	IF lRet
		IF cParam == 'valor'
			_cPicVlr :=   aPict[2] ; oGetPicVal:Refresh()
		elseif cParam == 'quantidade'
			_cPicQtd :=   aPict[2] ; oGetPicQtd:Refresh()
		endif
	Else 
        MsgStop(aPict[3],"Valida Picture!")
    ENDIF


Return lret

//-------------------------------------------------------------------
/*/{Protheus.doc} GeraPict
Copia da Funcao AGRGerPic
@author  Thiago.Zoppi
@Since   "14/01/2020"
/*/
//-------------------------------------------------------------------

Static Function GeraPict(nTamTotal, nTamPrec, lTxt)
	Local aPict		:= {}
	Local nTam		 
	Local cPicture	:= "@E "
	Local nRestDiv
	Local lRet 		:= .T.
	Local nX
	Default lTxt	:= .F.

	Do Case

	Case Valtype(nTamTotal) != 'N' .Or. Valtype(nTamPrec) != 'N'
		lRet := .F.
		aAdd(aPict, .F.)
		aAdd(aPict, "")
		aAdd(aPict, "O método aceita valores numericos.")

	Case lRet .And. (nTamTotal < nTamPrec)
		lRet := .F.
		aAdd(aPict, .F.)
		aAdd(aPict, "")
		aAdd(aPict, "O tamanho total recebido esta com valor inferior ao valor da precisao.")

	Case lRet .And. (nTamTotal <= 0 .Or. nTamTotal > 16)
		lRet := .F.
		aAdd(aPict, .F.)
		aAdd(aPict, "")
		aAdd(aPict, "O tamanho total invalido.")

	Case lRet

		//Está sendo diminuido 1 do total pois virgula conta como uma posição na mascara
		If lTxt
			nTamTotal -= 1
		EndIf
		nTam 	 := nTamTotal - nTamPrec
		nRestDiv := Mod(nTam,3)
		For nX := 1 To nTam

			If nX == 1
				If nRestDiv = 1
					cPicture += '9'
				ElseIf nRestDiv = 2
					cPicture += '99'
				ElseIf nRestDiv == 0
					cPicture += '999'
				EndIf
			EndIf
			If nX != 1
				cPicture += '999'
			EndIf
			nX += 2 
			If nX < nTam
				cPicture += IIF(lTxt,"", ",")
			EndIf
		Next nX

		If nTamPrec != 0
			cPicture += "."
			cPicture := PadR(cPicture, Len(cPicture)+nTamPrec, "9")
		EndIf
		aAdd(aPict, .T.)
		aAdd(aPict, cPicture)
		aAdd(aPict, "Picture gerada com sucesso.")

	EndCase

	If Empty(aPict)
		aAdd(aPict, .F.)
		aAdd(aPict, "")
		aAdd(aPict, "Erro nao tratado.")
	EndIf

Return aPict
