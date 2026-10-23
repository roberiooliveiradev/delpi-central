#include 'rwmake.ch'
#include 'topconn.ch'
#INCLUDE 'SET.CH'
#INCLUDE 'protheus.CH'
#Include 'FWMVCDef.ch'

/*/{Protheus.doc} M110MONT
@Description
@Author 	 TSC - Gabriel Araujo
@Since  	 30/05/2025
@Cliente	 DELPI
/*/
User Function M110MONT()
    //   C1_DINICOM  dDataBase
    //  C1_DATPRF  dDataBase
    Local cNumSC1   := PARAMIXB[1]
    Local nOpc      := PARAMIXB[2]
    Local lCopia    := PARAMIXB[3]
    Local nPos1     :=0
    Local nPos2     :=0
    Local nX := 0
    if lCopia
        nPos1 := aScan(aHeader,{|x| Trim(x[2])=="C1_DINICOM"})
        nPos2 := aScan(aHeader,{|x| Trim(x[2])=="C1_DATPRF"})
        //aCols[n][nPosDtIni]
        if nPos1 >0 .and. nPos2 > 0

            For nX:= 1 to Len(aCols)
                aCols[nX][nPos1] := dDatabase
                aCols[nX][nPos2] := dDatabase
            Next nX

        endif

    endif

Return
