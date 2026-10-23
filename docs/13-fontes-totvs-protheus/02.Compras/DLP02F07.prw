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
01  - Desenvolver caixa de perguntas com base no parambox
    - DA1 - Unica
    - Produto De/Ate
    - ID Calculo
    - Atualiza Tabela de Venda Sim/Nao
02  Desenvolver query para listar os produtos
03  Desenvolver Rotina para chamar o MVC
*/


user function DLP02F07()

    /*/{Protheus.doc} fParam

    Responsavel por carregar as perguntas  de processamento da formação de preco

    /*/

    /*
    aAdd(aPergs, {1, "Produto De",  cProdDe,  "", ".T.", "SB1", ".T.", 80,  .F.})
    aAdd(aPergs, {1, "Produto Até", cProdAt,  "", ".T.", "SB1", ".T.", 80,  .T.})
    Exemplo 4- ParamBox com parâmetros do tipo Combo:
    aAdd(aPergs, {2, "Tipo Importação",               nTipo, {"1=Pré Nota",              "2=Classificação em Documento de Entrada"},     122, ".T.", .F.})
    aAdd(aPergs, {2, "Vincula Pedido de Compra",      nVinc, {"1=Sim (Automaticamente)", "2=Não"},                                       090, ".T.", .F.})
    aAdd(aPergs, {1, "Qtde",  nQuant,  "@E 9,999",     "Positivo()", "", ".T.", 80,  .F.})
    aAdd(aPergs, {1, "Valor", nValor,  "@E 99,999.99", "Positivo()", "", ".T.", 80,  .F.})

Local nVinc    := 1

aAdd(aPergs, {2, "Tipo Importação",               nTipo, {"1=Pré Nota",              "2=Classificação em Documento de Entrada"},     122, ".T.", .F.})
aAdd(aPergs, {2, "Vincula Pedido de Compra",      nVinc, {"1=Sim (Automaticamente)", "2=Não"},                                       090, ".T.", .F.})


    */
    Local aPergs   := {}
    Local aRetPro   := {}
    Local aMvPar   := {}
    Local aRet     := {}
    Local cTabVen  := space(getsx3cache("DA0_CODTAB","X3_TAMANHO" ))
    Local cProdDe  := space(getsx3cache("B1_COD" ,"X3_TAMANHO" ))
    Local cProdAte := space(getsx3cache("B1_COD" ,"X3_TAMANHO" ))
    Local cIDSZ7   := space(getsx3cache("Z7_ID" ,"X3_TAMANHO"  ))
    Local cAtual   := "N"
    Local cVldPrc   := "N"
    Local nMv      := 0
    Local aArea    := getarea()
    Local aTam     := {20,60,60,60,60}
    Local n1 := 0
    Local aLogProc2 := {} // ID |CODIGO PRODUTO | erro

    Private aRetBox     := {}



    if RetCodUsr() == '000000'
        cTabVen := "160"
        cProdDe  := padr("",getsx3cache("B1_COD" ,"X3_TAMANHO" ))
        cProdAte := padr("TERCEIROS",getsx3cache("B1_COD" ,"X3_TAMANHO" ))
        cIDSZ7 := "000002"
    endif

    /*Armazena o conteudo do MV_PARXX*/
    For nMv := 1 To 60
        aAdd( aMvPar, &( "MV_PAR" + StrZero( nMv, 2, 0 ) ) )
    Next nMv

    conout("gabriel")

    //Box de Perguntas
    aAdd(aPergs, {1, "Tabela de Venda"     ,  cTabVen  ,  getsx3cache("DA0_CODTAB","X3_PICTURE" ),     '(ExistCpo("DA0") .AND. U_D02F6TAB('+cTabVen+') )', "DA0", ".T.",aTam[1] ,  .F.})
    aAdd(aPergs, {1, "Produto De"          ,  cProdDe  ,  getsx3cache("B1_COD","X3_PICTURE" ),     'Vazio() .or. ExistCpo("SB1")', "SB1", ".T.", aTam[2],  .F.})
    aAdd(aPergs, {1, "Produto Ate"         ,  cProdAte ,  getsx3cache("B1_COD","X3_PICTURE" ),     'ExistCpo("SB1")', "SB1", ".T.", aTam[3],  .T.})
    aAdd(aPergs, {1, "ID Calculo de"    ,  cIDSZ7   , "",      'ExistCpo("SZ8")', "SZ8", ".T.", aTam[4],  .F.})
    aAdd(aPergs, {1, "ID Calculo Ate"    ,  cIDSZ7   , "",      'ExistCpo("SZ8")', "SZ8", ".T.", aTam[4],  .F.})
    // aAdd(aPergs, {1, "Planilha Calculo"    ,  cIDSZ7   , "",      'ExistCpo("SZ7")', "SZ7SX1", ".T.", aTam[4],  .F.})
    // aAdd(aPergs, {1, "Planilha Calculo"    ,  cIDSZ7   , "",      'ExistCpo("SZ7")', "SZ7SX1", ".T.", aTam[4],  .F.})

    //aAdd(aPergs, {2, "Valida Preco Venda",  cAtual   ,  {"S=Sim","N=Não"},     aTam[5], ".T.", .T.})
    // aAdd(aPergs, {2, "Valida Preco",  cVldPrc   ,  {"S=Sim","N=Não"},     aTam[5], ".T.", .T.})

    aRetBox := ARRAY(LEN(aPergs))

    If ParamBox(aPergs, "Informe os parâmetros",@aRetBox)

        //GUARDA AS OPCOES ESCOLHIDAS
        cTabVen    := MV_PAR01
        cProdDe    := MV_PAR02
        cProdAte   := MV_PAR03
        cIDSZ7De   := MV_PAR04
        cIDSZ7Ate  := MV_PAR05


        For nMv := 1 To Len( aMvPar )
            &( "MV_PAR" + StrZero( nMv, 2, 0 ) ) := aMvPar[ nMv ]
        Next nMv

        FWMsgRun( ,{||  fPrcDA1(cTabVen,cProdDe,cProdAte,cIDSZ7De,cIDSZ7Ate,@aLogProc2)},"Atualizando Tabelas...")



    ELSE

        //    FWAlertError("Mensagem de erro", "Título FWAlertError")
        FWAlertError("Cancelado pelo Usuario", "Formação Preco - Atualização Tabela Venda")
        //       MsgStop("Cancelado", "GABRIEL")

    ENDIF
    //EEcView(cMsg, "Itens Não Processados")

    if len(aLogProc2) > 0
        cMsg := ""
        cEol := chr(10)
        For n1 := 1 to Len(aLogProc2)
            cMsg +=trim( aLogProc2[n1][1])+" | "+trim( aLogProc2[n1][2])+" | "+trim( aLogProc2[n1][3]) + cEol
        Next n1
        EEcView(cMsg, "Itens Não Localizados na Tabela de Vendas")
    endif

    /*Retorna o conteudo do MV_PARXX*/
    For nMv := 1 To Len( aMvPar )
        &( "MV_PAR" + StrZero( nMv, 2, 0 ) ) := aMvPar[ nMv ]
    Next nMv

    RestArea(aArea)
Return
/*/{Protheus.doc} fGetProd
REtorna os Produtos elegiveis se é necessario incluir ou alterar
@author Gabriel
@since 09/12/2021
@param cTabVen,cProdDe,cProdAte,cIDSZ7,cAtual
@return return_var, return_type, return_description
/*/
static Function fPrcDA1(cTabVen,cProdDe,cProdAte,cIDSZ7De,cIDSZ7Ate,aLogProc2)
    Local aRet := {}
    Local cEol := chr(10)

    /*
" + retsqlname("") + " SB1 (NOLOCK) " + cEol
    */

    cSql := " SELECT  Z8_FILIAL,Z8_ID    ,Z8_COD    ,Z8_PVTAB    ,Z8_PVSUGER    ,Z8_CDTABVN, R_E_C_N_O_ RECSZ8 " + cEol
    cSql += "   FROM " + retsqlname("SZ8") + " SZ8 (NOLOCK) " + cEol
    cSql += "       WHERE SZ8.D_E_L_E_T_       = ''  " + cEol
    cSql += "              AND SZ8.Z8_FILIAL   = "+ VALTOSQL(XFILIAL("SZ8"))  + cEol
    cSql += "              AND SZ8.Z8_ID       BETWEEN "+ VALTOSQL( cIDSZ7De) +"  AND "+  VALTOSQL( cIDSZ7Ate)  + cEol
    cSql += "              AND SZ8.Z8_COD      BETWEEN "+ VALTOSQL( cProdDe) +"  AND "+  VALTOSQL( cProdDe)  + cEol
    cSql += "              AND Z8_CDTABVN    =  "+ VALTOSQL( cTabVen) + cEol
    cSql += "              AND SZ8.Z8_SITUA  ='P' "+ cEol
    cSql += "ORDER BY 1,2 "


    If Select('TMPSZ8') <> 0
        TMPSZ8->(dbCloseArea())
    Endif
    CONOUT(cSql)
    TCQuery cSql Alias TMPSZ8 New
    DBSELECTAREA("DA1")
    DBSELECTAREA("SZ8")
    DA1->(dbSetOrder(1)) // DA1_FILIAL, DA1_CODTAB, DA1_CODPRO, DA1_INDLOT, DA1_ITEM, R_E_C_N_O_, D_E_L_E_T_
    While TMPSZ8->(!eof())
        SZ8->(dbGoTo(TMPSZ8->RECSZ8))
        cChave := xfilial("DA1") + TMPSZ8->Z8_CDTABVN + TMPSZ8->Z8_COD

        if    DA1->(DbSeek( cChave))

            RecLock('SZ8',.F.)
            SZ8->Z8_DTAPROV :=  DATE()
            SZ8->Z8_IDAPROV :=  RetCodUsr()
            SZ8->Z8_ULTPV   :=  DA1->DA1_PRCVEN
            SZ8->Z8_SITUA   :=  "A"
            SZ8->Z8_PVTAB   :=  TMPSZ8->Z8_PVSUGER
            //   SZ8->Z8_MARGEM  := 0

            SZ8->(MsUnLock())

            RecLock('DA1',.F.)
            DA1->DA1_PRCVEN := TMPSZ8->Z8_PVSUGER
            DA1->(MsUnLock())

        else

            aadd(aLogProc2,{TMPSZ8->Z8_ID,TMPSZ8->Z8_COD,TMPSZ8->Z8_CDTABVN})

        endif
        TMPSZ8->(dbskip())

    Enddo

    TMPSZ8->(dbCloseArea())
    SZ8->(dbGoToP())
Return
