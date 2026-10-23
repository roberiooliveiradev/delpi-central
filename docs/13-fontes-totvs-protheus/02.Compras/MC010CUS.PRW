#include 'protheus.ch'
#include 'topconn.ch'
#include 'parmtype.ch'
#INCLUDE "FWMVCDEF.CH"
#Include 'TBICONN.ch'

USER FUNCTION MC010CUS()
    Local aArea := getarea()
    Local cCodProd :=  paramixb[1]
    LOCAL nRet := paramixb[2]
    Local xfil := iif(Type("xFilDlp")<> "U" ,xFilDlp,cFilAnt)
    lOCAL cSql := ""
    LOCAL CEOL := CHR(10)
    Local cTpProd :=posicione("SB1",1,XFILIAL("SB1")+cCodProd,"B1_TIPO")
    Local nPicm :=0

    if cEmpAnt $ "01_05"
        //  if fGetFil(@cFil)

        cSql :="SELECT ISNULL(MIN(AIB_PRCCOM),0) AIB_PRCCOM" + CEOL
        cSql +="FROM "+retsqlname("AIB")+" A (NOLOCK) " + CEOL

        cSql +="WHERE A.D_E_L_E_T_ = '' AND SUBSTRING(AIB_DATVIG,1,4) = YEAR(GETDATE())" + CEOL
        cSql +="      AND AIB_FILIAL = "+VALTOSQL(iif(!Empty(xfil),xfil,cfilant) ) + CEOL
        cSql +="      AND AIB_CODPRO = "+VALTOSQL(cCodProd)

        CONOUT(cSql)

        If Select("TAIB") <> 0
            dbSelectArea("TAIB")
            dbCloseArea()
        EndIf

        TCQUERY cSql NEW ALIAS "TAIB"
        // + 2 % DE FRETE DEPOIS DESCONTA O BZ_PICMS
        if TAIB->(!EOF()) .AND. TAIB->AIB_PRCCOM > 0
            nPicm := (posicione("SBZ",1,XFILIAL("SBZ")+cCodProd,"BZ_PICM") /100)
            nRet := TAIB->AIB_PRCCOM +( TAIB->AIB_PRCCOM *0.02)
            if nPicm>0

                nRet := nRet * (1-nPicm)

            endif

        else

            IF ALLTRIM(cTpProd) $ "MP"

                nRet := 0

            ENDIF
        endif
        //   endif
    endif

    /*  CONOUT("1 - PRODUTO: "+  paramixb[1])
    CONOUT("2 - CUSTO ROTINA : "+CVALTOCHAR( paramixb[2]))
    CONOUT("3 - CUSTO CALC   : "+CVALTOCHAR( TAIB->AIB_PRCCOM))
    CONOUT("4 - CUSTO Retorno   : "+CVALTOCHAR( nRet))*/
    restarea(aArea)
Return nRet



Static Function fGetFil(cFil)

    Local aButtons := {}

    Local oGet1
    Local cGetFil := CEMPANT //space(tamsx3("B1_FILIAL")[1])

    Local oSay1
    Local oSay2
    Local cOldTitle := CCADASTRO
    Static oDlgPrd
    Static lRet := .F.
    CCADASTRO := "Delpi - Formacao de Preco"


    DEFINE MSDIALOG oDlgPrd TITLE CCADASTRO FROM 000, 000  TO 180, 570 COLORS 0, 16777215 PIXEL

    @ 035, 008 SAY oSay2 PROMPT "Filial" SIZE 053, 009 OF oDlgPrd COLORS 0, 16777215 PIXEL
    @ 035, 072 MSGET oGet1 VAR cGetFil SIZE 060, 010 OF oDlgPrd COLORS 0, 16777215  VALID !EMPTY(cGetFil)        PIXEL

    bOk := {|| F010End(@oDlgPrd,cGetFil,@cFil,@lRet ) } //Botao salvar
    bCancel := {||oDlgPrd:End()} //botao cancelar

    ACTIVATE MSDIALOG oDlgPrd ON INIT EnchoiceBar(oDlgPrd, bOk , bCancel,,,,,,,,,,"Form Preco")  CENTERED


    CCADASTRO := cOldTitle

Return lRet

sTATIC FUNCTION F010End(oDlgPrd,cGetFil,cFil,lRet)

    if !Empty(cGetFil)
        cFil:=cGetFil
        cGetFil:=.t.
        oDlgPrd:End()
    endif
Return
