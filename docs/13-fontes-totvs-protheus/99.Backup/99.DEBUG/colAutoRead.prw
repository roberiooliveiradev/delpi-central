#Include "Protheus.ch"

//-----------------------------------------------------------------
/*/{Protheus.doc} colAutoRead
Execucao do processo de leitura dos arquivos recebidos via TOTVS Colaboração 2.0.

@author  Rafael Iaquinto
@since   24/07/2014
@version 11.8
/*/
//-----------------------------------------------------------------
Function colAutoRead(aParam) 

Local oComTransmite := Nil 
Local lImpXML       := SuperGetMv("MV_IMPXML",.F.,.F.) .And. CKO->(FieldPos("CKO_ARQXML")) > 0 .And. !Empty(CKO->(IndexKey(5)))
Local cTraCID       := SuperGetMv("MV_XMLCID",.F.,"")
Local cTraCSEC      := SuperGetMv("MV_XMLCSEC",.F.,"")
Local lAgendTra     := AgendTra() //T=Tem agendamento separados / F = Nao tem agendamentos

colReadDocs()

If lImpXML .And. !Empty(cTraCID) .And. !Empty(cTraCSEC) .And. !lAgendTra
    oComTransmite := ComTransmite():New()

    If oComTransmite:TokenTotvsTransmite() 
        //Busca XML no Transmite e grava na CKO
        oComTransmite:XMLTransmite()

        //Atualiza Status
        oComTransmite:UpdStatus()
    Endif
Endif

return 

//-------------------------------------------------------------------
/*/{Protheus.doc} AgendTra
Avalia se possui agendamentos separados para o TOTVS Transmite

@author  Rafael Iaquinto
@since   24/07/2014
@version 12
/*/
//-------------------------------------------------------------------

Static Function AgendTra()

Local lRet      := .F.
Local cQry		:= ""
Local cQryStat  := ""
Local cAliXX1   := GetNextAlias()
Local oFindXX1  := Nil
Local aAgendTra := {"SCHEDIMPTRA","SCHEDUPDTRA"}
Local nAgendTra   := 0

oFindXX1 := FWPreparedStatement():New()

cQry := " SELECT XX1_ROTINA"
cQry += " FROM " + RetSqlName("XX1")
cQry += " WHERE XX1_ROTINA IN (?)"
cQry += " AND XX1_STATUS = '0'"
cQry += " AND D_E_L_E_T_ = ' '"
cQry := ChangeQuery(cQry) 

oFindXX1:SetQuery(cQry) 
oFindXX1:SetIn(1,aAgendTra)

cQryStat := oFindXX1:GetFixQuery()
MpSysOpenQuery(cQryStat,cAliXX1) 

While (cAliXX1)->(!EOF()) 
    nAgendTra+=1
    (cAliXX1)->(DbSkip())
Enddo

If nAgendTra == 2 //Possui 2 agendamento, não precisa executar pelo COLAUTOREAD
    lRet := .T.
Endif

(cAliXX1)->(DbCloseArea())

Return lRet

//-------------------------------------------------------------------
/*/{Protheus.doc} SchedDef
Retorna as perguntas definidas no schedule.

@return aReturn			Array com os parametros

@author  Rafael Iaquinto
@since   24/07/2014
@version 12
/*/
//-------------------------------------------------------------------

Static Function SchedDef()

Local aParam  := {}

aParam := { "P",;			//Tipo R para relatorio P para processo
            "",;	//Pergunte do relatorio, caso nao use passar ParamDef
            ,;			//Alias
            ,;			//Array de ordens
            }				//Titulo

Return aParam
