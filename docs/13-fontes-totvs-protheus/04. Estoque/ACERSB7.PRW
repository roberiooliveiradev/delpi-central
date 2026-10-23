#INCLUDE "rwmake.ch"

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³ACERSB7   º Autor ³ MARCOS             º Data ³  18/02/04   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³ ACERTO DE INVENTARIO DE PRODUTOS ACABADOS                  º±±
±±º          ³                                                            º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ DELPI                                                      º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
/*/

User Function ACERSB7()

SetPrvt("NDATA")

NDATA := CTOD('  /  /  ')
cTipoDe := '  '
cTipoAte := 'ZZ'

@ 96,42 TO 323,505 DIALOG oDlg5 TITLE "Rotina de Processamento"
@ 8,10 TO 84,222
@ 48,075 SAY 'Data do inventario '
@ 48,125 GEt ndata when .t. size 40,10
@ 58,075 SAY 'Do Tipo do Produto '
@ 58,125 GEt cTipoDe when .t. size 30,10
@ 68,075 SAY 'Ate Tipo do Produto'
@ 68,125 GEt cTipoAte when .t. size 30,10

@ 91,168 BMPBUTTON TYPE 1 ACTION OkProc()
@ 91,196 BMPBUTTON TYPE 2 ACTION Close(oDlg5)
@ 23,15 SAY "Gera inventario buscando o saldo dos Produtos "
ACTIVATE DIALOG oDlg5

Return(nil)

Static Function OkProc()

Processa( {|| RunProc() } )

Close(oDlg5)

Return(nil)

Static Function RunProc()

DbSelectArea("SB2")
ProcRegua(reccount())
if nData = ctod("  /  /  ")
	msgbox("A digitacao da data do inventario e Obrigatoria!")
	return
endif

SB1->(DBSETORDER(1))
SB2->(DBSETORDER(1))
SB7->(DBSETORDER(1))
SB2->(DBSEEK(XFILIAL("SB2"),.T.))
WHILE SB2->(!EOF())
	IncProc()
	SB1->(DBSEEK(XFILIAL('SB1')+SB2->B2_COD))
	if sb1->b1_tipo >= cTipoDe .and. sb1->b1_tipo <= cTipoAte
		if !sb7->(dbseek(xfilial('SB7')+dtos(ndata)+sb2->b2_cod+sb2->b2_local))
			RECLOCK('SB7',.T.)
			SB7->B7_FILIAL  := XFILIAL('SB7')
			SB7->B7_COD     := SB2->B2_COD
			SB7->B7_LOCAL   := SB2->B2_LOCAL
			SB7->B7_TIPO    := SB1->B1_TIPO
			SB7->B7_DOC     := DTOS(nData)
			SB7->B7_QUANT   := SB2->B2_QATU
			SB7->B7_QTSEGUM := SB2->B2_QTSEGUM
			SB7->B7_DATA    := nData
			SB7->B7_DTVALID := nData
			MSUNLOCK('SB7')
		endif
	endif
	SB2->(DBSKIP())
END

msgbox("Processamento Finalizado !!!")

RETURN
