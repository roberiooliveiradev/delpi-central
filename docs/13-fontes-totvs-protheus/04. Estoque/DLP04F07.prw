//Bibliotecas
#Include "Totvs.ch"
#Include "FWMVCDef.ch"
#include "TopConn.ch"


User Function DLP04F07()
    Local aArea := FWGetArea()

    fMontaTela()

    FWRestArea(aArea)
Return

Static Function fMontaTela()
    Local aArea         := GetArea()
    Local n1 := 0
    Local aCampos := {}
    Local oTempTable := Nil
    Local aColunas := {}
    Local cFontPad    := 'Tahoma'
    Local oFontGrid   := TFont():New(cFontPad, /*uPar2*/, -14)
    Private lOk        := .F.
    //Janela e componentes
    Private oDlgBrow
    Private oPanGrid
    Private oFWBrowse
    Private cAliasTmp := GetNextAlias()
    Private aRotina   := MenuDef()
    //Tamanho da janela
    Private aTamanho := MsAdvSize()
    Private nJanLarg := aTamanho[5]
    Private nJanAltu := aTamanho[6]-50

    Private aGroUsr := UsrRetGrp(PswChave(RetCodUsr()),RetCodUsr()) //Retorna um array contendo todos os códigos dos Grupos de Usuário em que o Usuário, passado na função, pertence.
    Private cGRPMnt := supergetmv("MV_ACSINV",.F.,"000007;000008") //codigo do grupo de usuario PARA ALTERAR O CAMPO PRODUTO X FORNECEDOR
    Private aUsers := FWSFGrpUsers("000007")
    Private cDest := ""
    Private lUsrPri := .F.

    for n1 := 1 to len(FWSFGrpUsers("000008"))
        aadd(aUsers,FWSFGrpUsers("000008")[n1])
    Next n1

    for n1 := 1 to len(aUsers)
        cDest += Alltrim(UsrRetMail(aUsers[n1]))+";"
    Next n1

    FOR n1 := 1 to len(aGroUsr)
        IF aGroUsr[n1] $ cGRPMnt
            lUsrPri := .T.
        ENDIF
    NEXT n1

<<<<<<< HEAD
    //Adiciona as colunas que serão criadas na temporária
    aAdd(aCampos, { 'OK',  'C', 2,                    0}) //Flag para marcação
    aAdd(aCampos, { 'B7_COD',   'C', TamSX3('B7_COD')[1],  0})
    aAdd(aCampos, { 'B1_DESC',   'C', TamSX3('B1_DESC')[1],  0})
    aAdd(aCampos, { 'B1_TIPO',   'C', TamSX3('B1_TIPO')[1],  0})
    aAdd(aCampos, { 'B7_LOCAL', 'C', TamSX3('B7_LOCAL')[1],  0})
    aAdd(aCampos, { 'B7_DATA',  'D', TamSX3('B7_DATA')[1], 0})
    aAdd(aCampos, { 'TMP_QATU',   'N', 18,   4})
    aAdd(aCampos, { 'TMP_CMUNI',  'N', 18,   4})
    aAdd(aCampos, { 'TMP_CM', 'N', 18,   4})
    aAdd(aCampos, { 'B7_QUANT',   'N', 18,   4})
    aAdd(aCampos, { 'TMP_VLINV',   'N', 18,   4})
    aAdd(aCampos, { 'TMP_VLDIF',     'N', 18,   4})

    //Cria a tabela temporária
    oTempTable:= FWTemporaryTable():New(cAliasTmp)
    oTempTable:SetFields( aCampos )
    oTempTable:Create()

    //Popula a tabela temporária
    Processa({|| fPopula()}, 'Processando...')

    //Adiciona as colunas que serão exibidas no browse
    aColunas := fCriaCols()

    //Criando a janela

    DEFINE MSDIALOG oDlgMark TITLE 'Monitor inventario' FROM 000, 000  TO nJanAltu, nJanLarg COLORS 0, 16777215 PIXEL
    //Dados
    oPanGrid := tPanel():New(001, 001, '', oDlgMark, , , , RGB(000,000,000), RGB(254,254,254), (nJanLarg/2)-1,     (nJanAltu/2 - 1))
    oMarkBrowse := FWMarkBrowse():New()
    oMarkBrowse:SetAlias(cAliasTmp)
    oMarkBrowse:SetDescription('Inventário')
    oMarkBrowse:DisableFilter()
    oMarkBrowse:DisableConfig()
    oMarkBrowse:DisableSeek()
    oMarkBrowse:DisableSaveConfig()
    oMarkBrowse:SetFontBrowse(oFontGrid)
    oMarkBrowse:SetFieldMark('OK')
    oMarkBrowse:SetTemporary(.T.)
    oMarkBrowse:SetColumns(aColunas)
    oMarkBrowse:SetOwner(oPanGrid)
    oMarkBrowse:Activate()
    ACTIVATE MsDialog oDlgMark CENTERED

    //Deleta a temporária e desativa a tela de marcação
    oTempTable:Delete()
    oMarkBrowse:DeActivate()

    If lOk
        fConfirmou()
    EndIf


=======
    //aScan(aGroUsr,{|x| AllTrim(x) == AllTrim(cGRPMnt)}) == 0 .and. (RetCodUsr() != "000000")
    //   FWAlertError("Sem permissão Acessar o Monitor de inventário", "Monitor Inventário")

    //Adiciona as colunas que serão criadas na temporária
    aAdd(aCampos, { 'OK',  'C', 2,                    0}) //Flag para marcação
    aAdd(aCampos, { 'B7_COD',   'C', TamSX3('B7_COD')[1],  0})
    aAdd(aCampos, { 'B1_DESC',   'C', TamSX3('B1_DESC')[1],  0})
    aAdd(aCampos, { 'B1_TIPO',   'C', TamSX3('B1_TIPO')[1],  0})
    aAdd(aCampos, { 'B7_LOCAL', 'C', TamSX3('B7_LOCAL')[1],  0})
    aAdd(aCampos, { 'B7_DATA',  'D', TamSX3('B7_DATA')[1], 0})
    aAdd(aCampos, { 'TMP_QATU',   'N', 18,   4})
    aAdd(aCampos, { 'TMP_CMUNI',  'N', 18,   4})
    aAdd(aCampos, { 'TMP_CM', 'N', 18,   4})
    aAdd(aCampos, { 'B7_QUANT',   'N', 18,   4})
    aAdd(aCampos, { 'TMP_VLINV',   'N', 18,   4})
    aAdd(aCampos, { 'TMP_VLDIF',     'N', 18,   4})

    //Cria a tabela temporária
    oTempTable:= FWTemporaryTable():New(cAliasTmp)
    oTempTable:SetFields( aCampos )
    oTempTable:Create()

    //Popula a tabela temporária
    Processa({|| fPopula()}, 'Processando...')

    //Adiciona as colunas que serão exibidas no browse
    aColunas := fCriaCols()

    //Criando a janela

    DEFINE MSDIALOG oDlgMark TITLE 'Monitor inventario' FROM 000, 000  TO nJanAltu, nJanLarg COLORS 0, 16777215 PIXEL
    //Dados
    oPanGrid := tPanel():New(001, 001, '', oDlgMark, , , , RGB(000,000,000), RGB(254,254,254), (nJanLarg/2)-1,     (nJanAltu/2 - 1))
    oMarkBrowse := FWMarkBrowse():New()
    oMarkBrowse:SetAlias(cAliasTmp)
    oMarkBrowse:SetDescription('Inventário')
    oMarkBrowse:DisableFilter()
    oMarkBrowse:DisableConfig()
    oMarkBrowse:DisableSeek()
    oMarkBrowse:DisableSaveConfig()
    oMarkBrowse:SetFontBrowse(oFontGrid)
    oMarkBrowse:SetFieldMark('OK')
    oMarkBrowse:SetTemporary(.T.)
    oMarkBrowse:SetColumns(aColunas)
    //oMarkBrowse:AllMark()
    oMarkBrowse:SetOwner(oPanGrid)
    oMarkBrowse:Activate()
    ACTIVATE MsDialog oDlgMark CENTERED

    //Deleta a temporária e desativa a tela de marcação
    oTempTable:Delete()
    oMarkBrowse:DeActivate()

    If lOk
        fConfirmou()
    EndIf


>>>>>>> e7efcd64650dbd2a7b96a8a56602e56dfd112053
    RestArea(aArea)
Return


Static Function MenuDef()
    Local aRotina := {}

    //Criação das opções
    ADD OPTION aRotina TITLE 'Proc. Inventário'  ACTION 'u_zConfInv'     OPERATION 2 ACCESS 0
    ADD OPTION aRotina TITLE 'Enviar p Análise'    ACTION 'u_zEnvAn'     OPERATION 2 ACCESS 0
    ADD OPTION aRotina TITLE 'Aprovar'    ACTION 'u_zAprvIn'     OPERATION 2 ACCESS 0
Return aRotina

Static Function fPopula()
    Local cQryDados := ''
    Local nTotal := 0
    Local nAtual := 0

    //Monta a consulta

    cQryDados += " SELECT B7_COD,B1_DESC,B1_TIPO,B7_LOCAL, B7_DATA ,'nVlrUCM' [CUSTO MEDIO UNIT],  "        + CRLF
    cQryDados += " 'nSldData' [SLD_DATA],'nVlrCM' [CUSTO MEDIO],B7_QUANT , "        + CRLF
    cQryDados += " 'nVlrB7' [VALOR INVENTARIADO],'nDif' [Diferenca] "        + CRLF
    cQryDados += " FROM "+RetSQLName("SB7")+" (NOLOCK) TBL1  "        + CRLF
    cQryDados += " JOIN "+RetSQLName("SB1")+" SB1(NOLOCK) ON SB1.D_E_L_E_T_ ='' AND B1_FILIAL = '' AND B1_COD  = B7_COD "        + CRLF
    cQryDados += " WHERE TBL1.D_E_L_E_T_ = '' "        + CRLF
    cQryDados += " AND TBL1.B7_FILIAL = '02'  "        + CRLF
    cQryDados += " AND B7_DATA >='20250101' "        + CRLF

    if lUsrPri
        cQryDados += " AND B7_BLQCNT ='1' "        + CRLF
    endif

    // PLSQuery(cQryDados, 'QRYDADTMP')
    If Select('QRYDADTMP') <> 0
        QRYDADTMP->(dbCloseArea())
    Endif
    TCQuery cQryDados New Alias QRYDADTMP

    //Definindo o tamanho da régua
    DbSelectArea('QRYDADTMP')
    Count to nTotal
    ProcRegua(nTotal)
    QRYDADTMP->(DbGoTop())

    //Enquanto houver registros, adiciona na temporária
    While ! QRYDADTMP->(EoF())
        nAtual++
        IncProc('Analisando registro ' + cValToChar(nAtual) + ' de ' + cValToChar(nTotal) + '...')
<<<<<<< HEAD

=======

>>>>>>> e7efcd64650dbd2a7b96a8a56602e56dfd112053
        cCod := QRYDADTMP->B7_COD
        cLocal := QRYDADTMP->B7_LOCAL
        dData :=  QRYDADTMP->B7_DATA
        aSaldo := CalcEst(cCod,cLocal,stod(dData))
        nVlrUCM  := aSaldo[2]/aSaldo[1]
        nSldData := aSaldo[1]
        nVlrCM := aSaldo[2]
        nVlrB7 :=  nVlrUCM * B7_QUANT
        nDif := nVlrCM-nVlrB7

<<<<<<< HEAD

        RecLock(cAliasTmp, .T.)
        (cAliasTmp)->OK := Space(2)
        (cAliasTmp)->B7_COD := QRYDADTMP->B7_COD
        (cAliasTmp)->B1_DESC   := QRYDADTMP->B1_DESC
        (cAliasTmp)->B1_TIPO   := QRYDADTMP->B1_TIPO
=======

        RecLock(cAliasTmp, .T.)
        (cAliasTmp)->OK := Space(2)
        (cAliasTmp)->B7_COD := QRYDADTMP->B7_COD
        (cAliasTmp)->B1_DESC   := QRYDADTMP->B1_DESC
        (cAliasTmp)->B1_TIPO   := QRYDADTMP->B1_TIPO
>>>>>>> e7efcd64650dbd2a7b96a8a56602e56dfd112053
        (cAliasTmp)->B7_LOCAL := QRYDADTMP->B7_LOCAL
        (cAliasTmp)->B7_DATA := STOD(QRYDADTMP->B7_DATA)
        (cAliasTmp)->TMP_CMUNI := nVlrUCM
        (cAliasTmp)->TMP_QATU :=nSldData
        (cAliasTmp)->TMP_CM := nVlrCM
        (cAliasTmp)->B7_QUANT :=  QRYDADTMP->B7_QUANT
        (cAliasTmp)->TMP_VLINV := nVlrB7
        (cAliasTmp)->TMP_VLDIF := nVlrCM-nVlrB7
        (cAliasTmp)->(MsUnlock())

        QRYDADTMP->(DbSkip())
    EndDo
    QRYDADTMP->(DbCloseArea())
    (cAliasTmp)->(DbGoTop())
Return

Static Function fCriaCols()
    Local nAtual       := 0
    Local aColunas := {}
    Local aEstrut  := {}
    Local oColumn

    //Adicionando campos que serão mostrados na tela
    //[1] - Campo da Temporaria
    //[2] - Titulo
    //[3] - Tipo
    //[4] - Tamanho
    //[5] - Decimais
    //[6] - Máscara
    //[7] - Editável? .T. = sim, .F. = não
    //[8] - Alinhamento 0 = Centralizado, 1 = Esquerda, 2 = Direita

    aAdd(aEstrut, { 'B7_COD',      'Código ' , 'C', TamSX3('B7_COD')[1],  0, '',     .F.,0})
    aAdd(aEstrut, { 'B7_LOCAL',    'Armazém' , 'C', TamSX3('B7_LOCAL')[1],  0, '',     .F.,0})
    aAdd(aEstrut, { 'B7_DATA',     'Data' , 'D', TamSX3('B7_DATA')[1], 0, '',     .F.,0})
    aAdd(aEstrut, { 'TMP_QATU',    'Saldo Qtd' ,  'N', 18,   2, '',     .F.,0})
    aAdd(aEstrut, { 'TMP_CMUNI',   'Custo Médio Unitário' , 'N', 18,   2, '',     .F.,0})
    aAdd(aEstrut, { 'TMP_CM',      'Custo Médio ' , 'N', 18,   2, '',     .F.,0})
    aAdd(aEstrut, { 'B7_QUANT',    'Qtd Inventariada' , 'N', 18,   2, '',     .F.,0})
    aAdd(aEstrut, { 'TMP_VLINV',   'Valor Inventariado' ,  'N', 18,   2, '',     .F.,0})
    aAdd(aEstrut, { 'TMP_VLDIF',   'Diferença Valor' ,   'N', 18,   2, '',     .F.,0})


    //Percorrendo todos os campos da estrutura
    For nAtual := 1 To Len(aEstrut)
        //Cria a coluna
        oColumn := FWBrwColumn():New()
        oColumn:SetData(&('{|| ' + cAliasTmp + '->' + aEstrut[nAtual][1] +'}'))
        oColumn:SetTitle(aEstrut[nAtual][2])
        oColumn:SetType(aEstrut[nAtual][3])
        oColumn:SetSize(aEstrut[nAtual][4])
        oColumn:SetDecimal(aEstrut[nAtual][5])
        oColumn:SetPicture(aEstrut[nAtual][6])

        //Se for ser possível ter o duplo clique
        If aEstrut[nAtual][7]
            oColumn:SetEdit(.T.)
            oColumn:SetReadVar(aEstrut[nAtual][1])
            //oColumn:SetValid({|| fSuaValid()})
        EndIf

        oColumn:nAlign := (aEstrut[nAtual][8])

        //Adiciona a coluna
        aAdd(aColunas, oColumn)
    Next
Return aColunas


User Function zConfInv()
    Processa({|| fProcessa()}, 'Processando...')
Return

User Function zEnvAn()
    Processa({|| fEnvInv()}, 'Processando...')
Return

User Function zAprvIn()
    Processa({|| fAprvIn()}, 'Processando...')
Return

Static Function fProcessa()
    Local aArea     := FWGetArea()
    Local cMarca    := oMarkBrowse:Mark()
    Local nAtual    := 0
    Local nTotal    := 0
    Local nTotMarc := 0
<<<<<<< HEAD

=======

>>>>>>> e7efcd64650dbd2a7b96a8a56602e56dfd112053
    //Define o tamanho da régua
    DbSelectArea(cAliasTmp)
    (cAliasTmp)->(DbGoTop())
    Count To nTotal
    ProcRegua(nTotal)
<<<<<<< HEAD

=======

>>>>>>> e7efcd64650dbd2a7b96a8a56602e56dfd112053
    //Percorrendo os registros
    (cAliasTmp)->(DbGoTop())
    While ! (cAliasTmp)->(EoF())
        nAtual++
        IncProc('Analisando registro ' + cValToChar(nAtual) + ' de ' + cValToChar(nTotal) + '...')
<<<<<<< HEAD

        //Caso esteja marcado
        If oMarkBrowse:IsMark(cMarca)
            nTotMarc++

=======

            //Caso esteja marcado
            If oMarkBrowse:IsMark(cMarca)
                nTotMarc++

>>>>>>> e7efcd64650dbd2a7b96a8a56602e56dfd112053
                //MATA340()

                /*
            //Aqui dentro você pode fazer o seu processamento
            Alert((cAliasTmp)->B1_COD)
                */
            EndIf
<<<<<<< HEAD

            (cAliasTmp)->(DbSkip())
            EndDo

            //Mostra a mensagem de término e caso queria fechar a dialog, basta usar o método End()
            FWAlertInfo('Dos [' + cValToChar(nTotal) + '] registros, foram processados [' + cValToChar(nTotMarc) + '] registros', 'Atenção')
            //oDlgMark:End()

=======

            (cAliasTmp)->(DbSkip())
            EndDo

            //Mostra a mensagem de término e caso queria fechar a dialog, basta usar o método End()
            FWAlertInfo('Dos [' + cValToChar(nTotal) + '] registros, foram processados [' + cValToChar(nTotMarc) + '] registros', 'Atenção')
            //oDlgMark:End()

>>>>>>> e7efcd64650dbd2a7b96a8a56602e56dfd112053
            FWRestArea(aArea)
            Return

            Static Function fEnvInv()
                Local aArea     := FWGetArea()
                Local cMarca    := oMarkBrowse:Mark()
                Local nAtual    := 0
                Local nTotal    := 0
                Local nTotMarc := 0
                Local aParamBox := {}
                Local aRet := {}
                LOCAL cPara:= SuperGetMV('MV_ZEMINVE', .F., 'eduardo.dalitz@totvs.com.br')
                Local cAssunto := "Emp: "+ cEmpAnt + " /  Fil:" + cFilAnt + " Inventario " + dtoc(dDataBase)
                Local cCorpo := ""

                //cPara := cDest
                aAdd(aParamBox,{11,"Informe a Justificativa","",".T.",".T.",.T.})

                If ParamBox(aParamBox,"Inventário",@aRet)

                    cCorpo := "<H3>Prezado, foi solicitado análise dos itens abaixo:<H3> <br>"
<<<<<<< HEAD
                    cCorpo += MV_PAR01 + "<br>"
=======
                    cCorpo += MV_PAR01 + "<br>"
>>>>>>> e7efcd64650dbd2a7b96a8a56602e56dfd112053
                    cCorpo += "<p>Itens..</p><br>"

                    cCorpo +="    <table style='width: 100%; border-collapse: collapse; table-layout: fixed;'> "
                    cCorpo +="        <tr> "
                    cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 8%'>Código</th> "
                    cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 28%;'>Descrição</th> "
                    cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 7%;'>Tipo</th> "
                    cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 7%'>Armazém</th> "
                    cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Saldo Qtd</th> "
                    cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Custo Médio</th> "
                    cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Custo Médio Unitário</th> "
                    cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Qtd Inventariada</th> "
                    cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Valor Inventariado</th> "
                    cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Diferença Qtd</th> "
                    cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Diferença Valor</th> "
                    cCorpo +="        </tr> "


                    //Define o tamanho da régua
                    DbSelectArea(cAliasTmp)
                    (cAliasTmp)->(DbGoTop())
                    Count To nTotal
                    ProcRegua(nTotal)
<<<<<<< HEAD

=======

>>>>>>> e7efcd64650dbd2a7b96a8a56602e56dfd112053
                    //Percorrendo os registros
                    (cAliasTmp)->(DbGoTop())
                    While ! (cAliasTmp)->(EoF())
                        nAtual++
                        IncProc('Analisando registro ' + cValToChar(nAtual) + ' de ' + cValToChar(nTotal) + '...')
                        //Caso esteja marcado
                        If oMarkBrowse:IsMark(cMarca)
                            nTotMarc++
<<<<<<< HEAD

=======

>>>>>>> e7efcd64650dbd2a7b96a8a56602e56dfd112053
                            cCorpo +="    <tr> "
                            cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+(cAliasTmp)->B7_COD+"</td>"
                            cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: justify; word-wrap: break-word; height: 3em; overflow: hidden;'>"+(cAliasTmp)->B1_DESC+"</td>"
                            cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+(cAliasTmp)->B1_TIPO+"</td>"
                            cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+(cAliasTmp)->B7_LOCAL+"</td>"
                            cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->TMP_QATU)+"</td>"
                            cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->TMP_CM)+"</td>"
                            cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->TMP_CM/(cAliasTmp)->TMP_QATU)+"</td>"
                            cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->B7_QUANT)+"</td>"
                            cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->TMP_VLINV)+"</td>"
                            cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->TMP_VLINV-(cAliasTmp)->B7_QUANT)+"</td>"
                            cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->TMP_CM-(cAliasTmp)->TMP_VLINV)+"</td>"
                            cCorpo +="    </tr>"

                            /*
                //Aqui dentro você pode fazer o seu processamento
                Alert((cAliasTmp)->B1_COD)
                            */
<<<<<<< HEAD

=======

>>>>>>> e7efcd64650dbd2a7b96a8a56602e56dfd112053
                            DbSelectArea("SB7")
                            //B7_FILIAL + DTOS(B7_DATA) + B7_COD + B7_LOCAL + B7_LOCALIZ + B7_NUMSERI + B7_LOTECTL + B7_NUMLOTE + B7_CONTAGE
                            SB7->(DBSetOrder(1))
                            if SB7->(DBSeek(xFilial("SB7")+DTOS((cAliasTmp)->B7_DATA)+(cAliasTmp)->B7_COD+(cAliasTmp)->B7_LOCAL))
                                RecLock('SB7',.F.)
                                SB7->B7_BLQCNT := '1'
                                SB7->(MsUnlock())
                            endif

                        EndIf

                        (cAliasTmp)->(DbSkip())
                    EndDo
                    cCorpo +="    </table>"

                    lRet := u_zEnvWF(cPara,cAssunto, cCorpo,  ,  , .T. ,,)


                Endif

                //Mostra a mensagem de término e caso queria fechar a dialog, basta usar o método End()
                FWAlertInfo('Dos [' + cValToChar(nTotal) + '] registros, foram processados [' + cValToChar(nTotMarc) + '] registros', 'Atenção')
                //oDlgMark:End()
                FWRestArea(aArea)
            Return

            Static Function fAprvIn()
                Local aArea     := FWGetArea()
                Local cMarca    := oMarkBrowse:Mark()
                Local nAtual    := 0
                Local nTotal    := 0
                Local nTotMarc := 0
                LOCAL cPara:= SuperGetMV('MV_ZEMINVE', .F., 'eduardo.dalitz@totvs.com.br') // definir pra quem mandar o email
                Local cAssunto := " Aprovação Inventario " + dtoc(dDataBase)
                Local cCorpo := ""

                cCorpo := "<H3>Prezado, foi realizado a aprovação dos itens abaixo:<H3> <br>"
                cCorpo += "<p>Itens..</p><br>"

                cCorpo +="    <table style='width: 100%; border-collapse: collapse; table-layout: fixed;'> "
                cCorpo +="        <tr> "
                cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 8%'>Código</th> "
                cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 28%;'>Descrição</th> "
                cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 7%;'>Tipo</th> "
                cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 7%'>Armazém</th> "
                cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Saldo Qtd</th> "
                cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Custo Médio</th> "
                cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Custo Médio Unitário</th> "
                cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Qtd Inventariada</th> "
                cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Valor Inventariado</th> "
                cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Diferença Qtd</th> "
                cCorpo +="            <th style='border: 1px solid black; padding: 8px; text-align: center; background-color: #f2f2f2; width: 10%;'>Diferença Valor</th> "
                cCorpo +="        </tr> "


                //Define o tamanho da régua
                DbSelectArea(cAliasTmp)
                (cAliasTmp)->(DbGoTop())
                Count To nTotal
                ProcRegua(nTotal)

                //Percorrendo os registros
                (cAliasTmp)->(DbGoTop())
                While ! (cAliasTmp)->(EoF())
                    nAtual++
                    IncProc('Analisando registro ' + cValToChar(nAtual) + ' de ' + cValToChar(nTotal) + '...')
                    //Caso esteja marcado
                    If oMarkBrowse:IsMark(cMarca)
                        nTotMarc++

                        cCorpo +="    <tr> "
                        cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+(cAliasTmp)->B7_COD+"</td>"
                        cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: justify; word-wrap: break-word; height: 3em; overflow: hidden;'>"+(cAliasTmp)->B1_DESC+"</td>"
                        cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+(cAliasTmp)->B1_TIPO+"</td>"
                        cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+(cAliasTmp)->B7_LOCAL+"</td>"
                        cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->TMP_QATU)+"</td>"
                        cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->TMP_CM)+"</td>"
                        cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->TMP_CM/(cAliasTmp)->TMP_QATU)+"</td>"
                        cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->B7_QUANT)+"</td>"
                        cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->TMP_VLINV)+"</td>"
                        cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->TMP_VLINV-(cAliasTmp)->B7_QUANT)+"</td>"
                        cCorpo +="        <td style='border: 1px solid black; padding: 8px; text-align: center;'>"+cValToChar((cAliasTmp)->TMP_CM-(cAliasTmp)->TMP_VLINV)+"</td>"
                        cCorpo +="    </tr>"

                        /*
                //Aqui dentro você pode fazer o seu processamento
                Alert((cAliasTmp)->B1_COD)
                        */

                        DbSelectArea("SB7")
                        //B7_FILIAL + DTOS(B7_DATA) + B7_COD + B7_LOCAL + B7_LOCALIZ + B7_NUMSERI + B7_LOTECTL + B7_NUMLOTE + B7_CONTAGE
                        SB7->(DBSetOrder(1))

                        IF aScan(aGroUsr,{|x| AllTrim(x) == "000007"}) != 0

                            if SB7->(DBSeek(xFilial("SB7")+DTOS((cAliasTmp)->B7_DATA)+(cAliasTmp)->B7_COD+(cAliasTmp)->B7_LOCAL))
                                RecLock('SB7',.F.)
                                SB7->B7_LIBGER := 'S'
                                SB7->(MsUnlock())
                            endif
                        ELSEIF aScan(aGroUsr,{|x| AllTrim(x) == "000008"}) != 0
                            if SB7->(DBSeek(xFilial("SB7")+DTOS((cAliasTmp)->B7_DATA)+(cAliasTmp)->B7_COD+(cAliasTmp)->B7_LOCAL))
                                RecLock('SB7',.F.)
                                SB7->B7_LIBSUP  := 'S'
                                SB7->(MsUnlock())
                            endif
                        ENDIF

                        IF SB7->B7_LIBGER == 'S' .AND. SB7->B7_LIBSUP = 'S'
                            //MATA340
                        ENDIF
                    EndIf

                    (cAliasTmp)->(DbSkip())
                EndDo
                cCorpo +="    </table>"

                lRet := u_zEnvWF(cPara,cAssunto, cCorpo,  ,  , .T. ,,)


                //Mostra a mensagem de término e caso queria fechar a dialog, basta usar o método End()
                FWAlertInfo('Dos [' + cValToChar(nTotal) + '] registros, foram processados [' + cValToChar(nTotMarc) + '] registros', 'Atenção')
                //oDlgMark:End()
<<<<<<< HEAD

=======

>>>>>>> e7efcd64650dbd2a7b96a8a56602e56dfd112053
                FWRestArea(aArea)
            Return
