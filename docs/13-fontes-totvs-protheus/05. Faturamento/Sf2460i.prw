#INCLUDE "rwmake.ch"      // incluido pelo assistente de conversao do AP5 IDE em 18/10/00

/*SIGAVILLE
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±³Cliente      ³ DELPI COMPONENTES LTDA                                  ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Programa     ³ SF2460I          ³ Responsavel ³ CRISTIANO NOVAK        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³Descri‡„o    ³ PONTO CHAMADA NOTA FISCAL DELPI                         ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÂÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Data        ³ 04/11/03         ³ Implantacao ³   /  /                 ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÁÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Programador ³ MARCOS SCHOEFFEL                                        ³±±
±±ÃÄÄÄÄÄÄÄÄÄÄÄÄÄÅÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ´±±
±±³ Objetivos   ³                                                         ³±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
SF24 - MTA10T
*/

User Function sf2460i()

/*
dbSelectArea("SX5")
dbSetOrder(1)
dbSeek(xFilial("SX5") + "01"+Alltrim(SF2->F2_SERIE),.T.)
If xFilial("SX5") + "01"+Alltrim(SF2->F2_SERIE) == SX5->X5_FILIAL+SX5->X5_TABELA+Alltrim(SX5->X5_CHAVE)
	reclock("SX5",.f.)
	SX5->X5_DESCRI  := StrZero(Val(SF2->F2_DOC)+1,6)
	SX5->X5_DESCSPA := StrZero(Val(SF2->F2_DOC)+1,6)
	SX5->X5_DESCENG := StrZero(Val(SF2->F2_DOC)+1,6)
	msunlock("SX5")
EndIf
*/

dbSelectArea("SD2")
dbSetOrder(3)
dbSeek(xFilial("SD2")+SF2->F2_DOC+SF2->F2_SERIE,.T.)

dbSelectArea("SC5")
dbSetOrder(1)
dbSeek(xFilial("SC5")+SD2->D2_PEDIDO,.T.)
iF xFilial("SC5")+SD2->D2_PEDIDO == SC5->C5_FILIAL+SC5->C5_NUM
	sNatureza := SC5->C5_NATUREZ
EndIf
iF SC5->C5_TIPO=='D' .Or. SC5->C5_TIPO=='B'
	dbSelectArea("SE2")
	dbSetOrder(6)
	dbSeek(xFilial("SE2")+SF2->F2_CLIENTE+SF2->F2_LOJA+SF2->F2_SERIE+SF2->F2_DOC,.T.)
	While !Eof() .And.  SE2->E2_FILIAL+SE2->E2_FORNECE+SE2->E2_LOJA+SE2->E2_PREFIXO+SE2->E2_NUM == ;
		xFilial("SE2")+SF2->F2_CLIENTE+SF2->F2_LOJA+SF2->F2_SERIE+SF2->F2_DOC
		RecLock("SE2",.F.)
		SE2->E2_NATUREZ := sNatureza
		msUnlock("SE2")
		dbSelectArea("SE2")
		DbSkip()
	EndDo
Else
	dbSelectArea("SE1")
	dbSetOrder(2)
	dbSeek(xFilial("SE1")+SF2->F2_CLIENTE+SF2->F2_LOJA+SF2->F2_SERIE+SF2->F2_DOC,.T.)
	While SE1->E1_FILIAL + SE1->E1_PREFIXO+SE1->E1_NUM == xFilial("SE1")+SF2->F2_PREFIXO+SF2->F2_DOC .And. !Eof()
		RecLock("SE1",.F.)
		SE1->E1_NATUREZ := sNatureza
		msUnlock("SE1")
		dbSelectArea("SE1")
		DbSkip()
	EndDo
EndIf                    
Return