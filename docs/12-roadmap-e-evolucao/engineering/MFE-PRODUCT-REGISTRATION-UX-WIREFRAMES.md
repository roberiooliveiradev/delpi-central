# MFE Portal Engenharia — Controle e Cadastro de Produtos: UX, wireframes e fluxo visual

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
