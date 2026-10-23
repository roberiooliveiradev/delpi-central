#include 'protheus.ch'
#include 'parmtype.ch'

user function DL05A01()

	Local lRet := .t.
	Local cCodPro   := &(ReadVar())
	Local cMsg := ""
	Local aArea := getarea()

	//5 A5_FILIAL, A5_CODPRF, A5_PRODUTO, A5_FABR, A5_FORNECE, R_E_C_N_O_, D_E_L_E_T_

	dbSelectArea("SA5")
	SA5->(dbSetOrder(5))

	IF (dbseek(xFilial("SA5")+cCodPro))
		if SUBSTR( ReadVar(),4,2) $ 'C6'

			GdFieldPut("C6_PRODUTO", SA5->A5_PRODUTO)

		ELSE

			GdFieldPut("C7_PRODUTO", SA5->A5_PRODUTO)

		ENDIF
		//M->C6_PRODUTO := SA5->A5_PRODUTO

	ELSE

		IF !EMPTY(cCodPro)

			cMsg:="Produto "+cCodPro+"Não Existe Cadastrado - SA5"
			Aviso("Delpi - Produto x Fornecedor",cMsg,{"OK"},3,"Atenção")
			RestArea(aArea)
			Return .f.
			
		ENDIF

	ENDIF
	RestArea(aArea)
return lRet