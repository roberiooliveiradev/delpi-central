#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"

/*
01  - Desenvolver caixa de perguntas com base no parambox
    - DA1 - Unica
    - Produto De/Ate
    - ID Calculo
    - Atualiza Tabela de Venda Sim/Nao
02  Desenvolver query para listar os produtos
03  Desenvolver Rotina para chamar o MVC
*/


user function DLP05F02()

    Local lRet := .t.
    Local dDtEnt  :=  GdFieldGet('C6_ENTREG',,.T.)
    conout("teste")
    if dDtEnt < date()
        lRet := .f.

        FWAlertWarning("A data de entrega não pode ser menor que a data do sistema", "Delpi - Pedido de Vendas")

    endif
    // GDFieldPut( 'AIB_ZDTINC', DATE())
    // M->AIB_ZDTINC := DATE()

RETURN lRet
