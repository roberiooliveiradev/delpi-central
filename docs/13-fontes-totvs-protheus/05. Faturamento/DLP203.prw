#include "totvs.ch"
#include "protheus.ch"
#INCLUDE "RWMAKE.CH"
#INCLUDE "TBICONN.CH"
#include 'fileio.ch'
#INCLUDE "TOPCONN.CH"
#INCLUDE "TBICONN.CH"

user function DLP203(xEmp)
	lOCAL aArea := GETAREA()
	Local cCPFCGC := IIF(eMPTY(&(ReadVar())),M->A1_CGC,&(ReadVar()))
	Local cSql := ""
	Local cEol := chr(10) + chr(13)
	Local lFound := .f.
	Local nOpc := 0
	lOCAL _cMens := ""
	Local  Query  := GetNextAlias()
	IF !(ISBLIND())

		cSql +="SELECT TOP 1 A.*  " + cEol
		cSql +="	FROM dbo.SA1"+xEmp+"0 A (nolock) " + cEol
		cSql +="WHERE 	A.D_E_L_E_T_ = '' " + cEol 
		cSql +="AND A1_CGC = "+ValtoSql(cCPFCGC)
		//If MsgYesNo(_cMens,"ATENÇÃO","YESNO")	

		CONOUT(cSql)
		CONOUT("ISBLIND =>"+CVALTOCHAR(ISBLIND()))

		TcQuery cSql New Alias (Query)
		if !(Query)->(Eof()) 

			lFound := .t.

		endif

		if lFound .AND. !eMPTY(cCPFCGC)

			_cMens+="Deseja Importar os Dados do Cliente:" + cEol
			_cMens+="Razão Social: " + (Query)->A1_NOME + cEol
			_cMens+="Nome Reduzido: " + (Query)->A1_NREDUZ + cEol
			_cMens+= alltrim((Query)->A1_MUN) + ' - ' + alltrim((Query)->A1_EST)

			nOpc := AVISO( "DELPI", _cMens,  {"Sim","Não"}, 2 ,"ATENÇÃO")

			If nOpc ==1	
				M->A1_NOME := (Query)->A1_NOME
				M->A1_PESSOA := (Query)->A1_PESSOA
				M->A1_NREDUZ := (Query)->A1_NREDUZ
				M->A1_TIPO := (Query)->A1_TIPO
				M->A1_END := (Query)->A1_END
				M->A1_MUN := (Query)->A1_MUN
				M->A1_EST := (Query)->A1_EST
				M->A1_NATUREZ := (Query)->A1_NATUREZ
				M->A1_BAIRRO := (Query)->A1_BAIRRO
				M->A1_CEP := (Query)->A1_CEP
				M->A1_DDI := (Query)->A1_DDI
				M->A1_DDD := (Query)->A1_DDD
				M->A1_TEL := (Query)->A1_TEL
				M->A1_PAIS := (Query)->A1_PAIS
				M->A1_CONTATO := (Query)->A1_CONTATO
				M->A1_INSCR := (Query)->A1_INSCR
				M->A1_INSCRM := (Query)->A1_INSCRM
				M->A1_RECISS := (Query)->A1_RECISS
				M->A1_EMAIL := (Query)->A1_EMAIL
				M->A1_CODMUN := (Query)->A1_CODMUN
				M->A1_RECINSS := (Query)->A1_RECINSS
				M->A1_RECCOFI := (Query)->A1_RECCOFI
				M->A1_AGREG := (Query)->A1_AGREG
				M->A1_RECPIS := (Query)->A1_RECPIS
				M->A1_COD_MUN := (Query)->A1_COD_MUN
				M->A1_CODPAIS := (Query)->A1_CODPAIS
				M->A1_SIMPLES := (Query)->A1_SIMPLES
				M->A1_CEINSS := (Query)->A1_CEINSS
				M->A1_FRETISS := (Query)->A1_FRETISS
				M->A1_ABATIMP := (Query)->A1_ABATIMP
				M->A1_RECIRRF := (Query)->A1_RECIRRF
				M->A1_CONTRIB := (Query)->A1_CONTRIB
				M->A1_FOMEZER := (Query)->A1_FOMEZER
				M->A1_SIMPNAC := (Query)->A1_SIMPNAC

			Endif

		Endif
	Endif		
RESTAREA(AAREA)
	//	While !(Query)->(Eof()) 
	//
	//		AAdd( aDados, { (Query)->ID,;	
return .T.