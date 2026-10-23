#include "totvs.ch"

/*/{Protheus.doc} User Function MPADDCPO
   Permite adicionar campos na interface Ver Mais do app Meu Protheus.
   @type Johnni C. Moraes
   @since 01/01/2024
   @author user
/*/
User Function MPADDCPO()
	Local cCampos := ""//  A separação dos campos devem ser feitos com uma barra vertical ( | )
	Local cAlias := PARAMIXB[1] // Alias do documento posicionado

	If  cAlias == "SC1"
		cCampos := "C1_OBS"
	EndIf

Return (cCampos)
