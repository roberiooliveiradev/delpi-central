#include 'protheus.ch'
#include 'topconn.ch'
#include 'parmtype.ch'
#INCLUDE "FWMVCDEF.CH"
#Include 'TBICONN.ch'

USER FUNCTION MT410INC()
    Local aArea:= Getarea()

    FWMsgRun( ,{|| fProc()},"Efetuando Ajustes no Pedido... ")
    restarea(aArea)
Return Nil

Static Function fProc()
    Local aRet04 := {}
    Local xOper := Nil
    Local cMV_030TOK2   := SUPERGETMV("MV_M030TOK2",.F.,"04")
    Local aParPV        :={}
    Local aVct        :={}
    lOCAL nPar          := "0"
    Private lRetSA1     := .t.
    Private lRetPV      := .t.


    if alltrim(cEmpAnt) $ cMV_030TOK2
        //chamo função para verificar e cadastrar cliente na empresa 03
        lRet := fPutSA1()
        if lRet
            conout("cadastrou o cliente")

            if SE4->E4_TIPO  $ '9'
                aStruSC5 :=  SC5->(dbStruct())
                aVct :={}

                for n1 := 1 to len(aStruSC5)
                    if alltrim(aStruSC5[n1][1] ) $ "C5_DATA_C5_PARC"
                        xCont :=   cDescP:= &("M->"+aStruSC5[n1][1])
                        aadd(aVct,{aStruSC5[n1][1],xCont  ,Nil})
                    endif
                Next n1
            ENDIF
            cMVPrdSrv := alltrim(supergetmv("MV_YPRDSRV",.F.,"90020001"))
            aInfPV04:=fGetItPV({ADY->ADY_PROPOS,cMVPrdSrv,cFilAnt,SE4->E4_TIPO})
            aadd(aParPV,{SA1->A1_CGC})     //[1]
            aadd(aParPV,{M->C5_NUM})       //[2]
            aadd(aParPV,{cFilAnt})         //[3]
            aadd(aParPV,{ADY->ADY_PROPOS}) //[4]
            aadd(aParPV,{SE4->E4_TIPO})    //[5]
            aadd(aParPV,{aVct})            //[6]
            aadd(aParPV,{aInfPV04})        //[7]

            if lRet
                cIpCon   := "192.168.1.8"
                //cPortCon := 1040
                cPortCon := 4040
                cEnvSrv  :=  "RPC_CRM"

                //instancia nova conexao e ambiente
                oRPCServer := nil
                oRPCServer := TRPC():New( cEnvSrv )
                //faz a conexao RPC
                If oRPCServer:Connect( cIpCon, cPortCon )
                    aRetJob := oRPCServer:CallProc ("u_fPutPV" ,aParPV, {'03','01',"FAT"} )
                    oRPCServer:Disconnect()
                Else

                    conout('Não foi possivel conectar ao RPC!')

                Endif
            Endif

        EndIf
        if !lRetPV
            CONOUT("xxxxxx")
        else
            conout("passou")
        EndIf
    EndIf
Return Nil


//-----------------------------------------------------------------------------
/*/{Protheus.doc} fPutSA1
Função que Prepara as variaveis para chamadad do execauto do cliente

@return 	aRet =>  lRet Variavel de controle de incluiu ou nao o Cliente
@author     Squad CRM / FAT
@version    12.1.17 / Superior
@since      08/2019
/*/
//-----------------------------------------------------------------------------

Static Function fPutSA1()
    Local lRet := .t.
    Local aParSA1 :={}

    aRet04 := fGetCli04({SA1->A1_CGC})
    IF !aRet04[1]

        xOper := MODEL_OPERATION_INSERT

        aadd(aParSA1,{'A1_LOJA'    ,             "01"})
        aadd(aParSA1,{'A1_TIPO'    ,SA1->A1_TIPO     })
        aadd(aParSA1,{'A1_CGC'     ,SA1->A1_CGC      })
        aadd(aParSA1,{'A1_NOME'    ,SA1->A1_NOME     })
        aadd(aParSA1,{'A1_PESSOA'  ,SA1->A1_PESSOA   })
        aadd(aParSA1,{'A1_END'     ,SA1->A1_END      })
        aadd(aParSA1,{'A1_NREDUZ'  ,SA1->A1_NREDUZ   })
        aadd(aParSA1,{'A1_BAIRRO'  ,SA1->A1_BAIRRO   })
        aadd(aParSA1,{'A1_EST'     ,SA1->A1_EST      })
        aadd(aParSA1,{'A1_ESTADO'  ,SA1->A1_ESTADO   })
        aadd(aParSA1,{'A1_CEP'     ,SA1->A1_CEP      })
        aadd(aParSA1,{'A1_COD_MUN' ,SA1->A1_COD_MUN  })
        aadd(aParSA1,{'A1_MUN'     ,SA1->A1_MUN      })
        aadd(aParSA1,{'A1_REGIAO'  ,SA1->A1_REGIAO   })
        aadd(aParSA1,{'A1_DSCREG'  ,SA1->A1_DSCREG   })
        aadd(aParSA1,{'A1_CONTA'   ,SA1->A1_CONTA    })
        aadd(aParSA1,{'A1_TEL'     ,SA1->A1_TEL      })
        aadd(aParSA1,{'A1_DDD'     ,SA1->A1_DDD      })
        aadd(aParSA1,{'A1_DDI'     ,SA1->A1_DDI      })
        aadd(aParSA1,{'A1_CONTATO' ,SA1->A1_CONTATO  })
        aadd(aParSA1,{'A1_PFISICA' ,SA1->A1_PFISICA  })
        aadd(aParSA1,{'A1_INSCR'   ,SA1->A1_INSCR    })
        aadd(aParSA1,{'A1_PAIS'    ,SA1->A1_PAIS     })
        aadd(aParSA1,{'A1_INSCRM'  ,SA1->A1_INSCRM   })
        aadd(aParSA1,{'A1_VEND'    ,SA1->A1_VEND     })
        aadd(aParSA1,{'A1_RISCO'   ,SA1->A1_RISCO    })
        aadd(aParSA1,{'A1_NATUREZ' ,SA1->A1_NATUREZ    })


        conout("Operação "+ cvaltochar(xOper))
        cIpCon   := "192.168.1.8"
        //cPortCon := 1040
        cPortCon := 4040
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
        // STARTJOB("u_fCadCli",getenvserver(),.t.,aParSA1,xOper)

    ENDIF
    lRet := lRetSA1

Return lRet


//-----------------------------------------------------------------------------
/*/{Protheus.doc} fGetCli04
Função que Verifica se o cliente existe na empresa 03
@param      aPar => 1 - CNPJ/CPF
@return 	aRet =>  lRet Variavel de controle de incluiu ou nao o Cliente
@author     Squad CRM / FAT
@version    12.1.17 / Superior
@since      08/2019
/*/
//-----------------------------------------------------------------------------
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

//----------------------------------------------------------------------------------------------------------------------------
/*/{Protheus.doc} fGetItPV
Função para retornar os itens do Pedidod e venda
@param      aPar => 1 - Numero Proposta   | 2 - Produto Serviço | 3 - Filial do Pedido Origem
@return 	aRet => 1 - Produto Srv       | 2 - Qtd Vend        | 3 - Valor Unit              | 4 - Valor Total
@author     Squad CRM / FAT
@version    12.1.17 / Superior
@since      08/2019
/*/
//----------------------------------------------------------------------------------------------------------------------------
Static Function fGetItPV(aPar)

    Local aRet    := {}
    Local aRetTrb := {}
    Local cSql    := ""
    Local cEol    := chr(10)
    lOCAL nTotPV  := 0
    lOCAL cCondPG := ""
    Local aVencto :={}

    /*cSql += "SELECT A.CK_PRODUTO,					          " + cEol
cSql += "       A.CK_QTDVEN,					          " + cEol
cSql += "       A.CK_PRCVEN,					          " + cEol
cSql += "       A.CK_VALOR,						          " + cEol
cSql += "       A.CK_TES,						          " + cEol
cSql += "       A.CK_ENTREG,					          " + cEol
cSql += "       A.CK_NUMPV						          " + cEol
cSql += "FROM dbo.SCK040 A (NOLOCK)				          " + cEol
cSql += "WHERE A.D_E_L_E_T_     = ''			          " + cEol
cSql += "      AND CK_FILIAL    = "  + valtosql(aPar[3])    + cEol
cSql += "      AND CK_PROPOST     = "  + valtosql(aPar[1])    + cEol
    cSql += "      AND A.CK_PRODUTO = "  + valtosql(aPar[2]) */

    cSql +="SELECT A.*                                   " + cEol
    cSql +="FROM dbo.ADZ040 A (NOLOCK)                   " + cEol
    cSql +="WHERE A.D_E_L_E_T_ = ''                      " + cEol
    cSql +="      AND A.ADZ_FILIAL = " + valtosql(aPar[3]) + cEol
    cSql +="      AND A.ADZ_PRODUT = " + valtosql(aPar[2]) + cEol
    cSql +="      AND A.ADZ_PROPOS = " + valtosql(aPar[1])

    conout(cSql)
    If Select("TRB004") <> 0
        dbSelectArea("TRB004")
        dbCloseArea()
    EndIf

    TCQUERY cSql NEW ALIAS "TRB004"

    While TRB004->(!EOF())

        nTotPV   += TRB004->ADZ_TOTAL
        cCondPG  := TRB004->ADZ_CONDPG
        dDayOne  := DataValida(TRB004->ADZ_DT1VEN, .T.)

        aadd(aRetTrb,{TRB004->ADZ_PRODUT,TRB004->ADZ_QTDVEN,TRB004->ADZ_PRCVEN,TRB004->ADZ_PRCTAB,TRB004->ADZ_TOTAL})

        TRB004->(dbSkip())

    enddo
    /*IF aPar[4] != '9'
    aVencto := Condicao(nTotPV,cCondPG,0,dDayOne,0)
    ENDIF    */
    //aRet :={aRetTrb,aVencto}
    aRet :={aRetTrb}
Return aRet