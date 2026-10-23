
#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"
//#include "Directry.ch"

User Function FiltroF3(cTitulo,cQuery,nTamCpo,cAlias,cCodigo,cCpoChave,cTitCampo,cMascara,cRetCpo,nColuna)
    /*
	+------------------+------------------------------------------------------------+
	!Modulo            ! Diversos                                                   !
	+------------------+------------------------------------------------------------+
	!Nome              ! FiltroF3                                                   !
	+------------------+------------------------------------------------------------+
	!Descricao         ! Função usada para criar uma Consulta Padrão  com SQL       !
	!			       !                                                            !
	!			       !                                                            !
	+------------------+------------------------------------------------------------+
	!Autor             ! Rodrigo Lacerda P Araujo                                   !
	+------------------+------------------------------------------------------------+
	!Data de Criacao   ! 03/01/2013                                                 !
	+------------------+-----------+------------------------------------------------+
	!Campo             ! Tipo	   ! Obrigatorio                                    !
	+------------------+-----------+------------------------------------------------+
	!cTitulo           ! Caracter  !                                                !
	!cQuery            ! Caracter  ! X                                              !
	!nTamCpo           ! Numerico  !                                                !
	!cAlias            ! Caracter  ! X                                              !
	!cCodigo           ! Caracter  !                                                !
	!cCpoChave         ! Caracter  ! X                                              !
	!cTitCampo         ! Caracter  ! X                                              !
	!cMascara          ! Caracter  !                                                !
	!cRetCpo           ! Caracter  ! X                                              !
	!nColuna           ! Numerico  !                                                !
	+------------------+-----------+------------------------------------------------+
	!Parametros:                                                                  !
	!==========		                                                        !
	!          																			   !
	!cTitulo = Titulo da janela da consulta                                         !
	!cQuery  = A consulta SQL que vem do parametro cQuery não pode retornar um outro!
	!nome para o campo pesquisado, pois a rotina valida o nome do campo real        !
	!          																			   !
	!Exemplo Incorreto                                                              !
	!cQuery := "SELECT A1_NOME 'NOME', A1_CGC 'CGC' FROM SA1010 WHERE D_E_L_E_T_='' !
	!          																			   !
	!Exemplo Certo                                                                  !
	!cQuery := "SELECT A1_NOME, A1_CGC FROM SA1010 WHERE D_E_L_E_T_=''              !
	!          																			   !
	!Deve-se manter o nome do campo apenas.                                         !
	!          																			   !
	!nTamCpo   = Tamanho do campo de pesquisar,se não informado assume 30 caracteres!
	!cAlias    = Alias da tabela, ex: SA1                                           !
	!cCodigo   = Conteudo do campo que chama o filtro                               !
	!cCpoChave = Nome do campo que será utilizado para pesquisa, ex: A1_CODIGO      !
	!cTitCampo = Titulo do label do campo                                           !
	!cMascara  = Mascara do campo, ex: "@!"                                         !
	!cRetCpo   = Campo que receberá o retorno do filtro                             !
	!nColuna   = Coluna que será retornada na pesquisa, padrão coluna 1             !
	+--------------------------------------------------------------------------------
    */

    Local nLista
    Local cCampos 	:= ""
    Local bCampo		:= {}
    Local nCont		:= 0
    Local bTitulos	:= {}
    Local aCampos 	:= {}
    Local cTabela
    Local cCSSGet		:= "QLineEdit{ border: 1px solid gray;border-radius: 3px;background-color: #ffffff;selection-background-color: #3366cc;selection-color: #ffffff;padding-left:1px;}"
    Local cCSSButton 	:= "QPushButton{background-repeat: none; margin: 2px;background-color: #ffffff;border-style: outset;border-width: 2px;border: 1px solid #C0C0C0;border-radius: 5px;border-color: #C0C0C0;font: bold 12px Arial;padding: 6px;QPushButton:pressed {background-color: #ffffff;border-style: inset;}"
    Local cCSSButF3	:= "QPushButton {background-color: #ffffff;margin: 2px;border-style: outset;border-width: 2px;border: 1px solid #C0C0C0;border-radius: 3px; border-color: #C0C0C0;font: Normal 10px Arial;padding: 3px;} QPushButton:pressed {background-color: #e6e6f9;border-style: inset;}"
    lOCAL nX
    Default cTitulo 	:= ""
    Default cCodigo 	:= ""
    Default nTamCpo 	:= 30
    Default _nColuna 	:= 1
    Default cTitCampo	:= RetTitle(cCpoChave)
    Default cMascara	:= PesqPict('"'+cAlias+'"',cCpoChave)

    Private _oLista	:= nil
    Private _oDlg 	:= nil
    Private _oCodigo
    Private _cCodigo
    Private _aDados 	:= {}
    Private _nColuna	:= 0



    _nColuna	:= nColuna

    If Empty(cAlias) .OR. Empty(cCpoChave) .OR. Empty(cRetCpo) .OR. Empty(cQuery)
        MsgStop("Os parametro cQuery, cCpoChave, cRetCpo e cAlias s�o obrigatorios!","Erro")
        Return
    Endif

    _cCodigo := Space(nTamCpo)
    _cCodigo := cCodigo

    cTabela:= CriaTrab(Nil,.F.)
    DbUseArea(.T.,"TOPCONN", TCGENQRY(,,cQuery),cTabela, .F., .T.)

    (cTabela)->(DbGoTop())
    If (cTabela)->(Eof())
        MsgStop("N�o h� registros para serem exibidos!","Aten��o")
        Return
    Endif

    Do While (cTabela)->(!Eof())
        /*Cria o array conforme a quantidade de campos existentes na consulta SQL*/
        cCampos	:= ""
        aCampos 	:= {}
        For nX := 1 TO FCount()
            bCampo := {|nX| Field(nX) }
            If ValType((cTabela)->&(EVAL(bCampo,nX)) ) <> "M" .OR. ValType((cTabela)->&(EVAL(bCampo,nX)) ) <> "U"
                if ValType((cTabela)->&(EVAL(bCampo,nX)) )=="C"
                    cCampos += "'" + (cTabela)->&(EVAL(bCampo,nX)) + "',"
                ElseIf ValType((cTabela)->&(EVAL(bCampo,nX)) )=="D"
                    cCampos +=  DTOC((cTabela)->&(EVAL(bCampo,nX))) + ","
                ElseIf ValType((cTabela)->&(EVAL(bCampo,nX)) )=="N"
                    cCampos +=  CVALTOCHAR((cTabela)->&(EVAL(bCampo,nX))) + ","
                Else
                    cCampos +=  (cTabela)->&(EVAL(bCampo,nX)) + ","
                Endif

                aadd(aCampos,{EVAL(bCampo,nX),Alltrim(RetTitle(EVAL(bCampo,nX))),"LEFT",30})
            Endif
        Next nX

        If !Empty(cCampos)
            cCampos 	:= Substr(cCampos,1,len(cCampos)-1)
            aAdd( _aDados,&("{"+cCampos+"}"))
        Endif

        (cTabela)->(DbSkip())
    Enddo

    DbCloseArea(cTabela)

    If Len(_aDados) == 0
        MsgInfo("N�o h� dados para exibir!","Aviso")
        Return
    Endif

    nLista := aScan(_aDados, {|x| alltrim(x[1]) == alltrim(_cCodigo)})

    iif(nLista = 0,nLista := 1,nLista)

    //  Define MsDialog _oDlg Title "Consulta Padr�o" + IIF(!Empty(cTitulo)," - " + cTitulo,"") From 0,0 To 280, 500 Of oMainWnd Pixel
    nVar1 := 280
    nVar2 := 600
    //nVar2 := 500
    conout("teste")
    Define MsDialog _oDlg Title "Consulta Padr�o" + IIF(!Empty(cTitulo)," - " + cTitulo,"") From 0,0 To nVar1, nVar2 Of oMainWnd Pixel

    oCodigo:= TGet():New( 003, 005,{|u| if(PCount()>0,_cCodigo:=u,_cCodigo)},_oDlg,205, 010,cMascara,{|| /*Processa({|| FiltroF3P(M->_cCodigo)},"Aguarde...")*/ },0,,,.F.,,.T.,,.F.,,.F.,.F.,,.F.,.F.,"",_cCodigo,,,,,,,cTitCampo + ": ",1 )
    oCodigo:SetCss(cCSSGet)
    //  oButton1 := TButton():New(010, 212," &Pesquisar ",_oDlg,{|| Processa({|| FiltroF3P(M->_cCodigo) },"Aguarde...") },037,013,,,.F.,.T.,.F.,,.F.,,,.F. )
    oButton1 := TButton():New(010, 252," &Pesquisar ",_oDlg,{|| Processa({|| FiltroF3P(M->_cCodigo) },"Aguarde...") },037,013,,,.F.,.T.,.F.,,.F.,,,.F. )
    oButton1:SetCss(cCSSButton)
    //bkp coordenadas26,05,245,90
    nVar1 := 26
    nVar2 := 05
    nVar3 := 286
    nVar4 := 90

    _oLista:= TCBrowse():New(nVar1,nVar2,nVar3,nVar4,,,,_oDlg,,,,,{|| _oLista:Refresh()},,,,,,,.F.,,.T.,,.F.,,,.f.)
    nCont := 1
    //Para ficar dinâmico a criação das colunas, eu uso macro substituição "&"
    For nX := 1 to len(aCampos)
        cAliTMP :=  getsx3cache(aCampos[nx][1],"X3_ARQUIVO")
        // IF substr(aCampos[nx][1],1,3) $ "DA0"
        //     cAliTMP := substr(aCampos[nx][1],1,3)
        // ELSE
        //     cAliTMP := cAlias
        // ENDIF
        cColuna := &('_oLista:AddColumn(TCColumn():New("'+aCampos[nX,2]+'", {|| _aDados[_oLista:nAt,'+StrZero(nCont,2)+']},PesqPict("'+cAlias+'","'+aCampos[nX,1]+'"),,,"'+aCampos[nX,3]+'", '+StrZero(aCampos[nX,4],3)+',.F.,.F.,,{|| .F. },,.F., ) )')
        nCont++
    Next
    _oLista:SetArray(_aDados)
    _oLista:bWhen 		 := { || Len(_aDados) > 0 }
    _oLista:bLDblClick  := { || FiltroF3R(_oLista:nAt, _aDados, cRetCpo)  }
    _oLista:Refresh()

    oButton2 := TButton():New(122, 005," OK "			,_oDlg,{|| Processa({|| FiltroF3R(_oLista:nAt, _aDados, cRetCpo) },"Aguarde...") },037,012,,,.F.,.T.,.F.,,.F.,,,.F. )
    oButton2:SetCss(cCSSButton)
    oButton3 := TButton():New(122, 047," Cancelar "	,_oDlg,{|| _oDlg:End() },037,012,,,.F.,.T.,.F.,,.F.,,,.F. )
    oButton3:SetCss(cCSSButton)

    Activate MSDialog _oDlg Centered
Return(bRet)

Static Function FiltroF3P(cBusca)
    Local i := 0

    if !Empty(cBusca)
        For i := 1 to len(_aDados)
            //Aqui busco o texto exato, mas pode utilizar a função AT() para pegar parte do texto
            if UPPER(Alltrim(_aDados[i,_nColuna]))==UPPER(Alltrim(cBusca))
                //Se encontrar me posiciono no grid e saio do "For"
                _oLista:GoPosition(i)
                _oLista:Setfocus()
                exit
            Endif
        Next
    Endif
Return

Static Function FiltroF3R(nLinha,aDados,cRetCpo)
    //  Local oModel     := FWMODELACTIVE()
    //  Local oView     := FWViewActive()
    //  Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    cCodigo := aDados[nLinha,_nColuna]

    &(cRetCpo) := cCodigo //Uso desta forma para campos como tGet por exemplo.
    if type("lAIB") == "L"
        IF lAIB
            fSetInfo(aDados[nLinha])
        ENDIF
    ENDIF
    if type("lParam") == "L"
        IF lParam

            dbSelectArea("SZ7")
            SZ7->(dbSetOrder(2))

            SZ7->(dBSeek(xFilial("SZ7")+cCodigo))

        ENDIF
    ENDIF
    // aCpoRet[1] := cCodigo //Não esquecer de alimentar essa variável quando for f3 pois ela e o retorno
    //   oModelSZ8:SETVALUE("Z8_IDSZ7",cCodigo)
    //   oModelSZ8:LoadValue("Z8_IDSZ7",cCodigo)
    bRet := .T.
    //   oView:Refresh("SZ8MASTER")
    _oDlg:End()
Return

//User Function ZZLF3()
User Function SZ7F3(nOpc)
    Local aArea := GetArea()
    Local cTitulo		:= "Planilhas"
    Local cQuery		:= "" 								//obrigatorio
    Local cAlias		:= "SZ7"							//obrigatorio
    Local cCpoChave	    := "Z7_ID" 					//obrigatorio
    Local cTitCampo	    := RetTitle(cCpoChave)			//obrigatorio
    Local cMascara	    := PesqPict(cAlias,cCpoChave)	//obrigatorio
    Local nTamCpo		:= TamSx3(cCpoChave)[1]
    Local cRetCpo		:= "M->Z8_IDSZ7"					//obrigatorio
    Local nColuna		:= 1
    LOCAL cEol          := CHR(10)
    lOCAL nTotal := 0
    Local cCodigo		:= M->Z8_IDSZ7		//pego o conteudo e levo para minha consulta padrão
    Private bRet 		:= .F.

    Private lParam  := .F.
    DEFAULT nOpc := 1

    if nOpc == 1

        cRetCpo		:= "M->Z8_IDSZ7"
        cCodigo		:= M->Z8_IDSZ7

    elseif nOpc == 2
        cRetCpo		:= "M->BZ_YIDSZ7"

        cCodigo := M->BZ_YIDSZ7
    elseif nOpc == 3

        cRetCpo	:= "M->MV_PAR04"
        cCodigo := M->MV_PAR04
        lParam  := .T.

    endif
    //Monto minha consulta, neste caso quero retornar apenas uma coluna, mas poderia inserir outros campos para compor outras colunas no grid, lembrando que não posso utilizar um alias para o nome do campo, deixar o nome real.
    //Posso fazer qualquer tipo de consulta, usando INNER, GROUPY BY, UNION's etc..., desde que mantenha o nome dos campos no SELECT.

    cQuery :=" SELECT DISTINCT  Z7_ID, Z7_DESCPLN " + cEol
    cQuery +="    FROM dbo."+RetSQLName("SZ7") + " SZ7 " + cEol
    cQuery +="WHERE SZ7.D_E_L_E_T_ = '' AND Z7_STACALC != 'I' " + cEol
    cQuery +="ORDER BY 1 "


    If Select("QRYTMP") <> 0
        dbSelectArea("QRYTMP")
        dbCloseArea()
    EndIf


    TCQuery cQuery New Alias "QRYTMP"

    //Contando os registros e voltando ao topo da query
    Count To nTotal

    IF nTotal == 0
        cQuery := "SELECT  TOP 1 SPACE ("+getsx3cache("Z7_ID","X3_TAMANHO")+") Z7_ID,SPACE ("+getsx3cache("Z7_DESCPLN","X3_TAMANHO")+")  Z7_DESCPLN " + cEol
        cQuery += " FROM dbo."+RetSQLName("SZ7") + "SZ7 WHERE 1=1 "
    ENDIF

    CONOUT("TESTE")
    QRYTMP->(DbCloseArea())
    bRet := U_FiltroF3(cTitulo,cQuery,nTamCpo,cAlias,cCodigo,cCpoChave,cTitCampo,cMascara,cRetCpo,nColuna)
    RestArea(aArea)
Return(bRet)

User Function SZ7F3RET(nOpc)

    DEFAULT nOpc := 1

    if nOpc == 1

        xRet := M->Z8_IDSZ7

    elseif nOpc == 2

        xRet := M->BZ_YIDSZ7

    elseif nOpc == 3

        xRet := SZ7->Z7_ID
        conout("stop")
    endif
reTURN(xRet )


User FUnction DA1F3()
    Local aArea := GetArea()
    Local cTitulo		:= "Tabela de Preco"
    Local cQuery		:= "" 								//obrigatorio
    Local cAlias		:= "DA1"							//obrigatorio
    Local cCpoChave	    := "DA1_CODTAB" 					//obrigatorio
    Local cTitCampo	    := RetTitle(cCpoChave)			//obrigatorio
    Local cMascara	    := PesqPict(cAlias,cCpoChave)	//obrigatorio
    Local nTamCpo		:= TamSx3(cCpoChave)[1]
    Local cRetCpo		:= "M->Z8_CDTABVN"					//obrigatorio
    Local nColuna		:= 1
    LOCAL cEol          := CHR(10)
    Local cCodigo		:= M->Z8_CDTABVN		//pego o conteudo e levo para minha consulta padrão
    Local aArea      := GetArea()
    lOCAL nTotal := 0
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local nTamPrd    := GetSx3cache("B1_COD","X3_TAMANHO")
    Local cSQL := ""

    Private bRet 		:= .F.

    //Monto minha consulta, neste caso quero retornar apenas uma coluna, mas poderia inserir outros campos para compor outras colunas no grid, lembrando que não posso utilizar um alias para o nome do campo, deixar o nome real.
    //Posso fazer qualquer tipo de consulta, usando INNER, GROUPY BY, UNION's etc..., desde que mantenha o nome dos campos no SELECT.

    cCodPro :=padr( oModelSZ8:getvalue("Z8_COD"),nTamPrd)

    if empty(cCodPro)
        MsgInfo("Gentileza preencher o Codigo do Produto antes de selecionar a Consulta","Tabela de Preco de Venda")
        Return(.f.)
    endif
    cSQL :=" SELECT  DISTINCT DA1_CODTAB ,DA0_DESCRI, DA1_PRCVEN " + cEol
    cSql +="FROM dbo." + retsqlname("DA0") + " DA0 (NOLOCK) " + cEol
    cSql +="    JOIN dbo." + retsqlname("DA1") + " DA1 (NOLOCK) " + cEol
    cSql +="        ON DA1.D_E_L_E_T_ = '' " + cEol
    cSql +="           AND DA1.DA1_FILIAL = DA0.DA0_FILIAL " + cEol
    cSql +="           AND DA1.DA1_CODTAB = DA0.DA0_CODTAB " + cEol
    cSql +="WHERE DA0.D_E_L_E_T_ = '' " + cEol

    cSql +="      AND DA1.DA1_CODPRO =  "+valtosql(cCodPro) + cEol
    cSql +="	  AND   DA0.DA0_ATIVO != '2'  " + cEol
    cSql +="	  AND  NOT(   DA0.DA0_DATATE < "+valtosql(dDataBase) + cEol
    cSql +="                         AND DA0.DA0_DATATE != '') " + cEol
    cSql +="						 ORDER BY 1 "

    CONOUT(cSql)
    cQuery := cSql


    If Select("QRYTMP") <> 0
        dbSelectArea("QRYTMP")
        dbCloseArea()
    EndIf

    TCQuery cQuery New Alias "QRYTMP"

    //Contando os registros e voltando ao topo da query
    Count To nTotal

    IF nTotal == 0
        cQuery := "SELECT  TOP 1 SPACE ("+VALTOSQL(getsx3cache("DA1_CODTAB","X3_TAMANHO"))+") DA1_CODTAB, "+ cEol
        cQuery += " SPACE ("+VALTOSQL(getsx3cache("DA0_DESCRI","X3_TAMANHO"))+")  DA0_DESCRI ," + cEol
        cQuery += " 0.00  DA1_PRCVEN " + cEol
        cQuery += " FROM dbo."+RetSQLName("DA0") + " DA0 WHERE 1=1 "
    ENDIF
    QRYTMP->(DbCloseArea())
    bRet := U_FiltroF3(cTitulo,cQuery,nTamCpo,cAlias,cCodigo,cCpoChave,cTitCampo,cMascara,cRetCpo,nColuna)

    RestArea(aArea)
Return(bRet)


User Function DA1F3RET()


reTURN(M->Z8_CDTABVN)


User FUnction AIBF3()
    Local aArea := GetArea()
    Local cTitulo		:= "Tabela de Preco Compra"
    Local cQuery		:= "" 								//obrigatorio
    Local cAlias		:= "AIB"							//obrigatorio
    Local cCpoChave	    := "AIB_CODTAB" 					//obrigatorio
    Local cTitCampo	    := RetTitle(cCpoChave)			//obrigatorio
    Local cMascara	    := PesqPict(cAlias,cCpoChave)	//obrigatorio
    Local nTamCpo		:= TamSx3(cCpoChave)[1]
    Local cRetCpo		:= "M->Z9_TABPRCC"					//obrigatorio
    Local nColuna		:= 1
    LOCAL cEol          := CHR(10)
    Local cCodigo		:= M->Z9_TABPRCC		//pego o conteudo e levo para minha consulta padrão
    Local aArea      := GetArea()
    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local nTamPrd    := GetSx3cache("B1_COD","X3_TAMANHO")
    Local oModelSZ91 := oModel:GetModel("SZ9DETAIL01")
    Local cSQL := ""
    Local    lSb1 := .f.
    Private bRet 		:= .F.
    Private lAIB := .t.
    cProd    := padr(trim( oModelSZ91:GETVALUE("Z9_CDPROD")),nTamPrd)

    //B1_TPMAT 1=Nao;2=Sim
    DBSELECTAREA("SB1")
    SB1->(dbSetOrder(1))
    SB1->(MsSeek(xFilial("SB1")+cProd))
    if 	SB1->(Found()) .and. SB1->B1_TIPO $ "MP" .AND. SB1->B1_TPMAT $ "1"
        lSb1 := .t.
    ENDIF
    if !lSb1
        MsgInfo("Consulta Permitida Apenas para Produtos do Tipo MP Materia Prima","Codigo de Produto Em Branco ou Invalido")
        Return(.f.)
    endif
    //cSql:="SELECT LTRIM(RTRIM(AIB.AIB_CODTAB)) +' '+LTRIM(RTRIM(A2_COD    ))+'/'+LTRIM(RTRIM(A2_LOJA	  ))+' '+LTRIM(RTRIM(A2_NREDUZ )) DESCTAB, " + cEol
    cSql:="SELECT AIB_CODTAB ,AIB_PRCCOM, A2_COD,A2_LOJA,A2_NREDUZ " + cEol
    //cSql+=" MIN(AIB_PRCCOM) AIB_PRCCOM,MAX(AIB_DATVIG)AIB_DATVIG " + cEol
    cSql+="FROM dbo." + retsqlname("AIB") + "  AIB(NOLOCK) " + cEol
    cSql+=" JOIN dbo." + retsqlname("AIA") + " AIA (NOLOCK) ON AIA.D_E_L_E_T_= ''
    cSql+="AND AIB.AIB_FILIAL = AIA.AIA_FILIAL " + cEol
    cSql+="AND AIB.AIB_CODTAB = AIA.AIA_CODTAB " + cEol
    cSql+=" AND AIB_CODFOR = AIA_CODFOR " + cEol
    cSql+=" AND AIB_LOJFOR = AIA_LOJFOR " + cEol
    cSql+=" JOIN dbo." + retsqlname("SA2") + " SA2 (NOLOCK)ON SA2.D_E_L_E_T_= '' AND   " + cEol
    cSql+="     SA2.A2_FILIAL= '' AND AIB.AIB_CODFOR = SA2.A2_COD  " + cEol
    cSql+="     AND AIB.AIB_LOJFOR = SA2.A2_LOJA  " + cEol
    cSql+="WHERE AIB.D_E_L_E_T_='' AND AIB.AIB_FILIAL=" +valtosql(xfilial("AIB")) + cEol
    cSql+="      AND AIB_DATVIG != ''  " + cEol
    cSql+="      AND AIB.AIB_CODPRO =" +valtosql(cProd) + cEol
    cSql+="      AND RTRIM(CONVERT(VARCHAR(10), GETDATE(), 112)) BETWEEN  AIA_DATDE AND " + cEol
    cSql+="                 CASE WHEN AIA_DATATE ='' THEN '20491231' ELSE AIA_DATATE END " + cEol
    //cSql+="GROUP BY AIB_CODTAB,A2_COD,A2_LOJA,A2_NREDUZ"

    cSql+="ORDER  BY 1,3,4"
    CONOUT(cSql)
    cQuery := cSql
    bRet := U_FiltroF3(cTitulo,cQuery,nTamCpo,cAlias,cCodigo,cCpoChave,cTitCampo,cMascara,cRetCpo,nColuna)
    RestArea(aArea)

Return(bRet)



User Function AIBF3RET()


reTURN(M->Z9_TABPRCC)


Static Function fSetInfo(aInfo)

    Local oModel     := FWMODELACTIVE()
    Local oView      := FWViewActive()
    Local oModelSZ8  := oModel:GetModel("SZ8MASTER")
    Local nTamObs    := GetSx3cache("Z9_OBS","X3_TAMANHO")
    Local nTamPrd    := GetSx3cache("B1_COD","X3_TAMANHO")
    Local oModelSZ91 := oModel:GetModel("SZ9DETAIL01")

    cObs := alltrim(aInfo[3])+"/"
    cObs += alltrim(aInfo[4])+" "
    cObs += alltrim(aInfo[5])

    cObs := padr(cObs,nTamObs)
    oModelSZ91:setvalue("Z9_OBS",cObs)

    conout("teste")
    oView:Refresh("SZ9DETAIL01")
REturn
