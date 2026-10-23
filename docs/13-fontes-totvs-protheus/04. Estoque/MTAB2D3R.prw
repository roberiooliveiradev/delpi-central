#include "protheus.ch"

/*
ÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜÜ
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
±±ÉÍÍÍÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍËÍÍÍÍÍÍÑÍÍÍÍÍÍÍÍÍÍÍÍÍ»±±
±±ºPrograma  ³MTAB2D3R  ºAutor  ³Microsiga           º Data ³  03/12/12   º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÊÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºDesc.     ³ Complementa gravação no arquivo de saldos                  º±±
±±º          ³ (executado DEPOIS da gravação do SB2).                     º±±
±±ÌÍÍÍÍÍÍÍÍÍÍØÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¹±±
±±ºUso       ³ P10                                                        º±±
±±ÈÍÍÍÍÍÍÍÍÍÍÏÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍÍ¼±±
±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±±
ßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßßß
*/

User Function MTAB2D3R()

    conout("stop")
    //Local aArea:= getarea()
    // Local     nTMLocal := getsx3cache("B2_LOCAL","X3_TAMANHO")

    // Local lOpcAuto      := .T.
    // PRIVATE lMsErroAuto := .F.
    // //Private lMsHelpAuto	:= .T.
    // //Private lAutoErrNoFile  := .T.

    // cCodPro := SD3->D3_COD

    // dbSelectArea("SB1")
    // SB1->(dbSetOrder(1))
    // SB1->(dbSeek(xFilial("SB1")+cCodPro))
    // cGrupo := SB1->B1_GRUPO
    // cTipo := SB1->B1_TIPO

    // conout("MT340D3 - ENTROU NA ROTINA Ç" )

    // aParametros :={}

    // AADD(aParametros, cCodPro)                 //  | mv_par01  || Produto de
    // AADD(aParametros, cCodPro)     //  | mv_par02  || Produto ate
    // AADD(aParametros, cGrupo )    //  | mv_par03  || Grupo de
    // AADD(aParametros, cGrupo)     //  | mv_par04  || Grupo ate
    // AADD(aParametros, cTipo)   //  | mv_par05  || Tipo de
    // AADD(aParametros, cTipo)   //  | mv_par06  || Tipo ate
    // AADD(aParametros, SPACE(nTMLocal))             //  | mv_par07  || Local de
    // AADD(aParametros, REPLICATE("Z",nTMLocal))     //  | mv_par08  || Local ate
    // AADD(aParametros, 1)                           //  | mv_par09  || Considera Necess Bruta 1 sim Pto Pedido
    // AADD(aParametros, 2)                           //  | mv_par10  || Saldo Neg Considera    1 sim Lot.Economico
    // AADD(aParametros, STOD("20491231"))            //  | mv_par11  || Data limite p/ empenhos
    // AADD(aParametros, 2)                           //  | mv_par12  || Cons.Qtd. De 3os.? Sim / Nao
    // AADD(aParametros, 2)                           //  | mv_par13  || Cons.Qtd. Em 3os.? Sim / Nao
    // AADD(aParametros, 1)                           //  | mv_par14  || Ao atingir Estoque Maximo ?  1=Qtde. Original; 2=Ajusta Est. Max
    // AADD(aParametros, 2)                           //  | mv_par15  || Quebra SC por Lote Econmico?
    // AADD(aParametros, 2)                           //  | mv_par16  || Qtd.PV nao Liberado?" Subtr/Ignora
    // AADD(aParametros, SPACE(nTMLocal))             //  | mv_par17  || Considera Saldo Armazem de
    // AADD(aParametros, REPLICATE("Z",nTMLocal))     //  | mv_par18  || Considera Saldo Armazem ate
    // AADD(aParametros, 2)                           //  | mv_par19  || Seleciona Filiais? (Sim/Nao)
    // AADD(aParametros, 2)                           //  | mv_par20  || Gera SC por produto(Sim/Nao)
    // AADD(aParametros, 1)                           //  | mv_par21  || Considera Est. Seguranca ?  (Sim / Nao)
    // AADD(aParametros, 1)                           //  | mv_par22  || Prioriza geração de         (1-Sol.Compra/2-Ped.Compra)

    // lMsErroAuto     := .F.

    // MSExecAuto({|x, y| mata170(x, y)},lOpcAuto, aParametros)

    // If lMsErroAuto
    //     cErro  := ""
    //     //  aLogAuto    := GetAutoGrLog()

    //     //  For nY := 1 To Len(aLogAuto)
    //     //      cErro += aLogAuto[nY] + CRLF
    //     //  Next nY
    //     conout(cErro)

    // Endif
    //restarea(aArea)

Return
