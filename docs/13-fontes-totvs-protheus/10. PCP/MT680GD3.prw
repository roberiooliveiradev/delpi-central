#INCLUDE "TOTVS.CH"
/*DESATIVADO*/

user function MT680GD3()


    //conout("MT680GD3")


    //sDesRec := ""
    //cCDRec := ""
    //cOPApont := ""
    //cPrdPA := ""
    //cPrdApont := ""
    //cTpApon   := ""
    //cDescAp   := ""
    //cCDUsr := ""
    //dDtApont := ctod("")
    //cHrApont := ""
    ///*Busca Codigo do Recurso*/
    //// nPos := aScan(aDados, {|x| x[1] == "H6_RECURSO"})
    //cCDRec      :=  SH6->H6_RECURSO//  aDados[nPos][2]

    ///*Busca PA da OP */
    //// nPos := aScan(aDados, {|x| x[1] == "H6_OP"})
    //cOPApont :=    SH6->H6_OP


    //cOpPA := substr( cOPApont,1,6)+"01001"
    //dbSelectArea("SC2")
    //SC2->(dbSetOrder(1))
    //If   SC2->(dBSeek(xFilial("SC2")+cOpPA))
    //    cPrdPA:= SC2->C2_PRODUTO
    //endif


    ///*Op Apontamento*/

    //dbSelectArea("SC2")
    //SC2->(dbSetOrder(1))
    //If   SC2->(dBSeek(xFilial("SC2")+cOPApont))
    //    cPrdApont := SC2->C2_PRODUTO
    //    cTpApon     :=  posicione("SB1",1,XFILIAL("SB1")+SC2->C2_PRODUTO,"B1_TIPO" )
    //    cDescAp     :=  posicione("SB1",1,XFILIAL("SB1")+SC2->C2_PRODUTO,"B1_DESC" )
    //endif

    ///*Quantidade */
    ////nPos := aScan(aDados, {|x| x[1] == "H6_QTDPROD"})
    //nQtd := SH6->H6_QTDPROD *1000

    //DbSelectArea("SH1")
    //SH1->( DbSetOrder(1))
    //IF SH1->(DbSeek(xFilial('SH1')+cCDRec))
    //    sDesRec := SH1->H1_DESCRI
    //EndIf

    //// nPos := aScan(aDados, {|x| x[1] == "H6_OPERADO"})
    //cCDUsr := SH6->H6_OPERADO


    //// nPos := aScan(aDados, {|x| x[1] == "H6_DTAPONT"})
    //dDtApont   := SH6->H6_DTAPONT

    //// nPos := aScan(aDados, {|x| x[1] == "H6_HORAFIN"})
    //cHrApont   := SH6->H6_HORAFIN
    //conout("cPrdPA   ->"      +cPrdPA)
    //conout("cPrdApont->"    +cPrdApont)
    //conout("cOPApont ->" +cOPApont)
    //conout("cTpApon  ->"  +cTpApon)
    //conout("cDescAp  ->"  +cDescAp )
    //conout("nQtd ->" + cvaltochar(nQtd))
    //conout("cCDRec ->"   +cCDRec )
    //conout("sDesRec ->"  +sDesRec)
    //conout("cCDUsr ->"   +cCDUsr)
    //conout("dDtApont ->" +dtoc(dDtApont))
    //conout("cHrApont ->"+    cHrApont)
    //if SH6->H6_OPERAC == '01' .and. SH6->H6_FILIAL == '02'

    //    U_DLP10F09(cPrdPA,cPrdApont,cOPApont,cTpApon,cDescAp,nQtd,cCDRec,sDesRec,cCDUsr,dDtApont,cHrApont)

    //ENDIF
Return .t.
