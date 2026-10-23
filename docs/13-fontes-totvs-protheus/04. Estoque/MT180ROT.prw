#include 'protheus.ch'
#include 'parmtype.ch'
/*revisar depois
Gabriel 01/2022*/
user function MT180ROT()

	//aadd(aRotina,{'Ajusta Oportunidade','U_TRA43A82()' , 0 , 3,0,NIL})

	//aAdd(aRotina, { "Consulta" ,"A010Consul"		, 0 , 2, 0, .F.} )
	aAdd(aRotina, { "Consulta" ,"U_DlpConPrd()"		, 0 , 2, 0, .F.} )
	aAdd(aRotina, { "Consulta" ,"U_Dlp()"		, 0 , 2, 0, .F.} )

return aRotina

USER Function DlpConPrd()
	Local aArea:= GetArea()

	dbSelectArea("SB1")
	SB1->(dbSetOrder(1))
	(dbseek(xFilial("SB1")+SA5->A5_PRODUTO))
	A010Consul()

	RestArea(aArea)
Return Nil
