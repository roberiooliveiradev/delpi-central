#INCLUDE "PROTHEUS.CH"
#INCLUDE "TOPCONN.CH"
#INCLUDE "rwmake.ch"


/*/{Protheus.doc} MT241GRV

    LOCALIZAÇÃO :  função A241GRAVA (Gravação do movimento)

    EM QUE PONTO : Após a gravação dos dados (aCols) no SD3, e tem a finalidade de atualizar algum arquivo ou campo.
    Envia vetor com os parâmetros:
    PARAMIXB[1] = Número do Documento
    PARAMIXB[2] = Vetor bidimensional com nome campo/valor do campo (somente será enviado se o Ponto de Entrada MT241CAB for utilizado).

    Programa Fonte MATA241.PRX

    @author  Gabriel
    @since   26-02-2021
/*/


USER FUNCTION MT241GRV()
    Local aArea := GetArea()

    dbselectarea("SF5")
    DBSETORDER(1)

    IF SF5->(MsSeek(xFilial("SF5")+cTM))
        if SF5->F5_TIPO $ "R"
            FWMsgRun( ,{||  U_DLP02F01("MATA241")},"Processando...")
        endif
    endif

    Pergunte("MTA240",.F.)

    restarea(aArea)
rETURN NIL
