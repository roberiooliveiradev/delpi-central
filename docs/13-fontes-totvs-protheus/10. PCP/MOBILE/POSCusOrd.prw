#INCLUDE 'TOTVS.CH'

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 25/07/2024
@version version
/*/
User Function POSCusOrd()
	Local cQuery      := PARAMIXB[4]
	Local nFieldsIni  := AT("TC_",cQuery)
	Local nFieldsFin  := AT("FROM",cQuery)
	Local cFields     := AllTrim(SUBSTRING(cQuery,nFieldsIni,nFieldsFin-nFieldsIni))
	Local cTable      := AllTrim(SUBSTR(cQuery,nFieldsFin+4))
	Local cSrchName   := ""
	Local cQueryOrd   := ""
	Local aOrder      := {}

	cSrchName  := "Consulta Carga Máquina"

	cQueryOrd := "SELECT "
	cQueryOrd += cFields
	cQueryOrd += " FROM " + cTable + " TC"
	cQueryOrd += " LEFT JOIN "+RetSqlName("SH8")+" SH8 ON SH8.H8_OP = TC.TC_OP AND SH8.H8_OPER = TC.TC_OPER"
	cQueryOrd += " ORDER BY SH8.H8_OPER,SH8.H8_BITINI"

	aAdd(aOrder,cSrchName)
	aAdd(aOrder,cQueryOrd)

Return aOrder
