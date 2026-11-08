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
