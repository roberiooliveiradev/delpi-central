#include "protheus.ch"
#include "topconn.ch"

User Function DLP016()

Local aArea		:= GetArea()
Local cProduto 	:= M->G2_PRODUTO
Local oModel	:= FWModelActive()
Local oGridSG2	:= oModel:GetModel("MATA632_SG2")

Local nX		:= 0
Local lRet		:= .T.

If	!MsgYesNo('Deseja Importar as Operações da '+IIf(cFilAnt=='01','Filial','Matriz')+' ?')
	RestArea(aArea)
	Return cProduto
EndIf

If	Select('TSG2')<>0
	TSG2->(DbCloseArea())
EndIf

BeginSql Alias 'TSG2'
	SELECT * FROM %Table:SG2%
	WHERE %NotDel% AND G2_FILIAL = %Exp:IIf(cFilAnt=='01','02','01')%
	AND G2_PRODUTO = %Exp:cProduto%
	ORDER BY G2_FILIAL, G2_CODIGO, G2_PRODUTO, G2_REFGRD, G2_OPERAC
EndSql

aEval(SG2->(dbStruct()), {|x| If(x[2] <> "C" .And. SG2->(FieldPos(x[1])) > 0, TcSetField('TSG2',x[1],x[2],x[3],x[4]),Nil)})

If	TSG2->(Eof())
	MsgInfo('Não existe Roteiro de Operações deste Produto na '+IIf(cFilAnt=='01','Filial','Matriz')+' !!!')
	RestArea(aArea)
	Return cProduto
EndIf

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Analisa os dados do Roteiro da outra filial e inclui no atual   .³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

// Obtemos a estrutura de dados do item
aAux	 := oModel:GetModel("MATA632_SG2"  ):GetStruct():GetFields()
nI   	 := 1
dbSelectArea('TSG2')
While !TSG2->(Eof())
	
	If	nI > 1
		oGridSG2:AddLine()
	EndIf
	
	For nJ := 1 To TSG2->(FCount())
		
		// Verifica se os campos passados existem na estrutura de item
		If ( nPos := aScan( aAux, { |x| AllTrim( x[3] ) ==  AllTrim( TSG2->(FieldName(nJ)) ) } ) ) > 0
			
			// Setar variavel para validacao de retorno da funcao SetValue
			lAux := .T.
			
			If	AllTrim(TSG2->(FieldName(nJ))) == 'G2_FILIAL'
				lAux := oModel:SetValue( "MATA632_SG2", TSG2->(FieldName(nJ)), IIf(cFilAnt=='01','01','02') )
			Else
				// Setar Variavel para controle de existencia ou nao dos cadastros de Recurso / Ferramenta
				lErro := .F.
				If	AllTrim(TSG2->(FieldName(nJ))) == 'G2_RECURSO'
					SH1->(DbSetOrder(1))
					SH1->(DbSeek(xFilial('SH1')+TSG2->(FieldGet(nJ))))
					If	!SH1->(Found())
						lErro := .T.
					EndIf
				ElseIf	AllTrim(TSG2->(FieldName(nJ))) == 'G2_FERRAM'
					SH4->(DbSetOrder(1))
					SH4->(DbSeek(xFilial('SH4')+TSG2->(FieldGet(nJ))))
					If	!SH4->(Found())
						lErro := .T.
					EndIf
				ElseIf	AllTrim(TSG2->(FieldName(nJ))) == 'G2_CTRAB'
					SHB->(DbSetOrder(1))
					SHB->(DbSeek(xFilial('SHB')+TSG2->(FieldGet(nJ))))
					If	!SHB->(Found())
						lErro := .T.
					EndIf
				ElseIf	AllTrim(TSG2->(FieldName(nJ))) $ 'G2_OPERGRP/G2_OPE_OBR/G2_SEQ_OBR/G2_LAU_OBR'
					lErro := .T.
				EndIf
				
				If	!lErro
					lAux := oModel:SetValue( "MATA632_SG2", TSG2->(FieldName(nJ)), TSG2->(FieldGet(nJ)) )
				EndIf
			EndIf
			
			If	!lAux
				// Caso a atribuição não possa ser feita, por algum motivo (validação, por exemplo)
				// o método SetValue retorna .F.
				lRet    := .F.
				oGridSG2:GoLine( nI )
				
				If !oGridSG2:IsDeleted()
					oGridSG2:DeleteLine()
				EndIf
				
				Exit
				
			EndIf
		EndIf
	Next
		
	If	!lRet
		MsgAlert('Não foi possível incluir as operações do produto, problema no preenchimento do campo '+AllTrim(TSG2->(FieldName(nJ)))+' !!!')
		Exit
	EndIf
	
	// Adiciona mais 1 para proxima linha da getdados
	nI++

	TSG2->(DbSkip())
EndDo

oGridSG2:GoLine(1)

RestArea(aArea)

Return cProduto