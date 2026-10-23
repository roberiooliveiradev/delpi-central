#include "protheus.ch"
#INCLUDE "TOTVS.CH"
#INCLUDE "FWLIBVERSION.CH"
#INCLUDE "FWEVENTVIEWCONSTS.CH"
#Include 'TOPConn.ch'

/*
Gabriel Araujo  03/2023
Ponto de Entrada para permitir apebnas que o Admin possa excluir notas em que o estoque ficara negativo
*/
User Function MT103EXC()
    lOCAL lRet := .T.
    lOCAL cUsrPer   := supergetmv("MV_ZEXCNF",.F.,"000000_000008") // codigo dos usuarios que podem excluir com estoque negativo
    Local aArea     :=getarea()
    Local aAreaB2	:= SB2->(GetArea())
    lOCAL cEol := chr(10)

    // Valido se o Usuario está na lista de permissao

    if !(RetCodUsr() $cUsrPer)

        cSql := "SELECT D1_COD,D1_LOCAL,SUM(D1_QUANT)D1_QUANT FROM  " + RetSqlName("SD1") + "   SD1 (NOLOCK) " + cEol
        cSql += "  WHERE  SD1.D_E_L_E_T_ = '' " + cEol
        cSql += "      AND SD1.D1_FILIAL   ="+valtosql(SF1->F1_FILIAL)  + cEol
        cSql += "      AND SD1.D1_DOC      ="+valtosql(SF1->F1_DOC)     + cEol
        cSql += "      AND SD1.D1_SERIE    ="+valtosql(SF1->F1_SERIE)   + cEol
        cSql += "      AND SD1.D1_FORNECE  ="+valtosql(SF1->F1_FORNECE) + cEol
        cSql += "      AND SD1.D1_LOJA     ="+valtosql(SF1->F1_LOJA)    + cEol
        cSql += "   AND EXISTS(SELECT NULL FROM  " + RetSqlName("SF4") + " SF4 (NOLOCK) " + cEol
        cSql += "   WHERE SF4.D_E_L_E_T_ = '' " + cEol
        cSql += "       AND F4_FILIAL    ='' " + cEol
        cSql += "       AND F4_CODIGO    = D1_TES " + cEol
        cSql += "       AND F4_ESTOQUE   = 'S') " + cEol
        cSql += " GROUP BY   D1_COD,D1_LOCAL"

        "
        If Select('TMPSD1') <> 0
            TMPSD1->(dbCloseArea())
        Endif

        TCQuery cSql Alias TMPSD1 New
        While TMPSD1->(!eof()) .AND. lRet
            nQtdSldB2 := 0.00
            dbSelectArea("SB2")
            SB2->(DbSetOrder(1))
            If	(SB2->(DbSeek(xFilial('SB2')+TMPSD1->D1_COD+TMPSD1->D1_LOCAL)))
                nQtdSldB2 := SaldoMov(/*lNecessidade*/,/*lEmpenho*/,/*dDataFim*/,/*lConsTerc*/, /*nQtdEmp*/,/* nQtdPrj*/, .f./*lSaldoSemR*/,SF1->F1_DTDIGIT,/*lConsEmpSA*/)

            ENDIF
            // nQtdSld := SaldoMov(/*lNecessidade*/,/*lEmpenho*/,/*dDataFim*/,/*lConsTerc*/, /*nQtdEmp*/,/* nQtdPrj*/, .f./*lSaldoSemR*/, ddemissao+2,/*lConsEmpSA*/)

            //QtdComp
            if QtdComp(nQtdSldB2 )-QtdComp(TMPSD1->D1_QUANT) < 0
                FWAlertError("Não é permitido excluir este documento de entrada.O Saldo em estoque ficará comprometido. Procure o administrador do sistema.", "Delpi")
                lRet := .f.
            endif
            TMPSD1->(dbskip())
        Enddo

        TMPSD1->(dbCloseArea())
    Endif
    restarea(aArea    )
    restarea(aAreaB2	)
Return lRet
