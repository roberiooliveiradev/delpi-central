#include 'protheus.ch'
#include 'parmtype.ch'

user function F240FIL()
	/*	Local Enter := CHR(13)+CHR(10)
	Local _cFiltro := ""
	Local cMsg := "Deseja Filtrar os Titulos de Mesmo banco de pagamento ???"
	If MsgYesNo(cMsg)
		//_cFiltro := " .AND. ( E2_BCOPAG $  cPort240 )"
		//_cFiltro :=  " .AND. ( GetAdvFval('SA2','A2_BANCO',xFilial('SA2')+E2_FORNECE+E2_LOJA,1) $ cPort240  )"
		_cFiltro := "( E2_FORBCO $ '" + cPort240 + "' ) "
		//	else
		//		_cFiltro :=  " .AND. ( GetAdvFval('SA2','A2_BANCO',xFilial('SA2')+E2_FORNECE+E2_LOJA,1) <> cPort240  )"
	endif

	conout(_cFiltro )*/

	Private cBordFil:= ".F."
	Private cFiltro := dbFilter()
	Private cCtaFor := 'POSICIONE("SA2",1,xFILIAL("SA2")+(cAliasSE2)->(E2_FORNECE+E2_LOJA), "A2_NUMCON")'

	If CModPgto $ "01.03.41"

		//	cBordFil := "(Empty( E2_CODBAR )) .And. !Empty( " + cCtaFor + ") "
	elseif CModPgto $ "30.31"
		If cModPgto == "31" //.and. alltrim(cPort240) $ "756_237"
			cBordFil := "(!Empty( E2_CODBAR )) .And. ( Left(E2_CODBAR, 3) <> '"+ alltrim(cPort240) +"' )"

		ElseIf cModPgto == "30" //.and. alltrim(cPort240) $ "756_237"
			cBordFil := "(!Empty( E2_CODBAR )) .And.  ( Left(E2_CODBAR, 3) == '"+ alltrim(cPort240) +"' )"

			//ElseIf cModPgto == "31" .AND. !( alltrim(cPort240) $ "756_237" )
			//
			//	cBordFil := "(!Empty( E2_CODBAR ))"
		Endif
	else
		cBordFil := ".t."
	EndIf

return (cBordFil)
