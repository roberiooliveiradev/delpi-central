#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"
//-------------------------------------------------------------------
/*/{Protheus.doc} DLP09F04
ROtina Automatica Valor Declaratorio
@author  author
@since   date
@version version
/*/
//-------------------------------------------------------------------

USER FUNCTION DLP09F04(cCodProd)
    /*10540159
    30193695       */
    DEFAULT cCodProd := PADR("30193695",GETSX3CACHE("B1_COD","X3_TAMANHO"))
    Local cSql := fGetQry()
    lOCAL nOper := 3 // INCLUSAO
    /*F3K_GRCLAN	F3K_GRPLAN	F3K_GRFLAN
   CABEÇALHO
    */

    If Select('TMPF3K') <> 0
        TMPF3K->(dbCloseArea())
    Endif
    TCQuery cSql Alias TMPF3K New
    if  TMPF3K->(!eof())


        oModel := FWLoadModel("FISA140")
        oModel:SetOperation(nOper)
        oModel:Activate()
        //oModel:AddGrid( 'F3KDETAIL','MODEL_F3K', oStruF3K2)

        //cDesc :=  PADR("GERADO VIA ROTINA AUTOMATICA",GETSX3CACHE("Z8_DESC","X3_TAMANHO")      )
        oMDF3KCab := oModel:GetModel("MODEL_F3K")
        oMDF3KDet := oModel:GetModel("F3KDETAIL")





        oMDF3KCab:SetValue("F3K_FILIAL"      , TMPF3K->F3K_FILIAL      )
        oMDF3KCab:SetValue("F3K_PROD"      , cCodProd      )
        oMDF3KCab:SetValue("F3K_GRCLAN"      , TMPF3K->F3K_GRCLAN      )
        oMDF3KCab:SetValue("F3K_GRPLAN"     ,TMPF3K->F3K_GRPLAN )
        oMDF3KCab:SetValue("F3K_GRFLAN"  , TMPF3K->F3K_GRFLAN      )
        n1 :=1
        While TMPF3K->(!eof())
            if n1 >1

                oMDF3KDet:AddLine()

            endif

            oMDF3KDet:SetValue("F3K_CFOP"   ,TMPF3K->F3K_CFOP)
            oMDF3KDet:SetValue("F3K_CODAJU" ,TMPF3K->F3K_CODAJU)
            //   oMDF3KDet:SetValue("F3K_VALOR"  ,TMPF3K->F3K_VALOR)
            oMDF3KDet:SetValue("F3K_CST"    ,TMPF3K->F3K_CST)
            oMDF3KDet:SetValue("F3K_CODREF" ,TMPF3K->F3K_CODREF)
            oMDF3KDet:SetValue("F3K_IFCOMP" ,TMPF3K->F3K_IFCOMP)
            oMDF3KDet:SetValue("F3K_CODLAN" ,TMPF3K->F3K_CODLAN)

            n1 ++
            TMPF3K->(dbskip())
        Enddo
        If oModel:VldData()
            If oModel:CommitData()
                lOk := .T.

                //Se não deu certo, altera a variável para false
            Else
                lOk := .F.
            EndIf

            //Se não conseguir validar as informações, altera a variável para false
        Else
            lOk := .F.
        EndIf

        If ! lOk
            //Busca o Erro do Modelo de Dados
            aErro := oModel:GetErrorMessage()

            //Monta o Texto que será mostrado na tela
            cMessage := "Id do formulário de origem:"  + ' [' + cValToChar(aErro[01]) + '], '
            cMessage += "Id do campo de origem: "      + ' [' + cValToChar(aErro[02]) + '], '
            cMessage += "Id do formulário de erro: "   + ' [' + cValToChar(aErro[03]) + '], '
            cMessage += "Id do campo de erro: "        + ' [' + cValToChar(aErro[04]) + '], '
            cMessage += "Id do erro: "                 + ' [' + cValToChar(aErro[05]) + '], '
            cMessage += "Mensagem do erro: "           + ' [' + cValToChar(aErro[06]) + '], '
            cMessage += "Mensagem da solução: "        + ' [' + cValToChar(aErro[07]) + '], '
            cMessage += "Valor atribuído: "            + ' [' + cValToChar(aErro[08]) + '], '
            cMessage += "Valor anterior: "             + ' [' + cValToChar(aErro[09]) + ']'

            //Mostra mensagem de erro
            //   lRet := .F.
            ConOut("Erro: " + cMessage)
            // Else
            //     //  lRet := .T.
            //     ConOut("Produto incluido!")
        EndIf
        //Desativa o modelo de dados
        oModel:DeActivate()
    endif

RETURN


static function fGetQry()

    Local cQryRet := ""
    Local cEOL    := chr(10)


    cQryRet := "SELECT *    FROM dbo."+ RetSqlName("F3K") + " F3K (NOLOCK) "   + cEol
    cQryRet += "    WHERE  F3K.D_E_L_E_T_   = ' ' "   + cEol
    cQryRet += "        AND F3K_PROD        = '10010001' "   + cEol
    cQryRet += "        and F3K_FILIAL = '01'  "   + cEol

Return cQryRet

