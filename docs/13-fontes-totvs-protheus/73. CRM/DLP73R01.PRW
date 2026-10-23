#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"


USER FUNCTION DLP73R01()
    Private aCpoCab := {}
    Private aCpoIte := {}

    Private cPerg       := "DLP73R01"
    Private  oReport    := nil
    Private oSect1      := Nil
    Private oSect2      := Nil
    //  Private oSect3      := Nil
    PRIVATE aPars :={}
    pRIVATE oBreak1     := NIL
    //pRIVATE oBreak2     := NIL
    //pRIVATE oBreak3     := NIL
    Private QRY1 	   := GetNextAlias()
    Private QRY2 	   := GetNextAlias()
    //  Private QRY3 	   := GetNextAlias()
    Private cEol := chr(10)

    //Pergunte(cPerg ,.f.)

    FWMsgRun(, {|| fProc() }, "Processando", "Gerando Relatorio...")


rETURN


static function fProc()

    oReport := RptDef(cPerg)

RETURN


Static Function RptDef(cNome)
    Local oBreak
    Local oFunction


    aadd(aCpoCab, "AD1_NROPOR")
    aadd(aCpoCab, "AD1_DESCRI")
    aadd(aCpoCab, "AD1_DATA")
    aadd(aCpoCab, "AD1_DTINI")
    aadd(aCpoCab, "AD1_DTFIM")
    aadd(aCpoCab, "A3_COD")
    aadd(aCpoCab, "A3_NOME")
    aadd(aCpoCab, "AD1_CODCLI")
    aadd(aCpoCab, "AD1_LOJCLI")
    aadd(aCpoCab, "A1_NOME")
    aadd(aCpoCab, "AD1_STAGE")
    aadd(aCpoCab, "AC2_DESCRI")
    aadd(aCpoCab, "AD1_NUMORC")


    aadd(aCpoIte, "ADJ_ITEM")
    aadd(aCpoIte, "ADJ_PROD")
    aadd(aCpoIte, "B1_DESC")
    aadd(aCpoIte, "ADJ_QUANT")
    aadd(aCpoIte, "ADJ_PRUNIT")
    aadd(aCpoIte, "ADJ_VALOR")
    aadd(aCpoIte, "ADJ_NUMORC")
    aadd(aCpoIte, "ADJ_PROPOS")

    Pergunte(cPerg, .F.)
    For ni := 1 to 14

        aadd(aPars, 	&("mv_par"+StrZero(ni,2)) )

    Next ni
    oReport := TReport():New(cNome,"Relatorio Oportunidade de Vendas",cNome,{|oReport| ReportPrint()},;
        "Relatorio Oportunidade de Vendas")

    oReport:SetLandscape(.T.)
    oReport:SetEnvironment(2)
    oReport:DisableOrientation()
    oReport:oPage:nPaperSize := 9
    oReport:SetColSpace(3)
    oReport:ShowParamPage()
    oSect1	:= TRSection():New(oReport, "01_DADOS","QRY1")
    oSect2	:= TRSection():New(oReport, "02_TENS","QRY2")
    // oSect3	:= TRSection():New(oReport, "03_ITENS","QRY3")

    For n1 := 1 to Len(aCpoCab)
        TRCell():New( oSect1,aCpoCab[n1],"QRY1",;
            GetSx3Cache(aCpoCab[n1],"X3_TITULO") ,;
            GetSx3Cache(aCpoCab[n1],"X3_PICTURE")  ,;
            GetSx3Cache(aCpoCab[n1],"X3_TAMANHO")+2 ,.f.)
    Next n1

    For n2 := 1 to Len(aCpoIte)
        TRCell():New( oSect2,aCpoIte[n2],"QRY2",;
            GetSx3Cache(aCpoIte[n2],"X3_TITULO") ,;
            GetSx3Cache(aCpoIte[n2],"X3_PICTURE")  ,;
            GetSx3Cache(aCpoIte[n2],"X3_TAMANHO"),.f. )
    Next n2

    // TRCell():New( oSect1, "D1_FILIAL"       ,"QRY1"  ,GetSx3Cache("D1_FILIAL","X3_TITULO")    			,GetSx3Cache("D1_FILIAL","X3_PICTURE")  ,6 	)//,GetSx3Cache("D1_FILIAL","X3_TAMANHO") +nTCol     ,.f.,, 'RIGHT'  ,, 'RIGHT' )
    //
    //
    // TRCell():New( oSect1, "M0_NOME"         ,"QRY1"  ,""   			,GetSx3Cache("M0_NOME","X3_PICTURE")  ,30	)//+nTCol     ,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect1,"D1_TOTAL"			,"QRY1"	,""   	,GetSx3Cache("D1_TOTAL"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect2,"D1_CC"		        ,"QRY2"	,GetSx3Cache("D1_CC","X3_TITULO")    		   ,GetSx3Cache("D1_CC","X3_PICTURE")   	)//,GetSx3Cache("D1_EMISSAO","X3_TAMANHO") +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect2,"CTT_DESC01"		,"QRY2"	,"Centro de Custo"   		,,20	)//,20										+nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect3,"D1_EMISSAO"		,"QRY3"	,GetSx3Cache("D1_EMISSAO"    ,"X3_TITULO")    	,GetSx3Cache("D1_EMISSAO"    ,"X3_PICTURE")  	)//,GetSx3Cache("A1_EST","X3_TAMANHO") 	+nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect3,"D1_FORNECE"		,"QRY3"	,GetSx3Cache("D1_FORNECE"    ,"X3_TITULO")    	,GetSx3Cache("D1_FORNECE"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect3,"D1_LOJA"			,"QRY3"	,GetSx3Cache("D1_LOJA"    ,"X3_TITULO")    	    ,GetSx3Cache("D1_LOJA"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect3,"A2_NOME"			,"QRY3"	,GetSx3Cache("A2_NOME"    ,"X3_TITULO")    	    ,GetSx3Cache("A2_NOME"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect3,"D1_DOC"			,"QRY3"	,GetSx3Cache("D1_DOC"    ,"X3_TITULO")    	    ,GetSx3Cache("D1_DOC"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect3,"D1_SERIE"			,"QRY3"	,GetSx3Cache("D1_SERIE"    ,"X3_TITULO")    	,GetSx3Cache("D1_SERIE"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect3,"D1_PEDIDO"			,"QRY3"	,GetSx3Cache("D1_PEDIDO"    ,"X3_TITULO")    	,GetSx3Cache("D1_PEDIDO"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect3,"D1_COD"			,"QRY3"	,GetSx3Cache("D1_COD"    ,"X3_TITULO")    	    ,GetSx3Cache("D1_COD"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect3,"B1_DESC"			,"QRY3"	,GetSx3Cache("B1_DESC"    ,"X3_TITULO")    	    ,GetSx3Cache("B1_DESC"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect3,"C7_OBS"			,"QRY3"	,GetSx3Cache("C7_OBS"    ,"X3_TITULO")    	    ,GetSx3Cache("C7_OBS"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    // TRCell():New(oSect3,"D1_TOTAL"			,"QRY3"	,GetSx3Cache("D1_TOTAL"    ,"X3_TITULO")    	,GetSx3Cache("D1_TOTAL"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )

    oBreak1 := TRBreak():New(oSect1,{||  QRY1->(AD1_FILIAL)+ QRY1->(AD1_NROPOR)},{|| "Total Filial" },.T.,,.F.)
    //  TRFunction():New(,,,oBreak1 ,,,/*uFormua*/,.F./*lEndSection*/,.t./*lEndReport*/,.F./*lEndPage*/ )
    //oBreak3 := TRBreak():New(oSect3,{||  QRY3->(D1_CC)},{|| "Total Centro de Custo" },.F.,,.F.)
    //TRFunction():New(oSect3:Cell("D1_TOTAL"),,"SUM",oBreak3 ,,X3PICTURE("D2_TOTAL"),/*uFormua*/,.F./*lEndSection*/,.F./*lEndReport*/,.F./*lEndPage*/ )

    oReport:SetTotalInLine(.F.)
    oSect1:SetHeaderBreak(.T.)   //Imprime o cabecalho das celulas apos a quebra
    oSect2:SetHeaderBreak(.T.)   //Imprime o cabecalho das celulas apos a quebra
    oReport:PrintDialog()

RETURN (oReport)

Static Function ReportPrint()
    Local cSql1 :=""
    Local cSql2 :=""
    Local cSql3 :=""

    oSect1       := oReport:Section(1)
    oSect2       := oReport:Section(2)

    cSql1:= "SELECT  AD1.AD1_FILIAL, AD1_NROPOR,AD1_DESCRI,AD1_DATA,AD1_DTINI,AD1_DTFIM," + cEol
    cSql1+= " CASE WHEN AD1_CODCLI != '' THEN  AD1_CODCLI ELSE AD1_PROSPE END  AD1_CODCLI," + cEol
    cSql1+= " CASE WHEN AD1_LOJCLI != '' THEN  AD1_LOJCLI ELSE AD1_LOJCLI END  AD1_LOJCLI," + cEol
    cSql1+= " CASE WHEN SA1.A1_NOME != '' THEN SA1.A1_NOME  ELSE SUS.US_NOME END A1_NOME," + cEol
    cSql1+= " AD1_STAGE,AD1_NUMORC,AC2.AC2_DESCRI,A3_COD,A3_NOME " + cEol
    cSql1+= "FROM dbo." + RetSqlName("AD1") + " AD1 (NOLOCK) " + cEol
    cSql1+= "   LEFT JOIN dbo." + RetSqlName("SA1") + "  SA1(NOLOCK) ON SA1.D_E_L_E_T_ ='' " + cEol
    cSql1+= "           AND SA1.A1_FILIAL =''  " + cEol
    cSql1+= "           AND AD1.AD1_CODCLI = SA1.A1_COD  " + cEol
    cSql1+= "           AND AD1.AD1_LOJCLI = SA1.A1_LOJA " + cEol
    cSql1+= "   LEFT JOIN dbo." + RetSqlName("SUS") + "  SUS (NOLOCK) ON SUS.D_E_L_E_T_= ''  " + cEol
    cSql1+= "           AND SUS.US_FILIAL =''  " + cEol
    cSql1+= "           AND AD1.AD1_PROSPE = SUS.US_COD  " + cEol
    cSql1+= "           AND AD1.AD1_LOJPRO = SUS.US_LOJA  " + cEol
    cSql1+= "   LEFT JOIN dbo." + RetSqlName("AC2") + " AC2 (NOLOCK) ON AC2.D_E_L_E_T_= '' " + cEol
    cSql1+= "           AND AC2.AC2_FILIAL ='' " + cEol
    cSql1+= "           AND AC2.AC2_PROVEN = AD1.AD1_PROVEN " + cEol
    cSql1+= "           AND AD1.AD1_STAGE = AC2.AC2_STAGE " + cEol
    cSql1+= "   LEFT JOIN dbo." + RetSqlName("SA3") + " SA3 (NOLOCK) ON SA3.D_E_L_E_T_ ='' " + cEol
    cSql1+= "           AND SA3.A3_FILIAL =''   " + cEol
    cSql1+= "           AND SA3.A3_COD = AD1.AD1_VEND  " + cEol
    cSql1+= "WHERE AD1.D_E_L_E_T_ = '' " + cEol
    cSql1+= "      AND AD1.AD1_FILIAL = " + valtosql(XFILIAL("AD1") ) + cEol
    cSql1+= "      AND AD1.AD1_NROPOR	    BETWEEN "+ valtosql(aPars[01]) + " AND " +  valtosql(aPars[02]  ) +  cEol
    cSql1+= "      AND AD1.AD1_STAGE	    BETWEEN "+ valtosql(aPars[03])  +"  AND " + valtosql(aPars[04]  ) +  cEol
    cSql1+= "      AND( AD1.AD1_CODCLI	    BETWEEN "+ valtosql(aPars[05])  +"  AND " + valtosql(aPars[06]  ) +  cEol
    cSql1+= "		OR AD1.AD1_PROSPE	    BETWEEN "+ valtosql(aPars[05])  +"  AND " + valtosql(aPars[06]  ) +" ) " + cEoL
    cSql1+= "      AND( AD1.AD1_LOJPRO	    BETWEEN "+ valtosql(aPars[07])  +"  AND " + valtosql(aPars[08]  ) +  cEol
    cSql1+= "          OR AD1.AD1_LOJCLI	BETWEEN "+ valtosql(aPars[07])  +"  AND " + valtosql(aPars[08]  ) +" ) " + cEoL
    cSql1+= "      AND AD1.AD1_DATA         BETWEEN "+ valtosql(DTOS(aPars[09]))  +"  AND " + valtosql(DTOS(aPars[10]  )) +  cEol
    cSql1+= "      AND AD1.AD1_DTINI        BETWEEN "+ valtosql(DTOS(aPars[11]))  +"  AND " + valtosql(DTOS(aPars[12]  )) +  cEol
    cSql1+= "      AND AD1.AD1_DTFIM        BETWEEN "+ valtosql(DTOS(aPars[13]))  +"  AND " + valtosql(DTOS(aPars[14]  )) +  cEol
    cSql1+= "ORDER BY AD1.AD1_FILIAL,AD1.AD1_NROPOR  "

    If (Select("QRY1") <> 0)
        dbSelectArea("QRY1")
        dbCloseArea()
    Endif

    CONOUT("cSql1"+cEol+cSql1)

    TCQuery cSql1 NEW  ALIAS "QRY1"

    While QRY1->(!Eof())

        oSect1:init()
        For n1 := 1 to Len(aCpoCab)

            if GetSx3Cache(aCpoCab[n1],"X3_TIPO") $"D"
                oSect1:Cell(aCpoCab[n1]):SetValue( DTOC(STOD( &("QRY1->"+aCpoCab[n1])   ) )	 )
            ELSE
                oSect1:Cell(aCpoCab[n1]):SetValue( &("QRY1->"+aCpoCab[n1])	 )
            ENDIF
        Next n1

        //    oSect1:Cell("D1_FILIAL"):SetValue(QRY1->D1_FILIAL	 )

        //  oSect1:Cell("M0_NOME"):SetValue( FWFilName  (cEmpAnt,QRY1->D1_FILIAL)    )
        //   oSect1:Cell("D1_TOTAL"):Hide()
        oSect1:Printline()

        If (Select("QRY2") <> 0)
            dbSelectArea("QRY2")
            dbCloseArea()
        Endif

        cSql2 := " SELECT '001' ADJ_ITEM,AD1.AD1_CODPRO ADJ_PROD,B1_DESC,0 ADJ_QUANT,0 ADJ_PRUNIT,0 ADJ_VALOR, " + cEol
        cSql2 += " AD1.AD1_NUMORC ADJ_NUMORC,AD1.AD1_PROPOS ADJ_PROPOS " + cEol
        cSql2 += " FROM dbo." + RetSqlName("AD1") + " AD1 (NOLOCK) " + cEol
        cSql2 += "     JOIN dbo." + RetSqlName("SB1") + " SB1 (NOLOCK)
        cSql2 += "         ON SB1.D_E_L_E_T_ = ''  " + cEol
        cSql2 += "            AND SB1.B1_FILIAL = '' " + cEol
        cSql2 += "            AND SB1.B1_COD = AD1.AD1_CODPRO " + cEol
        cSql2 += " WHERE AD1.D_E_L_E_T_ = '' " + cEol
        cSql2 += "       AND AD1.AD1_FILIAL =  " + valtosql(XFILIAL("AD1") ) + cEol
        cSql2 += "       AND AD1.AD1_NROPOR = " + valtosql(QRY1->AD1_NROPOR) + cEol
        cSql2 += " UNION " + cEol
        cSql2 += " SELECT ADJ_ITEM,ADJ_PROD,B1_DESC,ADJ_QUANT,ADJ_PRUNIT,ADJ_VALOR,ADJ_NUMORC,ADJ_PROPOS " + cEol
        cSql2 += " FROM dbo." + RetSqlName("ADJ") + "  ADJ (NOLOCK) " + cEol
        cSql2 += "     JOIN dbo." + RetSqlName("SB1") + "  SB1 (NOLOCK) " + cEol
        cSql2 += "         ON SB1.D_E_L_E_T_ = '' " + cEol
        cSql2 += "            AND SB1.B1_FILIAL = '' " + cEol
        cSql2 += "            AND SB1.B1_COD = ADJ.ADJ_PROD " + cEol
        cSql2 += " WHERE ADJ.D_E_L_E_T_ = '' " + cEol
        cSql2 += "       AND ADJ.ADJ_FILIAL = " + valtosql(XFILIAL("AD1") ) + cEol
        cSql2 += "       AND ADJ.ADJ_NROPOR =  " + valtosql(QRY1->AD1_NROPOR) + cEol
        cSql2 += " ORDER BY 1; "


        CONOUT("cSql2"+cEol+cSql2)

        TCQuery cSql2 NEW  ALIAS "QRY2"

        While QRY2->(!Eof())

            oSect2:init()

            For n2 := 1 to Len(aCpoIte)
                oSect2:Cell(aCpoIte[n2]):SetValue( &("QRY2->"+aCpoIte[n2])	 )
            Next n2

            //   oSect2:Cell("D1_CC"):SetValue(QRY2->D1_CC	 )
            //   oSect2:Cell("CTT_DESC01"):SetValue(QRY2->CTT_DESC01	 )
            oSect2:Printline()
            QRY2->(dbSkip())


        EndDo

        oSect2:Finish()
        oReport:SkipLine(2)
        QRY1->(dbSkip())

    EndDo
    oSect1:Finish()

Return Nil
