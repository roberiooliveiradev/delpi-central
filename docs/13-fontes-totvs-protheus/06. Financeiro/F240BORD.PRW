#INCLUDE "PROTHEUS.CH"
#INCLUDE "totvs.ch"
#INCLUDE "topconn.ch"


/*/{Protheus.doc} Funcao

    Descricao

    @author  Nome
    @example Exemplos
    @param   [Nome_do_Parametro],Tipo_do_Parametro,Descricao_do_Parametro
    @return  Especifica_o_retorno
    @table   Tabelas
    @since   03-04-2024
/*/


User Function F240BORD()


	Local cNumBor    := SEA->EA_NUMBOR
	/*01 - Quando o Tipo e Modelo determinado*/

	IF SEA->EA_MODELO == '03' .and. SEA->EA_TIPOPAG == '20'
		//       FWAlertError("entrou", "Delpi")
		fProc(cNumBor)

	ENDIF

rETURN NIL

/*/{Protheus.doc} Funcao
dsadasdasdas 111
    Descricao

    @author  Gabriel Araujo
    @example Exemplos
    @param   [Nome_do_Parametro],Tipo_do_Parametro,Descricao_do_Parametro
    @since   04-2024
/*/


Static Function fProc(cNumBor)
	Local n1 := 0
	nRegAte := 0
	cQryCMP := fGetQry(cNumBor)

	If Select('TMPQRY') <> 0
		TMPQRY->(dbCloseArea())
	Endif
	TCQuery cQryCMP Alias TMPQRY New
	// nRegs:=0
	Count To nRegAte
	TMPQRY->(DbGoTop())
	cNBorMx := ""
	DbSelectArea("SEA")
	DbSelectArea("SE2")
	cRgnAtu :=   TMPQRY->REGRA
	nCount := 1
	cNBorTmp := cNumBor
	WHILE  TMPQRY->(!eof())
		if   cRgnAtu !=   TMPQRY->REGRA
			//  cNBorTmp := cNumBor
			cRgnAtu :=   TMPQRY->REGRA
			nCount++
		endif

		conout("TMPQRY->REGRA "+TMPQRY->REGRA+" cNumBor "+cNumBor+" nCount "+cvaltochar( nCount))

		conout()
		aRetBor := fGetInfBor(TMPQRY->REGRA)
		// cNBorTmp := cNumBor
		cNBorTmp := cNumBor
		n1 := 0
		FOR n1:=1 to nCount
			cNBorTmp := Soma1(cNBorTmp)
			conout(" cNBorTmp "+cNBorTmp)
		next n1

		if cNBorTmp >cNBorMx
			conout("cNBorTmp "+ cNBorTmp+" cNBorMx "+  cNBorMx)
			cNBorMx:= cNBorTmp
		endif

		SEA->(dbGoTo(TMPQRY->RECSEA))
		SE2->(dbGoTo(TMPQRY->RECSE2))

		RecLock("SEA",.F.)
		SEA->EA_NUMBOR := cNBorTmp
		SEA->EA_MODELO 	:= aRetBor[1]
		SEA->EA_TIPOPAG := aRetBor[2]
		IF TMPQRY->REGRA == 'RGN07'
			SEA->EA_YBLQPIX := "N"
			SEA->EA_SUBCTA := "003"
			SEA->EA_YLOG := CUSERNAME + ALLTRIM(ComputerName()) + DtoC(Date()) + Time()

			U_DLP06F2A()
		ENDIF
		SEA->(MsUnlock())

		RecLock("SE2",.F.)
		SE2->E2_NUMBOR := cNBorTmp
		SE2->(MsUnlock())

		TMPQRY->(dbSkip())
	EndDo
	PUTMV("MV_NUMBORP", cNBorMx)

Return

Static Function fGetQry(cNumBor)

	Local cSql := ""
	Local cEol := chr(10)
	cSqlCs := "CASE WHEN  SubstrING(E2_CODBAR,1,3) = EA_PORTADO and E2_FORMPAG NOT IN ('13','16','17')  THEN 'RGN01' " + cEol
	cSqlCs += " WHEN  SubstrING(E2_CODBAR,1,3) <> EA_PORTADO AND E2_CODBAR!= '' and E2_FORMPAG NOT IN ('13','16','17')  THEN 'RGN02' " + cEol
	cSqlCs += " WHEN  E2_CODBAR!= '' and E2_FORMPAG  IN ('13')  THEN 'RGN03' " + cEol
	cSqlCs += " WHEN  E2_CODBAR= '' and E2_CODRET != '' AND E2_E_CNPJ != '' AND E2_FORMPAG = '16' THEN 'RGN04'  " + cEol
	cSqlCs += " WHEN( E2_CODBAR= ''  and E2_FORBCO != ''  ) and ( E2_FORMPAG = '01' or A2_FORMPAG = '01' or E2_FORBCO = EA_PORTADO) THEN 'RGN05'   " + cEol
	cSqlCs += " WHEN ( E2_CODBAR= '' and  E2_FORBCO != '' and (E2_FORMPAG = '43' or A2_FORMPAG = '43') ) THEN 'RGN06'  " + cEol
	cSqlCs += " WHEN E2_CODBAR= '' and  (E2_FORMPAG = '45' or A2_FORMPAG = '45')  THEN 'RGN07' " + cEol
	cSqlCs += " WHEN E2_CODBAR!= '' and  (E2_FORMPAG = '17' )  THEN 'RGN08' " + cEol
	cSqlCs += " ELSE '' END " + cEol
	cSql += "SELECT  " + cSqlCs+" REGRA,  RANK() OVER       (PARTITION BY EA_NUMBOR ORDER BY "+cSqlCs+" ) IDRANK, "
	cSql += " SE2.R_E_C_N_O_ RECSE2 , SEA.R_E_C_N_O_ RECSEA" + cEol
	cSql += ",SEA.EA_NUMBOR, SEA.EA_PREFIXO,	SEA.EA_NUM,		SEA.EA_PARCELA, " + cEol
	cSql += "SEA.EA_TIPO,	SEA.EA_FORNECE,	SEA.EA_LOJA," + cEol
	cSql += "SE2.E2_SALDO,	SA2.A2_BANCO " + cEol
	cSql += "FROM	dbo."+ RetSqlName("SEA") + " 	SEA (nolock) " + cEol
	cSql += "LEFT JOIN	dbo."+ RetSqlName("SE2") + " 	SE2 (nolock) " + cEol
	cSql += "ON		SE2.E2_FILIAL  = "+VALTOSQL( fwxFilial("SE2")	)+ " AND " + cEol
	cSql += "   SE2.E2_PREFIXO = SEA.EA_PREFIXO	AND " + cEol
	cSql += "   SE2.E2_NUM     = SEA.EA_NUM 	AND " + cEol
	cSql += "   SE2.E2_PARCELA = SEA.EA_PARCELA	AND " + cEol
	cSql += "   SE2.E2_TIPO    = SEA.EA_TIPO	AND " + cEol
	cSql += "   SE2.E2_FORNECE = SEA.EA_FORNECE	AND " + cEol
	cSql += "   SE2.E2_LOJA    = SEA.EA_LOJA	AND " + cEol
	cSql += "   SE2.D_E_L_E_T_ =''  " + cEol
	cSql += "LEFT JOIN	dbo."+ RetSqlName("SA2") + " 	SA2 (nolock) " + cEol
	cSql += "ON		SA2.A2_FILIAL = "+VALTOSQL( fwxFilial("SA2")	)+ " AND " + cEol
	cSql += "       SA2.A2_COD    = SE2.E2_FORNECE	AND " + cEol
	cSql += "       SA2.A2_LOJA   = SE2.E2_LOJA		AND " + cEol
	cSql += "       SA2.D_E_L_E_T_ =''  " + cEol
	cSql += "WHERE	 SEA.D_E_L_E_T_ =''  " + cEol
	cSql += "   AND SEA.EA_NUMBOR = "+VALTOSQL( cNumBor	)+cEol
	cSql += "   AND SEA.EA_FILIAL  =  "+VALTOSQL( fwxFilial("SEA")	)  + cEol
	cSql += "  ORDER BY 1"
	CONOUT( cSql )
Return cSql


Static Function fGetInfBor(cDscRgn)
	aRet := Array(2)
	aRet[1]:="" //MODELO
	aRet[2]:= ""//TIPO
	if cDscRgn=="RGN01"
		aRet[1]:="30" //MODELO
		aRet[2]:="20" //TIPO
	ELSEif cDscRgn=="RGN02"
		aRet[1]:="31" //MODELO
		aRet[2]:="20" //TIPO
	ELSEif cDscRgn=="RGN03"
		aRet[1]:="13" //MODELO
		aRet[2]:="20" //TIPO
	ELSEif cDscRgn=="RGN04"
		aRet[1]:="16" //MODELO
		aRet[2]:="22" //TIPO
	ELSEif cDscRgn=="RGN05"
		aRet[1]:="01" //MODELO
		aRet[2]:="20" //TIPO
	ELSEif cDscRgn=="RGN06"
		aRet[1]:= "43"//MODELO
		aRet[2]:="20" //TIPO
	ELSEif cDscRgn=="RGN07"
		aRet[1]:="45" //MODELO
		aRet[2]:="20" //TIPO
	ELSEif cDscRgn=="RGN08"
		aRet[1]:="17" //MODELO
		aRet[2]:="22" //TIPO
	ENDIF
return aRet
