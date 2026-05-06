# Minha DELPI — Consumo de Plugins no Portal

> **Arquivo:** `docs/06-portal-frontend/consumo-de-plugins.md`  
> **Status:** documentação oficial em construção  
> **Produto:** Minha DELPI  
> **Escopo:** carregamento e renderização de plugins pelo Portal

---

## 1. Objetivo

Este documento descreve como o **Portal** da Minha DELPI consome plugins registrados na Core API.

Ele explica como o Portal deve interpretar os dados retornados por `/me/apps`, escolher a estratégia de renderização e carregar corretamente plugins dos tipos:

- `microfrontend`;
- `iframe`;
- `backend-only`.

---

## 2. Princípio central

O Portal não deve descobrir plugins por leitura direta de arquivos locais, manifesto bruto ou configuração hardcoded.

A fonte oficial de plugins disponíveis para o usuário é:

```http
GET /me/apps
```

A Core API retorna somente apps e rotas autorizados para o usuário atual.

Regra:

> O Portal consome plugins a partir da visão autorizada da Core API, não a partir do manifesto bruto.

---

## 3. Fluxo geral

```text
Usuário autenticado
  ↓
Portal chama /me/apps
  ↓
Core API retorna apps autorizados
  ↓
Portal monta menu e rotas
  ↓
Usuário acessa uma rota
  ↓
Portal identifica app dono da rota
  ↓
Portal escolhe estratégia por app.type e renderMode
  ↓
Portal renderiza microfrontend, iframe ou fallback
```

---

## 4. Payload usado pelo Portal

Formato conceitual retornado por `/me/apps`:

```json
[
  {
    "id": "dashboard-lmps",
    "name": "Dashboard LMPs",
    "basePath": "/apps/dashboard-lmps",
    "icon": "bar-chart3",
    "type": "microfrontend",
    "entryUrl": "/apps/dashboard-lmps/assets/remoteEntry.js",
    "renderMode": "federated",
    "routes": [
      {
        "app": "dashboard-lmps",
        "app_name": "Dashboard LMPs",
        "app_icon": "bar-chart3",
        "path": "/apps/dashboard-lmps",
        "permission": "dashboard-lmps.access",
        "label": "Dashboard LMPs",
        "icon": "bar-chart3",
        "showInMenu": true,
        "order": 1,
        "entry": null
      }
    ]
  }
]
```

---

## 5. Campos relevantes para renderização

| Campo | Origem | Uso |
|---|---|---|
| `app.id` | Core API | Identificar plugin |
| `app.type` | Manifesto/app | Escolher estratégia de renderização |
| `app.entryUrl` | Manifesto | Entry global do plugin |
| `app.renderMode` | Manifesto `ui.renderMode` | Escolher modo de renderização |
| `app.basePath` | Manifesto/app | Validar path base |
| `route.path` | App route | Rota navegável |
| `route.entry` | Manifesto route entry | Entry específico da rota, quando existir |
| `route.permission` | App route | Informação de autorização já aplicada pela Core |
| `route.showInMenu` | App route | Exibição no menu |

---

## 6. Estratégia por tipo

O Portal deve tratar cada tipo de plugin separadamente.

| `type` | Estratégia |
|---|---|
| `microfrontend` | Carregar componente/app remoto ou integrado |
| `iframe` | Renderizar URL em iframe ou abrir externo |
| `backend-only` | Não renderizar UI |

Pseudocódigo:

```typescript
switch (app.type) {
  case "microfrontend":
    return renderMicrofrontend(app, route)

  case "iframe":
    return renderIframe(app, route)

  case "backend-only":
    return null

  default:
    return renderUnsupportedPlugin(app)
}
```

---

## 7. Resolução de entry

Uma rota pode ter entry específico.

Regra recomendada:

```text
entry efetivo = route.entry || app.entryUrl
```

Pseudocódigo:

```typescript
function resolveEntry(app, route) {
  return route.entry || app.entryUrl
}
```

Isso permite que um mesmo plugin tenha entry global e, futuramente, entradas específicas por rota.

---

## 8. Microfrontends

Para apps do tipo:

```text
microfrontend
```

O Portal deve usar:

```text
entry efetivo
renderMode
```

Exemplo:

```json
{
  "type": "microfrontend",
  "entryUrl": "/apps/dashboard-lmps/assets/remoteEntry.js",
  "renderMode": "federated"
}
```

Render modes esperados:

```text
embedded
federated
```

---

## 9. Microfrontend `federated`

Quando `renderMode = federated`, o Portal deve carregar o remote entry ou mecanismo equivalente definido pelo plugin.

Fluxo conceitual:

```text
Resolver entry
  ↓
Carregar remoteEntry.js
  ↓
Resolver módulo exposto
  ↓
Renderizar componente no shell
```

Cuidados:

- `entryUrl` deve estar acessível no navegador;
- o plugin deve ser servido pelo Gateway;
- assets devem respeitar `basePath`;
- falhas de carregamento devem exibir erro amigável;
- cache deve ser considerado em deploys.

---

## 10. Microfrontend `embedded`

Quando `renderMode = embedded`, o Portal pode usar uma estratégia de carregamento integrada mais simples, conforme implementação vigente.

Possibilidades:

- carregar bundle local/remoto;
- montar componente por registry interno;
- usar loader próprio;
- renderizar aplicação embutida no shell.

Regra:

> O contrato do Portal deve usar `entryUrl` e `renderMode` como fonte de decisão, sem hardcodar comportamento por plugin específico sempre que possível.

---

## 11. Iframe embedded

Para apps do tipo:

```text
iframe
```

com:

```text
renderMode = embedded
```

O Portal deve renderizar iframe usando o entry efetivo.

Exemplo:

```html
<iframe src="https://sistema.exemplo.com"></iframe>
```

Cuidados:

- aplicar sandbox conforme necessidade;
- lidar com carregamento;
- lidar com erro/bloqueio;
- garantir responsividade;
- verificar headers da aplicação externa.

---

## 12. Iframe external

Para apps do tipo `iframe` com:

```text
renderMode = external
```

O Portal pode abrir a URL fora do shell.

Possibilidades:

- nova aba;
- redirecionamento controlado;
- botão de abertura externa;
- tela intermediária informativa.

Regra recomendada:

> Manter o usuário consciente de que está saindo ou abrindo um sistema externo, quando aplicável.

---

## 13. Backend-only

Apps do tipo:

```text
backend-only
```

não devem ser renderizados como tela.

Uso esperado:

- dependência de outros plugins;
- registro de permissões;
- governança de API;
- metadados técnicos.

Comportamento do Portal:

```text
Não criar rota visual para backend-only.
Não criar item de menu para backend-only.
Não tentar renderizar entry.
```

---

## 14. Validação de rota autorizada

Quando o usuário acessa um path, o Portal deve verificar se o path existe nas rotas autorizadas carregadas de `/me/apps`.

Fluxo:

```text
Usuário acessa /apps/dashboard-lmps
  ↓
Portal procura route.path correspondente
  ↓
Se encontrar, identifica app
  ↓
Renderiza plugin
  ↓
Se não encontrar, redireciona ou mostra 403/404
```

Regra:

> O Portal não deve renderizar plugin cujo path não esteja na lista autorizada do usuário.

---

## 15. Diferença entre 403 e 404 no Portal

Quando a rota não está em `/me/apps`, o Portal pode escolher entre:

- mostrar 403, se souber que a rota existe mas usuário não tem permissão;
- mostrar 404, se não souber se a rota existe;
- redirecionar para home.

Como `/me/apps` só retorna rotas autorizadas, o Portal nem sempre sabe se a rota existe para outro usuário.

Regra recomendada:

```text
Para usuário comum, preferir página segura genérica:
"Página não encontrada ou acesso não permitido".
```

---

## 16. Contexto passado ao plugin

Microfrontends podem precisar de contexto.

Possíveis dados:

- access token;
- dados do usuário;
- permissões;
- rota atual;
- basePath;
- API base URL;
- callbacks de navegação;
- tema visual;
- idioma;
- informações do shell.

Regra de segurança:

> Passar apenas o necessário. Não expor segredos nem dados sensíveis desnecessários.

---

## 17. Tokens e APIs

Plugins que consomem APIs protegidas devem usar token do usuário.

Regras:

- token deve ser obtido do contexto do Portal;
- não salvar token em storage inseguro sem necessidade;
- não passar token em query string para iframe;
- APIs backend devem validar o JWT;
- permissões críticas devem ser validadas no backend.

---

## 18. Tratamento de erro de plugin

O Portal deve tratar falhas de carregamento.

Cenários:

- `entryUrl` indisponível;
- remote entry falhou;
- módulo remoto não exporta componente esperado;
- iframe bloqueado por header;
- rede indisponível;
- token expirado;
- plugin lança erro em runtime.

Comportamento recomendado:

```text
Exibir fallback de erro
Registrar erro no console/log
Permitir voltar para home
Permitir tentar novamente
Não quebrar o shell inteiro
```

---

## 19. Error boundary

Microfrontends devem ser envolvidos em uma boundary de erro.

Objetivo:

- impedir que erro no plugin quebre o Portal inteiro;
- mostrar fallback amigável;
- registrar falha;
- preservar navegação global.

Exemplo conceitual:

```tsx
<PluginErrorBoundary appId={app.id}>
  <RemotePlugin />
</PluginErrorBoundary>
```

---

## 20. Loading states

O Portal deve exibir estados de carregamento.

Exemplos:

```text
Carregando plugin...
Carregando módulo remoto...
Abrindo sistema externo...
```

Para iframes, pode haver loading até o evento `onLoad`.

Para microfrontends, pode haver loading até resolver remote/module.

---

## 21. Eventos administrativos e plugins

Eventos podem invalidar plugins carregados.

Exemplos:

| Evento | Impacto |
|---|---|
| `plugin_deactivated` | Plugin pode deixar de ser acessível |
| `plugin_unregistered` | Plugin deve sair da navegação |
| `plugin_manifest_updated` | Nome, ícone ou ordem podem mudar |
| `plugin_version_rolled_back` | Rotas e entry podem mudar |
| `route_deleted` | Rota atual pode deixar de existir |
| `role_removed_from_user` | Usuário pode perder acesso |

Comportamento recomendado:

```text
Evento recebido
  ↓
Recarregar /me/apps
  ↓
Verificar rota atual
  ↓
Se rota atual não existe mais, redirecionar
```

---

## 22. Cache de plugins no frontend

O Portal pode cachear dados de `/me/apps` em memória durante a sessão, mas deve invalidar quando:

- usuário muda;
- token muda;
- evento administrativo relevante chega;
- erro de autorização ocorre;
- app atual falha por possível desativação;
- usuário executa refresh manual.

Regra:

> Evitar persistir indefinidamente `/me/apps` em localStorage sem estratégia de invalidação.

---

## 23. Boas práticas para consumo

1. Usar `/me/apps` como fonte oficial.
2. Resolver entry por `route.entry || app.entryUrl`.
3. Tratar `type` desconhecido com fallback.
4. Não renderizar `backend-only`.
5. Envolver plugin em error boundary.
6. Exibir loading states.
7. Validar rota atual contra rotas autorizadas.
8. Recarregar apps em eventos administrativos.
9. Não passar token em query string.
10. Não quebrar o shell por erro de plugin.

---

## 24. Checklist de implementação

- [ ] `/me/apps` é carregado após login.
- [ ] Rotas frontend são derivadas de `app.routes`.
- [ ] `microfrontend` possui loader próprio.
- [ ] `iframe` possui renderer próprio.
- [ ] `backend-only` é ignorado na renderização visual.
- [ ] `route.entry` tem prioridade sobre `app.entryUrl`.
- [ ] Existe fallback para tipo desconhecido.
- [ ] Existe fallback para erro de carregamento.
- [ ] Existe loading de plugin.
- [ ] Eventos recarregam apps.
- [ ] Rota atual é validada após reload.

---

## 25. Pontos de atenção

1. O Portal consome DTO da Core API, não manifesto bruto.
2. `entryUrl` precisa estar acessível pelo Gateway.
3. Microfrontend pode falhar sem quebrar o shell.
4. Iframe pode ser bloqueado por headers de segurança.
5. Backend-only não deve aparecer como tela.
6. Rota não autorizada não deve renderizar plugin.
7. Eventos podem mudar rotas e permissões em tempo real.
8. O frontend não é segurança final.
9. Plugins devem consumir APIs com JWT válido.
10. Cache local de apps deve ser invalidável.

---

## 26. Documentos relacionados

```text
docs/06-portal-frontend/visao-geral-portal.md
docs/06-portal-frontend/menu-dinamico.md
docs/06-portal-frontend/app-authorization.md
docs/05-plugin-system/microfrontends.md
docs/05-plugin-system/iframe.md
docs/05-plugin-system/backend-only.md
docs/03-autenticacao-autorizacao/rbac.md
```

