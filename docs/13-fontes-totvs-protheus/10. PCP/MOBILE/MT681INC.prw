#include 'totvs.ch'

/*/{Protheus.doc} nomeFunction
Ponto de entrada - Inclusão de Apontamento - Rotinda Produção PCP Mod.2
@type user function
@author Pedro Lindenberg
@since 13/06/2024
/*/
User Function MT681INC()
	Local aAreas  := {SC2->(GETAREA()),SB1->(GETAREA())}
	Local aCab 		:= {}
	Local aItens 	:= {}
	Local aLinha := {}
	Local aLogAuto := {}
	Local nY := 0
	Local cPerda := M->H6_CCCA01
	Local cErro := ""
	Private cOP 	:= SH6->H6_OP

	SC2->(DbSetOrder(1))
	If SC2->(DbSeek(xFilial('SC2')+cOP)) .AND. IsInCallStack('POST_MATA681')

		// IF SH6->H6_QTDPROD <= (SC2->C2_QUANT - SC2->C2_QUJE)

		aCab   :={{"BC_OP" ,SH6->H6_OP , Nil},;
			         {"BC_RECURSO"              , SH6->H6_RECURSO, Nil},;
			         {"BC_OPERAC"               , SH6->H6_OPERAC , Nil}}

		aLinha := {;
			         {"BC_QUANT"                , cPerda         , Nil},;
			         {"BC_QTDDEST"              , cPerda         , Nil},;
			         {"BC_PRODUTO"              , SH6->H6_CCCA02 , Nil},; // Empenho
		         	 {"BC_LOCORIG"              , SH6->H6_LOCAL  , Nil},;
			         {"BC_TIPO"                 , SH6->H6_CCCA03 , Nil},; // R ou S
		         	 {"BC_DTVALID"              , SH6->H6_DTAPONT, Nil},;
			         {"BC_DATA"                 , SH6->H6_DTAPONT, Nil},;
			         {"BC_OPERADO"              , SH6->H6_OPERADO, Nil},;
			         {"BC_OBSERVA"              , SH6->H6_IDENT  , Nil},;
			}
		// {"BC_MOTIVO"    , SH6->H6_CCCA03    , Nil};}

		AAdd(aItens,aLinha)

		MsExecAuto( {|x,y,z| MATA685(x,y,z) }, aCab, aItens, 3)

		If lMsErroAuto

			aLogAuto := GetAutoGrLog()

			For nY := 1 To Len(aLogAuto)
				cErro += ALLTRIM(aLogAuto[nY]) + CRLF
			Next nY

			Help(cErro)

		Endif

		// ENDIF

	ENDIF

	AEval(aAreas,{|x,y| RestArea(x) })

Return
