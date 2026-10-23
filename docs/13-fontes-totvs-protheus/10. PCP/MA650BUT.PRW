
#INCLUDE "PROTHEUS.CH"

User Function MA650BUT()
    //Não declarar o array aRotina
    //Adiciona um novo item no menu principal do MATA650
    //aAdd(aRotina,{'Texto do Item','Nova_funcao( )',0,5 })
    Local aMenu := paramixb
    //paramixb[1]
    Local nPosExc := 0

    nPosExc := ascan(aMenu,{|x| UPPER(Trim(x[2])) == "A650DELETA"})

    IF nPosExc > 0

        aMenu[nPosExc][2] := "U_DLP10F03()"

    ENDIF
    aAdd(aMenu,{'Prioridade Dlp','U_DLP10F04()',0,4 })
    aAdd(aMenu,{'Altera Dt Em Lote','U_IMPRTSC2()',0,4 })
Return aMenu
