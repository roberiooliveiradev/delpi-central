# ADR candidato / contrato inicial — Registro de execuções de escrita Protheus na api-delpi

**Decisão PO:** 2026-10-21. **Estado:** `OWNER_DECIDED / DESIGN_TARGET`; implantação ainda `TEST_NOT_RUN`. Não constitui migração aprovada, deploy, habilitação de writes ou contrato final de schema. Revalidar HEAD e regras antes de construir.

## Decisão de ownership

A **api-delpi** é a proprietária da rastreabilidade das operações de escrita que **ela executa/encaminha** à API REST Protheus (integração implementada por Gabriel), independentemente do portal consumidor. A `supplies-api` **não** é dona dessa tabela: é BFF para autorização/composição do Portal Suprimentos, expõe o acompanhamento ao usuário com escopo por operação. Outros consumidores autorizados de rotas da `api-delpi` devem reutilizar o mesmo mecanismo. **Não** transformar a `api-delpi` em audit store genérico para todas as APIs corporativas: o boundary é a execução de integração que ela possui.

**Invariantes:** Keycloak identidade; Core API effective permissions, RBAC e auditoria de plataforma; `api-delpi` integração/regra TOTVS; `supplies-api` AuthZ Core-first e composição de produto; Protheus/Execauto MATA020 autoridade final do cadastro. **Nunca** escrever SA2 via SQL nem espelhar cadastro Protheus em `supplies` Postgres.

## Objetivo e semântica

Persistir um **registro por operação lógica de escrita** antes do envio ao REST e trilha de tentativas/eventos ligada a ele, contendo IDs de correlação, autor, cliente/portal, ação e recurso, request normalizado e **payload efetivamente encaminhado** (sanitizado, com versões de schema), resposta/status/error sanitizados, timestamps e evidências de reconciliação. Evitar perda de rastreabilidade em timeout, desconexão ou erro do Execauto; possibilitar consulta autorizada ao resultado pela BFF e futuro painel transversal (se aprovado em outra etapa).

### Estados candidatos — não confundir transporte com persistência

- `CREATED`: operação registrada duravelmente, **não enviada**.
- `SENDING`: envio iniciado ou potencialmente iniciado; após crash o resultado pode ser desconhecido.
- `ACKNOWLEDGED`: resposta REST 2xx recebida, **ainda não comprova** persistência.
- `CONFIRMED`: persistência confirmada por chave e read-after-write/consulta homologada; registrar evidência.
- `REJECTED`: falha determinística comprovada, sem efeito de gravação (não deduzir apenas de 5xx).
- `UNKNOWN`: timeout/perda de resposta/erro de transporte após possível envio, ou 5xx com efeito incerto; **sem retry automático** de POST/PUT.
- `RECONCILIATION_REQUIRED`: aguarda correlação segura/owner por falta de chave ou evidência suficiente.
- `FAILED_PRE_SEND`: falha definitivamente anterior ao envio e sem efeito upstream.

Histórico de transições é append-only; jamais reclassificar `UNKNOWN` como `REJECTED` sem prova. **Estado de envio não prova gravação.** Modelo de estados e nomenclatura finais dependerão de inventário de padrões do repositório.

## Campos candidatos de persistência (não migration pronta)

- `operation_id` UUID, `correlation_id`, `request_id`, `idempotency_key` interna se suportada; unique constraint apropriada após confirmar semântica; nunca prometer exatamente-uma-vez se upstream não suportar.
- `integration` (`protheus`), `resource` (`supplier`), `action` (`create`/`update`), `resource_key` (`A2_COD+A2_LOJA` quando conhecida), `environment_key`, `tenant/company/branch` de acordo com contrato real.
- `caller_app`/S2S client **validado**, `actor_subject` (identidade do JWT verificada e resolução Core), `codusr` **resolvido server-side**. Nunca confiar em campos do cliente como autoridade.
- `requested_fields`/hash de request, `outbound_payload_redacted` JSON versionado (**campos realmente enviados**, incluindo estrutura e nomes, com dados sensíveis minimizados), `outbound_payload_hash` e marcação dos campos protegidos/redigidos. Requisito do PO de registrar payload **não autoriza armazenamento indiscriminado** de CPF/CNPJ completo, tokens, senhas, dados pessoais ou dados fiscais sem análise de necessidade, política de criptografia, retenção e acesso.
- `status`, `attempt_count`, `http_status`, `upstream_error_code`, `error_redacted`, `ack_summary`, `reconciliation_status`, `confirmed_resource_key`, `confirmation_evidence` (proveniência/timestamp/hash resumido).
- `created_at`, `send_started_at`, `acknowledged_at`, `confirmed_at`, `updated_at`; histórico de eventos com `event_type`, `occurred_at`, `reason`, `correlation_id`, `metadata_redacted`.

**Retention/access:** definir com owner Segurança/Privacidade e padrões atuais da api-delpi. Campos protegidos devem ser criptografados quando estritamente necessários e exibidos mascarados; logs comuns não incluem payload bruto nem credenciais.

## Sequência candidata

1. Autenticar, resolver Core/AuthZ e validar payload; feature gates WRITE permanecem efetivos.
2. Após validações e antes do envio, **persistir tracking** em banco próprio autorizado da `api-delpi` com commit durável. Se falhar, **fail-closed: não enviar**.
3. Resolver de forma segura o request efetivamente transmitido e versionar/sanitizar evidência. Registro antes do network I/O; crash entre marcação `SENDING` e envio continua `UNKNOWN` até reconciliação; não reenviar automaticamente.
4. Executar POST/PUT uma única vez, sem retry automático.
5. Persistir ack/falha/transição; se resultado incerto, `UNKNOWN`, instruir reconciliação. Se falhar gravar status após envio, a operação pode ter ocorrido: tratar como `UNKNOWN`, não reenviar.
6. Confirmar resultado por GET no **mesmo ambiente** e chave correta; POST precisa do retorno código/loja prometido por Gabriel, ou mecanismo determinístico homologado de reconciliação. `CONFIRMED` somente com evidência.
7. Publicar contrato de consulta de operação/estado **somente a atores autorizados e ao consumidor associado**, via `api-delpi` e `supplies-api`, com RBAC e resource scope no backend.

## Fluxo técnico

```text
MFE supplies → supplies-api (Core authz + scope) → api-delpi (S2S + actor)
  → [store tracking in api-delpi-owned persistence] → REST Gabriel / Execauto MATA020
  ← response/timeout → tracking status → GET reconciliation / same REST environment
  → supplies-api status projection → MFE status / confirmar gravação
```

**Decisão para persistência física:** `TO_INVENTORY`. Não escolher tabela/schema/banco por suposição: investigar primeiro migrations, DB adapters, Postgres e SQL permitidos de `api-delpi`, ledger/auditoria existentes e políticas DBA. A localização deve ser **persistência própria da api-delpi**, não SA2, Intranet de parâmetros sem contrato, nem Postgres `supplies`.

## Descobertas contextuais (não revalidam runtime)

- F4.2: POST de teste via REST `:8701` localizado na `DELPI_TST01.SA2010` como `003878/01`, GET REST confirmando registro. Listagem do Portal consulta `DELPI`. **Escrita produtiva bloqueada**.
- Gabriel confirmou por e-mail em 2026-10-21 que `:8701` atende `DELPI_TST01`, prometeu verificar endpoint produtivo, implementar retorno código+loja no POST e enviar matrizes POST/PUT.
- Proposta inicial de Gabriel: tabela intermediária com status 1 enviado, 2 integrado com sucesso, 3 erro não integrado. Esta decisão de PO fixa **owner api-delpi**; detalhamento de status requer `UNKNOWN` e separação ACK vs persistência, mas não altera unilateralmente o serviço REST de Gabriel.
- Gates `PROTHEUS_SUPPLIER_CREATE_ENABLED`/`UPDATE_ENABLED` OFF conforme última verificação reportada. Nova etapa não os ativa.

## Fases e aceites para desenvolvimento

**T0 — Inventário obrigatório:** HEAD+status; regras `.cursor` gerais e de persistência/migrations/testes; detectar equivalente de auditoria/outbox/idempotência/transaction record já no repositório; definir owner físico e período de retenção; conferir contratos produtores/consumidores, e authority superior. Se conflito de owner: `EXECUTION_DRIFT`.

**T1 — Contrato/ADR final:** fechar schema persistente, política LGPD/mascaramento/criptografia, transições, fail-closed, índices, autoridade do status, idempotência possível, operações CREATE/UPDATE e extensão futura, interface `application`/ports/adapters. Não adaptar contratos silently.

**T2 — Menor implementação:** migrations/infra autorizadas no contexto `api-delpi`; use cases/port `IntegrationExecutionRepository` e adapter; eventos, payload sanitizado, status e error; integração sem mudança desnecessária do gateway; não tocar em rotas fora do escopo sem justificativa.

**T3 — Consulta e testes:** GET status/autorização do consumidor; testes transacionais, fail-before-send, crash, ACK sem persistência, timeout `UNKNOWN`, rejeição determinística, seleção de payload autorizado, concorrência, escopo cross-client/cross-actor, retenção e redaction. Não executar write real do ERP nesta fase.

**Gate de execução:** o PO autoriza iniciar inventário/contrato e implementação após aprovação do menor diff conforme autoridade; deployment de migrations e ativação produtiva exigem gate separado, plano de rollback e owner de infraestrutura/TOTVS.

## Regras STOP

- Sem banco próprio autorizado/política de dados, parar em `TO_INVENTORY`, não inventar schema físico.
- Sem autorização/capabilities efetivas, falhar fechado.
- Sem persistir tracking inicial, **não enviar** write.
- Sem certeza pós-envio, **não repetir** write automaticamente.
- Não incluir segredos no registro, payload completo com PII sem política, nem expor tracking de terceiros.
- Não mudar `URL_REST`, gates ou dados de `DELPI`/SA2.

## Report esperado do Cursor

`BASE HEAD | ORIGIN MAIN | FINAL HEAD | GIT STATUS | AUTHORITIES | EXISTING EQUIVALENTS | OWNER PHYSICAL STORAGE | RQ/AC | CONTRACT & ADR | MIGRATIONS | DATA CLASSIFICATION | AUTHZ | REQUEST/PAYLOAD DESIGN | STATUS TRANSITIONS | TESTS | SECURITY | EXECUTION_DRIFT | UNRESOLVED | NEXT STEP`.
