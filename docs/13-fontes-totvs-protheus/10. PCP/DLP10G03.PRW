#include "protheus.ch"
#include "parmtype.ch"



//user function para calculo da produtividade em tela no apontamento de produção, rotina Produção Mod2
//Deivid da cruz 23/02/2024

User function DLP10G03()

    // TEMPO ESTIMADO = G2_TEMPAD * H6_QTDPROD
    // TEMPO DE SETUP = G2_SETUP
    // ROTEIRO = C2_ROTEIRO
    // PRODUTIVIDADE = (TEMPO ESTIMADO + TEMPO DE SETUP) / H6_TEMPO * 100

    LOCAL cQuery:= ""
    LOCAL cQuery1:= ""
    LOCAL NTMPEST :=0
    LOCAL NTMPAD :=0
    LOCAL NEFICIENCIA :=0
    LOCAL NROTEIRO:=0
    LOCAL NTEMPMIN:=0
    LOCAL NTEMPHOR:=0

    cQuery1 +="SELECT C2_NUM, C2_ROTEIRO"
    cQuery1 +=" FROM "+RetSqlName("SC2")+ " SC2"
    cQuery1 +=" WHERE SC2.D_E_L_E_T_<> '*'AND C2_NUM ='"+SUBSTRING(M->H6_OP,1,6)+"'"
    cQuery += " AND C2_FILIAL ='"+XFILIAL("SC2")+"'"
    cQuery1 +=" AND C2_ITEM='"+SUBSTRING(M->H6_OP,7,2)+"'"
    cQuery1 +=" AND C2_SEQUEN='"+SUBSTRING(M->H6_OP,9,3)+"'"

    MPSysOpenQuery( cQuery1, 'SqlQuery1' )

    NROTEIRO := SqlQuery1->C2_ROTEIRO

    cQuery := ""
    cQuery += "SELECT G2_FILIAL, G2_CODIGO,G2_PRODUTO,G2_OPERAC,G2_TEMPAD,G2_SETUP"
    cQuery += " FROM "+RetSqlName("SG2")+" SG2 "
    cQuery += " WHERE SG2.D_E_L_E_T_<> '*' AND G2_FILIAL ='"+XFILIAL("SG2")+"'"
    cQuery += " AND G2_CODIGO= '"+NROTEIRO+"'"
    cQuery += " AND G2_PRODUTO ='"+M->H6_PRODUTO+"'"
    cQuery += " AND G2_OPERAC ='"+M->H6_OPERAC+"'"
    cQuery += " ORDER BY G2_FILIAL, G2_CODIGO,G2_PRODUTO,G2_OPERAC"

    MPSysOpenQuery( cQuery, 'SqlQuery' )

    NTMPEST := SqlQuery->G2_TEMPAD * M->H6_QTDPROD
    NTMPAD:=SqlQuery->G2_SETUP

    nPosIni := AT(":","000:10")+1

    NTEMPMIN := val(substr(M->H6_TEMPO,nPosIni,2))
    NTEMPMIN := NTEMPMIN/60
    NTEMPMIN := noround(NTEMPMIN)

    nPosFim :=  AT(":","000:10")-1

    NTEMPHOR := val(substr(M->H6_TEMPO,1, nPosFim))
    NTEMREAL := NTEMPHOR+NTEMPMIN

    NEFICIENCIA := ROUND(((NTMPEST + NTMPAD) / NTEMREAL) * 100, 2)

    RECLOCK( "SH6", .F. )
    M->H6_ZEFICI:=NEFICIENCIA
    SH6->(MSUNLOCK())

    SqlQuery->(DBCLOSEAREA())
    SqlQuery1->(DBCLOSEAREA())


RETURN
