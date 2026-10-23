#INCLUDE "TOPCONN.CH"
#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE "FWEVENTVIEWCONSTS.CH"
#include 'totvs.ch'
//pagar
USER FUNCTION DLP06F2A()
	Local cLockName As Character
	Local cToken := ""
	Local aSeaArea := SEA->(GetArea())
	Local cNumeBor := ""
	Private cDtVld := ALLTRIM(DtoC(Date())+time())
	cLockName := cEmpAnt + ' - FINA717'
	cEventID := "Z02"

	cNumeBor := SEA->EA_NUMBOR
	cToken := fGetTkn()

	IF !EMPTY(cToken)

		SEA->(DbSetOrder(1))
		If SEA->(DbSeek(xFilial("SEA")+SEA->EA_NUMBOR))
			while SEA->(!EOF())
				If RecLock('SEA',.F.)

					SEA->EA_YTOKEN := /*ENCODE64(*/cToken/*)*/
					SEA->(MsUnlock())

				EndIf
				SEA->(DBSKIP())
			ENDDO
		EndIf

		Teste_EV(cToken,cNumeBor)

	ENDIF

	SEA->(RESTAREA(aSeaArea))

RETURN

//receber
USER Function DLP06F2B()
	Local cLockName  As Character
	Local cCodSch	 As Character

	cLockName  := cEmpAnt + ' - FINA713'
	cCodSch    := "FINA713('" + cEmpAnt + "')"

	If F713VldUso()
		If &("gfin.util.schedule.validBranchesSchedule(cCodSch)")
			If LockByName(cLockName, .T./*lEmpresa*/, .F./*lFilial*/ ) // uma execução por vez
				F713Transf() // Transmite os boletos
				If F713VldAlCa()
					F713Alt()       // Transmite alteração de boletos
					F713Canc()      // Transmite cancelamento de boletos
				EndIf
				F713Mail()
				UnLockByName(cLockName, .T./*lEmpresa*/, .F./*lFilial*/ )
			EndIf
		Else
			FwLogMsg('ERROR',, "FINA713", "FINA713", "", 'Schedule', "Scheduling with more than one branch registered, or unspecified branch. Adjust the schedule to run only one branch." )
		EndIf
	EndIf
Return

/*/{Protheus.doc} SchedDef
    Execucao da rotina via Schedule.
    @return  aParam
/*/
Static Function SchedDef()
	Local aParam := {}

	aParam := {"P",; //Tipo R para relatorio P para processo
		"",;     //Nome do grupo de perguntas (SX1)
		Nil,;    //cAlias (para Relatorio)
		Nil,;    //aArray (para Relatorio)
		Nil}     //Titulo (para Relatorio)
Return aParam


STATIC Function Teste_EV(cRealTkn,cNumeBor)

	Local cEventID  := "Z02"
	Local cMsg := "Token para liberação de Borderô: " + cRealTkn
	Local cEol := chr(10)

	cSql := "	SELECT DISTINCT XI_USERID " + cEol
	cSql +="	FROM dbo.SXI (NOLOCK) TBL1 " + cEol
	cSql +="	WHERE TBL1.D_E_L_E_T_ = '' " + cEol
	cSql +="	AND TBL1.XI_EVENTID ='Z02' " + cEol

	If Select("TSXI") > 1
		TSXI->(DbCloseArea())
	EndIf

	TcQuery cSQL New Alias "TSXI"
	cBkpUsr	:= __cUserId
	While !TSXI->(Eof())
		__cUserId	:=TSXI->XI_USERID
		EventInsert(FW_EV_CHANEL_ENVIRONMENT, FW_EV_CATEGORY_MODULES, cEventID,FW_EV_LEVEL_INFO,"",'Liberação borderô: '+cNumeBor,cMsg,.F.)

		TSXI->(DbSkip())
	EndDo
	TSXI->(DbCloseArea())
	//__cUserId	:= cUser075
	//EventInsert(FW_EV_CHANEL_ENVIRONMENT, FW_EV_CATEGORY_MODULES, cEventID,FW_EV_LEVEL_INFO,""/*cCargo*/,STR0002,cMsg075,.F./*lPublic*/)
	//__cUserId	:= cBkpUsr075
	// PutGlbVars(cDtVld+E2_FILIAL+E2_PREFIXO+E2_NUM+E2_PARCELA+E2_TIPO+E2_FORNECE+E2_LOJA,cRealTkn)

	__cUserId := cBkpUsr
Return

/*/{Protheus.doc} nomeStaticFunction
	(long_description)
	@type  Static Function
	@author Pedro Lindenberg
	@since 02/07/2024
	@version version
/*/
Static Function fGetTkn()
	Local x := 0
	Local cToken := ""
	Local lVldTkn := .T.

	for x := 1 to 6

		cToken += cValToChar(Randomize(0,9))

	next x

	lVldTkn := fVldTokn(cToken)

	while !lVldTkn

		for x := 1 to 6

			cToken += cValToChar(Randomize(0,9))

		next x

		cToken := cToken
		lVldTkn := fVldTokn(cToken)

	end

Return cToken

/*/{Protheus.doc} nomeStaticFunction
  (long_description)
  @type  Static Function
  @author Pedro Lindenberg
  @since 02/07/2024
/*/
Static Function fVldTokn(cToken)
	Local lRet := .T.
	Local cAlias := GetNextAlias()

	If Select(cAlias) <> 0
		(cAlias)->(DbCloseArea())
	EndIf

	BeginSql alias cAlias
		%noparser%

		Select
			SEA.EA_NUMBOR
		from
			%Table:SEA% SEA
		Where
			SEA.EA_YTOKEN = %EXP:cToken%
			and SEA.%notDel%
	EndSql

	If (cAlias)->(!EOF())
		lRet := .F.
	EndIf

	(cAlias)->(DbCloseArea())

Return lRet
