#INCLUDE 'TOTVS.CH'

/*/{Protheus.doc} M261FILB
    (Montagem de array com botões na tela de inclusão.)
    @type user function
    @author Luan Woichechoscki
    @since 19/02/2025
    @return cRet, Caracter, Filtro para o MBrowse
/*/
User Function M261FILB()

    Local cRet := ""

    // SetKey(VK_F7, {|| IF(INCLUI .OR. ALTERA, fConsulta(), )})

Return cRet


/*/{Protheus.doc} fConsulta
    (Consulta a ultima nota disponível para a matéria prima em transferencia)
    @type  Static Function
    @author Luan Woichechoscki
    @since 19/02/2025
/*/
Static Function fConsulta()

    Local nPosProd  := aScan(aHeader,{ |x| x[2] == 'D3_COD'})
    Local nPosQuant := aScan(aHeader,{ |x| x[2] == 'D3_QUANT'})
    Local cTipo     := POSICIONE("SB1", 1, xFilial("SB1")+ aCols[n, nPosProd], "B1_TIPO")

    IF cTipo == 'MP'

        fTelaNota(nPosProd, nPosQuant)

    ELSE
        Alert('Produto informado não é uma matéria prima')
    ENDIF


Return .T.


/*/{Protheus.doc} fTelaNota
    (Tela para apresentação da nota disponível)
    @type  Static Function
    @author Luan Woichechoscki
    @since 19/02/2025
/*/
Static Function fTelaNota(nPosProd, nPosQuant)

    Local oButton1
    Local oButton2
    Local oGet1
    Local oGet2
    Local oGet3
    Local oGet4
    Local oGet5
    Local oGet6
    Local oGet7
    Local oSay1
    Local oSay2
    Local oSay3
    Local oSay4
    Local oSay5
    Local oSay6
    Local oSay7
    Local cAlias := GetNextAlias()
    Private cGet1 := "Define variable value"
    Private cGet2 := "Define variable value"
    Private dGet3 := Date()
    Private nGet4 := 0
    Private cGet5 := "Define variable value"
    Private cGet6 := "Define variable value"
    Private cGet7 := "Define variable value"
    Static oDlg

    IF !EMPTY(oDlg)
        Return
    ENDIF

    IF aCols[n,nPosQuant] <= 0
        MsgInfo('Deve ser informada a quantidade antes de consultar a nota fiscal disponível', 'Aviso')
        Return
    ENDIF

    BEGINSQL Alias cAlias
        SELECT
            TOP 1 *
        FROM
            (
                SELECT
                    DISTINCT SD1.D1_FILIAL,
                    SD1.D1_DOC,
                    SD1.D1_SERIE,
                    SD1.D1_EMISSAO,
                    SD1.D1_QUANT,
                    SD1.D1_FORNECE,
                    SD1.D1_LOJA,
                    SD1.D1_LTDLP  ,
                    SA2.A2_NOME,
                    COALESCE(
                        SUM(ZA1.ZA1_QUANT) OVER(PARTITION BY ZA1_SD1DLP),
                        0
                    ) AS SOMAQUANT,
                    SD1.R_E_C_N_O_
                FROM
                    %Table:SD1% SD1
                INNER JOIN %Table:SA2% SA2
                ON SD1.D1_FORNECE = SA2.A2_COD
                    AND SD1.D1_LOJA = SA2.A2_LOJA
                    AND SA2.%NotDel%
                LEFT JOIN %Table:ZA1% ZA1
                ON ZA1.ZA1_FILIAL = SD1.D1_FILIAL
                    AND ZA1.ZA1_SD1DLP = RTRIM(D1_DOC) + RTRIM(D1_SERIE) + RTRIM(D1_FORNECE) + RTRIM(D1_LOJA)
                    AND ZA1.%NotDel%
                WHERE
                    SD1.%NotDel%
                    AND SD1.D1_COD = %Exp:aCols[n,nPosProd]%
                    AND SD1.D1_FILIAL = %Exp:xFilial('SD1')%
            ) TMP
        WHERE
            TMP.SOMAQUANT + %Exp:aCols[n,nPosQuant]% <= TMP.D1_QUANT
        ORDER BY
            TMP.D1_EMISSAO desc,
            TMP.D1_QUANT desc
    ENDSQL

    cGet1 := (cAlias)->D1_DOC
    cGet2 := (cAlias)->D1_SERIE
    dGet3 := StoD((cAlias)->D1_EMISSAO)
    nGet4 := (cAlias)->D1_QUANT
    cGet5 := (cAlias)->D1_FORNECE
    cGet6 := (cAlias)->D1_LOJA
    cGet7 := (cAlias)->A2_NOME
    cGet8 := Space(12)
    cLTDlpD1 := (cAlias)->D1_LTDLP

    DEFINE MSDIALOG oDlg TITLE "Nota Disponível" FROM 000, 000  TO 480, 450 COLORS 0, 16777215 PIXEL

    @ 015, 010 MSGET oGet1 VAR cGet1 SIZE 070, 011 OF oDlg COLORS 0, 16777215 READONLY PIXEL
    @ 005, 010 SAY oSay1 PROMPT "Nota" SIZE 025, 007 OF oDlg COLORS 0, 16777215 PIXEL
    @ 015, 100 MSGET oGet2 VAR cGet2 SIZE 040, 011 OF oDlg COLORS 0, 16777215 READONLY PIXEL
    @ 005, 100 SAY oSay2 PROMPT "Serie" SIZE 025, 007 OF oDlg COLORS 0, 16777215 PIXEL
    @ 005, 165 SAY oSay3 PROMPT "Emissão" SIZE 025, 007 OF oDlg COLORS 0, 16777215 PIXEL
    @ 015, 165 MSGET oGet3 VAR dGet3 SIZE 050, 011 OF oDlg COLORS 0, 16777215 READONLY PIXEL
    @ 035, 010 SAY oSay4 PROMPT "Quantidade" SIZE 030, 007 OF oDlg COLORS 0, 16777215 PIXEL
    @ 045, 010 MSGET oGet4 VAR nGet4 SIZE 040, 011 OF oDlg COLORS 0, 16777215 READONLY PIXEL
    @ 070, 010 SAY oSay5 PROMPT "Cod. Fornecedor" SIZE 045, 007 OF oDlg COLORS 0, 16777215 PIXEL
    @ 080, 010 MSGET oGet5 VAR cGet5 SIZE 070, 011 OF oDlg COLORS 0, 16777215 READONLY PIXEL
    @ 070, 100 SAY oSay6 PROMPT "Loja Fornecedor" SIZE 040, 007 OF oDlg COLORS 0, 16777215 PIXEL
    @ 080, 100 MSGET oGet6 VAR cGet6 SIZE 050, 011 OF oDlg COLORS 0, 16777215 READONLY PIXEL
    @ 100, 010 SAY oSay7 PROMPT "Nome" SIZE 025, 007 OF oDlg COLORS 0, 16777215 PIXEL
    @ 110, 010 MSGET oGet7 VAR cGet7 SIZE 200, 011 OF oDlg COLORS 0, 16777215 READONLY PIXEL
    @ 120, 010 SAY oSay8 PROMPT "Leia o Codigo Lote Interno" SIZE 025, 007 OF oDlg COLORS 0, 16777215 PIXEL
    @ 130, 010 MSGET oGet8 VAR cGet8 SIZE 200, 011 OF oDlg COLORS 0, 16777215 Valid (fVldLt(cGet8,cLTDlpD1))  PIXEL


    @ 160, 125 BUTTON oButton1 PROMPT "Cancelar" SIZE 037, 012 OF oDlg ACTION oDlg:End() PIXEL
    @ 160, 175 BUTTON oButton2 PROMPT "Confirmar" SIZE 037, 012 OF oDlg ACTION fConfirma(cGet8,cLTDlpD1) PIXEL

    ACTIVATE MSDIALOG oDlg CENTERED

    FreeObj(oDlg)

Return

Static Function fVldLt(cLtDlp,cLTDlpD1)
    Local lRet := .t.

    if cLtDlp != cLTDlpD1
        lRet := .f.
        FWAlertError("Lote Divergente", "Erro Delpi")
    endif
Return lRet


/*/{Protheus.doc} fConfirma
    (Confirma a nota escolhida)
    @type  Static Function
    @author Luan Woichechoscki
    @since 19/02/2025
/*/
Static Function fConfirma()

    Local nPosFor  := aScan(aHeader,{ |x| x[2] == 'D3_DLPFOR'})
    Local nPosLoj  := aScan(aHeader,{ |x| x[2] == 'D3_DLPLJF'})
    Local nPosNfe  := aScan(aHeader,{ |x| x[2] == 'D3_DLPNFE'})
    Local nPosSer  := aScan(aHeader,{ |x| x[2] == 'D3_DLPSNF'})
    Local nPosLtc  := aScan(aHeader,{ |x| x[2] == 'D3_DLPLTC'})
    if ! fVldLt(cGet8,cLTDlpD1)
        oDlg:Refresh()
        Return
    endif
    aCols[n,nPosFor] := cGet5
    aCols[n,nPosLoj] := cGet6
    aCols[n,nPosNfe] := cGet1
    aCols[n,nPosSer] := cGet2
    aCols[n,nPosLtc] := cGet8

Return oDlg:End()
