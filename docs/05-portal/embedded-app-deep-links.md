# Deep links — apps embedded (iframe)

Apps com `renderMode: embedded` podem abrir uma rota interna ao clicar em notificação no portal.

> Tutorial completo (manifesto, SSO, notificações, deploy): [conectar-aplicacao-iframe.md](../10-guias-operacionais/conectar-aplicacao-iframe.md)

## Contrato da notificação (Core API)

```json
{
  "action": {
    "type": "portal_route",
    "label": "Abrir",
    "target": "/controle-mp"
  },
  "metadata": {
    "source": "meu_app",
    "deepPath": "/conversations/109",
    "event": "message:new"
  }
}
```

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `action.target` | Sim | `basePath` do app no portal (Admin → Apps) |
| `metadata.deepPath` | Sim | Rota **dentro** do iframe (React Router do filho) |
| `metadata.source` | Não | Identificador lógico (ex.: `controle_mp`) |

Sem `deepPath`, o clique só abre o app na rota raiz (comportamento `portal_route` padrão).

## Contrato no filho (iframe)

Escutar `postMessage` do portal:

```ts
window.addEventListener("message", (event) => {
  // Validar event.origin (domínio do portal pai)
  if (event.data?.type !== "DELPI_NAVIGATE") return;
  const path = event.data.path; // ex.: /conversations/109
  router.navigate(path);
});
```

Tipos já usados no ecossistema DELPI:

| Mensagem | Direção |
|----------|---------|
| `DELPI_AUTH_READY` | Filho → portal |
| `DELPI_AUTH` | Portal → filho |
| `DELPI_NAVIGATE` | Portal → filho |
| `DELPI_LOGOUT` | Portal → filho |

Implementação de referência: `controle_mp/front-cadastro-mp/src/app/sso/DelpiNavigateBridge.jsx`.

## Portal (código)

- `portal/src/utils/embeddedAppNotification.ts` — stash, evento, match de `basePath`
- `portal/src/utils/notificationNavigation.ts` — clique no card
- `portal/src/ui/AppHost.tsx` — `postMessage` com retry; só remove o stash após entregar ao iframe

## Filho (iframe) — ordem com SSO

1. Portal envia `DELPI_NAVIGATE` (deep link) e `DELPI_AUTH`.
2. O filho grava a rota em `sessionStorage` (`delpi.child.pending_navigate`) e navega.
3. Após o SSO, **não** redirecionar para `/conversations` se já houver rota pendente.

Referência Controle MP: `delpiEmbeddedNavigation.js`, `DelpiNavigateBridge.jsx`, `DelpiSsoBridge.jsx`.

## URL do portal

A barra do navegador permanece em `/controle-mp`; a conversa abre **dentro do iframe** (`/conversations/:id` no domínio do app).

## Aliases de rota

`resolvePortalRoute` alinha `action.target` ao `basePath` registrado e tolera `_` vs `-` (legado).

## Apps federated / external

- **federated**: usar `updateRoute` do module federation (outro fluxo).
- **external**: `action.type = external_url` ou abertura em nova aba.
