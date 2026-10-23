#include "rwmake.ch"

#INCLUDE 'PROTHEUS.CH'
#INCLUDE 'PARMTYPE.CH'
#INCLUDE 'TOPCONN.CH'

User Function DLP34R01()


    /*=====================================================================*\
    || ################################################################# # ||
    || # Programa: DLP34R01                                              # ||
    || # Desc: Relatorio Custos                                          # ||
    || # Tabelas Usadas (Alfabética): SD1 ; SF4 ; SB1 ; SF1 ; SA1 ; DHI  # ||
    || # Data - 03/2020 # Autor: Gabriel Araujo                          # ||
    || ################################################################### ||
    \*=====================================================================*/

    Private cPerg       := "DLP34R01"
    Private  oReport    := nil
    Private oSect1      := Nil
    Private oSect2      := Nil
    Private oSect3      := Nil
    pRIVATE oBreak3     := NIL
    pRIVATE oBreak1     := NIL
    pRIVATE oBreak2     := NIL
    Private QRY1 	   := GetNextAlias()
    Private QRY2 	   := GetNextAlias()
    Private QRY3 	   := GetNextAlias()
    Private cEol := chr(10)

    Pergunte(cPerg ,.f.)

    FWMsgRun(, {|| fProc() }, "Processando", "Gerando Relatorio...")

Return

static function fProc()

    oReport := RptDef(cPerg)

RETURN


Static Function RptDef(cNome)
    Local oBreak
    Local oFunction
    oReport := TReport():New(cNome,"Relatorio Despesas por Centro de Custo",cNome,{|oReport| ReportPrint()},"Relatorio Despesas por Centro de Custo Delpi")

    oReport:SetLandscape(.T.)
    oReport:SetEnvironment(2)
    oReport:DisableOrientation()
    oReport:oPage:nPaperSize := 9
    oReport:SetColSpace(3)
    oReport:ShowParamPage()
    oSect1	:= TRSection():New(oReport, "01_DADOS","QRY1")
    oSect2	:= TRSection():New(oReport, "02_CC","QRY2")
    oSect3	:= TRSection():New(oReport, "03_ITENS","QRY3")

    TRCell():New( oSect1, "D1_FILIAL"       ,"QRY1"  ,GetSx3Cache("D1_FILIAL","X3_TITULO")    			,GetSx3Cache("D1_FILIAL","X3_PICTURE")  ,6 	)//,GetSx3Cache("D1_FILIAL","X3_TAMANHO") +nTCol     ,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New( oSect1, "M0_NOME"         ,"QRY1"  ,""   			,GetSx3Cache("M0_NOME","X3_PICTURE")  ,30	)//+nTCol     ,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect1,"D1_TOTAL"			,"QRY1"	,""   	,GetSx3Cache("D1_TOTAL"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect2,"D1_CC"		        ,"QRY2"	,GetSx3Cache("D1_CC","X3_TITULO")    		   ,GetSx3Cache("D1_CC","X3_PICTURE")   	)//,GetSx3Cache("D1_EMISSAO","X3_TAMANHO") +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect2,"CTT_DESC01"		,"QRY2"	,"Centro de Custo"   		,,20	)//,20										+nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect3,"D1_EMISSAO"		,"QRY3"	,GetSx3Cache("D1_EMISSAO"    ,"X3_TITULO")    	,GetSx3Cache("D1_EMISSAO"    ,"X3_PICTURE")  	)//,GetSx3Cache("A1_EST","X3_TAMANHO") 	+nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect3,"D1_FORNECE"		,"QRY3"	,GetSx3Cache("D1_FORNECE"    ,"X3_TITULO")    	,GetSx3Cache("D1_FORNECE"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect3,"D1_LOJA"			,"QRY3"	,GetSx3Cache("D1_LOJA"    ,"X3_TITULO")    	    ,GetSx3Cache("D1_LOJA"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect3,"A2_NOME"			,"QRY3"	,GetSx3Cache("A2_NOME"    ,"X3_TITULO")    	    ,GetSx3Cache("A2_NOME"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect3,"D1_DOC"			,"QRY3"	,GetSx3Cache("D1_DOC"    ,"X3_TITULO")    	    ,GetSx3Cache("D1_DOC"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect3,"D1_SERIE"			,"QRY3"	,GetSx3Cache("D1_SERIE"    ,"X3_TITULO")    	,GetSx3Cache("D1_SERIE"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect3,"D1_PEDIDO"			,"QRY3"	,GetSx3Cache("D1_PEDIDO"    ,"X3_TITULO")    	,GetSx3Cache("D1_PEDIDO"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect3,"D1_COD"			,"QRY3"	,GetSx3Cache("D1_COD"    ,"X3_TITULO")    	    ,GetSx3Cache("D1_COD"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect3,"B1_DESC"			,"QRY3"	,GetSx3Cache("B1_DESC"    ,"X3_TITULO")    	    ,GetSx3Cache("B1_DESC"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect3,"C7_OBS"			,"QRY3"	,GetSx3Cache("C7_OBS"    ,"X3_TITULO")    	    ,GetSx3Cache("C7_OBS"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )
    TRCell():New(oSect3,"D1_TOTAL"			,"QRY3"	,GetSx3Cache("D1_TOTAL"    ,"X3_TITULO")    	,GetSx3Cache("D1_TOTAL"    ,"X3_PICTURE")  )//,GetSx3Cache("A1_PESSOA","X3_TAMANHO")  +nTCol,.f.,, 'RIGHT'  ,, 'RIGHT' )

    oBreak1 := TRBreak():New(oSect1,{||  QRY1->(D1_FILIAL)},{|| "Total Filial" },.F.,,.t.)

    TRFunction():New(oSect1:Cell("D1_TOTAL"),,"SUM",oBreak1 ,,X3PICTURE("D2_TOTAL"),/*uFormua*/,.F./*lEndSection*/,.t./*lEndReport*/,.F./*lEndPage*/ )

    oBreak3 := TRBreak():New(oSect3,{||  QRY3->(D1_CC)},{|| "Total Centro de Custo" },.F.,,.F.)
    TRFunction():New(oSect3:Cell("D1_TOTAL"),,"SUM",oBreak3 ,,X3PICTURE("D2_TOTAL"),/*uFormua*/,.F./*lEndSection*/,.F./*lEndReport*/,.F./*lEndPage*/ )

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
    oSect3       := oReport:Section(3)

    IF MV_PAR13 == 1

        cCond	:=	"  D1_FILIAL        BETWEEN " + VALTOSQL(MV_PAR01) + " AND " + VALTOSQL(MV_PAR02)+ cEol
        cCond	+=	" AND D1_EMISSAO    BETWEEN " + VALTOSQL(MV_PAR03) + " AND " + VALTOSQL(MV_PAR04)+ cEol
        cCond	+=	" AND D1_CC         BETWEEN " + VALTOSQL(MV_PAR05) + " AND " + VALTOSQL(MV_PAR06)+ cEol
        cCond	+=	" AND D1_FORNECE    BETWEEN " + VALTOSQL(MV_PAR07) + " AND " + VALTOSQL(MV_PAR08)+ cEol
        cCond	+=	" AND D1_LOJA       BETWEEN " + VALTOSQL(MV_PAR09) + " AND " + VALTOSQL(MV_PAR10)+ cEol

        cCond	+=	" AND D1_COD        BETWEEN " + VALTOSQL(MV_PAR11) + " AND " + VALTOSQL(MV_PAR12)
        cSql1 := "SELECT  D1_FILIAL  ,SUM(D1_TOTAL)D1_TOTAL FROM VW_PROTHEUS_CUSTO_ANALITIC_"+cEmpAnt+"  WHERE "+cEol
        cSql1 += cCond + cEol
        cSql1 += "GROUP BY D1_FILIAL ORDER BY 1 "

        cSql2 := "SELECT DISTINCT D1_CC  ,CTT_DESC01 FROM VW_PROTHEUS_CUSTO_ANALITIC_"+cEmpAnt+"  WHERE "+cEol
        cSql2+=cCond

        cSql3 := "SELECT D1_CC,D1_EMISSAO	,D1_FORNECE	,D1_LOJA	,A2_NOME	,D1_DOC	,D1_SERIE	,D1_PEDIDO	,D1_COD	,B1_DESC	,C7_OBS	,D1_TOTAL FROM VW_PROTHEUS_CUSTO_ANALITIC_"+cEmpAnt+"  WHERE "
        cSql3 += cCond + cEol
    else

        cCond	:=	"  D1_FILIAL        BETWEEN " + VALTOSQL(MV_PAR01) + " AND " + VALTOSQL(MV_PAR02)+ cEol
        cCond	+=	" AND D1_EMISSAO    BETWEEN " + VALTOSQL(MV_PAR03) + " AND " + VALTOSQL(MV_PAR04)+ cEol
        cCond	+=	" AND D1_CC         BETWEEN " + VALTOSQL(MV_PAR05) + " AND " + VALTOSQL(MV_PAR06)+ cEol
        cCond	+=	" AND D1_FORNECE    BETWEEN " + VALTOSQL(MV_PAR07) + " AND " + VALTOSQL(MV_PAR08)+ cEol
        cCond	+=	" AND D1_LOJA       BETWEEN " + VALTOSQL(MV_PAR09) + " AND " + VALTOSQL(MV_PAR10)+ cEol

        //cCond	+=	" AND D1_COD        BETWEEN " + VALTOSQL(MV_PAR11) + " AND " + VALTOSQL(MV_PAR12)
        cSql1 := "SELECT  D1_FILIAL , SUM(D1_TOTAL) D1_TOTAL FROM VW_PROTHEUS_CUSTO_SINT_"+cEmpAnt+"   WHERE "+cEol
        cSql1 += cCond + cEol
        cSql1 += "GROUP BY D1_FILIAL ORDER BY 1 "

        cSql2 := "SELECT DISTINCT D1_CC  ,CTT_DESC01 FROM VW_PROTHEUS_CUSTO_SINT_"+cEmpAnt+"  WHERE "+cEol
        cSql2+=cCond

        cSql3 := "SELECT D1_CC,D1_EMISSAO	,D1_FORNECE	,D1_LOJA	,A2_NOME	,D1_DOC	,D1_SERIE	,D1_PEDIDO	,C7_OBS	,D1_TOTAL FROM VW_PROTHEUS_CUSTO_SINT_"+cEmpAnt+"  WHERE "
        cSql3 += cCond + cEol

        oSect3:Cell("D1_COD"):Disable()
        oSect3:Cell("B1_DESC"):Disable()

    ENDIF

    If (Select("QRY1") <> 0)
        dbSelectArea("QRY1")
        dbCloseArea()
    Endif

    CONOUT("cSql1"+cEol+cSql1)

    TCQuery cSql1 NEW  ALIAS "QRY1"

    While QRY1->(!Eof())

        oSect1:init()
        oSect1:Cell("D1_FILIAL"):SetValue(QRY1->D1_FILIAL	 )
        oSect1:Cell("M0_NOME"):SetValue( FWFilName  (cEmpAnt,QRY1->D1_FILIAL)    )
        oSect1:Cell("D1_TOTAL"):Hide()
        oSect1:Printline()

        If (Select("QRY2") <> 0)
            dbSelectArea("QRY2")
            dbCloseArea()
        Endif

        cQuery2:= cSql2 +"AND D1_FILIAL =" +VALTOSQL(QRY1->D1_FILIAL	) +" ORDER BY 1"

        CONOUT("cQuery2"+cEol+cQuery2)

        TCQuery cQuery2 NEW ALIAS "QRY2"

        While QRY2->(!Eof())

            oSect2:init()
            oSect2:Cell("D1_CC"):SetValue(QRY2->D1_CC	 )
            oSect2:Cell("CTT_DESC01"):SetValue(QRY2->CTT_DESC01	 )
            oSect2:Printline()

            If (Select("QRY3") <> 0)
                dbSelectArea("QRY3")
                dbCloseArea()
            Endif

            cQuery3 := cSql3+cEol
            cQuery3 +="AND D1_FILIAL =" +VALTOSQL(QRY1->D1_FILIAL	) + cEol
            cQuery3 +="AND D1_CC =" +VALTOSQL(QRY2->D1_CC	)+" ORDER BY 2"

            CONOUT("cQuery3"+cEol+cQuery3)

            TCQuery cQuery3 NEW ALIAS "QRY3"

            While QRY3->(!Eof())

                oSect3:init()
                oSect3:Cell("D1_EMISSAO"):SetValue( stod(QRY3->D1_EMISSAO	 ))
                oSect3:Cell("D1_FORNECE"):SetValue( QRY3->D1_FORNECE	 )
                oSect3:Cell("D1_LOJA"):SetValue( QRY3->D1_LOJA	 )
                oSect3:Cell("A2_NOME"):SetValue( QRY3->A2_NOME	 )
                oSect3:Cell("D1_DOC"):SetValue( QRY3->D1_DOC	 )
                oSect3:Cell("D1_SERIE"):SetValue( QRY3->D1_SERIE	 )

                IF  MV_PAR13 == 1
                    oSect3:Cell("D1_COD"):SetValue( QRY3->D1_COD	 )
                    oSect3:Cell("B1_DESC"):SetValue( QRY3->B1_DESC	 )
                ENDIF

                oSect3:Cell("D1_PEDIDO"):SetValue( QRY3->D1_PEDIDO	 )
                oSect3:Cell("D1_TOTAL"):SetValue( QRY3->D1_TOTAL	 )
                oSect3:Printline()

                QRY3->(dbSkip())

            EndDo
            oSect3:Finish()

            QRY2->(dbSkip())
            oReport:SkipLine(2)

        EndDo

        oSect2:Finish()
        QRY1->(dbSkip())

    EndDo
    oSect1:Finish()


Return Nil
