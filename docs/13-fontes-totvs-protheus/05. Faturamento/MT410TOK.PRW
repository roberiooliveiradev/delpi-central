#include 'protheus.ch'
#include 'topconn.ch'
#include 'parmtype.ch'
#INCLUDE "FWMVCDEF.CH"

//RGN01 - Validação da Conta Contabil no Cadastro do Cliente, caso nao exista a conta contabil será cadastrado
User Function MT410TOK()
    Local aArea := GETAREA()
    Local lRet := .t.
    Local cA1CONTA := SA1->A1_CONTA
    Local cC6CONTA := ""
    lOCAL nParc := 0
    Local cMVPrdSrv := alltrim(supergetmv("MV_YPRDSRV",.F.,"90020001"))

    Local nTotSrv := 0

    IF alltrim(cEmpAnt) $ '04_03' .and. (altera .or. inclui)

        // verifico se nao tem conta cadastrada e cadastro a mesma
        IF EMPTY(cA1CONTA) .and.  !(M->C5_TIPO $ "DB")

            cA1CONTA := U_DL05P01({ SA1->A1_CGC, iif(Empty(SA1->A1_NREDUZ),SA1->A1_NOME,SA1->A1_NREDUZ)})[2]

            RECLOCK("SA1",.F.)

            SA1->A1_CONTA := cA1CONTA

            MsUnlock()

        ENDIF

        For nX := 1 to Len( aCols )

            //GDFieldGet ( < cCampo>, [ nLine], [ lReadVar], [ aHeaderPastPar], [ aColsPastPar] ) --> xRet
            //GDFieldPut ( < cCampo>, < xConteúdo>, [ nLine], [ aHeaderPastPar], [ aColsPastPar], [ lReadVar] ) --> uLast

            if !GDDeleted(nX)

                //verifico se a conta contabil está no pedido de venda
                cC6CONTA := GDFieldGet("C6_CONTA",nX)

                IF EMPTY(cC6CONTA) .AND. !EMPTY(cA1CONTA)

                    GDFieldPut("C6_CONTA",cA1CONTA,nX)

                ENDIF
                CONOUT("cEmpAnt "     + cEmpAnt)
                CONOUT("C6_PRODUTO "  + alltrim( GDFieldGet("C6_PRODUTO",nX)))
                CONOUT("cMVPrdSrv "   + cMVPrdSrv)
                //VERIFICO SE É DA EMPRESA 04 - VENDA MATERIAIS E O PRODUTO É DO TIPO SERVIÇO E DELETO A LINHA
                if  alltrim(cEmpAnt) $ '04' .and. alltrim( GDFieldGet("C6_PRODUTO",nX)) $cMVPrdSrv
                    nTotSrv :=  GDFieldGet("C6_VALOR",nX)
                    aCols[nX,Len(aHeader)+ 1] := .t.

                ENDIF
            EndIF

        Next nX
        nPar := "0"

        if alltrim(cEmpAnt) $ '04' .and. ALLTRIM(SE4->E4_TIPO ) $ "9" .and. nTotSrv > 0

            For nXI := 1 To 26

                nPar := soma1(nPar)

                cFieldCP := "M->C5_PARC"+nPar

                IF &(cFieldCP)  >0

                    nParc ++

                ENDIF

            Next nXI

            nPar := "0"

            For nX := 1 To nParc

                nPar := soma1(nPar)

                cFieldCP := "M->C5_PARC"+nPar

                IF  &(cFieldCP)  >0

                    &(cFieldCP) := &(cFieldCP) - ( nTotSrv / nParc )

                ENDIF

            Next nX

        ENDIF

    Endif


    RestArea(aArea)
Return lRet




