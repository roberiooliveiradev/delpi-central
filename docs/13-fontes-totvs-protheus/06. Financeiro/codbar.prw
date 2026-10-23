/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³CODBAR   ºAutor  ³TOTVS               º Data ³  31/03/06   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ PROGRAMA PARA TRATAMENTO DO CAMPO E2_CODBAR PARA UTILIZACAOº±±
±±º          ³ DO PAGFOR                                                  º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³                                                            º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±± Alteracao:                                                             ±±±
±±                                                                        ±±±
±±                                                                        ±±±
±±                                                                        ±±±
±±                                                                        ±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

///--------------------------------------------------------------------------\
//| Função: CODBAR				Autor: Flávio Novaes		Data: 19/10/2003 |
//|--------------------------------------------------------------------------|
//| Essa Função foi desenvolvida com base no Manual do Bco. Itaú e no RDMAKE:|
//| CODBARVL - Autor: Vicente Sementilli - Data: 26/02/1997.                 |
//|--------------------------------------------------------------------------|
//| Descrição: Função para Validação de Código de Barras (CB) e Representação|
//|            Numérica do Código de Barras - Linha Digitável (LD).	         |
//|                                                                          |
//|            A LD de Bloquetos possui três Digitos Verificadores (DV) que  |
//|				são consistidos pelo Módulo 10, além do Dígito Verificador   |
//|				Geral (DVG) que é consistido pelo Módulo 11. Essa LD têm 47  |
//|            Dígitos.                                                      |
//|                                                                          |
//|            A LD de Títulos de Concessinárias do Serviço Público e IPTU   |
//|				possui quatro Digitos Verificadores (DV) que são consistidos |
//|            pelo Módulo 10, além do Digito Verificador Geral (DVG) que    |
//|            também é consistido pelo Módulo 10. Essa LD têm 48 Dígitos.   |
//|                                                                          |
//|            O CB de Bloquetos e de Títulos de Concessionárias do Serviço  |
//|            Público e IPTU possui apenas o Dígito Verificador Geral (DVG) |
//|            sendo que a única diferença é que o CB de Bloquetos é         |
//|            consistido pelo Módulo 11 enquanto que o CB de Títulos de     |
//|            Concessionárias é consistido pelo Módulo 10. Todos os CB´s    |
//|            têm 44 Dígitos.                                               |
//|                                                                          |
//|            Para utilização dessa Função, deve-se criar o campo E2_CODBAR,|
//|            Tipo Caracter, Tamanho 48 e colocar na Validação do Usuário:  |
//|            EXECBLOCK("CODBAR",.T.).                                      |
//|                                                                          |
//|            Utilize também o gatilho com a Função CONVLD() para converter |
//|            a LD em CB.													 |
//\--------------------------------------------------------------------------/
USER FUNCTION CODBAR()

	local lret
	local cCpo := ReadVar()
	local cCont:= &(cCpo)
	local cCodBar := ''
	Local nTam := getsx3cache("E2_CODVIRT","X3_TAMANHO")
	Local nTamCB := getsx3cache("E2_CODBAR","X3_TAMANHO")
	Local nTamLN := getsx3cache("E2_LINDIG","X3_TAMANHO")
	For x:=1 To Len(cCont)
		If	IsDigit(Substr(cCont,x,1)) //$ '0/1/2/3/4/5/6/7/8/9'
			cCodBar += Substr(cCont,x,1)
		EndIf
	Next

	lRet := VldCodBar(cCodBar)
	//	if lRet
	//		VCodBarDLP(cCodBar)
	//	endif
	If	('M->E2_CODVIRT' == cCpo) .And. lRet
		M->E2_CODVIRT := PADR(cCodBar,nTam)
		M->E2_LINDIG  := PADR(cCodBar,nTamLN)
		cCodBar2 	  := FinLDCB(M->E2_LINDIG)
		M->E2_CODBAR  := PADR(cCodBar2,nTamCB)
	EndIf

RETURN(lRet)



Static Function DV_BarCode( cBarCode )
	Local cDig
	Local nPos
	Local nAux := 0

	For nPos := 1 To 43
		nAux += Val(SubStr(cBarCode,nPos,1)) * If( nPos<= 3, ( 5-nPos),     ;
			If( nPos<=11, (13-nPos),     ;
			If( nPos<=19, (21-nPos),     ;
			If( nPos<=27, (29-nPos),     ;
			If( nPos<=35, (37-nPos),     ;
			(45-nPos) )))))
	Next
	nAux := nAux % 11
	cDig := If( (11-nAux)>9, 1, (11-nAux) )

Return Str(cDig,1)


Static Function VldMod( cNum , cCodBar)
	Local cCodSub3 := SubStr(cCodBar,3,1)
	Local cRet := ""
	If cCodSub3 == '6' .or. cCodSub3 == '7'
		cRet :=Mod10(cNum)
	ElseIf cCodSub3 == '8' .or. cCodSub3 == '9'
		cRet :=Mod11(cNum)
	EndIf
Return cRet


Static Function Mod10( cNum )
	Local nFor    := 0
	Local nTot    := 0
	Local cNumAux

	// Verifico o numero de digitos e impar
	// Caso seja, adiciono um caracter
	If Len(cNum)%2 #0
		cNum := "0"+cNum
	EndIf

	For nFor := 1 To Len(cNum)
		If nFor%2 == 0
			cNumAux := StrZero(2 * Val(SubStr(cNum,nFor,1)), 2)
		Else
			cNumAux := StrZero(Val(SubStr(cNum,nFor,1))    , 2)
		Endif
		nTot += ( Val(LEFT(cNumAux,1)) + Val(Right(cNumAux,1)) )
	Next

	nTot := nTot % 10
	nTot := If( nTot#0, 10-nTot, nTot )

Return Str(nTot,1)




static Function VCodBarDLP(cCodBar)
	Local lRet := .T.
	Local nX
	Local	cCampo

	cCodBar := Alltrim(cCodBar)
	// Completa o tamanho do codigo de barras se ele for menor que 44 por se tratar de uma
	// linha digitavel.
	If Len(cCodBar) < 44
		cCodBar := Left(cCodBar+Replicate("0", 48-Len(cCodBar)),47)
	Endif

	If  Len(cCodBar) > 47 .and. AllTrim(SubStr(cCodBar,48)) == ""
		cCodBar := SubStr(cCodBar,1,47)
	EndIf

	Do Case
		Case Len(cCodBar)==44 // Validacao do codigo de Barras
			// Se nao conseguir validar o DV do codigo de barras, tenta validar como
			// se fosse titulo de concessionaria.
			If Dv_BarCode(Left(cCodBar,4)+SubStr(cCodBar,6))!=SubStr(cCodBar,5,1)
				// Codigo de barras de concessionarias
				cCampo:=Left(cCodBar,3)+SubStr(cCodBar,5)
				If VldMod(cCampo,cCodBar)!=SubStr(cCodBar,4,1)
					Help(" ",1,"INVCDBAR",,OemToAnsi('Codigo de Barras Inválido.'),1,0) //'Codigo de Barras Inválido.'
					lRet := .F. // Invalido
				Endif
			Endif
		Case Len(cCodBar)==47 // Validacao da linha digitavel
			// Elimina os digitos
			cCodSemDv	:= Left(cCodBar,9)+SubStr(cCodBar,11,10)+SubStr(cCodBar,22,10)
			cCodBar2		:= Left(cCodBar,4)+Substr(cCodBar,34)+Substr(cCodSemDv,5)
			// Calcula os digitos e os compara com os digitos informados
			For nX := 1 To 3
				cCampo := SubStr(cCodSemDv,If(nX==1,1,If(nX==2,10,20)),If(nX==1,9,10))
				If Mod10(cCampo) != SubStr(cCodBar,If(nX==1,10,If(nX==2,21,32)),1)
					Help(" ",1,"INVCDBAR",,OemToAnsi('Linha Digitável Inválida.'),1,0) //'Linha Digitável Inválida.'
					lRet := .F.
					Exit
				Endif
			Next
			//Valido o digito verificador geral da linha digitada (pos. 33 da linha digitada)
			If lRet
				If Dv_BarCode(cCodBar2)!=SubStr(cCodBar,33,1)
					Help(" ",1,"INVCDBAR",,OemToAnsi('Linha Digitável Inválida.'),1,0) //'Linha Digitável Inválida.'
					lRet := .F.
				Endif
			Endif
		OtherWise // Validacao da linha digitavel de concessionarias
			// Elimina os digitos
			cCodSemDv := Left(cCodBar,11)+SubStr(cCodBar,13,11)+SubStr(cCodBar,25,11)+SubStr(cCodBar,37,11)
			// Calcula os digitos e os compara com os digitos informados
			For nX := 1 To Len(cCodSemDv) Step 11
				cCampo := SubStr(cCodSemDv,nX,11)
				nPos :=  If(nX==1,12,If(nX==12,24,If(nX==23,36,48)))
				If VldMod(cCampo,cCodBar) != SubStr(cCodBar,nPos,1)
					Help(" ",1,"INVCDBAR",,OemToAnsi('Codigo de Barras Inválido.'),1,0) //'Codigo de Barras Inválido.'
					lRet := .F.
					Exit
				Endif
			Next
	EndCase
Return (lRet)
