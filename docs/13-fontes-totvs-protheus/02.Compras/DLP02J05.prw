#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE "FWEVENTVIEWCONSTS.CH"
#include 'totvs.ch'

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 19/07/2024
@version version
/*/
User Function DLP02J05()
	//RPCSetType(3)  //Nao consome licenças
	//RpcSetEnv("01","01","admin","#Delpi2024",,,) //Abertura do ambiente em rotinas automáticas

	// RocSetEnv('01','01')
	// Local jMsg as json
	// Local jNotification as json

	aCkoDados		:= {}
	cAliasExc		:= GetNextAlias()
	cQry := ""
	cEol := chr(10)
	cEventID  := "D21"
	nTamCKOARQ	:= TamSX3("CKO_ARQUIV")[1]
	cQry += " SELECT * FROM  " + RetSqlName("CKO") + " (NOLOCK) TBL1 " + cEol
	cQry += " WHERE TBL1.D_E_L_E_T_ = '' " + cEol
	cQry += " AND CKO_DT_IMP>='20240601' " + cEol //20240601?? -> Year()+Month()+'01'
	cQry += " AND CKO_CODERR != '' " + cEol
	cQry += " and not exists (select null from  " + RetSqlName("SF1") + " (NOLOCK) SF1 WHERE SF1.D_E_L_E_T_ ='' AND F1_CHVNFE = CKO_CHVDOC ) " + cEol
	cQry += " and not exists (select null from  " + RetSqlName("SDS") + " (NOLOCK) SDS WHERE SDS.D_E_L_E_T_ ='' AND DS_CHAVENF = CKO_CHVDOC ) " + cEol
	cQry += " ORDER BY CKO_EMPPRO , CKO_FILPRO , CKO_CHVDOC"

	dbUseArea(.T.,"TOPCONN",TcGenQry(,,cQry),cAliasExc,.T.,.T.)

	While (cAliasExc)->(!Eof())
		conout("passou")
		DbSelectArea("CKO")
		CKO->(DbSetOrder(1))
		If CKO->(DbSeek(Padr((cAliasExc)->CKO_ARQUIV,nTamCKOARQ)))
			aCkoDados := GetAdvFVal("CKO",{"CKO_CODEDI","CKO'_EMPPRO","CKO_FILPRO",;
				"CKO_CODERR","CKO_MSGERR","CKO_CNPJIM","CKO_XMLRET","CKO_DOC","CKO_SERIE","CKO_NOMFOR"},Padr((cAliasExc)->CKO_ARQUIV,nTamCKOARQ),1)

			// PutGlbVars(cDtVld+E2_FILIAL+E2_PREFIXO+E2_NUM+E2_PARCELA+E2_TIPO+E2_FORNECE+E2_LOJA,cRealTkn)
			cTit := "Erro Ao importar XML "+alltrim(aCkoDados[2]) +"/"+ alltrim(aCkoDados[3])  //CKO_EMPPRO  //CKO_FILPRO
			cTit += " Fornece:"+alltrim(aCkoDados[10])
			cTit += " NF:" + alltrim(aCkoDados[8]) +"/"+alltrim(aCkoDados[9]) //CKO_DOC + CKO_SERIE

			cMsg := alltrim(aCkoDados[5]) +cEol

			Sleep(1000)

			EventInsert(FW_EV_CHANEL_ENVIRONMENT, FW_EV_CATEGORY_MODULES, cEventID,FW_EV_LEVEL_INFO,"",cTit,cMsg,.T.)

			(cAliasExc)->(DbSkip())
		ENDIF
	Enddo

	(cAliasExc)->(DbCloseArea())

	// RPCClearEnv()

Return Nil
