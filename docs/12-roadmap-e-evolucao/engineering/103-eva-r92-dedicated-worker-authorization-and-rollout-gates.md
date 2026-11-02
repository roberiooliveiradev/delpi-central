# 103 — EVA R9.2: autorização de worker isolado e gates de substituição governada

**Data:** 2026-11-02. **Status:** OWNER_AUTHORIZED_FOR_SCOPED_PROVISIONING / EXECUTION_PENDING. **Solicitação:** o owner autorizou explicitamente provisionar **worker dedicado para motores Docling e PP-StructureV3**, preservando recursos da Engineering API em produção. Isso **não** autoriza custos não aprovados, compra de GPU, acesso irrestrito, envio de desenhos à cloud, alterar o motor produtivo por padrão nem bypass de SSH Operator/Core. Ref: docs 100–102.

## Contexto comprovado
- `drawing_perception_candidate.v1` e `PerceptionEnginePort` existem na Engineering API.
- Baseline EVA `eva_baseline_r823` é o motor ativo. PPS-v3: RESOURCE_BLOCKED no host atual; Docling: TEST_NOT_RUN. Comparação BOM fail-closed corrigida para tabela unreliable, confirmada por E2E autenticado.
- Não há evidência de infraestrutura dedicada já provisionada nem benchmark comparativo dos novos motores.
- R9.1 recomendou **≥8 GiB RAM como estimativa inicial, não sizing validado**.
- A ferramenta deste fluxo de Coordination não expõe executor SSH Operator/provisionamento; **não declarar deploy ou criação de VM/worker**.

## Escopo autorizado e owners
- **Autorizado:** investigar capacidade disponível, criar worker de laboratório **somente via processo de infraestrutura aprovado**, isolado, com modelo e dependências localmente provisionados, sem consumir cotas do serviço API em produção, executar benchmark autorizado, medir e produzir recomendação.
- **Infra + FinOps:** validar host/VM, capacidade e qualquer custo incremental, aprovação de contratação quando aplicável; owner de engenharia + segurança para modelo/licença e acesso.
- **Engineering API:** consumer e contrato, baseline+fallback; **Core** live AuthZ, **Keycloak** identidade, **API DELPI** PDFs/BOM, **Engenharia** valida ground truth.
- **Não autorizado sem novo gate explícito:** mudar engine padrão, alterar arquitetura/owner, provisionar novos recursos pagos sem envelope aprovado, enviar PDFs a SaaS, writes/publicação, aumento arbitrário do host produtivo.
- Detectou-se mudança de autoridade/owner/bounded context? `ARCHITECTURE_DECISION_REQUIRED` e retornar Coordination.

## Plano R9.2 de execução
1. Ler `AGENTS.md`, authorities, docs 93–103, scripts existentes do SSH Operator e infra canônica. Verificar HEAD, origin/main, status, concorrência; usar worktree isolado e menor diff.
2. Inventariar infraestrutura e deployment contract. Dimensionar CPU/RAM/GPU/disco e quotas medindo pesos, RSS, carga inicial e inferência. 8GiB é hipótese, não meta garantida. Registrar orçamento, compliance, e acesso delegado.
3. Se existir capacidade aprovada, provisionar worker **separado** por processo SSH Operator/IaC oficial. Exigir ambiente com limites, health, logs sem secrets, no internet em runtime, modelo read-only verificado por checksum, volumes temporários com TTL, isolamento de falhas e autenticação serviço-a-serviço governada (sem JWT no OCR).
4. Instalar PP-StructureV3 e Docling **em imagens/venvs isolados** com versões, hashes, licenças e SBOM, modelos provisionados sem downloads em runtime; smoke em PDF sintético/público.
5. Ligar somente ao **harness de benchmark isolado**, não ao dispatcher produtivo, e aplicar `drawing_perception_candidate.v1`. Se um engine falhar, erro tipado/timeout/RESOURCE_BLOCKED; baseline continua ativa.
6. Corpus governado: `90264302`, `90264161`; páginas selecionadas em `90263554` (18p), `90264135` (13p), controle `90264094`; conferir SHA e seleção de folhas. Nenhum arquivo obtido por bypass de API DELPI.
7. Executar baseline, PPS-v3 e Docling nas mesmas páginas/condições ou estratificar hardware; armazenar dados normalizados, overlays restritos, métricas de tempo/p95/RSS, detecção de regiões, tabela/células/cotas, e failure reasons. Sem GT aprovado: `EVAL_PENDING`, sem precisão fabricada.
8. Somente após resultados, propor winner/fusion e executar shadow mode se já governado. Baseline nunca desligada nesta missão.
9. Exigir testes/contratos/AuthZ/egress e SHA verificável, benchmark reproducível, documentação em doc numerado 104+; deploy de **worker de laboratório** e código só dentro dos gates, não confundir health com E2E.
10. Separate production replacement decision: owner aprova candidato após relatório e canary/rollback; nenhuma troca sem autorização explícita de release, testes authenticated MCP e critérios de qualidade.

## Entregáveis e aceite
- Worker físico/lógico realmente provisionado **ou** `OWNER_BLOCKED/RESOURCE_BLOCKED` com razão e necessidade concreta.
- Ambiente isolado e manifesto verificável: host/id não sensível, imagem/digest, memory/CPU, dependências e models hash, health, teste de no-egress.
- Docling e PPS-v3 produzem outputs reais ou blockers comprovados separadamente.
- Matriz por documento/página com outputs/overlays, cobertura e benchmark comparativo.
- Sem deslocamento do source of truth, sem nova MCP tool e sem token de usuário no worker.
- Baseline produtiva preservada, rollback/feature flag preparado, SHA e testes.
- **Nunca afirmar que provisionamento/deploy aconteceu com base nesta autorização/documentação.**

**Relatório obrigatório:**
```
TASK: EVA.R9.2.DEDICATED.WORKER.PROVISION.BENCHMARK
USER_AUTHORIZATION: worker isolated approved 2026-11-02
INFRA_OWNER/FINOPS_GATE: / AUTHORITY_DECISIONS:
BASE_HEAD: / FINAL_HEAD: / TESTED_SHA:
WORKER_PROVISION_STATUS: PASS|OWNER_BLOCKED|RESOURCE_BLOCKED|TEST_NOT_RUN
WORKER_HOST_RESOURCES: / IMAGE_DIGEST: / MODEL_DIGESTS: / OFFLINE_EGRESS_TEST:
PP_STRUCTURE_RUN: / DOCLING_RUN: / BASELINE_RUN:
DOCUMENTS_AND_PAGES: / PDF_SHAS: / REGION_TABLE_CELL_METRICS:
GROUND_TRUTH_STATUS: / RESOURCE_PERFORMANCE: / SECURITY:
PRODUCTION_DEFAULT_UNCHANGED: / MCP_TOOL_COUNT: / ROLLBACK:
DEPLOYED_SHA: / SSH_OPERATOR_EVIDENCE: / MCP_E2E:
ARCHITECTURE_DECISION_REQUIRED: / BLOCKERS: / NEXT_STEP:
```
