

#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"

/*

01 - Consulta para Retornar o Fornecedor
*/


//User Function ZZLF3()
User Function D04P01A()
    DEFAULT nOpc := 1
    Local aArea := GetArea()
    Local cTitulo		:= "Fornecedores"
    Local cQuery		:= "" 								//obrigatorio
    Local cAlias		:= "SD1"							//obrigatorio
    Local cCpoChave	    := "D1_FORNECE" 					//obrigatorio
    Local cTitCampo	    := RetTitle(cCpoChave)			//obrigatorio
    Local cMascara	    := PesqPict(cAlias,cCpoChave)	//obrigatorio
    Local nTamCpo		:= TamSx3(cCpoChave)[1] + TamSx3(cCpoChave)[1]
    Local cRetCpo		:= "M->D3_DLPFOR"					//obrigatorio
    Local nColuna		:= 1
    LOCAL cEol          := CHR(10)
    lOCAL nTotal := 0
    Local cCodigo		:= M->D3_DLPFOR		//pego o conteudo e levo para minha consulta padrão
    Private bRet 		:= .F.

    Private lParam  := .F.


    if nOpc == 1

        cRetCpo		:= "M->D3_DLPFOR "
        cCodigo		:= M->D3_DLPFOR

    endif
    //Monto minha consulta, neste caso quero retornar apenas uma coluna, mas poderia inserir outros campos para compor outras colunas no grid, lembrando que não posso utilizar um alias para o nome do campo, deixar o nome real.
    //Posso fazer qualquer tipo de consulta, usando INNER, GROUPY BY, UNION's etc..., desde que mantenha o nome dos campos no SELECT.



    cQuery :=" SELECT DISTINCT D1_FORNECE,D1_LOJA, A2_NOME  " + cEol
    cQuery +="FROM dbo."+RetSQLName("SD1") +" (NOLOCK) TBL1  " + cEol
    cQuery +="JOIN dbo."+RetSQLName("SA2") + " SA2 (NOLOCK) ON SA2.D_E_L_E_T_ =''   " + cEol
    cQuery +="AND A2_FILIAL ='' AND A2_COD = D1_FORNECE AND D1_LOJA = A2_LOJA  " + cEol
    cQuery +="WHERE TBL1.D_E_L_E_T_ = ''  " + cEol
    cQuery +="AND TBL1.D1_COD = '10080021'  " + cEol
    cQuery +="AND D1_FILIAL ="+VALTOSQL("SD1")  + cEol
    cQuery +="AND D1_EMISSAO >='20240101'  " + cEol
    cQuery +="AND D1_TES NOT IN ('150','040')  "


    If Select("QRYTMP") <> 0
        dbSelectArea("QRYTMP")
        dbCloseArea()
    EndIf


    TCQuery cQuery New Alias "QRYTMP"

    //Contando os registros e voltando ao topo da query
    Count To nTotal

    IF nTotal == 0
        cQuery := "SELECT  TOP 1 SPACE ("+getsx3cache("D1_FORNECE","X3_TAMANHO")+") D1_FORNECE ,SPACE ("+getsx3cache("D1_LOJA","X3_TAMANHO")+")  D1_LOJA " + cEol
        cQuery += " ,SPACE ("+getsx3cache("A2_NOME","X3_TAMANHO")+")  A2_NOME" + cEol
        cQuery += " FROM dbo."+RetSQLName("SD1") + "SD1 WHERE 1=1 "
    ENDIF

    QRYTMP->(DbCloseArea())
    bRet := U_FiltroF3(cTitulo,cQuery,nTamCpo,cAlias,cCodigo,cCpoChave,cTitCampo,cMascara,cRetCpo,nColuna)
    RestArea(aArea)
Return(bRet)



User Function D04P01B()



    xRet := M->D3_DLPFOR
    conout('stop')
reTURN(xRet )
