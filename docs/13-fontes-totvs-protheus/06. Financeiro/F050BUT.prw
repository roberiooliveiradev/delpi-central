#include 'totvs.ch'
#include 'rwmake.ch'


USER FUNCTION F050BUT()
	Local aBtn := {}

	//	Aadd(aBtn, {"DLP06F02", { ||U_DLP06F2A() }, OemToAnsi( 'Inserir Token p/ envio de Borderô' ) } )
	Aadd(aBtn, {"DLP06F03", { ||U_DLP06F03() }, OemToAnsi( 'Digita  Token p/Liberacao Bordero' ) } )

Return( aBtn )
