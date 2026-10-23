#include 'protheus.ch'
#include 'topconn.ch'
#include 'parmtype.ch'
#INCLUDE "FWMVCDEF.CH"
/*/{Protheus.doc} DL05P01
//ROTINA PARA CADASTRO DE CENTRO DE CUSTO A PARTIR DO CADASTRO DO CLIENTE
@author Gabriel Araujo
@since 07/2018
@version undefined

@type function
/*/

user Function DL05P01(aPars)

Local nOpcAuto :=0
Local nX
Local oCT1
Local aLog
Local cLog :=""
Local lRet := .T.
Local cCta := GetNextCta()
Local __oModelAut

    If __oModelAut == Nil //somente uma unica vez carrega o modelo CTBA020-Plano de Contas CT1
        __oModelAut := FWLoadModel('CTBA020')
    EndIf


nOpcAuto:=3


__oModelAut:SetOperation(nOpcAuto) // 3 - Inclusão | 4 - Alteração | 5 - Exclusão
__oModelAut:Activate() //ativa modelo

//---------------------------------------------------------
// Preencho os valores da CT1
//---------------------------------------------------------


oCT1 := __oModelAut:GetModel('CT1MASTER') //Objeto similar enchoice CT1 
oCT1:SETVALUE('CT1_CONTA',cCta)
oCT1:SETVALUE('CT1_DESC01',padr(aPars[2],tamsx3('CT1_DESC01')[1]))
oCT1:SETVALUE('CT1_CTASUP','11201')
oCT1:SETVALUE('CT1_CLASSE','2')
oCT1:SETVALUE('CT1_NORMAL' ,'1')

//---------------------------------------------------------
// Preencho os valores da CVD
//---------------------------------------------------------
/*
oCVD := __oModelAut:GetModel('CVDDETAIL') //Objeto similar getdados CVD
oCVD:SETVALUE('CVD_FILIAL' ,CVD->(xFilial('CVD'))) 
oCVD:SETVALUE('CVD_ENTREF','10')
oCVD:SETVALUE('CVD_CODPLA',PadR('2016',Len(CVD->CVD_CODPLA))) 
oCVD:SETVALUE('CVD_CTAREF',PadR('1.01.01.01.01', Len(CVD->CVD_CTAREF)))
oCVD:SETVALUE('CVD_TPUTIL','A')
oCVD:SETVALUE('CVD_CLASSE','2') 
oCVD:SETVALUE('CVD_VERSAO',PadR('0001',Len(CVD->CVD_VERSAO)))
oCVD:SETVALUE('CVD_CUSTO' ,PadR('001',Len(CVD->CVD_CUSTO)))

//---------------------------------------------------------
// Preencho os valores da CTS
//---------------------------------------------------------


oCTS := __oModelAut:GetModel('CTSDETAIL') //Objeto similar getdados CTS
oCTS:SETVALUE('CTS_FILIAL' ,CTS->(xFilial('CTS'))) 
oCTS:SETVALUE('CTS_CODPLA' ,'001')
oCTS:SETVALUE('CTS_CONTAG' ,'0000021')
*/

    If __oModelAut:VldData() //validacao dos dados pelo modelo

        __oModelAut:CommitData() //gravacao dos dados

    Else

        aLog := __oModelAut:GetErrorMessage() //Recupera o erro do model quando nao passou no VldData

//laco para gravar em string cLog conteudo do array aLog
        For nX := 1 to Len(aLog)
            If !Empty(aLog[nX])
                cLog += Alltrim(aLog[nX]) + CRLF
            EndIf
        Next nX

        lMsErroAuto := .T. //seta variavel private como erro
        AutoGRLog(cLog) //grava log para exibir com funcao mostraerro
        mostraerro()
        lRet := .F. //retorna false

    EndIf

    __oModelAut:DeActivate() //desativa modelo

Return( {lRet,cCta} )


Static Function GetNextCta()
    Local cSql := ""
    Local cEol := chr(10)
    Local nRet := ""


    cSql +="SELECT MAX(SUBSTRING(A.CT1_CONTA, 6, 3)) ID_CONTA " + cEol
    cSql +="FROM dbo." + retsqlname("CT1") + " A (NOLOCK) 	  " + cEol
    cSql +="WHERE A.D_E_L_E_T_ = '' 						  " + cEol
    cSql +="      AND A.CT1_CTASUP = '11201';				  " + cEol


    If Select("TRB001") <> 0
        dbSelectArea("TRB001")
        dbCloseArea()
    EndIf

    TCQUERY cSql NEW ALIAS "TRB001"

    IF EMPTY(TRB001->ID_CONTA)
        nRet :="000"
    ELSE
        nRet :=TRB001->ID_CONTA
    ENDIF

    nRet :='11201'+SOMA1(  nRet )
    nRet := padr(alltrim(nRet),tamsx3('CT1_CONTA')[1])

return nRet


User Function P01TST()
    Local cSql1 := " UPDATE dbo.SA1030 SET A1_CONTA = '' WHERE D_E_L_E_T_ ='' AND A1_CGC = ''"
    Local cSql2 := " UPDATE dbo.SA1040 SET A1_CONTA = '' WHERE D_E_L_E_T_ ='' AND A1_CGC = ''"
    Local cEol := chr(10)
    Local cSql
    Local aRetPar

    cSql := "SELECT DISTINCT A1_NOME,A1_NREDUZ,A1_CGC" + cEol
    cSql += "				FROM dbo.SA1030          " + cEol
    cSql += "WHERE D_E_L_E_T_ = '' AND A1_CONTA =''  " + cEol
    cSql += "UNION 									 " + cEol
    cSql += "SELECT DISTINCT A1_NOME,A1_NREDUZ,A1_CGC" + cEol
    cSql += "				FROM dbo.SA1040			 " + cEol
    cSql += "WHERE D_E_L_E_T_ = '' AND A1_CONTA =''	 " + cEol

    If Select("TRB002") <> 0
        dbSelectArea("TRB002")
        dbCloseArea()
    EndIf

    TCQUERY cSql NEW ALIAS "TRB002"

    While TRB002->(!EOF())

        aRetPar:=        U_DL05P01({ TRB002->A1_CGC,TRB002->A1_NREDUZ})
        if aRetPar[1]

            cSql1 := " UPDATE dbo.SA1030 SET A1_CONTA = "+valtosql(aRetPar[2])+" WHERE D_E_L_E_T_ ='' AND A1_CGC = "+valtosql(TRB002->A1_CGC)
            cSql2 := " UPDATE dbo.SA1040 SET A1_CONTA = "+valtosql(aRetPar[2])+" WHERE D_E_L_E_T_ ='' AND A1_CGC = "+valtosql(TRB002->A1_CGC)

            TCSQLExec(cSql1)
            TCSQLExec(cSql2)

        endif
        TRB002->(dbSkip())

    EndDo

RETURN
