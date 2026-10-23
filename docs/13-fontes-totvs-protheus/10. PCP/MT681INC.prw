#INCLUDE "PROTHEUS.CH"


/*/{Protheus.doc} User Function MT681INC
    Preenche a SBC através da rotina MATA685
    @type  Function
    @author Luan Woichechoscki
    @since 08/08/2022
    @version version
    @param
    @return nill
    @example
    (examples)
    @see (links_or_references)
/*/
User Function MT681INC()

    Local aCabec, aItens, aLinha    :=  {}
    Local dDataBase                 :=  Date()
    Local cArmazem                  :=  SUPERGETMV("MV_LOCPERD", .F., "99")
    Local cQuery                    :=  ""
    Local aArea		:= GetArea()
    Local aAreaSBC	:= SBC->(GetArea())
    Local aAreaSH6	:= SH6->(GetArea())
    Private lMsErroAuto := .f.
    conout("MT681INC")
    IF SH6->H6_QTDPERD>0 .AND. IsInCallStack('POST_MATA681')
        conout("ENTROU NA ROTINA DE PERDA")
        H6_CCCA01
        aCabec  :=  {;
            {"BC_OP"        , SH6->H6_OP        , Nil},;
            {"BC_RECURSO"   , SH6->H6_RECURSO   , Nil},;
            {"BC_OPERAC"    , SH6->H6_OPERAC    , Nil};
            }

        aItens  :=  {;
            {"BC_QUANT"     , SH6->H6_QTDPERD   , Nil},;
            {"BC_QTDDEST"   , SH6->H6_QTDPERD   , Nil},;
            {"BC_PRODUTO"   , SH6->H6_CCCA02    , Nil},;
            {"BC_LOCORIG"   , cArmazem          , Nil},;
            {"BC_TIPO"      , SH6->H6_CCCA01    , Nil},;
            {"BC_DTVALID"   , dDataBase         , Nil},;
            {"BC_DATA"      , dDataBase         , Nil},;
            {"BC_NCONFOR"   , SH6->H6_CCCA04    , Nil},;
            {"BC_OPERADO"   , SH6->H6_OPERADO   , Nil},;
            {"BC_OBSERVA"   , SH6->H6_IDENT     , Nil},;
            {"BC_MOTIVO"    , SH6->H6_CCCA03    , Nil};
            }

        aAdd(aLinha, aItens)
        MsExecAuto( { |x,y,z| MATA685(x,y,z) }, aCabec, aLinha, 3 )

        If lMsErroAuto
            conout("DEU ERRO NO EXECAUTO")
            //MostraErro()
            lMsErroAuto := .f.
        Else
            conout("DEU CERTO O EXECAUTO")
            cQuery := "Update "+RetSqlName("SBC")+" Set BC_IDENSH6 = "+valtosql(SH6->H6_IDENT)+" WHERE BC_OBSERVA = "+valtosql(SH6->H6_IDENT)
            TCSQLEXEC( cquery )
        EndIf

    ENDIF

    restarea( aArea)
    restarea( aAreaSBC)
    restarea( aAreaSH6)
Return
