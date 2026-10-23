


#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"

/*/{Protheus.doc} MSC1110D
    (long_description)
    @type  Ponto de Entrada
    @author Gabriel Araujo - TSC
    @since 01/05/2023
    Function A110Deleta  - Função de exclusão da Solicitação de Compras.

EM QUE PONTO :  Antes da apresentaçao da dialog de exclusão da SC possibilita validar a solicitação posicionada para continuar e executar a exclusão ou não.

/*/

User function MSC1110D()
    Local lRet := .t.
    Local aArea := GetArea()
    Local aSC1Area := GetArea("SC1")
    // Local aAlter := Paramixb[1]     //-- Rotina de customização do usuário
    // conout("stop")
    lVld := .f.
    /*max*/
    if ! lVld
        IF ALLTRIM(RetCodUsr()) $ "000074" .AND. ALLTRIM(SC1->C1_USER) $"000149_000125_"
            lVld := .t.
        ENDIF
    ENDIF
    /*peter*/
    if ! lVld
        IF ALLTRIM(RetCodUsr()) $ "000131" .AND. ALLTRIM(SC1->C1_USER) $"000093_000061_000265_000165_000048_000151_000062_000290_000156_000127"
            lVld := .t.
        ENDIF
    ENDIF
    if ! lVld
        IF EMPTY(SC1->C1_ORIGEM) .AND. ALLTRIM(RetCodUsr()) !=ALLTRIM(SC1->C1_USER) .AND.;
                !( ALLTRIM(RetCodUsr()) $"000008_000000") .AND. ;
                UPPER(ALLTRIM( SC1->C1_OBS) )!= UPPER("SC criada por aglutinacao")

            lRet := .F.
            FWAlertWarning("Atenção. Não é permitida a exclusao de Solicitação de Compra de outro Colaborador", "Delpi - Compras SC")
        ENDIF
    ENDIF
    if ! lVld
        IF FWISADMIN()
            lVld := .t.
        ENDIF
    ENDIF
    restArea(aArea)
    restArea(aSC1Area)
Return lRet
