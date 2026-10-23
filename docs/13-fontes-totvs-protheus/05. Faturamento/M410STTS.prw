/*/{Protheus.doc} M410STTS
    Este ponto de entrada pertence à rotina de pedidos de venda, MATA410().
Está em todas as rotinas de inclusão, alteração, exclusão, cópia e devolução de compras.
Executado após todas as alterações no arquivo de pedidos terem sido feitas.
Parâmetros:
nOper --> Tipo: Numérico - Descrição: Operação que está sendo executada, sendo:
3 - Inclusão 4 - Alteração 5 - Exclusão 6 - Cópia 7 - Devolução de Compras

    @since 14/10/2020
    @version version

/*/
user function M410STTS()

    // Local _nOper := PARAMIXB[1]

    // if ( _nOper == 3 .or. _nOper ==4) .and. !l410Auto

    //     //    u_DLP05F01()

    // endif
Return nil
