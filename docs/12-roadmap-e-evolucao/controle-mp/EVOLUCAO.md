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
