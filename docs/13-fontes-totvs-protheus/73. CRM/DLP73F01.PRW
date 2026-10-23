#Include "Topconn.ch"
#include "rwmake.ch"
#include "tbiconn.ch"
#include "ap5mail.ch"
#include "totvs.ch"

/*/{Protheus.doc} DLP73F01
Rotina responsável por envio de e-mail na alteração de estagio no processo da oportunidade de venda

@type function
@version 1.0
@author Gabriel
@since 29/12/2020
/*/

USER FUNCTION DLP73F01(cTo)
	<<<<<<< HEAD

	Local aArea := GetArea()
	Local cDir	:=	GetMV("MV_WFDIR")

	DEFAULT cTo := ''

	If Empty(cTo) .and. !EMPTY(AC2->AC2_ZEMAIL)
		cTo := ALLTRIM(AC2->AC2_ZEMAIL)
	EndIf
	=======
	>>>>>>> e0f01c3e91cc803c4754f4349666fbd01fd2595f

	Local aArea := GetArea()

	DEFAULT cTo := ''

	If Empty(cTo) .and. !EMPTY(AC2->AC2_ZEMAIL)
		cTo := ALLTRIM(AC2->AC2_ZEMAIL)
	EndIf

	oProcess := TWFProcess():New("DLP73F01","WF CRM")
	oProcess:NewTask("DLP73F01",cDir+"\"+cArqWF)
	//oProcess:cSubject := "OV 000002 - WEG MOTORES - 415804892" //+ALLTRIM(AD1->AD1_NROPOR)+" "+ALLTRIM(AD1_DESCRI)
	oProcess:cSubject := "HOMOLOGACAO LMP - OV "+ALLTRIM(AD1->AD1_NROPOR)+" "+ALLTRIM(AD1_DESCRI)
	oProcess:cBCC   := alltrim(AC2->AC2_ZEMAIL)
	//oProcess:cBCC   := "gabriel.araujo@totvs.com.br"

	oProcess:oHtml:ValByName("cDescEsta",alltrim(AC2->AC2_STAGE)+" - "+alltrim(AC2->AC2_DESCRI))
	// Anotações
	dbSelectArea("AOB")
	dbSetOrder(2)
	dbGoTop()
	If dbSeek(fWxFilial("AOB")+"AD1"+fWxFilial("AD1")+AD1->AD1_NROPOR)
		While !AOB->(EOF()) .And. AOB->AOB_FILIAL == fWxFilial("AOB") .and. AllTrim(AOB->AOB_ENTIDA+AOB->AOB_CHAVE) == AllTrim("AD1"+fWxFilial("AD1")+AD1->AD1_NROPOR)
			aAdd((oProcess:oHtml:ValByName("TB.cProp")),FwGetUserName(AOB->AOB_OWNER))
			aAdd((oProcess:oHtml:ValByName("TB.cDtAnot")),DToC(AOB->AOB_DTNOTA))
			aAdd((oProcess:oHtml:ValByName("TB.cTitAnot")),AOB->AOB_TITULO)
			aAdd((oProcess:oHtml:ValByName("TB.cMemAnot")),AOB->AOB_CONTEU)
			AOB->(dbSkip())
		End
	else

		aAdd((oProcess:oHtml:ValByName("TB.cProp")),"")
		aAdd((oProcess:oHtml:ValByName("TB.cDtAnot")),"")
		aAdd((oProcess:oHtml:ValByName("TB.cTitAnot")),"")
		aAdd((oProcess:oHtml:ValByName("TB.cMemAnot")),"")


	EndIf


EndIf

oProcess:cTo   := cTo

oProcess:Start()
oProcess:Finish()

RestArea(aArea)

return


