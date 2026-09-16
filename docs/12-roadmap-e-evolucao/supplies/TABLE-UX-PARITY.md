# TABLE-UX-PARITY — Portal Suprimentos

> **Status:** PLANNED / transversal · **não autoriza implementação por si só**.  
> **Referência visual/funcional:** Portal Comercial.  
> **Authority de componentes compartilhados:** `@delpi/plugin-ui`.  
> **Regra:** inventariar antes de copiar; nenhuma paridade 1:1 é presumida.

---

## 1. Objetivo

Evoluir as superfícies tabulares do Portal Suprimentos para uma experiência consistente com a Minha DELPI, usando o Portal Comercial como referência de UX e o `@delpi/plugin-ui` como caminho preferencial para capacidades reutilizáveis.

A intenção não é copiar a tabela Comercial inteira para `plugins/supplies`. O objetivo é separar:

1. capacidades tabulares realmente transversais da plataforma;
2. comportamentos específicos do domínio Comercial;
3. necessidades próprias de cada página de Suprimentos.

A implementação continua obedecendo ao fluxo page-by-page e ao GATE-FEATURE de cada página.

---

## 2. Baseline compartilhável candidato

Antes da próxima página cuja superfície principal seja tabular, executar inventário bounded `Portal Comercial × @delpi/plugin-ui × Portal Suprimentos` e classificar cada capacidade como `PROVEN | TO_INVENTORY | PLANNED | TARGET`.

Capacidades candidatas ao padrão compartilhado:

| Capacidade | Diretriz |
|---|---|
| Ordenação por coluna | compartilhar quando o contrato/backend suportar sem semântica ambígua |
| Exibir/ocultar colunas | preferência de apresentação; não altera AuthZ nem payload autorizado |
| Reordenar colunas | preferência de apresentação persistível quando houver mecanismo canônico |
| Persistência de preferências | navegador ou serviço canônico conforme contrato da página; não inventar sync de conta |
| Densidade/tamanho de fonte | usar primitivo/tokens compartilhados; não CSS isolado por página |
| Paginação | preservar paginação e limites do contrato backend |
| Loading/empty/error | usar estados canônicos do kit |
| Teclado/foco | navegação e controles operáveis por teclado, foco visível |
| Responsividade | desktop completo; mobile deve permanecer utilizável sem corte crítico |
| Light/dark | somente tokens do Portal/kit |
| Exportação | somente quando a capability e o contrato da página autorizarem |

Essas capacidades são candidatas a padronização; só viram contrato de implementação quando o inventário provar suporte e a página for promovida.

---

## 3. Funcionalidades que NÃO são baseline automático

Recursos existentes no Portal Comercial não são herdados automaticamente por Suprimentos.

Exemplos:

- alternância `Tabela / Cards / Board`;
- alternância de unidade de domínio, como `Milheiro / Peças`;
- ações ou colunas específicas do fluxo Comercial;
- regras de cobertura, faturamento, estoque comercial ou outras semânticas de outro bounded context;
- qualquer exportação sem capability/contrato explícito.

Esses recursos entram somente quando a jornada de Suprimentos provar necessidade própria.

---

## 4. Arquitetura e ownership

```text
Portal Comercial
  = referência de experiência e inventário de capacidades existentes

@delpi/plugin-ui
  = owner preferencial de primitivos/componentes reutilizáveis de tabela

plugins/supplies
  = composição e UX específica da página
  = não deve duplicar componente compartilhável do kit

supplies-api / owners backend
  = contratos, paginação, ordenação, export e AuthZ quando aplicáveis
```

Regras:

- `@delpi/plugin-ui` vem antes de novo componente reutilizável local;
- não copiar CSS/componentes do Comercial para o MFE de Suprimentos;
- preferências visuais não concedem acesso a dados;
- coluna oculta na UI não substitui AuthZ;
- ordenação/filtro/export server-side seguem o contrato do owner correto;
- nenhuma permission nova é criada apenas por existir controle de tabela.

---

## 5. Readiness obrigatório para nova superfície tabular

Ao promover uma página materialmente tabular, o Cursor deve provar:

1. quais capacidades a tabela equivalente/referência do Comercial realmente implementa;
2. quais dessas capacidades já existem no `@delpi/plugin-ui` no HEAD;
3. quais capacidades a jornada de Suprimentos realmente necessita;
4. quais dependem de contrato backend novo;
5. quais são apenas preferência visual local;
6. quais são específicas de outro domínio e ficam fora;
7. menor diff correto para reuso compartilhado.

Se uma capacidade necessária for reutilizável e estiver ausente do kit, avaliar mudança no `plugin-ui` antes de criar abstração equivalente em `plugins/supplies`.

`search miss != ausência`: abrir implementação, exports e testes reais antes de declarar gap.

---

## 6. Relação com a fila do Portal Suprimentos

Esta frente é transversal e **não cria nova etapa de produto nem altera a ordem da fila**.

Ela deve ser aplicada quando uma página tabular for efetivamente promovida. Exemplos futuros que podem consumir o padrão:

- Entregas / Atrasos;
- Controle de Estoques;
- Fornecedores;
- Produtos / MP;
- outras worklists/listas aprovadas posteriormente.

Em particular, `Fornecedores` continua previsto como lista/busca e `Fornecedor 360` como ficha separada; a existência desta diretriz não autoriza E13/E14 antecipadamente.

---

## 7. Critérios de aceite quando a padronização for executada

A página só declara a capacidade tabular implementada quando houver evidência correspondente:

- componente/contrato no owner correto;
- testes de ordenação/colunas/preferências quando aplicável;
- positive + sibling + negative para ações protegidas, como export;
- desktop/mobile;
- light/dark;
- teclado/foco;
- persistência de preferências comprovada no mecanismo escolhido;
- nenhuma chamada direta MFE → `api-delpi`;
- Help sincronizada se o controle exigir explicação user-facing;
- smoke federado quando material; indisponível = `INCONCLUSIVE`, nunca PASS inferido.

---

## 8. Decisão vigente

```text
Portal Comercial = referência de UX
@delpi/plugin-ui = caminho preferencial de reuso
Portal Suprimentos = não copiar tabela 1:1
paridade = por capacidade comprovada
Cards/Board/unidades de domínio = opt-in por jornada
fila de páginas = inalterada
implementação = somente após promoção/autorização da página correspondente
```

---

## 9. Purchase Orders (WF-05/WF-06) — inventário executado

Evidência no HEAD após conclusão UX da lista + ficha (sem promover paridade total com Comercial):

| Capability | Comercial | plugin-ui | Supplies (PO) | Backend necessário? | Decisão |
|---|---|---|---|---|---|
| DataTable canônico | sim | sim | HTML + toolbar kit | não | **RESIDUAL** — tabela própria; toolbar/prefs via kit |
| sort server-side | sim | sim | — | sim (`sort`/`order_by` ausente em GET `/purchase-orders`) | **BLOCKED_BY_CONTRACT** |
| column visibility | sim | sim | sim (`useTableColumnVisibility`) | não | **IMPLEMENTED** |
| column reorder | sim | sim (`TableColumnVisibilityMenu`) | sim | não | **IMPLEMENTED** |
| persisted preferences | sim | localStorage kit | chaves `supplies:purchase-orders:*` | não | **IMPLEMENTED** |
| font size | sim | sim | sim | não | **IMPLEMENTED** |
| pagination | sim | `createCompactPagination` | sim | não (page/page_size/total na URL) | **IMPLEMENTED** |
| Excel export | sim | sim | — | sim (sem rota/capability PO) | **BLOCKED_BY_CONTRACT** |
| table/cards/board | sim | sim | — | — | **OUT_OF_SCOPE** |
| mobile overflow | sim | — | sim (region + scroll) | não | **IMPLEMENTED** (preservado) |
| attention chips | sim | `ScopeChipBar` | Atenção Todos/Atrasados | não (`late_only`) | **IMPLEMENTED** |
| refresh + freshness | sim | — | Atualizar + horário local | não | **IMPLEMENTED** |
