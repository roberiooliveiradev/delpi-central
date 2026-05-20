# Deep links — apps embedded (iframe)

Apps com `renderMode: embedded` podem abrir uma rota interna ao clicar em notificação no portal.

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
- `portal/src/ui/AppHost.tsx` — `postMessage` com retry após load do iframe

## Aliases de rota

`resolvePortalRoute` alinha `action.target` ao `basePath` registrado e tolera `_` vs `-` (legado).

## Apps federated / external

- **federated**: usar `updateRoute` do module federation (outro fluxo).
- **external**: `action.type = external_url` ou abertura em nova aba.
