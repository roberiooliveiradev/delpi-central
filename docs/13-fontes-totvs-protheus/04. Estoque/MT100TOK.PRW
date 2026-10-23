#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"

/***************************************************
* Adicionado por Gabriel Araujo - Totvs SC 2019/08 *
* Validação para não permitir que o estoque fique  *
* negativo pois o MV_ESTNEG foi desabilitado       *
* Documento de Entrada                             *
***************************************************/


User Function MT100TOK()        // incluido pelo assistente de conversao do AP5 IDE em 25/08/01
    Local cArea     := GetArea()
    lRet :=  VldChvNfe()
    IF lRet
        lRet := fVldMP()
    endif
    restarea(cArea)
Return lRet

Static Function VldChvNfe()
    Local lRet := .T.
    Local nQtde := 0
    lOCAL cSql := ""
    if !IsInCallStack("MATA920")
        if 	 (ALLTRIM(cEspecie) $ "SPED/CTE") .AND. ALLTRIM(cFormul) <> 'S'

            cSql := " SELECT COUNT(*) QTD FROM dbo."+ RETSQLNAME("SF1") +  " SF1(NOLOCK) "
            cSql += " WHERE SF1.D_E_L_E_T_ = " + VALTOSQL(' ')
            cSql += " AND SF1.F1_EMISSAO >= "+VALTOSQL('20170101')
            cSql += " AND SF1.F1_CHVNFE = " + VALTOSQL(IIF(!EMPTY(M->F1_CHVNFE),M->F1_CHVNFE,aNFEDanfe[13]) )
            if l103Class
                cSql += " AND SF1.F1_DOC +F1_SERIE != " + VALTOSQL(cNFiscal+cSerie)
                //     cSql += " AND SF1.F1_SERIE != " + VALTOSQL(cSerie)
            endif
            CONOUT(cSql)


            If Select('TMPDSF1') <> 0
                TMPDSF1->(dbCloseArea())
            Endif


            TCQuery cSql Alias TMPDSF1 New



            nQtde := TMPDSF1->QTD

            ///IF  ( ( alltrim(cespecie)$"SPED" ) .AND. ( LEN(ALLTRIM(CSERIE)) < 3 .OR. LEN(ALLTRIM(CNFISCAL)) < 9   .or. nQtde > 0 ) )
            IF nQtde > 0

                FWAlertError("Atenção prezado usuário, A Chave já existe no Sistema","Delpi")

                lRet := .f.

            ENDIF
            if 	 (ALLTRIM(cEspecie) $ "CTE") .AND. EMPTY(SubStr(aNFEDanfe[14],1,1))
                FWAlertError("Atenção Obrigatorio preenchimento do Tipo de frete","Delpi")
                lRet := .f.
            ENDIF
        ENDIF
    ENDIF

Return lRet



Static Function fVldMP()
    Local lRet := .t.
    Local cEol := chr(10)
    lOCAL nX := Nil
    Local lDocEntr :=If(Type("l103GAuto") == "U" ,.F., !l103GAuto)



    IF lDocEntr .and. ALLTRIM(cEspecie) $"SPED" .and. ( Inclui .or. l103Class) .AND. ALLTRIM(cTipo)=="N";
            .and.!( alltrim(RetCodUsr()) $"000008")

        FOR nX := 1 to Len(aCols)


            cCodPrd:= GdFieldGet("D1_COD",nX)
            cTpPrd := posicione("SB1",1,XFILIAL("SB1")+cCodPrd,"B1_TIPO")
            nEmin := posicione("SBZ",1,XFILIAL("SBZ")+cCodPrd,"BZ_EMIN")

            IF cTpPrd == "MP" .OR. nEmin > 0

                //Monta uma mensagem com quebra de linhas
                cMensagem := "Não é possivel incluir a Nota Fiscal!"+ cEol
                cMensagem += "Pois existe(m) produto(s) do tipo Materia Prima"+ cEol
                cMensagem += "Ou tem estoque Minimo"+ cEol
                cMensagem += "Gentileza Utilizar o Importador de XML"
                FWAlertWarning(cMensagem, "Delpi - Compras")

                lRet := .f.
                exit
            endif

        NEXT nX
    endif
Return lRet
