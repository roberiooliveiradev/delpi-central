#Include 'Protheus.ch'

User Function COMCOLF4()

    Local cForn := PARAMIXB[1]
    Local cLoja := PARAMIXB[2]
    Local cPrd  := PARAMIXB[3]

    Local cTes := PARAMIXB[4]
    if cEmpAnt == "05" .AND. ALLTRIM(SDS->DS_TIPO) == "B"
        cTes := "085"
        //Customizações do cliente
    endif
Return cTes
