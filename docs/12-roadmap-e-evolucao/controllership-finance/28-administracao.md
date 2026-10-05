# 28 — Administração

## Estado

**TARGET / READY_FOR_IMPLEMENTATION_INVENTORY**

## Objetivo

**Administração** é a superfície governada para configuração e evolução dos cadastros próprios do Portal.

Ela consolida P6 — Administração e Configuração.

Fonte funcional principal:
- [13-p6-administracao-e-configuracao.md](./13-p6-administracao-e-configuracao.md)

## Rota lógica

```text
/apps/controllership-finance/administration
```

Permission:

```text
controllership-finance.manage
```

Não criar permissions adicionais por subseção, botão ou CRUD.


## Reuso obrigatório de `@delpi/plugin-ui`

Não há uma `AdministrationPage` completa canônica exportada. Administração deve ser composta com primitives do kit, sem recriar seus chromes.

Import base recomendado:

```ts
import {
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardSectionRouteCard,
  DataTableSection,
  createDashboardFiltersKit,
  FormGrid,
  FormActions,
  NativeTextField,
  NativeSelectField,
  NativeTextAreaField,
  ModalShell,
  ConfirmModalPanel,
  FloatingNoticeStack,
  StatusBadge,
  EmptyState,
  LoadingState,
} from "@delpi/plugin-ui/index";
```

Estilos/runtime:

```ts
await import("@delpi/plugin-ui/styles");
```

Mapeamento esperado:

| Necessidade | Reuso canônico |
|---|---|
| entrada/seções administrativas | `createDashboardSectionRouteCard` |
| cabeçalho/breadcrumb | `createDashboardPageHero` + `createDashboardPagePath` |
| listas de catálogos/templates | `DataTableSection` |
| filtros | `createDashboardFiltersKit` |
| formulários | `FormGrid` + Native form fields |
| ações de formulário | `FormActions` |
| confirmação/publicação/inativação | `ModalShell` / `ConfirmModalPanel` |
| feedback assíncrono | `FloatingNoticeStack` |
| estado/vigência | `StatusBadge` |
| loading/empty | `LoadingState` / `EmptyState` |

O domínio de templates, catálogos, vigência e auditoria permanece no Portal/BFF.

**DO NOT RECREATE:** tables, filter chrome, form controls, modal shell, confirm panel, notices e status badges já públicos no kit.

## Acesso

`MANAGE` administra.

`ACCESS` usa as configurações publicadas nas páginas operacionais, mas não altera o mestre.

```text
ACCESS != MANAGE
MANAGE_APPROVAL != EVIDENCE_VALIDATION
```

Validator/responsável operacional não vira MANAGE automaticamente.

## Áreas administrativas

A página deve organizar, conforme readiness/inventário:
- Templates de fechamento;
- Checklist;
- Bancos e contas;
- Responsáveis operacionais;
- Validadores;
- Destinatários;
- Motivos;
- Tipos/roles de anexo;
- Targets de notificação;
- Regras de satisfação/validação;
- Vigências;
- futuras configurações aprovadas do Portal.

Não transformar cada catálogo em item de topbar.

## Composição lógica

```text
AdministrationHome
→ AdministrationNavigation
→ TemplateManagement
→ CatalogManagement
→ EffectiveDateManagement
→ PublicationPanel
→ AuditHistory
→ ContextualHelp
```

## Template mestre

```text
DRAFT
→ REVIEW
→ PUBLISH
→ EFFECTIVE_FROM
```

Salvar não publica.

## Snapshot

Nova publicação não altera retroativamente competência aberta, histórico, pacote existente ou snapshot já criado.

## Inativação

```text
ACTIVE
→ INACTIVE_FROM(date)
```

Sem delete físico de referência histórica.

Exigir ator, timestamp, motivo quando aplicável e vigência.

## Configuração governada

```text
CONFIGURABLE != FREE_FORM_EVERYWHERE
```

Catálogos devem ter tipos/regras explícitos.

## Auditoria

Cobrir no mínimo criação/edição de draft, publicação, inativação, alteração de catálogo, ator, timestamp, before/after, motivo, vigência e correlation quando disponível.

## E/T

Continuam relevantes:
- E01 — seed/owner de bancos/contas;
- E05 — attachment roles;
- E06 — motivos;
- T02 — notificações;
- demais inventories técnicos conforme slice.

Não reabrir esses itens como product design sem nova evidência.

## Estados

Cobrir `LOADING`, `EMPTY`, `ERROR`, `FORBIDDEN`, `NOT_FOUND`, validation error, conflict/stale version quando houver concorrência e success.

## UX

- ações destrutivas/corretivas confirmadas;
- publicação deve deixar vigência clara;
- histórico acessível;
- teclado/foco;
- desktop/mobile;
- claro/escuro;
- Help contextual.

## Não objetivos

Administração não autoriza usuário no lugar do Core, não configura permission codes dinamicamente, não altera dados TOTVS diretamente, não valida evidência operacional, não sacramenta estoque e não apaga histórico.
