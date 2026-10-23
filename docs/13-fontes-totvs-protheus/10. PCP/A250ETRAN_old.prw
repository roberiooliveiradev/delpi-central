#Include 'FWMVCDef.ch'
#include 'protheus.ch'
#include 'parmtype.ch'
#INCLUDE 'TOPCONN.CH'
/*/{Protheus.doc} A250ETRAN

    Validacao do saldo em estoque

    @author  Name
    @example Example
    @param   [Parameter_Name],Parameter_type,Parameter_Description
    @return  Return
    @table   Tables
    @since   01-07-2020
/*/


user FUNCTION A250ETRAN()
    lOCAL cSql := ""
    local cEol := chr(10)
    lOCAL cMsgBody := "" //Corpo da Mensagem
    Local nTamDesc := 70
    Local nTamQtd := GetSx3Cache("D3_QUANT", "X3_TAMANHO")
    LOCAL  dData:=dDataBase



    Local aVetor := {}
    Local dData
    Local nOpc   := 5 //-Opção de execução da rotina, informado nos parametros quais as opções possiveisl

    Private lMsErroAuto := .F.
    dData:=dDataBase
    //msgalert("TESTE")
    // aVetor := {;
    //     {"D3_OP" ,_cNumOP ,NIL},;
    //     {"D3_QUANT" , cGet1  ,NIL},;
    //     {"D3_TM" ,"002" ,NIL}}
    //
    // MSExecAuto({|x, y| mata250(x, y)},aVetor, nOpc )
    cSql +=" SELECT LTRIM(RTRIM(SB2.B2_COD)) + ' - ' + LTRIM(RTRIM(SB1.B1_DESC)) [COD],SUM( SD3.D3_QUANT)D3_QUANT,  SB2.B2_QATU [SLD] " + cEol
    cSql +=" FROM "+retsqlname("SB2")+" SB2 (NOLOCK) 	 " + cEol
    cSql +="     JOIN "+retsqlname("SB1")+" SB1 (NOLOCK) " + cEol
    cSql +="         ON SB1.D_E_L_E_T_ = '' 			 " + cEol
    cSql +="            AND SB2.B2_COD = SB1.B1_COD		 " + cEol
    cSql +="     JOIN "+retsqlname("SD3")+" SD3 (NOLOCK) " + cEol
    cSql +="         ON SD3.D_E_L_E_T_     = '' 	     " + cEol
    cSql +="            AND SD3.D3_DOC     =   " + valtosql(SD3->D3_DOC) + cEol
    cSql +="            AND SD3.D3_FILIAL  =   " +  valtosql(xfilial("SD3")) + cEol
    cSql +="            AND SD3.D3_ESTORNO = ''          " + cEol
    cSql +="            AND SB2.B2_FILIAL + SB2.B2_COD + SB2.B2_LOCAL = SD3.D3_FILIAL + SD3.D3_COD + SD3.D3_LOCAL " + cEol
    cSql +=" WHERE SB2.D_E_L_E_T_ = '' " + cEol
    cSql +="       AND SB2.B2_QATU < 0 " + cEol
    cSql +=" GROUP BY SB2.B2_COD,SB1.B1_DESC,B2_QATU  ORDER BY 1 "


    If Select("QRYTMP") > 1
        QRYTMP->(DbCloseArea())
    EndIf

    TcQuery cSQL New Alias "QRYTMP"

    While !QRYTMP->(Eof())
        // adiciona cabeçalho
        if EMPTY(cMsgBody )

            cMsgBody:= "Não Existe saldo o suficiente para os produtos abaixo." + cEol
            cMsgBody+= "A Ordem de Producao não sera gerada" + cEol
            //    cMsgBody+= padr("Produto",nTamDesc) +" | " +;
            //        padr("Qtd OP",nTamQtd) +" | " +;
            //        padr("Estoque",nTamQtd) +" | "

        endif
        cMsgBody += cEol
        cMsgBody +=  substr(alltrim(QRYTMP->COD),1,nTamDesc) +" | "+;
            padr(Transform(QRYTMP->D3_QUANT, GetSx3Cache("D3_QUANT", "X3_PICTURE")),nTamQtd) +" | " +;
            padr(Transform(QRYTMP->SLD, GetSx3Cache("D3_QUANT", "X3_PICTURE")),nTamQtd) +" | "

        QRYTMP->(DbSkip())
    EndDo
    QRYTMP->(DbCloseArea())
    IF !EMPTY(cMsgBody)

        //  Aviso("DELPI",cMsgBody,{"OK"})
        AutoGrLog(cMsgBody)

        MostraErro()
        lMsErroAuto := .F.
        aApont := {}
        Aadd(aApont,{"D3_DOC"    ,SD3->D3_DOC       ,Nil})
        Aadd(aApont,{"D3_OP"     ,SD3->D3_OP        ,Nil})
        Aadd(aApont,{"D3_COD"    ,SD3->D3_COD       ,Nil})
        Aadd(aApont,{"D3_UM"     ,SD3->D3_UM        ,Nil})
        Aadd(aApont,{"D3_QUANT"  ,SD3->D3_QUANT     ,Nil})
        Aadd(aApont,{"D3_LOCAL"  ,SD3->D3_LOCAL     ,Nil})
        Aadd(aApont,{"D3_CC"     ,SD3->D3_CC        ,Nil})
        Aadd(aApont,{"D3_EMISSAO",SD3->D3_EMISSAO   ,Nil})
        Aadd(aApont,{"D3_LOTECTL",SD3->D3_LOTECTL   ,Nil})
        Aadd(aApont,{"D3_DTVALID",SD3->D3_DTVALID   ,Nil})
        Aadd(aApont,{"D3_NUMSEQ" ,SD3->D3_NUMSEQ    ,Nil})
        Aadd(aApont,{"D3_CHAVE"  ,SD3->D3_CHAVE     ,Nil})
        Aadd(aApont,{"D3_CF"     ,"PR0"             ,Nil})
        aAdd(aApont,{"INDEX"     , 4                ,Nil})

        MsExecAuto({|x,y| MATA250(x,y)},aApont,5)

        If lMsErroAuto

            DisarmTransaction()
            Mostraerro()

        EndIf
    ENDIF

    IF lMsErroAuto

        MSGALERT("Erro ao Estornar OP, gentileza estornar OP Manualmente.")
        MOSTRAERROR()

    ENDIF

Return nil


USER FUNCTION DLPOP()

    Private lMsErroAuto := .F.
    DBSELECTAREA("SD3")
    SD3->( dbGoTo( 2410104 ) )
    aApont := {}
    Aadd(aApont,{"D3_DOC"    ,SD3->D3_DOC       ,Nil})
    Aadd(aApont,{"D3_OP"     ,SD3->D3_OP        ,Nil})
    Aadd(aApont,{"D3_COD"    ,SD3->D3_COD       ,Nil})
    Aadd(aApont,{"D3_UM"     ,SD3->D3_UM        ,Nil})
    Aadd(aApont,{"D3_QUANT"  ,SD3->D3_QUANT     ,Nil})
    Aadd(aApont,{"D3_LOCAL"  ,SD3->D3_LOCAL     ,Nil})
    Aadd(aApont,{"D3_CC"     ,SD3->D3_CC        ,Nil})
    Aadd(aApont,{"D3_EMISSAO",SD3->D3_EMISSAO   ,Nil})
    Aadd(aApont,{"D3_LOTECTL",SD3->D3_LOTECTL   ,Nil})
    Aadd(aApont,{"D3_DTVALID",SD3->D3_DTVALID   ,Nil})
    Aadd(aApont,{"D3_NUMSEQ" ,SD3->D3_NUMSEQ    ,Nil})
    Aadd(aApont,{"D3_CHAVE"  ,SD3->D3_CHAVE     ,Nil})
    Aadd(aApont,{"D3_CF"     ,"PR0"             ,Nil})
    aAdd(aApont,{"INDEX"     , 4                ,Nil})
    MsExecAuto({|x,y| MATA250(x,y)},aApont,5)
    If lMsErroAuto
        DisarmTransaction()
        Mostraerro()


    EndIf

    IF lMsErroAuto
        MSGALERT("DEU MERDA")
        MOSTRAERROR()
    ENDIF