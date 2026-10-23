#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE "FILEIO.CH"
#INCLUDE 'TOPCONN.CH'
#INCLUDE "TBICONN.CH"


USER Function DLP05R01()
    Local x := 0
    Private aDados := {}
    Private aPar := {}
    Private aFils
    Private aProdMOD := {} // Ascan(aHeader,{|x| AllTrim(x[2]) == "N0_CHAVE" })

    Private cEol := chr(10)
    Private cHT := chr(9)
    Private aPars := {}
    Private aProd
    Private aEstExc
    Private aColsExc :={}
    Private NESTRU := 1
    Private oExcelApp := Nil
    Private cPath		:= AllTrim(GetTempPath())
    Private cDirDocs	:= MsDocPath()
    Private cArquivo	:= CriaTrab(,.F.)+".xml"
    Private oExcel	:= FWMSEXCEL():New()
    Private nTCUnit := 0
    Private nTCTot := 0
    Private nThrs := 0


    If !ApOleClient('MsExcel')
        ApMsgAlert('MsExcel nao instalado')
        Return
    EndIf

    //Definiao do Padrao do Excel
    // TSC 10/10/2018: Inicio: Diego Kerstner: Formatar as linhas
    oExcel:SetFrGeneralColor("#000000") // Cor das Letras no Documento
    oExcel:SetBgGeneralColor("#FFFFFF") // Cor de Fundo no Documento
    oExcel:SetFont("CALIBRI") 		// Fonte no Documento
    oExcel:SetFontSize(11)				// Tamanho da Fonte no Documento

    oExcel:SetHeaderBold(.T.) // Define Negrito para Cabealho
    oExcel:SetLineBold(.t.)
    If	!Pergunte("DLP05R01",.T.)
        Return
    EndIf
    if MV_PAR11 == 1
        cEstoque := "S"
    elseif MV_PAR11 == 2
        cEstoque := "N"
    else
        cEstoque := "A"
    endif
    if MV_PAR12 == 1
        cDupli := "S"
    elseif MV_PAR12 == 2
        cDupli := "N"
    else
        cDupli := "A"
    endif
    aadd(aPar,MV_PAR01)
    aadd(aPar,MV_PAR02)
    aadd(aPar,MV_PAR03)
    aadd(aPar,MV_PAR04)
    aadd(aPar,MV_PAR05)
    aadd(aPar,MV_PAR06)
    aadd(aPar,MV_PAR07) //cliente de
    aadd(aPar,MV_PAR09) // loja de
    aadd(aPar,MV_PAR08) // cliente ate
    aadd(aPar,MV_PAR10) // loja ate

    aadd(aPar,cEstoque)
    aadd(aPar,cDupli)
    aadd(aPar,iif(MV_PAR13==1,"S","N"))


    Processa({|lEnd| FiltraDados()})  // Chamada com regua
    Processa({|lEnd| GeraDados()})  // Chamada com regua


rETURN


Static Function GeraDados()

    Local nPos  := 0
    Local aCols := {{'Filial',1,1,.F.},;
        {'Cliente',1,1,.F.},;
        {'Nome',1,1,.F.},;
        {'Data Inicial',1,4,.F.},;
        {'Data Final',1,4,.F.},;
        {'Total Notas',3,2,.T.},  /*06*/;
        {'Total Itens',3,2,.T.},  /*07*/;
        {'Quant.Vendida',3,2,.T.},/*08*/;
        {'Vlr Devolucao',3,2,.T.},;
        {'Vlr Venda',3,2,.T.},;
        {'Valor Total R$',3,3,.T.},;
        {'U.M.',1,1,.F.}}

    Local cArquivo	:= CriaTrab(,.F.)+".xml"
    Local cDirDocs	:= MsDocPath()
    Local oExcelApp	:= Nil
    Local cPath		:= AllTrim(GetTempPath())
    Local oExcel	:= FWMSEXCEL():New()

    If !ApOleClient('MsExcel')
        ApMsgAlert('MsExcel nao instalado')
        Return
    EndIf

    oExcel:AddworkSheet("Resumo de Vendas")
    oExcel:AddTable("Resumo de Vendas","Resumo de Vendas")

    //cWorkSheet	   ,cTable		        ,cColumm	,nAlign	,nFormat	,lTotal
    For x:=1 To Len(aCols)
        oExcel:AddColumn("Resumo de Vendas","Resumo de Vendas"	,aCols[x,1], aCols[x,2], aCols[x,3], aCols[x,4]	)
    Next

    For	x:=1 To Len(aDados)
        //        AADD(aDados,{;
        //            TRB->FILIAL  /*01*/   ,alltrim(TRB->CLIENTE)+"|"+alltriM(TRB->LOJA) /*02*/, cNomCli  /*03*/ ,TRB->UM /*04*/,;
        //            TRB->QTDNF    /*05*/,TRB->QTDPRDVEN  /*06*/, TRB->D2_QUANT   /*07*/,TRB->D2_TOTAL  /*08*/, TRB->LIQUIVENDA /*09*/,;
        //            TRB->QTDNFDV /*10*/ ,TRB->QTDPRDDEV /*11*/ , TRB->D1_QUANT   /*12*/,TRB->D1_TOTAL  /*13*/ ,TRB->LIQDEV /*14*/})

        //nDev   := -1 * iif(aPar[11] == "S",aDados[x,14],aDados[x,13])
        //nVend  := iif(aPar[12] == "S",aDados[x,09],aDados[x,08])
        nDev   := -1 * iif(aPar[13] == "S",aDados[x,14],aDados[x,13])
        nVend  := iif(aPar[13] == "S",aDados[x,09],aDados[x,08])

        nTotal := nVend + nDev
        oExcel:AddRow("Resumo de Vendas","Resumo de Vendas", {aDados[x,1], aDados[x,2], aDados[x,3],;
            aPar[05],   aPar[06],;
            aDados[x,5],  aDados[x,6], aDados[x,7], ;
            nDev  ,nVend,nTotal,aDados[x,4]})

    Next x

    If !Empty(oExcel:aWorkSheet)
        oExcel:Activate()
        oExcel:GetXMLFile(cDirDocs+"\"+cArquivo)

        CpyS2T(cDirDocs+"\"+cArquivo,cPath)

        oExcelApp := MsExcel():New()
        oExcelApp:WorkBooks:Open(cPath+cArquivo) // Abre uma planilha
        oExcelApp:SetVisible(.T.)
        oExcelApp:Destroy()
    Else
        ApMgAlert("Não há valores para exportação.")
    EndIf

Return


sTATIC FUNCTION FiltraDados()

    lOCAL
    If (Select("TRB") <> 0)

        dbSelectArea("TRB")
        dbCloseArea()

    Endif
    cSql := "EXEC STP_DELPI_FATURAMENTO_"+cempant+" "
    cSql +=  valtosql(aPar[01]) +" , " //@FILIALDE
    cSql +=  valtosql(aPar[02]) +" , " //@FILIALATE
    cSql +=  valtosql(aPar[03]) +" , " //@PRODUTODE
    cSql +=  valtosql(aPar[04]) +" , " //@PRODUTOATE
    cSql +=  valtosql(aPar[05]) +" , " //@EMISSAODE
    cSql +=  valtosql(aPar[06]) +" , " //@EMISSAOATE
    cSql +=  valtosql(aPar[07]) +" , " //@CLIENTEDE
    cSql +=  valtosql(aPar[08]) +" , " //@CLIENTEATE
    cSql +=  valtosql(aPar[09]) +" , " //@LOJADE
    cSql +=  valtosql(aPar[10]) +" , " //@LOJAATE
    cSql +=  valtosql(aPar[11]) +" , " //@ESTOQUE
    cSql +=  valtosql(aPar[12]) //@DUPLICATA
    // valtosql(aModPar[1]) +","+;



    conout(cSql)

    TCQuery cSql NEW ALIAS "TRB"

    while TRB->(!Eof())
        /*FILIAL	CLIENTE	LOJA	UM	QTDNF	D2_QUANT	D2_VALIMP5	D2_VALIMP6
        D2_VALICM	D2_TOTAL	LIQUIVENDA	QTDNFDV	D1_QUANT	D1_VALIMP5	D1_VALIMP6	D1_VALICM
        D1_TOTAL	LIQDEV
        */

        cNomCli := alltrim(posicione("SA1",1,XFILIAL("SA1")+TRB->CLIENTE+TRB->LOJA,"A1_NOME"))
        AADD(aDados,{;
            TRB->FILIAL  /*01*/   ,alltrim(TRB->CLIENTE)+"|"+alltriM(TRB->LOJA) /*02*/, cNomCli  /*03*/ ,TRB->UM /*04*/,;
            TRB->QTDNF    /*05*/,TRB->QTDPRDVEN  /*06*/, TRB->D2_QUANT   /*07*/,TRB->D2_TOTAL  /*08*/, TRB->LIQUIVENDA /*09*/,;
            TRB->QTDNFDV /*10*/ ,TRB->QTDPRDDEV /*11*/ , TRB->D1_QUANT   /*12*/,TRB->D1_TOTAL  /*13*/ ,TRB->LIQDEV /*14*/})

        /* AADD(aDados,{;
            TRB->FILIAL     ,alltrim(TRB->CLIENTE)+"|"+alltriM(TRB->LOJA), cNomCli   ,TRB->UM         ,TRB->QTDNF ,TRB->QTDPRDVEN ,;
            TRB->D2_QUANT   ,TRB->D2_VALIMP5 ,TRB->D2_VALIMP6 ,TRB->D2_VALICM  ,TRB->D2_TOTAL ,;
            TRB->LIQUIVENDA ,TRB->QTDNFDV  ,TRB->QTDPRDDEV  ,TRB->D1_QUANT   ,TRB->D1_VALIMP5 ,TRB->D1_VALIMP6 ,;
                TRB->D1_VALICM  ,TRB->D1_TOTAL   ,TRB->LIQDEV })*/

        TRB->( DbSkip())

    EndDo

    dbCloseArea()
Return
