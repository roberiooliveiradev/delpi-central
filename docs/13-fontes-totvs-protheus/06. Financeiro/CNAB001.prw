#include "rwmake.ch"

User Function CNAB001()


    Local nValor    := 0
    Local nImpostos := 0
    Local _SALDOLIQ :=0

    nImpostos := SomaAbat(SE1->E1_PREFIXO,SE1->E1_NUM,SE1->E1_PARCELA,"R",1,ddatabase,SE1->E1_CLIENTE, SE1->E1_LOJA)


    _SALDOLIQ   :=  SE1->E1_SALDO-nImpostos-SE1->E1_SDDECRE

    if SEE->EE_CODIGO =="001"
        VALOR  :=  STRZERO(((_SALDOLIQ)*100),15)
    ELSE
        VALOR  :=  STRZERO(((_SALDOLIQ)*100),13)
    ENDIF

Return(VALOR)
