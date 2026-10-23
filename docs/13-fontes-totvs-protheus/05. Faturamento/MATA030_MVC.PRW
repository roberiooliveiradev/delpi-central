#include 'protheus.ch'
#include 'topconn.ch'
#include 'parmtype.ch'
#INCLUDE "FWMVCDEF.CH"
#Include 'TBICONN.ch'
/*/{Protheus.doc} MA030TOK
)
Local lRet @type  Function
@author lRet
@since 17/07/2019
@version version
@param param_name, param_type, param_descr
@return return_var, return_type, return_description
@example
(examples)
@see (links_or_references)
/*/

User Function CRMA980()

    Local aArea := geTarea()
    Local xRet := .T.
    Local aParsMVC     := PARAMIXB
    Local cMV_030TOK    := SUPERGETMV("MV_M030TOK",.F.,"04")
    Local cMV_030DLP    := SUPERGETMV("MV_M030DLP",.F.,"03")
    local oModel030   		:= FWModelActive()
    //Local oView   		:= FWViewActive()
    Local aRet04        := {}

    lOCAL aParSA1       := {}
    Local nOperation
    local oModelSA1
    Local cA1CGC
    Local cA1CONTA
    lOCAL cA1NREDUZ
    //oModelZZ8GR:LoadValue('T01_LEGEN',"BR_AMARELO")
    //oModelZZ6:GetValue('ZZ6_CODBAR')

    //// aParsMVC[2] == 'MODELPOS' _FORMCOMMITTTSPOS
    If   aParsMVC[2] $  "FORMCOMMITTTSPOS"  .AND. alltrim(cEmpAnt) $ cMV_030TOK .and. alltrim( aParsMVC[3]) $ "SA1MASTER_CRMA980" .AND. ALLTRIM(VALTYPE(oModel030)) $ "O"

        FWMsgRun( ,{|| fProc()},"Efetuando Cadastro de Cliente... ")

        xRet := nil
    elseif alltrim( aParsMVC[2]) $ "FORMCOMMITTTSPOS_MODELCOMMITTTS_MODELCOMMITNTTS_FORMCOMMITTTSPRE_FORMCOMMITTTSPOS"

        xRet := nil

    elseif  alltrim( aParsMVC[2]) $ "BUTTONBAR"

        xRet := {}

    else

        xRet := .t.

    endif


    //   CONOUT('FIM  CRMA980' )
Return xRet

Static Function fProc()
    Local aParsMVC     := PARAMIXB
    Local cMV_030TOK    := SUPERGETMV("MV_M030TOK",.F.,"04")
    Local cMV_030DLP    := SUPERGETMV("MV_M030DLP",.F.,"03")
    local oModel030   		:= FWModelActive()
    //Local oView   		:= FWViewActive()
    Local aRet04        := {}

    lOCAL aParSA1       := {}
    Local nOperation
    local oModelSA1
    Local cA1CGC
    Local cA1CONTA
    lOCAL cA1NREDUZ


    CONOUT("ENTROU EMP " + CEMPANT )
    nOperation      := oModel030:GetOperation()
    oModelSA1	    := oModel030:GetModel("SA1MASTER"   )
    //  oModelSA1	    := oModel030:GetModel(aParsMVC[3]   )

    IF ALLTRIM(VALTYPE(oModelSA1 )) $ "O" .and.( nOperation == 3 .or. nOperation == 4)

        cA1CGC          := oModelSA1:GetValue('A1_CGC'   )
        cA1CONTA        := oModelSA1:GetValue('A1_CONTA' )
        cA1NREDUZ       := oModelSA1:GetValue('A1_NREDUZ')
        xRet := .t.

        IF alltrim(cEmpAnt) $ cMV_030TOK

            IF EMPTY(cA1CONTA)

                //CADASTRO E RETORNO A CONTA CONTABIL
                cA1CONTA := U_DL05P01({cA1CGC,cA1NREDUZ})[2]
                oModelSA1:SetValue('A1_CONTA',cA1CONTA)

            ENDIF

            aadd(aParSA1,{'A1_FILIAL'  , "  "                 })
            aRet04 := fGetCli04({cA1CGC})
            IF aRet04[1]

                aadd(aParSA1,{'A1_COD'     , aRet04[2]   })
                aadd(aParSA1,{'A1_LOJA'    , aRet04[3]   })
                xOper := MODEL_OPERATION_UPDATE

            ELSE

                aadd(aParSA1,{'A1_LOJA'    , oModelSA1:GetValue('A1_LOJA'   )})
                //getsx8num("SA1","A1_COD")
                xOper := MODEL_OPERATION_INSERT
            ENDIF
            //    oModelSA1:SetValue('A1_NOME',"GABRIEL ALTERADO")
            //  oModelSA1:SetValue('A1_LOJA',"02")
            aadd(aParSA1,{'A1_TIPO'    , oModelSA1:GetValue('A1_TIPO'   )})
            aadd(aParSA1,{'A1_CGC'     , oModelSA1:GetValue('A1_CGC'    )})
            aadd(aParSA1,{'A1_NOME'    , alltrim(oModelSA1:GetValue('A1_NOME'   ))  })
            aadd(aParSA1,{'A1_PESSOA'  , oModelSA1:GetValue('A1_PESSOA' )})
            aadd(aParSA1,{'A1_END'     , oModelSA1:GetValue('A1_END'    )})
            aadd(aParSA1,{'A1_NREDUZ'  , oModelSA1:GetValue('A1_NREDUZ' )})
            aadd(aParSA1,{'A1_BAIRRO'  , oModelSA1:GetValue('A1_BAIRRO' )})
            aadd(aParSA1,{'A1_EST'     , oModelSA1:GetValue('A1_EST'    )})
            aadd(aParSA1,{'A1_ESTADO'  , oModelSA1:GetValue('A1_ESTADO' )})
            aadd(aParSA1,{'A1_CEP'     , oModelSA1:GetValue('A1_CEP'    )})
            aadd(aParSA1,{'A1_COD_MUN' , oModelSA1:GetValue('A1_COD_MUN')})
            aadd(aParSA1,{'A1_MUN'     , oModelSA1:GetValue('A1_MUN'    )})
            aadd(aParSA1,{'A1_REGIAO'  , oModelSA1:GetValue('A1_REGIAO' )})
            aadd(aParSA1,{'A1_DSCREG'  , oModelSA1:GetValue('A1_DSCREG' )})
            // aadd(aParSA1,{'A1_CONTA'   , oModelSA1:GetValue('A1_CONTA  ')})
            aadd(aParSA1,{'A1_TEL'     , oModelSA1:GetValue('A1_TEL'    )})
            aadd(aParSA1,{'A1_DDD'     , oModelSA1:GetValue('A1_DDD'    )})
            aadd(aParSA1,{'A1_DDI'     , oModelSA1:GetValue('A1_DDI'    )})
            aadd(aParSA1,{'A1_CONTATO' , oModelSA1:GetValue('A1_CONTATO')})
            aadd(aParSA1,{'A1_PFISICA' , oModelSA1:GetValue('A1_PFISICA')})
            aadd(aParSA1,{'A1_INSCR'   , oModelSA1:GetValue('A1_INSCR'  )})
            aadd(aParSA1,{'A1_PAIS'    , oModelSA1:GetValue('A1_PAIS'   )})
            aadd(aParSA1,{'A1_INSCRM'  , oModelSA1:GetValue('A1_INSCRM' )})
            aadd(aParSA1,{'A1_VEND'    , oModelSA1:GetValue('A1_VEND'   )})
            aadd(aParSA1,{'A1_RISCO'   , oModelSA1:GetValue('A1_RISCO'  )})
            aadd(aParSA1,{'A1_NATUREZ'   , oModelSA1:GetValue('A1_NATUREZ'  )})

            //   oModelSA1:DeActivate()
            oModel030:DeActivate()
            oModelSA1:DeActivate()
            //Inclui o mesmo produto na empresa '02'
            //STARTJOB("U_T010Auto",getenvserver(),.t.,aVetor)
            //    STARTJOB("u_fCadCli",getenvserver(),.t.,aParSA1,xOper)
            cIpCon   := "192.168.1.8"
            //cPortCon := 1040
            cPortCon :=  4040
            cEnvSrv  :=  "RPC_CRM"

            //instancia nova conexao e ambiente
            oRPCServer := nil
            oRPCServer := TRPC():New( cEnvSrv )
            //faz a conexao RPC
            If oRPCServer:Connect( cIpCon, cPortCon )
                aRetJob := oRPCServer:CallProc ("u_fCadCli" ,aParSA1,xOper, {'03','01',"FAT"})
                oRPCServer:Disconnect()
            Else

                conout('Não foi possivel conectar ao RPC!')

            Endif
            oModel030:Activate()
            oModelSA1:Activate()
            // RESTAREA(aArea)
        endif
    endif

Return


Static Function fGetCli04(aPar)

    Local aRet := {''}
    Local cSql := ""
    Local cEol := chr(10)

    CONOUT("INI fGetCli04")

    cSql +="SELECT A1_COD , A1_LOJA         " + cEol
    cSql +="    FROM dbo.SA1030 A (NOLOCK)  " + cEol
    cSql +="WHERE A.D_E_L_E_T_ = ''      " + cEol
    cSql +="      AND A.A1_CGC =         " + valtosql(aPar[1])

    If Select("TRB003") <> 0
        dbSelectArea("TRB003")
        dbCloseArea()
    EndIf

    TCQUERY cSql NEW ALIAS "TRB003"

    if TRB003->(!EOF())

        aRet := {.T.,TRB003->A1_COD,TRB003->A1_LOJA}

    ELSE

        aRet := {.F.,'',''}

    ENDIF

    CONOUT('FIM  fGetCli04' )

Return aRet



Static Function ALTEMP(cEmp, cFil)

    Local cemp:=cEmp
    Local cfil:=cFil
    CONOUT("INI ALTEMP" )
    conout("cEmp :"+cEmp+" / cFil :"+ cFil)
    dbcloseall()

    cempant :=cemp
    cfilant :=cfil
    cNumEmp :=cemp+cfil
    Opensm0(cempant+cfil)
    Openfile(cempant+cfil)
    lrefresh :=.T.
    CONOUT("FIM ALTEMP" )
Return

