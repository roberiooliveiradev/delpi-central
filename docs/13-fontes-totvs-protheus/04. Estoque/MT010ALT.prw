#Include "PROTHEUS.CH"

/*
================================================================================
 MT010ALT  -  Ponto de Entrada pos-confirmacao de ALTERACAO de produto (MATA010)

 Chamado por MATA010EVPE:InTTS quando nOpc == MODEL_OPERATION_UPDATE, ou seja,
 DENTRO da transacao do commit e LOGO APOS o flush padrao do complemento
 (o evento PADRAO/MATA010EVDEF roda antes do evento PE/MATA010EVPE).

 Objetivo:
   Garantir o Indicador de Produto (SBZ) nas DEMAIS filiais com os MESMOS
   defaults aplicados pelo A010TOK, SEM injetar a linha de outra filial no
   modelo do MATA010. Injetar outra filial no modelo torna o commit
   "multi-filial" e, com SB1 Compartilhado x SB5/SBZ Exclusivo, faz o flush
   padrao do complemento gravar na filial errada -> estoura SB5010_UNQ.

   A filial CORRENTE continua sendo tratada pelo A010TOK (via modelo).
   Aqui tratamos somente as filiais <> filial corrente, via gravacao direta.
   O SBZ nao possui gatilho (SX7), portanto a gravacao direta produz o MESMO
   dado da gravacao pelo modelo.

 Autor : Guilherme Pegoraro
 Data  : 21/05/2026
 Ref.  : Erro SB5010 'Cannot insert duplicate key SB5010_UNQ' em
         MATA010EVDEF:InTTS ao alterar produto com complemento em 2+ filiais.
================================================================================
*/
User Function MT010ALT()
    Local aArea := GetArea()
    Local aFil
    Local nX
    Local cProd
    Local cTipo

    // Mesmo gatilho do A010TOK: empresa 01 e tipos MP / PI / PA
    If !( AllTrim(cEmpAnt) $ "01" )
        RestArea(aArea)
        Return
    EndIf

    cProd := SB1->B1_COD
    cTipo := SB1->B1_TIPO

    If !( cTipo $ "MP_PI_PA" )
        RestArea(aArea)
        Return
    EndIf

    aFil := FWAllFilial("", "01")

    For nX := 1 To Len(aFil)
        // Filial corrente ja foi tratada pelo modelo (A010TOK) -> nao repete
        If aFil[nX] == cFilAnt
            Loop
        EndIf
        U_DLPSBZFil(cProd, aFil[nX], cTipo)
    Next nX

    RestArea(aArea)
Return


/*
================================================================================
 DLPSBZFil - Garante o Indicador (SBZ) de um produto numa filial, com os mesmos
             defaults do A010TOK. Idempotente (so preenche campo vazio).

 Para registro NOVO, replica os inicializadores X3 (igual ao oMdlSBZ:AddLine)
 via CriaVar(). SBZ nao tem gatilho (SX7), logo a gravacao direta == modelo.

 Parametros:
   cProd - codigo do produto (BZ_COD)
   cFil  - filial do indicador (BZ_FILIAL)
   cTipo - tipo do produto (B1_TIPO) ; default SB1->B1_TIPO
================================================================================
*/
User Function DLPSBZFil(cProd, cFil, cTipo)
    Local aArea    := GetArea()
    Local aAreaSBZ := SBZ->(GetArea())
    Local ix
    Local lAchou
    Local lAPSFil  := AllTrim( SuperGetMV("MV_APS", .F., "", cFil) ) $ "TOTVS"

    Default cTipo := SB1->B1_TIPO

    // Mesma abrangencia do A010TOK
    If !( cTipo $ "MP_PI_PA" )
        RestArea(aArea)
        Return .T.
    EndIf

    SBZ->( DbSetOrder(1) )                       // BZ_FILIAL + BZ_COD
    lAchou := SBZ->( DbSeek( cFil + cProd ) )

    RecLock("SBZ", !lAchou)

    If !lAchou
        // Registro novo: inicializa como o modelo (AddLine) faria, com inits X3
        For ix := 1 To SBZ->( FCount() )
            SBZ->( FieldPut( ix, CriaVar( SBZ->( FieldName(ix) ), .T. ) ) )
        Next ix
        SBZ->BZ_FILIAL := cFil
        SBZ->BZ_COD    := cProd
    EndIf

    // Defaults identicos ao A010TOK (sempre so preenche campo vazio)
    If cTipo $ "MP" .And. SBZ->BZ_MRP != "S"
        SBZ->BZ_MRP := "S"
    EndIf

    If lAPSFil .And. SBZ->BZ_MRP != "S" .And. cTipo $ "PI_PA"
        If Empty( SBZ->BZ_LOCPAD ) .Or. SBZ->BZ_LOCPAD != "01"
            SBZ->BZ_LOCPAD := "01"
        EndIf
    EndIf

    If cTipo == "MP" .And. Empty( SBZ->BZ_PE )
        If cFil == "01"
            SBZ->BZ_PE := 30
        ElseIf cFil == "02"
            SBZ->BZ_PE := 37
        EndIf
    EndIf

    If cTipo == "MP" .And. Empty( SBZ->BZ_TIPE ) .And. ( cFil == "01" .Or. cFil == "02" )
        SBZ->BZ_TIPE := "D"
    EndIf

    If cTipo $ "PI_PA" .And. Empty( SBZ->BZ_LM )
        SBZ->BZ_LM := IIf( lAPSFil, 0.010, 0.001 )
    EndIf

    If cTipo $ "PI_PA" .And. Empty( SBZ->BZ_LE )
        SBZ->BZ_LE := IIf( lAPSFil, 0.010, 0.001 )
    EndIf

    SBZ->( MsUnlock() )

    RestArea(aAreaSBZ)
    RestArea(aArea)
Return .T.
