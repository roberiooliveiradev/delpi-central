

User Function DLP05G02()

    CONOUT("M->C6_PRODUTO " + M->C6_PRODUTO)
    CONOUT("C6_PRODUTO->C6_PRODUTO " +GDFieldGet("C6_PRODUTO"))
    cCodPrd := M->C6_PRODUTO
    cItWeg := posicione("SB1",1,XFILIAL("SB1")+cCodPrd,"B1_ITEMWEG")

Return cItWeg
