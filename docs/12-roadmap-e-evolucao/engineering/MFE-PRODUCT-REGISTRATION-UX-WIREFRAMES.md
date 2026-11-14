# MFE Portal Engenharia — Controle e Cadastro de Produtos: UX, wireframes e fluxo visual

> **Decisão funcional superveniente PRC-REF-022 (2026-11-10):** fluxo único Enviada → Em atendimento ⇄ Devolvida para correção → Concluída, editor compartilhado create/read/edit. O adendo REF-022 ao final deste documento prevalece sobre fluxos legados contraditórios. `IMPLEMENTED_DEV`.

> **Estado:** `TARGET / UX_CONTRACT_SPECIFIED / IMPLEMENTATION_PENDING / VISUAL_QA_NOT_RUN` · **Decisão do Product Owner:** redesign completo antes de deploy de produção (2026-11-07).
>
> **Escopo:** somente experiência `plugins/engineering/src/features/product-registration/` e sua navegação no Portal Engenharia. Não altera domínio, TOTVS, owners, RBAC ou os seis tools MCP.
>
> **Documento associado:** [matriz de componentes e QA](./MFE-PRODUCT-REGISTRATION-COMPONENTS-AND-ACCEPTANCE.md).
>
> **Regra prioritária:** `PRODUCTION_DEPLOY_SUSPENDED / VISUAL_ACCEPTANCE_REQUIRED`. Esta especificação NÃO autoriza deployment ou ativação operacional.

## 0. Diagnóstico verificado em fonte e capturas do Product Owner

- A home DEV já apresenta **Controle e Cadastro de Produtos** separado de **Produtos**. A rota interna `/apps/engineering/product-registration` apresenta uma fila e `/apps/engineering/product-registration/{uuid}` abre detalhe.
- As capturas DEV mostram: tabela sem respiro/alinhamento, filtros comprimidos, UUID bruto de responsável, largura ociosa, conteúdos de ficha/ações/histórico empilhados e hierarquia inconsistente com a home.
- `PrcQueuePage.tsx` (fonte consultada) usa `section`, `input`, `select`, `button` e `table` nativos, sem a façade visual do MFE.
- `PrcDetailPage.tsx` (fonte consultada) agrupa identificação, ficha, alterações, ações, verificação, revisões e timeline em uma única página longa, também com `table` e `input` básicos.
- `ProductRegistrationFeature.tsx` resolve apenas `queue` e `detail`. Nova solicitação e outras áreas descritas abaixo são **target UX**; só devem virar rotas novas se contracts/routes/owner e necessidade real forem demonstrados.
- `plugins/engineering/src/ui/engineeringUi.ts` já expõe façade sobre `@delpi/plugin-ui/index`. A feature `products` usa essa façade e `DataTableSection` como referência implementada. Nomes dos componentes efetivamente inventariados estão na matriz vinculada.
- Nenhuma captura comprova fluxo visual completo, responsividade ou formulário guiado de nova solicitação. Evitar status `PROVEN` para essas metas.

## 1. Sistema visual e regras de composição

**Produto:** Portal Engenharia; **módulo:** Controle e Cadastro de Produtos. Usar tema/tokens/typografia do `@delpi/plugin-ui` via façade local, não paleta paralela nem CSS global novo. O tom é corporativo, técnico, enxuto e legível.

- Container fluido com largura útil, gutters consistentes com as demais features; cabeçalho e ações com alinhamento idêntico ao módulo `Produtos`.
- Superfícies em cards/sections discretas, com hierarquia `breadcrumb > título + descrição > estado/ação > conteúdo`; jamais apresentar dados e mutações sem delimitação.
- Uma ação primária contextual por view (ou por etapa do formulário); ações destrutivas ou terminais com confirmação explícita.
- Status como badge semântico e texto completo. Não depender de cor para transmitir status.
- Datas em formato local coerente; identificador curto visível com possibilidade de copiar ID integral. Nunca exibir UUID de pessoa como rótulo de responsável.
- Layout/cores/tamanhos: **herdar tokens existentes**, e não hardcode de valores do protótipo de conversa.
- O backend determina `allowedActions`, escopo, permissões, versão, idempotência e resultado de verificação. Frontend apenas apresenta estados/canais e captura intenção.

### 1.1 Navegação e IA de informação

```text
Portal Engenharia / Caminhos e funcionalidades / Trabalho
   |-- Produtos (consulta oficial preexistente — preservar)
   '-- Controle e Cadastro de Produtos
         |-- 01 Central de solicitações [ROTA EXISTENTE]
         |     '-- 02 Nova solicitação [FLUXO TARGET: etapa/página ainda a confirmar]
         '-- 03 Detalhe da solicitação [ROTA EXISTENTE /{requestId}]
               |-- Visão geral: identidade + estado + próximos passos
               |-- 04 Ficha técnica: leitura/edição seletiva
               |-- 05 Verificação TOTVS: diff + evidências + confirmação
               |-- 06 Histórico e revisões: eventos + snapshots imutáveis
               '-- 07 Acompanhamento simplificado: variante de apresentação,
                    MESMA rota/API/AuthZ, sem criar outro papel
```

`Products` e `Product Registration` não são a mesma feature. Navegar por URL interna estável, preservando back/forward/F5 e deep link; abas podem usar `?tab=` apenas após inventariar o padrão de `products` e testes.

## 2. Wireframe 01 — Central de solicitações

**Entrada:** `/apps/engineering/product-registration`; **implementação atual:** `PrcQueuePage.tsx`.

```text
┌ Portal Engenharia / Controle e Cadastro de Produtos ─────────────────────────────┐
│ SOLICITAÇÕES DE PRODUTOS                           [+ Nova solicitação]          │
│ Gerencie cadastros e alterações de matérias-primas autorizados.                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│ [ Em aberto — ]       [ Em atendimento — ]       [ Em revisão — ]               │
│ (contadores somente se contrato fornecer agregado confiável; senão OMITIR)      │
├─────────────────────────────────────────────────────────────────────────────────┤
│ [Todas] [Em andamento] [Concluídas]                                            │
│ [ Buscar nº / código / descrição / solicitante ... ] [Tipo ▼] [Status ▼] [Mais] │
│ ┌ Solicitações ───────────────────────────────────────────────────────────────┐ │
│ │ Nº/descrição │ Tipo │ Solicitante │ Abertura │ Status │ Responsável │ Abrir │ │
│ │ #3bace5e3   │ Cria │ ...         │ ...      │ badge  │ Nome / —    │  ›   │ │
│ │ #b867e2ff   │ Cria │ ...         │ ...      │ badge  │ Nome / —    │  ›   │ │
│ ├────────────────────────────────────────────────────────────────────────────┤ │
│ │ X itens autorizados                                [‹] Página n de m [›]  │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Estrutura:** `EngineeringPagePath` + `EngineeringPageHero`, ação `EngineeringActionButton`, métricas `EngineeringMetricStrip`/`EngineeringKpiCard` **condicionais ao contrato**, filtros `EngineeringFiltersRow`/`EngineeringFilterInput`/`EngineeringFilterSelect`, `DataTableSection`, `EngineeringStatusBadge`, `EngineeringEmptyState`, `EngineeringLoadingActivityCard`, `EngineeringStateBanner`.

**Dados:** `fetchPrcQueue` já fornece items/total/page e filtros status/type/search, conforme código atual; NÃO inventar busca por descrição, métricas ou endpoint de agregados caso API não ofereça esses recursos. `Responsável` deve usar display name validado se disponível; senão `Não atribuído` ou fallback honesto (não exibir GUID bruto). A lista deve preservar filtros/página em navegação e evitar resultados de resposta obsoleta.

**Ações:** abrir detalhe; atualizar; nova solicitação só fica ativa quando existir intake UI governado. Filtro de status com vocabulário real: enviada, em atendimento, aguardando informações, em revisão, concluída, rejeitada. Badge conforme API.

**Estados:** loading com skeleton; empty por ausência de dados vs zero resultados filtrados; 403 com mensagem e volta; erro com retry; refresh sem perder filtros; paginação visível e acessível; status suficiente também em texto.

## 3. Wireframe 02 — Nova solicitação (CREATE/UPDATE)

**Status:** `TARGET` — não existe terceira rota confirmada em `ProductRegistrationFeature.tsx`; reaproveitar intake oficial e planejar a menor experiência possível.

```text
┌ Voltar à fila    Nova solicitação ───────────────────────────────────────────────┐
│ [ 1 Identificação ] ─── [ 2 Dados técnicos ] ─── [ 3 Revisar e enviar ]       │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ETAPA 1 · O QUE PRECISA SER FEITO?                                              │
│ ┌ Novo produto ───────────┐  ┌ Alterar produto existente ─────────────────┐   │
│ │ criar matéria-prima     │  │ localizar código oficial e revisão-base    │   │
│ └─────────────────────────┘  └────────────────────────────────────────────┘   │
│ Descrição *          [.....................................................]  │
│ Justificativa        [.....................................................]  │
│ Solicitante          [derivado da identidade; não-editável]                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ETAPA 2 · FICHA TÉCNICA                                                        │
│ [Identificação] [Estoque/contabilidade] [Fornecedores]                          │
│ Grupo / Tipo / Unidade / Armazém / B1_CONTA / Referência / Terceiros          │
│ Fornecedores: código + loja + nome + PN opcional + catálogo                    │
│ Alteração: [✓ alterar este campo] [valor anterior] [novo] [justificativa]     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ETAPA 3 · REVISAR                                                               │
│ [Resumo] [Campos obrigatórios faltantes] [Mudanças propostas]                 │
│ Nota: enviar solicitação NÃO cadastra diretamente no TOTVS.                   │
│ [Cancelar]                                    [Voltar] [Enviar solicitação]   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Componentes-alvo:** `EngineeringPagePath`, `EngineeringPageHero`, `EngineeringSectionCard`, `EngineeringDetailCard`, `EngineeringFieldLabel`, `EngineeringFilterInput`/select quando compatíveis, `EngineeringActionButton`, `EngineeringStateBanner`; stepper, radio-card, textarea, validation summary e modal devem ser **inventariados no plugin-ui antes de introduzir**. Não inventar exports.

**Contrato e comportamento:** intake REST existente; autenticação define `requesterSubject`, backend controla idempotência/validation; criação e alteração divergem no campo código oficial, revisão-base e deltas. Validação em etapas não substitui validação de backend. `partNumber` aceita omitido/null/vazio; nunca inventar PN nem igualar a `catalogNumber`. Em UPDATE, omissão de path não equivale a limpar campo. Evitar perda de draft ao voltar etapa; confirmar descarte de mudanças.

**Critério:** sucesso navega ao detalhe e mostra número/status reais; falha de backend mantém valores e aponta o campo; não introduzir escrita ERP.

## 4. Wireframe 03 — Detalhe e andamento da solicitação

**Entrada:** `/apps/engineering/product-registration/{requestId}`; **implementação atual:** `PrcDetailPage.tsx`.

```text
┌ Engenharia / Solicitações / #978351f6 ─────────────────────────────────────────┐
│ Cadastro de matéria-prima                    [badge Enviada] [Iniciar atendimento]│
│ Código oficial: Aguardando cadastro • Solicitante: Nome • Tipo: Criação          │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ANDAMENTO                                                                     │
│ [Enviada ✓]──[Em atendimento]──[Em revisão]──[Concluída]                        │
│ Eventos especiais: aguardando informações / rejeitada (não avanço linear).     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ┌ Identificação ────────────────────┐ ┌ Próximas ações ──────────────────────┐ │
│ │ Solicitante: Nome                 │ │ Estado/next step explanatory         │ │
│ │ Responsável: Não atribuído       │ │ [Ação permitida] [Outras ações ...]  │ │
│ │ Abertura: data + hora            │ │ Alertas e justificativas obrigatórias│ │
│ │ Código TOTVS: —                  │ └─────────────────────────────────────┘ │
│ └───────────────────────────────────┘                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│ [Visão geral] [Ficha técnica] [Verificação TOTVS] [Histórico] [Revisões]      │
│ ┌ Área da aba selecionada ───────────────────────────────────────────────────┐ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Componentes:** `EngineeringPagePath`, `EngineeringPageHero`, `EngineeringStatusBadge`, `EngineeringDetailCard`, `EngineeringDetailFieldGrid`, `EngineeringActionButton`, `EngineeringStateBanner`; para eventos `EngineeringTimeline` quando props compatíveis. Tabs/step progress devem ser reutilizados do kit se existir; caso contrário desenho local mínimo governado por semântica/teclado. Não inferir finalização pela porcentagem linear.

**Ações:** `allowedActions` é source de disponibilidade em runtime; mostrar uma ação primária e demais ações coerentes, sempre diferenciando reabrir, solicitar informações, rejeitar, enviar para revisão, verificar/concluir. Mutações sensíveis exigem motivo/confirm modal quando contrato determinar. Persistir expectedVersion/CAS; atualizar detalhe após resultado. Não oferecer botões apenas porque o usuário tem `engineering.access`.

**Acessibilidade:** abas com roles/aria/keyboard, foco após navegação, feedback de mutation em live region, layout responsivo de cabeçalho e ações.

## 5. Wireframe 04 — Ficha técnica (visualização e edição seletiva)

**Implementar como aba do detalhe**, não como nova fonte oficial.

```text
┌ FICHA TÉCNICA                                   [Editar (se allowed)] ─────────┐
│ ┌ Identificação e classificação ─────────────────────────────────────────────┐ │
│ │ Descrição / Tipo / Grupo / Unidade                                        │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
│ ┌ Estoque e contabilidade ───────────────────────────────────────────────────┐ │
│ │ Armazém padrão / Conta contábil B1_CONTA / Terceiros / Referência cliente│ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
│ ┌ Fornecedores ──────────────────────────────────── [+ Adicionar permitido] ┐ │
│ │ Fornecedor/Loja │ Nome │ Part Number (opcional) │ Catálogo │ [ações]     │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
│ UPDATE (somente):                                                              │
│ [✓ Campo selecionado]  [Valor base] → [Valor proposto]  [Motivo]               │
├─────────────────────────────────────────────────────────────────────────────────┤
│ (somente em edição)   [Cancelar]             [Salvar alterações]               │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Componentes:** `EngineeringDetailCard`, `EngineeringDetailFieldGrid`, `EngineeringSectionCard`, `EngineeringFieldLabel`, `EngineeringActionButton`, `EngineeringStateBanner`, `DataTableSection` na seção fornecedores se adequado. Inputs/selects/checks devem preferir kit oficial existente; sem duplicação de formulário/CSS.

**Regras:** modo leitura separado de modo edição. `canEdit` baseado em `allowedActions.includes("edit_draft")`. Campo selecionado em UPDATE não se infere por truthiness; PN vazio pode ser delta explícito, PN omitido = não alterar. Não permitir edição em `under_review` se backend não autorizar. Validar campo/limites e mostrar motivo obrigatório junto à alteração. Falha 409 oferece refresh/resolve, sem overwrites silenciosos. Salvar é PATCH seletivo com expectedVersion e idempotência do contrato, com auditoria.

## 6. Wireframe 05 — Verificação oficial TOTVS / conclusão

**Aba do detalhe** que apresenta leitura oficial, comparação e decisão terminal.

```text
┌ VERIFICAÇÃO OFICIAL TOTVS ─────────────────────────────────────────────────────┐
│ Fonte: api-delpi → TOTVS • Código oficial • horário/fonte se oficialmente dado│
│ [Status: Nunca verificado | Correspondente | Divergente | Não verificável]     │
├─────────────────────────────────────────────────────────────────────────────────┤
│ CAMPO              ESPERADO           OFICIAL             RESULTADO           │
│ Descrição          ...                ...                 ✓ matched           │
│ Conta B1_CONTA     ...                ...                 ✓ / × / ?           │
│ Fornecedor/loja    ...                ...                 ✓ / × / ?           │
│ Part Number        vazio / texto      vazio / texto       ✓ / × / ?           │
│ ...                                                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│ [detalhes por campo e vínculo] [evidências auditáveis]                         │
│ Mismatch/ausência/permissão/timeout => BLOQUEAR conclusão e explicar.          │
│ MATCH completo + allowedAction + confirmação: [Verificar e concluir]          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Componentes:** `EngineeringPageHero` (em page), `EngineeringSectionCard`, `DataTableSection`, `EngineeringStatusBadge`, `EngineeringStateBanner`, `EngineeringActionButton`, `EngineeringLoadingActivityCard` e `EngineeringEmptyState`.

**Operação:** a comparação é resultado **do backend**, não diff inventado no frontend. Não dizer `matched` antes de executar. `verify_and_complete` é operação acoplada e terminal: o CTA deve informar que relê TOTVS e só publica se match, com confirmação antes de ato irreversível. Completude de campos (incl. B1_CONTA e SA5) e freshness são decisões de domínio/owner; nunca preencher dado ausente com `—` e tratar como PN vazio. PN presente e diferente bloqueia; atributo oficial ausente resulta `unverifiable`; usuário sem permissão, erro upstream e status inválido bloqueiam. Após sucesso mostrar revisão, verification id e histórico; após erro manter contexto e expor campos divergentes.

## 7. Wireframe 06 — Histórico e revisões

**Implementar em abas do detalhe** (dois subpainéis, não três tabelas empilhadas).

```text
┌ HISTÓRICO (timeline) ──────────────────────────────────────────────────────────┐
│ ○ Solicitação enviada       data/hora • autor • origem                        │
│ │   Metadados e justificativa (expandir)                                     │
│ ○ Atendimento iniciado      data/hora • responsável                          │
│ │   Alterações e eventos por ordem real                                      │
│ ○ Verificação oficial       data/hora • resultado e evidência                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│ REVISÕES                                                                       │
│ [Revisão] [Publicado em] [Responsável] [Verificação] [Visualizar snapshot]    │
│ Selecionar duas (quando permitido) → Comparação antes/depois por field path   │
│ Histórico de revisão é IMUTÁVEL; nunca há botão Editar revisão publicada.    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Componentes:** `EngineeringTimeline` (verificar contrato de props), `EngineeringDetailCard`, `DataTableSection`, `EngineeringStatusBadge`, `EngineeringEmptyState`; comparação de revisões via `EngineeringDetailFieldGrid` ou grid aprovado conforme payload. `fetchPrcTimeline`, `fetchPrcRevisions` e `fetchPrcVerifications` já existem como chamadas no detalhe; comparação entre revisões é `TARGET` dependente de snapshots disponíveis — não inventar API.

**Estados:** ledger em ordem cronológica real; data/autor e motivo quando disponíveis; diff por campo, não JSON bruto; 403, 404, lista vazia, revisão inexistente, histórico parcial e falha de fonte tratados com honestidade.

## 8. Wireframe 07 — Acompanhamento simplificado

**Não criar novo RBAC nem outro Portal.** É uma variante de organização da mesma página de detalhe, para legibilidade quando usuário acompanha um caso.

```text
┌ ACOMPANHAR SOLICITAÇÃO #... ───────────────────────────────────────────────────┐
│ [Status atual + explicação em linguagem simples]                              │
│ Etapa atual / próximo passo conhecido (não inventar SLA)                      │
│ Tipo • Solicitante • Responsável/Não atribuído • Código oficial/pendente     │
│ [Resumo técnico somente leitura]   [Ver histórico]   [Ver detalhes]           │
│ [Ações permitidas pelo backend, se houver]                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

**Componentes:** `EngineeringDetailCard`, `EngineeringStatusBadge`, `EngineeringDetailFieldGrid`, `EngineeringActionButton`, `EngineeringTimeline` e `EngineeringStateBanner`.

**Decisão:** apresentar informações progressivamente; não presumir identidade de solicitante como limitação de CRUD, pois `engineering.access` concede workflow operacional e o backend preserva regras de estado, identidade e escopo legítimos.

## 9. Breakpoints, densidade e acessibilidade

- Desktop: fila em tabela alinhada, filtros em linha, KPI cards (se dados), detalhe em duas colunas e abas no conteúdo; usar largura útil do MFE sem deixar grande área vazia.
- Tablet: cards em uma ou duas colunas conforme o kit, filtros em painel ou wrap, tabela com prioridades de coluna ou scroll controlado.
- Mobile: lista de cards em vez de tabela esmagada, filtros recolhidos, detalhes em coluna única, abas acessíveis por scroll/teclado, barra de ações sem cobrir conteúdo.
- **Breakpoints/tokens reais vêm do kit.** Números de uma maquete não são definição de design system.
- A11y: labels associados, foco visível, navegação teclado, texto para status, aria-live em mutations, contrastes do tema, acessibilidade das confirmações, table headings e organização responsiva.
- Experiências de loading, empty, filtered-empty, 401, 403, 404, 409/CAS, 422/form field, 5xx, api-delpi indisponível, match/mismatch/unverifiable e sucesso devem ter estados distintos (matriz complementar).

## 10. Limites de autoridade e critérios de aprovação

1. **Portal/MFE** apenas UI e workflows legítimos; **Engineering API** dados, regras, CAS, auditoria, publicação; **api-delpi** leitura TOTVS; **TOTVS** SoT. Nenhuma escrita ERP, nova ferramenta MCP ou novo RBAC.
2. Permissões vigentes: `engineering.access` operacional; `engineering.manager` administração. `allowedActions` do backend governa ações por estado.
3. Revisão publicada é imutável. PROVENANCE de fonte, dados e resultado é preservada.
4. Nova abstração/componentes só após inventário e Abstraction Gate; reutilizar `engineeringUi.ts` e `@delpi/plugin-ui`.
5. **Não publicar em produção** antes do redesign implementado, testes de UX e aceite visual do PO; gates funcionais HML e segurança continuam independentes.
6. Aceite mínimo: home distingue Produtos/PRC, fila legível e filtrável, abertura da solicitação, detalhe com tabs e cards, ficha adequada, verificação clara, timeline/revisões, responsividade, 401/403/409/erro e screenshots de browser real em DEV/HML; não aceitar apenas build ou inspeção DOM.
7. Status final deste documento: `TARGET`; não afirmar que wireframes representam UI já entregue.

## 11. Sequência de implementação e validação visual

**UX-0:** inventário de design system, props/export e contratos API; comparação com telas `products` e `lmps`.  
**UX-1:** infraestrutura de composição e central de solicitações.  
**UX-2:** detalhe, breadcrumbs, estado, ações, abas.  
**UX-3:** nova solicitação, edição seletiva e fornecedores.  
**UX-4:** verificação oficial, histórico, revisões, diff.  
**UX-5:** QA por browser real (desktop/tablet/mobile), acessibilidade, regressão REST/EVA, screenshots e aceite PO.  

Cada incremento deve apresentar before/after, componente reutilizado, lacunas reais do kit, testes e outcomes. Nenhum deploy produtivo por este plano.


## Trilha executável Devin — refatoração integral do MFE (2026-11-07)

**Plano canônico de execução:** [MFE-PRODUCT-REGISTRATION-DEVIN-IMPLEMENTATION-PLAN.md](./MFE-PRODUCT-REGISTRATION-DEVIN-IMPLEMENTATION-PLAN.md), cobrindo `MFE-PRC-UX0..UX5`, componentes confirmados em `@delpi/plugin-ui`/façade `engineeringUi.ts`, wireframes 01–07, mapa de arquivos, REST real (inclusive intake CREATE/UPDATE), responsividade, testes, screenshots e critérios de aceite. O executor Devin deve implementar a trilha inteira em DEV, com backend e owners preservados, sem inventar API/export. **`PRODUCTION_DEPLOY_SUSPENDED` até refatoração + QA visual real + aceite PO e gates funcionais separados.** Este adendo é documentação/plano, não implementação nem autorização produtiva.


## Wireframe aprovado V2 — Fornecedores em tabela com busca expansível (2026-11-08)

O PO aprovou nova apresentação **sem duplicar código/loja/razão social**: colunas separadas **[Lupa] | Código | Loja | Razão social | Nome fantasia | Part Number | Catálogo | [Lixeira]**. A lupa antes do código abre pesquisa colapsável **dentro da linha** para código, razão social ou fantasia. Botões de adicionar/remover com ícones oficiais. Seleção do SA2 preenche código/loja/razão social; PN e catálogo permanecem atributos editáveis/opcionais. **Especificação canônica e critérios de aceite**: [MFE-PRC-WIREFRAME-FORNECEDORES-V2-APPROVED.md](./MFE-PRC-WIREFRAME-FORNECEDORES-V2-APPROVED.md). **Arte visual SVG**: [prc-fornecedores-wireframe-v2.svg](./assets/prc-fornecedores-wireframe-v2.svg). Escopo proposto D11; `PO_APPROVED_VISUAL_TARGET / IMPLEMENTATION_PENDING / PRODUCTION_DEPLOY_SUSPENDED`.

## PRC-REF-020-UX-01 — Wireframe de diagnóstico de divergências (PO 2026-11-09)

**IMPLEMENTADO_DEV.** Área \`Verificação TOTVS\` orienta o próximo passo sem reduzir a força do bloqueio backend. Exemplo ilustrativo de uma tentativa com N verificações tipadas (contagens **sempre calculadas de dados reais**):

\`\`\`text
Verificação TOTVS
[!] Não foi possível concluir o atendimento
    5 problemas em 9 verificações · 4 conformes
    Continua EM ATENDIMENTO; nenhuma revisão foi publicada.
    Fonte oficial: api-delpi/TOTVS · Código: ... · Verificado em: ...

[Somente problemas (5)] [Todos os campos (9)]

Descrição             Solicitado: ...   TOTVS: ...   Divergente
  A ficha possui descrição diferente da oficial.
  [Revisar campo]

Grupo                 Solicitado: 1001  TOTVS: 1008  Divergente
  Classificação não coincide; verificar valor correto.
  [Revisar campo]

Unidade               Solicitado: UN    TOTVS: PC    Divergente
  Unidade diferente; não presumir equivalência.
  [Revisar campo]

Referência cliente    Solicitado: ...   TOTVS: [vazio verificado ou não verificável]
  Distinguir fonte vazia de atributo não retornado.
  [Revisar campo]

Fornecedor CÓD/LOJA   PN esperado ... / oficial ...  Divergente
  [Detalhar vínculo/atributo]

Corrigir ficha quando legitimamente necessário; solicitar informações quando
a decisão técnica depender do requester; correção ERP é manual e autorizada.
[Concluir atendimento novamente] (nova leitura oficial, sem forçar MATCH)
[Histórico de tentativas]
\`\`\`

Um só banner/resumo detalhado por tentativa, sem duas mensagens vermelhas idênticas; fora da aba, aviso compacto/navegação. \`Observação\` informa diferença/limitação, não fica vazia para problemas. Textos longos expansíveis; fornecedor discriminado por código + loja + atributo PN/Catálogo; filtro visual sem perder histórico. Ação \`Revisar campo\` muda para \`Ficha técnica\`, rola/foca/destaca alvo sem alterar dado; quando impossível, fallback honesto. Usar padrões oficiais \`@delpi/plugin-ui\`, teclado/zoom200/mobile e screenshots reais DEV. Comparação é somente da Engineering API, nunca do frontend.

## PRC-REF-021 — Wireframe simplificado: uma tabela para diagnosticar e decidir (PO 2026-11-09)

**\`IMPLEMENTED_DEV\`.** O PO rejeitou a engenharia visual repetitiva (banners grandes, resumo extenso, cartões e blocos duplicados). **Uma tabela resolve** — entregue em \`PrcVerificationPanel\` (cabeçalho compacto + tabela única SB1/SA5 + Encaminhamento + histórico recolhível).

\`\`\`text
Verificação TOTVS · Produto 10080022 · 09/11/2026 15:51
Conclusão bloqueada — 4 divergências · Em atendimento
[Problemas (4)] [Todos (11)]

Campo                  Solicitado        TOTVS               Situação      Encaminhamento
Unidade                UN                PC                  Divergente    [Definir]
Grupo                  1001              1008                Divergente    [Definir]
Descrição              REF019-FIX02 6    TERM. OLHAL...      Divergente    [Definir]
Referência cliente     REF...            Vazio verificado    Divergente    [Definir]
Fornecedor 000123/01
  Part Number           PN-2026           PN-2025             Divergente    [Definir]
...
[Histórico de tentativas ▾]
\`\`\`

**Sem** duplicar mensagem de erro acima da aba e dentro de painel; sem segunda tabela para fornecedores; **sem coluna de observação longa** que imponha scroll horizontal. O motivo e a orientação aparecem na expansão da própria linha, acionados por usuário e por teclado. Valores extensos quebram/expandem. Os números reais vêm da mesma tentativa, sem contagem duplicada SA5. Ação \`Definir\` abre interação simples com \`Solicitar correção ao solicitante\` / \`Ajuste manual TOTVS\` / \`Pedir esclarecimento\`; apenas a Engenharia autorizada escolhe, sem mudar MATCH automaticamente. O solicitante só edita ficha por contrato de correção estruturada aprovado; ERP só muda manualmente por operador autorizado. Após correção, \`Concluir atendimento\` repete leitura oficial, permanecendo bloqueado se houver qualquer erro. Filtro/ação, focus, feedback e a11y via \`@delpi/plugin-ui\`, sem visualização em cartões concorrentes.

## PRC-REF-021-REF-01 — Layout e operação simplificados (PO 2026-11-09)

**\`IMPLEMENTED_DEV\`; este adendo substitui o wireframe REF-021 com coluna \`Encaminhamento\` e botão \`Definir\`.**

\`\`\`text
FILA — HERO
Solicitações de produtos                    [Nova solicitação]
[Buscar] [Status] [Tipo]    [Flag Campos sinalizados (N)]
(sem faixa larga de bandeiras abaixo do hero)

VERIFICAÇÃO TOTVS — UMA TABELA
Produto 10080022 · 09/11/2026 15:51 · 4 divergências · Em atendimento
[Problemas (4)] [Todos (11)]
Campo                 Solicitado     TOTVS          Situação      Ação
Unidade               UN             PC             Divergente    [Revisar]
Grupo                 1001           1008           Divergente    [Revisar]
Fornecedor 000123/01 · PN-2026      PN-2025        Divergente    [Revisar]
[Histórico ▾]

Sem modal Definir encaminhamento. Engenharia usa o botão normal
Solicitar informações para devolver/confirmar dados, ou operador autorizado
ajusta manualmente TOTVS. Reexecuta Concluir atendimento após correção.

SOLICITAR INFORMAÇÕES — SUPPLIER_LINK
[Tipo de alvo: Vínculo de fornecedor]
[Pesquisar fornecedor: código, razão social ou fantasia...]
[Seleção oficial: 000123 / 01 — nome autorizado]
[Atributo: Part Number ou Catálogo]
[Pergunta: ...]
Sem digitação livre de código/loja; sem fallback quando lista local vazia.
\`\`\`

Kit \`@delpi/plugin-ui\` / façade \`engineeringUi\`; áreas responsivas/sem scroll horizontal, mouse/teclado/zoom200. O detalhe/CRUD de bandeiras permanece disponível sob demanda, sem segundo painel permanente. Busca de fornecedor depende exclusivamente de contrato oficial BFF/API e preserva identidade completa. Nenhuma mudança no backend de match ou escrita TOTVS.

## PRC-REF-022 — Páginas definitivas alvo: ficha compartilhada e devolução por campo (PO 2026-11-10)

**\`PO_APPROVED_TARGET / PLANNED\`.** Supersede a UX de \`Solicitar informações\` como correção principal e o formulário paralelo "Editar ficha técnica" exibindo "Novo valor — X" e "Justificativa" para cada campo. Foco em **uma única ficha** com modos \`create|read|edit\`, reutilizando schema, field specs e selects/lookup oficiais já existentes; não construir segundo formulário.

\`\`\`text
FILA / product-registration
Solicitações de produtos        [Nova solicitação] [Bandeiras (N)]
[Buscar] [Status: Enviada / Em atendimento / Devolvida para correção / Concluída / Rejeitada]
Uma tabela: Nº | Tipo | Solicitante | Código oficial | Abertura | Status | Responsável

DETALHE — SOLICITAÇÃO EM ATENDIMENTO (analista)
Solicitação #... [Em atendimento]
[Editar ficha] [Devolver para correção] [Concluir atendimento] [Rejeitar]
[Visão geral] [Ficha técnica] [Verificação TOTVS] [Histórico] [Revisões]
Ficha técnica com dados atuais; clicar Editar ativa os controles NA MESMA FICHA.

DEVOLVER PARA CORREÇÃO (analista)
Selecione os campos: [ ] Unidade  [ ] Descrição  [ ] Fornecedor 000123/01 PN
Por campo: orientação objetiva / motivo obrigatório
[Cancelar] [Devolver solicitação]
Sem perguntas/respostas independentes, sem "Definir encaminhamento".

SOLICITAÇÃO DEVOLVIDA (solicitante)
Solicitação #... [Devolvida para correção]
2 campos precisam de correção.
Ficha técnica compartilhada, em modo edit só para os alvos devolvidos:
Unidade [select com valor atual] (motivo: confirme PC vs UN)
Fornecedor 000123/01 · PN [controle oficial] (motivo: informe referência correta)
[Salvar alterações] [Reenviar para Engenharia]
Demais campos em read-only; sem editor em card separado e sem toggle de papel.

SOLICITAÇÃO DEVOLVIDA (Engenharia)
[Devolvida para correção] — aguardando solicitante.
Visualizar campos e histórico, sem edição simultânea.

RETORNO À ENGENHARIA
[Em atendimento] — Correções recebidas (eventos e diffs)
[Concluir atendimento] → Engineering API valida + lê TOTVS fresco.
Qualquer problema mantém Em atendimento; sucesso → Concluída.

TERMINAL
[Concluída/Rejeitada] — Ficha técnica somente leitura.
Bandeiras internas D16 seguem ações autorizadas.
\`\`\`

**Regras visuais:** modo edição reaproveita os componentes reais do cadastro, com valores preenchidos e validação/diff; fornecedores sempre por busca oficial e identidade code+store; help no label e bandeira contextual por campo; apenas campos devolvidos editáveis pelo requester. Justificativa só contextual e exigida quando houver alteração; nenhum formulário que repete campo/novo valor/justificativa para todos os atributos. Destacar alvos e motivos da devolução dentro da ficha; foco e scroll corretos. Nada de dashboards nem novas listas paralelas. Em desktop/tablet/mobile e zoom200, elementos sem horizontal overflow e botões acessíveis por teclado. Reutilizar estados do backend, jamais botão fake com autorização inexistente.

## PRC-REF-023 — Páginas alvo: documento opcional no formulário canônico, duas superfícies (2026-11-10)

**Status \`PO_APPROVED_FUNCTIONAL_TARGET / PLANNED\`.** UX enxuta, sem formularios duplicados.

\`\`\`text
PORTAL ENGENHARIA / NOVA SOLICITAÇÃO
[CREATE | UPDATE]   (mesmas seções e campos de hoje)
Identificação e classificação · atributos técnicos · fornecedores SA5
... Part Number obrigatório; Catálogo opcional ...
Documentos de apoio (opcional)
[Selecionar PDF ou imagem]   [Arquivos selecionados / remover]
[Nova solicitação / Enviar alteração]
(PDF ou imagem é apoio à análise, não campo obrigatório nem evidência TOTVS)

DETALHE DO PRC (usuário autorizado)
Ficha técnica | Verificação TOTVS | Histórico | Revisões
Documentos de apoio (se houver) [Nome | Autor | Data | Download seguro]

MINHAS SOLICITAÇÕES / NOVA CRIAÇÃO OU ALTERAÇÃO DE MATÉRIA-PRIMA
Mesmo formulário funcional da Engenharia: campos, selects oficiais,
busca fornecedor, PN obrigatório, Catálogo opcional, documentos opcionais.
[Enviar solicitação]
Após envio: caso PRC da Engineering API; acompanhamento/retorno autorizado
em Minhas Solicitações, sem criar cópia de workflow no requests-api.
\`\`\`

**Não é prioridade desenhar um novo wizard.** Primeiro sustentar anexo na API, depois adicionar o campo de upload discreto à ficha oficial, por último consumir a mesma semântica em Minhas Solicitações. \`StagedAttachmentsField\` no MFE My Requests serve como referência de staging/preview/removal, não como autorização para importar internals ou apontar upload PRC ao storage do requests-api. O suporte de upload deve distinguir arquivo local vs persistido, falha/retry e permissões no download. Se storage/permission/cutover não estiverem aprovados, manter UX sem controle falso de envio.

## PRC-REF-023-F02/F03/F04 — Mesma ficha e documentos nas duas superfícies (PO 2026-11-10)

**\`PO_APPROVED_TARGET / PLANNED\`.** Reutilizar controles canônicos; sem tela paralela de produto, novo wizard ou painel de anexos duplicado.

\`\`\`text
PORTAL ENGENHARIA · CREATE OU UPDATE
Ficha completa PRC · atributos oficiais · fornecedores SA2/SA5
Documentos de apoio (opcional)
[Dropzone] [miniaturas de imagem / ícone PDF] [remover antes do envio]
[Clique → FilePreviewModal / Baixar] [Enviar solicitação]
(falha parcial: retry só dos pendentes, caseId preservado)

PORTAL ENGENHARIA · DETALHE EM ATENDIMENTO
[Ficha técnica] [Verificação TOTVS] [Histórico]
Documentos de apoio: [miniaturas/ícones → modal PDF/imagem]
[Download autorizado]; sem criar outro painel concorrente
(solicitante consulta documentos permitidos; novos anexos em
 "Devolvida para correção" ainda pendem de decisão)

MINHAS SOLICITAÇÕES · NOVA SOLICITAÇÃO (MATÉRIA-PRIMA / PRODUTO)
[Tipo: Criar | Alterar] · MESMOS CAMPOS E CONTROLES PRC
[Descrição] [Grupo] [Tipo] [Unidade] [Estoque/Contabilidade]
[Fornecedor por pesquisa oficial] [PN*] [Catálogo opcional]
[Documentos opcionais: mesmo dropzone + preview + modal]
[Enviar] → um único caso oficial da Engineering API

MINHAS SOLICITAÇÕES · MINHA FILA/DETALHE
[Enviada] [Em atendimento] [Devolvida para correção] [Concluída]
Ver ficha/anexos/histórico permitidos
Devolvida: editar na própria ficha SOMENTE alvos indicados; [Reenviar]
Engenharia: atendimento/edição governados no Portal Engenharia
\`\`\`

Para cada tela validar desktop/tablet/mobile, zoom200, foco e teclado. Não expor ações não autorizadas; não copiar JSX de MFEs para criar uma segunda implementação. \`F02\` é consolidação e QA das superfícies documentais existentes; \`F03/F04\` exigem contratos Core/Coordination antes do cutover.


## PRC-REF-024 — Wireframe V3: detalhe PRC com hero orientado à decisão, conteúdo contextual e ações claras (PO 2026-11-14)

> **Estado: PO_DIRECTION_CAPTURED / UX_TARGET_FOR_REVIEW / IMPLEMENTATION_NOT_AUTHORIZED / VISUAL_E2E_NOT_RUN.** Este adendo refina a composição da página de detalhe, sem revogar PRC-REF-022 (ficha compartilhada e devolução por campo) nem as regras oficiais PRC-TRACK. Origem: captura real de HML do caso de alteração #1a808947 (em atendimento) e comentários do PO. Não é prova de mudança de backend.

### A. Diagnóstico auditado no código

- \`PrcDetailPage.tsx\` constrói \`identification\` com nove campos no \`EngineeringDetailFieldGrid\` dentro do hero: solicitante, responsável, código TOTVS, revisão base, abertura, última atualização, origem, referência externa e verificação oficial. Também exibe título/status/tipo/versão, \`PrcWorkflowProgress\`, ação primária e \`PrcActionBar\`. Embaixo vêm banners contextuais e abas \`Ficha técnica\`, \`Verificação TOTVS\`, \`Histórico\`, \`Revisões\`.
- Na captura, código oficial reaparece na Ficha técnica. Responsável ausente ocupa espaço com “Responsável não identificado”; origem exibe “Canal corporativo (My Requests)”; referência externa não explica utilidade; verificação resumida do tipo “Divergente em data” compete com aba dedicada.
- Há \`PrcPersonCell\` usado na fila (avatar + nome). Inventariar se seus contratos de \`requester\`/\`assignedTo\` são compatíveis com o detalhe antes de reutilizar.
- Corrigir **composição da apresentação**, não apagar proveniência/auditoria nem mascarar bloqueio de verificação.

### B. Princípios da página V3

1. **Hero = identidade + estado + próximo passo.** Não transformar o hero em ficha de metadados. Priorizar “o que é, em que etapa está, quem abriu e o que posso fazer agora?”.
2. **Informação em um lugar predominante:** código oficial na Ficha técnica; verificação e motivos na aba Verificação TOTVS; eventos/datas/origem/referência em Histórico/Informações da solicitação; revisão técnica em Revisões. Revisão base pode aparecer compacta no hero **se útil e comprovada**; não confundí-la com \`caseVersion\` (versão da solicitação).
3. **Progressão do workflow continua visível.** Usar \`PrcWorkflowProgress\` existente; eventos devolvida/rejeitada/aguardando informações não podem ser representados como conclusão normal.
4. **Ações legíveis:** botões com ícone+texto curto e tooltip explicativo, uma ação primária, secundárias e destrutiva diferenciadas; ícone sozinho não substitui rótulo nem \`allowedActions\`. Não inferir permissões por status.
5. **Dados técnicos oficiais e revisão não mudam de owner:** snapshot, TOTVS, diff, provenance, attachment, flags, CAS, confirmação e publicação permanecem governados.

### C. Matriz de redistribuição dos metadados

| Campo atual | Destino V3 | Regra |
|---|---|---|
| Número e status | Hero, título + badge | UUID preservado na URL; número curto legível |
| Tipo de solicitação | Subtítulo hero, “Alteração de matéria-prima”/“Criação de matéria-prima” | Sem redundância “versão X” ambígua |
| Solicitante | Hero, avatar + nome | Identidade autorizada; fallback neutro se dados ausentes |
| Responsável | Hero **somente quando atribuído** | Avatar + nome; não reservar bloco vazio para ausente |
| Código oficial TOTVS | Ficha técnica → Identificação do produto | Hero sem repetição; códigos de erro permanecem na aba técnica |
| Revisão base | Chip discreto no hero ou seção “Informações da solicitação”, conforme viewport | Exibir R2 se real; não confundir com versão do caso |
| Abertura | Metadados compactos sob menu “Informações da solicitação” + evento inicial do Histórico | Data pt-BR; pode haver data contextual discreta se essencial |
| Última atualização | Informações da solicitação / Histórico | Não duplicar no hero |
| Origem | Informações da solicitação / Histórico: “Canal: Minhas Solicitações” | Nome comercial pt-BR; código fonte intacto no backend |
| Referência externa | Informações da solicitação (opção avançada) | Rotular “Identificador no canal de origem” com ajuda “Código usado para rastrear a solicitação no sistema de origem”; se não possuir utilidade/contrato confirmado, não dar destaque no hero |
| Verificação oficial | Aba “Verificação TOTVS” (status, data, diagnóstico, evidência) | Se mismatch bloquear conclusão, mostrar **alerta compacto acionável** perto das ações com link para aba; não ocultar falha relevante |

### D. Wireframe textual — desktop (proposta V3)

\`\`\`text
← Solicitações / #1a808947

┌ HERO — Solicitação #1a808947  [Em atendimento] ────────────────────────────────┐
│ Alteração de matéria-prima                 [Revisão base R2] [ⓘ Informações]   │
│ [Avatar HT] Hml Tester    [Avatar do responsável + nome, se houver]           │
│                                                                               │
│  ✓ Enviada ───── ● Em atendimento ───── ○ Concluída                           │
│  (devolução/correção/rejeição são estados contextuais, não progresso fictício)│
│                                                                               │
│  [✓ Concluir atendimento] [↩ Devolver para correção] [⋯ Mais ações]            │
│  [⚠ Verificação oficial divergente → Ver diagnóstico]  (só se bloqueador)    │
└───────────────────────────────────────────────────────────────────────────────┘

[ Ficha técnica ] [ Verificação TOTVS ] [ Histórico ] [ Revisões ]

Aba Ficha técnica:
  [Acompanhamento técnico: 1 aberta]   [Legenda]        (discreto, contextual)
  [Identificação do produto] Código oficial 30190123
  [Alterações solicitadas] Campos técnicos, antes/depois quando aplicável
  [Demais grupos da ficha] Atributos, estoque/contabilidade, fornecedores...
  [Documentos de apoio] Anexos permitidos, preview/download autorizados

Aba Verificação TOTVS:
  [Divergência oficial] data/hora, diagnóstico e campos divergentes
  [Abrir campo correspondente da ficha] [Reexecutar conclusão, se permitido]

Aba Histórico:
  [Interações e solicitações de informação] [Timeline/auditoria]
  [Informações da solicitação ▾]
    Abertura | Última atualização | Canal: Minhas Solicitações
    Identificador no canal de origem: EVA-PRC-E2E-UPD (ajuda semântica)

Aba Revisões:
  [Revisão técnica oficial / snapshots e provenance, somente se existentes]
\`\`\`

**Nota de interação:** \`Informações\` no hero abre popover/drawer/resumo acessível de metadados de auditoria, sem esconder sua rastreabilidade no Histórico. Preferir um único conteúdo reutilizado ou acesso consistente em vez de duplicar painéis de nove campos. Se remover o menu \`Informações\`, manter todos os dados necessários claramente acessíveis no Histórico.

### E. Variante compacta para tablet/mobile e zoom 200%

\`\`\`text
← Solicitações
Solicitação #1a808947  [Em atendimento]
Alteração de matéria-prima · R2 (se couber)
[HT] Hml Tester           [ⓘ Informações]
✓ Enviada → ● Em atendimento → ○ Concluída (sem truncar)
[✓ Concluir atendimento]  [⋯ Ações]  (wrap, rótulos acessíveis)
[⚠ Ver diagnóstico] (somente se bloqueador)

[Ficha] [Verificação] [Histórico] [Revisões] (tablist acessível)
[Conteúdo da aba em uma coluna]
\`\`\`

Não criar toolbar sticky sem provar ausência de sobreposição do Portal/topbar e sem testes mobile. Ações destrutivas não podem ser acionadas acidentalmente.

### F. Estados a cobrir antes de implementar

- \`submitted\`: “Iniciar atendimento” se permitido; solicitante vê acompanhamento, sem controle de analista.
- \`in_progress\`: ação principal contextual, devolver/rejeitar conforme \`allowedActions\`; diagnóstico oficial bloqueador visível.
- \`needs_correction\`: solicitante vê alvos devolvidos na mesma ficha, correção e reenvio permitidos; Engenharia vê estado de espera e histórico sem edição concorrente.
- \`needs_information\`/\`under_review\` legados: mensagem fiel e ação permitida; nunca fingir que são etapa normal do tracker.
- \`completed\`/\`rejected\`: hero compacto somente leitura, estado terminal evidente, histórico e verificações consultáveis, sem CTA mutável.
- \`assignedTo = null\`: ocultar o slot de responsável no hero; manter fato de não atribuição acessível em Informações da solicitação se relevante ao atendimento.
- \`verificationSummary = null\`: sem alerta de erro; aba mostra “Ainda não verificada” conforme contrato.
- \`verificationSummary.result = mismatch\`: alerta compacto com link à aba; não simular sucesso.
- Erros/403/falhas parciais: alertas existentes governados continuam, sem ocultar bloqueio de backend.

### G. Componentes/contratos e pontos de inventário

\`PrcDetailPage.tsx\`, \`PrcWorkflowProgress.tsx\`, \`PrcActionBar.tsx\`, \`PrcPersonCell.tsx\`, \`PrcTechnicalSheet\`, \`PrcInformationExchangePanel\`, \`PrcVerificationPanel\`, \`PrcTimelineSection\`, \`PrcRevisionsSection\`, \`PrcFlagsOpsPanel\`, \`engineeringUi.ts\`, \`prc.css\`. Inspecionar componentes do \`plugin-ui\` para avatar, tooltip, menus e ícones; não copiar internals do Helpdesk ou outro MFE. Botões de conclusão/devolução/rejeição preservam confirmação, motivos, CAS e \`allowedActions\`. Reavaliar \`PrcVerificationPanel.onRetryComplete\`, que atualmente procura \`.engineering-prc__hero-actions\` por querySelector: após refatoração usar alvo estável/contrato legítimo sem seletor quebradiço.

### H. Gates e critérios de aceite da futura implementação

1. Somente informações prioritárias no hero, sem duplicação do código oficial.
2. Avatar solicitante, responsável condicional; nomes não devem virar UUID bruto.
3. Tracker visível, responsivo e sem falsa progressão.
4. Ícone + texto + tooltip nas ações, com hierarquia e confirm dialogs, sem novas ações/back-end.
5. Verificação oficial e referência externa rastreáveis em seus contextos; mismatch permanece acionável.
6. Abas e conteúdo técnico existentes preservados; flags contextuais sem faixa onerosa.
7. Keyboard, screen reader, 200% zoom, desktop/tablet/mobile, temas claro/escuro, status e permissões.
8. Regresso de intake My Requests, detalhe PRC, TOTVS verification, correction workflow, anexos, revisões e navegação.
9. Testes completos no SHA e E2E visual em HML antes de aceite PO; sem execução de writes de teste em PRD.
10. **Nenhuma implementação ou deploy autorizados por este adendo.** Decidir refinamentos visuais com PO antes de emitir pacote Devin; quando autorizado, trabalhar \`main\`, sem novas branches.


### I. Ratificação do Product Owner — V3 aprovada para execução (14/11/2026)

**Estado atualizado:** `PO_APPROVED_UX_V3 / IMPLEMENTATION_AUTHORIZED_IN_HML / PRD_RELEASE_NOT_AUTHORIZED`.

O Product Owner aprovou expressamente o wireframe V3 e formalizou como princípio futuro do Portal Engenharia o **design limpo, direcional, contextual e sem informação redundante**; diretriz transversal registrada em `WIREFRAMES.md` §17.

**Escopo de execução ratificado:** remodelar o detalhe PRC inteiro, usando o wireframe V3 das seções A–H e sem alteração funcional do workflow: hero com identidade/status/solicitante avatar/responsável somente quando presente/tracker/ações, ícones+rótulos+ajuda; mover metadados redundantes para contextos próprios; tornar origem “Minhas Solicitações”; referência externa interpretável e acessível; diagnóstico oficial na aba com alerta compacto se bloquear conclusão; preservar ficha, documentos, sinalizadores, histórico/interações, revisões, estados e avisos. Somente o texto de apresentação muda, não o contrato de origem. Os botões devem ser dirigidos por `allowedActions` e os mesmos mecanismos de CAS, idempotência, confirmação e motivos.

**Gate:** Devin pode implementar na branch `main`, sem criar branch, testar e publicar **somente em HML** para aceite visual final. Não iniciar conclusão técnica de produto com TOTVS, publicação de revisão, mudança de fonte de verdade ou release PRD neste pacote. Se mudança de owner/contrato cross-BC for efetivamente necessária: `ARCHITECTURE_DECISION_REQUIRED`.

**Ressalva histórica:** na descrição anterior do wireframe consta “implementação não autorizada” porque foi escrita no momento da proposta; **esta seção I posterior prevalece para V3**, sem reclassificar testes ou capacidades como PASS antes da execução.


## PRC-REF-025 — Separação solicitação vs produto e proveniência de revisão (PO, 14/11/2026)

**Status:** `PO_APPROVED_FUNCTIONAL_PRINCIPLE / UX_CORRECTION_TARGET / IMPLEMENTATION_PENDING / HML_NOT_RUN`. Supersede apenas a exposição ostensiva de `Revisão base Rn` no hero prevista no PRC-REF-024, não os fluxos REF-022, as regras R01–R18 ou proteções de concorrência existentes.

**Decisão:** solicitação PRC é um caso de trabalho com `requestId`, status, histórico e versão técnica de concorrência (`caseVersion`); não tem “revisão de produto” própria. Em UPDATE, aponta ao **produto-alvo/código oficial** desde o intake, e pode capturar uma referência técnica da revisão vigente para `stale_revision`, mas não se apresenta como revisão publicada ou como produtora de uma revisão. Em CREATE, o produto oficial pode nem existir; não mostrar código ou revisão inventados. Somente ao concluir após validação oficial e regras de publicação pode nascer provenance `produto/revisão publicada → solicitação de origem`. No-op após existência de Vn conclui sem Vn+1; primeira conclusão validada de produto sem histórico versionado cria V1 baseline, conforme R01.

**Wireframe corrigido do hero V3:**

```text
Solicitação #1a808947 [Em atendimento]
Alteração de matéria-prima
[avatar] Solicitante      [avatar] Responsável (apenas se atribuído)   [ⓘ Informações]
✓ Enviada ─── ● Em atendimento ─── ○ Concluída
[Concluir atendimento] [Devolver para correção] [Rejeitar]
[Verificação divergente → Ver diagnóstico] (somente se efetivo)
```

**Não há chip `Revisão base R2` no hero.** Em `Informações`, manter `caseVersion` somente como “Versão interna do atendimento” se necessário à auditoria, nunca como revisão do produto. Se `baseRevision` for relevante para rebase/conflito, exibir apenas contexto técnico de “Revisão técnica de referência do produto (no início da análise)”, com ajuda de que **não é revisão gerada por esta solicitação**, e apenas em superfície avançada adequada; evitar mostrar quando não houver registro versionado. Melhor priorizar tal dado na ficha/diagnóstico técnico a partir de contrato verificado.

**Após conclusão:** na área `Produtos acompanhados → Versões`, a ficha da revisão efetivamente publicada mostra fonte de verificação, data e `Solicitação de origem #...` com deep-link autorizado; na solicitação concluída, se realmente houve revisão, pode mostrar `Revisão técnica publicada Vn` com deep-link autorizado. Em no-op, mostrar `Concluída sem nova revisão técnica` quando esse resultado for comprovado; não atribuir à solicitação autoria de uma Vn pré-existente. Não permitir link de revisão futura em caso pendente/rejeitado.

**Gates:** esta é diretriz de produto e apresentação aprovada. Alterar persistência de `baseRevision`, semântica de `record/revision.request_id`, protocolo ou emissão de revisions requer inventário de consumidores, contrato e autorização arquitetural da Coordination/owner competente (`ARCHITECTURE_DECISION_REQUIRED`). Não alterar fluxo oficial TOTVS, CAS, idempotência ou RBAC para acomodar UI. Implementar UX isolada somente depois de confirmar estado atual do frontend e de contratos, com testes DEV/HML, nunca PRD.
