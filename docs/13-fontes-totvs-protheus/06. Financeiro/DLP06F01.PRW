//Bibliotecas
#Include "TOTVS.ch"
#Include "TopConn.ch"

//Posições do Array
Static nPosCodigo := 1 //Coluna A no Excel
Static nPosLojFor := 2 //Coluna B no Excel
Static nPosRazSoc := 3 //Coluna C no Excel
Static nPosObserv := 4 //Coluna D no Excel

/*/{Protheus.doc} zImpCSV
Função para importar informações do fornecedor via csv
@author Atilio
@since 07/06/2021
@version 1.0
@type function
/*/

User Function DLP06F01()
    Local aArea     := GetArea()
    Private cArqOri := ""

    //Mostra o Prompt para selecionar arquivos
    cArqOri := tFileDialog( "TXT files (*.txt) ", 'Seleção de Arquivos', , , .F., )

    //Se tiver o l de origem
    If ! Empty(cArqOri)

        //Somente se existir o l e for com a extensão CSV
        If File(cArqOri) .And. Upper(SubStr(cArqOri, RAt('.', cArqOri) + 1, 3)) == 'TXT'
            Processa({|| fImporta() }, "Importando...")
        Else
            MsgStop("Arquivo e/ou extensão inválida!", "Atenção")
        EndIf
    EndIf

    RestArea(aArea)
Return

/*-------------------------------------------------------------------------------*
 | Func:  fImporta                                                               |
 | Desc:  Função que importa os dados                                            |
*-------------------------------------------------------------------------------*/

Static Function fImporta()
    Local aArea      := GetArea()
    Local cArqLog    := "zImpCSV_" + dToS(Date()) + "_" + StrTran(Time(), ':', '-') + ".log"
    Local nTotLinhas := 0
    Local cLinAtu    := ""
    Local nLinhaAtu  := 0
    Local aLinha     := {}
    Local oArquivo
    Local cSep := chr(09)
    Local aLinhas
    Local cCodForn   := ""
    Local cLojForn   := ""
    Local cObserv    := ""
    Local cRazaoSoc  := ""
    Local nY := 0

    Private cDirLog    := GetTempPath() + "x_importacao\"
    Private cLog       := ""
    Private 	lMsErroAuto := .F.
    nPosDoc := 7
    nPosCC := 13
    nPosBA := 12
    nPosVlr := 11
    nPosEmp := 1
    nPosDt := 5
    nPosFld := rat("\",cArqOri)
    cDirLog := substr(cArqOri,1,nPosFld)
    cArq := alltrim(substr(cArqOri,nPosFld+1))
    cArqLog    := cArq+"_" + dToS(Date()) + "_" + StrTran(Time(), ':', '-') + ".log"
    //Se a pasta de log não existir, cria ela
    If ! ExistDir(cDirLog)
        MakeDir(cDirLog)
    EndIf

    //Definindo o l a ser lido
    oArquivo := FWFileReader():New(cArqOri)

    //Se o l pode ser aberto
    If (oArquivo:Open())

        //Se não for fim do l
        If ! (oArquivo:EoF())

            //Definindo o tamanho da régua
            aLinhas := oArquivo:GetAllLines()
            nTotLinhas := Len(aLinhas)
            ProcRegua(nTotLinhas)

            //Método GoTop não funciona (dependendo da versão da LIB), deve fechar e abrir novamente o l
            oArquivo:Close()
            oArquivo := FWFileReader():New(cArqOri)
            oArquivo:Open()

            //Enquanto tiver linhas
            While (oArquivo:HasLine())
                cLogLin := ""
                cErro := ""
                //Incrementa na tela a mensagem
                nLinhaAtu++
                IncProc("Analisando linha " + cValToChar(nLinhaAtu) + " de " + cValToChar(nTotLinhas) + "...")

                cLinAtu    := oArquivo:GetLine()
                aLinha     := StrTokArr(cLinAtu, cSep)
                if   !("Empresa"  $ cLinAtu)    .and. Len(aLinha)>6            //Pegando a linha atual e transformando em array
                    aDocSer    := StrTokArr(aLinha[nPosDoc],"-")
                    aInfBCO    := fGetBAC(aLinha[nPosBA],aLinha[nPosCC])
                    nVlBx      := abs( val(replace(replace(aLinha[nPosVlr],".",""),",",".")))
                    aDocSer[1] := right(aDocSer[1],6)
                    aDocSer[2] := "0"+ aDocSer[2]
                    aCli       := fGetCli(aDocSer[nPosEmp])
                    nDtBx      := ctod(aLinha[nPosDt])
                    lSeekSA6   := .f.
                    lSeekSE1   := .f.
                    dDataBase  := nDtBx
                    dbselectarea("SA6")
                    SA6->(dbsetOrder(1)) //-1 A6_FILIAL+A6_COD+A6_AGENCIA+A6_NUMCON
                    If SA6->(DbSeek(xFilial("SA6") +  aInfBCO[1]+aInfBCO[2]  +aInfBCO[3]    ))

                        lSeekSA6:= .T.

                    else

                        cLogLin +="Não encontrado Banco Agencia e Conta"

                    endif

                    cPrefix := padr(   aDocSer[2] ,getsx3cache("E1_PREFIXO","X3_TAMANHO"))
                    cDoc    := padr(   aDocSer[1] ,getsx3cache("E1_NUM","X3_TAMANHO"))
                    cCli    := padr(   aCli[1] ,getsx3cache("E1_CLIENTE","X3_TAMANHO"))
                    cLjCli  := padr(   aCli[2] ,getsx3cache("E1_LOJA","X3_TAMANHO"))
                    dbselectarea("SE1")
                    SE1->(dbSetOrder(1)) //E1_FILIAL+E1_PREFIXO+E1_NUM+E1_PARCELA+E1_TIPO

                    //Posiciona no titulo para desfazer baixa
                    If SE1->(dbSeek(xFilial("SE1") + cPrefix+ cDoc + "   " +"NF "))

                        lSeekSE1:= .T.

                    else
                        if !empty(cLogLin)
                            cLogLin +=chr(10)
                        endif
                        cLogLin +="Não encontrado Titulo"
                    endif
                    aBaixa := {}
                    lSeekSE1:= .T.
                    if lSeekSE1 .and.  SE1->E1_SALDO < nVlBx
                        if !empty(cLogLin)
                            cLogLin +=chr(10)
                        endif
                        cLogLin +="Saldo Insuficiente para baixa"
                    endif

                    if empty(cLogLin)
                        aBaixa := {{"E1_PREFIXO"  , SE1->E1_PREFIXO              ,Nil    },;
                            {"E1_NUM"      ,SE1->E1_NUM         ,Nil    },;
                            {"E1_PARCELA"  ,SE1->E1_PARCELA     ,Nil    },;
                            {"E1_TIPO"     ,SE1->E1_TIPO        ,Nil    },;
                            {"AUTMOTBX"    ,"NOR"               ,Nil    },;
                            {"AUTBANCO"    ,SA6->A6_COD         ,Nil    },;
                            {"AUTAGENCIA"  ,SA6->A6_AGENCIA     ,Nil    },;
                            {"AUTCONTA"    ,SA6->A6_NUMCON      ,Nil    },;
                            {"AUTDTBAIXA"  ,dDataBase              ,Nil    },;
                            {"AUTDTCREDITO",dDataBase              ,Nil    },;
                            {"AUTHIST"     ,"BAIXA TESTE"          ,Nil    },;
                            {"AUTJUROS"    ,0                      ,Nil,.T.},;
                            {"AUTVALREC"   ,700                    ,Nil    }}

                        lMsErroAuto := .F.

                        MSExecAuto({|x,y| Fina070(x,y)},aBaixa,3)

                        if lMsErroAuto
                            aLogAuto    := GetAutoGrLog()

                            For nY := 1 To Len(aLogAuto)
                                cErro += aLogAuto[nY] + CRLF
                            Next nY

                        endif
                    endif
                endif

                if !Empty(cErro)
                    if !empty(cLogLin)
                        cLogLin +=chr(10)
                    endif
                    cLogLin +=cErro
                endif

                if !empty(cLogLin)
                    cLog += "******************    Linha " + cValToChar(nLinhaAtu)+"     ******************" +chr(10)
                    cLog +=cLogLin+chr(10)
                endif
                //Se não for o cabeçalho (encontrar o texto "Código" na linha atual)
                // If ! "código" $ Lower(cLinAtu)

                //     //Zera as variaveis
                //     cCodForn   := aLinha[nPosCodigo]
                //     cLojForn   := aLinha[nPosLojFor]
                //     cRazaoSoc  := aLinha[nPosRazSoc]
                //     cObserv    := aLinha[nPosObserv]

                //     DbSelectArea('SA2')
                //     SA2->(DbSetOrder(1)) // Filial + Código + Loja

                //     //Se conseguir posicionar no fornecedor
                //     If SA2->(DbSeek(FWxFilial('SA2') + cCodForn + cLojForn))
                //         cLog += "+ Lin" + cValToChar(nLinhaAtu) + ", fornecedor [" + cCodForn + cLojForn + " - " + Upper(SA2->A2_NREDUZ) + "] " +;
                //             "a observação foi alterada, antes: [" + Alltrim(SA2->A2_X_OBS) + "], agora: [" + Alltrim(cObserv) + "];" + CRLF

                //         //Realiza a alteração do fornecedor
                //         RecLock('SA2', .F.)
                //         SA2->A2_X_OBS  := cObserv
                //         SA2->(MsUnlock())

                //     Else
                //         cLog += "- Lin" + cValToChar(nLinhaAtu) + ", fornecedor e loja [" + cCodForn + cLojForn + "] não encontrados no Protheus;" + CRLF
                //     EndIf

                // Else
                //     cLog += "- Lin" + cValToChar(nLinhaAtu) + ", linha não processada - cabeçalho;" + CRLF
                // EndIf

            EndDo

            //Se tiver log, mostra ele
            If ! Empty(cLog)
                cLog := "Processamento finalizado, abaixo as mensagens de log: " + CRLF + cLog
                MemoWrite(cDirLog + cArqLog, cLog)
                ShellExecute("OPEN", cArqLog, "", cDirLog, 1)
            EndIf

        Else
            MsgStop("Arquivo não tem conteúdo!", "Atenção")
        EndIf

        //Fecha o l
        oArquivo:Close()
    Else
        MsgStop("Arquivo não pode ser aberto!", "Atenção")
    EndIf
    dDataBase := date()
    RestArea(aArea)
Return

/*Amarração da Conta e Filial/Empresa*/

Static Function fGetBAC(cBCOAg,cConta)

    cBcoRet := ""
    cAgRet  := ""
    cCCRet  := ""
    if cBCOAg == "00193163" .and. cConta == "5156 X"
        cBcoRet := "001"
        cAgRet  := "31631"
        cCCRet  := "5156X     "
    elseif cBCOAg == "75603007" .and. cConta == "132519 1"
        cBcoRet := "756"
        cAgRet := "3007"
        cCCRet := "132519    "
    elseif cBCOAg == "75603069" .and. cConta == "286164 0"
        cBcoRet := "756"
        cAgRet := "3069"
        cCCRet := "286164    "
    endif



Return { cBcoRet ,cAgRet  ,cCCRet  }


Static Function fGetCli(cEmpWeg)

    cCodCli := ""
    cLjCli  := ""


    if cEmpWeg == "1001"
        cCodCli :="000001"
        cLjCli  :="13"

    elseif cEmpWeg == "1009"
        cCodCli :="000001"
        cLjCli  :="09"
    elseif cEmpWeg == "1013"
        cCodCli :="000001"
        cLjCli  :="11"
    endif


Return {cCodCli,cLjCli}
