#Include 'Protheus.ch'

User Function MT010COR()

    Local aCores:={}

    //Alert ("Passou pelo aCores")

    aAdd(aCores,{'B1_TIPO == "AI"','BR_VERMELHO', 'Produto teste','B1_TIPO == "AI"'})
    aAdd(aCores,{'B1_TIPO == "MP"','BR_VERDE', 'Produto MP','B1_TIPO == "MP"'})

Return aCores

