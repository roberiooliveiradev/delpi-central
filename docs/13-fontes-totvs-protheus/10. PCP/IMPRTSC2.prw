#INCLUDE 'TOTVS.CH'
#INCLUDE "TBICONN.CH"
#INCLUDE "TOPCONN.CH"

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 20/10/2024
@version version
/*/
User Function IMPRTSC2()
    Local aArea     := GetArea()
    Local lIsBlind  := IsBlind()
    Local cLockName := ProcName()
    Local cDirCsv   := SUPERGETMV("MV_ICSVDIR", .F., " ")
    Local cMask :="Arquivos CSV (*.CSV)|*.csv|"
    Private cArqOri := ""

    IF !lIsBlind
        IF !MSGYESNO("Deseja realizar a importacao?", "ATENCAO!")
            RETURN .F.
        ENDIF
    ENDIF

    //cArqOri := "C:\Users\pedro\Downloads\ops_exc2.csv"//Alltrim(cGetFile(cMask,OemToAnsi("Selecione o Arquivo"),0,"",.T.,GETF_ONLYSERVER+GETF_LOCALHARD+GETF_NETWORKDRIVE))
    cArqOri := Alltrim(cGetFile(cMask,OemToAnsi("Selecione o Arquivo"),0,"",.T.,GETF_ONLYSERVER+GETF_LOCALHARD+GETF_NETWORKDRIVE))

    //Diretorio do arquivo que será processado.
    // cArqOri := cDirCsv

    If ! Empty(cArqOri)
        //Somente se existir o arquivo e for com a extensao CSV
        If File(cArqOri) .And. Upper(SubStr(cArqOri, RAt('.', cArqOri) + 1, 3)) == 'CSV'
            Processa({|| fImporta() }, "Importando...")
        Else
            IF !lIsBlind
                MsgStop("Arquivo e/ou extensão invalida!", "Atencao")
            ENDIF
        EndIf
    EndIf

    RestArea(aArea)

Return

Static Function fImporta()
    Local aArea     := GetArea()
    Local lIsBlind  := IsBlind()
    Local cArqLog   := "zImpCSV_" + dToS(Date()) + "_" + StrTran(Time(), ':', '-') + ".log"
    Local nTotLinhas:= 0
    Local cLinAtu   := " "
    Local nLinhaAtu := 0
    Local aLinha    := {}
    Local aMata650 := {}
    Local oArquivo
    Local aLinhas
    Local lRet      := .T.
    Local cNumOp  := " "
    Local cDatPrf := " "
    Local aSD3Area := SD3->(GetArea())
    Local aSc2Area := SC2->(GetArea())
    Local cEol := chr(10)
    Local lMsErroAuto := .F.
    Private cDirLog := GetTempPath() //+ "alt.CurvaProd\" + DTOC(DATE()) + TIME()
    Private cLog    := ""

    //Se a pasta de log nao existir, cria ela
    If ! ExistDir(cDirLog)
        MakeDir(cDirLog)
    EndIf

    if lRet
        oArquivo := FWFileReader():New(cArqOri)

        If (oArquivo:Open())

            If ! (oArquivo:EoF())

                aLinhas := oArquivo:GetAllLines()
                nTotLinhas := Len(aLinhas)
                ProcRegua(nTotLinhas)

                oArquivo:Close()
                oArquivo := FWFileReader():New(cArqOri)
                oArquivo:Open()

                While (oArquivo:HasLine())

                    nLinhaAtu++
                    IF !lIsBlind
                        IncProc("Analisando linha " + cValToChar(nLinhaAtu) + " de " + cValToChar(nTotLinhas) + "...")
                    ENDIF

                    cLinAtu := oArquivo:GetLine()
                    aLinha  := StrTokArr(cLinAtu, ",")

                    If !(nLinhaAtu == 1)

                        cFilNum  := aLinha[1]
                        cNumOp   := aLinha[2]
                        cDatPrf  := ctod(aLinha[3])
                        cSql := "SELECT *
                        cSql += "FROM dbo."+ RetSqlName("SC2") + "  (NOLOCK) SC2 " + cEol
                        cSql += "WHERE SC2.D_E_L_E_T_ = '' " + cEol
                        cSql += "AND SC2.C2_FILIAL = "+VALTOSQL(cFilNum) + cEol
                        cSql += "AND C2_NUM = "+VALTOSQL(substr(cNumOp,1,6) )+ cEol

                        If Select('TMPSC2') <> 0
                            TMPSC2->(dbCloseArea())
                        Endif


                        TCQuery cSql Alias TMPSC2 New
                        //TMPIMP->( RecCount() )
                        WHILE  TMPSC2->(!eof())

                            SC2->(DbSetOrder(1))
                            If SC2->(DbSeek(cFilNum+ TMPSC2->C2_NUM+TMPSC2->C2_ITEM+TMPSC2->C2_SEQUEN))
                                nPRFOP := SuperGetMv("MV_YPRFOP", .F., -2)
                                nLeadOP := posicione("SBZ",1,XFILIAL("SBZ")+SC2->C2_PRODUTO,"BZ_YLEADOP")*-1
                                dDatPri := SomaPrazo(cDatPrf,nLeadOP )
                                if dDatPri < date()

                                    dDatPri := date()
                                endif

                                // IF cFilAnt == "01"
                                //     dDatPri := SomaPrazo(cDatPrf,nPRFOP )
                                //     if dDatPri < date()

                                //         dDatPri := date()
                                //     endif

                                // else
                                //     dDatPri := SomaPrazo(cDatPrf,nLeadOP )
                                //     if dDatPri < date()

                                //         dDatPri := date()
                                //     endif

                                // endif
                                reclock("SC2",.f.)
                                SC2->C2_DATPRF:=cDatPrf
                                SC2->C2_DATPRI :=dDatPri
                                SC2->(MsUnlock())

                            EndIf

                            TMPSC2->(dbskip())
                        ENDDO

                    EndIf

                EndDo

            Else
                IF !lIsBlind
                    MsgStop("Arquivo nao tem conteudo.", "Atencao!")
                ELSE
                    cLog := "Arquivo nao tem conteudo!"
                    MemoWrite(cDirLog + cArqLog, cLog)
                ENDIF
            EndIf

            oArquivo:Close()
            RestArea(aSc2Area)
            RestArea(aSD3Area)
        Else
            IF !lIsBlind
                MsgStop("Arquivo nao pode ser aberto.", "Atencao!")
            ELSE
                cLog := "Arquivo nao pode ser Aberto!"
                MemoWrite(cDirLog + cArqLog, cLog)
            ENDIF
        EndIf
    ENDIF

    RestArea(aArea)
Return
