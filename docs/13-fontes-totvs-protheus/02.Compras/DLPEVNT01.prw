#include 'TOTVS.CH'
#include 'parmtype.ch'
#INCLUDE "FWEVENTVIEWCONSTS.CH"
#include 'totvs.ch'

/*/{Protheus.doc} nomeFunction
(long_description)
@type user function
@author Pedro Lindenberg
@since 25/07/2024
/*/
User Function DLPEVNT01()
	Local cLockName As Character
	Local cToken := "6542"
	Local aSeaArea := SEA->(GetArea())
	Local cNumeBor := "123456"
	Private cDtVld := ALLTRIM(DtoC(Date())+time())
	cLockName := cEmpAnt + ' - FINA717'
	cEventID := "D02"

	// Teste_EV(cToken,cNumeBor)

	// fNewFunc()

	fOutraFunc()

	SEA->(RESTAREA(aSeaArea))

Return


STATIC Function Teste_EV(cRealTkn,cNumeBor)

	// Local cEventID  := "D02"
	Local cMsg := ""
	cMsg := "<script src='https://kit.fontawesome.com/a076d05399.js' crossorigin='anonymous'></script>"
	cMsg += "<h1 style='color:003867'>TESTE</h1>"
	cMsg += "<p>Teste de icones:</p>"
	cMsg += "<i class='fas fa-band-aid'></i>"
	cMsg += "<p style'font-size:48px;color:red;'=>Teste tamanho e cor:</p>"

	// PutGlbVars(cDtVld+E2_FILIAL+E2_PREFIXO+E2_NUM+E2_PARCELA+E2_TIPO+E2_FORNECE+E2_LOJA,cRealTkn)

	EventInsert(FW_EV_CHANEL_ENVIRONMENT, FW_EV_CATEGORY_MODULES, cEventID,FW_EV_LEVEL_INFO,"",'Liberação borderô: '+cNumeBor,cMsg,.T.)

Return

/*/{Protheus.doc} nomeStaticFunction
  (long_description)
  @type  Static Function
  @author user
  @since 25/07/2024
  @version version
/*/
Static Function fNewFunc()

	Local cEvento := "D02"
	Local cMensag := ""

	cMensag := '<!DOCTYPE html>'
	cMensag += '<html lang="en">'
	cMensag += '<head>'
	cMensag += '<meta charset="UTF-8">'
	cMensag += '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
	cMensag += '<title>Protheus com Ícones</title>'
	cMensag += '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">'
	cMensag += '</head>'
	cMensag += '<body>'
	cMensag += '<h1>Bem-vindo ao Protheus</h1><br>'
	cMensag += '<p><i class="fas fa-user"></i> Usuário</p><br>'
	cMensag += '<i class="fas fa-search search-icon"></i><br>'
	cMensag += '<h1>Testando</h1><br>'
	cMensag += '<p><i class="fas fa-user"></i> Usuário</p>'
	cMensag += '<p style="color:red;font-size:48px">Teste html</p><br>'
	cMensag += '</body>
	cMensag += '</html>

	EventInsert(FW_EV_CHANEL_ENVIRONMENT, FW_EV_CATEGORY_MODULES, cEvento, FW_EV_LEVEL_INFO, "","TESTE HTML",cMensag,.T.)

Return Nil

/*/{Protheus.doc} nomeStaticFunction
  (long_description)
  @type  Static Function
  @author user
  @since 25/07/2024
  @version version
  @param param_name, param_type, param_descr
  @return return_var, return_type, return_description
  @example
  (examples)
  @see (links_or_references)
/*/
Static Function fOutraFunc()

	Local cEvento := "D02"
	Local cMensag := ""
	Local cNewMsg := "<html><head>" + ;
		"<style>.icon { width: 24px; height: 24px; }</style></head>" + ;
		"<body><p>Olá,</p>" + ;
		"<p>Este é um e-mail de exemplo com um ícone:</p>" + ;
		"<img src='https://cdn-icons-png.flaticon.com/512/64/64572.png' onClick = 'https://tdn.totvs.com/pages/releaseview.action?pageId=567767216' alt='Ícone' class='icon'>" + ;
		"<p>Atenciosamente,<br>Seu Nome</p></body></html>"

	cLinkTdn := 'https://tdn.totvs.com/pages/releaseview.action?pageId=567767216'

	cMensag += '<!DOCTYPE html>'
	cMensag += '<script>'
	cMensag += 'async function requisitarApiProtheus(url, headers) {'
	cMensag += ' try {'
	cMensag += 'const resposta = await fetch(url, {'
	cMensag += 'method: "GET",'
	cMensag += 'headers: headers'
	cMensag += '});'

	cMensag += 'if (!resposta.ok) {'
	cMensag += 'throw new Error(`Erro na requisição: ${resposta.statusText}`);'
	cMensag += ' }'

	cMensag += '    const resultado = await resposta.json();'
	cMensag += '    console.log("Resultado:", resultado);'
	cMensag += ' } catch (erro) {'
	cMensag += '    console.error("Erro ao requisitar API Protheus:", erro);'
	cMensag += '}'
	cMensag += '}'

	cMensag += 'document.getElementById("meu-link").addEventListener("click", function(event) {'
	cMensag += 'event.preventDefault(); // Impede o comportamento padrão do link'

	cMensag += ' const url = "https://192.168.1.7:8061/rest/healthcheck/;"'
	cMensag += 'const headers = {'
	cMensag += '    "Authorization": "Bearer",'
	cMensag += '    "Content-Type": "application/json"'
	cMensag += '};'

	cMensag += '   requisitarApiProtheus(url, headers);'
	cMensag += '});'
	cMensag += '</script>'
	cMensag += '<html lang="en">'
	cMensag += '<head>'
	cMensag += '<meta charset="UTF-8">'
	cMensag += '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
	cMensag += '<title>Protheus com Ícones</title>'
	cMensag += '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">'
	cMensag += '</head>'
	cMensag += '<body>'
	cMensag += '<h1>Bem-vindo ao Protheus</h1><br>'
	cMensag += '<p><i class="fas fa-user"></i> Usuário</p><br>'
	cMensag += '<i class="fas fa-search search-icon"></i><br>'
	cMensag += '<h1>Testando</h1><br>'
	cMensag += '<p><i class="fas fa-user"></i> Usuário</p>'
	cMensag += '<p style="color:red;font-size:48px">Teste html</p><br>'
	cMensag += "<b><a target='_blank' href='"+cLinkTDN+"'> "
	cMensag += "Saiba Mais"  // "Saiba mais"
	cMensag += " </a></b>"
	cMensag += " <h1>Exemplo de Chamada à API</h1>'
	cMensag += "<a href='#' onclick='chamarAPI(); return false;'>Chamar API para Obter Posts</a>'
	cMensag += "<div id='result'></div>"
	cMensag += "<span color:red;'>" + "</span>"
	cMensag += '<a href="#" id="meu-link">Clique aqui para requisitar a API</a>'

	cMensag += '</body>
	cMensag += '</html>

	EventInsert(FW_EV_CHANEL_ENVIRONMENT, FW_EV_CATEGORY_MODULES, cEvento, FW_EV_LEVEL_INFO, "","TESTE HTML",cMensag,.T.)

Return

/*/{Protheus.doc} nomeStaticFunction
  (long_description)
  @type  Static Function
  @author user
  @since 25/07/2024
  @version version
  @param param_name, param_type, param_descr
  @return return_var, return_type, return_description
  @example
  (examples)
  @see (links_or_references)
/*/
// Static Function fNovaNova()
// 	cLinkTdn := 'https://tdn.totvs.com/pages/releaseview.action?pageId=567767216'

// 	cMsg001 := "<b><a target='_blank' href='"+cLinkTDN+"'> "
// 	cMsg001 += STR0011  // "Saiba mais"
// 	cMsg001 += " </a></b>"
// 	cMsg001 += "<span color: #565759;'>" + "</span>"

// Return
