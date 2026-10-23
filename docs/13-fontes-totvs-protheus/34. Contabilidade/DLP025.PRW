#INCLUDE "TOPCONN.CH"
#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 02/05/01

User Function DLP025()        // incluido pelo assistente de conversao do AP5 IDE em 02/05/01

/*
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦PROGRAMA  ¦ DLP025   ¦ Autor ¦ Diego Folchini        ¦ Data ¦ 23/04/07 ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Descriçào ¦ Rorina Para limpar lançamentos contabeis                   ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
*/


//Ú==============================================================¿
//³ AJUSTE NO SX1                                                ³
//À==============================================================Ù
cPerg := "DLP025"
aRegistros := {}

AADD(aRegistros,{cPerg,"01","Data Inicial      ?","","","mv_ch01","D",08,0,0,"G","","mv_par01",""           ,"","","","",""         ,"","","","",""       ,"","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"02","Data Final        ?","","","mv_ch02","D",08,0,0,"G","","mv_par02",""           ,"","","","",""         ,"","","","",""       ,"","","","","","","","","","","","","","","","","","",""})
AADD(aRegistros,{cPerg,"03","Modulos           ?","","","mv_ch03","N",01,0,0,"C","","mv_par03","Faturamento","","","","","Finaceiro","","","","","Compras","","","","","","","","","","","","","","","","","","",""})

dbSelectArea("SX1")
dbSeek(cPerg)
If !Found()
	dbSeek(cPerg)
	While SX1->X1_GRUPO==cPerg.and.!Eof()
		Reclock("SX1",.f.)
		dbDelete()
		MsUnlock("SX1")
		dbSkip()
	End
	For i:=1 to Len(aRegistros)
		RecLock("SX1",.T.)
		For j:=1 to FCount()
			FieldPut(j,aRegistros[i,j])
		Next
		MsUnlock("SX1")
	Next
Endif
If Pergunte(cPerg,.T.)
	u_GerNic26(Mv_par01,Mv_par02,Mv_par03)
EndIf
Return

***********************************
User Function GerNic26(DTINI,DTFIM,MODULOS)
*************

If MODULOS==1
	cQuery := "UPDATE " + RetSqlName("CT2") +" SET D_E_L_E_T_='*' "
	cQuery += "WHERE CT2_DATA>='"+dtos(DTINI)+"' AND CT2_DATA<='"+dtos(DTFIM)+"'  AND CT2_ROTINA='CTBANFS'"
	TCSQLExec(cQuery)
	
	cQuery := "UPDATE " + RetSqlName("SF2") +" SET F2_DTLANC='' "
	cQuery += "WHERE F2_EMISSAO>='"+dtos(DTINI)+"' AND F2_EMISSAO<='"+dtos(DTFIM)+"'  "
	TCSQLExec(cQuery)                                       
    MSGBOX("Lançamentos Contabeis de Faturamento excluidos")
Else
	If MODULOS==2
		//Deleta o Lançamento Contabil e Contas a Receber e a Pagar, o Movimentos e Cheques
		cQuery := "UPDATE " + RetSqlName("CT2") +" SET D_E_L_E_T_='*' "
		cQuery += "WHERE CT2_DATA>='"+dtos(DTINI)+"' AND CT2_DATA<='"+dtos(DTFIM)+"'  AND Left(CT2_ROTINA,4)='FINA'"
		TCSQLExec(cQuery)	
		
		cQuery := "UPDATE " + RetSqlName("SE1") +" SET E1_LA='' "
		cQuery += "WHERE E1_EMISSAO>='"+dtos(DTINI)+"' AND E1_EMISSAO<='"+dtos(DTFIM)+"'  "
		TCSQLExec(cQuery)		
		
		cQuery := "UPDATE " + RetSqlName("SE2") +" SET E2_LA='' "
		cQuery += "WHERE E2_EMISSAO>='"+dtos(DTINI)+"' AND E2_EMISSAO<='"+dtos(DTFIM)+"'  "
		TCSQLExec(cQuery)		
		
		cQuery := "UPDATE " + RetSqlName("SE5") +" SET E5_LA='' "
		cQuery += "WHERE E5_DATA>='"+dtos(DTINI)+"' AND E5_DATA<='"+dtos(DTFIM)+"'  "
		TCSQLExec(cQuery)		
		
		cQuery := "UPDATE " + RetSqlName("SEF") +" SET EF_LA='' "
		cQuery += "WHERE EF_DATA>='"+dtos(DTINI)+"' AND EF_DATA<='"+dtos(DTFIM)+"'  "
		TCSQLExec(cQuery)		
        MSGBOX("Lançamentos Contabeis de Financeiro excluidos")	
	Else
		cQuery := "UPDATE " + RetSqlName("CT2") +" SET D_E_L_E_T_='*' "
		cQuery += "WHERE CT2_DATA>='"+dtos(DTINI)+"' AND CT2_DATA<='"+dtos(DTFIM)+"'  AND CT2_ROTINA='CONA230'"
		TCSQLExec(cQuery)

		cQuery := "UPDATE " + RetSqlName("SF1") +" SET F1_DTLANC='' "
		cQuery += "WHERE F1_DTDIGIT>='"+dtos(DTINI)+"' AND F1_DTDIGIT<='"+dtos(DTFIM)+"'  "
		TCSQLExec(cQuery)			
        MSGBOX("Lançamentos Contabeis de Compras excluidos")
	EndIf
EndIf	
Return(.T.)


