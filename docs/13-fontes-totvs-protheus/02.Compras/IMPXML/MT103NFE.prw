#Include 'Protheus.ch'
#Include 'TOPConn.ch'
#Include "FILEIO.CH"
#Include "TbiConn.ch"

user function MT103NFE()
    Local n1
    xOPC := paramixb
    if IsInCallStack("COMXCOL") .and. xOPC ==  3 .and. len(aAutoCab)>0
        conout("stop")
        xNFiscal    := aAutoCab[ProcH("F1_DOC"),2]
        xSerDoc     := aAutoCab[ProcH("F1_SERIE"),2]
        xLojaFor := aAutoCab[ProcH("F1_LOJA"),2]
        xFornece := aAutoCab[ProcH("F1_FORNECE"),2]

        // GDFieldPos("DT_ITEMORI",aHeader)
        For n1 := 1 to Len(aAutoItens)
            aRetItem:= FGETITENS(xNFiscal ,xSerDoc  ,xLojaFor ,xFornece )
            // aScan(aAutoItens[1],{|x| AllTrim(x[1]) == "D1_SERIORI"})
            nPosITSD1 := aScan(aAutoItens[1],{|x| AllTrim(x[1]) == "D1_ITEM"})
            nPosITRet := 1 //ascan(aRetItem,{|x| Trim(x[2]) == "DT_ITEM"})
            if nPosITRet>0 .AND. nPosITSD1 > 0 .and. len(aRetItem)>0
                if aRetItem[nPosITRet][1]==aAutoItens[n1][nPosITSD1][2]

                    aAdd(aTail(aAutoItens[N1]),{"D1_NFORI",  aRetItem[nPosITRet][2],	 NIL})
                    aAdd(aTail(aAutoItens[N1]),{"D1_SERIORI", aRetItem[nPosITRet][3], NIL})
                    aAdd(aTail(aAutoItens[N1]),{"D1_ITEMORI", aRetItem[nPosITRet][4], NIL})
                endif
            endif
        Next n1
    endif
Return NIl

STATIC FUNCTION FGETITENS(xNFiscal ,xSerDoc  ,xLojaFor ,xFornece )
    Local cEOL := chr(10)
    Local aArea := GetArea()
    Local aRetItem := {}
    Local cTMPSDT		:= GetNextAlias()
    cQry	:= " SELECT * FROM SDT010 SDT (NOLOCK) " + cEOL
    cQry 	+= "    WHERE  SDT.D_E_L_E_T_ = '' " + cEOL
    cQry 	+= "        AND SDT.DT_FILIAL   =  " + VALTOSQL(xFilial("SF1")) + cEOL
    cQry 	+= "        AND SDT.DT_DOC      =  " + VALTOSQL(xNFiscal) + cEOL
    cQry 	+= "        AND SDT.DT_SERIE    =  " + VALTOSQL(xSerDoc) + cEOL
    cQry 	+= "        AND SDT.DT_FORNEC   =  " + VALTOSQL(xFornece) + cEOL
    cQry 	+= "        AND SDT.DT_LOJA     =  " + VALTOSQL(xLojaFor) + cEOL
    cQry 	+= "        AND SDT.DT_CHVNFO  !=     ''"
    cQry 	+= " ORDER BY DT_ITEM "


    cQry := ChangeQuery(cQry)

    dbUseArea(.T.,"TOPCONN",TCGenQry(,,cQry),cTMPSDT,.T.,.T.)

    While (cTMPSDT)->(!EOF())

        aadd(aRetItem,{(cTMPSDT)->DT_ITEM ,(cTMPSDT)->DT_NFORI,	(cTMPSDT)->DT_SERIORI,	(cTMPSDT)->DT_ITEMORI, (cTMPSDT)->DT_CHVNFO})

        (cTMPSDT)->(DbSkip())
    ENDDO

    (cTMPSDT)->(DbCloseArea())

    RestArea(aArea)



Return aRetItem

Static Function ProcH(cCampo)
Return aScan(aAutoCab,{|x|Trim(x[1])== cCampo })
