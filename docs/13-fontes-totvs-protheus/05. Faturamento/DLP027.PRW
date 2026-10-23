#include "rwmake.ch"        // incluido pelo assistente de conversao do AP5 IDE em 02/05/01
#INCLUDE "TOPCONN.CH"

User Function DLP027()        // incluido pelo assistente de conversao do AP5 IDE em 02/05/01

/*
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦PROGRAMA  ¦ DLP027   ¦ Autor ¦ MARCIO DA SILVA       ¦ Data ¦ 22/06/07 ¦¦¦
¦¦+----------+------------------------------------------------------------¦¦¦
¦¦¦Descriçào ¦ EXPORTACAO DE NOTAS FISCAIS PARA WEG                       ¦¦¦
¦¦¦          ¦                                                            ¦¦¦
¦¦+-----------------------------------------------------------------------+¦¦
¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦¦
¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯¯
*/                                
Local oPerg, cPerg := "DLP027"
oPerg := TPergunta():New(cPerg)
oPerg:AddGet  ("De  Fornecedor  ?",   "C", 06, 0, Nil, "SA2", "", "")
oPerg:AddGet  ("Ate Fornecedor  ?",   "C", 06, 0, Nil, "SA2", "", "")
oPerg:AddCombo("Ordem ?", { "Produto", "Descricao Produto" }, 1)
oPerg:Update()
If oPerg:Execute(.T.)
	Processa({ || fDLP027() }, "Ordenando Tabela... Aguarde...")
EndIf
Return

****************************
Static Function fDLP027()
*************

cQuery := "SELECT AIB.r_e_c_n_o_ Reg,*  FROM "
cQuery += RetSqlName("AIB") + " AIB, " + RetSqlName("SB1") + " SB1 "
cQuery += " WHERE B1_COD =AIB_CODPRO  "            
cQuery += " AND AIB_CODFOR >= '"+Alltrim(MV_PAR01)+"'  AND AIB_CODFOR <= '"+Alltrim(MV_PAR02)+"' "            
cQuery += " AND SB1.D_E_L_E_T_ = '' "            
If Mv_Par03 == 1
	cQuery += " ORDER BY AIB_FILIAL+AIB_CODFOR+AIB_LOJFOR+AIB_CODTAB+AIB_CODPRO "
Else
	cQuery += " ORDER BY AIB_FILIAL+AIB_CODFOR+AIB_LOJFOR+AIB_CODTAB+B1_DESC "
EndIf	

If (Select("TRBAIB") <> 0)
	DbSelectArea("TRBAIB")
	DbCloseArea()
EndIf
TCQUERY cQuery NEW ALIAS "TRBAIB"


DbSelectArea("TRBAIB")
DbGoTop()
While !Eof()
	sReg := TRBAIB->AIB_FILIAL + TRBAIB->AIB_CODFOR + TRBAIB->AIB_LOJFOR +  iif(Mv_Par03 == 1,TRBAIB->AIB_CODTAB,TRBAIB->B1_DESC)
	nOrder := 0
	While !Eof() .And. sReg == TRBAIB->AIB_FILIAL + TRBAIB->AIB_CODFOR + TRBAIB->AIB_LOJFOR +  iif(Mv_Par03 == 1,TRBAIB->AIB_CODTAB,TRBAIB->B1_DESC)
		nOrder += 1
		DbSelectArea("AIB")
		Goto(TRBAIB->Reg)
		RecLock("AIB",.F.)
		AIB->AIB_ITEM := STRZERO(nOrder,4)
		MsUnlock("AIB")
		DbSelectArea("TRBAIB")
		DbSkip()
	EndDo
EndDo
MSgbox("Arquivo Gerado Com Sucesso!")
Return


