# Portal Engenharia MFE — Plano incremental de refinamentos pós-redesign

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

## PRC-REF-008 e seguintes — próximas observações

`AWAITING_USER_FEEDBACK`. Preservar REF-001..007, sem iniciar implementação em lote até finalizar a coleta de refinamentos com o PO.
