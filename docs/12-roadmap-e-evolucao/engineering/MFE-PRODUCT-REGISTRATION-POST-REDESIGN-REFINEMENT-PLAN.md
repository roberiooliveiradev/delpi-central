# Portal Engenharia MFE — Plano incremental de refinamentos pós-redesign

> **Decisão funcional superveniente PRC-REF-022 (2026-11-10):** fluxo único Enviada → Em atendimento ⇄ Devolvida para correção → Concluída, editor compartilhado create/read/edit. O adendo REF-022 ao final deste documento prevalece sobre fluxos legados contraditórios. `IMPLEMENTED_DEV` (AuthZ solicitante sem `engineering.access` = `PENDING_OWNER`).

> **Status:** `PO_REFINEMENT_APPROVED / IMPLEMENTATION_PENDING / OPEN_FOR_MORE_FEEDBACK` · **Registrado:** 2026-11-07.
>
> **Origem:** inspeção visual DEV/localhost fornecida pelo Product Owner após o redesign PRC e análise de código atual. **Deploy de produção continua SUSPENSO** até aceite visual e gates funcionais.
>
> **Documentos-base:** [wireframes](./MFE-PRODUCT-REGISTRATION-UX-WIREFRAMES.md), [plano Devin UX0–UX5](./MFE-PRODUCT-REGISTRATION-DEVIN-IMPLEMENTATION-PLAN.md), [matriz plugin-ui](./MFE-PRODUCT-REGISTRATION-COMPONENTS-AND-ACCEPTANCE.md), [contrato técnico PRC](./PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md).
>
> **Política:** esta lista é **incremental**. Não iniciar implementação de todos os itens nem encerrar o refinamento antes que o PO conclua suas observações. Cada nova decisão deve ganhar ID, evidência, contrato, UX/AC e status, sem perder precedência.

## 0. Estado visual observado

O PO reconhece melhoria substancial do frontend pós-refatoração. As capturas DEV mostram:

- Central de solicitações agora possui breadcrumb, hero, filtros, DataTableSection e badges.
- Detalhe utiliza hero, progress, cards e abas; ficha técnica, verificação, histórico e revisões têm composição dedicada.
- Nova solicitação possui wizard de identificação, ficha técnica e revisão; opção de criação ou alteração.
- **Problema confirmado:** em `Nova solicitação → Alterar produto existente`, o usuário deve preencher manualmente **Revisão-base**; ao informar apenas código oficial, vê erro `Informe a revisão-base vigente do produto (número ≥ 1)`.
- Este campo é detalhe interno do controle técnico de concorrência, não informação que deve ser exigida de usuário de negócio.

A evidência fornecida é **visual**; não supor que outros fluxos estejam aceitos ou que HML esteja concluída.

## PRC-REF-001 — Revisão-base sempre automática em alteração de produto

**Decisão PO (aprovada):** ao abrir solicitação de **alteração**, o usuário informa/seleciona o **produto** e descreve o que deseja modificar. O usuário **não precisa saber, localizar, digitar nem selecionar** a revisão-base. O sistema deve resolver de modo governado a **última revisão técnica vigente** e garantir que a solicitação seja baseada nela. Não se trata de escolher a última revisão do TOTVS nem inventar revisão `1`.

**UI TARGET:**

```text
Nova solicitação                                     Etapa 1 / 3
[ Nova matéria-prima ] [ Alterar produto existente ✓ ]

Produto a alterar *
[Código oficial TOTVS ou lookup pelo BFF ..................] [Localizar]
  → Se identificado: [Descrição oficial disponível] [Informações úteis]
  → Se não encontrado: mensagem clara / correção de código

A revisão técnica de referência será identificada automaticamente.
(NENHUM input, select, número ou campo obrigatório de revisão-base)

                                              [Cancelar] [Avançar]
```

**UX:** remover `Revisão-base` do formulário, do validation summary e do resumo final do wizard para o usuário operacional. Não trocar input por número fixo, campo oculto com valor adivinhado ou default `1`. Na ficha de solicitação concluída, a revisão-base pode permanecer nos dados de auditoria e histórico técnico quando legitimamente disponível, sem virar escolha do solicitante.

### 1. Código existente — inventário verificado

- `plugins/engineering/src/features/product-registration/pages/PrcCreatePage.tsx`: mantém `baseRevision` em `useState("")`, valida `parseInt(baseRevision,10) >= 1`, renderiza campo `Revisão-base` e serializa `baseRevision` no payload e no resumo do wizard.
- `plugins/engineering/src/features/product-registration/api/productRegistrationApi.ts`: `PrcIntakeBody.baseRevision?: number | null` e `fetchPrcRecord(recordId)` tipados; ainda não há comprovação de endpoint de lookup de revisão vigente **por código oficial** disponível ao MFE.
- `engineering-api/engineering_app/interface/http/routes/product_registration_routes.py`: `IntakeBody.baseRevision: int | None`, recebe `POST /v1/product-registration/intake/requests`; a rota repassa o atributo à aplicação.
- `engineering-api/engineering_app/application/use_cases/product_registration/service.py`: ao receber `update`, busca record técnico por código oficial via repositório, obtém `current_revision_number`; **se record existe e `baseRevision` não é informado ou difere, hoje retorna `PrcConcurrencyError("stale_revision")`**; busca snapshot da revisão corrente para composição. Sem record técnico, o branch atual admite outra situação; **não inventar revisão no MFE**.
- Portanto, esconder input na UI **não é suficiente**: se a Engenharia tem record corrente, o backend atual exigirá valor manual e rejeitará a tentativa. O contrato servidor precisa de mudança explícita pelo owner Engineering API ou introdução de lookup oficial que não tire autoridade do backend.

### 2. Contrato-alvo preferido (backend-first, sem exposição de revision internals no wizard)

**Preferir a menor mudança no caso de uso de intake do owner Engineering API**:

1. Para `requestType="update"` e `officialProductCode` autenticado e válido, buscar record técnico vigente de Engenharia pelo repositório próprio.
2. Se houver record, resolver `baseRevision = current_revision_number` **no backend**, obter snapshot correspondente e associar de maneira atômica/consistente a base e os deltas da solicitação. Usar mecanismo de versão/transaction/lock/retry canônico para evitar TOCTOU.
3. O contrato público de intake não deve exigir que o humano forneça `baseRevision`. **Se for aceito opcional para compatibilidade de consumidores existentes**, não permitir fixar revisão arbitrária antiga; conflito ou divergência deve retornar resposta de contrato explícita (e manter clients históricos compatíveis onde possível). A decisão do servidor sobre a revisão corrente permanece mandatória.
4. Se **não existir record técnico publicado na Engenharia**, inventariar regra de negócio já vigente: o sistema pode ou não admitir solicitação de alteração para produto oficial ainda sem snapshot técnico. Não gerar revisão fictícia nem declarar revisão do TOTVS como revisão Engenharia. Documentar estado `NO_TECHNICAL_BASE`/regra canônica e ação correta sem inventar novo erro se já existir um código apropriado. Escalar questão de owner se exigir decisão funcional nova.
5. No momento de salvar, aplicar CAS/idempotência e, quando relevante, garantir que a base ainda seja a corrente; uma revisão avançada concorrente produz `409 stale_revision` e exige atualização da solicitação, jamais rebase silencioso de alterações já aprovadas.
6. Não alterar revisões históricas publicadas, `technical_snapshot`, audit trail e provenance. O source of truth de revisão técnica permanece no repository/Domain API de Engenharia; TOTVS continua SoT do produto **oficial**.
7. Não requisitar revisão-base ao frontend; o MFE encaminha somente os dados de negócio e deltas selecionados. Caso o backend precise de token opaco de concorrência produzido por endpoint read, isso deve ser retornado e validado via contrato apropriado, **nunca digitado pelo usuário**, e não autoriza bypass de verificação live.

**Justificativa arquitetural:** a decisão modifica parte do contrato/caso de uso de intake sob owner Engineering API; **não é somente CSS/UI**. Mudança deve ser testada em REST, domínio, PostgreSQL (quando disponível) e paridade EVA/consumers; aplicar contract-first e manter compatibilidade. Não criar novo bounded context, query TOTVS direta nem dependência de internals.

### 3. Arquivos-alvo e componentes

| Local | Trabalho necessário |
|---|---|
| `PrcCreatePage.tsx` | Remover state, render, validação e resumo manual `baseRevision`; usar texto neutro de base automática; UX loading/erro ao identificar produto se lookup oficial já existir |
| `productRegistrationApi.ts` | Atualizar tipo `PrcIntakeBody` e serialização do fluxo update sem revisão humana; respeitar contract server final |
| `engineering-api/.../product_registration/service.py` | Resolver revisão corrente no backend, CAS/idempotência/estado sem record e conflito de versão |
| `engineering-api/.../product_registration_routes.py` | Atualizar contrato doc/schema, se necessário, mantendo compatibilidade |
| Testes `productRegistration.test.ts` e casos frontend novos | Assert não exibir campo, não exigir revision, envio update sem número, 409 explicável e tratamento sem record |
| `engineering-api/tests/test_product_registration.py` / paridade EVA | Asserts da revisão corrente, concorrência e clientes existentes |
| Documentação PRC e manual `HelpPage.tsx` | Atualizar orientação para `revisão controlada pelo sistema`, não pedir ao solicitante que informe versão |

**Kit-first:** usar `EngineeringPageHero`, `EngineeringSectionCard`, `EngineeringFieldLabel`, `EngineeringActionButton`, `EngineeringStateBanner`, campos oficiais de `engineeringUi.ts`; não criar componente novo só para esconder revisão.

### 4. Critérios de aceite PRC-REF-001

- [ ] Ao escolher **Alterar produto existente**, não existe campo `Revisão-base` nem validação de número ≥1 nas três etapas do wizard.
- [ ] Usuário com `engineering.access` consegue iniciar alteração informando produto oficial e deltas legítimos, sem conhecer revisão técnica.
- [ ] A Engineering API resolve a **última revisão técnica corrente** da Engenharia quando existente e a associa corretamente ao caso.
- [ ] O sistema não confunde revisão técnica Engenharia com cadastro/revisão TOTVS.
- [ ] Se a revisão corrente mudar durante o intake, 409/CAS com recuperação segura; nenhum rebase ou publicação implícita.
- [ ] Se não houver record técnico, a política existente é inventariada e testada; nada de default `1`.
- [ ] Atualização seletiva preservada, com motivos, PN opcional, supplier code+store e verificação oficial posterior.
- [ ] REST, EVA, testes e usuários legados não sofrem regressão de contrato; IDs de revisão e audit trail permanecem governados.
- [ ] Typecheck/build/Vitest e testes Python/PG pertinentes; browser real para demonstrar não existência do input nas três etapas.
- [ ] Erro de backend em mudança concorrente se traduz em orientação funcional ao usuário (não exibir exceção interna).

**Status:** `PO_APPROVED / TO_IMPLEMENT`; não declarar corrigido apenas por este documento.

## PRC-REF-002 e seguintes — espaço reservado a próximas observações do PO

**Status:** `AWAITING_USER_FEEDBACK`. Anexar cada novo refinamento com: `ID / imagem e sintoma / decisão PO / análise do contrato / UX antes-depois / componentes do kit / arquivos / AC / owner / status`. Não inventar desejos ou antecipar a lista.

## Sequenciamento

1. Coletar demais apontamentos do Product Owner no mesmo plano sem perder o item PRC-REF-001.
2. Revisar owner/contrato e dependencies entre refinamentos; aprovar qualquer alteração de authority em Coordination.
3. Gerar implementação Devin em lote coerente depois de fechar feedback, mantendo deploy produtivo suspenso.
4. QA real DEV/HML por screenshots e tarefas executadas; aceite do PO em separado.

**Status de projeto:** `VISUAL_REFINEMENT_IN_PROGRESS / PRC-REF-001_APPROVED / PRODUCTION_DEPLOY_SUSPENDED`.


## PRC-REF-002 — Ícone do acesso na home

**Decisão PO (2026-11-08; aprovado, a implementar):** o acesso **Controle e Cadastro de Produtos** na área **Trabalho** da home de Engenharia deve possuir ícone consistente com as demais entradas (Minhas solicitações, LMPs, Não conformidades, Produtos). A captura DEV mostra esse item sem ícone, gerando inconsistência visual.

**Fonte identificada:** `plugins/engineering/src/content/engineeringRouteCatalog.ts` contém `id: "product-registration"` com label, description, target internal, permission `engineering.access` e keywords; identificar como o ícone é definido no catálogo/resolver/componente compartilhado antes de modificar. Não concluir de antemão que existe campo `icon` no catálogo — verificar contrato real e mapping para os demais acessos.

**Visual alvo:**
```text
TRABALHO
  [ícone] Minhas solicitações
  [ícone] LMPs
  [ícone] Não conformidades
  [ícone] Controle e Cadastro de Produtos  ← adicionar ícone coerente
  [ícone] Produtos
```

**AC:** ícone distinto e semanticamente adequado (cadastro/clipboard de produto, conforme iconografia real do kit), mesmo alinhamento, tamanho, cor e estados de hover/foco dos itens vizinhos; sem SVG ad hoc, emojis, CSS paralelo ou alteração do acesso `Produtos`. Respeitar tema, teclado e busca/favoritos. **Status:** `PO_APPROVED / TO_IMPLEMENT`.

## PRC-REF-003 — Linha inteira da fila abre o detalhe; remover “Abrir”

**Decisão PO (aprovada):** retirar coluna/link/botão **Abrir** da tabela; **clique em qualquer área não interativa da linha** deverá abrir a solicitação correspondente. Reutilizar `DataTableSection` com prop `onRowClick` já comprovada em `plugins/engineering/src/features/lmps/components/DataTableSection.tsx`.

**Alvo:**
```text
┌ #3bace5e3 │ Criação │ Solicitante │ 80016622 │ Concluída │ Responsável ┐
│              linha inteira navegável; foco/Enter acessível              │
└──────────────────────────────────────────────────────────────────────────┘
```

**Comportamento:** cursor/hover/focus e feedback semântico de item clicável; Enter/Space quando padrão do DataTable permitir, respeitando HTML/ARIA acessível. Não colocar handlers concorrentes sobre checkbox, seletor de colunas, links, menu de contexto ou seleção de texto; click nesses controles não deve navegar. Ao abrir, preservar back/forward, filtros e paginação da fila. Não transformar `<tr>` em botão inválido nem criar overlay que capture foco. Usar `onRowClick` e capacidades oficiais antes de extensão.

**AC:** sem coluna `Abrir`; abrir detalhe por mouse e teclado; click em controles internos não navega; sem regressão mobile/cards/kanban; navegação de volta preserva contexto. **Status:** `PO_APPROVED / TO_IMPLEMENT`.

## PRC-REF-004 — Seletor de colunas e reordenação

**Decisão PO (aprovada):** permitir exibir/ocultar e reordenar colunas da visão Tabela, com preferência persistida por usuário/navegador conforme mecanismo oficial do kit.

**Referências PROVEN CODE:** `plugins/commercial/src/components/TableColumnSettings.tsx` (usa `TableColumnVisibilityMenu` e `DEFAULT_TABLE_COLUMN_VISIBILITY_LABELS` de `@delpi/plugin-ui/index`); `plugins/commercial/src/components/OpenOrdersTable.tsx`; `plugins/engineering/src/features/lmps/components/DataTableSection.tsx` já oferece `columnPreferencesKey`, `defaultColumnVisibility` e `onVisibleColumnKeysChange`, com `useTableColumnVisibility` e gestão de colunas.

**Abordagem preferida:** usar os recursos `columnPreferencesKey` e toolbar já existentes em `DataTableSection` na lista PRC antes de recriar `TableColumnSettings`. Chave de storage isolada, por exemplo `engineering:prc:requests:columns`, sem reutilizar preferências do Comercial. Verificar possibilidade de pin/locked de uma coluna identificadora (código/número) pelo próprio kit; caso não suporte, manter alternativa robusta e garantir ao menos uma coluna de identificação visível. Reset restaura configuração inicial.

**Colunas a configurar:** Nº da solicitação, tipo, solicitante, código oficial, abertura, status, responsável; outras somente se os campos já vierem do contrato PRC.

**AC:** menu `Colunas` acessível; ocultar/exibir, reordenar e restaurar; persiste após F5; nenhum dado fora de permission scope; tabela e exportação (se existente, não criar) coerentes. **Status:** `PO_APPROVED / TO_IMPLEMENT`.

## PRC-REF-005 — Ordenação por colunas e ordenação consistente nos três layouts

**Decisão PO (aprovada):** ordenar dados por colunas no modo tabela (clicar cabeçalhos), incluindo direção ascendente/descendente; oferecer ordenação apropriada também em Cards/Kanban segundo os campos legitimamente suportados.

**Referência PROVEN CODE:** `DataTableSection` de Engenharia já dispõe de `clientSort` e `serverSort`; `plugins/commercial/src/components/OpenOrdersTable.tsx` tem `sortKey`, `sortDirection`, `onSort`, `CommercialDataCardsSortBar`, e indicadores de ordenação.

**CONTRACT GAP identificado:** `GET /v1/product-registration/requests` atualmente aceita `status,type,assignee,source,search,dateFrom,dateTo,page,pageSize`, mas **não expõe `sortBy`/`sortDir`**. Com paginação no servidor, ordenar apenas as linhas carregadas **NÃO** é ordenação global correta. O Devin deve primeiro confirmar contrato e capabilities atuais e propor menor extensão governada pelo owner Engineering API com allowlist de sort keys, defaults determinísticos/tiebreaker e parâmetros versionados/compatíveis. Não adicionar query params ignorados pela API; não ordenar uma única página alegando ordem global. Se backend extension ainda não for autorizada pelo owner, marcar `CONTRACT_GAP / PENDING_OWNER`, não prometer sort global, podendo implementar uma affordance explicitamente limitada aos itens carregados somente com rótulo honesto e aceite específico. **Não bloquear refinamentos independentes.**

**Campos candidatos:** abertura, número, tipo, status, solicitante e código oficial se garantidos pelo contrato. Não ordenar por label resolvido client-side como se backend possuísse esse dado sem checagem. Preferência `sortBy/sortDir` preservada em URL/persistência com padrão estável.

**AC:** cabeçalhos clicáveis e indicadores de direção, ordenação global coerente com paginação e filtros; F5 mantém preferência; Cards/board seguem mesma ordem validada; novos registros e estados não quebram sort. **Status:** `PO_APPROVED / CONTRACT_EXTENSION_TO_VALIDATE / TO_IMPLEMENT`.

## PRC-REF-006 — Alternar Tabela / Cards / Kanban conforme Portal Comercial

**Decisão PO (aprovada):** adicionar seletor de apresentação à fila de solicitações com três modos:

```text
Solicitações de produtos                    [Tabela | Cards | Kanban] [Colunas] [Atualizar]
  Tabela: linhas + colunas configuráveis + sorting
  Cards: grid responsivo; card inteiro abre detalhe
  Kanban: colunas por estado do workflow; card inteiro abre detalhe;
          somente leitura, sem drag/drop ou transição automática de estado.
```

**Referências PROVEN CODE no MFE Comercial:**
- `plugins/commercial/src/components/OpenOrdersTable.tsx`: `usePersistedViewLayout` com `storageKey`, `SegmentToggle` de `table/cards/board`, `CommercialDataCardsGrid`, `CommercialDataCardsSortBar`, `TableColumnSettings` e `OpenOrdersKanbanBoardView`.
- `plugins/commercial/src/components/OpenOrdersKanbanBoard.tsx`: board via `CommercialKanbanBoard` + cards da façade `commercialUi.ts`.
- `plugins/commercial/src/app/commercialUi.ts`: factories reais `createDashboardDataCardsGrid`, `createDashboardDataCardsSortBar`, `createDashboardInteractiveDataCard`, `createDashboardKanbanBoard`; hook `usePersistedViewLayout`.
- `plugins/plugin-ui/src/components/data/KanbanBoard.tsx`: componente **read-only**, sem drag-and-drop; colunas com título, count opcional e card slots. Usar esse contrato para não permitir mudança de estado visual sem autorização.
- `plugins/engineering/src/ui/engineeringUi.ts`: verificar exports atuais para `EngineeringSegmentToggle` e criar façade enxuta para cards/kanban através das factories do kit se ainda não expostas, aplicando Abstraction Gate. **Não importar componentes específicos de negócio do Comercial** para Engenharia: referenciar a composição, reusar apenas a biblioteca compartilhada.

**Tabela:** `DataTableSection` e estados/filtros existentes; `onRowClick`; colunas e sort.

**Cards:** usar `createDashboardDataCardsGrid` + `createDashboardInteractiveDataCard` com título Nº e tipo, status `EngineeringStatusBadge`, código oficial, solicitante, abertura, responsável legível e navegação acessível; sem mostrar UUID como nome; grid fluido desktop/tablet/mobile.

**Kanban:** usar `createDashboardKanbanBoard` com colunas mapeadas aos estados reais: Enviada (`submitted`), Em atendimento (`in_progress`), Aguardando informações (`needs_information`), Em revisão (`under_review`), Concluída (`completed`) e Rejeitada (`rejected`), ou agrupamentos mais compactos com rótulos claros e sem perda de estado. Cards são links para detalhe, não draggable. Contagens somente se realmente abrangem todo o escopo autorizado.

**PAGINAÇÃO / COMPLETUDE — GATE IMPORTANTE:** a fila atual é paginada; um board feito com os 25 registros da primeira página **não representa o Kanban completo**, nem permite contagens verdadeiras. Antes de implementar board com escopo geral, negociar contrato mínimo BFF (agregados por estado/consulta de colunas paginadas ou view multi-status com cursores), com limites e AuthZ de dados; não baixar milhares de casos em loop para montar board e não afirmar contagens globais a partir do chunk local. Se não houver extensão de API aprovada, apresentar apenas itens da página explicitamente rotulados `Exibindo somente itens carregados` e preservar paginação/contexto; o modo Kanban global fica `PENDING_CONTRACT`. Manter status enum do backend e movimentação unicamente via workflow autorizado do detalhe.

**Preferência:** `usePersistedViewLayout({storageKey:"engineering:prc:requests:layout"})` (nome proposto, validar política); `view=table|cards|board` opcional em URL apenas seguindo padrão real de navegação (em Comercial há deep link state). Troca modo não deve perder filtro, página ou ordem; back/forward/F5 consistentes.

**AC:** alternância imediata e persistida, mesmas solicitações autorizadas e mesmas semânticas em todos layouts, sem fake counts, cards e board acessíveis, sem DnD, sem mudança de status no MFE, browser DEV screenshots desktop/tablet/mobile, testes de seleção/sort/filtros/paginação. **Status:** `PO_APPROVED / CONTRACT_DEPENDENCIES_TO_VALIDATE / TO_IMPLEMENT`.

## PRC-REF-007 e seguintes — próximas observações do PO

**Status:** `AWAITING_USER_FEEDBACK`. Continuar anexando observações, sem encerrar coleta e sem começar deploy. Avaliar com o PO se refatoração final será executada em lote após nova revisão visual.

## Integração ao plano e gates

- `REF-002` e `REF-003`: mudanças frontend pequenas, independentes.
- `REF-004`: utilizar imediatamente DataTableSection existente; não criar menu duplicado.
- `REF-005`: **ordenação global necessita contrato backend** se ainda não existente; owner Engineering API decide menor extensão, testar repository PostgreSQL e AuthZ/limit.
- `REF-006`: composição UI usa kit, mas **Kanban do escopo completo necessita plano de paginação/agregados**; apenas carregados pode ser alternativa honesta, não prometer falso global.
- Não alterar Core permissions, TOTVS, api-delpi nem autorizar DnD.
- Não alterar RQ-001: revisão-base automática continua como decisão aprovada pendente.
- Gates gerais: `UI_REFINEMENT_COLLECTING / PO_APPROVED / IMPLEMENTATION_PENDING / PRODUCTION_DEPLOY_SUSPENDED`.


## PRC-REF-007 — Consolidar identificação, andamento e ações no hero do detalhe

**Decisão PO (2026-11-08, aprovada para planejamento):** Na página de detalhe de solicitação, **todas as informações atualmente apresentadas entre o hero principal e a segunda barra de navegação (abas)** devem ser consolidadas em uma composição compacta **dentro do próprio hero**, para reduzir de forma significativa a altura acima do conteúdo da aba. Evidência: captura DEV em `/apps/engineering/product-registration/{requestId}` exibindo hero "Solicitação #...", progress tracker isolado, cards separados "Identificação" / "Próximas ações" e então tabs "Visão geral | Ficha técnica | Verificação TOTVS | Histórico | Revisões". O PO quer eliminar esta duplicação/verticalidade.

### Wireframe alvo desktop

```text
breadcrumb: ← Solicitações / #3bace5e3
┌ HERO / CONTROLE E CADASTRO DE PRODUTOS ──────────────────────────────────────────┐
│ SOLICITAÇÃO #3bace5e3  [Concluída]          [Ação primária contextual, se houver]│
│ Criação · Matéria-prima · v5                         [Mais ações, quando válidas]│
│                                                                               │
│ Solicitante: Rober Dev       Responsável: não identificado                     │
│ Código TOTVS: 80016622     Abertura: 06/11/2026 16:42                       │
│                                                                               │
│ [✓ Enviada] ── [✓ Atendimento] ── [✓ Revisão] ── [✓ Conclusão]                │
└───────────────────────────────────────────────────────────────────────────────┘
[Visão geral] [Ficha técnica] [Verificação TOTVS] [Histórico] [Revisões]
┌ Conteúdo da aba ───────────────────────────────────────────────────────────────┐
│ Dados específicos desta aba; sem replicar todos os metadados do hero          │
└───────────────────────────────────────────────────────────────────────────────┘
```

**O que vai para o hero:** tipo e produto; status semântico; versão da solicitação (somente leitura); solicitante; responsável (display honesto, sem UUID); código oficial TOTVS ou "Aguardando cadastro"; abertura; origem e revisão-base **somente se úteis ao contexto** como metadados secundários/expandíveis — não pedir revisão-base manual; sequência de workflow; ações legítimas, com motivo/confirm quando requeridas. Não incluir histórico completo, ficha técnica nem tabela de verificação no hero. O caso encerrado deve dizer em texto discreto que não há mais ações, **sem card alto separado "Próximas ações"**.

**Redundância a eliminar:** cards fixos "Identificação" e "Próximas ações" que repetem informações do hero, progress tracker em linha solta, repetição desnecessária do mesmo status em várias superfícies. A aba "Visão geral" deve trazer **informação complementar** ao hero (resumo da solicitação, finalidade, verificação oficial, próxima ação ou destaque real), não repetir todos os atributos e status já legíveis no cabeçalho.

**Componentes do kit (inventário/props no SHA antes de editar):**
- `EngineeringPageHero` como base visual única; verificar se admite slots, content/children, actions e conteúdo complementar; se não admitir, envolver o hero + metadados + progress em **um único contêiner visual** com `EngineeringSectionCard` e grid local, preservando tipografia/tokens oficiais, sem forçar children em componente incompatível e sem segundo design system.
- `EngineeringStatusBadge` para status.
- `EngineeringDetailFieldGrid` para metadados em apresentação compacta.
- `EngineeringProgressTracker`/componente já integrado ao MFE, reaproveitado numa faixa do hero.
- `EngineeringActionButton` e diálogo host-contained para ações permitidas por `allowedActions`, com CAS, motivo e confirmação terminal.
- `EngineeringUnderlineNav`/tabs oficial usado na refatoração; **posicionar logo abaixo do novo hero**.

**Layout responsivo:** desktop: título+badge+ação na mesma faixa, metadados em grid compacto e progresso horizontal; tablet: wrap de ações, 2–3 colunas nos metadados; mobile: titulo e badge em linha/quebra, metadados em coluna/duas, tracker compacto acessível e actions sem obstruir abas; reduzir altura sem esconder contexto obrigatório. Não transformar altura mínima em valor fixo que corte conteúdo.

**Comportamento/autoridade:** mesmo conteúdo de backend e mesmas ações permitidas; não inferir autorização por status visual; não remover dados importantes ou ocultar erros; `needs_information`/rejected não devem ser forçados em linha progressiva de sucesso. Revisão-base é governada pela decisão REF-001 e não é input de usuário. Os códigos de domínio/caso de uso e backend continuam intactos nesta refatoração visual.

### Critérios de aceite

- [ ] O espaço entre o fim do hero e a barra das cinco abas é eliminado ou reduzido ao espaçamento do design system; o tracker fica no hero.
- [ ] Solicitação, status, tipo, código oficial, solicitante, responsável e data ficam visíveis/legíveis no hero, sem cartões independentes redundantes.
- [ ] "Próximas ações" passa a uma área compacta de ações contextuais no hero; em caso concluído não gera card vazio.
- [ ] As abas começam imediatamente após o hero (respeitando margin/gap oficial), e permanecem acessíveis por teclado, deep link `?tab=` e refresh.
- [ ] Aba Visão geral não duplica metadados; apresenta dados de valor complementar.
- [ ] Caso enviado, em atendimento, aguardando informações, em revisão, concluído e rejeitado são legíveis; ações preservam `allowedActions`/CAS/confirm.
- [ ] Screenshots de antes/depois em DEV e browser desktop/tablet/mobile mostram redução real de altura e ausência de clipping/overlap.
- [ ] Componente kit-first, sem CSS global novo; typecheck/build/Vitest e testes de navegação no SHA final.

**Arquivos-alvo:** `plugins/engineering/src/features/product-registration/pages/PrcDetailPage.tsx`; `PrcWorkflowProgress.tsx`, `PrcActionBar.tsx` e `prc.css` conforme nomes reais; façade `engineeringUi.ts` somente se slot/adaptação necessária e com contrato verificado.

**Status:** `PO_APPROVED / TO_IMPLEMENT`; não implementado por esta documentação. **Produção continua suspensa.**

## PRC-REF-008 — Identidade visual de quem executou cada evento do Histórico

**Decisão PO (2026-11-08, aprovada, implementação pendente):** na aba **Histórico**, cada evento deve apresentar **avatar, nome e e-mail do ator que executou a ação**, além de título, detalhes, transição de estado e data/hora. Substituir o texto genérico "Ator registrado no Portal" quando a identidade real puder ser resolvida com permissão.

**Inventário de contrato (GitHub):** `PrcTimelineEvent` no cliente expõe `actor_subject`, mas **não** expõe `displayName`, e-mail ou avatar. `PrcTimelineSection.tsx` usa hoje `EngineeringTimeline` e gera `actorLabel(subject)`. `EngineeringInitialsAvatar = createInitialsAvatar(ENG_UI_PREFIX)` já existe em `engineeringUi.ts`. Portanto, **não inventar nome/e-mail a partir de UUID nem usar identidade do usuário logado como se fosse o ator de todos os eventos**. A API de Engenharia ou um contrato oficial autorizado de identidade precisará fornecer a apresentação do ator; o Core/Keycloak permanece owner de identidade. Para eventos históricos sem associação resolvível, apresentar fallback honesto.

**Wireframe:**
```text
● [avatar] Nome real do ator                                  06/11/2026 16:42
           email@dominio (somente com dado autorizado)
  Ficha técnica alterada
  Em atendimento → Em atendimento
  Campos/justificativa comprovados · Canal: portal
```

**Implementação/authority:** verificar primeiro contrato oficial existente de resolução `actor_subject -> displayName,email,avatar`; preferir payload enriquecido/DTO governado pela Engineering API para consumidor com `engineering.access`, com live AuthZ e políticas de minimização de dados. Não consultar base de identidade diretamente pelo MFE, não derivar e-mail, não registrar PII extra em ledger técnico apenas por decoração. URL de avatar externa somente se fonte autorizada e segura; avatar por iniciais com `EngineeringInitialsAvatar` se nome válido, fallback neutro se não. Reutilizar `EngineeringTimeline` e seus slots/props reais; se API não suporta, marcar `CONTRACT_GAP/PENDING_OWNER`, sem mascarar com dados fictícios.

**AC:** evento mostra avatar+nome+e-mail quando disponíveis/autorizados, fallback quando não; timestamp preservado, ação humanizada (inclusive `verify_and_complete`), transição, motivo e ordem do ledger; sem UUID cru como identidade principal; a11y/responsividade/testes de atores diferentes, indisponibilidade da fonte, anonimização/ausência, 403 e dados históricos.

**Status:** `PO_APPROVED / CONTRACT_DEPENDENCY / TO_IMPLEMENT`.

## PRC-REF-009 — Avatar e nome de Solicitante e Responsável na fila

**Decisão PO (2026-11-08, aprovada, implementação pendente):** nas colunas **Solicitante** e **Responsável** da tabela de solicitações mostrar uma composição humana com **avatar + nome** alinhados na mesma célula, seguindo o padrão do plugin-ui. A captura atual exibe texto puro `Rober Dev`, `PG Test`, `Responsável não identificado` e `analyst-pg`. O usuário quer identidade visual, não identificadores crus.

**Inventário real:** `PrcRequestSummary.requester` atualmente contém `subject` e `displayName?`; `assignedTo` é apenas `string | null` (subject, que pode ser login/ID). Na fila `PrcQueuePage.tsx` a coluna solicitante usa `prcRequesterLabel(row.requester)` e responsável usa `prcPersonLabel(row.assignedTo)`. A façade `engineeringUi.ts` já possui `EngineeringInitialsAvatar`, reutilizável sem nova dependência. **Não assumir que há e-mail/foto no payload da fila.**

**Wireframe da linha:**
```text
Nº          TIPO      SOLICITANTE               STATUS         RESPONSÁVEL
#3bace5e3   Criação   [RD] Rober Dev            Concluída      [avatar] Nome real
#978351f6   Criação   [PT] PG Test              Enviada        [neutro] Não atribuído
#...        Alteração [--] Não identificado    Em revisão     [neutro] Não identificado
```
(Avatar de exemplo por iniciais; usar foto somente com URL contratual autorizada.)

**Componentes:** `EngineeringInitialsAvatar` via façade `engineeringUi.ts`; opcionalmente bloco local mínimo `PrcActorCell` se compartilhado entre fila/histórico/revisões e com semântica real. Reutilizar `DataTableSection` para layout e `DataTableColumn.mobileLabel` quando aplicável. **Não copiar componentes de domínio do Comercial**; seguir padrão de identidade do plugin-ui/Portal.

**Regras de resolução:**
- Solicitante: usar `requester.displayName` quando existir e autorizado; quando não, resolver por contrato oficial autorizado ou mostrar fallback `Solicitante não identificado`, sem inventar nome.
- Responsável: `assignedTo == null` -> **Não atribuído**, avatar neutro; subject presente + dados de exibição resolvidos -> avatar e nome; subject presente sem display resolvível -> **Responsável não identificado**, avatar neutro. Não mostrar GUID cru como nome, nem assumir que o usuário logado é responsável.
- Evitar N chamadas individuais de identidade por linha (N+1); preferir retorno governado na lista ou batch autorizado, com escopo de acesso correto, caching seguro e fallback em indisponibilidade.
- E-mail no **Histórico (REF-008)** quando disponível e autorizado; na fila priorizar **avatar e nome**, sem exigir e-mail em todas as linhas.
- Célula de avatar/nome é conteúdo da **linha clicável** conforme REF-003; clique na linha abre detalhe, sem botão `Abrir`.

**AC:** solicitante e responsável apresentam avatar+nome quando houver identidade resolvida; ator sem nome tem fallback honesto; pessoa não atribuída distinguida de pessoa não identificada; loading e largura de coluna não quebram layout; não exibir UUID/login técnico; ordenação de responsável/solicitante apenas quando suportada de verdade pelo backend (REF-005); vista Cards/Kanban deve usar a mesma identidade resolvida; foco/teclado e responsividade; testes com identidade completa, somente displayName, somente subject e null.

**Status:** `PO_APPROVED / CONTRACT_DEPENDENCY_ASSIGNEE / TO_IMPLEMENT`.

## PRC-REF-010 — Ficha técnica compacta em colunas e fornecedores em tabela editável

**Decisão PO (2026-11-08; aprovada para planejamento):** na etapa **Nova solicitação → Ficha técnica**, reorganizar todos os campos em **grade responsiva com múltiplas colunas** que aproveite a largura disponível, evitando um input de largura total por campo, separadores redundantes e rolagem exagerada. A seção **Fornecedores** deve ser uma **tabela editável**: cada fornecedor ocupa **uma linha** e os atributos ficam em **colunas**, não uma sequência vertical de cinco inputs e um botão “Remover” largo.

**Evidência visual DEV:** capturas do formulário `/apps/engineering/product-registration/new` (passo 2) mostram “Descrição / Grupo / Tipo / Unidade” e “Armazém padrão / Conta contábil / Produto de terceiros / Referência do cliente” verticalizados, seguidos de “Fornecedores” com código, loja, nome, Part Number e catálogo em cinco linhas independentes. O mesmo padrão desperdiça espaço em telas desktop.

**Inventário de implementação verificado:** `plugins/engineering/src/features/product-registration/pages/PrcCreatePage.tsx` renderiza `FIELD_GROUPS.map` com `EngineeringSectionCard` e `className="engineering-prc__edit-list"`, contendo `renderSheetField`; fornecedores usam `suppliers.map` com `className="engineering-prc__supplier-row"` e `EngineeringTextField`, além de `EngineeringCheckboxControl` para UPDATE. `prc.css` já contém `engineering-prc__supplier-row` (CSS grid), mas a experiência vista no navegador ainda aparece verticalizada: **não presumir que definir grid basta; investigar wrappers, larguras, breakpoints, CSS específico e especificidade real no runtime**. Reutilizar o formulário do kit por meio de `engineeringUi.ts`. Para tabela de formulários inspecionar props do `DataTableSection` e componentes de tabela do `@delpi/plugin-ui`; se não suportarem células editáveis sem violar acessibilidade/estado, compor uma tabela semântica simples com os inputs oficiais do kit (sem nova biblioteca, sem segundo design system).

### Wireframe desktop — passo 2

```text
[Nova solicitação]     ✓ Identificação ── ● Ficha técnica ── ○ Revisar e enviar
┌ IDENTIFICAÇÃO E CLASSIFICAÇÃO ──────────────────────────────────────────────┐
│ Descrição [.............................................................] │
│ Grupo [..................]  Tipo [................]  Unidade [...........] │
└───────────────────────────────────────────────────────────────────────────┘
┌ ESTOQUE E CONTABILIDADE ───────────────────────────────────────────────────┐
│ Armazém padrão [........]  Conta contábil [..............]                │
│ Produto de terceiros [Sim/Não oficial]  Referência cliente [...........] │
└───────────────────────────────────────────────────────────────────────────┘
┌ FORNECEDORES ───────────────────────────────────── [+ Adicionar fornecedor]┐
│ Código       Loja       Nome do fornecedor      Part Number      Catálogo │
│ [........]   [....]     [...................]   [...........]    [......] │
│ [........]   [....]     [...................]   [...........]    [......] │
│                                                        [Remover] por linha │
│ Nenhum fornecedor: empty state explicativo quando aplicável               │
└───────────────────────────────────────────────────────────────────────────┘
                                             [Cancelar] [Voltar] [Avançar]
```

**Regras de distribuição dos campos:** descrição deve ocupar largura principal ou `grid-column: span 2/3` conforme tamanho; grupo/tipo/unidade em uma mesma linha quando houver largura; armazém e conta contábil lado a lado; produto de terceiros como seleção booleana com rótulo humano (sem texto cru `1` se kit/contrato permitir), referência do cliente ao lado. Distribuição baseada em intenção e comprimento esperado, evitando cinco colunas iguais para campos com tamanhos distintos. Não alterar tipos, limites e required do `reference-data`.

**Fornecedores como tabela editável:**
- Cabeçalho: **Código, Loja, Nome, Part Number (opcional), Catálogo (opcional), Ações**. Cada vínculo = uma linha; botão `Adicionar fornecedor` adiciona uma nova linha em branco e foca o primeiro campo; ação `Remover` pequena por linha, com rótulo acessível e sem deslocar as outras linhas.
- `supplierCode`, `store`, `supplierName` mantêm validação; PN vazio/omitido continua legítimo, nunca wildcard; não confundir PN com catálogo; identidade composta `supplierCode+store` e erros por linha/campo.
- Em UPDATE, preservar seleção explícita de `suppliers` e justificativa obrigatória do change-set. A tabela só é editável quando `allowedActions`/estado/seleção autorizarem; `suppliers[]` substituído por inteiro somente sob a regra do contrato vigente, sem apagar vínculos sem intenção. Tratamento de duplicatas e conflitos é do backend e refletido na UI.
- Inputs por célula com labels acessíveis (headers + `aria-label` incluindo linha e campo), erros próximos ao input ou linha e foco no primeiro inválido. Evitar tabela com altura dinâmica que perca foco ao adicionar/remover; usar keys estáveis por identidade local, não somente index se reordenação puder ocorrer.
- Se for necessário pesquisar fornecedores, **não criar lookup TOTVS direto pelo MFE**. Consumir somente Engineering API BFF quando contrato oficial existente; ausência de contrato = campo digitável, sem autocomplete fictício.

**Responsividade obrigatória:** desktop ≥ largura útil do kit: colunas proporcionais, sem inputs full-width isolados; tablet: grid de 2 colunas e fornecedores com scroll horizontal **somente no container da tabela**, mantendo cabeçalhos/campos acessíveis; mobile: form em coluna única e cada fornecedor apresentado em **card editável semanticamente equivalente** ou tabela com rolagem controlada, com todos os rótulos visíveis, ações acessíveis e sem overflow da página. Não usar breakpoints hardcoded em substituição aos tokens do kit.

**Componentes e superfícies:** `EngineeringSectionCard`, `EngineeringFieldLabel`, `EngineeringTextField` e demais campos `NativeFormFields` realmente exportados, `EngineeringActionButton`, `EngineeringCheckboxControl`, `EngineeringStateBanner`, `EngineeringFormActions` (confirmar nome/props na façade), layout CSS local e, se suportado, `DataTableSection` para fornecedores editáveis. Não forçar DataTableSection se sua tabela não aceitar edição controlada sem conflitos; preferir tabela semântica com componentes oficiais de formulário.

### Critérios de aceite

- [ ] Desktop: **Descrição** em linha ampla; **Grupo, Tipo e Unidade** alinhados em colunas; **Armazém e Conta contábil** alinhados; **Produto de terceiros e Referência** em colunas coerentes.
- [ ] Nenhum campo ocupa uma linha inteira por padrão salvo necessidade semântica/responsiva; altura do passo 2 significativamente menor do que a captura atual.
- [ ] Fornecedores são visualizados/editados em tabela com cabeçalhos e uma linha por vínculo; adicionar/remover linha funciona sem perda de valores ou foco.
- [ ] Erros de Código/Loja/Nome, duplicação, Part Number, catálogos e limites vinculados ao campo correto; foco e leitores de tela testados.
- [ ] PN vazio aceito com fonte vazia, PN preenchido comparado pelo backend; UPDATE mantém checkbox, motivo por campo/delta, CAS/idempotência sem alterar contrato.
- [ ] Desktop/tablet/mobile e zoom 200% sem overflow horizontal da página; scroll horizontal contido apenas na tabela quando necessário.
- [ ] Etapas 1/2/3 preservam valores e botão `Voltar/Avançar`; estados loading/erro preservados.
- [ ] Browser DEV real com screenshots de **formulário sem fornecedor, com um, com múltiplos e com erro**, antes/depois; teste typecheck/build/Vitest; sem alteração de backend apenas por estética.

**Arquivos-alvo:** `PrcCreatePage.tsx`, `prc.css` e componentes PRC de formulário caso haja necessidade comprovada. Estender a mesma composição à edição da ficha técnica quando fizer sentido, sem quebrar `PrcTechnicalSheet` ou contratos existentes.

**Status:** `PO_APPROVED / TO_IMPLEMENT`; este registro não implementa o visual. **Produção continua suspensa.**



## PRC-REF-011 — Catálogos oficiais TOTVS e busca assistida de fornecedores

**Decisão PO (2026-11-08, aprovada para planejamento; implementação pendente):** no wizard **Nova solicitação → Ficha técnica**, substituir os inputs livres de **Grupo, Tipo, Unidade, Armazém padrão, Conta contábil e Produto de terceiros** por **selects/comboboxes alimentados com opções oficiais do TOTVS**, exibindo `código — descrição` quando houver descrição oficial. Na tabela de **Fornecedores** (REF-010), permitir buscar fornecedor **pelo código ou nome**, selecionar o registro oficial (código + loja + nome) e então preencher **Part Number (opcional)** e **Catálogo (opcional)** associados ao vínculo. Nada de digitar manualmente códigos mestres quando a lookup estiver disponível.

**Objetivo da experiência:** dados técnicos consistentes com o ERP, menos erros de digitação, sem criar cadastros paralelos nem permitir o MFE consultar TOTVS ou Suprimentos diretamente.

### 1. Padrão REAL já existente em Suprimentos — evidência do GitHub

- `plugins/supplies/src/features/suppliers/SupplierFormFields.tsx`: campos com catálogo oficial, `SuppliesSelectField` pesquisável, `useCatalogSearch` com lista remota, seleção de opção com código/descrição e estados loading/empty/error.
- `plugins/supplies/src/features/suppliers/supplierCatalogs.ts`: cache de rótulos, `PRELOAD_CATALOG_LIMIT`, `REMOTE_CATALOG_LIMIT`, busca por `query`, parâmetros dependentes, `httpGet` por BFF (`/suppliers/catalogs/{kind}`).
- `supplies-api/app/interfaces/http/routes/suppliers_routes.py`: `GET /suppliers` consulta `api-delpi` e devolve resultado paginado; política `supplies.access` é **daquele bounded context, NÃO autoridade de Engenharia**.
- `api-delpi/app/interface/http/routes/supplies/suppliers_router.py`: `GET /supplies/suppliers` com `query`, paginação e mapeamento controlado; **acesso S2S atualmente restrito ao client `supplies-api` e scope `suppliers.read`**.
- `api-delpi/app/infrastructure/persistence/totvs/supplier_repositories/totvs_supplier_repository.py`: leitura SA2 `A2_COD`, `A2_LOJA`, `A2_NOME` (inclusive nome fantasia), busca por código/nome e paginação, com origem oficial/proteção.
- **Reuso correto:** reutilizar design pattern e contratos oficiais da `api-delpi` (após owner autorizar consumer Engenharia), **NÃO** importar components de negócio `plugins/supplies` em runtime, não chamar `supplies-api` pela Engenharia, não copiar SQL/ODBC para Engineering API e não copiar permissões `supplies.access`. Se necessário ampliar allowlist de consumer/scope, isso exige contrato e aprovação do owner `api-delpi`/Identidade/Core; não alterar unilateralmente o boundary.
- O contrato `engineering-api/.../domain/product_registration/catalog.py` possui tipos `code/text/enum/suppliers` e `enum_values` estáticos para parte dos campos. **Esses enums e a resposta atual `reference-data` não comprovam por si só listas oficiais dinâmicas para grupo, unidade, armazém, contas etc.** Inventariar origem/endpoint real de cada catálogo.

### 2. Wireframe alvo — campos oficiais por seção (desktop)

```text
┌ IDENTIFICAÇÃO E CLASSIFICAÇÃO ──────────────────────────────────────────────┐
│ Descrição [.............................................................] │
│ Grupo [🔎 Pesquisar grupo no TOTVS ▼]   Tipo [Tipo de produto ▼]          │
│ Unidade [🔎 Pesquisar unidade ▼]        ...                                │
└───────────────────────────────────────────────────────────────────────────┘
┌ ESTOQUE E CONTABILIDADE ───────────────────────────────────────────────────┐
│ Armazém padrão [🔎 Código ou descrição ▼]  Conta contábil [🔎 Pesquisar ▼]│
│ Produto de terceiros [Seleção de domínio ▼] Referência cliente [.........]│
└───────────────────────────────────────────────────────────────────────────┘

┌ FORNECEDORES ──────────────────────────────────── [+ Adicionar fornecedor]┐
│ FORNECEDOR (busca por código ou nome) │ LOJA │ PART NUMBER │ CATÁLOGO │  │
│ [🔎 Código / nome ...           ▼]    │ 01   │ [opcional]  │ [opcional]│ ×│
│  → 000089 / 01 — WEG EQUIPAMENTOS... (escolher registro exato)            │
│ [🔎 ...                         ▼]    │ ..   │ [opcional]  │ [opcional]│ ×│
└───────────────────────────────────────────────────────────────────────────┘
```

**Interação fornecedores:**
1. Clicar `+ Adicionar fornecedor` cria linha local vazia na tabela (REF-010).
2. Focar combobox/lookup `Fornecedor`; aceitar busca textual por **código** ou **nome** (e, se contrato oficial suportar, nome fantasia).
3. Buscar **assincronamente pelo BFF Engenharia** com debounce, cancelamento de requisições obsoletas e paginação/limite (não carregar todos os fornecedores do TOTVS em memória).
4. Mostrar `código / loja — razão social` em resultados; códigos como strings, preservar zeros à esquerda; tratar múltiplas lojas do mesmo fornecedor (seleção deve identificar exatamente `supplierCode+store`).
5. Ao escolher, preencher de forma **atômica** código, loja e nome oficiais, como campos read-only/ligados à seleção; permitir limpar/trocar fornecedor com confirmação se houver Part Number/catálogo digitado, sem troca silenciosa de vínculo.
6. **Part Number e Catálogo permanecem editáveis pelo usuário**; não preenchê-los artificialmente e não buscá-los na SA5 como valor obrigatório do cadastro do fornecedor. Se houver dado oficial já associado ao produto, somente mostrar preenchimento inicial quando o contrato e a intenção de alteração justificarem. Part Number vazio legítimo; preenchido deve ser comparado com `A5_CODPRF` pelo backend na conclusão.
7. Impedir seleção duplicada de `(supplierCode,store)` na mesma tabela, com erro junto à linha; no UPDATE manter seleção de `suppliers`, justificação e PATCH seletivo já definidos.
8. Consulta autorizada falhou/403/sem resultados: erro honesto, retry; nunca converter código parcial não validado em fornecedor selecionado sem conferência pela Engineering API.

### 3. Contratos a inventariar e implementar pelo owner

| Campo do wizard | Apresentação alvo | Origem/contrato | Gate |
|---|---|---|---|
| Grupo | Combo buscável `código — descrição` | Catálogo de grupos de produtos no TOTVS, via `api-delpi`; endpoint específico **TO_INVENTORY** | não presumir tabela/endpoints |
| Tipo | Select com rótulos reais e códigos da ficha | Enum oficial/domínio B1_TIPO, através do catálogo autorizado; validar se `enumValues` atual é suficiente ou se há catálogo oficial | owner define |
| Unidade | Combo `código — descrição` | Lista de unidades oficiais, via `api-delpi`; contrato **TO_INVENTORY** | codes/string |
| Armazém padrão | Combo de armazéns válidos | Catálogo de armazéns TOTVS, considerando unidade/filial quando aplicável | não misturar escopos |
| Conta contábil | Lookup pesquisável com `código — descrição` | Contas oficiais autorizadas para o contexto de produto, via `api-delpi`; contrato **TO_INVENTORY** | confidencialidade/escopo |
| Produto de terceiros | Select legível `Sim/Não` ou semântica oficial correspondente | Regra de domínio/enum oficial existente, não necessariamente tabela dinâmica; preservar `1/2` ou mapeamento comprovado | não inventar rótulos |
| Fornecedor | Combobox remoto `código/loja/nome` | SA2 real **PROVEN na api-delpi**, contrato atual S2S scoped Suprimentos — necessitar consumer Engineering | **CROSS_OWNER_CONTRACT** |

**Contrato Engineering API candidato (NÃO implementado por esta decisão):** endpoints read-only sob `/v1/product-registration/reference-data/... ` para catálogos tipados e `/v1/product-registration/suppliers/search?query=...&page=... ` apenas se o inventário provar necessidade e owner Engenharia aprovar. Antes: owner → fonte canônica → consumidor → DTO, query/response, AuthN/AuthZ, limites, sorting/paging, idempotência N/A, erros, observabilidade e testes. **Não anunciar paths exemplificativos como rotas existentes.** Preferir expansão mínima do reference-data atual quando adequada; não criar abstração genérica de catálogo sem consumer real.

**Segurança e limites:** `engineering.access` + live Core authorization no Engineering API, delegação com credencial S2S individual e bearer humano onde contratualmente exigido, `api-delpi` autoriza consumer e acessa TOTVS; nenhum atalho por MFE, SQL direto, serviço de Suprimentos ou MCP. Menor privilégio. Não exibir opções fora do acesso efetivo, nem transportar tokens/segredos para frontend.

**Estados UI obrigatórios:** seleção carregando, busca vazia ou curta, resultados, sem resultados, erro, 403, timeout, selected item mantido na etapa 3, busca abortada, dados de referência stale e seleção inválida; evitar opção livre que se faça passar por catálogo verificado. O browser deve usar `EngineeringSelectField`, `EngineeringFieldLabel`, `EngineeringStateBanner`, `EngineeringActionButton` e combobox/lookup real do `plugin-ui` (inventariar props); não importar `SuppliesSelectField` como componente de outro bounded context. Form grid e tabela fornecedores seguem REF-010.

### 4. Critérios de aceite

- [ ] Grupo, Tipo, Unidade, Armazém, Conta e Produto de terceiros têm seletores com opções e labels oficiais verificáveis; quando não houver catálogo TOTVS necessário, enum de domínio legítimo e aprovado. Nenhuma lista hardcoded por conveniência.
- [ ] Consultas de referência passam pelo BFF Engenharia e pela `api-delpi`, respeitando Core/SSO, limites e fonte canônica.
- [ ] Seleção guarda **código oficial** (string, zeros preservados), apresenta descrição oficial e mantém valor no resumo; entrada livre inválida não passa como código selecionado.
- [ ] Fornecedor pesquisável por código ou nome, lista código+loja+nome, seleciona vínculo real SA2 e popula os três campos; PN e Catálogo permanecem editáveis/independentes.
- [ ] Duplicata de fornecedor+loja bloqueada; alternar fornecedor não apaga PN/catálogo sem intenção.
- [ ] CREATE e UPDATE funcionam, com seleção explícita e motivo de alterações; REF-001 revisão-base automática não conflita; PN opcional e CAS mantidos.
- [ ] Testes do contrato api-delpi/Engineering API, fallbacks fail-closed, UI com loading/erro/seleção/múltiplas lojas, race conditions, debounce e cache; browser desktop/tablet/mobile DEV.
- [ ] Nenhuma escrita no TOTVS; nenhuma dependência runtime de Suprimentos; nenhum escopo/permissão emprestado de outro owner.
- [ ] Se algum catálogo não estiver exposto no contrato oficial, marcar `TO_INVENTORY / PENDING_OWNER` e implementar os campos independentes; **não inventar código/descrição nem afirmar que TOTVS foi consultado**.

**Implementação planejada:** adicionar read adapters/contratos pelo owner `api-delpi` quando faltarem; Engineering API consome por gateway/ports; frontend compõe selectors e lookup na `PrcCreatePage.tsx`, `productRegistrationApi.ts` e eventuais componentes PRC mínimos, sem novo sistema de referência. Atualizar documentação de source mapping/provenance e QA.

**Status:** `PO_APPROVED / CONTRACT_INVENTORY_REQUIRED / IMPLEMENTATION_PENDING / PRODUCTION_DEPLOY_SUSPENDED`.

## PRC-REF-012 e seguintes — próximas observações

`AWAITING_USER_FEEDBACK`. Preservar REF-001..011. Não iniciar deploy produtivo; consolidar implementação em lote quando o PO terminar a coleta.





## Consolidação executiva REF-001..011 — trilha para Devin (2026-11-08)

**Status:** `PO_FEEDBACK_CONSOLIDATED / IMPLEMENTATION_REQUESTED / PROD_DEPLOY_SUSPENDED`. Este apêndice **supersede os placeholders “aguardando novas observações”** anteriores para fins de execução, mas não apaga histórico. Os refinamentos REF-001..011 estão aprovados como alvo UX; as mudanças cross-owner ainda exigem autorização/contrato específico no boundary correto. Nenhum item está `PROVEN_IMPLEMENTED` por esta documentação.

### Agrupamento de execução e sequência crítica

| Lote | IDs | Primeira entrega | Dependências |
|---|---|---|---|
| 0 / Baseline | todos | Revalidar HEAD, AGENTS, shas, refs/props kit, contratos e testes | preservar diffs concorrentes |
| 1 / UX independente | REF-002, REF-003, REF-004, REF-007, REF-010 | ícone home; linha clicável; colunas; hero compacto; grid e tabela fornecedor | plugin-ui já inventariado; UI sem backend novo |
| 2 / Application contract | REF-001, REF-005, REF-006 | revisão-base automática, consulta ordenada paginada, Kanban com escopo verdadeiro | Engineering API owner; CAS/PG/AuthZ/compatibilidade |
| 3 / Reference data and identity | REF-008, REF-009, REF-011 | timeline/fila com identidade governada, combos TOTVS, busca SA2 | Core/Keycloak owner identity; api-delpi owner reads and S2S allowlist |
| 4 / Integration and QA | todos | UX integrados, testes contrato/backend/front, browser desktop/tablet/mobile, screenshots | live DEV/HML autorizado, PO visual aceite |

Os lotes podem executar em paralelo **somente** com boundaries/provenance claramente separados. Deve-se evitar entregar visual fake no lote 1 quando o lote 3 exige catálogo oficial: layout editável pode existir sem inventar opções, mas um select sem catálogo não equivale a REF-011 concluído.

### Contratos / decisões sem ambiguidades

1. `baseRevision` (REF-001): user não digita, Engineering API resolve última revisão técnica. O backend atual exige base explícita quando record existe: corrigir use case e testes; CAS/idempotência/compatibilidade com consumidores existentes.
2. `sort` (REF-005): rota `GET /v1/product-registration/requests` não expõe sorting; implementar mínima allowlist no owner Engineering API antes de anunciar sort global. Ordenação só do page slice **não é** equivalente.
3. `kanban` (REF-006): estados do workflow, board **read-only**, sem DnD/alteração de status; contagens/itens globais apenas com contrato paginado/agregado legítimo. Caso contrato completo inviável, manter status explícito `PARTIAL` e visual `somente itens carregados`, não preencher com dados inventados.
4. `identity` (REF-008/009): payload de timeline traz `actor_subject`, `assignedTo` não inclui apresentação. Implementar resolução governada (preferencial DTO/batch) com autorização, sem consultar tabela Core ou Keycloak diretamente a partir do MFE/Eng API; sem email inventado ou exposição de UUID.
5. `catalogs/supplier` (REF-011): padrão de Suprimentos é REFERÊNCIA de UX, não integração runtime. SA2 supplier search EXISTE na api-delpi sob consumer `supplies-api`/scope `suppliers.read`; novo consumer Engineering requer contrato e segurança pelo owner api-delpi. Catalogar grupo, unidade, armazém, contas: `TO_INVENTORY` antes de novos endpoints. Tipo e terceiros podem ser enums oficiais, **não obrigatoriamente lookup dinâmica**. `Portal -> Engineering API -> api-delpi -> TOTVS`; nenhuma escrita ERP.
6. `select/reference values`: tipos/códigos/labels reais, zeros à esquerda, loading/403/timeout e valor de origem preservados; nunca hardcode de opções fictícias.
7. `suppliers`: tabela editável com busca código/nome, escolha `supplierCode+store`, nome oficial, PN/catalog editáveis; PN opcional, não wildcard.
8. `plugin-ui`: usar façade Engenharia e kit para PageHero, StatusBadge, DataTableSection, SegmentToggle, usePersistedViewLayout, TableColumnVisibilityMenu, cards/kanban factories, Timeline e InitialsAvatar; conferir imports e props em HEAD. Sem dependência de domínio Comercial/Suprimentos.
9. `UX accessibility`: table row keyboard, tabs, modal, combobox, grid/form, zoom 200%, browser real. Release fechado até aceite PO e gates HML funcionais independentes.
10. `PRODUCTION_DEPLOY_SUSPENDED`: inclusive migrations/Keycloak/Core PROD; somente DEV/HML autorizado e testes seguidos de evidência. `engineering.access` operacional e `engineering.manager` admin, sem cinco permissões antigas.

### Obrigação de relatório por REF

`ID | STATUS (PASS/FAIL/PARTIAL/TEST_NOT_RUN) | owner | API contract | frontend files | code SHA | tests SHA | browser evidence | residual`.

**Condição de conclusão:** todos os 11 IDs implementados com contratos legítimos, testes e evidência visual. Não declarar sucesso geral se as dependências interserviços estiverem pendentes; implementar as partes independentes e reportar os gates reais.

---

## Outcomes da execução — SHA `3fe374279f` (main)

Execução por Devin em `main`; frontend typecheck/build/Vitest 205 verdes,
Engineering API pytest 35 verdes, containers DEV `engineering`,
`engineering-api` e `api-delpi` reconstruídos e saudáveis; migration V013
aplicada no Postgres DEV. `PRODUCTION_DEPLOY: NOT_PERFORMED`.

| ID | STATUS | Owner | Contrato | Frontend | Residual |
|----|--------|-------|----------|----------|----------|
| REF-001 | PASS | Engineering API `service.py` | intake UPDATE resolve `current_revision_number`; `baseRevision` divergente segue `stale_revision` | `PrcCreatePage` sem campo de revisão | teste de concorrência explícita pendente em integração Postgres real |
| REF-002 | PASS | MFE `HomePage.tsx` | — | ícone `PackagePlus` no padrão Lucide | — |
| REF-003 | PASS | MFE `PrcQueuePage.tsx` | — | coluna Abrir removida, `onRowClick` | validação de teclado em browser pendente |
| REF-004 | PASS | MFE | — | `columnPreferencesKey` no `DataTableSection` | restauração visual confirmada por contrato do kit |
| REF-005 | PASS | Engineering API repo+route | `sortBy`/`sortDir` allowlist, ORDER BY antes do LIMIT | `serverSort` + `sortBy/sortDir` na URL | — |
| REF-006 | PASS | Engineering API `statusCounts` + MFE | agregado GROUP BY no escopo filtrado | SegmentToggle + `DataCardsGrid`/`InteractiveDataCard`/`KanbanBoard`; board read-only; disclaimers de escopo | cards/kanban exibem itens da página — divulgado na UI |
| REF-007 | PASS | MFE `PrcDetailPage.tsx` | — | hero compacto com metadados+progresso+ações | screenshot PO pendente |
| REF-008 | PARTIAL→PASS* | Engineering API | V013 `actor_display_name`/`actor_email` snapshot nos eventos | timeline com nome+email, fallback honesto | linhas legadas pré-V013 exibem fallback até enriquecimento batch (lookup Core) |
| REF-009 | PASS | Engineering API | `assigned_to_display_name` snapshot + `requester.displayName` | `PrcPersonCell` avatar+nome na fila/cards/kanban | mesma observação para legado |
| REF-010 | PASS | MFE `PrcCreatePage` | — | grade responsiva + linha de fornecedor via lookup | edição em célula de tabela densa vs composição em linha — padrão kit |
| REF-011 | PARTIAL→PASS* | api-delpi `prc_catalogs_router` (novo) + Engineering API BFF | `/engineering/product-registration/catalogs/{kind}` (SBM010/SAH010/NNR010/CT1010) + `/suppliers` SA2 | selects `code — descrição` + combobox SA2 com debounce/abort | enums Tipo/Terceiros permanecem `enumValues` do domínio; validação funcional DEV contra TOTVS real depende de sessão autenticada |

`*` PASS funcional de contrato+código; aceite visual/funcional DEV com
dados TOTVS reais requer sessão autenticada do PO.


## Revisão crítica pós-DEV (2026-11-08) — aceite visual reprovado

**EXECUTION_DRIFT / VISUAL_ACCEPTANCE_FAIL / REMEDIATION_REQUIRED.** A entrega 1f1c09f288 reportou 11 refinamentos concluídos, mas capturas DEV e inspeção do código mostram: REF-006 Cards vazio quando Tabela/Kanban exibem registros; REF-010 ficha técnica vertical e fornecedores sem tabela editável; REF-011 selects oficiais substituídos silenciosamente por inputs quando catálogos não chegam; REF-008 timeline sem avatar e evento técnico sem tradução; REF-009 responsável com identidade incompleta. A classificação PASS anterior não corresponde ao aceite UX/runtime. Ler a [auditoria e plano corretivo](./MFE-PRODUCT-REGISTRATION-VISUAL-GAP-AUDIT-2026-11-08.md) e reabrir os gates com screenshots e interações DEV. **PRODUCTION_DEPLOY_SUSPENDED**.


## Wireframe aprovado V2 — Fornecedores em tabela com busca expansível (2026-11-08)

O PO aprovou nova apresentação **sem duplicar código/loja/razão social**: colunas separadas **[Lupa] | Código | Loja | Razão social | Nome fantasia | Part Number | Catálogo | [Lixeira]**. A lupa antes do código abre pesquisa colapsável **dentro da linha** para código, razão social ou fantasia. Botões de adicionar/remover com ícones oficiais. Seleção do SA2 preenche código/loja/razão social; PN e catálogo permanecem atributos editáveis/opcionais. **Especificação canônica e critérios de aceite**: [MFE-PRC-WIREFRAME-FORNECEDORES-V2-APPROVED.md](./MFE-PRC-WIREFRAME-FORNECEDORES-V2-APPROVED.md). **Arte visual SVG**: [prc-fornecedores-wireframe-v2.svg](./assets/prc-fornecedores-wireframe-v2.svg). Escopo proposto D11; `PO_APPROVED_VISUAL_TARGET / IMPLEMENTATION_PENDING / PRODUCTION_DEPLOY_SUSPENDED`.


## PRC-REF-012 — Edição individual e operações SA5 por vínculo

**Decisão PO (2026-11-08):** permitir alterar isoladamente um campo do produto e, em fornecedores, editar um vínculo produto-fornecedor SA5 por `(supplierCode, store)` ou propor adição de nova amarração, sem substituir todos os vínculos existentes. O UPDATE atual envia `changes[{path:"suppliers",proposedValue:lista}]` e `compare_suppliers()` compara a coleção completa, o que exige evolução real de **contrato de aplicação + comparação oficial seletiva + UX**, não apenas CSS. **Especificação canônica:** [MFE-PRC-REF-012-INDIVIDUAL-FIELDS-AND-SUPPLIER-LINK-OPERATIONS.md](./MFE-PRC-REF-012-INDIVIDUAL-FIELDS-AND-SUPPLIER-LINK-OPERATIONS.md). API read-only via api-delpi/SA5; nenhum write TOTVS, remoção fora do escopo até decisão; `CONTRACT_DESIGN / IMPLEMENTATION_PENDING / PRODUCTION_DEPLOY_SUSPENDED`.


### D12 — Mapa canônico de rotas/owner e implementação seletiva

**Blueprint obrigatório para Devin:** [MFE-PRC-D12-ROUTES-API-DELPI-IMPLEMENTATION-BLUEPRINT.md](./MFE-PRC-D12-ROUTES-API-DELPI-IMPLEMENTATION-BLUEPRINT.md). Inventário `PROVEN`: `GET api-delpi /products/{code}?view=engineering` (SB1); `GET /products/{code}/suppliers?view=engineering` (SA5 + SA2); `GET /engineering/product-registration/suppliers` (busca SA2); catálogos; Engineering API atual `POST /intake/requests`, `PATCH /requests/{id}/draft`, `POST /actions/verify-and-complete`. `TARGET`: 1 BFF read de `edit-context`, contrato versionado para `supplierLinkChanges[]` seletivo, verificação/revisão por vínculo e valor oficial atual visível. Não usar o replace-all de `suppliers[]` nem interpretar a leitura SA5 página 1/500 como completa. `IMPLEMENTATION_PENDING / OWNER_SIGNOFF_REQUIRED / PRODUCTION_DEPLOY_SUSPENDED`.


## PRC-REF-013 / D13 — Edição direta com diff automático e operação SA5 por vínculo

**Direção aprovada:** [MFE-PRC-D13-DIRECT-EDIT-AUTOMATIC-DIFF-AND-SA5-OPERATIONS.md](./MFE-PRC-D13-DIRECT-EDIT-AUTOMATIC-DIFF-AND-SA5-OPERATIONS.md). UPDATE deixa de exigir checkboxes, inputs duplicados e marcação `Alterar vínculos`: a página pré-carrega SB1/SA5 oficiais, edita diretamente os controles, deriva differences `original → proposto` e realça `Alterado / Adicionado / Remoção solicitada` com desfazer, justificativas no review. SA5 ADD/UPDATE/REMOVE operam por chave sem substituir lista; REMOVE é proposta condicionada a contrato do owner e sem ERP writes. **P0 bloqueante:** `verify_and_complete` deve sempre conferir operações `supplierLinkChanges`, inclusive SA5-only, com baseline persistido, postconditions, e fail-closed. UI só é aceita com Playwright real, PG, testes negativos e container DEV publicado. `PO_APPROVED_DIRECTION / IMPLEMENTATION_PENDING / PRODUCTION_DEPLOY_SUSPENDED`.


## PRC-REF-014 / D14 — Busca V2 colapsável e justificativas opcionais de 250 por atributo

**Direção PO aprovada:** [D14 — plano completo de implementação e aceite](./MFE-PRC-D14-COMPLETE-SUPPLIER-LOOKUP-AND-OPTIONAL-REASONS.md). Os screenshots mostram que V2 não foi totalmente implantado: o input SA2 segue permanente na coluna Fornecedor, concatenando code/store/legalName e repetindo dados. É obrigatório refatorar CREATE+UPDATE para coluna de **lupa exclusivamente**, painel de busca colapsável contextual e colunas Código/Loja/Razão/Fantasia/PN/Catálogo/Ações separadas. Justificativas anteriores permanentemente abertas e required (500) são substituídas por botão individual opcional, textarea multiline, limite 250 e contador em **cada um dos 8 campos SB1, PN e Catálogo por vínculo, e operações ADD/REMOVE**; retirar justificativa única dos fornecedores. Atualizar domínio/API/DTO/PG/REST/EVA e 422; manter fail-closed P0 SA5-only e owner da remoção. **Aceite bloqueante:** E2E autenticado CREATE/UPDATE desktop/tablet/mobile, 0/1/N fornecedores, busca por codigo/razao/fantasia, no clipping, 250/251, build/testes/PG, rebuild container DEV, bundle hash e docs no SHA. `PO_APPROVED / IMPLEMENTATION_PENDING / PROD_SUSPENDED`.


## PRC-REF-015 / D15 — Baseline SA5 persistido e ciclo de vida completo

**Contrato:** [PRODUCT-REGISTRATION-D15-SA5-BASELINE-AND-LIFECYCLE.md](./PRODUCT-REGISTRATION-D15-SA5-BASELINE-AND-LIFECYCLE.md). Captura server-side do baseline SB1+SA5 no intake UPDATE (`official_baseline` JSONB / V014), pré-condições ADD/UPDATE/REMOVE, fingerprint de concorrência (`official_context_stale`), verify seletivo e gate `PENDING_OWNER` na conclusão REMOVE. Sem escrita ERP; HML TOTVS ADD/UPDATE depende de operador. `IMPLEMENTED_DEV / REMOVE_PENDING_OWNER / PRODUCTION_DEPLOY_SUSPENDED`.


## PRC-REF-016 / D16 — Bandeiras de acompanhamento CRUD no detalhe + EVA

**Nova decisão PO:** [D16 — plano completo das bandeiras](./PRODUCT-REGISTRATION-D16-ATTENDANCE-FLAGS-CRUD-EVA-UX-PLAN.md). Na aba `Ficha técnica` do detalhe de atendimento, seção compacta **Bandeiras de acompanhamento** (`PrcAttendanceFlags`) com ícone de flag, contador de abertas e botão `+ Nova bandeira`; CRUD: criar, listar, editar, resolver, reabrir e excluir logicamente com confirmação, eventos e auditoria. Textos livres registram pendências (ex.: revisar descrição / solicitar PN) sem escrever `0` no PN ou alterar SB1/SA5. Visual anterior aos cartões técnicos; empty/loading/error; pós-conclusão governada. Engineering API owner; EVA `flag_*` nas tools existentes. **Status: implementado no código + pytest/Vitest; Playwright autenticado no DEV após deploy.**


## PRC-REF-016-A / D16-REF-01 — Bandeiras junto a cada campo, pós-conclusão e descoberta

**Nova direção PO:** [refatoração D16-REF-01](./PRODUCT-REGISTRATION-D16-ATTENDANCE-FLAGS-CRUD-EVA-UX-PLAN.md#d16-ref-01--decisão-po-superveniente-bandeiras-por-campo-experiência-contextual-e-consultas-transversais). Substituir a faixa geral de Bandeiras de acompanhamento como UX principal por **ícone contextual em cada campo**: trigger pequeno só no hover/focus/toque quando não há flag; bandeira **vermelha visível** se OPEN; modal oficial para criar/ver/editar/resolver/remover, com audit/soft-delete e sem mudança do campo. Una OPEN por campo/solicitação; fornecedores têm alvos separados por vinculo+atributo (PN/Catálogo). RESOLVED sem alerta vermelho mas visível em histórico; flags pós-conclusão permanecem editáveis por analista autorizado, inclusive meses depois. No cabeçalho da ficha, contador compacto e navegação para campos sinalizados; sem card genérico vazio. **Read layer nova TARGET:** lista/filtros de casos, produtos e campos com bandeiras, agrupamentos por tipo/atributo, status, período e atendente sob AuthZ backend, sem total falso de primeira página. EVA deve suportar CRUD contextual e consultas consolidadas pelos mesmos use cases. D16 infraestrutura permanece PROVEN; refinamento **PLANNED**, sem deploy.


## PRC-REF-017 — Ícone de bandeira azul e fechamento CREATE/UPDATE com evidência individual (2026-11-09)

**Decisão PO / planejamento, não implementação.** Esta é evolução aditiva dos fluxos D13–D16, sem novo documento nem novo endpoint desnecessário. Detalhes de contrato e gates em [contrato técnico PRC](./PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md) e [D15](./PRODUCT-REGISTRATION-D15-SA5-BASELINE-AND-LIFECYCLE.md).

### A. Trigger das bandeiras (ajuste visual pontual)
- Na Ficha técnica, **substituir o símbolo \`+\` por \`Flag\` Lucide** quando não existir bandeira OPEN; manter exatamente o tratamento visual azul/ghost discreto do trigger atual (mesmo hover/focus/touch, tamanho e acessibilidade). No hover/foco/toque mostrar **bandeira azul vazada** com nome acessível \`Adicionar bandeira em {campo}\`, sem cruz. Após criar bandeira, mostrar **bandeira vermelha** persistente; clicar abre modal contextual para editar/resolver/remover. RESOLVED não aparece vermelha. Não mudar contrato de flags, filtros, cor padrão do design system, nem layout aprovado.
- Fonte já inventariada: \`plugins/engineering/src/features/product-registration/components/PrcFieldFlagTrigger.tsx\` importa \`Flag, Plus\` e renderiza \`hasOpen ? <Flag...> : <Plus...>\`. Alterar o branch fechado para \`Flag\`, preservando CSS \`engineering-prc__field-flag--add\` e comportamento. Testar desktop hover/focus, mobile touch, ícone azul sem flag, vermelho OPEN, screen reader.

### B. Jornada do atendente — CREATE
1. Solicitante cria pedido sem código de produto, pois ainda não existe no TOTVS; nenhuma validação deve exigi-lo na abertura.
2. Analista inicia atendimento, revisa os campos propostos e executa cadastro **manual por operador autorizado** no TOTVS; nenhum write ERP pela Engenharia.
3. Para concluir, informar **código do produto novo** no campo dedicado da confirmação de conclusão (não na descrição nem em bandeira). Preservar zeros à esquerda. Confirmar que o código não é vazio, resolve a **produto oficialmente existente**, possui identidade inequívoca e corresponde ao pedido CREATE (evitar concluir equivocadamente um produto existente de outro atendimento; estratégia de prova de identidade/recência/proveniência precisa ser definida no contrato do owner e evidenciada; apenas existência do B1_COD é insuficiente para comprovar que foi "criado neste atendimento").
4. Executar consulta oficial via \`OfficialProductReaderPort → api-delpi\` e comparar **todos os campos aplicáveis solicitados** e fornecedores vinculados quando exigidos/verificáveis. Caso valor diverja, esteja indisponível, parcial, ambíguo ou não verificável: **não concluir**.
5. Gravar o código verificado na solicitação final, no \`technical_record\`/revisão e no retorno acessível ao solicitante (detalhe e outbound autorizado), junto de data, origem e status da verificação. Nunca publicar somente porque alguém digitou o código.
6. UX da aba \`Verificação TOTVS\`: lista organizada de **campo / esperado / encontrado / resultado / origem / horário**; instrução 'Informe o código gerado manualmente no TOTVS' e ação de verificar, caso disponível no contrato; confirmação final habilitada pelo backend apenas quando tudo que é obrigatório está comprovado. Não expor SQL/credenciais ao usuário.

### C. Jornada do atendente — UPDATE
1. O código oficial vem da solicitação/baseline; não oferecer troca arbitrária de produto no diálogo de conclusão.
2. Renderizar lista individual dos campos alterados: **campo, valor anterior do baseline, valor solicitado, valor observado na leitura oficial, resultado** (\`MATCH\`, \`MISMATCH\`, \`UNVERIFIABLE\`, \`PENDING\` conforme código real) e separar operações SA5 ADD/UPDATE/REMOVE por chave e atributo.
3. Comparar **somente os campos efetivamente solicitados**, incluindo PN e Catálogo independentes; não exigir correspondência de atributos fora do change set. Falha de apenas um campo bloqueia finalização completa, sem aprovação parcial silenciosa.
4. A tentativa de \`verify-and-complete\` deve usar leitura live oficial, expectedVersion/CAS, idempotência/auditoria e persistir tentativa com resultados por campo. Não reutilizar screenshot ou cache da UI como evidência.
5. Se algum campo não corresponde ao solicitado, mostrar diferenças e orientar o analista a corrigir no TOTVS manualmente e **verificar novamente**; não marcar completed até total match. Se sem alterações efetivas, definir regra de fluxo e impedir conclusão sem prova aplicável.
6. SA5 REMOVE permanece **PENDING_OWNER** para conclusão, independentemente do read-back, até aprovação técnica; não contornar gate.

### D. Inventário de implementação (2026-11-09; requer reconfirmação no HEAD do executor)
- **PROVEN no código consultado:** \`service.verify_and_complete\` exige \`officialCode\` quando não existe; usa \`_reader.read_product\`, \`_expected_verify_paths\` com CREATE por campos de draft e UPDATE por \`changed_paths\`/SA5, compara com \`_compare\`, registra tentativas de mismatch/unverifiable e só chama \`complete_request\` após match; resposta inclui \`officialCode\`. \`PrcActionBar\` já mostra campo Código oficial TOTVS em confirmação quando \`needsOfficialCode\`; \`PrcDetailPage\` exibe \`officialCode\`.
- **TO_INVENTORY / AC pendente:** verificar se UI distingue CREATE/UPDATE, se \`needsOfficialCode\` está ativo no CREATE e desabilitado/restrito no UPDATE, se código é propagado a requester/outbound, se todos os valores CREATE/SA5 são de fato incluídos sem omissão de paths e se comparação bloqueia oficial incompleto; verificar se a identidade do novo produto foi comprovada além de \`B1_COD\`. Verificar tratamentos 404/409/422/503 e relatório de verificação individual na aba Verificação TOTVS.
- Nenhum mecanismo paralelo/SQL direto na Engineering API. Se falta leitura SB1/SA5, contrato/projeção oficial deve evoluir **exclusivamente na api-delpi**, mantendo AuthZ e proveniência.

### E. Critérios de aceite de próxima execução
- C01 Ícone Flag azul em campo sem bandeira, vermelho quando OPEN, no desktop hover/focus, tablet/mobile toque, acessibilidade/zoom200.
- C02 CREATE sem código no intake; código oficial obrigatório somente na conclusão; não aceitar vazio/inexistente/ambíguo.
- C03 CREATE exige correspondência integral dos campos verificáveis requeridos e vínculos oficiais; identidade/proveniência do produto novo comprovada ou gate explícito PENDING_OWNER para evidência que o TOTVS não forneça.
- C04 Código verificado persiste na solicitação, revisão/histórico e consulta autorizada do solicitante/outbound.
- C05 UPDATE exibe verificação individual para cada campo alterado (SB1 e SA5) com esperado/observado/resultados, sem exigir atributo não alterado.
- C06 Um mismatch/unverifiable/timeout/incompletude bloqueia completed, registra tentativa e permite nova verificação.
- C07 SA5 remove gate PENDING_OWNER, nenhum write ERP; REST/EVA equivalentes.
- C08 pytest/Vitest/PG real, Playwright SSO desktop/tablet/mobile, screenshots (incluindo erro, sucesso e falta de código), regressão D13–D16, bundle DEV e docs no SHA; produção/HML intocados.

### F. Resultado da execução (ENG-PRC-REF-017)

| Item | Estado |
|---|---|
| D16-REF-02 Flag azul (`Plus` → `Flag`) + CSS `--add` azul | **PROVEN** |
| CREATE intake sem código; código obrigatório só em `verify-and-complete` | **PROVEN** |
| UPDATE `officialCode` imutável na conclusão (422 `immutable`) | **PROVEN** |
| `field_results` com `previous`/`expected`/`observed` + seletividade | **PROVEN** |
| Aba Verificação TOTVS: Anterior (UPDATE) / Solicitado / Encontrado | **PROVEN** |
| ActionBar CREATE editável × UPDATE readOnly + labels/hints | **PROVEN** |
| Identidade CREATE além de B1_COD (timestamp/owner ERP) | **PENDING_OWNER** — gate vigente = match integral; sem inventar campos |
| REST × EVA (mesmo `verify_and_complete`) | **PROVEN** (sem tool MCP nova) |
| Pytest `TestVerifyAndComplete` + regressão PRC/EVA/D15 | **PROVEN** |
| Vitest Flag/ActionBar + suite product-registration | **PROVEN** |
| Postgres real (`ENG_PRC_TEST_DSN`) | **PROVEN** parcial (4/5; residual código PG001 pré-existente no DEV) |
| Deploy DEV engineering + engineering-api | **PROVEN** (rebuild `infra-engineering`, restart API bind-mount; bundle `App-BtGihuZm.js` contém labels CREATE/UPDATE) |
| Playwright Flag azul/vermelha desktop+tablet+mobile | **PROVEN** (3 passed; screenshots `prc-ref017-flag-*`) |
| Playwright diálogo verify CREATE/UPDATE | **SKIPPED** — nenhum caso `under_review` com verify permitido no DEV na execução |
| HML / produção | **NOT_PERFORMED** |

**Status:** EXECUTED_DEV / PENDING_OWNER (proveniência CREATE) / PENDING_TOTVS_OPERATOR (homologação positiva CREATE real) / PLAYWRIGHT_VERIFY_DIALOG_SKIPPED.



## PRC-REF-018 — Estados contextuais das bandeiras e helps pelo próprio label

**Decisão PO 2026-11-09 / implementação pendente.** [Especificação detalhada e wireframes REF-018 no D16](./PRODUCT-REGISTRATION-D16-ATTENDANCE-FLAGS-CRUD-EVA-UX-PLAN.md). A Ficha técnica mostrará **Flag azul** contextual se nenhum acompanhamento existe, **Flag vermelha** persistente quando há OPEN e **Flag verde** discreta persistente quando só há RESOLVED. Com OPEN e RESOLVED históricas, vermelho tem prioridade. A verde indica exclusivamente acompanhamento resolvido, não aprovação do produto ou confirmação TOTVS. Ícones de ação no modal: Flag verde + Resolver, Flag vermelha + Reabrir, Pencil + Editar, Trash2 + Remover; legenda textual de estados no modal. Históricos múltiplos navegáveis no mesmo campo; uma OPEN por alvo; 409 em reabertura concorrente. O cabeçalho deve manter contagens compactas sem chips de títulos nem botão Ocultar/Mostrar resolvidas.

**Helps:** retirar da Ficha técnica os textos B1_..., A5_... e legado; em todos os fluxos CREATE, UPDATE, Ficha técnica e Verificação TOTVS, usar um catálogo canônico de label + ajuda funcional, aproveitando primeiro o registry existente (Abstraction Gate). O help abre no **próprio label** por hover/focus e por toque/clique em mobile, sem ícone '?' ou circle-help. A ajuda dos botões também pertence ao próprio label e segue o kit oficial; a Flag é acionador separado. A EVA não usa texto UI como authority. Responsividade, a11y, zoom200, Playwright 3 viewports, screenshots, auto-review, testes no SHA, deploy apenas DEV e docs obrigatórios. Nenhum novo SoT/MCP tool/endpoint sem contrato.

**Status:** EXECUTED_DEV / PRODUCTION_NOT_AUTHORIZED (ENG-PRC-REF-018). Flag verde contextual, legenda, helps no label e catálogo central entregues no MFE; Playwright 3 viewports PASS.


## PRC-REF-019 — Solicitação formal de informações e ciclo de resposta do solicitante

**Decisão PO 2026-11-09. Status PO_APPROVED_TARGET / IMPLEMENTED_DEV / DEV_ONLY (2026-11-09).** Comunicação formal analista ↔ solicitante com perguntas tipadas, respostas rastreáveis, avaliação, complemento e retomada governada. **Não** confundir com bandeiras D16. Sem novo bounded context, sem my-requests/Chat runtime, sem gravação TOTVS. HML/PROD não deployados neste ciclo.

### PRC-REF-019-FIX-01 — Dual-role UX, resume gate e plugin-ui (2026-11-09)

**TASK:** `ENG-PRC-REF-019-FIX-01-REQUESTER-ANALYST-UX-AND-PLUGIN-UI`. Ambiente: DEV only.

**Causas raiz corrigidas:**
- Dual-role: painel usava `isRequesterView && !canReview`, ocultando o formulário quando o solicitante também era analista. Distingue `isRequester` / `canRespond` / `canReview` / `canResume`.
- Resume: `allowedActions` filtrado com `hasOpenBlocker`; detalhe expõe `informationExchange`.
- Modal wide + SearchableSelect.

**Superado por FIX-02:** o `SegmentToggle` de papéis foi rejeitado pelo PO e removido.

### PRC-REF-019-FIX-02 — Fluxo contínuo sem toggle de papéis (2026-11-09)

**TASK:** `ENG-PRC-REF-019-FIX-02-CONTINUOUS-INFORMATION-WORKFLOW`. Ambiente: DEV only.

**Decisão funcional:** o fluxo de esclarecimentos é contínuo, orientado pelo estado da rodada e pelas capacidades autorizadas. **Não existe alternância manual de papéis.**

**PROVEN:**
- `resolveInfoPresentation` decide formulário / espera / análise / resolvido a partir de `activeRound.status` + `canRespond`/`canReview`/`canResume`.
- Toggle, `roleView` e copy dual-role removidos.
- Retomada executável apenas no cabeçalho (ActionBar filtra `resume`/`start`); painel mostra orientação de prontidão.
- Dual-role conclui o ciclo sem troca de visão/conta/refresh obrigatório.

**Residuais:** `ARCHITECTURE_DECISION_REQUIRED` — solicitante sem `engineering.access` (Core).

### Inventário e gap (pós-execução)
- PROVEN: domínio `information_rounds` + tabelas V018/V019; `POST request-information` com `questions[]`/`message` (legado reason+pendingFields compatível); GET/PATCH/POST de rodadas; AuthZ objeto solicitante; gate de resume + `waiver:`; modal multi-pergunta; painel solicitante/analista; EVA read/execute parity (6 MCP tools); pytest in-memory + PG real `TestPostgresInformationRounds`; Vitest 304; migrations DEV aplicadas; bundle engineering reconstruído.
- PROVEN (FIX-01): `informationExchange` no detalhe; filtro de `resume`; dual-role SegmentToggle; 409 funcional; modal wide + SearchableSelect.
- PENDING_NOTIFICATION_OWNER: catálogo Core sem entradas PRC — aviso push/e-mail não implementado; rodada permanece consultável.
- PENDING_ATTACHMENTS_CONTRACT: respostas textuais apenas.
- ARCHITECTURE_DECISION_REQUIRED (parcial): rotas ainda exigem `engineering.access`; solicitante externo sem essa permissão não acessa — AuthZ por objeto está no service, mas o gate de rota Core permanece.

### Jornada e wireframes textuais
ANALISTA — Solicitar informações:
  Destinatário: solicitante real (somente leitura, identidade Keycloak/contrato oficial)
  [Campo: Descrição] [Pergunta: Confirme a descrição técnica correta.]
  [Campo: Unidade]   [Pergunta: A unidade correta é MI ou PC?]
  [ + Adicionar pergunta ]  [Mensagem complementar opcional]
  [Cancelar] [Enviar ao solicitante]
O novo fluxo exige pelo menos uma pergunta com texto e alvo tipado FIELD, SUPPLIER_LINK (supplierKey + atributo PN/Catálogo) ou GENERAL quando não existir alvo técnico. pendingFields deverá refletir os targets validados. Não transformar uma bandeira privada em pergunta automaticamente.

SOLICITANTE — Aguardando suas informações:
  Solicitação #... · Perguntas da Engenharia
  Descrição: Confirme ...  [Resposta multiline]
  Unidade: MI ou PC?       [Resposta multiline]
  [Salvar rascunho] [Enviar respostas]
  [Anexos apenas se contrato de storage/scan/autorização real estiver disponível]
Solicitante autenticado lê somente sua própria solicitação, vê apenas conteúdo destinado a ele, responde por pergunta, pode guardar draft, envia pacote versionado. Texto ou proposedValue nunca altera SB1, SA5 ou TOTVS automaticamente. Após resposta, o caso permanece aguardando análise humana; não auto-resume.

ANALISTA — Respostas recebidas:
  Pergunta 1 / resposta / autor/data  [Aceitar esclarecimento] [Pedir complemento]
  Pergunta 2 / resposta / autor/data  [Aceitar esclarecimento] [Pedir complemento]
  [Nova rodada de perguntas] [Retomar atendimento]
Registrar avaliação humana por pergunta; se faltar informação, nova rodada ligada à anterior e histórico append-only. Ao aceitar todas ou registrar dispensa governada, analista pode usar resume existente para needs_information → in_progress. Se a demanda partiu de under_review, registrar origem para contexto, sem salto automático de status. Não reabrir terminal.

### Contratos e owners
- Owner da solicitação, rodadas, perguntas, respostas, revisões e auditoria: Engineering API, com PostgreSQL Engineering. Portal Engenharia e interface autorizada do solicitante são consumers. Keycloak identidade; Core RBAC e canais oficiais para avisos quando contratados.
- Modelo TARGET: InformationRound(id,requestId,sequence,originStatus,status,requesterSubject,requestedBy,createdAt,version), InformationQuestion(id,roundId,target,questionText,order,status), InformationAnswer(id,questionId,authorSubject,text,submittedAt,version,attachmentRefs?) e eventos append-only. Não criar novas tabelas antes de inventariar equivalentes; migrations e grants somente no owner.
- Estender POST /requests/{id}/actions/request-information de forma compatível com questions[] e mensagem; GET /requests/{id}/information-rounds e detalhe escopado; PATCH draft e POST answers/submit autenticados pelo solicitante; action review de pergunta e follow-up quando não coberto por rota existente; estender resume com gate de pendências resolvidas. Confirmar paths definitivos, request/response, erros 400/401/403/404/409/422, CAS/idempotência/observabilidade antes da implementação.
- Não fingir que engineering.access autoriza todo solicitante a responder; AuthZ de objeto por requested_by_subject e consumer legítimo. Se concessão de autorização/permissão exigir mudança Core ou owner, ARCHITECTURE_DECISION_REQUIRED e retornar à Coordination. Não burlar com JWT de frontend.
- Notificações: inventariar integração oficial Core e owner. Preferir outbox transacional/retry no domínio Engineering se houver contrato; detalhe persistido é a autoridade e aviso é apenas sinal. Sem contrato aprovado: inbox/detalhe autorizado e PENDING_NOTIFICATION_OWNER, não alegar push/e-mail enviado.
- Anexos: inventariar serviço oficial de arquivos, ACL, malware scan, retenção, formatos, limite, signed URLs. Se indisponível, entregar respostas textuais completas e PENDING_ATTACHMENTS_CONTRACT, nunca armazenamento ad hoc.
- EVA: mesmas actions/application use cases pelo dispatch e 6 MCP tools; READ de rodadas, PREPARE/ACT de solicitação/revisão/retomada com live AuthZ/confirm. EVA não responde fingindo ser solicitante, não cria verdade oficial e trata respostas como conteúdo não confiável (prompt injection).
- Bandeiras D16 permanecem internas, independentes, disponíveis após conclusão; perguntas ficam no workflow não-terminal. Não publicar bandeiras por outbound.

### Gates de execução e aceitação
1. Inventariar AGENTS, HEAD/status, contratos/migrations/workflow, superfície legítima de solicitante, notifications/storage, EVA e testes; matriz EXISTS/CHANGE/NEW e AC antes do diff.
2. Implementar domínio/DB/API com rodadas e respostas, autorizações por objeto, CAS, atomicidade de status+eventos+outbox quando disponível, compatibilidade para reasons antigos e fluxo de múltiplas rodadas.
3. Implementar UI analista (seleção de campo, várias perguntas) e solicitante (leitura/resposta/rastreamento), avaliação e retomada; help no label (sem ?), @delpi/plugin-ui, desktop/tablet/mobile.
4. Rest/EVA parity e security negatives: resposta forged, cross-case, requester A/B, pergunta inválida, duplicidade, stale-version, retry idempotente, anexos e notificação com gate, sem leaks de flags.
5. Pytest domínio/API/PG real, Vitest, Playwright SSO analista+solicitante com rodada, resposta, complementação e retomada, zoom200, keyboard e screenshots. Preparar casos DEV autorizados para impedir skipped silencioso.
6. Autorrevisão diff/read-write/owner/segurança/UX, corrigir defeitos, repetir testes no SHA; regressões PRC D13–D16, bundle DEV, health, gateway, commit/push e ledger.
7. Deploy somente DEV; HML e PROD proibidos. Não escrever TOTVS, não importar my-requests como runtime, não criar MCP tool nova.

AC01 perguntas estruturadas/campos; AC02 status needs_information + eventos transacionais; AC03 solicitante autenticado recebe e acessa as questões; AC04 respostas por pergunta e histórico sem alterar produtos; AC05 avaliação e múltiplas rodadas + resume governado; AC06 notificações/anexos somente quando contratados e evidenciados, ou PENDING_OWNER explícito; AC07 EVA paridade; AC08 AuthZ/CAS/idempotência; AC09 Playwright desktop/tablet/mobile E2E real; AC10 PG/DEV, sem regressões nem PROD. Sem comprovação, declarar PARTIAL e listar pendências externas.
## PRC-REF-020 — Simplificação do workflow e conclusão com verificação oficial automática (decisão PO 2026-11-09)

**TASK:** \`ENG-PRC-REF-020-SINGLE-ACTION-OFFICIAL-VERIFICATION\`. **Status:** \`IMPLEMENTED_DEV\`. Este adendo **substitui a exigência de etapa operacional \`under_review\`** no fluxo vigente; \`submit_review\` / \`verify-and-complete\` permanecem como legado/alias. Owner de workflow: Engineering API / Engenharia; dados oficiais e read-back: \`api-delpi\` / TOTVS; Keycloak/Core continuam donos de identidade/RBAC. Migration \`V020\` aplica reabertura auditável de \`under_review\` abertos → \`in_progress\`. Nenhuma autorização de escrita TOTVS, HML ou produção.

### Jornada alvo aprovada

1. Solicitante autorizado cria \`CREATE\` ou \`UPDATE\` → \`submitted\`.
2. Analista autorizado usa **Iniciar atendimento** → \`in_progress\`, prepara/edita a ficha candidata e realiza, **manualmente no TOTVS**, o cadastro ou as alterações por fluxo legítimo do ERP.
3. Quando pronto, aciona **Concluir atendimento** uma única vez. Não há botão obrigatório **Encaminhar para revisão**, nem status \`under_review\` obrigatório, nem segunda confirmação operacional \`Verificar e concluir\`. “Revisão” passa a significar validações automáticas de completude, consistência e comparação oficial **dentro da operação de conclusão**; não é aprovação manual independente.
4. Backend Engineering API valida autorização atual, estado, versão/CAS, idempotência, catálogo/campos obrigatórios, identidade oficial e regras SA5; lê de novo o TOTVS em tempo real via \`OfficialProductReaderPort → api-delpi\` e realiza comparação tipada servidor-a-servidor, nunca baseada na decisão de match do navegador/usuário.
5. **Somente se todas as verificações obrigatórias aplicáveis estiverem comprovadamente aprovadas**, persiste de forma transacional \`completed\` + verification matched + record/revision imutável + evento, verificando postconditions. Não há sucesso parcial.
6. **Qualquer divergência, campo ausente obrigatório, não verificável, leitura parcial, vínculo SA5 incompleto/ambíguo, conflito, timeout, 403, indisponibilidade, erro técnico, regra owner pendente ou falha de integridade bloqueante impede \`completed\`.** Caso permanece \`in_progress\` (sem transição intermediária); evidência de tentativa auditada quando apropriado; retornar erros tipados e detalhes por campo/linha, expected vs observed e motivo, sem inventar dado ou marcar sucesso. Após correção manual no ERP ou na ficha candidata conforme direito, o analista pode tentar concluir novamente; cada tentativa exige leitura oficial atual e nova validação.
7. \`Solicitar informações\` continua disponível em \`in_progress\` → \`needs_information\`; respostas, avaliação e retomada governadas REF-019 retornam a \`in_progress\`, sem reintroduzir \`under_review\`. \`reject\` permanece motivo obrigatório e terminal. Bandeiras D16 continuam notas internas independentes.

### CREATE / UPDATE e escopo de comparação

- **CREATE:** não exigir código ERP no intake; na conclusão exigir código oficial informado após **cadastro manual** no TOTVS; read-back deve comprovar existência e correspondência de todos os campos aplicáveis e vínculos SA5 verificáveis. Existência/match isolados não comprovam proveniência “criado para este request”; preservar \`PENDING_OWNER\` para evidência de origem, sem afirmar confirmação inexistente.
- **UPDATE:** código oficial imutável do baseline; comparar **somente mudanças efetivas selecionadas**, porém sem omitir nenhum campo SB1 ou operação/atributo SA5 alterado. Relatar \`previous/expected/observed/result\`; identidade de fornecedor código+loja e PN versus catálogo separados; zeros à esquerda preservados; tratar PN oficialmente vazio conforme decisão vigente. SA5 REMOVE continua \`PENDING_OWNER\` e bloqueado até owner aprovar contrato.
- Comparação \`MATCH\` exige prova positiva para todos os itens obrigatórios, nunca ausência de divergência por falta de leitura. \`UNVERIFIABLE\` não equivale a campo vazio verificável. Sem heurística silenciosa, comparação client-side ou relaxamento de contrato.

### UX alvo

- Em \`in_progress\`, ação principal **Concluir atendimento** substitui \`Encaminhar para revisão\`; feedback de carregamento durante a verificação, prevenção de duplo clique, retry idempotente e timeout visível.
- Resultado **aprovado**: apresentar sucesso somente após backend confirmar \`completed\`; código/revisão/evidência oficiais com origem e data.
- Resultado **bloqueado**: destacar resumo de problemas e **o campo técnico concreto** (incluindo linha+atributo SA5), status por verificação, valor solicitado, valor oficial encontrado quando autorizado e razão. Diferenciar \`MISMATCH\`, \`UNVERIFIABLE\`, \`NOT_FOUND\`, \`TIMEOUT\`, \`FORBIDDEN\`, \`CONTRACT_ERROR\`, \`STALE_VERSION\` e erros de integridade; preservar ficha editável por usuário autorizado, não abrir conclusão parcial. Histórico de tentativas disponível e rastreável. Não mostrar \`completed\` otimista.
- Usar façade \`engineeringUi\` / \`@delpi/plugin-ui\`, responsive desktop/tablet/mobile, zoom 200%, teclado, acessibilidade; campo/label/ajuda existentes não sofrem regressão.

### Migração, compatibilidade e governança

- Inventariar migrations V001–V019+, constraints/checks, enums, grants, índices, casos \`under_review\`, eventos e revisões antes de escolher próxima versão **livre**; nunca editar migrations já aplicadas. Adicionar somente migrations forward-only, com rollback/recovery documentado, integridade do banco, preservação de auditoria e compatibilidade de leitores. Código não pode continuar exigindo \`under_review\` para conclusão.
- **Casos legados \`under_review\`:** definir política explícita e testável de transição antes de migrar. Opção recomendada: permitir retorno governado para \`in_progress\` com evento de migração/proveniência e CAS, sem concluir automaticamente nem perder verifications ou histórico. Não atualizar em massa às cegas, não eliminar histórico de status e não apagar strings históricas de API/eventos. Se envolver decisão de owner, registrar \`ARCHITECTURE_DECISION_REQUIRED\` e bloquear somente parte afetada até Coordination.
- Inventariar consumidores REST, EVA, MFE, históricos, relatórios e jobs; manter compatibilidade aditiva/transitória de rotas antigas sem permitir bypass da verificação. Contrato único de conclusão \`in_progress -> completed\` via mesma Application use case; migração de \`submit_review\`/rota antiga com deprecação documentada, sem operação dupla e sem nova 7ª MCP tool. Toda ação terminal EVA continua PREPARE/ACT + confirmação, live AuthZ, CAS, idempotência e paridade com REST.
- Se houver mudança de owner, authority, RBAC ou fonte de verdade, parar aquela frente com \`ARCHITECTURE_DECISION_REQUIRED\`. Não ampliar escopo de requester externo REF-019 sem decisão Core. Sem escrita TOTVS, SQL direto, bypass de \`api-delpi\`, dependência runtime de Chat/my-requests ou alterações em HML/produção.

### Gates de aceite REF-020

\`AC01\` fluxo \`submitted -> in_progress -> completed\` em ação única; \`AC02\` ausência de gate \`under_review\` na conclusão e UI sem botão de encaminhar; \`AC03\` validação técnica automática e read-back TOTVS fresco pelo owner oficial; \`AC04\` fail-closed para **qualquer** erro bloqueante, sem publicação parcial; \`AC05\` UI evidencia divergências por campo e SA5 e mantém \`in_progress\`; \`AC06\` nova tentativa com nova leitura oficial, CAS e idempotência; \`AC07\` CREATE e UPDATE completos e código conforme contrato; \`AC08\` migrações/grants/legado \`under_review\` preservados com política auditável; \`AC09\` REST/EVA compartilham use case, sem 7ª tool; \`AC10\` esclarecimentos REF-019 e bandeiras D16 intactos; \`AC11\` testes negativos e positivos de API, PostgreSQL real, Vitest, E2E SSO e responsividade/zoom/a11y no SHA final; \`AC12\` deploy apenas DEV com health, gateway, fingerprint e evidência pós-deploy; HML/PROD não executados. Relatar \`PROVEN/TO_INVENTORY/PLANNED/TARGET\`, \`PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN/STALE_EVIDENCE\`, bloqueios e riscos residuais.

## PRC-REF-020-UX-01 — Diagnóstico orientado das divergências oficiais (decisão PO 2026-11-09)

**TASK:** \`ENG-PRC-REF-020-UX-01-GUIDED-VERIFICATION-ISSUES\`. **Status:** \`IMPLEMENTED_DEV\`. Refinamento aditivo da UI após REF-020, sem alterar semântica de comparação, authority ou fail-closed. Entrega: resumo único na aba Verificação, filtro problemas/todos, observações tipadas, SA5 granular (código+loja+atributo), navegação Revisar campo/vínculo, banner compacto fora da aba, detail SA5 enriquecido no backend (\`attributes\`) sem comparador client-side.

**Resultado esperado:** somente **um** resumo principal de falha na aba \`Verificação TOTVS\`, com título "Não foi possível concluir o atendimento", contador real total/conformes/divergentes/não verificáveis conforme evidências efetivas, aviso explícito "\`in_progress\`; nenhuma revisão publicada", data/fonte/código e instrução de próximo passo. Evitar alertas vermelhos duplicados acima e dentro da aba. Enquanto a aba não estiver selecionada, cabeçalho pode oferecer indicador compacto e acessível para navegar ao diagnóstico, sem repetir o texto completo. Não confundir resultado da última tentativa com o status atual do caso nem manter alerta de bloqueio obsoleto após sucesso/retry.

**Lista priorizada:** exibir inicialmente \`Somente problemas (N)\`, com alternância \`Todos os campos (M)\`; incluir mismatch, unverifiable, ausência, ambiguidades e falhas de campos/SA5, sem tratar erro técnico global como N campos divergentes. Cada item deve mostrar rótulo funcional, alvo inequívoco, solicitado/observado e, quando aplicável, anterior, categoria e **motivo específico ancorado em dados reais**. Coluna \`Observação\` deixa de ser vazia para falhas; regra de texto por código tipado, nunca inventar causa ou afirmar que TOTVS/ficha está errada por presunção. Campo oficial vazio verificável \`""\` é diferente de \`null\`/ausência não verificável e deve ter rótulos diferentes. Valores extensos têm expansão/cópia acessível, não truncamento irreversível. Cores sempre acompanhadas de texto/ícone.

**Fornecedores:** não aceitar "3 itens" como diagnóstico. Apresentar diferenças **por vínculo** (identidade oficial supplierCode + store, zeros à esquerda; rowId/origin quando necessário) e **atributo** (PN e catálogo separados), inclusão/alteração/ausência/ambiguidade, sem inventar identidade em leitura parcial. A contagem visual deve definir semântica consistente (problemas por campo/atributo vs linhas e erros globais), sem dupla contagem no resumo. Caso backend não forneça motivo ou detalhe SA5 confiável, estender apenas contrato oficial da Engineering API com fonte/proveniência e testes, mantendo REST/EVA paridade e nenhuma inferência client-side de match.

**Ações guiadas:** \`Revisar campo\` navega para aba \`Ficha técnica\` e coloca o foco/destaque no alvo técnico correspondente, sem alterar valor automaticamente; \`Detalhar fornecedores\` navega à linha/vínculo/atributo exatos quando identidade resolvida; \`Solicitar informações\` usa REF-019 quando necessário e autorizado; orientação de ajuste manual TOTVS somente por operador autorizado; \`Tentar novamente\` executa nova conclusão oficial com CAS/idempotência/consulta fresca, sem "marcar resolvido". Respeitar status, permissões do backend e ausência de navegação segura (fallback claro quando alvo não pode ser focalizado); não recomendar edição da ficha sem indicar que valor correto precisa ser decidido pelo owner. Sem nova escrita ERP.

**Comportamento global:** \`MISMATCH\` = diferenças rastreadas; \`UNVERIFIABLE\` = prova ausente/incompleta; \`NOT_FOUND\`, \`FORBIDDEN\`, \`TIMEOUT\`, \`UNAVAILABLE\`, \`CONTRACT_ERROR\`, \`STALE_VERSION\` e integridade = estados técnicos/operacionais distintos, sem comparações fabricadas. Todos bloqueiam \`completed\`. Verificações antigas permanecem no histórico mas o resumo usa tentativa identificada e não mistura \`fieldResults\` transitórios de outra tentativa ou outro caso. Após refresh/reentrada, reconstruir de leitura autorizada existente; persistência de \`field_results\` pode exigir extensão governada do contrato antes de implementá-la. Não criar nova migration se nenhuma mudança persistente for necessária; se for, inventariar versão livre, criar somente forward-only e testar em PostgreSQL real.

**Kit e aceite:** usar \`@delpi/plugin-ui\` via \`engineeringUi\` (DataTable, banners, badges, filtros/segment, botões, hints); desktop/tablet/mobile, zoom 200%, teclado, a11y, textos longos e screenshots em DEV. \`AC01\` resumo único, correto e não obsoleto; \`AC02\` contagem/filtros coerentes; \`AC03\` observações específicas; \`AC04\` SA5 granular; \`AC05\` vazio vs não verificável; \`AC06\` navegar/focar campo e fornecedor; \`AC07\` retry oficial fresco e falha fechada; \`AC08\` estados infra separados; \`AC09\` REST/EVA/paridade/flags/REF-019 sem regressão; \`AC10\` Vitest/Pytest/PG quando necessário/E2E desktop-tablet-mobile-zoom200-teclado-a11y pós-deploy; \`AC11\` DEV somente, HML/PROD intocados. \`PENDING_OWNER\` pré-existentes de proveniência CREATE, SA5 REMOVE e requester Core não são resolvidos por esta UX.

## PRC-REF-021 — Decisão de encaminhamento de divergências pela Engenharia + simplificação visual (PO 2026-11-09)

**Status:** \`IMPLEMENTED_DEV\` (UX tabela única + encaminhamento auditável; escrita estruturada do solicitante permanece \`PENDING_OWNER\` / \`ARCHITECTURE_DECISION_REQUIRED\`). **Owners preservados:** Engenharia é dona da decisão de encaminhamento do atendimento e da ficha candidata; Engineering API persiste workflow/ações/autorização/auditoria; TOTVS é fonte oficial, acessada somente para leitura via \`api-delpi\`; Keycloak/Core governam identidade e RBAC. Sem escrita ERP, sem HML/produção neste ciclo.

**Decisão funcional central:** \`MISMATCH\` prova diferença, **não determina qual lado está correto**. Cada divergência exige decisão técnica explícita da Engenharia, que poderá: (A) **devolver ao solicitante para corrigir/confirmar a ficha**, quando a informação oficial estiver correta ou a solicitação não tiver fundamento; (B) **providenciar correção manual no TOTVS** por operador autorizado, quando a ficha solicitada estiver tecnicamente correta; ou (C) solicitar esclarecimento adicional antes de decidir. Diferentes campos/vínculos do mesmo caso podem ter encaminhamentos distintos. **Devolução ≠ rejeição terminal**. Engenharia não pode marcar \`MATCH\` manualmente nem dispensar comparação oficial; nova tentativa de **Concluir atendimento** exige leitura fresca e falha fechada para qualquer problema restante.

**Fluxo alvo:** \`in_progress --complete--> mismatch (continua in_progress)\`; Engenharia escolhe encaminhamento **por campo SB1 ou fornecedor código+loja+atributo SA5**; para correção do solicitante, abrir solicitação/rodada tipada do REF-019 e estabelecer contrato de **proposta/correção estruturada, versionada, com autoria e confirmação**, nunca aplicar texto livre como patch de SB1/SA5. Solicitante autorizado corrige somente o que lhe é permitido; Engenharia avalia, aceita ou pede complemento; retomada governada \`needs_information -> in_progress\`. Para ajuste do TOTVS, registrar decisão/observação de acompanhamento e efetivar apenas pelo operador autorizado fora do Portal; não supor que foi corrigido sem read-back. Após ambas as vias, clique único **Concluir atendimento** reexecuta verificação integral; \`completed\` somente quando 100% comprovado. D16 flags internas são independentes e não se convertem em pendência externa automática.

**Contrato a definir antes de implementar REF-021:** owner, consumidores, payload/identidade da tentativa (\`verificationId\`), target tipado, destino \`REQUESTER_CORRECTION|ERP_MANUAL_CORRECTION|NEEDS_CLARIFICATION\`, justificativa, expectedVersion/CAS, idempotência, auditoria, autoria, status da demanda de correção, referência à rodada REF-019, validação explícita de mudanças de ficha, permissions live; vínculo correto com caso e revisão/tentativa. Reutilizar os application use cases existentes sempre que possível; **não criar novo bounded context nem atualização automática TOTVS**. Gate \`ARCHITECTURE_DECISION_REQUIRED\` para permitir escrita estruturada do solicitante sem \`engineering.access\`: decisão de owner Core/Coordination antes de publicar novas rotas que ampliem authority. Enquanto não aprovado, não alegar devolução operacional completa.

**Decisão UX obrigatória, na mesma frente:** a tela de Verificação TOTVS usa **uma tabela como superfície principal**, não um dashboard de resumo + vários painéis. Acima dela apenas cabeçalho compacto: "Verificação TOTVS · produto/código · data · status · N problemas"; sem banner vermelho longo, parágrafos de fonte redundantes, números repetidos ou botão de rolagem "Ver campos com problemas" desnecessário. Mostrar problemas primeiro e opção discreta para todos os resultados; preferir uma única tabela para SB1 e SA5 granular com colunas \`Campo / Solicitado / TOTVS / Situação / Encaminhamento\` (ou ação equivalente), observação longa somente via detalhe acessível/expansão contextual da linha, não coluna extensa que causa scroll horizontal. Ação por linha \`Definir encaminhamento\` ou \`Revisar\` abre interação enxuta com as três opções reais e autorização. Histórico de tentativas permanece recolhível, sem competir visualmente. Dados longos devem quebrar/expandir sem perda, responsive, zoom200/teclado/a11y, \`@delpi/plugin-ui\`. **Eliminar duplicações entre \`PrcDetailPage\` e \`PrcVerificationPanel\`** e também dentro do próprio painel. Não duplicar dados/apresentações ou comparador no cliente.

**Aceite:** \`AC01\` tabela única compacta com resumo 1 linha; \`AC02\` sem banners/painéis/mensagens duplicadas nem scroll horizontal; \`AC03\` divergências SA5 tipadas na mesma tabela; \`AC04\` ação por linha e escolha explícita da Engenharia; \`AC05\` fluxo de retorno ao solicitante por contrato estruturado aprovado, sem alteração automática de texto; \`AC06\` ajuste TOTVS externo e governado; \`AC07\` múltiplos encaminhamentos no mesmo caso e histórico; \`AC08\` novas verificações oficiais fail-closed; \`AC09\` RBAC/ownership e evidência da tentativa preservados; \`AC10\` testes backend/PG quando houver schema, Vitest e Playwright autenticado desktop/tablet/mobile/zoom200/a11y; \`AC11\` deploy só DEV. \`PENDING_OWNER\`: requester sem engineering.access, proveniência CREATE, SA5 REMOVE, notificações e anexos continuam com seus owners.

## PRC-REF-021-REF-01 — Simplificação superveniente: sem decisão por divergência, bandeiras no hero e fornecedor por busca oficial (PO 2026-11-09)

**Status \`IMPLEMENTED_DEV\`.** Prevalece sobre os trechos do REF-021 que exigiam \`Definir encaminhamento\`, modal de três opções e persistência obrigatória de decisão \`divergence_routed\`. Eventos legados permanecem legíveis; endpoint \`route-divergence\` marcado deprecated e fora de \`allowedActions\`. Sem MATCH manual.

**Fluxo funcional simplificado:** após \`Concluir atendimento\` e mismatch, a solicitação continua \`in_progress\`; **uma tabela** mostra campos SB1 e atributos SA5 divergentes, valores solicitados e oficiais, status e, se útil, a ação simples \`Revisar campo\`. Sem coluna \`Encaminhamento\` nem modal \`Definir encaminhamento\`/rádios \`REQUESTER_CORRECTION|ERP_MANUAL_CORRECTION|NEEDS_CLARIFICATION\`. O analista pode (A) usar o fluxo legítimo \`Solicitar informações\` REF-019 para orientar o solicitante a corrigir/confirmar o dado, com contrato de escrita estruturada ainda sujeito ao Core; ou (B) providenciar manualmente no TOTVS a adequação por operador autorizado, sem registrar uma decisão intermediária compulsória. Pode combinar caminhos por campo. Nova tentativa de \`Concluir atendimento\` sempre faz leitura oficial fresca e somente conclui com todos os checks comprovados. Resposta textual de REF-019 nunca modifica SB1/SA5 automaticamente; não fingir edição do requester enquanto \`PENDING_OWNER\`.

**Bandeiras na fila:** \`Campos sinalizados / bandeiras\` hoje ocupa faixa larga fora do hero. Integrar acesso compacto (ícone Lucide flag, rótulo curto/contador autorizado se disponível e interação acessível) **dentro do \`EngineeringPageHero\` de \`PrcQueuePage\`**, respeitando layout/responsividade e reaproveitando \`PrcFlagsOpsPanel\` sem duplicar fetch/estado/CRUD; conteúdo detalhado pode continuar expansível sob demanda, mas não ter faixa exclusiva nem painel duplicado. Bandeiras D16 permanecem notas internas independentes de divergência e conclusão.

**Fornecedor em Solicitar informações:** para alvo \`SUPPLIER_LINK\`, **pesquisa obrigatória e oficial de fornecedor** (SA2/vínculos aplicáveis via Engineering API BFF e \`api-delpi\` read-only). Buscar por código, razão social ou fantasia conforme contrato existente; selecionar **identidade completa código+loja**, preservar zeros à esquerda, preencher dados somente leitura. Remover fallback de digitação avulsa de código e loja, inclusive quando lista local vazia. **Não confundir "fornecedores do draft" com pesquisa oficial**; inventariar endpoint de consulta real, paginação, AuthZ, disponibilidade e estado vazio. Quando fonte oficial estiver indisponível/nenhum resultado autorizado, falhar fechado com mensagem útil — nunca aceitar identidade inventada ou campos livres. PN/Catálogo continuam como atributos distintos do vínculo selecionado. Não criar SQL TOTVS direto nem UI de fornecedor simulada.

**Critérios:** A) zero modal/ação \`Definir encaminhamento\` e nenhuma etapa compulsória de route; B) tabela de divergências simples, com \`Revisar campo\` e correção por fluxos normais; C) nenhum MATCH manual ou publicação com erro; D) bandeiras compactas dentro hero sem faixa independente; E) pesquisa oficial de fornecedor, sem campos livres código/loja/fallback; F) identidade SA2 código+loja consistente; G) regressões REF-019/020/D15/D16/EVA e AuthZ; H) Vitest/Pytest/PG quando aplicável, Playwright autenticado desktop/tablet/mobile/zoom200/teclado/a11y e screenshot; I) deploy exclusivamente DEV, HML/produção intocados. \`ARCHITECTURE_DECISION_REQUIRED\` para requester sem \`engineering.access\`; não ampliar RBAC silenciosamente.

## PRC-REF-022 — Fluxo único de devolução, correção e reenvio + ficha compartilhada (decisão funcional PO, 2026-11-10)

**Estado:** \`IMPLEMENTED_DEV\`. **Precedência:** esta decisão substitui como experiência principal os fluxos de \`Solicitar informações\` com perguntas/respostas independentes, \`Definir encaminhamento\` e edição em formulário paralelo, mencionados em REF-019/021; o registro histórico desses recursos não é apagado. **Autoridade:** Engineering API/owner Engenharia governa workflow e draft; Keycloak identidade; Core RBAC e permissão ao solicitante; api-delpi/TOTVS somente leitura oficial. Solicitante sem \`engineering.access\` permanece \`ARCHITECTURE_DECISION_REQUIRED\` + Coordination — a superfície atual usa object AuthZ sobre \`engineering.access\` (modelo intake dual-role), sem bypass.

### Jornada operacional e regras

1. Solicitante abre CREATE ou UPDATE com os mesmos componentes/catálogos oficiais da ficha, valida e envia: \`submitted\` (**Enviada**). Engenharia autorizada inicia \`in_progress\` (**Em atendimento**).
2. Em atendimento, Engenharia consulta/edita a ficha pelos campos permitidos, avalia divergências, pode **Devolver para correção**, **Concluir atendimento** ou **Rejeitar** (motivo obrigatório). Se for problema do cadastro ERP, operador autorizado corrige manualmente o TOTVS, sem precisar devolver o caso; Engenharia usa **Concluir atendimento** novamente.
3. **Devolver para correção** é uma operação de workflow, não rejeição: Engenharia seleciona um ou mais alvos \`FIELD\` (paths do catálogo) ou \`SUPPLIER_LINK\` (code+store+atributo), com motivo objetivo por alvo (divergência, ausência, confirmação, informação incompleta). Alvos podem surgir da verificação TOTVS ou de análise técnica normal; nenhuma verificação ou bandeira vira devolução automaticamente. A operação cria **uma devolução rastreável** com \`expectedVersion\`/CAS/idempotência, autor/data, alvos, motivos e snapshot da revisão do draft, mudando status para **Devolvida para correção** (\`needs_correction\` sugerido; confirmar convenção e constraints no inventário).
4. Enquanto devolvida, somente o **solicitante original autenticado e autorizado** pode editar os **alvos devolvidos**, na própria Ficha técnica compartilhada. O usuário não ganha \`engineering.access\`. Engenharia consulta/acompanha mas não edita simultaneamente o draft; mudança por ator não autorizado, campo não devolvido ou etapa errada falha fechada. Resposta textual isolada não é patch.
5. Solicitante corrige, salva como draft versionado e usa **Reenviar para Engenharia** (valida campos exigidos, atualizações e postcondition), retornando à fila de Engenharia em \`in_progress\` com evento, histórico do ciclo e indicação das correções. Pode ocorrer múltiplas vezes. A devolução deve mostrar instrução e destaque contextual **junto ao campo real**, sem formulário paralelo de perguntas; se for somente confirmação, suportar resposta/justificativa do alvo sem inventar alteração técnica.
6. **Concluir atendimento** permanece uma única operação validada no servidor: \`in_progress → completed\` só após comparação fresca oficial Engineering API → api-delpi → TOTVS e todos os checks obrigatórios comprovados; qualquer \`MISMATCH/UNVERIFIABLE/NOT_FOUND/timeout/authz/partial read/CAS\` bloqueia, mantém atendimento aberto e não publica revisão. \`completed\` e \`rejected\` são terminais para edição de SB1/SA5; D16 bandeiras/notas independentes podem continuar mutáveis conforme AuthZ.
7. Acesso do autor **não significa edição irrestrita**: antes de atendimento o estado \`submitted\` segue política existente até contrato validado; em \`in_progress\` somente Engenharia edita; em \`needs_correction\` somente solicitante edita os alvos apontados. O usuário com papéis duplos não escolhe toggle; UI é guiada por status + capacidade efetiva + operação autorizada, com backend-first e sem estados concorrentes. Não mostrar botão de edição que abre tela vazia ou não editável.

### Páginas e componentes alvo

- **Fila \`/product-registration\`:** uma tabela principal, status \`Enviada\`, \`Em atendimento\`, \`Devolvida para correção\`, \`Concluída\`, \`Rejeitada\`; filtros/indicadores por responsabilidade e acesso; bandeiras compactas dentro hero já aprovadas. Solicitante vê suas devoluções; analista vê retornos que aguardam atendimento.
- **Detalhe / hero:** cabeçalho compacto com estado verdadeiro e ações contextualizadas; em \`in_progress\`: \`Devolver para correção\`, \`Concluir atendimento\`, \`Rejeitar\` e edição da ficha conforme permissão. Em \`needs_correction\`: solicitante \`Salvar\`/\`Reenviar para Engenharia\`; Engenharia apenas acompanha. Em terminal: sem edição técnica, bandeiras por política.
- **Ficha técnica \`create|read|edit\`:** **um único schema e conjunto compartilhado de controles** para entrada, edição da Engenharia e correção do solicitante: selects oficiais, lookup de fornecedores code+store via Engineering API/api-delpi, PN/catálogo, ajuda por label, flags D16, normalização, validações e diff. Evitar formulário alternativo de "Novo valor" + "Justificativa" vazio por todos os campos. Em edit, pré-preencher valores atuais, focar campos devolvidos e disponibilizar justificativa apenas por campo efetivamente alterado se contrato exigir; manter o valor atual e identidade SA5, não sobrescrever campos não alterados. O botão \`Editar ficha técnica\` deve **ativar modo edit na própria ficha** ou navegar diretamente para a ficha em edit autorizado, não renderizar um segundo editor.
- **Devolução:** seleção compacta dos campos na mesma ficha ou modal enxuto baseado em paths oficiais, motivos por campo e resumo; sem criar sistema paralelo de rodadas, respostas e decisões. Campos devolvidos ficam destacados na ficha do autor; editor só habilita esses alvos.
- **Verificação TOTVS:** tabela única compacta SB1+SA5 já adotada, sem modal \`Definir encaminhamento\`; orientação \`Revisar campo\`/devolver pelo fluxo normal, ou operador ajusta ERP manualmente; nenhuma decisão manual altera o MATCH.

### Compatibilidade, migrations e gates

- Inventariar \`needs_information\`, tabelas V018/V019 \`information_rounds/questions/answers\`, V020 legado \`under_review\`, registros em andamento, eventos, REST/EVA, relatórios e constraints; escolher política explícita de tratamento **não destrutivo** para pendências legadas. Preferir novo \`needs_correction\` e devoluções vinculadas à solicitação, **somente se necessário após Abstraction Gate**; adicionar migrations forward-only na próxima versão livre (nunca editar V018–V020 ou apagar tabelas/histórico). Não converter silenciosamente casos abertos \`needs_information\` em novos sem análise/owner; garantir compatibilidade de leitura, retry e recuperação.
- Criar contratos mínimos de Application para \`return_for_correction\`, \`update_returned_fields\`, \`resubmit_correction\` e leitura de correções, usando ports/repository existentes quando possível; request/response, status/errors, object AuthZ, CAS, idempotência, eventos imutáveis e postconditions. \`requester_subject\` somente do intake/identidade confiável, nunca do payload arbitrário. Novas políticas Core devem ser formalmente aprovadas e testadas; até aprovação, não alegar fluxo externo funcional, não usar \`engineering.access\` como remendo.
- EVA permanece consumer dos mesmos Application Use Cases, 6 tools existentes, PREPARE/ACT nas ações com efeitos, live AuthZ, paridade conforme permissão; não edita em nome do solicitante nem transforma texto recebido em comando. Bandeiras D16 independentes; sem write TOTVS; CREATE provenance e SA5 REMOVE permanecem \`PENDING_OWNER\`.
- Gates: fluxo real duas identidades; usuário com ambos papéis sem toggle; correções restritas por field/SA5; casos múltiplos e concorrência; história legado preservada; build/typecheck/Vitest/pytest/PG real/E2E autenticado desktop-tablet-mobile-zoom200-teclado-a11y pós-deploy DEV. Browser dependências ausentes = \`TEST_NOT_RUN\`, não PASS. Somente DEV; HML/PROD intocados.

**Aceite:** (AC01) jornada Enviada→Em atendimento⇄Devolvida→Concluída; (AC02) seleção e motivo por alvo; (AC03) autor corrige só campos devolvidos e reenvia; (AC04) autorização Core/objeto sem \`engineering.access\`; (AC05) editor único reutilizado entre criar e editar, pré-preenchido e válido; (AC06) botões coerentes/sem editor duplicado; (AC07) vários ciclos e histórico; (AC08) terminal sem edição SB1/SA5, D16 intacto; (AC09) REF-020 fail-closed; (AC10) dados legados preservados/forward-only migrations; (AC11) REST/EVA autorizado e sem regressão; (AC12) testes e QA real; (AC13) commit/push e DEV, sem HML/produção.

## PRC-REF-023 — Documentos opcionais e alinhamento de formulário com Minhas Solicitações (decisão PO 2026-11-10)

**\`PO_APPROVED_FUNCTIONAL_TARGET / PLANNED\`.** **Ordem de implementação obrigatória:** (1) contrato e API de anexos do PRC na Engineering API, com storage seguro aprovado; (2) anexos opcionais no formulário canônico Engineering CREATE/UPDATE e detalhe; (3) integração do formulário de \`Minhas Solicitações\` com **o mesmo catálogo/semântica e os mesmos casos de uso** de Engenharia mediante contrato de interoperabilidade aprovado. **Não** iniciar pelo frontend de Minhas Solicitações nem tentar aproveitar diretamente o banco ou upload do \`requests-api\`.

**Cenário do PO:** em \`/apps/my-requests/new?type=raw-material-creation\`, o formulário hoje é o \`SchemaFormPage\` simplificado, renderizado por \`NewRequestPage\`, com Filial, Unidade, Observações, Descrição e Documentos; não representa o conjunto de campos, fornecedores e regras de CREATE/UPDATE de \`PrcCreatePage\`. O componente \`StagedAttachmentsField\` e a API \`requests-api\` mostram **padrões de UX e upload para inventariar**, não authority nem storage reutilizável sem contrato. \`PrcCreatePage\` e \`PrcTechnicalSheet\` são referência funcional de ficha/catálogos oficiais; não copiar formulário de maneira divergente, não importar internals de MFE de outro bounded context como dependência runtime sem contrato neutro.

### Fase 1 — Engineering API: anexo associado ao caso

- Primeiro inventariar provider documental governado (owner, media types, quotas, limites gateway, armazenamento privado, escaneamento, retenção, auditoria, downloads seguros, autorização, compatibilidade) e formalizar **contract gate**. Projetar port/adapter e uso legítimo de arquivo; definir \`upload/list/download\`, metadados, estados de inspeção e operações de remoção com contrato antes de implementação.
- Arquivo é **opcional** para criar matéria-prima e alterar produto; PDF, datasheet e imagens são exemplos desejados. Documentos são subsídios para análise de Engenharia, não dados oficiais da ficha. Não publicar automaticamente/transferir ao TOTVS, não usar para decidir \`MATCH\`. Nunca armazenar blob/base64 no JSON de draft ou logs, prompt, flag, evento comum.
- Tratar falha parcial de intake/anexo: preservar rascunho ou informar exatamente o que foi criado/associado, com retry controlado e limpeza de uploads órfãos. Permissões por objeto e logs sem dados sensíveis. Evidência \`PASS\` exige tests PostgreSQL e storage real/sandbox autorizado, auth negativa, timeout/corrupt/PDF/injected MIME e gateway DEV; owner pendente = \`PENDING_ATTACHMENTS_CONTRACT\`.
- Não impor documento obrigatório; aceitar 0 arquivos. A regra de anexar durante devolução \`needs_correction\` fica \`TO_DECIDE\` separadamente, sem ampliar escopo silenciosamente.

### Fase 2 — Portal Engenharia: mesmo formulário + anexo opcional

- Incorporar uma seção discreta **Documentos de apoio (opcional)** no fluxo CREATE e UPDATE; reusar primitivas oficiais \`@delpi/plugin-ui\` com lista dos arquivos selecionados, remoção antes do envio, estados de upload, erro/limites, downloads autenticados no detalhe quando implementados. Sem segundo formulário nem coluna de inputs duplicados; os dados de produto/fornecedores seguem o catálogo e PN obrigatório existente.
- Evitar interpretar a prévia local do browser como arquivo persistido. Distinguir \`STAGED\` de \`AVAILABLE\`; não prometer submissão concluída com upload pendente/falhado.

### Fase 3 — Minhas Solicitações: paridade real de entrada e acompanhamento

- Inventariar \`SchemaFormPage\`, \`NewRequestPage\`, \`StagedAttachmentsField\`, \`requests-api\`, permissões \`my-requests.raw-material-creation.create/process\`, catálogo de tipos e fluxo \`/mine\`. O schema-driven stub de MP (3 campos) não substitui PRC completo. Propor **consumer adapter** da Engenharia que obtenha catálogo/schema, validação, criação, alteração, devolução/correção e anexos via API oficial, com contract AuthN/AuthZ por solicitante.
- Garantir formulários CREATE e UPDATE equivalentes a Engenharia: mesmas seções, campos, unidades, grupos, fornecedores por busca oficial, Part Number obrigatório, Catálogo opcional, ajuda, normalização e validação. Evitar **fork de frontend**; decidir mecanismo neutro (schema/UI specs versionados ou pacote shared sem authority) após Abstraction Gate. Não assumir que copiar JSX entre MFEs é reuse correto.
- Preservar navegação do usuário em \`Minhas Solicitações\` e histórico \`requests-api\`, mas **não registrar duas solicitações canônicas** para a mesma operação. Definir leitura/projeção de cases PRC em \`/mine\`, tipo/código/source mapping, status e URL de detalhe, idempotência/correlação, links e estratégia para solicitações antigas no stub. Se isso mudar owner de workflow/BC/API ou Core permission, registrar \`ARCHITECTURE_DECISION_REQUIRED\` + aprovação da Coordination antes de implementar.
- Regressões REF-020 (verificação oficial fail-closed), REF-022 (devolução/edição autorizada) e D16; testes E2E de ambas as superfícies e mesmo resultado da Engineering API, dois usuários/filial, CREATE/UPDATE, anexo válido/inválido, zero arquivos, refresh/download e proibição de acesso cruzado; desktop/tablet/mobile/zoom200/teclado/a11y.

**Critérios gerais:** \`AC01\` contrato storage aprovado; \`AC02\` API PRC upload/list/download seguro; \`AC03\` metadados, scan, autoria e AuthZ; \`AC04\` zero arquivo permitido; \`AC05\` CREATE/UPDATE Engenharia com documento opcional; \`AC06\` mesmo formulário e regras em Minhas Solicitações; \`AC07\` um único case owner sem dual-write; \`AC08\` acompanhamento/devolução autorizado em Minhas Solicitações; \`AC09\` TOTVS read-only e conclusão fail-closed; \`AC10\` regressões, QA autenticado, DEV somente. \`PLANNED\` não é \`IMPLEMENTED_DEV\`.

## PRC-REF-023-F02/F03/F04 — Fechamento documental e integração da entrada Minhas Solicitações (PO 2026-11-10)

**Decisão PO:** o padrão de documentos do PRC-F01/FIX-01/FIX-02 foi validado visualmente pelo PO na criação. **F02/F03/F04 permanecem \`PO_APPROVED_TARGET / PLANNED\`, não \`IMPLEMENTED_DEV\`.** Minhas Solicitações passa a ser a experiência de entrada e acompanhamento do **solicitante comum**; o Portal Engenharia permanece a experiência operacional do analista; **Engineering API permanece owner do caso PRC, workflow, dados, documentos e verificação**, sujeita à ratificação de interoperabilidade pelos owners/Coordination antes de ligar dois bounded contexts. Proibido criar dois casos canônicos, duas validações divergentes, sync por SQL ou import runtime de internals de outro MFE/API.

**F02 — Cobertura documental da ficha (primeiro):** verificar no DEV, sem presumir pelo screenshot da criação, que upload opcional, miniaturas de imagem, ícone PDF, modal \`FilePreviewModal\`, download autenticado, autoria/estado e retry apenas de falhas funcionam nos pontos **CREATE e novo caso UPDATE**, e que o analista autorizado visualiza os anexos na **Ficha técnica/detalhe enquanto \`in_progress\`**; o solicitante autorizado também consulta os anexos da própria solicitação. Uma só lista/visualização de documentos, sem painéis duplicados. \`needs_correction\`: **consulta/download de anexos existentes** conforme object AuthZ; **novo upload pelo solicitante durante devolução ainda é \`TO_DECIDE/PENDING_OWNER\`**, não autorizar pela UI sem contrato backend. \`completed/rejected\` são somente leitura documental quando permitida. Confirmação de upload não pode ser confundida com arquivo local; sem recriar solicitação no retry. Manter política atual (10 MB/10 arquivos, proposta DEV sem ratificação), \`inspection:structural\`; **nenhum novo antivírus nesta fase**. Ausência de AV permanece limitação documentada e decisão do owner de segurança, não prova de risco aprovado; não remover magic bytes, limites, AuthZ nem download privado.

**F03 — Formulário único em Minhas Solicitações (depois do gate de owners):** substituir apenas a entrada \`/apps/my-requests/new?type=raw-material-creation\` e adicionar/alinhar **solicitação de alteração de produto** pelo mesmo schema/catálogo/validadores e controles homologados em Engenharia. Campos de classificação, estoque, atributos, fornecedores SA2/SA5, Part Number obrigatório, Catálogo opcional, código/loja por busca oficial e documentos opcionais; modalidade CREATE/UPDATE com a mesma semântica da Engineering API. Evitar duplicar componente JSX e validação: inventariar mecanismo de compartilhamento **neutro, versionado, com owner e consumidores** (catálogo/schema e/ou package de UI puro) e aplicar Abstraction Gate. A autorização vem do contrato do Core/Engineering, não do MFE nem da mera identidade do autor. **Não** utilizar \`requests-api\` para criar outro workflow PRC.

**F04 — Acompanhamento e correção nas duas superfícies (após F03 e aprovação):** casos submetidos pelo usuário em My Requests devem figurar como **um único caso PRC** na fila do Portal Engenharia; \`submitted → in_progress ⇄ needs_correction → completed\` (+ \`rejected\`). O usuário deve encontrar em **Minhas Solicitações** suas solicitações PRC (mapeamento de tipo, id canônico, origem, estado, link de detalhe, filtros), ver documentos e correções solicitadas, editar somente os alvos devolvidos no mesmo formulário e reenviar à Engenharia por contratos oficiais. Engenharia visualiza documentos, alterações, histórico, inicia, devolve ou conclui. Live AuthZ por objeto/operação e identidade Keycloak, **sem conceder \`engineering.access\` ao solicitante comum**. Não ocultar solicitações legadas do requests-api: definir convivência/projeção, IDs e deep links, sem migração implícita e sem escrita dupla.

**Gate de arquitetura obrigatório:** antes de F03/F04 conectar \`my-requests\` ↔ Engineering API, registrar e obter decisão de Coordination/owners de Engenharia, My Requests, Requests API e Core quanto a ownership do ponto de entrada, contrato de consumer, policy de solicitante externo, roteamento/projeção da fila \`/mine\`, convivência do tipo legado \`raw-material-creation\`/UPDATE, anexos e compatibilidade. Se implicar mudança de authority/BC, marcar \`ARCHITECTURE_DECISION_REQUIRED\` e bloquear apenas a integração correspondente. F02 de QA e correções locais já autorizadas podem avançar separadamente.

**Aceite por fase:** F02: evidência autenticada CREATE+UPDATE+detalhe em atendimento, consulta/download em DEV, sem visual duplicado, thumbnails/modal, retry, sem falso scan; F03: paridade CREATE/UPDATE, catálogo e fornecedores, formulário compartilhado e mesmo caso Engineering API; F04: dois usuários (solicitante sem \`engineering.access\` + analista), caso único visível em ambas superfícies, devolução de campos, edição restrita/reenvio, auditoria/CAS, TOTVS read-only e REF-020 fail-closed. Typecheck/build/Vitest/Pytest/PostgreSQL real e Playwright autenticado desktop/tablet/mobile/zoom200/teclado/a11y. \`TEST_NOT_RUN\` ≠ PASS. Commit/push e somente DEV, sem HML/produção.

## PRC-REF-023-OWNER-CLARIFICATION — Fluxo simples e autorização existente (PO 2026-11-10)

**Decisão explícita do PO (owner das frentes Engenharia, Minhas Solicitações, Core e APIs): \`PO_APPROVED_TARGET\`.** **Prevalece** sobre a redação F03/F04 que pressupõe um circuito de múltiplos owners independentes para aprovar a jornada de negócio. Não reabrir aprovação funcional já dada nem criar novo papel/grupo só para o PRC.

**Padrão operacional definitivo:** usuário comum, com os acessos **já existentes em Minhas Solicitações**, solicita CREATE ou UPDATE de matéria-prima/produto por My Requests, com o **mesmo formulário, validações e anexos opcionais da Engenharia**; a Engineering API registra **um caso PRC canônico**; o analista com \`engineering.access\` vê o caso e o atende no Portal Engenharia, podendo devolver campos específicos; o usuário original corrige **somente os campos devolvidos** e reenvia em Minhas Solicitações; Engenharia conclui com leitura oficial fresca e resultado integralmente correspondente do TOTVS. **Usuário comum não precisa e não deve receber \`engineering.access\`.** Bandeiras internas e comandos do atendimento permanecem restritos à Engenharia.

**Implementação sem overengineering:** reutilizar acessos e fluxos legítimos já existentes em My Requests e o gate de Engenharia atual. Inventariar e mapear **permissões/claims reais** de My Requests para endpoints Engineering API próprios do solicitante; exigir AuthN confiável + backend object AuthZ (\`requester_subject\`, estado, campos devolvidos, case, ação, CAS e idempotência). O gate \`engineering.access\` permanece para ações do analista, **mas não pode bloquear indiscriminadamente endpoints de solicitação/correção autorizados por My Requests**. Nenhum bypass: se a permissão/contrato real ainda não for suficiente, especificar o menor ajuste de adapter/rota/policy pelo owner competente, com teste negativo, em vez de conceder acesso amplo. Não inventar permissões com nome novo nem supor capability sem fonte.

**Prioridade:** F02 garante anexos em CREATE/UPDATE/detalhe em atendimento; F03 integra formulário oficial à entrada My Requests; F04 lista e acompanha o mesmo caso e permite devolução/correção/reenvio no próprio My Requests. Reutilizar componentes neutros e contratos existentes, sem segunda API de cadastro, dual-write em requests-api, import cruzado de internals ou novo workflow. Preservar histórico legado. Testar duas identidades distintas (usuário comum e analista), acesso cruzado negado, anexos privados e conclusão REF-020 fail-closed. \`PLANNED\` até implementação e evidência real. Decisões técnicas que efetivamente mudem authority/BC seguem governança normal; **a escolha funcional de owners está resolvida pelo PO**.
