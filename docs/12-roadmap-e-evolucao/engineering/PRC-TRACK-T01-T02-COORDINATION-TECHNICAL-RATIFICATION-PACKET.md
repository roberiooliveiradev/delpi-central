# PRC-TRACK — T01/T02 | Pacote técnico de ratificação para PROD-02

> **Data:** 2026-11-13. **Status:** `COORDINATION_TECHNICAL_PROPOSAL / ENGINEERING_OWNER_RATIFICATION_PENDING / PROD02_CODE_BLOCKED`.
> **Natureza:** decisão técnica proposta sobre **como** atender às regras funcionais já aprovadas. **Não é ratificação assinada pelo owner, autorização de migrations ou evidência de runtime**.
>
> **Fonte funcional vinculante:** [PRC-TRACK — regras canônicas e plano único](./PRC-TRACK-CANONICAL-PRODUCT-RULES-AND-EXECUTION-PLAN.md), §§1–2, 4–5, R01–R05/R18; em caso de divergência com histórico G1, prevalece o documento canônico.
> **Execução:** Devin implementa após gate; ChatGPT/EVA coordena e revisa; Engineering API owner e Coordination ratificam; Cursor verifica HML independente. **PROD-01 não precisa de nova implementação**.

## 1. Baseline técnica observada no GitHub

- `ProductRegistrationService._build_snapshot(request,draft_data)` atualmente faz `dict(draft_data)` e remove `officialProductCode` em CREATE. Não forma ficha consolidada nem identifica cobertura ou provenance.
- `ProductRegistrationService._revision_changes` usa `changed_paths` e `before` de revisão anterior, sem diff técnico canônico do estado consolidado.
- `PostgresProductRegistrationRepository.complete_request` faz lock/CAS de request, `SELECT ... FOR UPDATE` de record, insere verification e **sempre** insere revision com `revision_number+1`, atualiza record/request e emite evento na mesma transação. Há adapter in-memory e port equivalentes que devem continuar semanticamente compatíveis.
- Existem rotas REST de registro e revisões, port `OfficialProductReaderPort`, read-back com `_compare` e validação `matched`; não inventar nova leitura direta do TOTVS. PROD-01 listagem já integrada, com HML reportada pelo Devin.
- **Evidência:** inspeção do código no GitHub, não benchmark/teste novo. Devin deve revalidar o SHA antes de implementar.

## 2. T01 — contrato de snapshot consolidado e provenance (proposta para aprovação)

**Owner:** Engineering API / PRC. **Consumers:** PRC REST, Portal Engenharia, futura API de comparação; EVA apenas consumidora autorizada. **Fonte oficial:** gateway existente de leitura autorizada Domain API/TOTVS; valores registrados PRC não ganham estatuto de observação oficial automaticamente.

### 2.1 Shape de domínio proposto, não API congelada

Cada revisão é um **estado técnico consolidado** do catálogo de acompanhamento PRC, serializado com `schemaVersion` explícito; não é o draft nem catálogo total de TOTVS. Modelar conceitualmente:

- `fields[path] = { value, coverageState, valueOrigin, verificationState, evidenceRef? }`.
- `coverageState`: `present | unknown | not_applicable`, com distinção de campo **não capturado/legado** e `null` explícito. Valor `null` não significa ausência de chave nem intenção de limpeza.
- `valueOrigin`: `official_verified | inherited_confirmed | registered_unverified | unknown`, nome técnico final sujeito ao catálogo existente. `verificationState` é independente da origem para não confundir proveniência histórica e verificação do request corrente.
- `evidenceRef` e timestamps só quando existem, vinculados a fonte/caminho efetivamente comprovados; dados sensíveis ficam fora do DTO público.
- `supplierLinks`: identidade estável `supplierCode + store`; atributos por campo, cobertura e presença do vínculo. Não supor confirmação de `REMOVE_LINK` se o contrato atual não permitir; D15 permanece gate específico.

**Abstraction Gate:** reusar `catalog`, `sa5_baseline`, normalizadores, verificações atuais e modelos de dados disponíveis. Não criar nova engine genérica de schema/diff sem necessidade comprovada.

### 2.2 Construção de snapshot

1. Obter catálogo exato de paths PRC suportados pela Engineering API (não incluir atributos externos não contratados).
2. Carregar revisão vigente quando houver; validar `schemaVersion` e cobertura. **Não reescrever revisões históricas**.
3. Preparar baseline por campo: legado sem provenance confiável permanece `registered_unverified` ou `unknown`, nunca promovido a `official_verified` por inferência.
4. Aplicar exclusivamente alterações explicitamente presentes no request e **individualmente cobertas** pela evidência/verificação permitida. `omitted` preserva valor/proveniência originais; `null`, string vazia ou lista vazia ambíguas não são `CLEAR`.
5. `CLEAR` / `REMOVE_LINK` exigem intenção explícita e validação de suporte/observação. Se o owner oficial não permite, bloquear fail-closed sem alterar histórico.
6. Vincular proof ao campo verificado e manter estado anterior quando não revisto; uma nova conclusão `matched` não revalida automaticamente toda a ficha.
7. Normalizar valores técnicos antes do diff (conforme catálogo oficial); ordem incidental, metadata de evidência e timestamps não constituem alteração técnica. Valores/estados incomparáveis não podem ser silenciosamente tratados como iguais ou diferentes; devolver condição explícita `incomparable` e não publicar revisão baseada em inferência.

**V1 sem versão anterior:** produzir baseline com **todos os campos do catálogo**, indicando `unknown/not_applicable` para lacunas; o mínimo de cobertura necessário para concluir deve ser **o conjunto exigido pela verificação PRC existente**, não uma exigência inventada de leitura integral TOTVS. Se não for possível compor baseline honesta e válida, falhar antes da persistência de conclusão. Uma primeira UPDATE validada sem diff ainda cria V1.

### 2.3 Compatibilidade

- `technical_snapshot` existente pode ser objeto legado plano; novos consumers devem identificar `schemaVersion` e distinguir formatos, sem afirmar provenance retroativa. Evolução de persistência preferencialmente **aditiva e dentro do JSONB/colunas existentes**, condicionada à inspeção de schema/migrations.
- API de detalhe legada usa `snake_case`; não alterar seu shape sem contrato de versão/compatibilidade do PROD-03. Não misturar atualização de DTO com PROD-02.
- Histórico imutável não recebe backfill automático; criar testes de convivência legacy/new.
- Logs/auditoria não incluem token ou segredo; `evidenceRef` é referência segura, não payload completo de fonte oficial.

## 3. T02 — contrato de conclusão, V1 e no-op (proposta para aprovação)

**Owner:** Engineering API / PRC. **Fronteira de transação:** DB PRC do owner; leitura oficial ocorre por API read-only antes do commit local. Não presumir rollback distribuído no TOTVS nem escrita nele.

### 3.1 Algoritmo de domínio

1. Validar ator/AuthZ existente e estado elegível; conferir `expectedVersion`, código oficial e política de read-back.
2. Verificar `matched` contra fonte oficial conforme contrato existente; `mismatched/unverifiable/unavailable` **não publicam** record/revision nem concluem solicitação. Preservar auditoria de tentativa de verificação do fluxo já existente.
3. Montar **candidateSnapshot** via T01, com `schemaVersion`, `coverage` e proveniência; calcular `canonicalTechnicalDiff` contra snapshot consolidado da versão vigente quando comparável.
4. **Record sem revisão publicada:** concluir validado e publicar **V1 baseline**, `changeKind=baseline_initial`, mesmo `diff=[]`.
5. **Record com revisão e diff técnico real:** publicar **Vn+1**, `changeKind=technical_change`.
6. **Record com revisão, diff técnico vazio:** concluir solicitação, persistir verification/ledger e vínculo com `recordId` + `currentRevisionNumber`, `changeKind=no_technical_change`, **sem INSERT em revisions e sem alterar snapshot ou contador**. É permitido atualizar timestamp de verificação/observabilidade no record se o contrato disser claramente que **não equivale a evolução técnica**.
7. `incomparable`, conflito CAS, baseRevision stale ou verificação falha: fail-closed no caminho correspondente, sem publicar revisão ou concluir parcialmente; não mascarar `incomparable` como no-op.
8. Idempotency-Key/replay da mesma conclusão produz **mesmo outcome** sem duplicar evento, verification, request completion ou revisão; concorrência sobre o mesmo record e request respeita locks/case version e a base vigente.

### 3.2 Atomicidade local

**Em uma transação PRC**: revalidar request/status/CAS e registro/source+code sob lock; revalidar condição de publicação contra revisão vigente após lock; inserir verification matched; condicionalmente inserir revisão; atualizar ponteiro somente se V1/Vn+1; marcar request completed/vinculado; registrar evento auditável com `recordId`, `effectiveRevisionNumber`, `technicalChange: bool`, `changeKind` e `verificationId`. Em caso de falha da transação, rollback local, sem estado de produto nem request parcialmente publicado.

**Ponto crítico de concorrência:** o diff e a escolha Vn+1/no-op calculados antes do lock **não são autoritativos**. Exigir revalidação por base_revision/version e/ou diff dentro da fronteira serializada (sob lock) antes do INSERT. Se o estado mudou, devolver `409` recuperável com retry controlado; nunca concluir a partir de comparação stale. Não criar camada de transação externa no application.

**Semântica de resposta proposta:** manter envelope PRC atual, com `recordId`, `revisionNumber` efetiva (também no no-op), `verificationId`, `technicalChange` e `changeKind`; definir como sinalizar ausência de novo objeto revision no no-op sem quebrar consumidores atuais. **Não forjar uma revisão recém-criada**. As propriedades concretas exigem conferência de consumers e contrato antes de editar retorno.

### 3.3 Erros/observabilidade/rollback

- `401/403` identidade/acesso; `409` CAS, stale revision, incongruência de publicação; `422` contrato inválido ou operação explícita não suportada; `503` backend/official reader indisponível conforme mapeamento atual. Preservar nomenclatura real de erros do PRC até revisão dos testes.
- Métricas: conclusão `baseline_initial / technical_change / no_technical_change / blocked` por operationId sem payload sensível, correlationId e SHA.
- Reversão de código deve preservar leitura do histórico já emitido. Se novo snapshot se tornar incompatível com versão anterior, feature gate/estratégia dual-read deve ser aprovada antes do deploy; **rollback não deve apagar revisões imutáveis nem desfazer conclusão válida**.
- Schema/migration só com evidência de necessidade, owner oficial e plano de rollback testado. Nenhuma mudança de tabelas de outros bounded contexts.

## 4. Acordos de interface e compatibilidade a confirmar pelo owner (sem nova decisão do PO)

| Interface | Proposta e validação exigida |
|---|---|
| `ProductRegistrationService` | montar snapshot T01, calcular diff técnico; manter business rules independentes de framework |
| `ProductRegistrationRepository.complete_request` | outcome condicional com replay seguro e atomicidade PRC; estender port sem quebrar consumers |
| Postgres/in-memory/unavailable | paridade de V1/no-op/diff/erros e teste de corrida |
| PRC REST | preservar resposta/operationId/idempotência existentes, adicionar metadata só com compatibilidade |
| Domain API/official-reader | somente READ com acesso oficial; classificar cobertura por path; sem escrita TOTVS |
| PRC/Portal/My Requests/EVA | inventariar consumidores de `revision` obrigatório no retorno e índices de versão, sem quebrá-los |
| HML/release | imagens versionadas, teste dois usuários, no-op/matched, segurança; **produção apenas health e reads sem escrita de negócio** |

## 5. RQ/AC para Devin após ratificação

| ID | Critério verificável |
|---|---|
| T01-AC01 | snapshot V1 contém catálogo PRC com coverage e provenance honesta; sem campos externos inferidos |
| T01-AC02 | UPDATE parcial preserva omitidos, origem e timestamps; CLEAR explícito aceito somente se suportado |
| T01-AC03 | supplier links diferenciam omitted/unknown/ADD/UPDATE/REMOVE, por code+store |
| T01-AC04 | legado plano permanece legível e não recebe confirmação retroativa |
| T02-AC01 | primeira UPDATE matched, ainda sem histórico, cria V1 inclusive no-op técnico |
| T02-AC02 | segunda conclusão matched sem diff: request completed e ledger/verification, **revisionNumber permanece V1** |
| T02-AC03 | diff real publica V2 uma única vez, snapshot consolidado imutável |
| T02-AC04 | replay idempotente da mesma chave e CAS concorrente não duplicam revisão nem conclusão |
| T02-AC05 | mismatch/unverifiable/forbidden/stale/incomparable não publicam nem deixam resultado parcial |
| T02-AC06 | parity Postgres/memory e teste integração real no SHA |
| T02-AC07 | retorno REST antigo conserva contrato, no-op sinalizado sem revision recém-publicada fictícia |
| T02-AC08 | HML multiusuário autorizado/negado, fluxo V1/no-op/V2; Cursor revalidação independente |
| T02-AC09 | PRD sem testes mutáveis, somente health/read-only smoke; PROD não liberado por este pacote |

## 6. Gate de ratificação — não confundir proposta com aprovação

**Coordination + Engineering API domain owner** devem registrar, no ledger, decisão explícita sobre:

1. **T01:** shape/catalog/coverage/provenance + política de legacy read e normalização de links.
2. **T02:** ramo no-op e V1, serialização/locking, metadata de retorno e compatibilidade.
3. **Migração/rollback:** aprovação condicionada a inventário de schema e consumers; escopo mínimo correto, sem nova autoridade.

**Modelo de decisão:** `T01: APPROVED|REVISE|REJECT; T02: APPROVED|REVISE|REJECT; OWNER; SHA; RATIONALE; CONTRACT_VERSION; MIGRATION_GATE; ROLLBACK; TESTS`.

Se as interfaces de retorno/legado precisarem decisões locais de compatibilidade dentro do mesmo owner, Devin apresenta inventário antes da mutação; não devolve escolhas funcionais já resolvidas ao PO.

**Liberação de Devin PROD-02:** somente depois de T01/T02 aprovados pelo owner competente e Coordination, e de eventual `ARCHITECTURE_DECISION_REQUIRED` encerrado. Até lá, `DEVIN_PROD02_BLOCKED_BY_COORDINATION`. Cursor pode finalizar revalidação PROD-01 em paralelo, sem ser bloqueador de ratificação.

**Próximo executor após gate:** Devin implementa via branch dedicada com menor diff, testes SHA, PR governado, HML com escrita em dados segregados, Cursor aceite independente e PRD exclusivamente smoke READ-only após release autorizado.


## 7. Deliberação registrada — aceite do PO sobre a proposta T01/T02 (13/11/2026)

**Decisão expressa recebida neste chat:** PO concordou com as recomendações para T01 e T02 e autorizou registrar tudo no GitHub. **Status de negócio/direção de Coordination:** `PO_APPROVED / COORDINATION_RECOMMENDATION_ACCEPTED_WITH_CONDITIONS`. **Ratificação final do Engineering API domain owner:** `PENDING_OWNER_CONFIRMATION`, pois não há evidência de anuência formal desse owner nesta interação. Não converter o aceite do PO em assinatura de outro owner.

| ID | Direção aceita | Condições de execução |
|---|---|---|
| **T01** | **APPROVED_BY_PO_WITH_CONDITIONS** — snapshot consolidado do catálogo PRC, schema/cobertura/provenance por campo, valores heredados/unknown honestos, UPDATE parcial omitido preserva, supplierCode+store, legado imutável | Engineering API owner confirma catálogo/DTO/contrato de official reader, adequação de `null/CLEAR/REMOVE_LINK`, compatibilidade das revisões legadas e migrations mínimas |
| **T02** | **APPROVED_BY_PO_WITH_CONDITIONS** — primeira conclusão matched V1; após V1 Vn+1 só com diff real; no-op auditado sem nova revisão; uma transação local, CAS, locks, replay idempotente | Engineering API owner confirma serialização e postconditions, contrato de resposta e consumidores, tratamento de falha, migração/rollback e testes de paridade |

**Proibições mantidas:** nenhuma nova permissão/BC/autoridade; nenhuma escrita TOTVS; produção sem qualquer escrita de dados de negócio para teste; não deduzir provenance oficial de drafts; nenhuma aprovação automática de deploy ou merge por este documento.

**Gate formal:** `ENGINEERING_OWNER_RATIFICATION_PENDING` até registro inequívoco do owner competente com `APPROVED/REVISE/REJECT`, versão de contrato e eventuais restrições de compatibilidade. O Devin pode fazer preparação documental e inventário mínimo condicionado à confirmação, mas **não iniciar mutações de contrato/código PROD-02** antes do gate formal exigido pelo projeto. Após esse registro, Coordination emite ordem executável DEVIN-PROD-02 com RQ/AC desta proposta.

**Evidência:** decisão do PO neste chat de 13/11/2026; implementação PROD-02 `TEST_NOT_RUN`; nenhuma mudança de runtime nesta deliberação.
