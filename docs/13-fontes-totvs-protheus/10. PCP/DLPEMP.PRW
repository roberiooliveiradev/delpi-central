#include 'protheus.ch'
#include 'topconn.ch'
#include 'parmtype.ch'
#Include 'TBICONN.ch'


USER FUNCTION DLPEMP()
Local cSql := ""
Local cEol := chr(10)
Local aOps := {}

cSql :="SELECT DISTINCT TOP 10 A.D4_OP                     " + cEol
cSql +="FROM dbo.SD4010 A (NOLOCK)                  " + cEol
cSql +="WHERE A.D_E_L_E_T_ = ''                     " + cEol
cSql +="      AND A.D4_FILIAL = '01'                " + cEol
cSql +="      AND A.D4_LOCAL = '99'                 " + cEol
cSql +="      AND A.D4_COD BETWEEN '' AND 'ZZZZZZZ' " + cEol
cSql +="      AND A.D4_OP  BETWEEN '' AND 'ZZZZZZZ' " + cEol
cSql +="      AND D4_DATA  BETWEEN '' AND 'ZZZZZZZ' " 

conout(cSql)
If Select("TRB004") <> 0
    dbSelectArea("TRB004")
    dbCloseArea()
EndIf

TCQUERY cSql NEW ALIAS "TRB004"

While TRB004->(!EOF())
aadd(aOps,TRB004->D4_OP)
TRB004->(dbSkip())

enddo
IF LEN(aOps) > 0 
u_Zera381Aut(aOps)
endif
RETURN

User Function Zera381Aut(aOps)
Local aCab   := {}
Local aItens := {}

PRIVATE lMsErroAuto := .F.
for nXI := 1 To len(aOps)
conout(aOps[nXI])

    //Monta o cabeçalho com as informações da ordem de produção que terá os empenhos zerados.
    //O parâmetro AUTZERAEMP identifica que será realizado o processo de zerar empenhos.
    aCab := {{"D4_OP", aOps[nXI] , NIL},;
            {"AUTZERAEMP",.T.,Nil},;
            {"INDEX",2,Nil}}

    //Executa o MATA381 com a operação 4, e o indicador para zerar os empenhos.
    MSExecAuto({|x,y,z| mata381(x,y,z)},aCab,aItens,4)
    If lMsErroAuto
        //Se ocorrer erro.
        MostraErro()
    Else
        //Processamento realizado com sucesso
        Alert("Empenhos zerados com sucesso.")
    EndIf
Next nXI
Return