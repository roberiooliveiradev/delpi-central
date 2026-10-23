#include "protheus.ch"

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³SF1100I   ºAutor  ³Microsiga           º Data ³  11/12/15   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ Ponto de Entrada Executado na confirmacao da nota fiscal   º±±
±±º          ³ de entrada, quando for originada de importacao A2_EST = EX º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ AP                                                        º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

User function MT103FIM()

	// ParamIxb[1] - Opcao escolhida pelo usuário
	// ParamIxb[2] - 1 Confirmado ou 2 Cancelado

	If	ParamIxb[1] == 3  .And. ParamIxb[2] == 1

		If 	SF1->F1_EST == "EX"  .And. ;
				FunName()=='MATA103' .And. ;
				SF1->F1_FORMUL = "S" .And. ;
				Upper(Alltrim(SF1->F1_ESPECIE)) = "SPED" .AND. ;
				!(SF1->F1_TIPO $ "D, B")
			ExecBlock("DLP017",.F.,.F.)
		EndIf

		//IF cEmpAnt $"05"

		//	FWMsgRun( ,{|| u_DLP02F05(SF1->F1_FILIAL ,SF1->F1_DOC,SF1->F1_SERIE,SF1->F1_FORNECE,SF1->F1_LOJA)},"Processando...")

		//endif

	EndIf

Return


SaldoMov(.T./*lNecessida*/, .T./*lEmpenho*/, ddemissao, .T./*lConsTerc*/, /*nQtdEmp*/, /*nQtdPrj*/, .T./*lSaldoSemR*/, ddemissao,.T./*lConsEmpSA*/)
