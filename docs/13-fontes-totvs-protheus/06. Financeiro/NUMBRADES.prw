#include 'protheus.ch'
#include 'parmtype.ch'

User Function NUMBRADES()

	Local cNumSEE := ""
	Local cCartei := AllTrim(SEE->EE_CODCART)
	Local nTam    := Len(AllTrim(SEE->EE_FAXATU))

	If Empty(SE1->E1_NUMBCO)

		// Enquanto nao conseguir criar o semaforo, indica que outro usuario
		// esta tentando gerar o nosso numero.
		cNumSEE := StrZero(Val(AllTrim(SEE->EE_FAXATU)),nTam)

		While !MayIUseCode( SEE->(EE_FILIAL+EE_CODIGO+EE_AGENCIA+EE_CONTA+EE_SUBCTA))  //verifica se esta na memoria, sendo usado
			cNumSEE := Soma1(cNumero)										// busca o proximo numero disponivel
			Conout('Reservado código de Faixa para número de Título '+cNumSEE+' !!!')
		EndDo

		cNumero := cNumSEE + MODULO11(cCartei+STRZERO(VAL(cNumSEE),11),2,7)

		Conout('Calculado Nosso Número '+AllTrim(cNumero)+' para Cobranca Bancária Banco '+SEE->EE_CODIGO+' !!!')

		RecLock("SE1",.F.)
		Replace SE1->E1_NUMBCO With cNumero
		SE1->( MsUnlock( ) )

		RecLock("SEE",.F.)
		Replace SEE->EE_FAXATU With Soma1(cNumSEE, nTam)
		SEE->( MsUnlock() )

		Leave1Code(SEE->(EE_FILIAL+EE_CODIGO+EE_AGENCIA+EE_CONTA+EE_SUBCTA))
		Conout('Liberado código de Faixa para número de Título '+cNumSEE+' !!!')

	Else
		cNumero := SE1->E1_NUMBCO
	EndIf

	DbSelectArea("SE1")

Return(cNumero)


Static Function Modulo11(cStr,nMultIni,nMultFim)

	Local i, nModulo := 0, cChar, nMult

	nMultIni := Iif( nMultIni==Nil,2,nMultIni )
	nMultFim := Iif( nMultFim==Nil,7,nMultFim )
	nMult := nMultIni
	cStr := AllTrim(cStr)

	For i := Len(cStr) to 1 Step -1
		cChar := Substr(cStr,i,1)
		If isAlpha( cChar )
			Help(" ", 1, "ONLYNUM")
			Return .f.
		End
		nModulo += Val(cChar)*nMult
		nMult:= IIf(nMult==nMultfim,2,nMult+1)
	Next
	nRest := nModulo % 11
	cRet  := IIf(11-nRest==10,'P',IIf(nRest==0,'0',Str(11-nRest,1)))

Return(cRet)