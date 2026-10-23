
user function SPDFIS09()
    Local cEntSai := ParamixB[1]
    Local aDados :=  ParamixB[2]
    Local aParc := {}
    Local cPrefixo	:=""
    Local cNum		:=""
    Local cFor		:=""
    Local cLoj		:=""
    Local cFilSE1   :=""

    conout(cEntSai+" - "+alltrim(aDados[1])+"|"+alltrim(aDados[2])+"|"+alltrim(aDados[3])+"|"+alltrim(aDados[4])+"|"+alltrim(aDados[5]))

    cPrefixo	:= 	aDados[2]
    cNum		:=	aDados[1]
    cFor		:=	aDados[3]
    cLoj		:=	aDados[4]
    cFilSE1 := xfilial("SE1")
    If("1"$cEntSai)


        cAliasSE2	:=	GetNextAlias()

        BeginSql Alias cAliasSE2

			COLUMN E2_VENCTO AS DATE
			COLUMN E2_VENCREA AS DATE

			SELECT
				SE2.E2_FILIAL,SE2.E2_PREFIXO,SE2.E2_NUM,SE2.E2_PARCELA,SE2.E2_TIPO,SE2.E2_FORNECE,SE2.E2_LOJA,
				SE2.E2_HIST,SE2.E2_VENCREA,SE2.E2_VALOR,SE2.E2_VLCRUZ,SE2.E2_VENCTO
			FROM
				%Table:SE2% SE2
			WHERE
				SE2.E2_FILIAL=%xFilial:SE2% AND
				SE2.E2_FORNECE=%Exp:cFor% AND
				SE2.E2_LOJA=%Exp:cLoj% AND
				SE2.E2_PREFIXO=%Exp:cPrefixo% AND
				SE2.E2_NUM=%Exp:cNum% AND
				SE2.%NotDel%
			ORDER BY
				1,2,3,4,5,6,7
        EndSql

        Do While (!(cAliasSE2)->(Eof ()) .And.;
                xFilial("SE2")==(cAliasSE2)->E2_FILIAL .And.;
                cFor==(cAliasSE2)->E2_FORNECE .And.;
                cLoj==(cAliasSE2)->E2_LOJA .And.;
                cPrefixo==(cAliasSE2)->E2_PREFIXO .And.;
                cNum==(cAliasSE2)->E2_NUM )

            //ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
            //³Montando as parcelas³
            //ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

            aAdd(aParc, {(cAliasSE2)->E2_TIPO, (cAliasSE2)->E2_HIST, (cAliasSE2)->E2_NUM, (cAliasSE2)->E2_PARCELA, (cAliasSE2)->E2_VENCREA, (cAliasSE2)->E2_VLCRUZ, (cAliasSE2)->E2_VENCTO})


            (cAliasSE2)->(DbSkip())
        EndDo
        (cAliasSE2)->(DbCloseArea())

    else
        cAliasSE1	:=	GetNextAlias()

        BeginSql Alias cAliasSE1

			COLUMN E1_VENCTO AS DATE
			COLUMN E1_VENCREA AS DATE

			SELECT
				SE1.E1_FILIAL,SE1.E1_PREFIXO,SE1.E1_NUM,SE1.E1_PARCELA,SE1.E1_TIPO,SE1.E1_CLIENTE,SE1.E1_LOJA,
				SE1.E1_HIST,SE1.E1_VENCREA,SE1.E1_VALOR,SE1.E1_VLCRUZ,SE1.E1_VENCTO
			FROM
				%Table:SE1% SE1
			WHERE
				SE1.E1_FILIAL=%xFilial:SE1% AND
				SE1.E1_CLIENTE=%Exp:CFOR% AND
				SE1.E1_LOJA=%Exp:cLoj% AND
				SE1.E1_PREFIXO=%Exp:cPrefixo% AND
				SE1.E1_NUM=%Exp:cNum% AND
				SE1.%NotDel%
			ORDER BY 1,6,7,2,3
        EndSql
        Do While (!(cAliasSE1)->(Eof ()) .And.;
                cFilSE1==(cAliasSE1)->E1_FILIAL .And.;
                CFOR==(cAliasSE1)->E1_CLIENTE .And.;
                cLoj==(cAliasSE1)->E1_LOJA .And.;
                cPrefixo==(cAliasSE1)->E1_PREFIXO .And.;
                cNum==(cAliasSE1)->E1_NUM )

            aAdd(aParc, {(cAliasSE1)->E1_TIPO, (cAliasSE1)->E1_HIST, (cAliasSE1)->E1_NUM, (cAliasSE1)->E1_PARCELA, (cAliasSE1)->E1_VENCREA, (cAliasSE1)->E1_VLCRUZ, (cAliasSE1)->E1_VENCTO})

            (cAliasSE1)->(DbSkip ())
        EndDo

        DbSelectArea(cAliasSE1)
        (cAliasSE1)->(DbCloseArea())

    endif

Return aParc
