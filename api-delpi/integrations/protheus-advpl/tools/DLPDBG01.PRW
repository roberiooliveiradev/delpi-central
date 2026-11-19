/* =================================================================
   DLPDBG01.PRW — Diagnostico: lista os campos do formulario SB1MASTER
   do modelo oficial MATA010 (uma execucao, sem efeito colateral).

   Motivo: FWFormFieldsModel rejeita ids de campo que o formulario nao
   expoe ("O id de formulario 'X' nao e valido") — o erro revela UM
   campo por vez. Este dump enumera TODOS de uma vez para diff offline
   contra o catalogo aB1Fields() do DLP04I01.

   Uso: compilar no RPO do ambiente alvo; executar u_DLPDBG01 via
   TDS/debug. A saida vai ao console do AppServer (ConOut).
   Nao toca em dados — FWLoadModel e somente leitura de metamodelo.
   ================================================================= */

#Include "TOTVS.CH"
#Include "FWMVCDEF.CH"

user function DLPDBG01()

    Local oModel  := NIL
    Local oMaster := NIL
    Local oF      := NIL
    Local nI      := 0
    Local cNome   := ""
    Local cErroBlk := ""
    Local oException := ErrorBlock({|e| cErroBlk := e:Description, Break(e)})

    Begin Sequence

        oModel  := FWLoadModel("MATA010")
        oMaster := oModel:GetModel("SB1MASTER")

        ConOut("DLPDBG01 === SB1MASTER " + ClassName(oMaster) + " ===")

        if __ObjHasData(oMaster, "aFields") .and. ValType(oMaster:aFields) == "A"
            for nI := 1 to len(oMaster:aFields)
                oF    := oMaster:aFields[nI]
                cNome := ""
                if ValType(oF) == "O"
                    if __ObjHasData(oF, "cIdField")
                        cNome := oF:cIdField
                    elseif __ObjHasMethod(oF, "GetID")
                        cNome := oF:GetID()
                    elseif __ObjHasData(oF, "cID")
                        cNome := oF:cID
                    endif
                endif
                ConOut("DLPDBG01 FIELD|" + cValToChar(nI) + "|" + cNome + ;
                    "|" + iif(ValType(oF) == "O", ClassName(oF), ValType(oF)))
            next nI
            ConOut("DLPDBG01 === total: " + cValToChar(len(oMaster:aFields)) + " ===")
        else
            // aFields nao exposto neste build — despeja a lista de dados
            // do objeto para orientar a enumeracao alternativa
            ConOut("DLPDBG01 aFields ausente; dados do objeto:")
            ConOut("DLPDBG01 " + lJoin(__ObjGetDataList(oMaster), ","))
        endif

    Recover
        ConOut("DLPDBG01 ERRO: " + cErroBlk)
    End Sequence

    ErrorBlock(oException)

Return
