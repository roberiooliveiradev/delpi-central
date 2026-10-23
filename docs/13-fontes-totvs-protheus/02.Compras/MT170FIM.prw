

/*nao compilar*/
/****************************************
* PONTO DE ENTRADA PARA DELPI           *
* ENTENDER LOCAL 99 COMO EXTENSÃO DO 01 *
* NAO COMPILAR 2020/10 - ALINHAR COM A  *
* JOICI ANTES                           *
*****************************************/

User Function MT170FIM()
	Local aScs := PARAMIXB[1]
	Local nX   := 0
	For nX := 1 To Len(aScs)
		DbSelectArea("SC1")
		If DbSeek(xFilial("SC1") + aScs[nX, 2]) .AND. SC1->C1_LOCAL == "99"
			RecLock("SC1", .F.)
			DbDelete()
			MsUnlock()
		Endif
	Next
Return Nil

User Function MT170SLD()
	Local nQuant  := PARAMIXB[1]
	Local cProd   := PARAMIXB[2]
	Local cLocal  := PARAMIXB[3]

	Local xEmin    := 0.00
	Local xEstSeg  := 0.00
	Local xLE  	 := 0.00
	Local aArea := getarea()
	If cLocal == "01"
		DbSelectArea("SB2")
		DbSetOrder(1)
		If DbSeek(xFilial("SB2") + cProd + "99")
			nQuant += SB2->B2_QATU - SB2->B2_QEMP
		EndIf
	ElseIf cLocal == "99"
		DbSelectArea("SB1")
		DbSetOrder(1)
		If DbSeek(xFilial("SB1") + cProd)
			nQuant := SB1->B1_ESTSEG  //+ 1
		EndIf
	EndIf


	IF IsInCallStack("MATA170") .OR. IsInCallStack("MATR440")
		Dbselectarea("SBZ")
		SBZ->(DbSetOrder(1))
		IF	SBZ->(DbSeek(xFilial('SBZ')+cProd  ))

			xEmin    := SBZ->BZ_EMIN
			xEstSeg  := SBZ->BZ_ESTSEG
			xLE  	 := SBZ->BZ_LE
			/*
				1.1
				Quando Estoque de Seguranca Maior que 0
				Quando Estoque Minimo igual 0
				Quando Lote Economico Diferente de  0
				1.2
				a Necessidade original For Maior Que Estoque de Seguranca
				Necessidade Retorna Quantidade: Estoque de Seguranca
			*/
			if xEstSeg > 0 .and. xEmin == 0.00 .and. xLE # 0
				if nQuant > xEstSeg
					nQuant := xEstSeg
				endif
				/*
				2.1
				Quando Estoque de Seguranca igual 0
				Quando Estoque Minimo igual 0
				Quando Lote Economico Diferente de  0
				2.2
				Lote Economico For Maior Que a Necessidade original
				Necessidade Retorna 0
				*/
			elseif xEstSeg == 0 .and. xEmin == 0.00 .and. xLE # 0
				if xLE > nQuant
					nQuant := xEstSeg
				endif
			endif
		endif
	endif

	restarea(aArea)
Return (nQuant)

