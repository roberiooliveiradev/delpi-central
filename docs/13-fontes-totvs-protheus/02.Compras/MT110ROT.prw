#INCLUDE "PROTHEUS.CH"
#INCLUDE "FWMVCDEF.CH"
#INCLUDE "FWADAPTEREAI.CH"
#Include "FWLIBVERSION.CH"

/*/{Protheus.doc} MT120BRW

    //Define Array contendo as Rotinas a executar do programa
// ----------- Elementos contidos por dimensao ------------
// 1. Nome a aparecer no cabecalho
// 2. Nome da Rotina associada
// 3. Usado pela rotina
// 4. Tipo de Transa‡„o a ser efetuada
//    1 - Pesquisa e Posiciona em um Banco de Dados
//    2 - Simplesmente Mostra os Campos
//    3 - Inclui registros no Bancos de Dados
//    4 - Altera o registro corrente
//    5 - Remove o registro corrente do Banco de Dados
//    6 - Altera determinados campos sem incluir novos Regs

    @author  Gabriel Araujo
    @since   27-01-2021
/*/


user function MT110ROT()

    AAdd( aRotina, { 'Eliminar Residuo', 'U_120ROT()', 0, 0 } )
    AAdd( aRotina, { 'Extrato Produto', 'U_DLP02F11()', 0, 0 } )
    SetKey( VK_F8, { || U_DLP02F11(SC1->C1_PRODUTO) } )
Return aRotina
