#INCLUDE 'TOTVS.CH'

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 25/06/2024
@version version
/*/
User Function 	FINALEG ()

	Local nReg 			:= PARAMIXB[1] // Com valor: Abrir a telinha de legendas ### Sem valor: Retornar as regras
	Local cAlias 		:= PARAMIXB[2] // SE1 ou SE2
	Local aRegras 	:= PARAMIXB[3] // Regras do padrão
	Local aLegendas := PARAMIXB[4] // Legendas do padrão
	Local aRet := {}
	Local nI := 0
	Local cBlqBor := ""
	Local cTmpAls := GetNextAlias()
	IF cEmpAnt == "01"
		If nReg = Nil

			If cAlias = "SE2"

				BEGINSQL ALIAS cTmpAls
				SELECT
					DISTINCT TRIM(SEA.EA_NUMBOR) AS BORDKEY
				FROM
					%Table:SEA% SEA
				WHERE
					SEA.D_E_L_E_T_ = ' '
					AND SEA.EA_YBLQPIX = 'S'
				ENDSQL

				while !(cTmpAls)->(eof())
					cBlqBor += ALLTRIM((cTmpAls)->BORDKEY) + "|"
					(cTmpAls)->(DBSKIP())
				end

				aAdd(aRet,{"ALLTRIM(SE2->E2_NUMBOR) $ '"+cBlqBor+"' .AND. !Empty(SE2->E2_NUMBOR)","BR_VIOLETA"})

				For nI := 1 To Len(aRegras)
					aAdd(aRet,{aRegras[nI][1],aRegras[nI][2]})
				Next nI
			else
				For nI := 1 To Len(aRegras)
					aAdd(aRet,{aRegras[nI][1],aRegras[nI][2]})
				Next nI
			Endif

		Else

			If cAlias = "SE2"

				aAdd(aLegendas,{"BR_VIOLETA","Título em um Borderô bloqueado"})

			Endif

			BrwLegenda(cCadastro, "Legenda", aLegendas)

		Endif
	else
		If cAlias = "SE2"
			For nI := 1 To Len(aRegras)
				aAdd(aRet,{aRegras[nI][1],aRegras[nI][2]})
			Next nI
		else
			For nI := 1 To Len(aRegras)
				aAdd(aRet,{aRegras[nI][1],aRegras[nI][2]})
			Next nI
		Endif



	Endif

Return aRet
