#INCLUDE "PROTHEUS.CH"
#INCLUDE "FWMVCDEF.CH"


User Function DLP73F04()

    lOCAL aArea := GETAREA()
    //Local cRetLeg :="ENABLE"
    Local cRetLeg :="DISABLE"
    lOCAL cAlias := "AD1"
    Local aAreaSX2 	:= SX2->( GetArea() )
    Local aChave	:= {"",""}
    Local cChave	:= ""
    nRecNo := ( cAlias )->( RecNo() )

    // If !Empty( cAlias )
    DbSelectArea( "SX2" )
    DbSetOrder( 1 )
    If SX2->( DbSeek( cAlias ) ) .AND. !Empty( SX2->X2_UNICO )
        ( cAlias )->( DBGoTo( nRecNo ) )
        cChave := XFILIAL("AOB")+cAlias+( cAlias )->&( SX2->X2_UNICO )
        //   aChave := {cAlias, cChave}
    EndIf
    /*POSICIONO PARA SABER SE EXISTE ANOTAÇÃO SE ACHAR TEM*/
    DbSelectArea( "AOB" )
    AOB->(DbSetOrder( 2 )) //AOB_FILIAL, AOB_ENTIDA, AOB_CHAVE, R_E_C_N_O_, D_E_L_E_T_

    If AOB->( DbSeek( cChave ) )

        cRetLeg :="FOLDER11"
    ELSE

        cRetLeg :=  "FOLDER14"
    EndIf
    RestArea( aArea )
    RestArea( aAreaSX2 )


    CONOUT("TESTE")


    //AOB_FILIAL, AOB_ENTIDA, AOB_CHAVE, R_E_C_N_O_, D_E_L_E_T_
    /*  dbSelectArea("AOB")
    AOB->(DbSetOrder(2))
    IF AOB->(MsSeek(xFilial('AOB')+"AD1"+AD1->AD1_FILIAL + AD1->AD1_NROPOR))

        //cRetLeg :="BPMSDOCA"
        cRetLeg :="F11_NULL_OCEAN.BMP"

    ELSE

        //cRetLeg :="BPMSDOCE"
        //cRetLeg :="F8_NULL"
        cRetLeg :="F7_NULL_OCEAN.BMP"
    ENDIF
    // BPMSDOCA_OCEAN.PNG
    // BPMSDOCE.PNG*/

RETURN cRetLeg
