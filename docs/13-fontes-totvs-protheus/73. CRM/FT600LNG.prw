#INCLUDE "PROTHEUS.CH"

/*/{Protheus.doc} FT600ENG
Wrapper para impressao da proposta comercial em Ingles.
Seta o idioma e delega para Ft600Exe.
@type  Function
@author  DELPI
@since   13/04/2026
@see     U_Ft600Exe
/*/
User Function FT600ENG()
	Private cDLP_IDIOMA := "002"
	U_Ft600Exe()
Return

/*/{Protheus.doc} FT600ESP
Wrapper para impressao da proposta comercial em Espanhol.
Seta o idioma e delega para Ft600Exe.
@type  Function
@author  DELPI
@since   13/04/2026
@see     U_Ft600Exe
/*/
User Function FT600ESP()
	Private cDLP_IDIOMA := "003"
	U_Ft600Exe()
Return

/*/{Protheus.doc} DLPTrdPr
Retorna a string traduzida para o idioma informado.
Usada pelas funcoes de preenchimento da proposta comercial (Ft600Exe/Ft601Exe).
@type  Function
@param cChave   , Caractere, Chave da string a traduzir
@param cIdioma  , Caractere, Codigo do idioma (001=PT, 002=EN, 003=ES)
@return cRet    , Caractere, String traduzida
@author  DELPI
@since   13/04/2026
/*/
User Function DLPTrdPr(cChave, cIdioma)
	Local cRet := ""
	Default cIdioma := "001"

	Do Case

	// --- ICMS ---
	Case cChave == "INCLUSO"
		Do Case
		Case cIdioma == "002" ; cRet := "INCLUDED"
		Case cIdioma == "003" ; cRet := "INCLUIDO"
		Otherwise             ; cRet := "INCLUSO"
		End Case

	Case cChave == "NAO_INCLUSO"
		Do Case
		Case cIdioma == "002" ; cRet := "NOT INCLUDED"
		Case cIdioma == "003" ; cRet := "NO INCLUIDO"
		Otherwise             ; cRet := "NAO INCLUSO"
		End Case

	// --- Embalagem ---
	Case cChave == "INCLUSA"
		Do Case
		Case cIdioma == "002" ; cRet := "INCLUDED"
		Case cIdioma == "003" ; cRet := "INCLUIDA"
		Otherwise             ; cRet := "INCLUSA"
		End Case

	Case cChave == "NAO_INCLUSA"
		Do Case
		Case cIdioma == "002" ; cRet := "NOT INCLUDED"
		Case cIdioma == "003" ; cRet := "NO INCLUIDA"
		Otherwise             ; cRet := "NAO INCLUSA"
		End Case

	// --- Prazo / Validade ---
	Case cChave == "DIAS"
		Do Case
		Case cIdioma == "002" ; cRet := "DAYS"
		Case cIdioma == "003" ; cRet := "DIAS"
		Otherwise             ; cRet := "DIAS"
		End Case

	// --- Referencia pedido cliente ---
	Case cChave == "REFERENTE"
		Do Case
		Case cIdioma == "002" ; cRet := "Reference: "
		Case cIdioma == "003" ; cRet := "Referencia: "
		Otherwise             ; cRet := "Referente: "
		End Case

	// --- CEP no endereco ---
	Case cChave == "CEP"
		Do Case
		Case cIdioma == "002" ; cRet := "ZIP: "
		Case cIdioma == "003" ; cRet := "CP: "
		Otherwise             ; cRet := "CEP: "
		End Case
	Case cChave == "VENDAS"
		Do Case
		Case cIdioma == "002" ; cRet := "SALES"
		Case cIdioma == "003" ; cRet := "VENTAS"
		Otherwise             ; cRet := "VENDAS"
		End Case

	// --- Frete (CIF/FOB sao termos internacionais, nao traduz) ---
	// Se necessario adicionar outros termos, basta incluir novos Cases aqui.

	Otherwise
		cRet := cChave

	End Case

Return cRet
