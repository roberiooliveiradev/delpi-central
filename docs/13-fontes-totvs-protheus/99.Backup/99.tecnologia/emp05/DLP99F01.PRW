#INCLUDE "RPTDEF.CH"
#INCLUDE "FWPrintSetup.ch"
#INCLUDE "protheus.ch"
#Include 'TopConn.ch'



User Function DLP99F01()
  Private cEol := chr(10)
  IF alltrim(cFilAnt )!= "0501"
    FWAlertError("Filial Incorreta", "Delpi")
    return
  endif

  FWMsgRun(, {|| fPrcSC7() } , "Delpi", "Pedido de Compras")


rETURN


STATIC FUNCTION fPrcSC7()

  Local cQry1 := ""
  Private lMsErroAuto := .F.

  cQry1 := "SELECT DISTINCT  C7_NUM,C7_ITEM,C7_EMISSAO ,C7_FORNECE, C7_LOJA ,C7_COND" +cEol
  cQry1 += "  FROM dbo.SC7050 (NOLOCK) TBL1  " +cEol
  cQry1 += "WHERE TBL1.D_E_L_E_T_ = '' " +cEol
  cQry1 += "AND C7_RESIDUO ='' " +cEol
  cQry1 += "AND  C7_QUJE < C7_QUANT " +cEol
  cQry1 += "AND C7_NUM ='000857' " +cEol
  cQry1 += "ORDER BY 1,2 "

  If Select('TMP') <> 0
    TMP->(dbCloseArea())
  Endif


  TCQuery cQry1 Alias TMP New

  While TMP->(!eof())
    aCabec := {}
    aItem := {}
    cDoc :=GETNUMSC7(.T.)
    dDataBase := stod( TMP->C7_EMISSAO)
    cFornece := TMP->C7_FORNECE
    cLojaFor := TMP->C7_LOJA
    cCond := TMP->C7_COND

    aadd(aCabec,{"C7_NUM"   	,cDoc		, Nil})
    aadd(aCabec,{"C7_EMISSAO" 	,dDataBase	, Nil})
    aadd(aCabec,{"C7_FORNECE" 	,cFornece	, Nil})
    aadd(aCabec,{"C7_LOJA" 		,cLojaFor	, Nil})
    aadd(aCabec,{"C7_COND" 		,cCond		, Nil})
    aadd(aCabec,{"C7_FILENT" 	,CriaVar("C7_FILENT"),Nil})
    aadd(aCabec,{"C7_MOEDA"    	,1.0		, Nil})
    aadd(aCabec,{"C7_TXMOEDA"  	,1.0		, Nil})

    cQry2 := "SELECT DISTINCT  * " +cEol
    cQry2 += "  FROM dbo.SC7050 (NOLOCK) TBL1  " +cEol
    cQry2 += "WHERE TBL1.D_E_L_E_T_ = '' " +cEol
    cQry2 += "AND C7_RESIDUO ='' " +cEol
    cQry2 += "AND  C7_QUJE < C7_QUANT " +cEol
    cQry2 += "AND C7_NUM = "+valtosql(TMP->C7_NUM) +cEol
    cQry2 += "ORDER BY C7_ITEM "

    If Select('TMPSC7') <> 0
      TMPSC7->(dbCloseArea())
    Endif
    TCQuery cQry2 Alias TMPSC7 New
    nX := 0
    While TMPSC7->(!eof())
      aLinha := {}
      nX++
      cObs := PADR("PC ORIG: "+ TMPSC7->C7_NUM + "| ITEM "+ TMPSC7->C7_ITEM,GETSX3CACHE("C7_OBS","X3_TAMANHO"))
      cC7Item := StrZero(nX,TamSX3("C7_ITEM")[1])
      aAdd(aLinha,{"C7_ITEM", cC7Item, Nil})
      aadd(aLinha,{"C7_PRODUTO" ,  TMPSC7->C7_PRODUTO,Nil})
      aadd(aLinha,{"C7_LOCAL" ,  TMPSC7->C7_LOCAL,Nil})

      aadd(aLinha,{"C7_QUANT"   ,  TMPSC7->C7_QUANT				,Nil})
      aadd(aLinha,{"C7_PRECO"   , 	TMPSC7->C7_PRECO,Nil})
      aadd(aLinha,{"C7_TOTAL"   , 	TMPSC7->C7_TOTAL,Nil})
      aadd(aLinha,{"C7_TES" 	  , 	TMPSC7->C7_TES,Nil})
      aadd(aLinha,{"C7_DATPRF" 	  , 	TMPSC7->C7_DATPRF,Nil})
      aadd(aLinha,{"C7_CC" 	  , 	TMPSC7->C7_CC,Nil})
      aadd(aLinha,{"C7_CONTATO" 	  , 	TMPSC7->C7_CONTATO,Nil})
      aadd(aLinha,{"C7_IPI" 	  , 	TMPSC7->C7_IPI,Nil})
      aadd(aLinha,{"C7_PICM" 	  , 	TMPSC7->C7_PICM,Nil})
      aadd(aLinha,{"C7_OBS" 	  , 	cObs,Nil})
      aadd(aItem,aLinha)
      TMPSC7->(dbskip())
    Enddo

    lMsErroAuto := .F.
    MsExecAuto({|v,x,y,z| MATA120(v,x,y,z)},1,aCabec,aItem,3)

    If lMsErroAuto

      MOSTRAERRO()

    EndIf

    TMP->(dbskip())
  Enddo

  TMP->(dbCloseArea())

RETURN
