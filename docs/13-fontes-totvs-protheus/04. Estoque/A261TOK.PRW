#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

/***************************************************
* Adicionado por Gabriel Araujo - Totvs SC 2019/08 *
* Validação para não permitir que o estoque fique  *
* negativo pois o MV_ESTNEG foi desabilitado       *
* PE Transferencia entre armazens                  *
***************************************************/
User Function  A261TOK()
    Local lRet := .t.
    Local cProd := ""
    Local cLocal := ""
    Local nD3Qnt := 0
    Local nB2Qatu := 0
    Local cEol := chr(10)
    Local nY
    Local cCampo := ""
    Local cLocOri
    Local cLocDest
    Local cAlias


    if  cEmpAnt $"01_05"
        For nY := 1 To Len( aCols)
            IF !(GDDeleted(nY,aHeader,aCols))

                cProd := GDFieldGet('D3_COD',nY,,,aCols)
                cLocal  := GDFieldGet('D3_LOCAL',nY,,,aCols)
                nD3Qnt := GDFieldGet('D3_QUANT',nY,,,aCols)
                //B2_FILIAL, B2_COD, B2_LOCAL, R_E_C_N_O_, D_E_L_E_T_
                nB2Qatu := POSICIONE("SB2",1,XfILIAL("SD3")+cProd+cLocal,"B2_QATU")

                IF nD3Qnt > nB2Qatu

                    MSGALERT("Quantidade da Transferencia superior ao saldo em estoque"+cEol+"Produto: " + cProd ,"Delpi")
                    lRet := .F.
                    EXIT

                endif

                cLocOri  := aCols[nY, aScan(aHeader, {|x| AllTrim(Upper(x[1])) == 'ARMAZEM ORIG.'})]
                cLocDest := aCols[nY, aScan(aHeader, {|x| AllTrim(Upper(x[1])) == 'ARMAZEM DESTINO'})]

                cPrdOri   := aCols[nY, aScan(aHeader, {|x|  'PROD' $ AllTrim(Upper(x[1])) .AND.    'ORI' $ AllTrim(Upper(x[1]))})]
                cPrdDest  := aCols[nY, aScan(aHeader, {|x|  'PROD' $ AllTrim(Upper(x[1])) .AND.    'DEST' $ AllTrim(Upper(x[1]))})]

                cDscOri   := aCols[nY, aScan(aHeader, {|x|  'DESC' $ AllTrim(Upper(x[1])) .AND.    'ORI' $ AllTrim(Upper(x[1]))})]
                cDscDest  := aCols[nY, aScan(aHeader, {|x|  'DESC' $ AllTrim(Upper(x[1])) .AND.    'DEST' $ AllTrim(Upper(x[1]))})]

                if cPrdOri != cPrdDest  .and. !FWIsAdmin()

                    cMsg :="Não é Permitido transferir produtos Origem / Destino diferentes "+cEol
                    cMsg += "Produto Origem "+ ALLTRIM(cPrdOri)+" - "+ALLTRIM(cDscOri)+cEol
                    cMsg += "Produto Destino "+ ALLTRIM(cPrdDest)+" - "+ALLTRIM(cDscDest)
                    FWAlertWarning(cMsg , "Delpi -Controladoria")

                    lRet := .f.
                    exit

                endif

                /*Gabriel comentado porque entrou o controle de lote padrao            */
                //    IF POSICIONE("SB1", 1, xFilial("SB1")+cProd, "B1_TIPO") == 'MP' .AND. cLocOri = '01' .AND. cLocDest = '99'
                //        Do Case
                //            Case EMPTY(GDFieldGet('D3_DLPSNF',nY,,,aCols))
                //                cCampo := 'D3_DLPSNF'
                //            Case EMPTY(GDFieldGet('D3_DLPNFE',nY,,,aCols))
                //                cCampo := 'D3_DLPNFE'
                //            Case EMPTY(GDFieldGet('D3_DLPLJF',nY,,,aCols))
                //                cCampo := 'D3_DLPLJF'
                //            Case EMPTY(GDFieldGet('D3_DLPFOR',nY,,,aCols))
                //                cCampo := 'D3_DLPFOR'
                //            Case EMPTY(GDFieldGet('D3_DLPLTC',nY,,,aCols))
                //                cCampo := 'D3_DLPLTC'
                //            OtherWise
                //                cCampo := ''
                //        EndCase
                //
                //        IF !EMPTY(cCampo)
                //            Help( ,, 'Help',, "Favor verificar o preenchimento do campo: "+cCampo, 1, 0,,,,,, {"Preencher a informação necessária"})
                //            lRet := .F.
                //            EXIT
                //        ENDIF
                //
                //        SA2->(dbSetOrder(1))
                //        IF !SA2->(MsSeek(xFilial('SA2') + GDFieldGet('D3_DLPFOR',nY,,,aCols) + GDFieldGet('D3_DLPLJF',nY,,,aCols) ))
                //            Help( ,, 'Help',, "Favor verificar o preenchimento do campo de forncedor", 1, 0,,,,,, {"Realizar o cadastro do fornecedor informado"})
                //            lRet := .F.
                //            EXIT
                //        ENDIF
                //
                //        cAlias := GetNextAlias()
                //        BEGINSQL Alias cAlias
                //            SELECT
                //                TOP 1 *
                //            FROM
                //                (
                //                    SELECT
                //                        DISTINCT SD1.D1_FILIAL,
                //                        SD1.D1_DOC,
                //                        SD1.D1_SERIE,
                //                        SD1.D1_EMISSAO,
                //                        SD1.D1_QUANT,
                //                        SD1.D1_FORNECE,
                //                        SD1.D1_LOJA,
                //                        SA2.A2_NOME,
                //                        COALESCE(
                //                            SUM(ZA1.ZA1_QUANT) OVER(PARTITION BY ZA1_SD1DLP),
                //                            0
                //                        ) AS SOMAQUANT,
                //                        SD1.R_E_C_N_O_
                //                    FROM
                //                        %Table:SD1% SD1
                //                    INNER JOIN %Table:SA2% SA2
                //                    ON SD1.D1_FORNECE = SA2.A2_COD
                //                        AND SD1.D1_LOJA = SA2.A2_LOJA
                //                        AND SA2.%NotDel%
                //                    LEFT JOIN %Table:ZA1% ZA1
                //                    ON ZA1.ZA1_FILIAL = SD1.D1_FILIAL
                //                        AND ZA1.ZA1_SD1DLP = RTRIM(D1_DOC) + RTRIM(D1_SERIE) + RTRIM(D1_FORNECE) + RTRIM(D1_LOJA)
                //                        AND ZA1.%NotDel%
                //                    WHERE
                //                        SD1.%NotDel%
                //                        AND SD1.D1_DOC = %Exp:GDFieldGet('D3_DLPNFE',nY,,,aCols)%
                //                        AND SD1.D1_SERIE = %Exp:GDFieldGet('D3_DLPSNF',nY,,,aCols)%
                //                        AND SD1.D1_FORNECE = %Exp:GDFieldGet('D3_DLPFOR',nY,,,aCols)%
                //                        AND SD1.D1_LOJA = %Exp:GDFieldGet('D3_DLPLJF',nY,,,aCols)%
                //                        AND SD1.D1_FILIAL = %Exp:xFilial('SD1')%
                //                ) TMP
                //            WHERE
                //                TMP.SOMAQUANT + %Exp:GDFieldGet('D3_QUANT',nY,,,aCols)% <= TMP.D1_QUANT
                //            ORDER BY
                //                TMP.D1_EMISSAO desc,
                //                TMP.D1_QUANT desc
                //        ENDSQL
                //
                //        IF (cAlias)->(EOF())
                //            Help( ,, 'Help',, "Favor verificar o preenchimento da nota fiscal. Quantidade informada maior que o saldo para a nota", 1, 0,,,,,, {"Verificar a nota fiscal informada ou utlizar o F7 para verificar a nota disponível!"})
                //            lRet := .F.
                //            EXIT
                //        ENDIF
                //
                //        (cAlias)->(dbCloseArea())
                //
                //    ENDIF

            endif
        next nY
    endif

Return lRet
