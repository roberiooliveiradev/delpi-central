# ENGINEERING.NC.ICON.PROD.R1 — Icon Fix & Production Evidence

- **Mission**: ENGINEERING.NC.ICON.PROD.R1
- **Executor**: Devin (CLI)
- **Date**: 2026-10-30
- **Scope**: exibir o ícone do item "Não conformidades" no catálogo/Início do Portal Engenharia, alinhado ao padrão dos demais itens; sem redesign, sem alterar rotas/permissões/comportamento.

---

## 1. Causa-raiz

- O catálogo da Home (`engineeringRouteCatalog.ts`, seção `work`) possui a rota `id: "nonconformities"` desde as fases T*, mas o mapa `ROUTE_ICONS` em `HomePage.tsx` — criado no commit `ba5a437788` (F3.R3) **antes** da rota NC existir — nunca recebeu a entrada correspondente.
- Resultado: `icon: ROUTE_ICONS["nonconformities"]` resolvia `undefined` e o `EngineeringSectionRouteCard` renderizava o item **sem ícone**, enquanto LMPs, Visão geral, Dashboard, Início e Ajuda renderizavam o seu.
- Não era chave incorreta, não era regressão de build, não era divergência de favoritos/recents — era **mapeamento ausente** (favoritos reutilizam o mesmo card/ícone; recents renderizam apenas label, sem ícone por design).

## 2. Correção

Fonte correta (mapa canônico de ícones do catálogo, não workaround visual):

`plugins/engineering/src/features/home/HomePage.tsx`
- import `ClipboardX` de `lucide-react` (mesma lib já usada; família visual `ClipboardList`/`ClipboardCheck` dos irmãos "Minhas solicitações"/"LMPs");
- `nonconformities: <ClipboardX size={16} aria-hidden="true" />` em `ROUTE_ICONS` — tamanho 16 e aria-hidden idênticos aos demais.

Sem CSS novo, sem adapter, sem mudança de contrato. Tema claro/escuro inalterado (o ícone herda a cor do card como os demais).

## 3. Evidência de testes

| Gate | Comando | Resultado |
|------|---------|-----------|
| Typecheck | `tsc -p tsconfig.app.json --noEmit` | 0 erros |
| Lint | `npm run lint` | 0 erros (14 warnings pré-existentes) |
| Unit | `npx vitest run` | **157/157** |
| Build | `npm run build` | OK — `App-Dbjuy5TQ.js` |
| Browser | Playwright `home-icon.spec.ts` (novo) | **6/6** — desktop+mobile+tablet |
| Regressão | Playwright `nonconformities.spec.ts` | **18/18** |
| Total E2E | suite completa | **24/24** |

Spec nova (`e2e/specs/home-icon.spec.ts`) autentica via SSO real e asserta:
- o item "Não conformidades" no catálogo da Home contém `<svg>` visível;
- paridade: "LMPs" e "Não conformidades" exibem ícone ("Minhas solicitações" não renderiza para o usuário dev — requer `my-requests.access`; favoritos usam o mesmo card).

Incidente de ambiente durante a homologação: `delpi-nc-sandbox` (Postgres dev) estava `Exited (255)` causando "Não conformidades indisponíveis" no primeiro run; reiniciado → suite verde. Não relacionado à correção.

## 4. Deploy

| Campo | Valor |
|-------|-------|
| SHA testado | (HEAD local + fix) |
| SHA deployado | ver seção de commits |
| Serviço alterado | **somente `delpi-engineering`** (MFE) |
| Comando canônico | `./infra/scripts/up-prod-sequential.sh --build engineering` via SSH `operador@192.168.1.237` |
| Health pós-deploy | container Up · `remoteEntry.js` 200 · bundle novo servido publicamente |
| Regressão | API/Core/Keycloak/gateway intocados · flags ACT preservadas |
| Rollback | rebuild do MFE em SHA anterior |

## 5. Resultado final

Item "Não conformidades" exibe `ClipboardX` (lucide) no Início/catálogo do Portal Engenharia, no mesmo padrão visual dos demais itens — validado em browser real (Playwright, SSO) em desktop, mobile e tablet, e deployado em produção.
