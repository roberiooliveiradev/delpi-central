#include 'protheus.ch'
#include 'parmtype.ch'
#Include "TOTVS.ch"
#INCLUDE "TOPCONN.CH"
#INCLUDE "FWBROWSE.CH"
#INCLUDE "RWMAKE.CH"
#INCLUDE "FWMVCDEF.CH"
#Include "RwMake.ch"
#include "fileio.ch"


user function COLF1D1()
    Local aCab := PARAMIXB[1]
    Local aItens := PARAMIXB[2]
    Local aRet := {}
    Local aArea		:= GetArea()
    Local aAreaSDT	:= SDT->(GetArea())
    Local aAreaSC7	:= SC7->(GetArea())
    Local nPosFor  		:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_FORNECE"})
    Local nPosLoj  		:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_LOJA"})

    Local nPosDoc    	:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_DOC"})
    Local nPosSerie    	:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_SERIE"})
    Local nPosFil		:= aScan(aCab,{|x| AllTrim(x[1]) == "F1_FILIAL"})
    Local n1
    Local  nTotSDT := 0.00
    //Customizações do cliente
    /*  DT_FILIAL, DT_FORNEC, DT_LOJA, DT_DOC, DT_SERIE, DT_PRODFOR, R_E_C_N_O_, D_E_L_E_T_
    |    DT_FILIAL, DT_FORNEC, DT_LOJA, DT_DOC, DT_SERIE, DT_COD, R_E_C_N_O_, D_E_L_E_T_
    */

    DbSelectArea("SDT")
    SDT->(dbSetOrder(8))
    dbSelectArea("SA2")
    SA2->(DbSetOrder(1))

    SA2->(DbSeek(xFilial("SA2")+aCab[nPosFor,2]   +aCab[nPosLoj,2] ))
    cGrTrib := ALLTRIM(SA2->A2_GRPTRIB)

    For n1 := 1 to Len(aItens)
        nPItem		:= aScan(aItens[n1],{|x| AllTrim(x[1]) == "D1_ITEM"})
        nPVLICMS		:= aScan(aItens[n1],{|x| AllTrim(x[1]) == "D1_VALICM"})
        nPPICMS		:= aScan(aItens[n1],{|x| AllTrim(x[1]) == "D1_PICM"})
        nPVLIPI		:= aScan(aItens[n1],{|x| AllTrim(x[1]) == "D1_VALIPI"})
        nPVLrUni		:= aScan(aItens[n1],{|x| AllTrim(x[1]) == "D1_VUNIT"})
        nPCC		:= aScan(aItens[n1],{|x| AllTrim(x[1]) == "D1_CC"})
        nTPot		:= aScan(aItens[n1],{|x| AllTrim(x[1]) == "D1_TOTAL"})
        aDadosPC := {}

        if nPItem >0
            //DT_FILIAL, DT_FORNEC, DT_LOJA, DT_DOC, DT_SERIE, DT_ITEM, R_E_C_N_O_, D_E_L_E_T_
            IF   SDT->(dbSeek(       aCab[nPosFil,2]   +aCab[nPosFor,2]   +aCab[nPosLoj,2]   +aCab[nPosDoc,2];
                    +aCab[nPosSerie,2]   + aItens[n1,nPItem,2]  ))
                nTotSDT += SDT->DT_TOTAL

                IF !EMPTY(SDT->DT_PEDIDO)
                    aDadosPC := GetAdvFval("SC7",{"C7_QUANT","C7_PRECO","C7_MOEDA","C7_TXMOEDA","C7_TOTAL","C7_COND","C7_PICM","C7_VALICM","C7_CC"},xFilial("SF1") + PadR(SDT->DT_PEDIDO,TamSx3("C7_NUM")[1]) + PadR(SDT->DT_ITEMPC,TamSx3("C7_ITEM")[1]),1)
                    if nPVLrUni == 0
                        aAdd(aItens[n1],{"D1_VUNIT", aDadosPC[2],	 NIL})
                    ELSE
                        aItens[n1][nPVLrUni][2]:=aDadosPC[2]
                    endif
                endif
                /*C7_CC */
                if len(aDadosPC)
                    if nPCC == 0
                        aAdd(aItens[n1],{"D1_CC", aDadosPC[9],	 NIL})
                    else
                        aItens[n1][nPCC][2]:=aDadosPC[9]
                    endif
                endif


                IF	!("SN" $ ALLTRIM(UPPER(cGrTrib))  )
                    if nPVLICMS == 0
                        aAdd(aItens[n1],{"D1_VALICM", SDT->DT_XMLICM,	 NIL})
                    else
                        aItens[n1][nPVLICMS][2]:=SDT->DT_XMLICM
                    endif
                ELSE
                    if len(aDadosPC)>0

                        //      C7_QUJE,C7_FILIAL,C7_TIPO,C7_ITEM,C7_PRODUTO,C7_DESCRI,C7_UM,C7_SEGUM,C7_EMBAL,C7_QUANT,C7_QTSEGUM,C7_PRECO,C7_TOTAL,C7_TES,C7_DATPRF,C7_BASEIPI,C7_IPI,C7_VALIPI,C7_PICM,C7_VALICM,C7_NUMSC,C7_COND,C7_CONTATO,C7_OBS,C7_ITEMSC,C7_LOCAL,C7_FORNECE,C7_EMISSAO,C7_NUM,C7_CC,C7_CONTA,C7_ITEMCTA,C7_LOJA,C7_FILENT,C7_DESC1,C7_DESC2,C7_DESC3,C7_QUJE,C7_REAJUST,C7_FRETE,C7_TX,C7_EMITIDO,C7_TPFRETE,C7_ENCER,C7_OP,C7_QTDREEM,C7_CODLIB,C7_RESIDUO,C7_NUMCOT,C7_MSG,C7_CONTROL,C7_IPIBRUT,C7_VLDESC,C7_SEQUEN,C7_NUMIMP,C7_ORIGEM,C7_QTDACLA,C7_VALEMB,C7_FLUXO,C7_TPOP,C7_APROV,C7_CONAPRO,C7_GRUPCOM,C7_USER,C7_STATME,C7_OK,C7_QTDSOL,C7_DESC,C7_BASEICM,C7_SEGURO,C7_DESPESA,C7_TXMOEDA,C7_VALFRE,C7_MOEDA,C7_PENDEN,C7_CLVL,C7_BASEIR,C7_ALIQIR,C7_VALIR,C7_ICMCOMP,C7_SEQMRP,C7_ICMSRET,C7_CODORCA,C7_DTLANC,C7_CODTAB,C7_CODCRED,C7_TIPOEMP,C7_ESPEMP,D_E_L_E_T_,R_E_C_N_O_,R_E_C_D_E_L_,C7_BASESOL,C7_VALSOL,C7_TRANSP,C7_CONTRA,C7_CONTREV,C7_PLANILH,C7_MEDICAO,C7_ITEMED,C7_FREPPCC,C7_POLREPR,C7_DT_IMP,C7_PERREPR,C7_AGENTE,C7_GRADE,C7_ITEMGRD,C7_FORWARD,C7_TIPO_EM,C7_ORIGIMP,C7_DEST,C7_COMPRA,C7_PESO_B,C7_INCOTER,C7_IMPORT,C7_CONSIG,C7_CONF_PE,C7_DESP,C7_EXPORTA,C7_LOJAEXP,C7_CONTAIN,C7_MT3,C7_CONTA20,C7_CONTA40,C7_CON40HC,C7_ARMAZEM,C7_FABRICA,C7_LOJFABR,C7_DT_EMB,C7_TEC,C7_EX_NCM,C7_EX_NBM,C7_DIACTB,C7_NODIA,C7_RATEIO,C7_FILCEN,C7_ACCNUM,C7_ACCITEM,C7_ACCPROC,C7_ESTOQUE,C7_CODED,C7_PO_EIC,C7_NUMPR,C7_DINICQ,C7_DINITRA,C7_DINICOM,C7_RESREM,C7_NUMSA,C7_REVISAO,C7_IDTSS,C7_TPCOLAB,C7_ALIQISS,C7_VALISS,C7_BASECSL,C7_ALQCSL,C7_VALINS,C7_ALIQINS,C7_CODRDA,C7_LOTPLS,C7_VALCSL,C7_BASEISS,C7_FISCORI,C7_RATFIN,C7_BASEINS,C7_SOLICIT,C7_BASIMP5,C7_BASIMP6,C7_VALIMP5,C7_VALIMP6,C7_FILEDT,C7_GCPIT,C7_GCPLT,C7_CODNE,C7_ITEMNE,C7_DIREITO,C7_PLOPELT,C7_OBRIGA,C7_OBSM,C7_TIPCOM,C7_RETENCA,C7_QUJEFAT,C7_QUJERET,C7_DEDUCAO,C7_QUJEDED,C7_FATDIRE,C7_FRETCON,C7_TRANSLJ,C7_IDTRIB,C7_VALPIS,C7_VALCOF,C7_BASPIS,C7_ALQCOF,C7_ALQPIS,C7_BASCOF,C7_ALQPS2,C7_ALQCF2,S_T_A_M_P_,C7_MSUIDT
                        if nPVLICMS == 0
                            aAdd(aItens[n1],{"D1_VALICM",  aDadosPC[8],	 NIL})
                        else
                            aItens[n1][nPVLICMS][2]:= aDadosPC[8]
                        endif
                        //D1_PICM
                        if nPPICMS == 0
                            aAdd(aItens[n1],{"D1_PICM", aDadosPC[7],	 NIL})
                        else
                            aItens[n1][nPPICMS][2]:=aDadosPC[7]
                        endif
                    endif
                    if nPVLIPI == 0
                        aAdd(aItens[n1],{"D1_VALIPI", SDT->DT_XMLIPI,	 NIL})
                    else
                        aItens[n1][nPVLIPI][2]:=SDT->DT_XMLIPI
                    endif
                    //  aAdd(aItens,{"D1_ITEMPC", SDT->DT_ITEMPC,	 NIL})

                    aRet := {aCab,aItens}
                ENDIF
            ENDIF
        ENDIF

    Next n1

    DbSelectArea("SDS")
    SDS->(DbSetOrder(1))
    If SDS->(DbSeek(  aCab[nPosFil,2]  +aCab[nPosDoc,2]+aCab[nPosSerie,2]+;
            aCab[nPosFor,2]+aCab[nPosLoj,2]))//Filial + RPS + SERIE RPS + FORNECEDOR + LOJA
        nDif :=  SDS->DS_VALMERC - nTotSDT
        if nDif != 0.00

            aItens[1][nTPot][2]+=nDif
            conout("entrou no ultimo")
        endif
    endif
    RESTAREA(aArea)
    RESTAREA(aAreaSDT)
    RESTAREA(aAreaSC7)
Return aRet

