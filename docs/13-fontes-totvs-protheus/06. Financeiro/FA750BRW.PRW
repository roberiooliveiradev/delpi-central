#INCLUDE "TOTVS.CH"
#Include 'TOPCONN.ch'

#Define STR_PULA    Chr(13)+Chr(10)

/*/{Protheus.doc} User Function FA750BRW
    (desenvolvido para adicionar itens no menu da mBrowse)
    @type  Function
    @author Luan Woichechoscki
    @since 20/12/2022
/*/
User Function FA750BRW()

    Local aRotina := {}
    /*

	Aadd(aBtn, {"DLP06F02", { ||U_DLP06F2A() }, OemToAnsi( 'Inserir Token p/ envio de Borderô' ) } )
	Aadd(aBtn, {"DLP06F03", { ||U_DLP06F03() }, OemToAnsi( 'Digita  Token p/Liberacao Bordero' ) } )
    */

    aAdd(aRotina, {'Lib Bord Pix'          ,"U_DLP06F03()"			, 0 , 3 })
    //aAdd(aRotina, {'Ajusta Saldo'    ,"U_AjustSaldo('1')"	, 0 , 3 })
    //aAdd(aRotina, {'Alt. Venc. PR'   ,"U_ZAttBUs"			, 0 , 3 })

    //aAdd(aRotina,{"Atualizar Codigo de Barras","U_ATTCODBAR()",0,1}) //Chamada função de usuário ATTCODBAR()

Return(aRotina)
