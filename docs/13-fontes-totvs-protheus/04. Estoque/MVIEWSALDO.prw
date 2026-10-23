

#include "colors.ch"
#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"
#include "Directry.ch"


User Function MVIEWSALDO()
    Local cProd  := PARAMIXB[1]
    Local cLocal := PARAMIXB[2]
    Local aSaldo := PARAMIXB[3]
    Local aRet   := {}
    Local cEol := chr(13)


    conout("gabriel")


    cSql := 	"SELECT B2_FILIAL,B2_COD,B2_LOCAL "+cEol
    cSql += " FROM dbo."+ RetSqlName("SB2")  +" SB2 (NOLOCK)" +cEol
    cSql += " WHERE D_E_L_E_T_ = '' AND B2_QATU > 0 AND B2_COD = "+valtosql(cProd)
    cSql += " order by 1,2 "


    If (Select("QRY1") <> 0)
        dbSelectArea("QRY1")
        dbCloseArea()
    Endif

    aSaldo[1][1]  := 0
    aSaldo[1][2]  := 0
    aSaldo[1][3]  := 0
    aSaldo[1][4]  := 0
    aSaldo[1][5]  := 0
    aSaldo[1][6]  := 0
    aSaldo[1][7]  := 0
    aSaldo[1][8]  := 0
    aSaldo[1][9]  := 0
    aSaldo[1][10] := 0
    aSaldo[1][11] := 0
    aSaldo[1][12] := 0


    TCQuery cSql NEW  ALIAS "QRY1"

    While QRY1->(!Eof())

        DbSelectArea("SB2")
        DbSetOrder(1)        //B2_FILIAL + B2_COD + B2_LOCAL
        If DbSeek(xFilial('SB2') + cProd	+ QRY1->B2_LOCAL)

            nSldSB2 := SaldoSB2()

            aSaldo[1][1]  += nSldSB2             //  Qtd. Disponivel (SaldoSB2())
            aSaldo[1][2]  += SB2->B2_QATU        //  Saldo Atual (B2_QATU)
            aSaldo[1][3]  += SB2->B2_QPEDVEN     //  Qtd. Pedido de Vendas (B2_QPEDVEN)
            aSaldo[1][4]  += SB2->B2_QEMP        //  Qtd. Pedido de Vendas (B2_QPEDVEN)
            aSaldo[1][5]  += SB2->B2_SALPEDI     //  Qtd. Empenhada (B2_QEMP)
            aSaldo[1][6]  += SB2->B2_QEMPSA      //  Qtd. Prevista Entrada (B2_SALPEDI)
            aSaldo[1][7]  += SB2->B2_RESERVA     //  Qtd. Empenhada S.A. (B2_QEMPSA)
            aSaldo[1][8]  += SB2->B2_QTNP        //  Qtd. Reservada (B2_RESERVA)
            aSaldo[1][9]  += SB2->B2_QNPT        //  Qtd. Ter.Ns.Pd. (B2_QTNP)
            aSaldo[1][10] += SB2->B2_QTER        //  Saldo Poder 3 (B2_QTER)
            aSaldo[1][11] += SB2->B2_QEMPN       //  Qtd. Emp. NF (B2_QEMPN)
            aSaldo[1][12] += SB2->B2_QACLASS     //  Qdt. a Endereçar (B2_QACLASS)
        endif
        QRY1->(dbSkip())

    EndDo
    //PARAMIXB3[1,1] -> Qtd. Disponivel (SaldoSB2())
    //PARAMIXB3[1,2] -> Saldo Atual (B2_QATU)
    //PARAMIXB3[1,3] ->  Qtd. Pedido de Vendas (B2_QPEDVEN)
    //PARAMIXB3[1,4] ->  Qtd. Empenhada (B2_QEMP)
    //PARAMIXB3[1,5] ->  Qtd. Prevista Entrada (B2_SALPEDI)
    //PARAMIXB3[1,6] ->  Qtd. Empenhada S.A. (B2_QEMPSA)
    //PARAMIXB3[1,7] ->  Qtd. Reservada (B2_RESERVA)
    //PARAMIXB3[1,8] ->  Qtd. Ter.Ns.Pd. (B2_QTNP)
    //PARAMIXB3[1,9] ->  Qtd. Ns.Pd.Ter (B2_QNPT)
    //PARAMIXB3[1,10] -> Saldo Poder 3 (B2_QTER)
    //PARAMIXB3[1,11] -> Qtd. Emp. NF (B2_QEMPN)
    //PARAMIXB3[1,12] -> Qdt. a Endereçar (B2_QACLASS)
    // If Len(aSaldo) > 0 .And. Alltrim(cProd) == '01' .And. cLocal <> '99'
    //     //      aAdd(aRet,{aSaldo[1,1]+546,aSaldo[1,2],aSaldo[1,3],aSaldo[1,4]+500,aSaldo[1,5],aSaldo  [1,6],aSaldo[1,7],aSaldo[1,8],aSaldo[1,9],aSaldo[1,10],aSaldo[1,11],aSaldo[1,12]})
    // Endif
Return(aSaldo)
