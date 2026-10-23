#INCLUDE "PROTHEUS.CH"

/*/{Protheus.doc} User Function MA126CPO
   PE alterar valores de outros campos na Aglutinação
   @type Function
   @since 12/11/2024
   @author user
/*/
User Function  MA126CPO()


    Local Acampos   := PARAMIXB
    Local Aarray    := {}  // Campos do usuário que irão ser adicionados ao array aCampos.

    CONOUT("STOP")
    // Aadd(Aarray,{"C1_GRPRD" ,"0001"})


Return (Aarray)
