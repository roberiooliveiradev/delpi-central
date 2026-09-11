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
