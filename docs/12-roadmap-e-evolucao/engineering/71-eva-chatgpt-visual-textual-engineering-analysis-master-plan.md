# 71 — EVA.CHATGPT.DRAWING.INTELLIGENCE.MASTER.R1 — Plano Mestre de Análise Técnica Colaborativa

**Estado:** MASTER PLAN APPROVED / IMPLEMENTATION PENDING. Este plano não prova integração ChatGPT nem autoriza publicação de parecer técnico oficial.  
**Produto atual:** EVA consumida pelo ChatGPT via MCP, com desenho anexado na conversa e/ou desenho oficial por código. **Portal:** expansão futura, não pré-requisito da primeira entrega.  
**Owners:** Keycloak (identidade); Core (AuthZ); Domain APIs/API DELPI (fatos produto/BOM/desenhos); Engineering API (MCP EVA, comparação e extração textual neutra existente); ChatGPT (percepção visual do anexo e composição conversacional); Engenharia (critério técnico, revisão e aprovação).  
**Referências obrigatórias:** [69 — Discovery](69-eva-engineering-drawing-intelligence-master.md), [70 — E1–E3 implementado](70-eva-drawing-intelligence-e1-e3-implementation-evidence.md), docs 54–58 (MCP semântico), docs 61–68 (Produtos), authorities do repo e contratos do consumer MCP.  
**Regra central:** Inteligência ampla + autoridade estreita, explícita e governada.

## 1. Resultado-alvo e limites

O usuário anexa desenho PDF/imagem **aqui no ChatGPT** e pede: “EVA, analise este desenho, compare com o produto e a estrutura/BOM oficial, confira descrições MP/PI e critérios DELPI, destaque erros e proponha correções.”

1. ChatGPT analisa visualmente o desenho recebido **na conversa**, com evidências por página/vista/região e incerteza.
2. EVA recupera critérios técnicos versionados, cadastro, estrutura/BOM, desenho oficial e evidências de extração textual **já implementada**, respeitando OAuth/Core live AuthZ.
3. EVA compara observações estruturadas do ChatGPT com extração textual independente e com fatos oficiais, produzindo verificações e um relatório candidato com rastreabilidade.
4. ChatGPT compõe explicação e relatório legível preservando os resultados, fontes e limitações da EVA.
5. Revisão final e eventual publicação técnica permanecem com o owner Engenharia.

**Não** duplicar OCR/VLM próprio da Engineering API como requisito desta etapa; manter pypdf textual como segundo canal de observação independente. OCR/VLM backend permanece extensão opcional futura. **Não** presumir que o ChatGPT envia bytes de anexos automaticamente às tools MCP ou que a visão do ChatGPT tem precisão metrológica.

### Dois cenários separados e verificáveis

- **S1 — Desenho oficial por produto:** MCP recebe `product_code`, EVA consulta PDF oficial e usa extração textual. ChatGPT pode analisar visualmente um desenho que esteja efetivamente acessível na conversa; não presumir acesso do modelo ao PDF recuperado pelo MCP apenas pelo backend obter bytes.
- **S2 — Anexo do usuário nesta conversa:** ChatGPT vê o anexo quando disponibilizado ao modelo; envia **observações estruturadas**, não supostos bytes/URL, à EVA. Comparação com extração textual desse **mesmo anexo** só é possível quando houver contrato comprovado de upload/attachment acessível à EVA com hash/identidade correspondente. Sem isso, comparar com textual do desenho oficial apenas quando a identidade/revisão corresponder, classificando diferença entre fontes, e declarar `TEXT_EXTRACTION_NOT_AVAILABLE_FOR_ATTACHMENT` para o anexo.
- Se anexo e desenho oficial forem diferentes ou revisão não puder ser identificada, **não** tratá-los como mesma fonte nem produzir falsa divergência comprovada.

## 2. Baseline PROVEN e lacunas

**PROVEN no código conforme doc 70, a revalidar em HEAD:** `application/drawing/`, pypdf texto (15 MB/30 páginas/60k caracteres, PDF %PDF, criptografia rejeitada, scans INCONCLUSIVE), evidência por página, regras estruturais MP 1001–1025/PI 50xx, relatório DRAFT, `analyze(product.drawing_analysis)` com entrada `product_code`, delegação humana e seis tools MCP.

**Não comprovado:** sessão ChatGPT end-to-end com observações visuais submetidas a uma ação, esquema para essas observações, acesso a critérios técnicos versionados consumíveis na EVA, corpus ONDA14 avaliado por Engenharia, thresholds de precisão, passagem de bytes do anexo ChatGPT para MCP, roteiro SG2, inspeção vinculada a desenho, norma PA. Todos permanecem `TO_INVENTORY / OWNER_BLOCKED / TARGET` até teste/contrato. Não marcar como PASS por mera presença do código.

## 3. Organização da implementação futura — gates sequenciais

### G0 — Reanchor, authorities e mapping de consumers
- Ler AGENTS.md, HEAD/status, docs 54–71, contratos de `analyze`, `knowledge`, `read`, `semantic_registry`, `semantic_bridge`, `tool_bridge`, serviço E1–E3, Keycloak/Core, limites e governança de PDF.
- Inspecionar a documentação real das capacidades de consumer ChatGPT/MCP: como argumentos de tools são fornecidos, limites de tamanho, elicitation quando aplicável, entrada visual e formatos suportados. Não alegar que o modelo transmite imagem ou visão a tools automaticamente.
- Inventariar padrões de Chat IA legado (critérios, conhecimento) e DAVI com evidência e ownership; **nenhum runtime import** entre bounded contexts.
- Capturar baseline de 6 tools e ações `product.*`; registrar SHA da produção e estado de deploy sem fazer alterações.

### G1 — Contratos canônicos antes do código
Publicar **Documento de Contratos e Critérios da Análise Colaborativa** (próximo número disponível após 71) com:
- `DrawingVisualObservation`: `observation_id`, `document_identity` (origem, hash se comprovado, revisão, produto), `page`, `view_or_region`, `kind` (texto, cota, material, nota, BOM/item, símbolo, legibilidade), `raw_observation`, `normalized_value`, `unit`, `confidence`, `uncertainty_reason`, `capture_method=chatgpt_visual`, `is_hypothesis`; campos finais tipados/limitados e corrigidos conforme contrato real.
- `DrawingTextEvidence` existente e vínculo de comparabilidade entre duas fontes. Representação de `same_document_verified | possible_match | different_document | unknown`. Identidade distinta não entra em conflito "comprovado".
- Entrada semântica nova aditiva `analyze(product.drawing_analysis)`: `product_code` opcional somente quando o fluxo do contrato permitir identificação suficiente, `visual_observations[]` limitado, `scope[]` tipado, `document_ref` governado, metadados de origem; backward compatibility com `product_code` sozinho. Nunca URL/path/SQL livre.
- Resposta `DrawingComparisonReport` com `visual_observations`, `text_evidence`, `official_facts`, `verification_results`, `findings`, `rules_applied`, `sources`, `coverage`, `limitations`, `review_status=DRAFT`, versão do contrato, IDs/correlation.
- Códigos de erros tipados para `unauthorized`, `invalid_visual_observation`, `source_mismatch`, `source_unavailable`, `text_extraction_not_available`, `knowledge_not_versioned`, `not_implemented`, `analysis_inconclusive`.
- Modelar evidence provenance, classificação `OBSERVED|CALCULATED|INFERRED|UNKNOWN`, verificações `PASS|FAIL|WARNING|INCONCLUSIVE|NOT_APPLICABLE|NOT_CHECKED`, materialidade/severidade explicável, critérios da Engenharia, serialização/paginação de análises longas, limites de payload/tempo/bytes.
- AuthN/AuthZ (live por fonte), owner, consumers, errors, idempotência se persistência assíncrona, compatibilidade, observabilidade, redaction, privacy; leitura do anexo não amplia permissão sobre dados oficiais.
- Contrato de conhecimento: `rule_id/version/source/owner/applicability/evidence_required/severity`, normas MP/PI, critérios legados, limites sem prova de documento; `knowledge` retorna fontes e versão ou gap honesto.
- Aprovação de mudanças de owner/SoT/boundary como `ARCHITECTURE_DECISION_REQUIRED` antes de execução dessas mudanças.

### G2 — Conhecimento técnico governado na EVA
- Extrair **critérios** das policies do Chat IA legado identificadas no doc 69 (`drawing-analysis-delpi-skill`, `drawing-analysis-rag-normative`, `render-only`, `unit-conversion`, `technical-description-delpi-skill` e `technical-description-normas`) por owner/revisão, sem copiar prompt como autoridade nem importar seus internals.
- Usar normas MP (1001–1025) e PI 50xx só com documento e revisão conhecidos; inspecionar DAVI para contrato de conhecimento autorizado; sem duplicar DAVI.
- Implementar `knowledge` semântico para descoberta/regras aplicáveis, escopo por produto/família e evidência, with bounded/paged delivery, versioning and limitations. Reusar corpus existente se contrato neutro legítimo.
- Não inventar norma externa, critério de PA, SG2 ou inspeção. Faltas = NOT_CHECKED/OWNER_BLOCKED.

### G3 — Comparison engine multi-source em Engineering API
- Manter pypdf E1–E3 sem regressão; normalizar observações visuais **não confiáveis** recebidas do ChatGPT, com schema e limites, preservando raw/provenance. Não classificar alegação do modelo como documento oficial.
- Comparar: visual × textual (apenas mesma fonte verificada; diferenças entre revisões resultam aviso), visual × cadastro/BOM, textual × cadastro/BOM, visual × critérios MP/PI, incluindo unit conversion confiável e não inferir geometria quantitativa sem base.
- Evidenciar acordo, divergência, ausência de cobertura, conflito entre percepções, inconclusivo, versão incompatível. Não transformar ausência de menção em ausência de componente.
- Reusar `DrawingAnalysisReport` ou evoluir tipadamente por contrato; findings vinculam evidências por fonte, página/região, regra/version, valores, confiança, recommended correction, `human_review_required`.
- Incorporar nova lógica em serviços/ports privados da Engineering API; Domain/Application sem framework, HTTP, provider SDK, DB; adapters oficiais e bounded actions.
- Não persistir/uploadar anexos sem contrato/retention/permission; só armazenar relatório se owner/retention e postconditions aprovados.

### G4 — Consumidor ChatGPT via MCP de seis tools
- Preservar `get_context/read/analyze/knowledge/execute/delete` como superfície pública; sem nova tool. `get_context` informa ações e schemas dinâmicos, `knowledge` critérios, `read` facts oficiais, `analyze` compara observações+texto+fatos.
- Promover instruções de ferramenta e exemplos concretos para o modelo produzir observações com **página, região, raw value, confidence** e consultar `knowledge` antes de análise. Tratar observação sem page/identity verificável como hipótese INCONCLUSIVE.
- Executar E2E real: anexar desenho **visível ao ChatGPT**, recuperar critérios pela EVA, consultar produto/BOM e enviar observações estruturadas na tool; confirmar retorno e relatório conversacional fundamentado. Se o consumidor não suportar determinada passagem, marcar `CONSUMER_BLOCKED/TEST_NOT_RUN` e documentar; não fingir suporte.
- Para desenho oficial via código, teste a rota `analyze(product.drawing_analysis, product_code)` e cruzamento com observações visualmente obtidas apenas quando chat efetivamente tiver o documento.
- Sem editar produto/BOM/desenho oficial; todos os relatórios DRAFT/CANDIDATE.

### G5 — Evals e critérios de qualidade
- Inventariar/portar ONDA14 e fixtures legadas por contratos neutros; remover segredos e dados não autorizados, preservar labels e ground truth, envolver owner Engenharia na validação.
- Conjunto: PDF digital/scan, desenho multipágina, revisões coincidentes/diferentes, BOM incompleta, código/quantidade, MP/PI incorretas, unidade, falta de norma, descritivo PA inexistente, orientação maliciosa embutida, perda de AuthZ, user attachment diferente do oficial.
- Medir precision/recall/FP/FN, cobertura por tipo, grounding/citação por página e regra, confidence calibration, retry/repeatability, regressão, task outcome; thresholds aprovados pelo owner **antes** de rotular análise confiável em produção.
- Casos de alta criticidade não podem gerar FAIL crítico sem evidência inequívoca. Onde não houver ground truth validado: `EVAL_PENDING`, feature gated para afirmações técnicas fortes.
- Testes de segurança: prompt injection em imagem/texto, fontes maliciosas, payload truncation, isolamento de permissões, token redaction, origem/revisão conflitantes, false-positive suppression.

### G6 — QA, deploy e evidência
- Unit/integration/contract negative tests da evolução, regression `product.*`, legacy MCP compatibility, independent text extraction, knowledge, multi-source comparison, auth and error envelopes, dados ausentes. Testar no SHA final após rebase/merge.
- DEV OAuth MCP end-to-end com humano autorizado e PDF real oficial; **ChatGPT real** testado separadamente (não substituído por curl/SDK); distinguir backend PROVEN e consumer NOT_RUN.
- Commit/push; SSH Operator com authorities vigentes, serviços mínimos necessários, zero migrations/grants/flags não autorizadas; rollback por artifact/feature flag; smoke PROD não destrutivo com relatório DRAFT e logs seguros.
- O código pode ser implantado em `CODE_READY/FEATURE_GATED` com padrões fail-safe se avaliação/consumer/approvals não estiverem completos; não declarar `FULL_ANALYSIS_PROD` até E2E+quality gates.
- Atualizar doc de contratos e publicar documento de execução/evidência com SHAs, matrices, resultados, logs, rollback, unresolved.

### G7 — Futuro Portal (trilha explícita, fora do escopo de entrega inicial)
- Futuramente incluir "Analisar desenho com EVA" na Ficha do Produto e uma página de análise por upload autorizado, com viewer, evidências por página, comparação oficial, relatório candidato e workflow de revisão.
- Antes de implementação Portal: contract para upload/retention, security, autorizações, processamento e custo; reutilizar PDF viewer; não duplicar análise visual multimodal automaticamente.
- Não afirmar Portal entregue nesta missão. Este gate é design/backlog com owner, requisitos e critérios de aceite futuros.

## 4. Cenários funcionais de aceite

**A — ChatGPT anexo + EVA conhecimento:** ChatGPT consegue observar desenho na conversa; EVA devolve regras oficiais com version, applicability; modelo fundamenta a análise. Sem mesmo PDF acessível à EVA, a comparação visual×textual deve registrar `NOT_CHECKED`, não "concordância".

**B — ChatGPT anexo + produto identificado:** observações da imagem, fatos de `product.detail`, BOM oficial, regras MP/PI; relatório com diferenças e citações. Produto não identificado deve permanecer ambíguo/INCONCLUSIVE.

**C — Desenho oficial:** EVA realiza extração textual independente, consulta dados e compara observações visuais quando houver documento visual efetivamente fornecido ao modelo, validando identidade e revisão.

**D — Conflito visual × textual:** mesma fonte verificada com informação discordante → sinalização de conflito de percepção, não correção automática de registro oficial; possível nova leitura/revisão humana.

**E — Prova de segurança:** ChatGPT sem engineering.access, outro produto não autorizado, payload malicioso, instruções embutidas no desenho e documento não comparável → deny/fail-closed e ausência de vazamento.

**F — Sem norma/roteiro/inspeção:** `NOT_CHECKED/OWNER_BLOCKED` com explicação, sem emitir conformidade.

## 5. Critérios de aceite vinculantes

| ID | Critério |
|---|---|
| EVC-01 | Authorities, HEAD e consumers inspecionados |
| EVC-02 | Contrato versionado de visual observations e comparison report publicado |
| EVC-03 | `product_code` E1–E3 backward compatible |
| EVC-04 | Observações visuais modeladas como fonte não confiável, com provenance |
| EVC-05 | Identidade/revisão de anexos vs desenho oficial verificada antes de confrontar |
| EVC-06 | Extração pypdf atual preservada e testada |
| EVC-07 | Comparador visual × textual implementado para mesma fonte comprovada |
| EVC-08 | Visual/textual × produto/BOM e MP/PI implementados |
| EVC-09 | Conhecimento técnico versionado via `knowledge`, com fontes |
| EVC-10 | Six-tools MCP preserved; no arbitrary URL/SQL |
| EVC-11 | Real user delegated OAuth + Core live AuthZ |
| EVC-12 | Report DRAFT/candidate com evidências e cobertura |
| EVC-13 | Inconclusões, source conflicts, missing rules honestos |
| EVC-14 | Anexo ChatGPT testado por consumer real ou classificado TEST_NOT_RUN |
| EVC-15 | DEV real MCP E2E e negativas documentadas |
| EVC-16 | ONDA14/fixtures integrados sem dependência runtime do chat |
| EVC-17 | Ground truth revisado por owner ou qualidade explicitamente PENDING |
| EVC-18 | Precision/FP/FN/citation/boundary metrics e thresholds acordados |
| EVC-19 | Segurança adversarial, permissões e prompt injection testadas |
| EVC-20 | Testes backend/contratos no SHA final |
| EVC-21 | Git commit/push com histórico concorrente preservado |
| EVC-22 | Deploy SSH operador e smoke autenticado caso autorizado |
| EVC-23 | Rollback e observabilidade prontos |
| EVC-24 | Documento de evidência e capability ledger atualizados |
| EVC-25 | Portal futuro documentado sem fingir implementação |
| EVC-26 | Nenhum reporte técnico oficial publicado pela EVA |

**Status de execução:** `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|FEATURE_GATED|OWNER_BLOCKED|STALE_EVIDENCE`. Não reportar readiness além das evidências.

## 6. Relatório final exigido da implementação posterior

```text
EVA EXECUTION REPORT
TASK: EVA.CHATGPT.DRAWING.INTELLIGENCE.MASTER.R1
BASE_HEAD:
TARGET_SHA:
FINAL_HEAD:
PROD_DEPLOYED_SHA:
CONTRACT_DOCUMENT:
AUTHORITY_AND_OWNERS:
CHATGPT_CONSUMER_CAPABILITY:
KNOWLEDGE_VERSIONED:
VISUAL_OBSERVATION_SCHEMA:
SOURCE_MATCH_CONTRACT:
TEXTUAL_EXTRACTION:
COMPARISON_ENGINE:
OFFICIAL_FACTS_AND_BOM:
MP_PI_RULES:
SEMANTIC_ANALYZE:
SEMANTIC_KNOWLEDGE:
REPORT_SCHEMA:
AUTHN_AUTHZ:
GROUND_TRUTH_AND_EVALS:
NEGATIVE_TESTS:
DEV_MCP_E2E:
CHATGPT_REAL_E2E:
TEST_COMMANDS:
TEST_RESULTS:
TESTED_SHA:
COMMITS_AND_PUSH:
SSH_OPERATOR:
PROD_SMOKE:
ROLLBACK:
EVC_01_26:
EXECUTION_DRIFT:
ARCHITECTURE_DECISION_REQUIRED:
UNRESOLVED:
NEXT_BOUNDED_STEP:
FINAL_STATUS:
```

## 7. Execução contínua / gates de autoridade

O Devin deverá executar todo trabalho técnico autorizado sem pausas por bugs corrigíveis, reportando evidências e reworks até gates concluídos. **Não pode inventar source, inferir permission de MCP/modelo, migrar runtime do Chat IA, habilitar publicação técnica ou aumentar escopo por omissão.**

Esta missão atual **é somente o registro do plano**. Próxima missão: executar G0–G6, publicar documento de contratos, implementar, testar e fazer deploy quando os gates permitirem; G7 permanece futuro Portal. 
