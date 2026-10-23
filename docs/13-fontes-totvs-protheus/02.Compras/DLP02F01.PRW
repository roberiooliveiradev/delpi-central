#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"


/*/{Protheus.doc} DLP02F01

    Description
    Rotina que ira listar os produtos da movimentacao interna de baixa (requisição)
    e com base nisso sera gerado a solicitacao por pontod e pedido
    execauto mata170
    @author  Gabriel Araujo

    @param

    ///////////////////////////////////////////////////////////////////////////////////////////
    ///  | Variaveis utilizadas para parametros                                              ||
    ///  | mv_par01  || Produto de                                                           ||
    ///  | mv_par02  || Produto ate                                                          ||
    ///  | mv_par03  || Grupo de                                                             ||
    ///  | mv_par04  || Grupo ate                                                            ||
    ///  | mv_par05  || Tipo de                                                              ||
    ///  | mv_par06  || Tipo ate                                                             ||
    ///  | mv_par07  || Local de                                                             ||
    ///  | mv_par08  || Local ate                                                            ||
    ///  | mv_par09  || Considera Necess Bruta 1 sim Pto Pedido                              ||
    ///  | mv_par10  || Saldo Neg Considera    1 sim Lot.Economico                           ||
    ///  | mv_par11  || Data limite p/ empenhos                                              ||
    ///  | mv_par12  || Cons.Qtd. De 3os.? Sim / Nao                                         ||
    ///  | mv_par13  || Cons.Qtd. Em 3os.? Sim / Nao                                         ||
    ///  | mv_par14  || Ao atingir Estoque Maximo ?  1=Qtde. Original; 2=Ajusta Est. Max     ||
    ///  | mv_par15  || Quebra SC por Lote Econmico?                                         ||
    ///  | mv_par16  || Qtd.PV nao Liberado?" Subtr/Ignora                                   ||
    ///  | mv_par17  || Considera Saldo Armazem de                                           ||
    ///  | mv_par18  || Considera Saldo Armazem ate                                          ||
    ///  | mv_par19  || Seleciona Filiais? (Sim/Nao)                                         ||
    ///  | mv_par20  || Gera SC por produto(Sim/Nao)                                         ||
    ///  | mv_par21  || Considera Est. Seguranca ?  (Sim / Nao)                              ||
    ///  | mv_par22  || Prioriza geração de         (1-Sol.Compra/2-Ped.Compra)              ||
    ///////////////////////////////////////////////////////////////////////////////////////////

    @return  Return
    @table   Tables
    @since   12-08-2020
/*/

uSER FUNCTION DLP02F01(cRot)
    Local aArea         :=GetArea()
    Local aAreaSB1 := SB1->(GetArea())
    Local aAreaSD3 := SD3->(GetArea())
    Local lOpcAuto      := .T.
    lOCAL aParametros   := {}
    lOCAL aProdTmp      :={}
    // Local aGrpTmp       :={}
    // Local aTipoTmp      :={}
    Local nX := 0
    Local nY := 0
    Local cTipoTM       := POSICIONE("SF5",1,XFILIAL("SF5")+iif( UPPER(cRot) $"MATA241" ,cTM,SD3->D3_TM),"F5_TIPO" )
    PRIVATE lMsErroAuto     := .F.
    dbSelectArea("SB1")
    SB1->(dbSetOrder(1))

    /////////////////////////////////////////////////////////////
    // VAI PERCORRER O ACOLS PARA ARMAZENAR OS PRODUTOS        //
    // VALIDO APENAS PARA O TIPO DE MOVIMENTACAO DE REQUISIÇÃO //
    /////////////////////////////////////////////////////////////
    if  cTipoTM $"R"
        if UPPER(cRot) $"MATA241"
            For nY := 1 To Len( aCols)
                IF !(GDDeleted(nY,aHeader,aCols))

                    cProd := GDFieldGet('D3_COD',nY,,,aCols)

                    if SB1->(MsSeek(xFilial("SB1")+cProd))

                        aadd(aProdTmp ,{cProd  ,SB1->B1_GRUPO   ,SB1->B1_TIPO   }  )

                        //  aadd(aProdTmp ,cProd         )
                        //  aadd(aGrpTmp  ,SB1->B1_GRUPO )
                        //  aadd(aTipoTmp ,SB1->B1_TIPO  )

                    endif

                endif
            next nY

        ELSE

            cProd := SD3->D3_COD

            if SB1->(MsSeek(xFilial("SB1")+cProd))

                aadd(aProdTmp ,{cProd  ,SB1->B1_GRUPO   ,SB1->B1_TIPO   }  )
                // aadd(aProdTmp ,cProd         )
                // aadd(aGrpTmp  ,SB1->B1_GRUPO )
                // aadd(aTipoTmp ,SB1->B1_TIPO  )
            ENDIF

        ENDIF
        //ORDENA OS ARRAYS
        IF LEN(aProdTmp)>0

            For nX := 1 to Len(aProdTmp)
                aParametros   := {}


                //    aSort(aProdTmp)
                //    aSort(aGrpTmp)
                //    aSort(aTipoTmp)

                nTMLocal := getsx3cache("B2_LOCAL","X3_TAMANHO")
                AADD(aParametros, aProdTmp[nx][1])                 //  | mv_par01  || Produto de
                AADD(aParametros, aProdTmp[nx][1])     //  | mv_par02  || Produto ate
                AADD(aParametros, aProdTmp[nx][2] )    //  | mv_par03  || Grupo de
                AADD(aParametros, aProdTmp[nx][2])     //  | mv_par04  || Grupo ate
                AADD(aParametros, aProdTmp[nx][3] )   //  | mv_par05  || Tipo de
                AADD(aParametros, aProdTmp[nx][3] )   //  | mv_par06  || Tipo ate
                AADD(aParametros,  '01') //SPACE(nTMLocal))             //  | mv_par07  || Local de
                AADD(aParametros,  '01') //REPLICATE("Z",nTMLocal))     //  | mv_par08  || Local ate
                AADD(aParametros, 2)                           //  | mv_par09  || Considera Necess Bruta 1 sim Pto Pedido
                AADD(aParametros, 1)                           //  | mv_par10  || Saldo Neg Considera    1 sim Lot.Economico
                AADD(aParametros, STOD("20491231"))            //  | mv_par11  || Data limite p/ empenhos
                AADD(aParametros, 1)                           //  | mv_par12  || Cons.Qtd. De 3os.? Sim / Nao
                AADD(aParametros, 2)                           //  | mv_par13  || Cons.Qtd. Em 3os.? Sim / Nao
                AADD(aParametros, 1)                           //  | mv_par14  || Ao atingir Estoque Maximo ?  1=Qtde. Original; 2=Ajusta Est. Max
                AADD(aParametros, 2)                           //  | mv_par15  || Quebra SC por Lote Econmico?
                AADD(aParametros, 1)                           //  | mv_par16  || Qtd.PV nao Liberado?" Subtr/Ignora
                AADD(aParametros, '01') //SPACE(nTMLocal))             //  | mv_par17  || Considera Saldo Armazem de
                AADD(aParametros, '01') //REPLICATE("Z",nTMLocal))     //  | mv_par18  || Considera Saldo Armazem ate
                AADD(aParametros, 2)                           //  | mv_par19  || Seleciona Filiais? (Sim/Nao)
                AADD(aParametros, 1)                           //  | mv_par20  || Gera SC por produto(Sim/Nao)
                AADD(aParametros, 1)                           //  | mv_par21  || Considera Est. Seguranca ?  (Sim / Nao)
                AADD(aParametros, 1)                           //  | mv_par22  || Prioriza geração de         (1-Sol.Compra/2-Ped.Compra)

                lMsErroAuto     := .F.

                MSExecAuto({|x, y| mata170(x, y)},lOpcAuto, aParametros)

                If lMsErroAuto

                    Mostraerro()

                Endif
            Next nX
        ENDIF
    ENDIF

    RESTAREA(aArea)
    RESTAREA(aAreaSB1)
    RESTAREA(aAreaSD3)

RETURN
