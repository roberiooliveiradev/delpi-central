


#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"

User function MT235G2()

	Local aArea := GetArea()
	Local aSC1Area := GetArea("SC1")
	Local nTipo		:= PARAMIXB[2]
	Local lRet		:= .T.
	Private cAliSC1	        := PARAMIXB[1]

	If nTipo==3 //Solicitacao de Compra

		DbSelectArea('SC1')
		DbSetOrder(1)
		SC1->(DbGoTo(  (cAliSC1)->(SC1RECNO)  ) )//(DbSeek( (cAliSC1)->(C1_FILIAL)+(cAliSC1)->(C1_NUM)+(cAliSC1)->(C1_ITEM) ) )

		//    If SC1->(!Eof())
		lVld := .f.
		if ! lVld
			IF ALLTRIM(RetCodUsr()) $ "000074" .AND. ALLTRIM(SC1->C1_USER) $"000149_000125_"
				lVld := .t.
			ENDIF
		ENDIF
		if ! lVld
			IF ALLTRIM(RetCodUsr()) $ "000131" .AND. ALLTRIM(SC1->C1_USER) $"000093_000061_000265_000165_000048_000151_000062_000290_000156_000127"
				lVld := .t.
			ENDIF
		ENDIF
		if ! lVld
			IF EMPTY(SC1->C1_ORIGEM) .AND. ALLTRIM(RetCodUsr()) !=ALLTRIM(SC1->C1_USER) .AND.!( ALLTRIM(RetCodUsr()) $"000008_000000") .AND.;
					UPPER(ALLTRIM( SC1->C1_OBS) )!= UPPER("SC criada por aglutinacao") .AND. !FWISADMIN()


				lRet := .F.
				FWAlertWarning("Atenção. Não é permitida a exclusao de Solicitação de Compra de outro Colaborador", "Delpi - Compras SC")
			ENDIF

			//  EndIf

		EndIf

		if ! lVld
			IF FWISADMIN()
				lVld := .t.
			ENDIF
		ENDIF
	EndIf
	restArea(aArea)
	restArea(aSC1Area)

Return(lRet)
