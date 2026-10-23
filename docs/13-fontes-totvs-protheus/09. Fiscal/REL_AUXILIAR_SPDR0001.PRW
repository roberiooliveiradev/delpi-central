#INCLUDE "PROTHEUS.CH"
#include "topconn.ch"

/**
* Função			: SPDR0001 
* Autor				: FABIO S. ASSARICE
* Data				: 12/05/2010
* Descrição			: Relatório contendo as informações do livro fiscal para auxiliar na conferência do SPED Pis/Cofins
*
* Parâmetros		: n/a
*
* Retorno			: n/a
*                        
* Observações		: 
*/

User Function SPDR0001()
Local  	oReport          
Local 	oSection1                       
Local  	cTitulo     := 	""
Local  	cDescricao 	:=	""  
Local 	nTamData 	:= 	IIF(__SetCentury(),10,8)  
Local	cPerg		:=	'SPDR0001'

oReport := ReportDef()

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Criacao do componente de impressao                                      ³
//³                                                                        ³
//³TReport():New                                                           ³
//³ExpC1 : Nome do relatorio                                               ³
//³ExpC2 : Titulo                                                          ³
//³ExpC3 : Pergunte                                                        ³
//³ExpB4 : Bloco de codigo que sera executado na confirmacao da impressao  ³
//³ExpC5 : Descricao                                                       ³
//³                                                                        ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
cTitulo := "Relatório Auxiliar SPED Pis/Cofins"
cDescricao := "Relatório contendo as informações do livro fiscal para auxiliar na conferência do SPED Pis/Cofins, conforme parâmetros do usuário."    
oReport := TReport():New(cPerg,cTitulo,cPerg, {|oReport| ReportPrint(oReport,oSection1)},cDescricao)	
oReport:SetLandscape() 
oReport:SetTotalInLine(.F.)

CriaSx1(cPerg)
Pergunte(oReport:uParam,.F.)

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Criacao da secao utilizada pelo relatorio                               ³
//³                                                                        ³
//³TRSection():New                                                         ³
//³ExpO1 : Objeto TReport que a secao pertence                             ³
//³ExpC2 : Descricao da seçao                                              ³
//³ExpA3 : Array com as tabelas utilizadas pela secao. A primeira tabela   ³
//³        sera considerada como principal para a seção.                   ³
//³ExpA4 : Array com as Ordens do relatório                                ³
//³ExpL5 : Carrega campos do SX3 como celulas                              ³
//³        Default : False                                                 ³
//³ExpL6 : Carrega ordens do Sindex                                        ³
//³        Default : False                                                 ³
//³                                                                        ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

oSection1 := TRSection():New(oReport,/*Descricao da Sessão*/,{"cAlias"},/*{Array com as ordens do relatório}*/,/*Campos do SX3*/,/*Campos do SIX*/)	

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Criacao da celulas da secao do relatorio                                ³
//³                                                                        ³
//³TRCell():New                                                            ³
//³ExpO1 : Objeto TSection que a secao pertence                            ³
//³ExpC2 : Nome da celula do relatório. O SX3 será consultado              ³
//³ExpC3 : Nome da tabela de referencia da celula                          ³
//³ExpC4 : Titulo da celula                                                ³
//³        Default : X3Titulo()                                            ³
//³ExpC5 : Picture                                                         ³
//³        Default : X3_PICTURE                                            ³
//³ExpC6 : Tamanho                                                         ³
//³        Default : X3_TAMANHO                                            ³
//³ExpL7 : Informe se o tamanho esta em pixel                              ³
//³        Default : False                                                 ³
//³ExpB8 : Bloco de código para impressao.                                 ³
//³        Default : ExpC2                                                 ³
//³                                                                        ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ

TRCell():New(oSection1,"cTpMov"			,"cAlias","Tipo Mov."	   			,/*Picture*/,17,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"dDtEntr"		,"cAlias","Dt. Entrada"   		   	,/*Picture*/,12,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"cEspecie"		,"cAlias","Especie"				   	,/*Picture*/,10,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"cProduto"		,"cAlias","Produto"					,/*Picture*/,15,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"cNF"			,"cAlias","Numero NF"				,/*Picture*/,20,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"cClieFor"		,"cAlias","Cliente/Forn."			,/*Picture*/,20,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"cCFOP" 			,"cAlias","CFOP"					,/*Picture*/,07,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"nValCont"		,"cAlias","Val. Contabil" 			,/*Picture*/,20,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"cCSTPis"		,"cAlias","CST Pis"					,/*Picture*/,07,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"nBasPis"		,"cAlias","Valor Base PIS" 			,/*Picture*/,20,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"nValPis"		,"cAlias","Valor Pis" 				,/*Picture*/,20,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"cCSTCof" 		,"cAlias","CST Cofins"				,/*Picture*/,07,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"nBasCof"		,"cAlias","Valor Base COFINS" 		,/*Picture*/,20,.F.,/*{|| code-block de impressao }*/)
TRCell():New(oSection1,"nValCof"		,"cAlias","Valor Cofins" 			,/*Picture*/,20,.F.,/*{|| code-block de impressao }*/)

oSection1 :SetTotalText("T O T A I S : ")

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³ Alinhamento a direita as colunas de valor                              ³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
//oSection1:Cell("nValContab"):SetHeaderAlign("RIGHT")
//oSection1:Cell("cValICMS"):SetHeaderAlign("RIGHT")
//oSection1:Cell("cValIPI"):SetHeaderAlign("RIGHT")
//oSection1:Cell("cBasPIS"):SetHeaderAlign("RIGHT")
//oSection1:Cell("cBasCOFINS"):SetHeaderAlign("RIGHT")

oReport:PrintDialog()
Return ()
         
/**
* Função			: ReportPrint 
* Autor				: FABIO S. ASSARICE
* Data				: 11/11/2010
* Descrição			: Coleta de dados e impressão do relatório
*					  
*
* Parâmetros		: oReport 	: Objeto do relatório
*					: oSection1 : Objeto da Sessão do relatório
*
* Retorno			: n/a
*                        
* Observações		: n/a
*/

Static Function ReportPrint(oReport,oSection1)
Local	cAlias 		:= 	GetNextAlias()
Local	nTotRegs	:=	0             
Local	aTotPisEnt	:= 	{}
Local	aTotCofEnt	:= 	{}
Local	aTotPisSai	:=	{}
Local	aTotCofSai	:=	{}
Local	aTotCFOP	:=	{}
Local	nPos		:=	0
Local	cCSTAnt		:=	''
Local	cCFOPAnt	:=	''
                                      

oReport:Section(1):BeginQuery()
	BeginSql Alias cAlias    
	
	SELECT 
		FT_FILIAL,FT_TIPOMOV,FT_ENTRADA,FT_ESPECIE,FT_PRODUTO,FT_NFISCAL,FT_SERIE,FT_CLIEFOR,FT_LOJA, 
		FT_CFOP,FT_VALCONT,FT_VALCOF,FT_VALPIS,FT_BASECOF,FT_BASEPIS,FT_CSTPIS,FT_CSTCOF,FT_OBSERV
	FROM 
		%Table:SFT% SFT
	WHERE 
		FT_FILIAL = %xFilial:SFT%
		AND SFT.FT_DTCANC = '        '
		AND ( FT_ENTRADA >= %Exp:DTOS(MV_PAR01)% 
		AND FT_ENTRADA <= %Exp:DTOS(MV_PAR02)% )
		AND SFT.%notdel%
	ORDER BY
		FT_CSTPIS,FT_CSTCOF,FT_TIPOMOV,FT_ENTRADA,FT_ESPECIE
	EndSql                    
oReport:section(1):EndQuery()  

TcSetField(cAlias,'FT_ENTRADA',"D", TamSx3("FT_ENTRADA")[1], TamSx3("FT_ENTRADA")[2] )

TcSetField(cAlias,'FT_VALCONT',"N", 14,02)
TcSetField(cAlias,'FT_VALPIS',"N", 14,02)
TcSetField(cAlias,'FT_VALCOF',"N", 14,02)
TcSetField(cAlias,'FT_BASECOF',"N", 14,02)
TcSetField(cAlias,'FT_BASEPIS',"N", 14,02)

nTotRegs += (cAlias)->(LastRec())

	oReport:SetMeter(nTotRegs)
	
	//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
	//³Inicio da impressao do fluxo do relatório                               ³
	//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
	oReport:Section(1):Init() 
	(cAlias)->(dbGoTop())
	While !oReport:Cancel() .And. !((cAlias)->(Eof()))        
		oSection1:Cell("cTpMov"			):SetValue(IIf((cAlias)->FT_TIPOMOV=='E','Entrada','Saída'))
		oSection1:Cell("dDtEntr"		):SetValue((cAlias)->FT_ENTRADA)
		oSection1:Cell("cEspecie"		):SetValue((cAlias)->FT_ESPECIE)
		oSection1:Cell("cProduto"		):SetValue((cAlias)->FT_PRODUTO)
		oSection1:Cell("cNF"			):SetValue((cAlias)->FT_SERIE  +' / '+(cAlias)->FT_NFISCAL)
		oSection1:Cell("cClieFor"		):SetValue((cAlias)->FT_CLIEFOR+' / '+(cAlias)->FT_LOJA)
		oSection1:Cell("cCFOP" 			):SetValue((cAlias)->FT_CFOP)
		oSection1:Cell("nValCont"		):SetValue(Transform((cAlias)->FT_VALCONT,"@E 999,999,999.99"))
		oSection1:Cell("cCSTPis"		):SetValue((cAlias)->FT_CSTPIS)
		oSection1:Cell("nBasPis"		):SetValue(Transform((cAlias)->FT_BASEPIS,"@E 999,999,999.99"))
		oSection1:Cell("nValPis"		):SetValue(Transform((cAlias)->FT_VALPIS,"@E 999,999,999.99"))
		oSection1:Cell("cCSTCof" 		):SetValue((cAlias)->FT_CSTCOF)
		oSection1:Cell("nBasCof"		):SetValue(Transform((cAlias)->FT_BASECOF,"@E 999,999,999.99"))
		oSection1:Cell("nValCof"		):SetValue(Transform((cAlias)->FT_VALCOF,"@E 999,999,999.99")) 
		If (cAlias)->FT_TIPOMOV=='E'
			&& Totais do PIS
			nPos := aScan(aTotPisEnt,{|x| x[1]== (cAlias)->FT_CSTPIS}) 
			If nPos > 0
				aTotPisEnt[nPos][2] += (cAlias)->FT_VALCONT
				aTotPisEnt[nPos][3] += (cAlias)->FT_BASEPIS
				aTotPisEnt[nPos][4] += (cAlias)->FT_VALPIS
			Else  
				aAdd(aTotPisEnt,{(cAlias)->FT_CSTPIS,(cAlias)->FT_VALCONT,(cAlias)->FT_BASEPIS,(cAlias)->FT_VALPIS})
			EndIf           
			&& Totais do Cofins
			nPos := aScan(aTotCofEnt,{|x| x[1]== (cAlias)->FT_CSTCOF}) 
			If nPos > 0
				aTotCofEnt[nPos][2] += (cAlias)->FT_VALCONT
				aTotCofEnt[nPos][3] += (cAlias)->FT_BASECOF
				aTotCofEnt[nPos][4] += (cAlias)->FT_VALCOF
			Else  
				aAdd(aTotCofEnt,{(cAlias)->FT_CSTCOF,(cAlias)->FT_VALCONT,(cAlias)->FT_BASECOF,(cAlias)->FT_VALCOF})
			EndIf		
		Else
			&& Totais do PIS
			nPos := aScan(aTotPisSai,{|x| x[1]== (cAlias)->FT_CSTPIS}) 
			If nPos > 0
				aTotPisSai[nPos][2] += (cAlias)->FT_VALCONT
				aTotPisSai[nPos][3] += (cAlias)->FT_BASEPIS
				aTotPisSai[nPos][4] += (cAlias)->FT_VALPIS
			Else  
				aAdd(aTotPisSai,{(cAlias)->FT_CSTPIS,(cAlias)->FT_VALCONT,(cAlias)->FT_BASEPIS,(cAlias)->FT_VALPIS})
			EndIf           
			&& Totais do Cofins
			nPos := aScan(aTotCofSai,{|x| x[1]== (cAlias)->FT_CSTCOF}) 
			If nPos > 0
				aTotCofSai[nPos][2] += (cAlias)->FT_VALCONT
				aTotCofSai[nPos][3] += (cAlias)->FT_BASECOF
				aTotCofSai[nPos][4] += (cAlias)->FT_VALCOF
			Else  
				aAdd(aTotCofSai,{(cAlias)->FT_CSTCOF,(cAlias)->FT_VALCONT,(cAlias)->FT_BASECOF,(cAlias)->FT_VALCOF})
			EndIf
		EndIf

		&& Totais por CFOP
		nPos := aScan(aTotCFOP,{|x| x[1]== (cAlias)->FT_CFOP}) 
		If nPos > 0
			aTotCFOP[nPos][2] += (cAlias)->FT_VALCONT
			aTotCFOP[nPos][3] += (cAlias)->FT_BASECOF
			aTotCFOP[nPos][4] += (cAlias)->FT_VALCOF      
			aTotCFOP[nPos][5] += (cAlias)->FT_BASEPIS
			aTotCFOP[nPos][6] += (cAlias)->FT_VALPIS			
		Else  
			aAdd(aTotCFOP,{(cAlias)->FT_CFOP,(cAlias)->FT_VALCONT,(cAlias)->FT_BASECOF,(cAlias)->FT_VALCOF,(cAlias)->FT_BASEPIS,(cAlias)->FT_VALPIS})
		EndIf		
		

		oSection1:PrintLine()
		oReport:IncMeter()
		(cAlias)->(dbSkip())
		If oReport:Cancel()
			Exit
		EndIf   
	EndDo     
                 
	oReport:ThinLine()

	oReport:PrintText("T O T A I S : (Entradas) ",oReport:Row())
	&& Limpar celulas
	oSection1:Cell("cTpMov"			):SetValue('')
	oSection1:Cell("dDtEntr"		):SetValue('')
	oSection1:Cell("cEspecie"		):SetValue('')
	oSection1:Cell("cProduto"		):SetValue('')
	oSection1:Cell("cNF"			):SetValue('')
	oSection1:Cell("cClieFor"		):SetValue('')
	oSection1:Cell("cCFOP" 			):SetValue('')
	oSection1:Cell("nValCont"		):SetValue('')
	oSection1:Cell("cCSTPis"		):SetValue('')
	oSection1:Cell("nBasPis"		):SetValue('')
	oSection1:Cell("nValPis"		):SetValue('')
	oSection1:Cell("cCSTCof" 		):SetValue('')
	oSection1:Cell("nBasCof"		):SetValue('')
	oSection1:Cell("nValCof"		):SetValue('')	
	&& Totais das Entradas
	cCSTAnt:= ''
	oReport:PrintText('PIS',oReport:Row(),oSection1:Cell("cClieFor"):ColPos()-5)              
	For nPos:=1 to Len(aTotPisEnt)
		If aTotPisEnt[nPos][1] <> cCSTAnt
			oSection1:Cell("cCSTPis"		):SetValue(aTotPisEnt[nPos][1])
			cCSTAnt := aTotPisEnt[nPos][1]
		EndIf   
		oSection1:Cell("nValCont"		):SetValue(Transform(aTotPisEnt[nPos][2],"@E 999,999,999.99"))
		oSection1:Cell("nBasPis"		):SetValue(Transform(aTotPisEnt[nPos][3],"@E 999,999,999.99"))
		oSection1:Cell("nValPis"		):SetValue(Transform(aTotPisEnt[nPos][4],"@E 999,999,999.99"))
		oSection1:PrintLine()
	Next nPos
    If Len(aTotPisEnt)!=0
    	oReport:SkipLine()
    EndIf	
	
	&& Limpar celulas
	oSection1:Cell("cTpMov"			):SetValue('')
	oSection1:Cell("dDtEntr"		):SetValue('')
	oSection1:Cell("cEspecie"		):SetValue('')
	oSection1:Cell("cProduto"		):SetValue('')
	oSection1:Cell("cNF"			):SetValue('')
	oSection1:Cell("cClieFor"		):SetValue('')
	oSection1:Cell("cCFOP" 			):SetValue('')
	oSection1:Cell("nValCont"		):SetValue('')
	oSection1:Cell("cCSTPis"		):SetValue('')
	oSection1:Cell("nBasPis"		):SetValue('')
	oSection1:Cell("nValPis"		):SetValue('')
	oSection1:Cell("cCSTCof" 		):SetValue('')
	oSection1:Cell("nBasCof"		):SetValue('')
	oSection1:Cell("nValCof"		):SetValue('')	
	
	cCSTAnt:= ''
	oReport:PrintText('COFINS',oReport:Row(),oSection1:Cell("cClieFor"):ColPos()-5)              
	For nPos:=1 to Len(aTotCofEnt)
		If aTotCofEnt[nPos][1] <> cCSTAnt                                                             
			oSection1:Cell("cCSTCof"		):SetValue(aTotCofEnt[nPos][1])
			cCSTAnt := aTotCofEnt[nPos][1]
		EndIf                 
		oSection1:Cell("nValCont"		):SetValue(Transform(aTotCofEnt[nPos][2],"@E 999,999,999.99"))
		oSection1:Cell("nBasCof"		):SetValue(Transform(aTotCofEnt[nPos][3],"@E 999,999,999.99"))
		oSection1:Cell("nValCof"		):SetValue(Transform(aTotCofEnt[nPos][4],"@E 999,999,999.99"))
		oSection1:PrintLine()		
	Next nPos         
    If Len(aTotCofEnt)!=0
    	oReport:SkipLine()
    EndIf

	oReport:ThinLine()

	oReport:PrintText("T O T A I S : (Saidas) ",oReport:Row())
	&& Limpar celulas
	oSection1:Cell("cTpMov"			):SetValue('')
	oSection1:Cell("dDtEntr"		):SetValue('')
	oSection1:Cell("cEspecie"		):SetValue('')
	oSection1:Cell("cProduto"		):SetValue('')
	oSection1:Cell("cNF"			):SetValue('')
	oSection1:Cell("cClieFor"		):SetValue('')
	oSection1:Cell("cCFOP" 			):SetValue('')
	oSection1:Cell("nValCont"		):SetValue('')
	oSection1:Cell("cCSTPis"		):SetValue('')
	oSection1:Cell("nBasPis"		):SetValue('')
	oSection1:Cell("nValPis"		):SetValue('')
	oSection1:Cell("cCSTCof" 		):SetValue('')
	oSection1:Cell("nBasCof"		):SetValue('')
	oSection1:Cell("nValCof"		):SetValue('')	
	&& Totais das Saidas
	cCSTAnt:= ''
	oReport:PrintText('PIS',oReport:Row(),oSection1:Cell("cClieFor"):ColPos()-5)              
	For nPos:=1 to Len(aTotPisSai)
		If aTotPisSai[nPos][1] <> cCSTAnt
			oSection1:Cell("cCSTPis"		):SetValue(aTotPisSai[nPos][1])
			cCSTAnt := aTotPisSai[nPos][1]
		EndIf   
		oSection1:Cell("nValCont"		):SetValue(Transform(aTotPisSai[nPos][2],"@E 999,999,999.99"))
		oSection1:Cell("nBasPis"		):SetValue(Transform(aTotPisSai[nPos][3],"@E 999,999,999.99"))
		oSection1:Cell("nValPis"		):SetValue(Transform(aTotPisSai[nPos][4],"@E 999,999,999.99"))
		oSection1:PrintLine()
	Next nPos
    If Len(aTotPisSai)!=0
    	oReport:SkipLine()
    EndIf
    	
	&& Limpar celulas
	oSection1:Cell("cTpMov"			):SetValue('')
	oSection1:Cell("dDtEntr"		):SetValue('')
	oSection1:Cell("cEspecie"		):SetValue('')
	oSection1:Cell("cProduto"		):SetValue('')
	oSection1:Cell("cNF"			):SetValue('')
	oSection1:Cell("cClieFor"		):SetValue('')
	oSection1:Cell("cCFOP" 			):SetValue('')
	oSection1:Cell("nValCont"		):SetValue('')
	oSection1:Cell("cCSTPis"		):SetValue('')
	oSection1:Cell("nBasPis"		):SetValue('')
	oSection1:Cell("nValPis"		):SetValue('')
	oSection1:Cell("cCSTCof" 		):SetValue('')
	oSection1:Cell("nBasCof"		):SetValue('')
	oSection1:Cell("nValCof"		):SetValue('')	
	
	cCSTAnt:= ''
	oReport:PrintText('COFINS',oReport:Row(),oSection1:Cell("cClieFor"):ColPos()-5)              
	For nPos:=1 to Len(aTotCofSai)
		If aTotCofSai[nPos][1] <> cCSTAnt                                                             
			oSection1:Cell("cCSTCof"		):SetValue(aTotCofSai[nPos][1])
			cCSTAnt := aTotCofSai[nPos][1]
		EndIf                 
		oSection1:Cell("nValCont"		):SetValue(Transform(aTotCofSai[nPos][2],"@E 999,999,999.99"))
		oSection1:Cell("nBasCof"		):SetValue(Transform(aTotCofSai[nPos][3],"@E 999,999,999.99"))
		oSection1:Cell("nValCof"		):SetValue(Transform(aTotCofSai[nPos][4],"@E 999,999,999.99"))
		oSection1:PrintLine()		           
	Next nPos         
    If Len(aTotCofSai)!=0
    	oReport:SkipLine()
    EndIf
    
	oReport:SkipLine()
	oReport:SkipLine()
	oReport:PrintText("T O T A I S : (por CFOP) ",oReport:Row())
	&& Ordenando por codigo
	aTotCFOP := aSort(aTotCFOP, , , {|x,y|x[1] < y[1]})	
	&& Limpar celulas
	oSection1:Cell("cTpMov"			):SetValue('')
	oSection1:Cell("dDtEntr"		):SetValue('')
	oSection1:Cell("cEspecie"		):SetValue('')
	oSection1:Cell("cProduto"		):SetValue('')
	oSection1:Cell("cNF"			):SetValue('')
	oSection1:Cell("cClieFor"		):SetValue('')
	oSection1:Cell("cCFOP" 			):SetValue('')
	oSection1:Cell("nValCont"		):SetValue('')
	oSection1:Cell("cCSTPis"		):SetValue('')
	oSection1:Cell("nBasPis"		):SetValue('')
	oSection1:Cell("nValPis"		):SetValue('')
	oSection1:Cell("cCSTCof" 		):SetValue('')
	oSection1:Cell("nBasCof"		):SetValue('')
	oSection1:Cell("nValCof"		):SetValue('')	
	&& Totais das Entradas
	cCFOPAnt:= ''
	For nPos:=1 to Len(aTotCFOP)
		If aTotCFOP[nPos][1] <> cCFOPAnt
			oSection1:Cell("cCFOP"		):SetValue(aTotCFOP[nPos][1])
			cCFOPAnt := aTotCFOP[nPos][1]
		EndIf   
		oSection1:Cell("nValCont"		):SetValue(Transform(aTotCFOP[nPos][2],"@E 999,999,999.99"))
		oSection1:Cell("nBasCof"		):SetValue(Transform(aTotCFOP[nPos][3],"@E 999,999,999.99"))
		oSection1:Cell("nValCof"		):SetValue(Transform(aTotCFOP[nPos][4],"@E 999,999,999.99"))				
		oSection1:Cell("nBasPis"		):SetValue(Transform(aTotCFOP[nPos][5],"@E 999,999,999.99"))
		oSection1:Cell("nValPis"		):SetValue(Transform(aTotCFOP[nPos][6],"@E 999,999,999.99"))
		oSection1:PrintLine()
	Next nPos
    If Len(aTotCFOP)==0
    	oReport:SkipLine()
    EndIf	
    
	oReport:Section(1):Finish() 	
	oReport:ThinLine()                               
	oReport:EndPage(.T.) 
	(cAlias)->(dbCloseArea())
Return()
                     

/*/
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³CriaSX1   º Autor ³ FABIO SPESSOTTO    º Data ³  08/11/10   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDescricao ³Objetivo desta funcao e verificar se existe o grupo de      º±±
±±º          ³perguntas, se nao existir a funcao ira cria-lo.             º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³cPerg -> Nome com  grupo de perguntas em questão.           º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß/*/
Static Function CriaSx1(cPerg)

Local aRegs
Local aHelp			:= Array(2,1)
Local aRegs 		:= {}
Local nI 			:= 0
Local nJ 			:= 0                    
Local nH			:= 0

dbSelectArea("SX1")
dbSetOrder(1)
cPerg := PADR(cPerg,Len(SX1->X1_GRUPO))

Aadd(aRegs,{cPerg,"01","Data de?"	 		 ,"","","mv_ch1","D",08,0,0,"G","NaoVazio()"                ,"MV_PAR01",""       ,"" ,"" ,"","",""           ,"" ,"" ,"","","","","","","","","","","","","","","","","","","",""})
Aadd(aRegs,{cPerg,"02","Data até?"  		 ,"","","mv_ch2","D",08,0,0,"G","NaoVazio()"                ,"MV_PAR02",""       ,"" ,"" ,"","",""           ,"" ,"" ,"","","","","","","","","","","","","","","","","","","",""})

For nI:=1 to Len(aRegs)
	If !dbSeek(cPerg+aRegs[nI,2])
		RecLock("SX1",.T.)
		For nJ:=1 to FCount()
			If nJ <= Len(aRegs[nI])
				FieldPut(nJ,aRegs[nI,nJ])
			Endif
		Next
		MsUnlock()
	Endif
Next

//ÚÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄ¿
//³Monta array com o help dos campos dos parametros.³
//ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÄÙ
aAdd(aHelp[01],OemToAnsi("Data de Entrada, Inicial?"))
aAdd(aHelp[02],OemToAnsi("Data de Entrada, Final?"))
For nH:=1 to Len(aHelp)
	PutSX1Help("P."+AllTrim(cPerg)+StrZero(nH,2)+".",aHelp[nH],aHelp[nH],aHelp[nH])
Next nH

Return Nil