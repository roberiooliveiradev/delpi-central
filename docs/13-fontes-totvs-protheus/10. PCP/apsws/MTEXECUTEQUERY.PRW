#INCLUDE "protheus.ch"
#INCLUDE "apwebsrv.ch"

/* ===============================================================================
WSDL Location    http://192.168.1.7:8102/ws/MTEXECUTEQUERY.apw?WSDL
Gerado em        19/11/24 06:04:58
Observa��es      C�digo-Fonte gerado por ADVPL WSDL Client 1.120703
Altera��es neste arquivo podem causar funcionamento incorreto
e ser�o perdidas caso o c�digo-fonte seja gerado novamente.
=============================================================================== */

User Function _PJLMKKB ; Return  // "dummy" function - Internal Use

/* -------------------------------------------------------------------------------
WSDL Service WSMTEXECUTEQUERY
------------------------------------------------------------------------------- */

WSCLIENT WSMTEXECUTEQUERY

	WSMETHOD NEW
	WSMETHOD INIT
	WSMETHOD RESET
	WSMETHOD CLONE
	WSMETHOD GETEXECUTEQUERY

	WSDATA   _URL                      AS String
	WSDATA   _HEADOUT                  AS Array of String
	WSDATA   _COOKIES                  AS Array of String
	WSDATA   cUSERCODE                 AS string
	WSDATA   cQUERYSTMT                AS string
	WSDATA   cRESULTFILE               AS string
	WSDATA   cDELIMITER                AS string
	WSDATA   cGETEXECUTEQUERYRESULT    AS string

ENDWSCLIENT

WSMETHOD NEW WSCLIENT WSMTEXECUTEQUERY
	::Init()
	If !FindFunction("XMLCHILDEX")
		UserException("O C�digo-Fonte Client atual requer os execut�veis do Protheus Build [7.00.240223P-20241010] ou superior. Atualize o Protheus ou gere o C�digo-Fonte novamente utilizando o Build atual.")
	EndIf
Return Self

WSMETHOD INIT WSCLIENT WSMTEXECUTEQUERY
Return

WSMETHOD RESET WSCLIENT WSMTEXECUTEQUERY
	::cUSERCODE          := NIL
	::cQUERYSTMT         := NIL
	::cRESULTFILE        := NIL
	::cDELIMITER         := NIL
	::cGETEXECUTEQUERYRESULT := NIL
	::Init()
Return

WSMETHOD CLONE WSCLIENT WSMTEXECUTEQUERY
	Local oClone := WSMTEXECUTEQUERY():New()
	oClone:_URL          := ::_URL
	oClone:cUSERCODE     := ::cUSERCODE
	oClone:cQUERYSTMT    := ::cQUERYSTMT
	oClone:cRESULTFILE   := ::cRESULTFILE
	oClone:cDELIMITER    := ::cDELIMITER
	oClone:cGETEXECUTEQUERYRESULT := ::cGETEXECUTEQUERYRESULT
Return oClone

// WSDL Method GETEXECUTEQUERY of Service WSMTEXECUTEQUERY

WSMETHOD GETEXECUTEQUERY WSSEND cUSERCODE,cQUERYSTMT,cRESULTFILE,cDELIMITER WSRECEIVE cGETEXECUTEQUERYRESULT WSCLIENT WSMTEXECUTEQUERY
	Local cSoap := "" , oXmlRet

	BEGIN WSMETHOD

	cSoap += '<GETEXECUTEQUERY xmlns="http:webservices.microsiga.com.br/mtexecutequery.apw">'
	cSoap += WSSoapValue("USERCODE", ::cUSERCODE, cUSERCODE , "string", .T. , .F., 0 , NIL, .F.,.F.)
	cSoap += WSSoapValue("QUERYSTMT", ::cQUERYSTMT, cQUERYSTMT , "string", .T. , .F., 0 , NIL, .F.,.F.)
	cSoap += WSSoapValue("RESULTFILE", ::cRESULTFILE, cRESULTFILE , "string", .T. , .F., 0 , NIL, .F.,.F.)
	cSoap += WSSoapValue("DELIMITER", ::cDELIMITER, cDELIMITER , "string", .T. , .F., 0 , NIL, .F.,.F.)
	cSoap += "</GETEXECUTEQUERY>"

	oXmlRet := SvcSoapCall(Self,cSoap,;
		"http:webservices.microsiga.com.br/mtexecutequery.apw/GETEXECUTEQUERY",;
		"DOCUMENT","http:webservices.microsiga.com.br/mtexecutequery.apw",,"1.031217",;
		"http://192.168.1.7:8102/ws/MTEXECUTEQUERY.apw")

	::Init()
	::cGETEXECUTEQUERYRESULT :=  WSAdvValue( oXmlRet,"_GETEXECUTEQUERYRESPONSE:_GETEXECUTEQUERYRESULT:TEXT","string",NIL,NIL,NIL,NIL,NIL,NIL)

	END WSMETHOD

	oXmlRet := NIL
Return .T.



