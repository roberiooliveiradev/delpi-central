# 69 — EVA — Engineering Drawing Intelligence Master: Legacy Inventory, Technical Criteria, Data Contracts & Implementation Blueprint

**Status:** DISCOVERY CONSOLIDATED — contratos e critérios inventariados com evidência real; nenhuma capacidade nova habilitada.
**Data:** 2026-10-31. **Autoridade da missão:** EVA.ENGINEERING.INTELLIGENCE.DISCOVERY.R1.
**Base:** `14d6e26629` (main).

## 1. Objetivo e limites

Reunir, com rastreabilidade, a inteligência técnica legada de análise de desenhos/BOM/roteiros/descrições existente na Minha DELPI (Chat IA legado, DAVI, Engineering/api-delpi) e definir como ela compõe a inteligência de Engenharia da EVA — **sem** criar autoridade paralela, **sem** importar internals de outro bounded context, **sem** declarar aprovação técnica pela EVA.

## 2. Authorities e owners

- **Fatos/produtos/BOM/desenhos:** api-delpi (TOTVS/SB1/SG1) via Engineering API (delegation governada, `engineering_access`).
- **Identidade/permissões:** Keycloak + Core AuthZ; domain APIs.
- **EVA:** MCP semântico na Engineering API — 6 tools (`get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`), `semantic_registry.py` + `tool_bridge.py`.
- **Chat IA legado:** `minha-delpi-ai-api` — owner da inteligência conversacional; EVA **consome contratos neutros extraídos**, nunca internals.
- **DAVI:** especialista em dados/informações (docs `12-roadmap-e-evolucao/davi/`); EVA pode consumir conhecimento/contratos autorizados de DAVI sem duplicar autoridade.

## 3. Inventário — Chat IA legado (`minha-delpi-ai-api`) — PROVEN

### 3.1 Pipeline de visão de documentos/desenho
`app/application/services/chat_document_vision/` — pipeline staged real:
`document_vision_runtime`, `chat_document_vision_config_service`, `attachment_service`, `vlm_payload_service`, `pipeline_service`, `stage_service`, `facade_access`, `drawing_merge_service`, `chat_document_vision_service`, `turn_service`, `metrics_service`.
Gateways VLM: `infrastructure/llm/openai_compatible_vision_llm_gateway.py`, `ollama_vision_llm_gateway.py`; OCR runner `infrastructure/vision/document_vision_ocr_process_runner.py`; config `config/vision_llm_config.py`; exceções `domain/exceptions/vision_exceptions.py`.
**Regra técnica:** extração de PDF/imagem via pipeline própria do chat (OCR + VLM), com métricas e config por ambiente (`Dockerfile.vision.dev`, `requirements-vision.txt`).

### 3.2 Analisador de desenho (drawing analyser)
`chat_drawing_follow_up_service`, `chat_drawing_report_export_service`, `chat_drawing_metrics_service`, `chat_drawing_validation_assertiveness_metrics_service`, `chat_drawing_turn_enrichment_service`, `chat_drawing_library_attachment_service`, `chat_drawing_bom_vision_refinement_service`, `chat_drawing_extraction_llm_solve_service`, `chat_drawing_analyser_bom_confirmation_orchestration_service`, `chat_drawing_report_adjustment_turn_service`, `chat_drawing_follow_up_turn_service`, `chat_drawing_admin_debug_service`; domínio: `chat_drawing_validation_orchestration_service`, `chat_drawing_extraction_quality_retry_service`.
Admin use cases: `get_admin_drawing_analysis_summary_use_case`, `get_admin_document_vision_summary_use_case`.
**Regra técnica:** existe orquestração **desenho×BOM** (`bom_confirmation_orchestration`, `bom_vision_refinement`), métricas de assertividade, retry de qualidade de extração e anexos de biblioteca de desenhos.

### 3.3 Prompt policies (critérios técnicos extraíveis — `app/domain/prompt_policies/`)
| Policy | Critério contido |
|---|---|
| `drawing-analysis-delpi-skill` | análise de desenho DELPI (cotas, notas, materiais) |
| `drawing-analysis-rag-normative` | verificação normativa fundamentada em RAG |
| `drawing-analysis-render-only` | apresentação render-only (separação análise×render) |
| `drawing-analysis-unit-conversion` | conversão de unidades em cotas |
| `drawing-report-llm-fallback` | fallback de relatório LLM |
| `document-vision-delpi-skill` | leitura genérica de documentos |
| `technical-description-delpi-skill` + `technical-description-normas` | regras de descrição MP/PI (ver §7–8) |
| `company-knowledge-skill` | RAG `company-knowledge` (Normas_Tecnicas_DELPI.md) |

### 3.4 Suite de validação real (`scripts/`)
Homologação por produto real: `evaluate_drawing_90262008*.py`, `validate_drawing_90263149_live.py`, `smoke_drawing_90264227_live.py`, `onda14_desenhos_batch_validation.py`, `build_drawing_fixture_pdf.py`, `audit_drawing_library_assertiveness.py`, `audit_drawing_validation_registry.py`, `scan_drawing_false_criticals.py`, `run_drawing_analyser_bom_anchor_smoke.py`, `smoke_chat_multipage_drawing.py`, `test_desenhos_extraction.py`.
**Evidência:** existem corpus de desenhos (ONDA14), auditoria de falsos críticos e registro de validação — base pronta para ground truth.

### 3.5 Classificação para reuso na EVA
- **PROVEN e extraível por contrato neutro:** conceitos de pipeline PDF→OCR→VLM, modelo de relatório de análise, critérios de prompt (sem copiar prompts), corpus/fixtures de validação, orquestração desenho×BOM.
- **Não reutilizar direto:** internals de turno/chat (`chat_*_turn_service`), sessão, follow-up conversacional.

## 4. Inventário DAVI

- `docs/12-roadmap-e-evolucao/davi/` — trilha DAVI (domain exclusivo, governed knowledge); docs delia 137–184 cobrem acesso exclusivo ao domínio DAVI, boundary removal do provider direto, release authorization e produção.
- Branch histórica `feat/davi-product-vocabulary` — diretivas de vocabulário de produto para busca DAVI (TO_INVENTORY: status de merge).
- **TO_INVENTORY:** corpus real de conhecimento DAVI (matérias-primas/intermediários/acabados), owner do catálogo de regras e formato autorizado para consumo pela EVA.
- Boundary: EVA pode chamar capacidades DAVI via contrato, nunca internals.

## 5. Desenhos técnicos — fontes e formatos — PROVEN

- **api-delpi:** `product_drawing_routes.py` + use cases `get_product_drawing_metadata`, `get_product_drawing_pdf`, `list_product_drawings` + `drawing_pdf_library_storage` — PDF oficial do file server, metadados (filename, revision, variant_suffix, size, modified_at, media_type, found/message).
- **Engineering API:** façade delegada `/v1/products/{code}/drawing*` (metadados+PDF autenticados, blob servido ao MFE sem token em URL).
- **MFE:** `useFilePreviewLoader`+`FilePreviewView` (doc 66/68) — prova de entrega autenticada; não é análise.
- **Pipeline FONTE→EXTRAÇÃO→PERCEPÇÃO→ANÁLISE→CANDIDATO→REVISÃO→PUBLICAÇÃO:** fonte e extração já existentes; percepção/análise só no chat legado (§3); revisão/publicação = OWNER_BLOCKED (sem contrato WRITE de desenho).
- TO_INVENTORY: desenhos de cliente vs DELPI, biblioteca completa (`drawing_pdf_library_storage` — escopo do acervo), comparação de revisões.

## 6. Contratos de produtos/BOM — PROVEN

Engineering API: `GET /v1/products` (search: code/description/group_code CSV/subgroup/product_type CSV/customer_reference, sort/direction, paginação), `/v1/products/{code}` (view=engineering), `/structure` (BOM multinível), `/parents` (where-used), `/suppliers` (sem preço), `/drawing*`, `filter-options`. EVA `product.*` espelha via registry/tool_bridge.
Campos filtráveis BOM (items): code, description, type, unit, quantity, components[] — sem dedup entre ramos.

## 7. Regras de descrição — MATÉRIAS-PRIMAS (MP) — PROVEN

Fonte: `Normas_Tecnicas_DELPI.md` (RAG `company-knowledge`) + skill `technical-description-delpi`.
- Grupos **1001–1025**: terminais→1008, cabos→1001-1005, cabo PP→1006/1007, isoladores/insertos/conectores→1009, etiquetas/anilhas→1011, tubo isolante→1012, termoencolhível→1013/1050, prensa cabo→1015, resistor→1016, termistor→1025.
- Descrição = sequência canônica de campos por grupo (ITEM, MATERIAL, BITOLA, COR, BANHO, ISOLAÇÃO…); cor MP = 1ª+4ª letra (PT, BN; compostos VDAR, MRBN); veredito conforme/parcial/não conforme; proibido inventar bitola/norma/banho; subtipos de 1008 (PINO, FORQUILHA, ILHÓS, LINGUETA, FASTON, OLHAL, LUVA) cobertos pelo doc do grupo.

## 8. Regras de descrição — INTERMEDIÁRIOS (PI 50xx) — PROVEN

Fonte: `Understanding DELPI Intermediate Product Codes` (doc gpt/espelho + RAG).
Formato: `50xx xxxx xx xxx xxxx-xx/xx-xxxx-xxxx` — família 5021–5058 | sequência | isolação+bitola (**CA**=PVC, **CB**=EPR, **CF**=Silicone, **CT**=Teflon, **CV**=Especial; ex.: `CB1,50`) | cor **4 letras** (PRET, BRAN, VERD, AZUL) | comprimento mm | decape E/D mm | terminais+isoladores E/D (2 dígitos cada). Ex.: `50232222 CB1,50VERD-00255/06/06–6314–0111`.
Cor PI ≠ cor MP (4 letras vs abreviação curta).

## 9. Regras de descrição — PRODUTOS ACABADOS (PA 90xx) — PROVEN-como-ausência

**Não existe norma de descrição de PA na base autorizada** (a própria skill ordena declarar ausência e proíbe inventar checklist de PA). → OWNER_BLOCKED para validação de descrição PA; requer norma do owner Engenharia antes de qualquer critério.

## 10. Contratos de roteiros e inspeção — TO_INVENTORY / OWNER_BLOCKED

- **Roteiros produtivos (SG2/operações/postos/recursos):** nenhum contrato encontrado em engineering-api nem em `/v1/products*`. Não existe hoje consulta oficial de roteiro → capacidade pendente de Contract Gate com api-delpi/TOTVS. **Não inventar operações pela aparência do desenho.**
- **Inspeção:** plugins `inspecoes-entrada` e `inspecoes-processo` existem (bounded contexts próprios) — contratos de inspeção ligada a desenho/produto TO_INVENTORY (owner: qualidade). `api-delpi` tem services de `quality_labels` (certificado/audit) — insumo candidato.

## 11. Matriz desenho × dados oficiais (critérios-alvo)

| Verificação | Fonte desenho | Fonte oficial | Status |
|---|---|---|---|
| Componentes/códigos × BOM | tabela de itens do PDF | `/structure` | critério definível — PROVEN sources |
| Quantidades/unidades | BOM do desenho | SB1/SG1 qty+UM | idem |
| Revisão do desenho | bloco de revisão | `drawing metadata.revision`, `product.current_revision` | PROVEN |
| Descrição MP/PI | título/notas | normas §7–8 | PROVEN rules |
| Descrição PA | — | — | OWNER_BLOCKED |
| Roteiro | símbolos/processos | SG2 | OWNER_BLOCKED (sem contrato) |
| Normas aplicáveis | notas | Normas DELPI + externas | parcial — inventário de normas em §12 |

Classificações obrigatórias por informação: explícita / extraída-com-incerteza / oficial-BOM / divergência comprovada / divergência potencial / insuficiente. **Proibido** inferir ausência em BOM por ausência visual.

## 12. Normas e critérios técnicos — inventário

- **Internas PROVEN:** `Normas_Tecnicas_DELPI.md` (MP 1001–1025), doc de códigos intermediários 50xx — ambos já versionados na base RAG `company-knowledge`.
- **Externas:** nenhuma norma ISO/ABNT catalogada na base (TO_INVENTORY — owner Engenharia; não declarar conformidade sem documento+versão).
- Campo por critério (contrato alvo): id, título, versão, owner, família aplicável, condições, fonte, regra de verificação, evidência, severidade, limitações, ação recomendada, necessidade de aprovação.

## 13. Arquitetura-alvo na EVA (6 tools preservadas)

- `product.drawing`/`product.drawing_analysis` como **ações semânticas tipadas** novas em `semantic_registry` (read/analyze), NÃO nova tool MCP.
- Fluxo: anexo/referência do consumidor (com AuthZ) OU desenho oficial via `product.drawing` → extração (serviço neutro extraído do pipeline chat §3.1, owner definido) → análise (critérios §11–12) → relatório §14 → revisão humana.
- Boundaries: anexo do usuário ≠ autorização a dados de terceiros; limites de tamanho/páginas/timeout; auditoria+proveniência por página/região; INCERTEZA explícita (nunca confundir PDF localizado com análise concluída).
- Knowledge: `knowledge` tool passa a expor critérios/normas versionados (Normas DELPI, doc 50xx, catálogo de critérios §12) com source+versão.

## 14. Contrato de relatório técnico (alvo)

Identificação (produto/código/tipo/desenho/revisão/fonte/data/refs oficiais) → resumo executivo (escopo, verificações, resultados, limitações, riscos) → verificações (legibilidade, cotas, materiais/acabamento, BOM, descrições MP/PI/PA, roteiro, inspeções, normas, revisões, doc. obrigatória) → achados: {id, categoria, severidade, evidência localizada (página/região), regra aplicada+fonte, valor observado, valor esperado, diferença, confiança, correção recomendada, responsável validação}.
Evidências: `OBSERVED | CALCULATED | INFERRED | UNKNOWN`. Verificações: `PASS | FAIL | WARNING | INCONCLUSIVE | NOT_APPLICABLE | NOT_CHECKED`. Sem aprovação técnica pela EVA — artefato candidato a revisão humana.

## 15. Matriz de testes e ground truth

Corpus inicial já existente: scripts ONDA14 + produtos 90262008/90263149/90264227/90264258 + `build_drawing_fixture_pdf.py`. Cobrir: correto, info ausente, revisão divergente, BOM divergente, componente faltante, qty inconsistente, descrição MP/PI incorreta, roteiro divergente (quando contrato existir), norma inaplicável/sem revisão, desenho ilegível, PDF digital vs escaneado, multipágina, produto não identificado, usuário sem acesso à estrutura, **PDF com instruções maliciosas embutidas** (prompt injection). Métricas: precisão de achados, FP/FN, citação, boundary de permissão, utilidade. Ground truth validado por Engenharia.

## 16. Segurança e permission boundaries

Sem acesso a desenho/estrutura sem permissão efetiva backend; sem token em URL; sanitização de conteúdo de PDF (prompt injection indireta); limites de páginas/tamanho/timeout; auditoria de fonte e revisão; sem WRITE sem contrato; EVA não aprova, só reporta.

## 17. Gaps e OWNER_BLOCKED

1. **PA 90xx** sem norma de descrição → owner Engenharia (norma).
2. **Roteiros SG2** sem contrato → owner api-delpi/TOTVS (Contract Gate).
3. **Inspeção vinculada a desenho** → owner qualidade (contratos inspecoes-*).
4. **Serviço neutro de extração/análise** → extrair do pipeline chat legado (owner + adapter + testes — Abstraction Gate).
5. **Catálogo versionado de normas externas** → owner Engenharia.
6. **DAVI knowledge API** para EVA → contrato autorizado (TO_INVENTORY).

## 18. Sequência recomendada de implementação

E1. Contract Gate extração PDF→texto/imagem (serviço neutro extraído de §3.1, owner definido) + fixtures ONDA14 como corpus.
E2. Ação semântica `product.drawing_analysis` (read) — legibilidade/revisão/metadados × cadastro; relatório §14 mínimo.
E3. Desenho × BOM (componentes/qty/UM/revisão) com classificações §11; descrições MP/PI com normas §7–8.
E4. Contract Gates pendentes (PA norm, SG2 roteiro, inspeção) conforme owners.
E5. RAG de critérios versionados + evals de ground truth (precisão/FP/FN/citação) → homologação → rollout.

## 19. Critérios de aceite

- Nenhum critério sem fonte declarado PROVEN; divergências só com evidência página/região+regra.
- Zero internals legados importados; serviços extraídos por contrato neutro com testes.
- Relatório obedece §14 com classificações obrigatórias; sem aprovação técnica EVA.
- Evals com ground truth de Engenharia; segurança (injection, permissão) testada em caso próprio.
- Seis tools MCP preservadas.

## 20. Evidências, caminhos e commits

- Chat legado: `minha-delpi-ai-api/app/application/services/chat_document_vision/`, `chat_drawing_*`, `domain/prompt_policies/*`, `scripts/*drawing*`, `tests/`.
- Normas/regras: `prompt_policies/technical-description-delpi-skill.md`, `technical-description-normas.md`; RAG `company-knowledge` (`Normas_Tecnicas_DELPI.md`, doc intermediários 50xx).
- Contratos: `engineering-api/.../routes/product_routes.py`, `delegated_auxiliary.py`, `semantic_registry.py`, `tool_bridge.py`; `api-delpi/.../product_drawing_routes.py`, `use_cases/product/*drawing*`, `services/drawings/drawing_pdf_library_storage.py`.
- EVA: `engineering-api/.../eva/semantic_registry.py` (product.search/detail/structure/where_used/suppliers/drawing/history).
- DAVI: `docs/12-roadmap-e-evolucao/davi/`, trilha delia 137–184, branch `feat/davi-product-vocabulary`.
- Commits: este documento (push em main); referencial de UI/contratos `07c0815ea2` (doc 68).
