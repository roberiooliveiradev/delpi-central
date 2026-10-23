/*/{Protheus.doc} mr440qtd
    ponto-de-Entrada: MR440QTD - Manipula quantidade no cálculo do relatório
    LOCALIZAÇÃO   : Localizado na função de impressão dos dados
    EM QUE PONTO : É chamado após o cálculo da quantidade que será utilizada nos cálculos do relatório e impressa na coluna de 'Quantidade' ; Este Ponto de Entrada pode ser utilizado para manipular esta quantidade.
    Eventos
    Programa Fonte
    MATR440.PRX
    Sintaxe
    MR440QTD - Manipula quantidade no cálculo do relatório ( < PARAMIXB> ) --> nQuant

    Conforme Regra Solicitada pela Joici, nao é para permitir adicionar + 1 peça conforme calculo de necessidade bruta
    @author  GABRIEL

    @since   21-10-2020
/*/

user function MS170QTD()
    Local aArea:=getarea()
    Local nQtd := PARAMIXB

    //if nQtd >0
    //    nQtd -= 1
    //endif
    RestArea(aArea)
Return nQtd

User Function MR440QTD()
    Local aArea:=getarea()
    Local nQtd := PARAMIXB
    Local xNecess := 0.00
    Local xEmin := QtdComp(RetFldProd(SB1->B1_COD,"B1_EMIN"))

    xNecess := nestseg+nsaldo
    if NESTSEG > 0 .and. xEmin == 0.00
        if xNecess > NESTSEG
            nQtd := 0.00
        endif
    endif

    /*

NSALDO-NQUANT
-2028
NESTSEG
8000
NESTSEG*-1
-8000
    */
    //if nQtd >0
    //    nQtd -= 1
    //endif
    RestArea(aArea)
Return(nQtd)
