#include "protheus.ch"

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
ฑฑษออออออออออัออออออออออหอออออออัออออออออออออออออออออหออออออัอออออออออออออปฑฑ
ฑฑบPrograma  ณMTAB2D1R  บAutor  ณMicrosiga           บ Data ณ  03/12/12   บฑฑ
ฑฑฬออออออออออุออออออออออสอออออออฯออออออออออออออออออออสออออออฯอออออออออออออนฑฑ
ฑฑบDesc.     ณ Complementa grava็ใo no arquivo de saldos                  บฑฑ
ฑฑบ          ณ (executado DEPOIS da grava็ใo do SB2).                     บฑฑ
ฑฑฬออออออออออุออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออนฑฑ
ฑฑบUso       ณ P10                                                        บฑฑ
ฑฑศออออออออออฯออออออออออออออออออออออออออออออออออออออออออออออออออออออออออออผฑฑ
ฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑฑ
฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿฿
*/

User Function MTAB2D1R()

// Chama rotina para acerto de custo nas moedas 2 a 5 
AcerCusMoeda(ParamIxb[1], ParamIxb[2], ParamIxb[3])

Return


Static Function AcerCusMoeda(cProduto, cLocal, nMultip)

Local cMVMOEDA := GetMv('MV_MOEDACM')
Local lMoeda2  := !(cMVMOEDA $ '2')
Local lMoeda3  := !(cMVMOEDA $ '3')
Local lMoeda4  := !(cMVMOEDA $ '4')
Local lMoeda5  := !(cMVMOEDA $ '5')

Default cProduto := Space(TamSx3('B1_COD')[1])
Default cLocal   := Space(TamSx3('B2_LOCAL')[1])
Default nMultip	 := 0

If	Empty(cProduto) .Or. Empty(cLocal) .Or. Empty(nMultip)
		Return
EndIf

If	Empty(cMvMOEDA) .Or. lMoeda2 .Or. lMoeda3 .Or. lMoeda4 .Or. lMoeda5
		RecLock('SB2',.F.)
EndIf      

If	lMoeda2
		Replace B2_CM2 		With 	0
		Replace B2_VATU2	With	0
EndIf

If	lMoeda3
		Replace B2_CM3 		With	0
		Replace B2_VATU3	With	0
EndIf

If	lMoeda4
		Replace B2_CM4 		With	0
		Replace B2_VATU4	With	0
EndIf
		
If	lMoeda5
		Replace B2_CM5 		With	0			
		Replace B2_VATU5	With	0			
EndIf

If	Empty(cMvMOEDA) .Or. lMoeda2 .Or. lMoeda3 .Or. lMoeda4 .Or. lMoeda5
		MsUnlock()
EndIf      

Return 