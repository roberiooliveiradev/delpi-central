# Minha DELPI — Plugins Iframe

> **Arquivo:** `docs/05-plugin-system/iframe.md`  
> **Status:** documentação oficial (maio/2026)  
> **Produto:** Minha DELPI  
> **Escopo:** plugins do tipo `iframe`

---

## 1. Objetivo

Este documento descreve plugins do tipo **iframe** na Minha DELPI.

Plugins iframe são usados para integrar aplicações web externas ou internas que não são microfrontends nativos, mas que podem ser exibidas dentro do Portal ou abertas externamente conforme o modo de renderização.

---

## 2. Conceito

Um plugin `iframe` representa uma aplicação visual carregada por URL.

Ele pode ser usado para:

- embutir sistemas internos já existentes;
- integrar aplicações externas autorizadas;
- disponibilizar módulos que ainda não foram convertidos para microfrontend;
- publicar telas legadas dentro do Portal;
- abrir aplicações externas a partir do menu da Minha DELPI.

Diferente de `microfrontend`, o iframe não depende de remote entry ou module federation.

Ele depende de uma URL HTTP/HTTPS acessível pelo navegador.

---

## 3. Tipo no manifesto

Para declarar um plugin iframe, usar:

```json
{
  "type": "iframe"
}
```

A versão de schema suportada continua sendo:

```json
{
  "schemaVersion": "1.0.0"
}
```

---

## 4. Regras principais

Plugins iframe possuem regras específicas.

| Regra | Obrigatório |
|---|---:|
| `entry` global | Sim, no contrato efetivo atual |
| `entry` com `http://` ou `https://` | Sim |
| `routes` com ao menos uma rota | Sim |
| `basePath` válido | Sim |
| Rotas dentro do `basePath` | Sim |
| Permissões declaradas | Sim |
| `ui.renderMode` restrito a `embedded` ou `external` | Sim, se informado |

---

## 5. Entry point

Para iframe, o campo `entry` deve ser uma URL absoluta iniciando com:

```text
http://
https://
```

Exemplo válido:

```json
{
  "entry": "https://sistema.exemplo.com"
}
```

Exemplos inválidos:

```json
{
  "entry": "/apps/sistema"
}
```

```json
{
  "entry": "sistema.exemplo.com"
}
```

Erro esperado:

```text
invalid_iframe_entry_url
```

---

## 6. Render modes suportados

Para `iframe`, os valores aceitos de `ui.renderMode` são:

```text
embedded
external
```

| Render mode | Comportamento esperado |
|---|---|
| `embedded` | Portal renderiza a URL dentro de um iframe |
| `external` | Portal pode abrir a URL fora do shell, por exemplo em nova aba |

Exemplo embedded:

```json
{
  "ui": {
    "renderMode": "embedded"
  }
}
```

Exemplo external:

```json
{
  "ui": {
    "renderMode": "external"
  }
}
```

---

## 7. Rotas

Plugins iframe devem declarar pelo menos uma rota.

Exemplo:

```json
{
  "routes": [
    {
      "path": "/apps/sistema-externo",
      "label": "Sistema Externo",
      "icon": "external-link",
      "permission": "sistema-externo.access",
      "showInMenu": true,
      "order": 20
    }
  ]
}
```

Regras:

- `routes` é obrigatório;
- deve conter ao menos uma rota;
- cada `path` deve iniciar com `basePath`;
- rotas não podem ser duplicadas;
- `permission` deve existir em `permissions[].code`;
- `showInMenu` controla exibição no menu.

---

## 8. Entry por rota

O schema permite `routes[].entry`.

Para iframe, se uma rota declarar `entry`, ela também deve iniciar com:

```text
http://
https://
```

Exemplo:

```json
{
  "routes": [
    {
      "path": "/apps/sistema-externo/home",
      "label": "Home",
      "entry": "https://sistema.exemplo.com/home",
      "permission": "sistema-externo.access"
    },
    {
      "path": "/apps/sistema-externo/relatorios",
      "label": "Relatórios",
      "entry": "https://sistema.exemplo.com/reports",
      "permission": "sistema-externo.reports"
    }
  ]
}
```

Ponto de atenção:

> O contrato efetivo atual exige `entry` global para `iframe`, mesmo que haja `routes[].entry`. Portanto, declarar também `entry` global é obrigatório.

---

## 9. Permissões

Plugins iframe devem declarar permissões no manifesto.

Exemplo:

```json
{
  "permissions": [
    {
      "code": "sistema-externo.access",
      "name": "Acessar Sistema Externo",
      "description": "Permite acessar o sistema externo.",
      "module": "sistema-externo"
    }
  ]
}
```

Regras:

- `permissions` é obrigatório;
- deve conter ao menos uma permissão;
- `permissions[].module` deve ser igual ao `id`;
- permissões usadas nas rotas devem existir no manifesto.

---

## 10. Como o Portal carrega iframe

Fluxo conceitual:

```text
Portal chama /me/apps
  ↓
Core API retorna app type=iframe
  ↓
Portal lê entryUrl e renderMode
  ↓
Se renderMode=embedded, renderiza iframe
  ↓
Se renderMode=external, abre URL conforme comportamento definido
```

Payload conceitual:

```json
{
  "id": "sistema-externo",
  "name": "Sistema Externo",
  "basePath": "/apps/sistema-externo",
  "icon": "external-link",
  "type": "iframe",
  "entryUrl": "https://sistema.exemplo.com",
  "renderMode": "embedded",
  "routes": [
    {
      "path": "/apps/sistema-externo",
      "label": "Sistema Externo",
      "permission": "sistema-externo.access",
      "showInMenu": true,
      "order": 20,
      "entry": null
    }
  ]
}
```

---

## 11. Autorização

A autorização de iframe segue o mesmo modelo dos demais plugins visuais.

Regra:

- superadmin recebe todos os apps ativos;
- usuário comum recebe apenas rotas sem permissão ou rotas cuja permissão esteja nas permissões efetivas;
- app sem rota autorizada não é retornado.

O Portal só exibe o iframe se a Core API retornar o app/rota em `/me/apps`.

---

## 12. Segurança de iframe

Iframes exigem cuidados extras.

A aplicação de destino precisa permitir ser carregada em iframe.

Headers relevantes:

```text
X-Frame-Options
Content-Security-Policy frame-ancestors
```

Se a aplicação externa usar:

```text
X-Frame-Options: DENY
```

ou

```text
X-Frame-Options: SAMEORIGIN
```

sem compatibilidade com o domínio da Minha DELPI, o navegador pode bloquear o carregamento.

---

## 13. Autenticação em aplicações iframe

Aplicações carregadas por iframe podem ter autenticação própria.

Cenários possíveis:

1. Aplicação já possui SSO com o mesmo Keycloak.
2. Aplicação usa sessão própria.
3. Aplicação aceita token ou contexto via integração específica.
4. Aplicação é pública dentro da rede corporativa.

Regra recomendada:

> Sempre que possível, aplicações iframe internas devem usar o mesmo Keycloak ou uma estratégia compatível de SSO.

Não é recomendado expor tokens sensíveis em query string.

---

## 14. Limitações de iframe

Plugins iframe possuem limitações naturais:

- menor integração visual com o Portal;
- controle limitado sobre a aplicação carregada;
- possíveis bloqueios por headers de segurança;
- dificuldade de compartilhar estado;
- possíveis problemas de responsividade;
- experiência inconsistente se a aplicação externa tiver layout próprio completo;
- autenticação duplicada se não houver SSO.

Por isso, iframe deve ser usado preferencialmente para integração rápida ou legado.

Para módulos novos altamente integrados, preferir `microfrontend`.

---

## 15. Exemplo completo de manifesto iframe

```json
{
  "schemaVersion": "1.0.0",
  "id": "sistema-externo",
  "name": "Sistema Externo",
  "description": "Integração com sistema externo via iframe.",
  "category": "Sistemas",
  "version": "1.0.0",
  "icon": "external-link",
  "type": "iframe",
  "basePath": "/apps/sistema-externo",
  "entry": "https://sistema.exemplo.com",
  "permissions": [
    {
      "code": "sistema-externo.access",
      "name": "Acessar Sistema Externo",
      "description": "Permite acessar o sistema externo.",
      "module": "sistema-externo"
    }
  ],
  "routes": [
    {
      "path": "/apps/sistema-externo",
      "label": "Sistema Externo",
      "icon": "external-link",
      "permission": "sistema-externo.access",
      "showInMenu": true,
      "order": 20,
      "menuGroup": "Sistemas"
    }
  ],
  "ui": {
    "renderMode": "embedded"
  },
  "metadata": {
    "owner": "DELPI",
    "integration": "iframe"
  }
}
```

---

## 16. Registro

O registro é feito pelo endpoint padrão:

```http
POST /admin/apps/register
```

Permissão exigida:

```text
apps.manage
```

Durante o registro:

- cria ou atualiza app;
- salva manifesto vigente;
- cria versão histórica;
- cria permissões;
- cria rotas;
- publica evento `plugin_registered`.

---

## 17. Atualização

Mudanças não estruturais usam:

```http
PUT /admin/apps/<plugin_id>/manifest
```

Exemplos:

- alterar nome;
- alterar descrição;
- alterar ícone;
- alterar label;
- alterar ordem;
- alterar `showInMenu`.

Mudanças estruturais exigem nova versão via register:

- alterar `entry` global de forma significativa;
- alterar rotas;
- alterar permissões;
- alterar `basePath`;
- alterar `type`.

---

## 18. Rollback

Iframe também suporta rollback.

Endpoint:

```http
POST /admin/apps/<plugin_id>/rollback
```

Rollback restaura:

- versão ativa;
- manifesto vigente;
- permissões;
- rotas;
- entry salvo na versão histórica.

Atenção:

> O rollback só restaura o contrato na Core API. A URL externa precisa continuar disponível e compatível.

---

## 19. Checklist para plugin iframe

- [ ] `type` é `iframe`.
- [ ] `schemaVersion` é `1.0.0`.
- [ ] `entry` global existe.
- [ ] `entry` começa com `http://` ou `https://`.
- [ ] `routes` possui ao menos uma rota.
- [ ] Rotas começam com `basePath`.
- [ ] Permissões estão declaradas.
- [ ] Permissões das rotas existem em `permissions`.
- [ ] `ui.renderMode` é `embedded` ou `external`.
- [ ] A aplicação permite ser carregada em iframe, se `embedded`.
- [ ] Estratégia de autenticação da aplicação externa foi definida.
- [ ] Usuários receberam permissões necessárias.

---

## 20. Boas práticas

1. Preferir `microfrontend` para módulos novos e profundamente integrados.
2. Usar `iframe` para legado, sistemas externos ou integrações rápidas.
3. Garantir SSO quando possível.
4. Evitar token em query string.
5. Validar headers de segurança antes de publicar.
6. Definir `renderMode` explicitamente.
7. Usar permissões específicas por rota quando necessário.
8. Manter `basePath` estável.
9. Versionar mudanças estruturais.
10. Documentar limitações da aplicação integrada.

---

## 21. Pontos de atenção

1. Iframe precisa de URL absoluta HTTP/HTTPS.
2. Aplicação externa pode bloquear iframe por headers.
3. Autenticação pode ser duplicada se não houver SSO.
4. Portal não controla internamente a aplicação carregada.
5. Rotas continuam sendo autorizadas pela Core API.
6. App sem rota autorizada não aparece.
7. Rollback não garante disponibilidade da URL externa.
8. Mudanças estruturais exigem nova versão.
9. `ui.renderMode` para iframe não aceita `federated`.
10. Iframe não deve ser usado como substituto padrão de microfrontend para novos módulos complexos.

---

## 22. Documentos relacionados

```text
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/registro-de-plugin.md
docs/05-plugin-system/atualizacao-de-manifesto.md
docs/05-plugin-system/versionamento-e-rollback.md
docs/05-plugin-system/microfrontends.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/03-autenticacao-autorizacao/rbac.md
```

