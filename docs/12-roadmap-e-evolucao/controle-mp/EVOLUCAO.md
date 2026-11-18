# Controle de matéria-prima — evolução nativa na Minha DELPI

> **Status:** evolução futura — **não implementar a partir deste documento.**  
> **Vigência:** 2026-09-11  
> **Produto hoje:** iframe `controle-mp` (`https://controle-mp.minhadelpi.com.br`)  
> **Alvo:** MFE federado na Minha DELPI, com **Minhas Solicitações** como porta de entrada e **fila/detalhe do analista** para as tratativas.

Este arquivo é a fonte de evolução do vertical. Não substitui o [PLAYBOOK de Minhas Solicitações](../my-requests/PLAYBOOK.md) nem a arquitetura do legado no repositório `controle_mp` (`docs/ARQUITETURA.md`). Quando este texto e o PLAYBOOK D17 divergirem, **este documento vence para o produto de matéria-prima**.

---

## 1. Objetivo

Qualquer colaborador com permissão de criar solicitações de MP abre o pedido em **Minhas Solicitações** (`/apps/my-requests`), sem precisar do app iframe nem de conta local do Controle MP.

Analistas de cadastro tratam esses pedidos numa **tela de fila + detalhe especializado** (iniciar, devolver, rejeitar, finalizar com código TOTVS), no mesmo MFE.

O Controle MP legado permanece em dual-run até o cutover. Dados de produção precisam ser preservados.

---

## 2. O que existe hoje (evidência)

### 2.1 Controle MP (legado, produção)

Repositório `controle_mp`. App **embedded** no portal (`id: controle-mp`, `basePath: /controle-mp`, permissão `controle-mp.access`).

| Peça | Evidência | Implicação |
|-------|-----------|------------|
| Front React próprio | `front-cadastro-mp` | Não é Module Federation; SSO por `postMessage` |
| API Flask | `api-cadastro-mp` | Dona do domínio atual; Postgres próprio |
| Identidade local | `tbUsers` + papéis ADMIN/ANALYST/USER | Ponte recente: `central_subject` = `sub` Keycloak |
| Tipos | CRIAR / ALTERAR | Dois fluxos com regras de campo diferentes |
| Status | CRIADO → EM PROCESSO → DEVOLVIDO / FINALIZADO / REJEITADO / FRACASSADO | Devolver + reenviar já existem |
| Ficha | código, grupo, descrição, tipo, armazém, unidade, terceiro, CTA, ref. cliente, fornecedores (grid) | MVP de 3 campos em my-requests **não** cobre |
| TOTVS | Leitura SB1 / SA5; finalizar exige produto no ERP e `novo_codigo` no CRIAR | Integração de domínio, não só formulário |
| Chat | Conversas + Socket.IO + solicitação como mensagem | Canal de tratativa acoplado ao pedido |
| Catálogo local | `tbProduct` após finalizar | Cópia operacional; TOTVS continua a verdade do código |
| Notificações | S2S Core `controle_mp` | Já usa e-mail + `controle-mp.access` |

### 2.2 Minhas Solicitações (canônico de solicitações)

| Peça | Evidência | Implicação |
|-------|-----------|------------|
| MFE | `plugins/my-requests` | Tile `/apps/my-requests`; rotas internas `/mine`, `/work-queue`, `/new`, `/requests/:id` |
| API | `requests-api` `/apps/requests-api/v1` | Request Engine, workflow JSON, outbox, comentários, anexos |
| Tipo `raw-material-creation` | Seed `V007` — schema-driven, 3 campos (`description`, `unit`, `notes`) | Prova de plugabilidade (PLAYBOOK D17), **não** é o Controle MP |
| Workflow do stub | `start` / `complete` / `reject` / `cancel` | **Falta** `needs_information` (DEVOLVIDO) e `resubmit` |
| Destination | `"adapter": "none"` | Não lê TOTVS nem grava produto |
| Permissões | `my-requests.raw-material-creation.create` / `.process` | Já no manifesto; ainda não equivalem ao fluxo real |
| Referência de paridade | Cutover de `invoice-issuance` + [MIGRATION-RUNBOOK.md](../my-requests/MIGRATION-RUNBOOK.md) | Molde de dual-run + ETL one-shot |

### 2.3 Gap que este documento fecha

O stub `raw-material-creation` demonstra que um tipo novo entra no motor **sem** `if request_type` no engine. Ele **não** substitui a ficha, o ALTERAR, o TOTVS, a devolução nem a fila do analista do Controle MP.

---

## 3. Arquitetura alvo

```text
Portal
  └─ MFE my-requests
        ├─ /mine                         ← qualquer solicitante vê os próprios pedidos
        ├─ /new  (CRIAR | ALTERAR)        ← qualquer pessoa com .create
        ├─ /work-queue?type=raw-material-*  ← analista
        └─ /requests/:id                  ← detalhe + tratativa especializada
              │
              ▼ JWT
         requests-api (Request Engine)
              ├─ Postgres my_requests
              ├─ ports → api-delpi (TOTVS SB1/SA5)
              └─ outbox → Core notifications
```

O **iframe Controle MP não faz parte do alvo**. Ele só permanece até o cutover.

Um futuro “portal da engenharia” (módulo-shell com `routes[].target`) pode **apontar** para estas rotas. Não é pré-requisito nem justifica um segundo MFE de MP.

### 3.1 Duas superfícies, um bounded context

| Superfície | Quem | Onde | API |
|------------|------|------|-----|
| Solicitar e acompanhar | Qualquer pessoa com `.create` do tipo | `/apps/my-requests/new` e `/mine` | `requests-api` |
| Tratar | Analista com `.process` | `/work-queue` + detalhe especializado | `requests-api` (allowed_actions no backend) |

Não criar um plugin federado paralelo só para o analista. A fila unificada de Minhas Solicitações **é** a tela de tratativa, com feature especializada do tipo MP (como o wizard de NF).

### 3.2 Ownership

| Conceito | Dono | Não fazer |
|----------|------|-----------|
| Intake, workflow, comentários, anexos, fila, notificações | `requests-api` + MFE `my-requests` | Recriar fila no Flask |
| Ficha MP, regras CRIAR vs ALTERAR, finalizar com código | Validators/plugin do tipo em `requests-api` + feature MFE | 3 campos genéricos como produto final |
| Leitura TOTVS (produto, fornecedor) | `api-delpi` via adapter da `requests-api` | MFE chamar `api-delpi` direto; Flask TOTVS eterno |
| Identidade | Keycloak `sub` | Continuar `tbUsers.id` como identidade canônica |
| Autorização efetiva | Core RBAC + WorkflowEngine | Analista só “esconder botão” no front |

---

## 4. Modelo de produto a reproduzir

### 4.1 Tipos de solicitação

Dois `RequestType` (não um tipo só com flag escondida):

| Código alvo | Legado | Quem cria | Quem processa |
|-------------|--------|-----------|----------------|
| `raw-material-creation` | CRIAR | `.create` | `.process` |
| `raw-material-update` | ALTERAR | `.create` | `.process` |

O seed atual de `raw-material-creation` **evolui** (schema/workflow/presentation). `raw-material-update` é tipo novo.

`presentation_mode` alvo: **`specialized`** (ficha + lookups TOTVS + grid de fornecedores). O modo `schema_driven` de 3 campos deixa de ser o produto.

### 4.2 Workflow (paridade Controle MP)

Mapear para a máquina genérica do Request Engine (mesmo padrão da NF):

| Legado | Status canônico | Quem age |
|--------|-----------------|----------|
| CRIADO | `submitted` | Solicitante criou |
| EM PROCESSO | `in_progress` | Analista (`start`, `assignSelf`) |
| DEVOLVIDO | `needs_information` | Analista devolve; solicitante corrige e `resubmit` |
| FINALIZADO | `completed` | Analista `complete` (com invariantes) |
| REJEITADO | `rejected` | Analista |
| FRACASSADO | `rejected` ou motivo em payload — **decidir na implementação**, sem dois terminais sem semântica | |

Transições obrigatórias que o stub **ainda não tem:** `return` e `resubmit`.

### 4.3 Ficha (campos a preservar)

Do legado (`requestItemFields.schema.js`):

- CRIAR: `novo_codigo` (analista na finalização), grupo, descrição, tipo, armazém padrão, unidade, produto terceiro, CTA contábil, ref. cliente, fornecedores
- ALTERAR: `codigo_atual` (+ lookup TOTVS), demais campos da ficha, `novo_codigo` se houver recodificação

Invariantes de negócio a copiar (não o chat):

- Solicitante só edita em `needs_information` (e campos permitidos por tipo)
- Em CRIAR devolvido, o solicitante **não** edita `novo_codigo`
- Finalizar CRIAR exige `novo_codigo` e existência do código no TOTVS
- FINALIZADO / REJEITADO travados

### 4.4 Comentários no lugar do chat

A conversa Socket.IO do legado **não** precisa ser portada na primeira entrega nativa.

Alvo: comentários / thread já existentes no detalhe de Minhas Solicitações + notificações Core (categoria a definir, sem criar `controle_mp` paralelo eterno).

Anexos do chat legado entram como `request_attachments` na migração, se existirem arquivos.

### 4.5 Catálogo pós-finalização

`tbProduct` é cache operacional. No alvo:

- Código vigente vive no TOTVS
- A solicitação `completed` guarda o payload + código efetivo
- Uma tela de consulta no MFE (analista) pode listar MPs via lookup `api-delpi`, **não** reimplementar um segundo cadastro

---

## 5. Identidade e migração de dados

### 5.1 Identidade

Chave canônica: **Keycloak `sub`**.

O Controle MP já persiste `tbUsers.central_subject` (SSO + botão admin **Atualizar IDs**). A migração **não** casa só por e-mail. Linhas sem `central_subject` e sem e-mail na Core ficam de fora até vínculo.

`tbUsers` / senha / `role_id` locais **não** são o modelo de identidade da Minha DELPI. Papéis viram permissões RBAC (`create` vs `process`).

### 5.2 ETL one-shot (molde NF)

Padrão: script na `requests-api` (como `migrate_invoice_issuance_to_my_requests.py`).

- Dry-run e `--apply` idempotentes
- Legado **intacto** (não resetar Postgres do Controle MP)
- `payload._migration = { source: "controle_mp", legacy_request_id, … }`
- Mapear item CRIAR/ALTERAR → tipo canônico; status → tabela da § 4.2
- Usuário: `central_subject` → `users.id` da Core
- Anexos: copiar volume se houver; falhar se arquivo sumiu (flag explícita)

Proibido: dual-write eterno; `requests-api` ler o Postgres do Flask como API; MFE `my-requests` chamar a API Flask.

### 5.3 Dual-run e cutover

1. Feature nativa atrás de permissões (create/process) **sem** desligar o iframe
2. Homologar paridade (criar, fila, start, devolver, reenviar, finalizar, rejeitar, TOTVS)
3. Soft cutover: menu/iframe `controle-mp` deixa de ser o caminho principal; redirect para `/apps/my-requests`
4. Hard cutover: app embedded sai do portal; Flask só leitura/retenção
5. Retenção do schema legado — mesmo critério da NF (não `DROP` na semana do cutover)

---

## 6. O que precisa ser feito (fases)

Ordem de evolução. **Não** é plano Cursor `E*.S*` nem autorização para implementar.

### Fase 0 — Travas (documentação / produto)

- [x] Intake = Minhas Solicitações; tratativa = work-queue + detalhe do mesmo MFE
- [ ] Confirmar grupos Keycloak que recebem `.create` (qualquer pessoa ≠ todo mundo da empresa)
- [ ] Confirmar grupos que recebem `.process` (analistas de cadastro MP)
- [ ] Decidir destino de FRACASSADO e do catálogo `tbProduct`

### Fase 1 — Contrato do tipo (requests-api)

- Evoluir `raw-material-creation` para ficha real + workflow com devolução
- Criar `raw-material-update`
- Validators no plugin do tipo (zero `if request_type` no engine)
- Adapter TOTVS (produto por código, fornecedores) via `api-delpi`
- Destination no `complete` (invariantes de código)
- Permissões no manifesto + seed RBAC
- Evals/testes: P0 CRIAR, irmão ALTERAR, negativo (finalizar CRIAR sem `novo_codigo`)

### Fase 2 — MFE solicitante

- `/new` specialized (não o SchemaForm de 3 campos)
- Grid de fornecedores no kit `@delpi/plugin-ui`
- `/mine` filtrável pelos dois tipos
- Estados: loading, vazio, erro, forbidden, devolvida
- Ajuda in-app (`helpTooltips` + Manual my-requests)

### Fase 3 — MFE analista (tratativa)

- Fila `/work-queue` filtrada por tipo MP (já existe a rota; falta UX/filtro e detalhe rico)
- Detalhe: iniciar, devolver com motivo, rejeitar, finalizar (preencher `novo_codigo`, conferir TOTVS)
- Comentários e anexos de atendimento (`artifacts` se o analista gerar evidência)
- Sem Socket.IO na v1 nativa

### Fase 4 — Notificações e deep link

- Outbox `request.created` / devolvida / concluída → Core
- `action.target` = `/apps/my-requests` + `deepPath` do pedido
- Não depender da categoria `controle_mp` depois do cutover

### Fase 5 — Migração e cutover

- Script ETL + runbook (dry-run staging → apply)
- Amostragem de pedidos CRIAR/ALTERAR/DEVOLVIDO
- Comunicação: quem pedia no iframe passa a usar Minhas Solicitações
- Desligar tile `controle-mp` quando a paridade estiver assinada

### Fase 6 — Retenção

- Flask e Postgres legado só backup/consulta
- Remover Compose/DNS do iframe quando a retenção expirar (decisão Ops, não automática)

---

## 7. Proibições

| Proibido | Por quê |
|---------|---------|
| Entregar o stub de 3 campos como “Controle MP nativo” | Não cobre ficha, ALTERAR, TOTVS nem devolução |
| MFE `my-requests` → HTTP da API Flask | Viola boundary; identidade e contrato errados |
| `requests-api` SELECT no banco do Controle MP | Banco de outro contexto não é API |
| Dual-write eterno (grava nos dois) | Duas verdades |
| Novo MFE só de analista + outro de solicitante | A fila canônica já é `/work-queue` |
| Portar `tbUsers`/senha como login nativo | Identidade é Keycloak |
| Esperar o módulo-shell de engenharia | Não bloqueia o vertical |
| `if request_type ==` no WorkflowEngine | Plugabilidade do PLAYBOOK §11 |

---

## 8. Critérios de aceite do vertical (quando for implementar)

Não são tarefas deste documento. São o que a evolução precisa atingir:

1. Pessoa com só `.create` pede CRIAR e ALTERAR em `/apps/my-requests` e acompanha em `/mine`.
2. Sem `.process`, não vê ações de analista (API 403; UI não inventa permissão).
3. Analista vê a fila, inicia, devolve, o solicitante corrige e reenvia, analista finaliza.
4. CRIAR não completa sem `novo_codigo` conferido no TOTVS.
5. Comentários e sino substituem o chat do iframe no fluxo feliz.
6. Pedidos migrados do legado abrem no detalhe nativo com o mesmo `sub`.
7. Iframe some do menu só depois da paridade assinada.

---

## 9. Referências

| Fonte | Papel |
|-------|--------|
| [PLAYBOOK my-requests](../my-requests/PLAYBOOK.md) | Motor, RBAC, plugabilidade |
| [WIREFRAMES my-requests](../my-requests/WIREFRAMES.md) | `/mine`, `/work-queue`, detalhe |
| [MIGRATION-RUNBOOK NF](../my-requests/MIGRATION-RUNBOOK.md) | Molde de ETL |
| [conectar iframe](../../10-guias-operacionais/conectar-aplicacao-iframe.md) | Como o legado está no portal hoje |
| `controle_mp` `docs/ARQUITETURA.md` | Stack Flask/React atual |
| `requests-api` `V007__seed_raw_material_creation_request_type.sql` | Stub a evoluir, não a preservar como produto |


## 10. Adendo de direcionamento — Portal Engenharia / Product Registration (2026-11-06)

> **Status:** `PLANNED`, não implementado. **Plano mestre atualizado:** [Portal Engenharia — ROADMAP.md, adendo Product Registration](../engineering/ROADMAP.md). Este adendo reconcilia a decisão de experiência e **não apaga** a migração nativa anterior ou muda o owner de dados.

O Product Owner direcionou uma **primeira etapa incremental** distinta da proposta das seções 1–8: o **solicitante permanece no Controle MP legado**; o **analista de Engenharia terá uma superfície dedicada no MFE `plugins/engineering`**, apresentada como **Controle e Cadastro de Produtos** (identificadores técnicos em inglês; rótulos pt-BR). A integração inicial será pelo **BFF `engineering-api` → API oficial do Controle MP**, respeitando contratos, identidade/escopo e AuthZ. Não criar acesso do MFE ao Flask, ao seu Postgres ou ao TOTVS diretamente; não recriar workflow na `engineering-api`.

A direção anterior de migrar o workflow integral para `requests-api`/`my-requests` passa a ser **etapa futura sujeita a decisão de cutover e paridade**, não requisito para construir a primeira tela do analista. `requests-api` mantém seu ownership transversal e seu stub `raw-material-creation` **não** será usado como substituto prematuro do fluxo real. Sem dual-write.

**Bloqueios antes de ações:** validar a delegação do usuário de Portal para a API legado, permissão por solicitação/conversa, tokens S2S apropriados, contratos de ação e o owner técnico de aprovação. SSO iframe existente **não** demonstra autorização backend-to-backend. Até esses contratos serem comprovados, apenas leitura autorizada (ou navegação ao legado se leitura também estiver bloqueada), sem simular aprovação. `ARCHITECTURE_DECISION_REQUIRED` para mudança material de authority/consumer e writes.

**Execução paralela:** o agente de VAL-01 trabalha em percepção tabular da `engineering-api`. Esta frente deve usar worktree isolada, reservar paths distintos e serializar alterações em router, auth, bootstrap, manifests, shared modules e deploy sob integrador designado. Nenhuma edição nos módulos OCR/SLANet/drawing/AnalysisJobStore.

**Próximo bounded step:** inventário `PROVEN` de rotas/auth/status da API Controle MP, de router/contratos da Engineering API e do MFE; definir RQ/AC e contrato read-only do novo consumer; implementar somente após gate. Não desativar legado nem migrar dados nesta etapa.


## 11. Nova direção — cadastro técnico nativo e alteração seletiva (2026-11-06)

> **Direção funcional atual do Product Owner — TARGET, não implementação.** Referência de desenvolvimento: [engineering/ROADMAP.md — Native Product Registration](../engineering/ROADMAP.md) e [engineering/IMPLEMENTATION-PLAN.md — PRC-N0–N6](../engineering/IMPLEMENTATION-PLAN.md). O levantamento factual de 51 rotas permanece em [PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md](../engineering/PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md).

**Substitui a estratégia operacional de fase inicial da seção 10 (BFF permanente para API Controle MP):** construir capacidade de cadastro técnico nativa da Engenharia, recebendo solicitações de origens autorizadas mediante contrato de intake; o Controle MP permanece operacional para solicitantes enquanto o novo sistema está sendo construído e até migração/cutover aprovados. Não duplicar workflows corporativos: ownership ante `requests-api` é `ARCHITECTURE_DECISION_REQUIRED`. O catálogo oficial segue pertencendo ao TOTVS/Domain APIs; ficha técnica versionada da Engenharia não se torna cadastro ERP oficial automaticamente.

**Criação (`create`):** dados obrigatórios de solicitação devem incluir somente os requisitos aprovados para intake (ex.: descrição inicial, fornecedores e `compart number` informado pelo PO, com mapeamento a confirmar). A Engenharia completa/valida o registro. Campos de solicitação não equivalem a campos obrigatórios para publicação.

**Alteração (`update`):** solicitante consulta a ficha atual, escolhe somente os campos a alterar e informa valores propostos/justificativa. Pedido guarda `productId`, `baseRevision` e change set com `fieldPath`/antes/depois; **não força o preenchimento de toda a ficha**, e uma mudança aprovada preserva todos os campos não escolhidos. Aplicar CAS/controle de concorrência.

**Histórico:** ficha técnica variável em JSONB versionado, snapshot imutável por revisão + diferenças por campo com autoria, origem, momento, motivo, evidência e aceite. Rejeições não alteram a revisão vigente; nenhum `completed` falso sem confirmação oficial necessária.

**Atendimento:** fila e detalhe de análise no Portal Engenharia, sem replicar o chat legado; EVA auxilia na descrição e validação, `DRAFT/CANDIDATE` até decisão de analista autorizado. A busca de semelhantes e sugestão automática para o solicitante são **FUTURE** e ficam fora do MVP.

**Dados legados:** preservar dados e anexos via migração validada (dry-run, IDs de origem, Keycloak `sub`, checagem de contagens e hashes, cutover controlado, retenção e rollback). Não acessar DB legado em runtime, não fazer dual-write perpétuo, não desligar o app anterior antes do aceite funcional.

**Execução paralela:** esta frente não altera OCR, SLANet, drawing/comparator/AnalysisJobStore da VAL-01; merges em `engineering-api` bootstrap, router/manifest do Portal, auth e deploy devem ser serializados e testados no SHA integrado.


## 12. Direcionamento Engineering-only / portas de entrada e saída (2026-11-06)

> **Atualização de precedência:** o Product Owner definiu que o MVP de Controle e Cadastro de Produtos será construído nativamente **na Engineering API**, sem integração runtime com `requests-api`, `my-requests` ou API Flask Controle MP. Os planos anteriores de BFF/integração imediata são histórico, não backlog vigente. Ver [engineering/ROADMAP.md](../engineering/ROADMAP.md) e [engineering/IMPLEMENTATION-PLAN.md](../engineering/IMPLEMENTATION-PLAN.md).

**Escopo atual:** Engenharia recebe solicitações autorizadas por uma porta de intake versionada, processa fila/validação e registra casos/ficha técnica com JSONB versionado, diffs por campo e auditoria; uma porta de saída expõe resultado/alterações somente para consumidores autorizados sob contrato. `create` usa mínimos de solicitação; `update` especifica somente mudanças selecionadas + `baseRevision`. EVA sugere, não aprova. TOTVS continua autoridade de cadastro oficial.

**Futuro separado:** conectar `requests-api`, migrar cadastros e histórico do legado com ETL governado e cutover, permitir novas categorias e pesquisa de semelhantes. O Controle MP atual permanece operacional até substituição aprovada. Mudança de ownership do workflow requer `ARCHITECTURE_DECISION_REQUIRED`; não confundir aprovação do plano com aprovação de publicação ou escrita ERP. Nenhuma alteração produtiva nesta etapa.


## 13. Contrato de verificação TOTVS e Part Number (2026-11-06)

> **Direção mais recente do Product Owner; TARGET, não implementada.** A Engenharia constrói fluxo nativo isolado, sem BFF runtime com Controle MP e sem integração `requests-api` no MVP. A aplicação Controle MP é referência de paridade e fonte de migração futura, não fonte operacional da primeira etapa.

O analista atende a solicitação no Portal, **faz o cadastro/alteração manual no TOTVS** e só conclui na Engenharia após operação de verificação pela API de leitura oficial. Em `create`, exigir código oficial encontrado **e** atributos necessários correspondentes; em `update`, verificar **os campos efetivamente alterados** e não apenas existência do produto. Falha, divergência, timeout ou campo sem leitura oficial verificável → manter aberto e informar ao usuário, sem publicar revisão como vigente. Nenhum write ao ERP nesta etapa.

**Nome correto:** **Part Number**, campo `part_number` por fornecedor, relacionado no inventário a `A5_CODPRF` (SA5); `catalog_number` é campo distinto (`A5_CODPRCA`). Preservar o catálogo de 11 tags mapeadas no legado; a obrigatoriedade de front legado deve ser formalizada no backend nativo, distinguindo solicitação, análise e publicação. Novas entradas chegam por porta versionada da `engineering-api`; saída retorna estado/resultado/revisão aos consumidores autorizados; harness autenticado de teste permitido, sem integração externa imediata.

**Consulta oficial:** o fato de o legado consultar SQL SB1/SA5 não prova que `api-delpi` exponha os mesmos campos. Verificar os contratos autorizados e ampliar no owner de dados se necessário; não criar SQL paralelo na `engineering-api`. Ver [engineering/ROADMAP.md](../engineering/ROADMAP.md) e [engineering/IMPLEMENTATION-PLAN.md](../engineering/IMPLEMENTATION-PLAN.md).

A migração do banco legado e integrações futuras permanecem fora do MVP.

## PRC-REF-023 — Convergência da entrada de MP em Minhas Solicitações com o PRC da Engenharia (PO 2026-11-10)

**\`PO_APPROVED_FUNCTIONAL_TARGET / PLANNED / ARCHITECTURE_DECISION_REQUIRED\` para integração entre bounded contexts.** O formulário atual em \`/apps/my-requests/new?type=raw-material-creation\` é o schema-driven \`SchemaFormPage\` com conjunto reduzido de campos, entregue por \`requests-api\`, e dispõe de estágio de anexos. O PO determina que o fluxo de criação/alteração de produtos/matérias-primas utilize **a mesma ficha técnica completa e regras** do Portal Engenharia, acrescida de documento de apoio **opcional** (PDF/datasheet/imagem) nos dois pontos de entrada. O trabalho começará pela Engineering API, não por refatorar a página de My Requests.

**Fases:** 1. Engineering API define storage oficial/seguro e expõe contratos PRC de anexos por caso (upload/list/download, autoria, segurança, scan, limites, retenção, proteção de órfãos e autorizacao); 2. Portal Engenharia adiciona upload opcional CREATE/UPDATE e leitura de documentos no detalhe; 3. Minhas Solicitações substitui o stub simplificado por uma experiência com **paridade de schema/controls** do PRC para CREATE/UPDATE e integração autorizada à Engineering API; 4. \`/mine\`/devoluções/correções passam a acompanhar o mesmo caso da Engenharia por uma projeção/consumer contract versionado, com identidades, status e permissão coerentes.

**Boundary atual a resolver:** documentos históricos deste diretório atribuem workflow MP ao \`requests-api\` e tratamento a \`my-requests\`; o PRC mais recente foi implementado com a Engineering API como owner de seu caso. **Não estabelecer dual-write nem mover owner por interpretação de documentação.** Antes de ligar superfícies, Coordination + owners Engenharia/My Requests/Requests API/Core devem aprovar authority do caso, mapping de tipo \`raw-material-creation\` e UPDATE, source ids, histórico stub legado, ACL requester (sem \`engineering.access\`) e responsabilidade pelo upload. A Engineering API não importará domínio/repository/storage de \`requests-api\`; My Requests não reimplementará o comparador TOTVS nem terá acesso direto ao banco Engineering. Em caso de não aprovação, manter as duas superfícies isoladas e registrar blocker real, sem sincronização fake.

**Gates:** schema/catálogo coerente CREATE/UPDATE; Part Number obrigatório e catálogo opcional; fornecedor por pesquisa oficial; arquivo opcional sem bypass de validação de produto; anexos não são fonte oficial para concluir; AuthZ por objeto e download; REF-022 devolução/reenvio por campo; 0 arquivo permitido; falhas de upload claras; testes negativos 401/403/413/415, dedup/retry/scan, Playwright autenticado nas duas superfícies, DEV somente. \`PENDING_ATTACHMENTS_CONTRACT\` e \`ARCHITECTURE_DECISION_REQUIRED\` até owner decidir.

## PRC-REF-023-F02/F03/F04 — Plano de integração real da entrada e do retorno em Minhas Solicitações (PO 2026-11-10)

**\`PO_APPROVED_TARGET / PLANNED\`; \`ARCHITECTURE_DECISION_REQUIRED\` para o cutover entre Engineering API/Requests API/My Requests/Core.** O PO validou a experiência de anexos do PRC em CREATE e definiu Minhas Solicitações como porta de entrada e acompanhamento para usuário comum; Portal Engenharia é o local do atendimento analista. Ambos devem trabalhar com **um único request PRC da Engineering API**, sem duplicação ou alteração de owner por import/integrador informal.

**F02 — Engenharia primeiro:** evidenciar documentos na criação e solicitação de alteração, com miniaturas/previews/download no detalhe em atendimento; usar \`FileDropzone\`, \`AttachmentPreviewStrip\`, \`FilePreviewModal\` do \`@delpi/plugin-ui\`, sem segundo widget. Consulta de anexos de caso devolvido permitida somente quando AuthZ do objeto autorizar; novo upload durante correção é política pendente. Não implementar AV nesta fase; manter validações estruturais e limitação de segurança registrada para decisão do owner.

**F03 — Formulário equivalente em My Requests:** substituir a página schema-driven simplificada de \`raw-material-creation\` e alinhar a criação/alteração de produtos às seções e validações PRC: campos técnicos canônicos, opções oficiais, fornecedores pesquisáveis code+store, Part Number obrigatório/Catálogo opcional, documento opcional, mesmo create/read/edit. Não copiar/recriar a lógica de PRC no requests-api. Definir compartilhamento neutro do catálogo/controles ou adapter versionado oficial antes do código; a UI é consumer da Engineering API, não sua authority.

**F04 — End-to-end do mesmo chamado:** usuário comum autenticado em My Requests cria caso na Engineering API; vê no \`/mine\` status/anexos e quando devolvido corrige campos indicados e reenvia; analista vê o mesmo caso na fila Engineering, consulta anexos e conclui somente com verificação fresca TOTVS. Projeção/identidade do caso, tipo \`raw-material-creation\` / UPDATE, mapeamento legado, links, idempotência e ownership de \`requests-api\` devem ter contrato ratificado por Coordination e owners. Autorização de usuário sem \`engineering.access\` requer live Core permission + object AuthZ Engineering, não bypass JWT/frontend.

**Gates para F03/F04:** aprovação explícita ownership/consumer + Core permission; schemas e validações equivalentes nas duas entradas; sem dual-write; histórico requests-api preservado; testes de dois usuários, acesso negado a terceiros, uploads/downloads privados, devolução por campo, reenvio, REF-020 fail-closed, persistência real e E2E autenticado, DEV somente. Se approval não ocorrer, documentar \`PENDING_OWNER\` e continuar F02/partes neutras sem publicar tela funcional falsa em My Requests.

## PRC-REF-023-OWNER-CLARIFICATION — My Requests é entrada do usuário comum (PO 2026-11-10)

**Decisão do PO:** o mesmo owner responde pelas frentes Engenharia, Minhas Solicitações, Core e APIs. **Não exigir novo role ou circuito funcional de autorização para operar o fluxo básico.** Usuário comum usa **os acessos que já possui em Minhas Solicitações** para criar/alterar matéria-prima/produto, acompanhar o chamado, consultar seus documentos e, quando devolvido, corrigir os campos selecionados e reenviar. **Somente quem tem \`engineering.access\` atende pelo Portal Engenharia**, incluindo início de atendimento, edição técnica operacional, devolução, rejeição e conclusão oficial.

**Um caso só:** a Engineering API registra e governa a solicitação PRC; My Requests fornece a experiência de entrada/consulta/correção sem segundo workflow no requests-api. O formulário segue catálogo e componentes canônicos do PRC em CREATE/UPDATE, fornecedores por busca oficial, Part Number obrigatório, Catálogo opcional, documentos opcionais com previews. Status: Enviada → Em atendimento ⇄ Devolvida para correção → Concluída (+ Rejeitada). Engenharia relê o TOTVS e bloqueia conclusão com qualquer problema.

**Contrato técnico mínimo:** identificar exatamente as permissões **já existentes** de My Requests e seus middleware/claims; mapear para endpoints específicos de solicitante na Engineering API, com live backend AuthZ por objeto, campo e estado. Manter o gate \`engineering.access\` para endpoints de analista e jamais concedê-lo ao requester para contornar bloqueios. Preservar cases históricos de requests-api e acesso isolado de terceiros, sem dual-write ou SQL cruzado. A decisão funcional de ownership está dada; alterações técnicas reais de authority/BC continuam sujeitas aos controles normais. F02/F03/F04 seguem \`PLANNED\` até implementação, testes com duas identidades e DEV validado.

## PRC-REF-023-F02/F03/F04 — Execução: um único caso PRC nas duas superfícies (2026-11)

**Status: `IMPLEMENTED` (DEV a validar em runtime).**

- **F02 — Anexos consolidados.** Identidade local estável por arquivo (`PrcSupportFile.localId`) substituiu índices de array em `plugins/engineering` — seleção, prévia, remoção, upload, falha e retry não desviam mais o arquivo errado. O `requestId` criado é preservado entre tentativas; apenas arquivos não confirmados são reenviados. Validação server-side (magic bytes, limites, SHA-256, storage privado) permanece autoridade. Os helpers puros vivem em `plugins/plugin-ui/src/utils/prcProductRegistration.ts` e são consumidos pelos dois MFEs.
- **F03 — Formulário completo em Minhas Solicitações.** `raw-material-creation` em `/apps/my-requests/new` agora abre `PrcRequestPage` (ficha completa, CREATE/UPDATE, edit-context TOTVS, catálogos oficiais, fornecedores SA2 com Part Number obrigatório e Catálogo opcional, justificativas, documentos opcionais). O intake vai direto à Engineering API (`source: "my-requests"`); nenhum chamado paralelo é criado no requests-api. Histórico legado do requests-api preservado.
- **F04 — Acompanhamento e correção do solicitante.** Nova rota `/apps/my-requests/prc/{requestId}` mostra status, histórico, documentos privados e a devolução REF-022; o solicitante edita apenas os campos devolvidos e reenvia o mesmo caso (save + resubmit com versão e idempotência). `/mine` lista os casos PRC próprios. Backend: permissões já existentes `my-requests.access`/`my-requests.raw-material-creation.create` (nenhum papel novo) nas superfícies do requester, com `_scope_check` por objeto (`requester_subject`) preservado; operações de analista seguem gated por `engineering.access`/`engineering.manager`. api-delpi ganhou `PRC_READ_ACCESS` apenas nas leituras de produto/catálogo/fornecedor exigidas pelo fluxo (TOTVS read-only; nenhum write automático).
- **Nota de build:** o transform do `@originjs/vite-plugin-federation` exige **um único `import` por módulo remoto por arquivo** — múltiplos `import`/`export ... from "@delpi/plugin-ui/index"` no mesmo arquivo geram declarações duplicadas no bundle. Shims locais devem usar um único `import` + `export` de bindings locais.


---

## PRC-TOTVS-AUTOMATION-AND-NORMATIVE-SIMILARITY — Direção vigente 18/11/2026

**TASK_ID de planejamento:** `PRC-TOTVS-AUTOMATION-NORMATIVE-SIMILARITY-MASTER-PLAN-01`  
**Estado:** `PO_DIRECTION_RECORDED / TARGET / CONTRACT_INVENTORY_REQUIRED / IMPLEMENTATION_NOT_AUTHORIZED / NO_TOTVS_WRITE_EXECUTED_BY_THIS_PLAN`  
**Data de decisão:** 18/11/2026  
**Produto/owner de negócio:** Portal Engenharia / Engenharia (PRC). **Engineering API** é owner do caso e das regras do fluxo; **api-delpi** é owner de integração REST/ERP; **TOTVS** é fonte de verdade de produto/fornecedor; **Keycloak/Core** fornecem identidade/RBAC; **EVA** interpreta, compara e recomenda sem aprovar ou publicar; **Plugin UI** e MFEs compõem a experiência.  
**Recurso documental principal para continuar esta trilha:** este capítulo de `docs/12-roadmap-e-evolucao/controle-mp/EVOLUCAO.md`. Acrescentar decisões e evidências **aqui** nas próximas rodadas; não criar sucessivos master plans concorrentes. Referenciar normas/contratos já existentes, sem copiá-los.

### 1. Precedência, escopo e mudança de contexto

As seções históricas acima (setembro/2026) representam migração do antigo iframe/Request Engine e devem ser lidas como **baseline histórica**, não como instrução vigente de criar um novo fluxo `requests-api` para matéria-prima. O PRC operacional atual possui **uma solicitação de Engenharia governada pela Engineering API**, consumida tanto pelo Portal Engenharia quanto por Minhas Solicitações. Não criar segunda autoridade, clone de pedidos, segundo cadastro mestre nem importações cruzadas entre bounded contexts.

O recorte de conversa/UX foi concluído pelo PO em 18/11/2026; evidências, SHAs e resíduos estão em [fechamento consolidado PRC](../engineering/PRC-CONVERSATION-UX-PRODUCTION-CLOSURE-2026-11-18.md). Este capítulo é uma **nova evolução**, e não reabre esse aceite.

A regra antiga que descrevia **cadastro/alteração manual no TOTVS, seguido de verificação** permanece descritiva do fluxo anterior. O alvo agora é permitir execução **assistida e automatizada via API**, com confirmação explícita do analista autorizado. A política histórica `TOTVS_WRITE_TEST_FORBIDDEN` em [plano canônico PRC-TRACK](../engineering/PRC-TRACK-CANONICAL-PRODUCT-RULES-AND-EXECUTION-PLAN.md) permanece válida para testes comuns do PRC e **não é revogada genericamente** por esta decisão de planejamento. Qualquer ensaio de write em **TST01** requer aprovação técnica/operacional delimitada, massa segura, snapshot/restore, pin de ambiente e evidências; **nenhuma escrita produtiva está autorizada por este documento**.

**Escopo inicialmente proposto:** CREATE e UPDATE de cadastro de produto (SB1), operações de vínculo fornecedor/produto (SA5) a inventariar, pré-análise de possíveis duplicidades com normas técnicas DELPI, read-after-write oficial e conclusão do PRC somente após verificação. DELETE de produto não faz parte da automação proposta.

### 2. Inventário de capacidades já existentes (e lacunas)

| Capacidade | Evidência / fonte no repositório | Classificação |
|---|---|---|
| PRC intake, atendimento, revisão e conclusão por verificação oficial | `engineering-api/.../product_registration/service.py`: `complete_attendance`/`verify_and_complete` | `PROVEN_CODE`; manter como única autoridade de conclusão |
| Consulta produtos/fornecedores e lookup de Part Number | `api-delpi` e [evidência de similaridade DAVI](../../../../api-delpi/docs/integrations/evidence/davi-product-detail-similarity-001.md) | `PROVEN_CODE/CONTRACT` na superfície existente; autorização do consumidor PRC a validar |
| Escrita produto UPDATE | `PUT /integrations/protheus/products/{product_code}` no `protheus_router.py`; [playbook](../../../../api-delpi/docs/integrations/protheus-write-integration-playbook.md) | `PROVEN_CODE`; ensaio TST01 17/11 documentado; **não integrado ainda ao PRC** |
| Representação completa da ficha UPDATE | `delpiproduto` lê todos os campos B1 no `DLP04I01.PRW`; façade exige 21 campos + código do path | `PROVEN_DOCUMENTED`; PUT parcial pode zerar campos/gerar falha |
| Produto CREATE | Upstream `delpiproduto/v1/IncProduto/incluir` documentado, sujeito à conferência do handler publicado | `TO_INVENTORY` para contrato e operação live; façade `POST` api-delpi **não localizada** em inspeção 18/11 |
| Fornecedor e vínculos SA5 | Lookup SA2 e consulta/edição proposta de vínculos no PRC | `TO_INVENTORY` para existência de **write** SA5 autorizado (ADD/UPDATE/REMOVE); **não** confundir com PUT de SB1 |
| Normas técnicas MP | [normas governadas](../../../../api-delpi/docs/api/padroes-totvs/normas-tecnicas-descricao-materias-primas.md) (knowledge freeze-002) | `PROVEN_DOCUMENT` como orientação normativa, não truth de produto |
| Avaliação normativa de descrição | `engineering-api/engineering_app/application/drawing/normative_description.py` (`normative_description.v1`) | `PROVEN_CODE` para avaliação de uma descrição; reuso no PRC condicionado a contrato/owner e testes |
| Composição de similaridade READ | DAVI `search_products` + detalhe + PN + fornecedores + conhecimento técnico | `PROVEN_DOCUMENTED` como referência de reuso; **não** criar dependência runtime no agente DAVI/Chat legado |
| Confirmação pós-escrita | PUT atual retorna `ACKNOWLEDGED`, `persistence_proven=false` | `GAP`: read-after-write e reconciliação autoritativa no fluxo |
| Automatização PRC → ERP | Fluxo PREPARE/ACT e composição de operações | `TARGET`, não declarar deploy |

**Regra de inventário:** contrato e código atuais vencem este quadro quando divergirem; manter `PROVEN`, `TO_INVENTORY`, `TARGET` e teste `PASS/INCONCLUSIVE/TEST_NOT_RUN` separados. Revalidar `HEAD`, `origin/main` e serviço real antes de implementação.

### 3. Jornada alvo do analista no Portal Engenharia

1. **Receber/analisar PRC:** CREATE ou UPDATE, ficha técnica, grupo, descrição, fornecedores e PN, documentos, bandeiras e justificativas, com dados permitidos ao ator.
2. **Analisar correspondências técnicas antes de CREATE:** identificar família, aplicar norma DELPI versionada, extrair atributos conhecidos, buscar candidatos oficiais semelhantes, obter fichas SB1 e vínculos SA5/PN, explicar convergências e diferenças; não exigir correspondência textual exata.
3. **Decisão do analista:** `UTILIZAR_EXISTENTE`, `DEVOLVER_PARA_CORRECAO` (ação governada já existente) ou `PROSSEGUIR_NOVO_CADASTRO` com justificativa; nenhum agente decide sozinho. Reuso de existente exige caminho de negócio explicitamente aprovado (não trocar silenciosamente código ou encerrar sem verificação).
4. **Preparar aplicação no TOTVS:** somente no backend, materializar operação permitida, payload, valores originais, diferenças, identidade do objeto/caso/versão, snapshot oficial, fingerprint, risco e resultado de similaridade. Mostrar ao analista `Antes → Solicitado`, fornecedores e operações; prevenir lost update.
5. **Confirmar autorização:** interação explícita por usuário com permissão live de escrita, ligada a proposta expiráveis/versão/caso, sem confiar em JWT/frontend como authority e sem usar identidade de outro ator. Revalidar semelhanças/cadastro antes de ACT.
6. **Executar escrita governada:** Engineering API invoca a capacidade api-delpi autorizada; api-delpi resolve Core identity, destino pinado, gate, ledger pré-envio; Protheus executa rotina oficial via REST/`MSExecAuto`. **Sem SQL de escrita nem retry automático**.
7. **Confirmar persistência:** ler novamente produto e vínculos pelo contrato oficial, confrontar os campos pretendidos; só evidência de `CONFIRMED` e validação PRC atual permite publicar revisão e concluir. `ACKNOWLEDGED` sozinho não basta.
8. **Tratar falha/indeterminação:** `REJECTED`, `UNKNOWN`, divergência, concorrência ou confirmação parcial deixam solicitação aberta para reconciliação/suporte, sem segunda tentativa cega e sem falsa conclusão.
9. **Auditar/acompanhar:** correlacionar `request_id`, `operation_id`, `actor_subject`, `protheus_user_id`, versão do caso, timestamp, origem normativa, candidatos comparados, justificativa, payload hash, ACK/CONFIRM e revisão publicada. Não registrar tokens/secrets.

O botão de **Concluir atendimento** não deve disparar write implícito. Exibir etapa distinta **Aplicar no TOTVS** (PREPARE → confirmação → ACT → read-back), seguida da conclusão já governada.

### 4. Similaridade normativa — objetivo e escopo

**Decisão PO (18/11/2026):** não basta igualdade da descrição. Uma descrição escrita com abreviações, sequências distintas ou unidades diferentes pode denotar produto próximo. O motor deve aplicar **a norma ratificada da família técnica** e explicar se um produto semelhante já existe. A finalidade é apoiar organização do cadastro, não bloquear automaticamente a análise.

**Pipeline candidato (contrato a ratificar):**

`PRC descrição + dados técnicos + fornecedores/PN` → `norma aprovada por grupo/subtipo + extração/normalização determinística` → `busca limitada por descrição parcial, atributos, grupo e PN` → `detalhe oficial por candidato` → `vínculos de fornecedores` → `comparação explicável pela EVA` → `decisão humana auditada`.

Separar com clareza:
- **Correspondência textual** (descrição normalizada, termos/abreviações) ≠ **correspondência técnica** (atributos normativos) ≠ **correspondência de fornecedor/Part Number**.
- **Grupo 1008 — terminais:** subtipo (PINO, FORQUILHA, ILHÓS/TUBULAR, LINGUETA, FASTON/BANDEIRA, OLHAL/ANZOL, LUVA/EMENDA, outros conforme norma), bitola/faixa do cabo (mm²/AWG), dimensão ou comprimento quando previsto, banho, isolação, variante, embalagem e norma/certificação. Não inferir equivalência quando bitola, geometria ou características críticas divergem.
- **Grupos 1001–1005 — cabos:** material, temperatura, seção (mm²/AWG), cor, tensão, observações e certificações; **1006–1007**: vias, bitola, composição, cores, modelo e plug/comprimento aplicável. Subgrupos adicionais somente pelo documento governado.
- **Dados ausentes:** valor `UNKNOWN/NOT_OBSERVED` e motivo, nunca completar por adivinhação.
- **Fontes:** norma com nome/versão/hash + código/grupo/descrição TOTVS e vínculo fornecedor/PN observados, timestamps; conteúdo externo/datasheet tratado como evidência não confiável até verificação.
- **Resultado:** `POSSIBLE_DUPLICATE`, `POSSIBLE_TECHNICAL_SIMILARITY`, `TECHNICAL_MISMATCH`, `INSUFFICIENT_INFORMATION`, `NO_CANDIDATES_FOUND`. A última classe significa somente “consulta autorizada não retornou candidatos”, **não prova inexistência**.
- **Sem score artificial:** percentuais só com método validado, dataset de referência e limiares aprovados por Engenharia. Preferir matriz `atributo / solicitado / candidato / estado / fonte` e ranking explicável.
- **Consulta restrita:** busca paginada/bounded, AuthZ por ator, campos autorizados somente, sem dump do ERP, índice paralelo ou novo banco vetorial como premissa.
- **Fornecedores/PN:** PN deve ser correlacionado com identidade de fornecedor e loja. Mesmo PN isolado não prova equivalência técnica; PN divergente também não dispensa investigação.

**Decisão de continuidade:** o analista pode prosseguir apesar de candidatos com descrição/técnica próxima, **mediante justificativa e permissão correta**. Isso não dispensa gates de conformidade, conflito real de chave, classificação/atributos obrigatórios ou eventual recusa do próprio ERP. É uma decisão de negócio rastreável, não bypass de validações.

### 5. Contratos e fronteiras a definir antes de codar

**A. Análise de similaridade (READ):** owner da regra, consumers (`Engineering API`, Portal, EVA), entrada autorizada `request_id`/versão/família/contexto, resposta `candidates[]` limitada e explicável com `code, description, group, attributes, supplier_links, part_numbers, evidence, missing_fields, norm_ref/version, comparison_status`; limites de paginação, erros e `not_found/forbidden/unavailable` distintos. Reutilizar `normative_description.v1` **via extração de componente neutro ou porta apropriada se justificado pelo Abstraction Gate**; não importar internals de desenho ou do DAVI.

**B. Decisão humana:** ator, request/case version, candidatos e snapshot analisados, `decision`, `reason` obrigatório para prosseguir com duplicidade possível, resultado auditado imutável e validade contra mudança de contexto; operação não terminal até verificação do ERP.

**C. CREATE SB1:** inventariar `delpiproduto/v1/IncProduto/incluir` e/ou API nativa via `/restall`, fonte `.PRW` e payload `MSExecAuto`, código/geração, representação completa, campos obrigatórios, erros, permissões, idem e reconciliação. Se não existir façade oficial, propor `POST` **somente** na api-delpi com gate default OFF e destination pin. Não afirmar que o contrato de UPDATE vale para CREATE.

**D. UPDATE SB1:** reutilizar `PUT /integrations/protheus/products/{product_code}`; fazer read fresco e representação completa dos campos exigidos (21 `B1_*` + código path no contrato documentado), preservando campos não alterados; tratar `null`, divergência de baseline e concorrência fail-closed; não admitir PATCH parcial que zera campos.

**E. Vínculos SA5:** inventariar ADD/UPDATE/REMOVE e existência de API oficial; cada operação exige identidade fornecedor/loja e Part Number/ catálogo adequados. Se write SA5 não existir, **não** marcar caso com operações SA5 como completamente aplicado. Avaliar falha parcial entre SB1 e SA5, compensação autorizada ou reconciliação manual; não pressupor transação distribuída.

**F. PREPARE/ACT e AuthN/AuthZ:** contrato com expiração, idempotency key por intenção, binding `actor+case+version+official_snapshot+payload_hash+decision`, scopes/permissões live Core, conta Protheus resolvida no backend, S2S restrito `engineering-api`, erros `FORBIDDEN, STALE, CONFLICT, REJECTED, UNKNOWN, UNAVAILABLE`, observabilidade e postconditions. MCP/A2A é meio de interoperabilidade, **nunca autoridade**.

**G. Read-back/reconciliação:** `ACKNOWLEDGED` = REST aceitou; `CONFIRMED` = leitura oficial compatível por operação e atributos; `UNKNOWN` exige investigação antes de retentar. Não concluir nem publicar V1/Vn+1 sem aplicação confirmada e validação já existente do PRC. Eventos de tracker e case devem ser correlacionáveis sem dual-write transacional fictício.

### 6. Pacotes de execução e gates

| Fase | Entrega | Critério de saída | Estado |
|---|---|---|---|
| G0 — Inventário | HEAD/status, owners, contratos/schemas atuais, endpoints REST reais, arquivos ADVPL, normas e testes, matriz SB1/SA5, capability de busca normativa | Matriz `PROVEN/TO_INVENTORY`, riscos e delta por sistema | `PLANNED` |
| G1 — Ratificação | RQ/AC; semântica de duplicidade e decisão; CREATE/UPDATE/SA5; auth; PREPARE/ACT; postconditions e failure modes | Owners Engenharia/API DELPI/Coordination aprovam contratos e baseline | `PLANNED` |
| G2 — Similaridade READ | Pipeline por família, candidatas bounded, confronto técnico/PN, resposta explicável, auditoria da decisão | Evals com duplicatas verdadeiras/falsos positivos, bitola, PN, ausência, autorização | `PLANNED` |
| G3 — CREATE na api-delpi | Capacidade nova somente se não houver equivalente; gate OFF, pin, ExecAuto, ledger | Testes de contrato e POC controlada **TST01**, se autorizada | `PLANNED` |
| G4 — UPDATE/SB1 e SA5 | Reuso de PUT e implementação governada de SA5 apenas com contrato; idempotência e rebase | Testes de payload completo, partial failure, UNKNOWN e concorrência | `PLANNED` |
| G5 — PRC aplicação | PREPARE/ACT Engine API, decisão vinculada, read-back e complete existente | Testes fail-closed, guards, revisão/versão e idempotência | `PLANNED` |
| G6 — Portal/EVA | UI `Analisar duplicidade` → `Aplicar no TOTVS` → `Confirmar`; ações semânticas elegíveis nas **seis tools existentes** | A11y, estados, mensagens, paridade usuário e permission boundaries | `PLANNED` |
| G7 — HML/TST01 | E2E autorizado sem tocar produção, snapshots e restauração, comparação de dados e negative cases | RQ/AC, evidências SHA e técnico owner; bloqueios resolvidos | `PLANNED` |
| G8 — Release | Planejamento de produção, feature gates inicialmente OFF, rollout/rollback/revoke, monitoramento | Aprovação específica de deploy e de **habilitação de write**; smoke seguro | `PLANNED / NOT_AUTHORIZED` |

**Sequência não é licença para implementar todas as fases de uma só vez.** G0 é `READ_ONLY / NO_DEPLOY`; mudança de owner, authority, contrato externo breaking ou novo bounded context: `ARCHITECTURE_DECISION_REQUIRED` e retorno à Coordination. Não executar G3+ ou habilitar gate sem autorização de fase.

### 7. Critérios de aceite iniciais (evolutivos)

| AC | Evidência exigida |
|---|---|
| AC-01 | Busca aproximada retorna candidatos tecnicamente próximos, não apenas descrição exata |
| AC-02 | Terminais 1008: subtipo/bitola/dimensões/banho/isolação comparados segundo norma aplicável |
| AC-03 | Cabos: material/bitola/vias/tensão/temperatura/cor quando aplicáveis |
| AC-04 | Dados oficiais e SA5/PN exibidos somente quando autorizados, com proveniência e ausências |
| AC-05 | PN de fornecedor igual não é confundido com equivalência técnica automática |
| AC-06 | Analista decide usar existente, devolver ou prosseguir com motivo auditável; sem bloqueio arbitrário por similaridade |
| AC-07 | Revalidação de candidatos/contexto e AuthZ antes do ACT; proposta expirada/conflitada falha fechada |
| AC-08 | CREATE não usa contrato PUT por suposição; upstream, ExecAuto e código oficial comprovados |
| AC-09 | UPDATE preserva representação completa e valores não modificados, impedindo lost update |
| AC-10 | Operações SA5 só declaradas aplicadas com contrato e confirmação oficial; falha parcial não conclui |
| AC-11 | ACK e CONFIRMED distintos; timeout/5xx UNKNOWN sem retry cego |
| AC-12 | Caso PRC somente fecha/publica revisão após read-back e verificação oficial íntegra |
| AC-13 | Permissões live Core, pin TST01/PRD, feature gates OFF default, ledger e idempotência testados |
| AC-14 | UI e EVA usam mesmos casos de uso governados; sem novas tools ou acesso direto ao ERP |
| AC-15 | Cenários positivos e negativos executados no SHA e ambiente autorizados; nenhuma escrita PRD de teste |
| AC-16 | O documento evolutivo é atualizado incrementalmente com decisões, ADRs, hashes, resultados e pendências, sem master plans duplicados |

### 8. Matriz de cenários de teste a construir

1. Terminais com mesma bitola e texto abreviado diferente → candidato e atributos explicáveis.
2. Terminal bitola diferente → `TECHNICAL_MISMATCH` no atributo, não declarar duplicidade conclusiva.
3. Mesmo PN + mesmo fornecedor/loja, descrição diferente → recuperar candidato e exigir análise, não equiparar automaticamente.
4. PN idêntico com fornecedores distintos → deixar contexto explícito.
5. Cabo mesma seção mas tensão/material diferente → destacar divergência técnica.
6. Grupo/subtipo fora da norma aplicável → `INSUFFICIENT_INFORMATION` ou `NOT_APPLICABLE`, sem inventar regra.
7. Busca sem candidatos, página parcial, indisponibilidade ou 403 → sem candidato ≠ inexistência; falha de leitura não vira autorização implícita.
8. Analista escolhe prosseguir com justificativa e permissão correta → decisão persistida; sem motivo/sem permissão → bloqueio.
9. Mudança de cadastro/candidato entre análise e PREPARE/ACT → stale/novo review.
10. UPDATE com um campo alterado, demais campos de representação completa preservados.
11. CREATE que recebe ACK mas read-back não confirma → caso aberto, sem revisão publicada.
12. Timeout após envio e possível gravação → UNKNOWN, reconciliação, sem retry automático.
13. SA5 ADD/UPDATE/REMOVE com falha parcial → nenhum falso `complete`; decisão de recuperação governada.
14. Usuário sem permissão e caso de outra identidade → backend nega sem revelar ficha restrita.
15. HML TST01 com snapshot, operação e restore autorizados; PROD read-only, inalterada.

### 9. Registro de decisões e próximos complementos — manter neste capítulo

| Data | Decisão PO / Coordenação | Estado | Próximo complemento |
|---|---|---|---|
| 18/11/2026 | Incorporar criação/edição **assistidas via API** ao fluxo de Engenharia, com decisão humana e confirmação oficial | `PO_DIRECTION_RECORDED` | G0 contratos CREATE/UPDATE/SA5 e segurança |
| 18/11/2026 | Não impedir automaticamente a análise quando há descrição parecida; mostrar cadastro e fornecedores/PN; continuidade justificada por analista | `PO_DIRECTION_RECORDED` | Contrato de decisão e audit trail |
| 18/11/2026 | Similaridade deve ser **aproximada e técnica**, aplicar normas DELPI por família (bitola, cabo, terminais etc.) e reusar inteligência da EVA | `PO_DIRECTION_RECORDED` | G0/G1 norm engine, candidate retrieval e avaliação |
| 18/11/2026 | Concentrar próximos refinamentos no **plano evolutivo já existente**, sem multiplicar master plans | `PO_DIRECTION_RECORDED` | Append-only nesta seção |

**Pendências de decisão ainda abertas (não converter em fato):** owner e lifecycle exato do contrato de análise; campos críticos por família e equivalência admissível; estratégia de código oficial no CREATE; permissões específicas para escritura; API de write SA5; comportamento de `UTILIZAR_EXISTENTE`; transações parciais; expiração da decisão; limites/ranking dos candidatos; disponibilização sem novos scopes. Resolver via inventário e ratificação técnica, sem preencher lacunas por inferência.

**Regra editorial para as próximas rodadas:** acrescentar neste capítulo novas subseções `G0 evidence`, `G1 decisions`, `execution reports`, `residual ledger` com `TASK_ID, SHA, owner, contract_version, environment, PASS/FAIL/PENDING/TEST_NOT_RUN, reversibility`. Atualizar este plano em vez de escrever master plan paralelo; documentação de contrato técnico ratificado pode existir na área do próprio owner e ser referenciada daqui.
