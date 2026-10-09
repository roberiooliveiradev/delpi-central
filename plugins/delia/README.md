# DÉLIA MFE — bootstrap C1

Standalone federated frontend da DÉLIA (`plugins/delia/`).

## Escopo atual (C1-T3 / C1-T4)

- pasta MFE independente
- Module Federation (`./App` → `bootstrap.tsx`)
- consumo runtime de `@delpi/plugin-ui`
- mount / unmount / updateRoute compatíveis com Portal AppHost e com o companion dock do Portal
- shell mínimo + baseline responsivo/a11y
- o Portal pode abrir a mesma federação `delia` / `./App` num companion dock quando `/me/apps` inclui `id=delia` e o workspace comporta o split; a página completa continua em `/apps/delia`
- manifesto de publicação: `delpi.manifest.json` (owner DÉLIA; registry owner = Core)
- sem Chat runtime, sem captura de mídia automática
- Gateway/Compose/registro Core live **ainda não** feitos nesta fase

## Manifesto

Arquivo: [`delpi.manifest.json`](./delpi.manifest.json)

- `id=delia`, `basePath=/apps/delia`, `entry=/apps/delia/assets/remoteEntry.js`
- `ui.renderMode=federated`
- `delia.access` = Product Master APPROVED (C1-T4D1) bootstrap/platform-access permission (shell + `/apps/delia` visibility only; ≠ business/Domain/ACT AuthZ)
- `backend.serviceName=delia-api`, `baseUrl=/apps/delia-api`
- Portal default `exposedModule=./App` (campo não existe no schema)

Registro Core e atribuição RBAC (ops; **não** feitos em C1-T4/T4D1):

```bash
TOKEN=... bash scripts/register-manifest.sh
```

## Scripts

```bash
cd plugins/delia
npm install
npm test
npm run build
npm run verify:federation
```

Dev standalone: `npm run dev` (requer plugin-ui remoto conforme convenção da plataforma).

## Modo demonstração (dev/preview apenas)

Fixtures locais permitem exercitar a interface conversacional sem chamadas ao backend ou ao modelo. O modo é **OFF por padrão** e só existe quando o bundle roda em `import.meta.env.DEV` (`npm run dev`) ou foi deliberadamente buildado com `VITE_DELIA_DEMO=1` (decisão de ambiente/preview). Produção normal nunca entra nesse caminho.

Ativação explícita por query param:

```text
/apps/delia?delia-demo=<cenário>
```

Cenários: `simple` (default) · `long` · `clarification` · `source_unavailable` · `authz_denied` · `precondition` · `confirmation` (visual-only, sem ACT) · `error` · `loading`.

Garantias: zero chamadas de rede (`/interaction/turns` nunca é invocado), banner persistente `Modo demonstração — dados simulados`, respostas marcadas como simulação (`NON_GROUNDED`, sem provenance), nada persistido. Para desativar, remova o query param — não há estado ou toggle persistente.

Fonte: [`src/demo/demoMode.ts`](./src/demo/demoMode.ts) · testes: [`src/demoMode.test.tsx`](./src/demoMode.test.tsx)
