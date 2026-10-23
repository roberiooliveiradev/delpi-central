#INCLUDE "PROTHEUS.CH"
#INCLUDE "APWIZARD.CH"
#INCLUDE "FWADAPTEREAI.CH"
#INCLUDE 'FWMVCDEF.CH'
#INCLUDE "TOPCONN.CH"

user function DL04A02(cCodPrd)

	Local cDesPrd := POSICIONE("SB5",1,xFilial("SB5")+cCodPrd,"B5_CEME")

	CONOUT("**************GDA**************")
	CONOUT("B1: "+SB1->B1_COD)

return cDesPrd
