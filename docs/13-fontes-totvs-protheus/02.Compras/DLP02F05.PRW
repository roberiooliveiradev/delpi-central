#include 'protheus.ch'
#include 'topconn.ch'
#include 'parmtype.ch'

/*/{Protheus.doc} DLP02F05
Rotina para realizar transferencia do armazem 01 para o 99 quando for produto do tipo MP e Empresa 05
@author Gabriel Araujo
@since 05/2021
/*/

User function DLP02F05(cFil, cDoc, cSerNF, cCodFor, cLjFor)
    Local aArea := getarea()
    Local cEol := chr(10)
    Local cSql := fGetQuery(cFil, cDoc, cSerNF, cCodFor, cLjFor)
    Local aAuto 	:= {}
    Local aItem 	:= {}
    Local aLinha 	:= {}
    Local nOpcAuto  := 3
    Local caSD1Rec 	:= {}
    Local nTMIte    := getsx3cache("D3_ITEM","X3_TAMANHO")
    Local aAreaSD1	:= SD1->(GetArea())
    Local aAreaSB2	:= SB2->(GetArea())
    Local aAreaSD3	:= SD3->(GetArea())

    PRIVATE lMsErroAuto     := .F.

    If Select('TMPSF1') <> 0
        TMPSF1->(dbCloseArea())
    Endif
    nX := 0
    TCQuery cSql Alias TMPSF1 New
    dbSelectArea("SB1")
    dbSelectArea("SB2")
    cDoc := nextnumero("SD3",2,"D3_DOC",.t.) //GetSxeNum("SD3","D3_DOC")
    aadd(aAuto,{cDoc,dDataBase}) //Cabecalho
    While TMPSF1->(!eof())

        aLinha 		:= {}
        //Cabecalho a Incluiradmin
        nX++
        //Origem
        SB1->(DbSetOrder(1))
        SB1->(DbSeek(xFilial("SB1")+PadR(TMPSF1->D1_COD, tamsx3('D3_COD') [1])))

        //NWVERAMZ((cAliasSD2)->D2_COD,'01') //Função Responsável por incluir SB2 e SB9
        SB2->(DbSetOrder(1))
        If	!(SB2->(DbSeek(xFilial('SB2')+SB1->B1_COD+TMPSF1->D1_LOCAL)))
            CriaSB2(SB1->B1_COD,TMPSF1->D1_LOCAL)
        EndIf

        If	!(SB2->(DbSeek(xFilial('SB2')+SB1->B1_COD+'99')))
            CriaSB2(SB1->B1_COD,'99')
        EndIf

        aadd(aLinha,{"ITEM"      ,  StrZero(nX,nTMIte),Nil})
        aadd(aLinha,{"D3_COD"    , SB1->B1_COD, Nil}) //Cod Produto origem
        aadd(aLinha,{"D3_DESCRI" , SB1->B1_DESC, Nil}) //descr produto origem
        aadd(aLinha,{"D3_UM"     , SB1->B1_UM, Nil}) //unidade medida origem
        aadd(aLinha,{"D3_LOCAL"  , TMPSF1->D1_LOCAL, Nil}) //armazem origem
        aadd(aLinha,{"D3_LOCALIZ", criavar('D3_LOCALIZ') ,Nil}) //Informar endereço origem

        aadd(aLinha,{"D3_COD"       , SB1->B1_COD, Nil}) //cod produto destino
        aadd(aLinha,{"D3_DESCRI"    , SB1->B1_DESC, Nil}) //descr produto destino
        aadd(aLinha,{"D3_UM"        , SB1->B1_UM, Nil}) //unidade medida destino
        aadd(aLinha,{"D3_LOCAL"     , '99', Nil}) //armazem destino
        aadd(aLinha,{"D3_LOCALIZ",  criavar('D3_LOCALIZ') ,Nil}) //Informar endereço destino

        aadd(aLinha,{"D3_NUMSERI",  criavar('D3_NUMSERI'), Nil}) //Numero serie
        aadd(aLinha,{"D3_LOTECTL",  criavar('D3_LOTECTL'), Nil}) //Lote Origem
        aadd(aLinha,{"D3_NUMLOTE",  criavar('D3_NUMLOTE'), Nil}) //sublote origem
        aadd(aLinha,{"D3_DTVALID",  criavar('D3_DTVALID'), Nil}) //data validade
        aadd(aLinha,{"D3_POTENCI",  criavar('D3_POTENCI'), Nil}) // Potencia
        aadd(aLinha,{"D3_QUANT"  ,  TMPSF1->D1_QUANT, Nil}) //Quantidade
        aadd(aLinha,{"D3_QTSEGUM",  TMPSF1->D1_QTSEGUM, Nil}) //Seg unidade medida
        aadd(aLinha,{"D3_ESTORNO",   criavar('D3_ESTORNO'), Nil}) //Estorno
        aadd(aLinha,{"D3_NUMSEQ" ,   criavar('D3_NUMSEQ'), Nil}) // Numero sequencia D3_NUMSEQ

        aadd(aLinha,{"D3_LOTECTL", criavar('D3_LOTECTL'), Nil}) //Lote destino
        aadd(aLinha,{"D3_NUMLOTE", criavar('D3_NUMLOTE'), Nil}) //sublote destino
        aadd(aLinha,{"D3_DTVALID", criavar('D3_DTVALID'), Nil}) //validade lote destino
        aadd(aLinha,{"D3_ITEMGRD", criavar('D3_ITEMGRD'), Nil}) //Item Grade
        aadd(aLinha,{"D3_CODLAN" , criavar('D3_CODLAN'), Nil}) //cat83 prod origem
        aadd(aLinha,{"D3_CODLAN" , criavar('D3_CODLAN'), Nil}) //cat83 prod destino

        aAdd(aAuto,aLinha)

        aadd(caSD1Rec,{TMPSF1->RECSD1})

        TMPSF1->(dbskip())
    Enddo

    If Len(aAuto) > 0
        Begin Transaction
            MSExecAuto({|x,y| mata261(x,y)},aAuto,nOpcAuto)

            if lMsErroAuto
                MostraErro()
                DisarmTransaction()
            Else
                AVISO("Sucesso", "Documento de Transferência feito com sucesso : "  + cDoc, { "Fechar" }, 1)
                For x1 := 1 To Len(caSD1Rec)
                    SD1->(Dbgoto(caSD1Rec[x1][1]))
                    RecLock("SD1",.F.)
                    SD1->D1_ZDOC := cDoc //Gravar o número documento
                    SD1->(MsUnLock())
                Next x1
            EndIf
        End Transaction
    EndIf

    RestArea(aAreaSB2)
    RestArea(aAreaSD3)
    RestArea(aAreaSD1)
    RestArea(aArea)

Return


/*/{Protheus.doc} fGetQuery

    Retorna Sql para processamento

    @author  Gabriel Araujo
    @since   31-05-2021
/*/


Static Function fGetQuery(cFil, cDoc, cSerNF, cCodFor, cLjFor)

    Local cEol := chr(10)
    Local cQry := ""
    //+ RetSqlName("SB2") + "
    cQry := "SELECT SD1.R_E_C_N_O_[RECSD1],SD1.* "                             + cEol
    cQry += "   FROM dbo."+ RetSqlName("SD1") + " SD1 (NOLOCK) "               + cEol
    cQry += "       JOIN dbo."+ RetSqlName("SF4") + " SF4 (NOLOCK) "           + cEol
    cQry += "           ON SF4.D_E_L_E_T_     = '' "                           + cEol
    cQry += "               AND SF4.F4_FILIAL = " + VALTOSQL(XFILIAL("SF4"))   + cEol
    cQry += "               AND SF4.F4_CODIGO = SD1.D1_TES "                   + cEol
    cQry += "       JOIN dbo."+ RetSqlName("SB1") + "  SB1 (NOLOCK) "          + cEol
    cQry += "           ON SB1.D_E_L_E_T_     = '' "                           + cEol
    cQry += "               AND SB1.B1_FILIAL = " + VALTOSQL(XFILIAL("SB1"))   + cEol
    cQry += "               AND SB1.B1_COD    = SD1.D1_COD "                   + cEol
    cQry += "WHERE SD1.D_E_L_E_T_ = '' "                                       + cEol
    cQry += "           AND SD1.D1_FILIAL   = " + VALTOSQL(cFil)               + cEol
    cQry += "           AND SD1.D1_DOC      = " + VALTOSQL(cDoc)               + cEol
    cQry += "           AND SD1.D1_SERIE    = " + VALTOSQL(cSerNF)             + cEol
    cQry += "           AND SD1.D1_FORNECE  = " + VALTOSQL(cCodFor)            + cEol
    cQry += "           AND SD1.D1_LOJA     = " + VALTOSQL(cLjFor)             + cEol
    cQry += "           AND SD1.D1_LOCAL    = '01'  "                          + cEol
    cQry += "           AND SB1.B1_TIPO     = 'MP'  "                          + cEol
    cQry += "           AND SF4.F4_ESTOQUE  = 'S'   "                          + cEol


Return cQry
