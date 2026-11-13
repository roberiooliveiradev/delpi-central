# 165 — TRILHA DE EXECUÇÃO: Migração do Lançamento de Notas Fiscais até a CLARA (F5a → F7)

> **Documento de execução para o Cursor.** Esta é a trilha oficial e única. Siga na ordem, sem pular, sem inventar etapa, sem mudar escopo.
> Local no repositório: `docs/12-roadmap-e-evolucao/controllership-finance/165-trilha-execucao-migracao-lnf-ate-clara.md`
> Criado em: 2026-11-12 · Owner: owner do produto Portal Controladoria & Finanças · Revisor: arquiteto (Claude)
> Autoridades relacionadas: plano **163**, runbook **164**, **ADR-001** (ACCEPTED). Em caso de conflito: ADR-001 > este documento (ordem de execução) > 164 > 163.

---

## PARTE 0 — COMO O CURSOR USA ESTE DOCUMENTO

### 0.1 Prompt de início (colar no Cursor)

```text
Leia por inteiro docs/12-roadmap-e-evolucao/controllership-finance/165-trilha-execucao-migracao-lnf-ate-clara.md
(se ainda não existir no repo, copie-o do arquivo que o owner forneceu, commite e faça push).
Você está PROIBIDO de desviar desta trilha. Execute a partir da primeira fase do QUADRO DE STATUS (Parte 2) que não esteja DONE,
seguindo o PROTOCOLO PADRÃO (Parte 3) e as REGRAS DE PARADA (Parte 4).
Ao final de cada etapa, atualize o QUADRO DE STATUS e o REGISTRO DE EXECUÇÃO (Parte 9) neste mesmo arquivo, commit + push.
Ao parar (fim de fase ou regra de parada), entregue o RELATÓRIO no formato da Parte 8.
```

### 0.2 Autorização do owner (válida para toda a trilha)

O owner **autorizou previamente todos os gates de implementação** desta trilha, nesta ordem:
**implementar → testar em DEV → testar em HML → se HML PASS, promover para PROD → verificar PROD → documentar.**
A autorização vale **somente** para o que está escrito nesta trilha. Qualquer coisa fora dela exige o owner (Parte 4).

### 0.3 Regras permanentes de trabalho

1. **Main, sem branches.** Outros agentes trabalham no mesmo repo. Commits pequenos, **só dos seus arquivos**, `git pull --rebase` antes do push, **nunca** force push, **nunca** stash/reset/checkout de alterações alheias. Se alterações alheias bloquearem o rebase, reporte e aguarde.
2. **Referência de comportamento = api-delpi atual**, congelada no golden da suíte `tests/contracts/lancamento-notas-fiscais/` (28 arquivos). **Nunca** altere golden para "fazer passar". Única divergência aceita: **D8** (token de serviço recusado na BFF).
3. **Nada de "melhorias".** Regra de negócio, SQL, mensagens, validações, permissões e telas ficam como estão.
4. **Segredos** nunca em código, commit, log, relatório ou prompt. Relatórios sem nomes de pessoas, CPF/CNPJ ou dados de fornecedores.
5. **Linguagem de evidência:** PASS | FAIL | INCONCLUSIVE | TEST_NOT_RUN | PENDING_OWNER | NOT_COVERED_BLACKBOX | AS_IS_BEHAVIOR | KNOWN_DIVERGENCE_D8. Teste não executado nunca é PASS.
6. **Problema encontrado dentro da trilha:** corrija → reteste no mesmo ambiente → reteste nos ambientes anteriores → continue. Registre no Registro de Execução (causa, correção, SHA, reteste).
7. **Teste instável:** até 3 reexecuções; se continuar instável, é FAIL.

---

## PARTE 1 — O QUE ESTÁ DECIDIDO (não reabrir)

### 1.1 Objetivo
Transferir o módulo **Lançamento de Notas Fiscais (LNF)** da `api-delpi` para a `controllership-finance-api` (BFF), **sem mudar comportamento**, e depois expor as funcionalidades do app na **CLARA** usando as tools semânticas **já existentes**.

### 1.2 O que NÃO muda (garantia ao usuário)
- **O micro front-end é o MESMO** (`plugins/lancamento-notas-fiscais`). Não se cria MFE novo e não se altera tela, fluxo, componente ou comportamento. **Única mudança permitida: o endereço base da API** (`VITE_LNF_API_BASE`), de `/apps/api-delpi/lancamento-notas-fiscais` para `/apps/controllership-finance-api/lancamento-notas-fiscais`.
- **Permissões continuam as mesmas** `lancamento-notas-fiscais.*`: access, create, view, view.filial-01, view.filial-02, process, manage, review-unmapped-products. Mesma regra de filial. Ninguém ganha nem perde acesso. **Não** se exige `controllership-finance.access` para o app.
- **Dados não se movem**: mesmo schema `lancamento_notas_fiscais` no `postgres-plugins`; a BFF passa a ser a dona. Mesmo volume de DANFE/XML.
- **Notificações** iguais: `sourceApp=lancamento-notas-fiscais`, categorias `lancamento_notas_fiscais` e `lancamento_notas_fiscais_unmapped_products`.
- **Protheus só leitura.** O módulo nunca escreve no ERP.

### 1.3 Decisões (ADR-001)
| # | Decisão |
|---|---|
| D1 | BFF autoriza pelas `lancamento-notas-fiscais.*` (via Core `/me`). Exceção registrada ao freeze "só access/manage". |
| D2 | Transferência de posse do schema, sem mover dados. Runner dedicado lendo o ledger existente; V001–V014 byte a byte. |
| D3 | SQL Protheus do módulo vai junto para a BFF (desvio consciente; duplicação SA2/SC7 como residual). |
| D4 | Corte direto (sem proxy) — rotas antigas saem da api-delpi. |
| D5 | Envelope e erros do módulo idênticos aos da api-delpi (handlers escopados). |
| D6 | BFF chama a financial-api com o mesmo `API_DELPI_INTERNAL_SERVICE_TOKEN` / `X-Delpi-Service-Token` / principal `internal_invoice_reader`. |
| D7 | Regra de filial preservada exatamente (inclusive rotas sem filtro de filial). |
| D8 | Rotas LNF na BFF exigem `principal_type == "user"`; token de serviço → 403. |
| D9 | Chat/TV perdem as operações LNF no corte. **Risco aceito pelo owner** (sem verificação de uso). |

### 1.4 Chaves de corte (default = comportamento atual)
| Chave | Onde | Default | Valor no corte |
|---|---|---|---|
| `LNF_HOSTED_ENABLED` | BFF | `false` | `true` |
| `LNF_MIGRATIONS_MODE` | BFF | `verify` | `verify` (vira `apply` só em F6) |
| `LNF_MODULE_ENABLED` | api-delpi | `true` | `false` |
| `VITE_LNF_API_BASE` | build do MFE | `/apps/api-delpi/lancamento-notas-fiscais` | `/apps/controllership-finance-api/lancamento-notas-fiscais` |

---

## PARTE 2 — QUADRO DE STATUS (o Cursor atualiza a cada etapa)

| Fase | Nome | Status | Ambiente atual | SHA(s) | Data | Evidência |
|---|---|---|---|---|---|---|
| F0–F4b | Inventário, contrato, implementação dark, ensaio HML | DONE | — | até `fddd4bb813` | 2026-11-12 | 163/164, suíte |
| F5a | Preparação dark de PROD | DONE | PROD | `fdc31ad48e` + deploys 2026-11-12 | 2026-11-12 | BFF/MFE/api-delpi dark; preflight 5/5; OpenAPI BFF 112/0 LNF; api 731/22 LNF; MFE base api-delpi; observação 15 min sem incidente |
| F5b | Corte em PROD | técnico PASS; smoke PENDING_OWNER (não bloqueante) | PROD | `630ca6f3b9` + fix PO `e43aa9558b` | 2026-11-13 | Virada: BFF 13,4s / api 15,1s / MFE 56,3s; revisor: 22 paths/24 ops BFF, 0 LNF api-delpi; fallback Vite morto |
| F5c | Estabilização (hypercare) | IN_PROGRESS (dia 1; janela 5 DU a partir do corte) | PROD | — | 2026-11-13 | Checagens: total=1430; 5xx=0; HOSTED=true; recheck pós-F7 OK |
| F7.0 | CLARA — inventário e contrato | DONE | docs | `0926f07160` | 2026-11-13 | doc 166; R2=SIM JWT usuário |
| F7.1 | CLARA — leituras | DONE | HML/PROD | `1328cd0d85` | 2026-11-13 | 8 reads; HML JSON-RPC PASS; PROD health+import |
| F7.2 | CLARA — análise | DONE (F7-R) | HML/PROD | `348140ec53` | 2026-11-13 | enum `invoice_posting_backlog` no tools/list; schema-callable |
| F7.3 | CLARA — ações governadas | DONE (F7-R) | HML/PROD | `348140ec53` | 2026-11-13 | presentation displayable=true; HML prepare→commit E2E |
| F7.4 | CLARA — produção + roteiro de teste do owner | PENDING_OWNER | PROD | `348140ec53` | 2026-11-13 | rework F7-R deployado; revisor refaz pelo conector |
| F6 | Limpeza final (encerra o rollback) | TODO | | | | |

Status possíveis: TODO · IN_PROGRESS · BLOCKED (regra de parada) · DONE.
**Ordem de execução obrigatória:** F5a → F5b → F5c (inicia o período de estabilização) → F7.0 → F7.1 → F7.2 → F7.3 → F7.4 → F6.
F6 é a última porque remove a possibilidade de rollback; só começa depois que F5c terminar **e** F7.4 estiver DONE.

---

## PARTE 3 — PROTOCOLO PADRÃO (vale para toda fase)

```text
P1  REBASELINE      git rev-parse HEAD; git status --short; ler este documento e o Registro de Execução.
P2  PRÉ-CONDIÇÕES   conferir os critérios de entrada da fase. Se algum falhar → Parte 4.
P3  IMPLEMENTAR     mudança mínima descrita na fase. Nada além.
P4  DEV             testes unitários + suíte de contrato (quando aplicável). Tudo PASS.
P5  HML             deploy em HML; mesmos testes; smoke da fase. Tudo PASS.
P6  CONTROLE        antes de PROD: listar commits entre a versão em PROD e o HEAD nas pastas do(s) serviço(s) que vão subir.
                    Commits de outros trabalhos nessas pastas → Parte 4 (parada R4).
P7  PROD            deploy de UM serviço por vez, com linha de base antes e verificação depois.
                    Falha → rollback imediato daquele serviço (Parte 5) → corrigir em DEV/HML → nova tentativa (máx. 1).
P8  VERIFICAR       critérios de saída da fase, com evidência.
P9  DOCUMENTAR      Quadro de Status + Registro de Execução + docs da fase (163/164/ADR quando indicado). Commit + push.
P10 RELATÓRIO       formato da Parte 8.
```

**Horário para PROD:** deploys que reiniciam a `api-delpi` (afeta todos os apps da Minha DELPI) e o corte F5b só fora do horário comercial (antes de 07:00 ou depois de 19:00, horário de Brasília, ou fim de semana), ou com OK explícito do owner no chat.

---

## PARTE 4 — REGRAS DE PARADA (parar, reportar e aguardar o owner)

Parar **imediatamente** (status BLOCKED) se ocorrer qualquer item abaixo. Não contornar.

| ID | Situação |
|---|---|
| R1 | **Dados:** contagem diferente entre antes/depois, ledger divergente, necessidade de DDL/migration nova, qualquer risco de perda ou duplicação de dados. |
| R2 | **Segurança:** qualquer divergência de AuthZ além de D8; rota acessível sem autenticação; usuário ganhando/perdendo acesso; CLARA não usando a identidade do próprio usuário final; necessidade de relaxar D8. |
| R3 | **PROD:** falha que o rollback não resolveu, ou segunda falha na mesma etapa após correção. |
| R4 | **Deploy misturado:** commits de outros trabalhos nas pastas dos serviços que vão para PROD. **Exceção (owner, 2026-11-12):** publicar a `api-delpi` com **todos** os commits pendentes da `main` está autorizado, **somente** com as salvaguardas **F5a.4-API (a→f)** abaixo. A exceção não cobre outros serviços nem dispensa R1/R3/R5/R8. |
| R5 | **Fora da trilha:** necessidade de alterar permissões no Core, tela/fluxo do MFE, outros serviços não listados, persona/ficha da CLARA, ou qualquer arquivo de HML com alterações alheias pendentes. |
| R6 | **Escrita no Protheus** detectada em qualquer código. |
| R7 | Golden precisaria ser alterado (exceto D8) para um teste passar. |
| R8 | Ambiente indisponível que impeça um teste obrigatório da fase (ex.: HML fora do ar) por mais de 1 hora. |

Formato da parada: `BLOCKED R<n> — <fase/etapa> — <o que aconteceu> — <evidência> — <opções> — <recomendação>`.

---

## PARTE 5 — ROLLBACK (sempre disponível até F6)

| Situação | Ação | Tempo ensaiado |
|---|---|---|
| Falha após o corte (F5b/F5c) | 1) api-delpi `LNF_MODULE_ENABLED=true` + restart; 2) MFE rebuild/deploy com `VITE_LNF_API_BASE` default; 3) BFF `LNF_HOSTED_ENABLED=false` + restart; 4) regenerar catálogos chat/TV | ~44 s (HML) |
| Falha num deploy dark (F5a) | Voltar só o serviço afetado para a imagem anterior | — |
| Falha na CLARA (F7) | Voltar a imagem anterior do serviço da CLARA; LNF no app continua funcionando pela BFF | — |

Dados: o schema é o mesmo nas duas pontas e não muda durante a trilha (até F6), portanto o rollback não perde nada do que foi gravado pela BFF.
Gatilhos obrigatórios de rollback em PROD: 5xx nas rotas LNF acima de 1% em 10 min; qualquer 401/403 indevido reportado ou observado; contagem divergente; smoke do owner FAIL; preflight FAIL.

---

## PARTE 6 — FASES

### F5a — Preparação dark de PROD (em execução)
Prompt já entregue: `prompt-cursor-F5a-migracao-lancamento-notas-fiscais.md`. Resumo:
- Passo 0: smoke do MFE em HML pelo navegador (P11, P6, P2; filial-01/02; prova pela aba Network de que tudo vai para a BFF); rollback HML.
- Preflight CLI (`lnf_preflight`): ledger, `SELECT 1` no Protheus, health financial-api/Core, volume gravável.
- Compose/env de PROD com chaves explícitas no default; controle de commits por serviço (R4); deploy dark.
- Docs: runbook 164 + risco D9 aceito no ADR-001.

#### F5a.4 — Deploy dark em PROD (ordem fixa)

**Baseline antes (registrar):** BFF OpenAPI paths (esperado 112, LNF=0); api-delpi LNF paths (esperado 22); string do MFE = `/apps/api-delpi/lancamento-notas-fiscais`; health 200.

1. **BFF dark** — `git pull --ff-only` + `./infra/scripts/up-prod-sequential.sh --build controllership-finance-api`  
   Verificar: health/ready 200; OpenAPI ainda 112 sem LNF; `GET …/lancamento-notas-fiscais/requests` = **404**; rotas de fechamento OK; **preflight PROD 5/5 PASS** (`python -m controllership_finance_app.interface.cli.lnf_preflight` no container).
2. **MFE dark** — `./infra/scripts/up-prod-sequential.sh --build lancamento-notas-fiscais`  
   Verificar: remoteEntry/bundle servindo; string `/apps/api-delpi/lancamento-notas-fiscais` presente; **sem** base da BFF.
3. **F5a.4-API (a→f)** — obrigatório antes/durante o rebuild da `api-delpi` (exceção R4):
   - **(a)** Inventário do pacote PROD→HEAD em `api-delpi/` + **diff de OpenAPI** (paths/operationIds LNF devem permanecer 22 / mesmos IDs; listar paths novos não-LNF).
   - **(b)** **Migrations pendentes** do runner da api-delpi / plugins: nenhuma migration LNF nova; demais schemas — inventariar e **não aplicar** nada fora do fluxo canônico; se DDL arriscada → **R1**.
   - **(c)** **Envs novos** exigidos pelos commits do pacote: nomes presentes em `infra/.env` (sem imprimir valores); faltando → **R5/R8**.
   - **(d)** **Suíte completa** da api-delpi em DEV (ou CI local) — FAIL → não sobe.
   - **(e)** **HML** com `api-delpi` no HEAD: deploy HML + health + smoke LNF (fila/OpenAPI 22 paths) PASS.
   - **(f)** **PROD** `./infra/scripts/up-prod-sequential.sh --build api-delpi` com OK do owner (janela ou autorização explícita); health 200; OpenAPI LNF=22; fila MFE ainda via api-delpi; **observação 15 min** de 5xx / apps quebrados → rollback imediato da imagem anterior se aumentar 5xx ou outro app quebrar.

Qualquer FAIL em (a)–(f) ou nas verificações BFF/MFE → parada R1/R3/R5/R8 (não contornar).

**Saída (DONE quando):** smoke MFE HML PASS; preflight PROD 5/5; BFF/MFE/api-delpi dark em PROD sem mudança para o usuário (BFF 112 sem LNF; api-delpi 22 LNF; bundle MFE com endereço atual); F5a.4-API (a→f) PASS + observação 15 min sem incidente.

---

### F5b — Corte em PROD

**Entrada:** F5a DONE; janela conforme Parte 3; preflight PROD PASS executado no máximo 1 hora antes.

**Passos:**
1. **Linha de base (antes):** contagem por tabela e por status/filial do schema `lancamento_notas_fiscais` (somente leitura); health de BFF/api-delpi; bundle do MFE com o endereço atual.
2. **Virada (nesta ordem, cronometrar):**
   1. BFF: `LNF_HOSTED_ENABLED=true` (`LNF_MIGRATIONS_MODE=verify`) + restart → verify do ledger PASS nos logs.
   2. api-delpi: `LNF_MODULE_ENABLED=false` + restart.
   3. MFE: build + deploy com `VITE_LNF_API_BASE=/apps/controllership-finance-api/lancamento-notas-fiscais`.
   4. Regenerar catálogos: `scripts/homologacao/sync-api-delpi-openapi.sh` (chat) e `sync-api-delpi-openapi-tv.sh` (TV), conforme o procedimento de PROD desses serviços.
3. **Verificação técnica (Cursor, sem token de usuário):**
   - com o token de serviço: `GET /apps/controllership-finance-api/lancamento-notas-fiscais/requests` → **403** (prova que a rota está montada e que D8 está ativo); `GET /apps/api-delpi/lancamento-notas-fiscais/requests` → **404**;
   - OpenAPI da BFF contém as 24 operações LNF com os mesmos operationIds; OpenAPI da api-delpi sem LNF;
   - bundle do MFE contém o endereço da BFF e não contém `/apps/api-delpi/lancamento-notas-fiscais`;
   - contagens iguais às da linha de base;
   - logs da BFF sem 5xx nas rotas LNF.
4. **Smoke do owner (PENDING_OWNER — o Cursor entrega este checklist e aguarda o resultado):** com usuários reais de perfis diferentes:
   - abrir o app nas filiais 01 e 02; fila carrega com os mesmos números de antes;
   - usuário só com filial 01 não vê a filial 02;
   - abrir o detalhe de uma nota; baixar um **DANFE** e um **XML** de documento recebido;
   - criar uma nota real (ou usar uma recebida no dia) e seguir o fluxo normal até onde o processo do dia permitir;
   - comentar com menção e conferir a notificação no sino do destinatário;
   - aba Network: chamadas de negócio indo para `/apps/controllership-finance-api/...`.
   *(O revisor também verifica pelo navegador em paralelo.)*
5. **Docs:** 164 (horários, tempos, resultados), 163 status "CORTE CONCLUÍDO", README.

**Saída (DONE quando):** verificações técnicas PASS + smoke do owner PASS. Qualquer FAIL → rollback (Parte 5) → corrigir em DEV/HML → nova janela.

---

### F5c — Estabilização (hypercare)

**Duração:** 5 dias úteis a partir do corte. Rollback continua disponível.
**Rotina diária (Cursor, somente leitura):** 5xx e 403 nas rotas LNF da BFF; contagem de solicitações por status (crescendo coerente, sem sumiços); notificações LNF emitidas no Core; erros no log da BFF ligados a Protheus/financial-api/storage; reclamações registradas pelo owner.
**Saída (DONE quando):** 5 dias úteis sem gatilho de rollback e sem incidente aberto. Registrar resumo diário no Registro de Execução.
**Em paralelo ao F5c**, executar F7.0 → F7.4 (a CLARA não depende de F6).

---

### F7 — CLARA

**Princípios da F7 (não negociáveis):**
- **Paridade funcional total (decisão do owner):** a CLARA deve executar **tudo o que o usuário consegue fazer no app**, dentro das permissões dele — leitura, análise, **escrita e deleção** — no padrão em que a CLARA já é desenvolvida. Não é uma entrega só de leitura. As 24 operações da API LNF estão cobertas na tabela abaixo: 19 viram entradas de catálogo e 5 são downloads de PDF/XML, entregues como link para a tela existente do app (o usuário baixa por lá).
- **Nenhuma tool nova.** Somente novas entradas `(entity, action)` no catálogo semântico existente (`get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`).
- A CLARA **espelha a BFF**: cada leitura/ação chama a rota LNF da BFF já existente, **com a identidade do usuário final**. A BFF continua sendo a autoridade (CLARA nunca autoriza).
- Visibilidade no catálogo pelas permissões `lancamento-notas-fiscais.*` efetivas do usuário (mesmos conjuntos da BFF). Quem não tem LNF não vê as entradas.
- **Não alterar persona/ficha da CLARA** (R5). Não alterar o MFE.
- PDFs/XML **não** passam pela CLARA: a resposta aponta para a tela existente do app (deep link para rota já existente do MFE).
- Escritas seguem o padrão já existente da CLARA: `prepare → consentimento explícito → commit`, com Core, idempotência e read-back.

#### F7.0 — Inventário e contrato (somente docs)
1. Onde está o código do MCP da CLARA (serviço, pasta, imagem), como monta o catálogo `clara-semantic-v1`, como deriva capacidades das permissões, como chama a BFF (bearer do usuário? token de serviço? cabeçalhos), onde roda em HML (se não rodar, preparar como foi feito com a BFF no F4b, espelhando PROD).
2. **Checagem de identidade (R2):** provar que cada chamada da CLARA à BFF carrega o principal do **usuário final**. Se a CLARA chamar a BFF como serviço, D8 bloqueará — **PARAR (R2)**; não relaxar D8.
3. Escrever `docs/12-roadmap-e-evolucao/controllership-finance/166-clara-lancamento-notas-fiscais-contrato.md` com a tabela do catálogo abaixo (ajustando só nomes técnicos ao padrão real encontrado) e os testes previstos.

**Catálogo alvo:**

| Tool | entity.action | Rota BFF | Visível para | Política |
|---|---|---|---|---|
| read | `invoice_posting.list` | GET `/requests` (filtros: branch, status, supplier, document, issued/received from/to, page) | READ LNF | — |
| read | `invoice_posting.get` | GET `/requests/{id}` | READ LNF | — |
| read | `invoice_posting.purchase_orders` | GET `/requests/{id}/purchase-orders` | READ LNF | — |
| read | `purchase_order.open` | GET `/purchase-orders/open` | create | — |
| read | `received_invoice.list` | GET `/received-invoices` | create | — |
| read | `received_invoice.detail` | GET `/received-invoices/{id}/detail` | create | — |
| read | `unmapped_product.list` | GET `/unmapped-products` | review-unmapped-products | — |
| read | `supplier.search` | GET `/suppliers` | create | — |
| analyze | `invoice_posting_backlog` (wire enum; alias `invoice_posting.backlog`) | composição dos reads | READ LNF | FACT/RECOMMENDATION: pendentes por filial, idade desde o recebimento, bloqueadas por motivo, divergências com o ERP, CT-e sem NF vinculada, notas recebidas sem solicitação; recorte por competência |
| execute | `invoice_posting.comment` | POST `/requests/{id}/comments` | create/process/manage | direct |
| execute | `reconciliation.refresh` | POST `/reconciliation/refresh` | READ LNF | direct |
| execute | `invoice_posting.create` | POST `/requests` | create (+filial) | governed |
| execute | `invoice_posting.update` | PATCH `/requests/{id}` | create/process/manage | governed |
| execute | `invoice_posting.link_purchase_order` | POST `/requests/{id}/purchase-orders/link` | process/manage | governed |
| execute | `invoice_posting.start` | POST `/requests/{id}/start` | process/manage | governed |
| execute | `invoice_posting.block` | POST `/requests/{id}/block` | process/manage | governed |
| execute | `invoice_posting.resume` | POST `/requests/{id}/resume` | process/manage | governed |
| execute | `invoice_posting.post_manual` | POST `/requests/{id}/post-manual` | process/manage | governed; **justificativa obrigatória na CLARA** |
| execute | `reconciliation.run` | POST `/reconciliation/run` | manage | governed |
| delete | `invoice_posting.cancel` | POST `/requests/{id}/cancel` | create/process/manage | destructive, governed, justificativa |

Os conjuntos "Visível para" devem ser **idênticos** aos decorators da BFF (fonte: matriz da suíte de contrato). A BFF continua decidindo; a visibilidade é só conveniência.

**Saída:** doc 166 + evidência de identidade (R2 limpo) + plano de testes.

#### F7.1 — Leituras
- Implementar as 8 entradas `read` + `get_context(topic='schema')` de cada uma.
- **Testes DEV/HML (via API do MCP, JSON-RPC com tokens dos perfis de teste P0–P12):** `tools/list` inalterado (mesmas 6 tools); `get_context(catalog)` mostra as entradas LNF **somente** para os perfis com a permissão correspondente; cada `read` devolve os **mesmos dados** que a rota da BFF chamada diretamente pelo mesmo perfil; perfil sem filial 02 não obtém dados da filial 02; P10 (serviço) não acessa.
- PROD: deploy do serviço da CLARA (protocolo P6/P7); verificação técnica de health; teste funcional fica para F7.4.

#### F7.2 — Análise
- Implementar `analyze` com `analysis_type=invoice_posting_backlog` (nome wire-safe no enum de `tools/list`; alias `invoice_posting.backlog` aceito no dispatch) sobre os reads (sem SQL próprio, sem acesso direto a banco).
- Achados FACT (com números e origem) vs RECOMMENDATION; ausência de fonte ≠ zero; nunca "validar" ou "lançar" por inferência.
- Testes DEV/HML com dados conhecidos (fixtures da suíte): números da análise batem com contagens da BFF.
- **F7-R (2026-11-13):** clientes MCP reais validam o enum antes de enviar — o enum publicado **deve** incluir `invoice_posting_backlog`; teste automatizado valida cada entrada do catálogo contra o `inputSchema` de `tools/list` (jsonschema).

#### F7.3 — Ações governadas
- Implementar as entradas `execute`/`delete` da tabela, no padrão existente da CLARA (prepare sela a operação; commit exige `proposal_handle` + `confirmation=true`; read-back pós-commit; idempotência; proposta expirada/de outro ator rejeitada).
- `direct` somente para `comment` e `reconciliation.refresh`.
- Testes DEV/HML via API do MCP: para cada ação, prepare não altera nada (contagem igual); commit altera exatamente o esperado (read-back = resposta da BFF); perfil sem permissão → negado no prepare **e** no commit; commit com proposta de outro usuário → rejeitado; cancel exige justificativa; post_manual exige justificativa; batch respeita dependências.
- Nenhuma ação dispara sem consentimento quando for governed.
- **F7-R (2026-11-13):** apresentação selada (`displayable=true`) para **todas** as actions LNF governadas/destrutivas (e read-back legível em comment/refresh); HML E2E com **commit** (canal conversacional só em HML para automação; PROD permanece `portal`).

#### F7.4 — Produção + roteiro de teste do owner
- Deploy PROD do serviço da CLARA (P6/P7); health; catálogo publicado.
- Entregar ao owner o **roteiro de teste** (ChatGPT e Claude), para ele executar com o próprio usuário:
  1. "CLARA, quais ações de lançamento de notas fiscais eu tenho?" → lista coerente com as permissões dele.
  2. "Quantas notas estão aguardando lançamento na filial 01 e na 02?" → bate com o app.
  3. "Detalhe a nota <número>." → bate com o detalhe no app.
  4. "Faça a análise do backlog de lançamento de notas desta competência." → números conferem com o app.
  5. "Comente na nota <número>: teste CLARA" → comentário aparece no app (direct).
  6. "Inicie o atendimento da nota <número>." → CLARA apresenta a proposta e **não executa** sem o "confirmo"; após confirmar, o app mostra "Em atendimento".
  7. Usuário sem permissão de filial 02 pede dados da 02 → negado.
- **Saída:** roteiro PASS informado pelo owner (PENDING_OWNER até lá).

---

### F6 — Limpeza final (última fase; encerra o rollback)

**Entrada:** F5c DONE **e** F7.4 DONE.
1. **api-delpi:** remover o módulo LNF (router, use cases, domínio, SQL, gateway, notificações, testes, pasta de migrations do schema LNF do runner de plugins), a chave `LNF_MODULE_ENABLED` e o mount do volume DANFE; manter envs compartilhados usados por outros módulos. Doc `api-delpi/docs/api/lancamento-notas-fiscais.md` passa a apontar para a BFF.
2. **MFE:** trocar o default de `VITE_LNF_API_BASE` para o endereço da BFF (nenhuma outra mudança).
3. **BFF:** `LNF_HOSTED_ENABLED` passa a `true` por padrão (ou a chave é removida, mantendo o módulo sempre montado); `LNF_MIGRATIONS_MODE=apply` (com ledger completo é no-op — provar em HML que nada é executado); BFF passa a ser a única dona de futuras migrations V015+.
4. **Suíte de contrato:** alvo padrão = BFF; manter golden e a nota D8.
5. **Testes:** DEV e HML completos; deploy PROD na ordem BFF → api-delpi → MFE; verificar que o app segue funcionando e contagens coerentes.
6. **Docs:** 163 = CONCLUÍDO; ADR-001 consequências finais; 164 arquivado; 165 Quadro todo DONE; README.

**Saída:** PROD sem código LNF na api-delpi, app funcionando pela BFF, CLARA operando, docs atualizados.

---

## PARTE 7 — CHECKLIST DE NÃO-REGRESSÃO (rodar em toda promoção para PROD)

- [ ] Suíte de contrato LNF contra o alvo da fase: matriz AuthZ 100% (P10 = D8) e `compare_golden` = 0 diferenças além de D8
- [ ] Suíte completa da BFF verde (fechamento, CLARA, minhas tarefas)
- [ ] Testes da api-delpi verdes (enquanto o módulo existir lá)
- [ ] Testes do MFE verdes; bundle com o endereço correto da fase
- [ ] Preflight LNF PASS no ambiente de destino
- [ ] Health/ready dos serviços tocados
- [ ] Nenhuma alteração fora das pastas previstas (git diff --stat por pasta)

---

## PARTE 8 — FORMATO DO RELATÓRIO (ao final de cada fase ou parada)

```text
FASE / ETAPA:
STATUS: DONE | BLOCKED R<n> | IN_PROGRESS
HEAD inicial → final; SHAs; push ok?
O QUE FOI FEITO: (lista curta)
TESTES: DEV | HML | PROD — resultado por item (PASS/FAIL/...), com comando/saída resumida
NÃO-REGRESSÃO (Parte 7): itens marcados
PROBLEMAS E CORREÇÕES: causa → correção → SHA → reteste
PENDÊNCIAS DO OWNER: (ex.: smoke F5b, roteiro F7.4)
PRÓXIMO PASSO DA TRILHA:
```

---

## PARTE 9 — REGISTRO DE EXECUÇÃO (o Cursor acrescenta; nunca apaga)

| Data/hora | Fase.etapa | Ambiente | Ação | Resultado | SHA | Observação |
|---|---|---|---|---|---|---|
| 2026-11-12 | F0–F4b | DEV/HML/PROD(leitura) | Inventário, contrato, implementação dark, ensaio de corte e rollback em HML | PASS (ressalvas registradas) | até `fddd4bb813` | ver 163/164 |
| 2026-11-12 ~17:00–17:50 -03 | F5a.0 | HML | Smoke MFE federado P11/P2/P6B + Network BFF-only + rollback | PASS (P6→P6B) | `496644bbb7` | artefatos `tests/contracts/.../f5a-smoke/`; to_api_delpi=0 |
| 2026-11-12 | F5a.1 | DEV/HML | CLI `lnf_preflight` + unit tests | DEV PASS 5/5; HML 4/5 (financial FAIL esperado) | `496644bbb7` | PROD preflight TEST_NOT_RUN |
| 2026-11-12 | F5a.2 | versionado + host PROD | compose dark + nomes `.env` PROD | PASS | `496644bbb7` | flags default AS-IS; volume DANFE BFF |
| 2026-11-12 | F5a.3 | PROD→HEAD | Controle commits CF / MFE / api-delpi | **BLOCKED R4** | `9d0d591b0a` | CF+MFE só LNF; api-delpi dezenas de commits não-LNF |
| 2026-11-12 | F5a.4 | PROD | Deploy dark BFF→api-delpi→MFE | TEST_NOT_RUN | — | parado por R4; baseline OpenAPI registrada no 164 |
| 2026-11-12 | F5a.5 | docs | 164/ADR-001/163/README + trilha 165 no repo | PASS | docs `9d0d591b0a` + este arquivo | D9/logs aceitos owner |
| 2026-11-12 17:51 -03 | F5a | — | Ingresso na trilha 165; status F5a → BLOCKED R4 | BLOCKED R4 | `3cde750655` | aguarda decisão owner sobre rebuild api-delpi |
| 2026-11-12 17:52 -03 | F7 princípios | docs | Owner reforça paridade funcional total CLARA (leitura+escrita+delete) | registrado | `0b2652553b` | F5a permanece BLOCKED R4; upload 610678e5 mesclado sem apagar Registro |
| 2026-11-12 17:53 -03 | F5a.R4 | — | Owner: publicar api-delpi com todos os commits pendentes da main + salvaguardas F5a.4-API | DECISÃO | — | desbloqueia R4 só para api-delpi nesta fase |
| 2026-11-12 17:54 -03 | F5a.4 | PROD | Owner: deploys F5a.4 (incl. api-delpi) autorizados AGORA fora da janela | DECISÃO | — | manter observação 15 min + rollback se 5xx/app quebrar |
| 2026-11-12 17:55 -03 | F5a | docs | 165: exceção R4 + F5a.4 detalhada; status → IN_PROGRESS (F5a.4) | IN_PROGRESS | `fdc31ad48e` | Downloads sem texto F5a.4-API; conteúdo mesclado da decisão do owner + Registro preservado |
| 2026-11-12 18:00 -03 | F5a.4.1 | PROD | BFF dark rebuild + verify + preflight | PASS 5/5 | imagem nova CF | OpenAPI 112/LNF0; LNF 404; closing 401 sem JWT |
| 2026-11-12 18:01 -03 | F5a.4.2 | PROD | MFE dark rebuild | PASS | imagem nova MFE | bundle api-delpi=1 bff=0 |
| 2026-11-12 18:02 -03 | F5a.4-API.a | — | Inventário 68 commits api-delpi; OpenAPI LNF 22 paths / 24 ops | PASS | — | LNF path/ops estáveis before=after |
| 2026-11-12 18:02 -03 | F5a.4-API.b | PROD DB | Migrations eng≤V023 quality≤V047 já no ledger | PASS | — | sem DDL pendente LNF; PRC/quality já aplicadas |
| 2026-11-12 18:02 -03 | F5a.4-API.c | PROD .env | PORTAL_RH_* + LNF_MODULE_ENABLED presentes | PASS | — | só nomes |
| 2026-11-12 18:03 -03 | F5a.4-API.d | imagem | pytest HEAD vs imagem PROD antiga | PASS (paridade) | `a674524ce866` | 61 failed idênticos (only_new=0); 5889 vs 5887 passed |
| 2026-11-12 18:04 -03 | F5a.4-API.e | HML | up-hml api-delpi HEAD | PASS | HML healthy | paths 731 LNF 22; LNF_MODULE_ENABLED=true |
| 2026-11-12 18:05–18:20 -03 | F5a.4-API.f | PROD | up-prod api-delpi + observação 15 min | PASS | `a674524ce866` | 1×502 healthcheck no recreate; depois 0 5xx; scrap TV 200 |
| 2026-11-12 18:20 -03 | F5a | — | Critérios de saída F5a atendidos | DONE | `38f46c0eac` | próximo: F5b (janela + smoke owner) |
| 2026-11-13 07:26 -03 | F5b | PROD | Owner: corte F5b autorizado AGORA (qualquer horário, incl. comercial) | DECISÃO | — | rollback imediato se gatilho Parte 5 |
| 2026-11-13 07:27 -03 | F5b | docs | Quadro → IN_PROGRESS; compose PROD MFE build-arg VITE_LNF_API_BASE | IN_PROGRESS | `f6950fdb0d` | espelha HML para permitir corte via script |
| 2026-11-13 07:28 -03 | F5b.1 | PROD | Preflight 5/5 + baseline contagens/health/bundle | PASS | — | requests=1430; pending=21 posted=1383; MFE base api-delpi |
| 2026-11-13 07:28 -03 | F5b.2.1 | PROD | BFF `LNF_HOSTED_ENABLED=true` + rebuild | PASS 13,4 s | — | `lnf_migrations_verify_ok` V001–V014; LNF noauth 401 |
| 2026-11-13 07:28 -03 | F5b.2.2 | PROD | api-delpi `LNF_MODULE_ENABLED=false` + rebuild | PASS 15,1 s | — | service token LNF → 404 |
| 2026-11-13 07:29 -03 | F5b.2.3 | PROD | MFE build `VITE_LNF_API_BASE`=BFF | PASS 56,3 s | — | runtime BFF; residual string api-delpi = fallback Vite morto |
| 2026-11-13 07:31 -03 | F5b.2.4 | PROD | Sync catálogos chat/TV (OpenAPI sem LNF) | PASS | — | chat actions=788; TV routes=585; lnf_mentions=0 (wrapper script rc≠0 por logs NDJSON) |
| 2026-11-13 07:31 -03 | F5b.3 | PROD | Verificação técnica (D8 403, api 404, OpenAPI, contagens) | PASS | — | BFF 134/22/24ops; api 709/0; contagens iguais; 5xx LNF=0 |
| 2026-11-13 07:32 -03 | F5b.4 | PROD | Smoke do owner | PENDING_OWNER | — | checklist entregue no relatório; F5b não DONE até PASS do owner |
| 2026-11-13 ~08:00 -03 | DECISÃO | — | Owner: execução contínua F5b→F5c→F7.0…F7.4 sem pausa; gates HML/PROD autorizados; parada só H1–H4; F6 aguarda | DECISÃO | — | smoke F5b não bloqueante; tokens HML ok; nunca usuários PROD |
| 2026-11-13 08:00 -03 | F5b | docs/PROD | Fechamento técnico: PASS; smoke PENDING_OWNER (não bloqueante) | técnico PASS | `630ca6f3b9` / `e43aa9558b` | tempos BFF 13,4s api 15,1s MFE 56,3s; fallback Vite morto confirmado pelo revisor |
| 2026-11-13 08:04 -03 | F5c.d1 | PROD | 1ª checagem hypercare | PASS | — | total=1430; pending=15 posted=1389 blocked=1 cancelled=25; 5xx_60m=0; 403_60m=4 (detail create); HOSTED=true MODULE=false |
| 2026-11-13 08:05 -03 | F7.0 | docs | Inventário CLARA + R2 + doc 166 | DONE | (ciclo F7) | MCP in-process BFF; JWT usuário SIM; catálogo alvo travado |
| 2026-11-13 08:05 -03 | F7.1–F7.3 | DEV | Implementação reads/analyze/governed LNF nas 6 tools | PASS | `0926f07160` | `invoice_posting_bridge` + `invoice_posting_capabilities` |
| 2026-11-13 08:20 -03 | F7.HML | HML | MCP clients Keycloak + CF.access nos perfis LNF + DAG HML | PASS | — | client `mcp-controllership-finance`; manifesto CF registrado |
| 2026-11-13 08:25 -03 | F7.fix | DEV/HML | Query defaults quebravam list/analyze (`cannot adapt type Query`) | PASS | `1328cd0d85` | `_resolved_route_kwargs` / `_call_route` |
| 2026-11-13 08:30 -03 | F7.1–F7.3 | HML | JSON-RPC: catalog por perfil, read, analyze, refresh, prepare, negativos | PASS | `1328cd0d85` | tools/list=6; P0=403; P10=401; justificativas obrigatórias |
| 2026-11-13 08:35 -03 | F7.4 | PROD | Deploy BFF + health + OpenAPI 22/24 + import 8 reads + mcp 401 | PASS técnico | `1328cd0d85` | roteiro owner PENDING |
| 2026-11-13 08:35 -03 | F5c | PROD | Recheck pós-F7 | PASS | — | total=1430; 5xx_15m=0; HOSTED=true |
| 2026-11-13 08:30 -03 | F7-R | PROD→docs | Revisor (conector Claude): enum analyze sem LNF; prepare start `displayable=false` | REWORK | — | prompt F7-R; commits só HML |
| 2026-11-13 08:34 -03 | F7-R | DEV | enum `invoice_posting_backlog` + LNF presenters + testes schema/presentation | PASS | `348140ec53` | 36 unitários no container |
| 2026-11-13 08:35 -03 | F7-R | HML | Deploy + `CLARA_CONSENT_CHANNEL=conversational` (só HML) | PASS | `348140ec53` | canal armado p/ E2E commit |
| 2026-11-13 08:41 -03 | F7-R | HML | E2E prepare→commit (P9) + negativos + jsonschema tools/list | PASS 36/36 | — | `/tmp/f7r-hml-e2e.json`; expire via `handle_hash`; branch deny no commit P11×02 |
| 2026-11-13 08:42 -03 | F7-R | PROD | Deploy BFF; forçar `CLARA_CONSENT_CHANNEL=portal`; tech checks | PASS | `348140ec53` | enum+6 tools+presentation; unit 36; health 200; **sem commit real** |
| 2026-11-13 08:43 -03 | F7.4 | PROD | Roteiro owner reaberto pós-F7-R | PENDING_OWNER | `348140ec53` | refrescar tools no conector; retestar 4 e 6 |

### Roteiro de teste do owner — F7.4 (ChatGPT / CLARA em PROD)

Pré-condição: usuário com `controllership-finance.access` **e** as permissões LNF do perfil real.

1. "CLARA, quais ações de lançamento de notas fiscais eu tenho?" → catálogo coerente com o perfil (sem entradas de create se não tiver create).
2. "Liste as solicitações abertas da filial 01." → mesmos totais que o app.
3. "Abra a solicitação \<id\>." → detalhe + link do app para PDF/XML (sem binário na conversa).
4. "Analise o backlog de lançamento de notas da filial 01." → tool `analyze` com `analysis_type=invoice_posting_backlog` (enum de tools/list); FACT com números/fonte; RECOMMENDATION sem lançar por inferência.
5. "Comente na nota \<id\>: teste CLARA F7.4" → comentário aparece no app (direct).
6. "Inicie o atendimento da nota \<id\>." → prepare com **presentation.displayable=true** (alvo/efeito legíveis) e **não executa** sem confirmação Portal; após step-up, app mostra Em atendimento.
7. Negativos: perfil só view não vê create/start; cancel/post_manual sem justificativa recusados; serviço/token de máquina não entra no MCP.

**Após F7-R:** o revisor deve refrescar tools no conector e repetir 4 e 6 (enum + presentation). Marcar F7.4 DONE somente com PASS do owner neste roteiro.

**F6 (limpeza) — não inicia agora.** Pré-requisitos: (a) 5 dias úteis de F5c sem incidente a partir de 2026-11-13; (b) smoke F5b PASS do owner; (c) este roteiro F7.4 PASS. Data mais cedo possível para F6: **2026-11-20** (após o 5º DU: 13, 14, 17, 18, 19), se (b) e (c) estiverem PASS.
