#INCLUDE "PROTHEUS.CH"
#INCLUDE "rwmake.ch"
/*/{Protheus.doc} nomeFunction

OBJETIVO:Essa rotina permite cadastrar as tabelas de preços dos fornecedores que atendem à empresa.
 Podendo ser informados os preços e a condição de pagamento a serem praticados.
Programa Fonte:COMA010.PRW


    @type  Pontod e Entrada
    @author Gabriel Araujo
    @since 19/09/2019
/*/
User Function CM010TOK()

    Local lRet := .t.
    Local nTItem := TamSx3('AIB_ITEM')[1]

    //ORDENA ARRAY POR CODIGO DE PRODUTO
    aSort(aCols,,,{|x,y| x[2] < y[2]})
    //AJUSTA O ITEM CONFORME NOVA ORDENAÇÃO POIS O INDICE É PELO ITEM
    //  For nX:= 1 To Len(aCols)
    //
    //      GdFieldPut("AIB_ITEM" , STRZERO(nX,nTItem)  , nx,,aCols )
    //
    //  next nX

Return lRet
