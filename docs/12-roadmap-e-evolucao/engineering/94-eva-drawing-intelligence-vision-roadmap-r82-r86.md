# 94 — EVA Drawing Intelligence: visão e roadmap governado R8.2–R8.6

**Estado:** PLANNED. **Data:** 2026-11-01. **Coordination:** EVA/Portal Engenharia. **Owners:** Engineering API (interpretação), API DELPI (PDF e produto/BOM autorizados), Core (RBAC), Engenharia DELPI (validação).

## Princípio
Não é necessário empregar LLM para todas as etapas. Usar primeiro técnicas determinísticas e visão computacional já disponíveis: PDFium, PaddleOCR, OpenCV, extração vetorial quando o contrato suportar, coordenadas, regras contextuais e comparações governadas. A interpretação de **qualquer PDF sem erros não é garantível**; ambiguidade, abstention e cobertura parcial são resultados válidos. Modelos treinados de layout, detecção de símbolos ou VLMs são **candidatos de avaliação futura**, não infraestrutura já comprovada nem permissão de enviar desenhos a SaaS.

Pipeline candidato: PDF oficial delegado → percepção visual/textual → segmentação de regiões → estrutura de células/campos → relações técnicas → mapa técnico candidato por folha → comparação com dados oficiais → revisão/validação Engenharia. `drawing_understanding.v1` continua DRAFT/CANDIDATE; desenhos/estrutura/BOM/revisões oficiais mantêm seu owner. Seis tools MCP, análise em `analyze`.

## Etapas sequenciais

| Etapa | Escopo | Produto verificável | Pré-requisito/gate |
|---|---|---|---|
| **R8.2 (AGORA)** | Layout-aware region boundaries; carimbo/tabela/histórico/notas/área gráfica; ownership dos tokens; reconstrução restrita à região; comparações BOM fail-closed | `drawing_understanding` sem contaminação cross-region em `90264302`; evidência real e métricas de regressão | Doc 93 + doc 95; sem novo LLM |
| **R8.3** | Cobertura multipágina, página/folha, detecção de revisão/carimbo por página, OCR seletivo governado | resultados e cobertura explícitos em `90263554` (18p) e `90264135` (13p), sem fingir OCR de 31 páginas | Limites de memória/CPU e autorização; `partial` honesto |
| **R8.4** | Símbolos: balões de itens, linhas de chamada, setas, linhas de cota/extensão, vistas, tolerâncias, símbolos geométricos | candidatos espaciais com bbox/polígonos e vínculos justificados | GT por owner; avaliação comparativa de métodos |
| **R8.5** | Grafo técnico de evidências: folha→região→elemento→relação→BOM/cadastro oficiais | artefato candidato versionado com provenance, alternativas e revisão | Sem novo source of truth / bounded context implícito |
| **R8.6** | Avaliação de qualidade e workflow governado de revisão técnica; corpus holdout/variações; métricas | GT aprovado por Engenharia + precisão/recall por tarefa, falhas e regressões | Owner técnico, autorização do acervo |

## Corpus oficial prioritário (consultado pela EVA, identidade delegada)

- `90263554.pdf` — 18 páginas confirmadas por pypdf/pdfplumber/PDFium; 6.202.644 bytes; SHA histórico `89f9b4d574c8c1dbae2d87315e47743b4a75d36279581b7e0d2ef24b149c4f4d`.
- `90264135.pdf` — 13 páginas confirmadas pelos mesmos extratores; 4.434.155 bytes, produto acabado CHICOTE - P66.
- `90264302.pdf` — 1 página; baseline com carimbo `REV: 00`, códigos `50226113`, `50226114`, `10020033`, `10080106`, cotas OCR `643±2` / `663±2`; mistura de tabela com carimbo e referência de cliente/OV na resposta R8.1.
- `90264161.pdf` e `90264094.pdf` — controles `9026`, 1 página cada.
- `10210267-2.pdf` — controle escaneado **secundário**, não representa corpus principal de produtos acabados.

Inventário adicional: catálogo pesquisado por `9026` retornou 4.306 cadastros, **não** contagem de PDFs. Preferir `9026` e confirmar documento/permissão pela API oficial; tamanhos não inferem page count. Nunca varrer acervo indiscriminadamente.

## Regras comuns de engenharia e segurança

- Keycloak identidade, Core autorização live, API DELPI dados/documentos, Engineering API interpretação, owner Engenharia valida; MCP/A2A são interfaces, não authority.
- Sem credenciais, URLs arbitrárias, paths/arquivos de filesystem fornecidos pelo cliente, payloads de modelo não autorizados, envios SaaS, mutações ou publicação.
- Guardar `document_sha256`, página, região, token/linha/célula, método, provider, versão, coordenadas, evidências, limitações e `DRAFT`.
- `OCR confidence != association confidence != technical validation`. Ausência em OCR não prova ausência no desenho.
- Preserve `drawing_analysis.v3`, benchmark textual/visual e ENG-REV-001.
- Multiplas páginas: document count, pages seen/rendered/OCR/understood e amostragem; no global claims from partial coverage.
- Testar no SHA, regressões/autorizações, deploy governado e E2E autenticado pelo MCP. Reportar `PASS | FAIL | TEST_NOT_RUN | INCONCLUSIVE | OWNER_BLOCKED | FEATURE_GATED | STALE_EVIDENCE`.
- Avaliar modelos multimodais apenas após testes comparativos e autorização de privacy/infra/GT. Nunca prometer leitura total de qualquer PDF.

## Referências / próximos artefatos
- Doc 93: plano R8.2 e evidências reais por produto.
- Doc 95: missão executável R8.2 com aceite e relatório.
- Após execução: novo documento de evidência real, sem sobrescrever históricos.
- R8.3–R8.6 são `PLANNED`, não código entregue; criar missões detalhadas separadas após fechar cada gate.
