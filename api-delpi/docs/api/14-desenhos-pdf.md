# Biblioteca de desenhos PDF (FILESERVER)

A api-delpi expõe os PDFs técnicos DELPI armazenados em pasta configurável no servidor de arquivos.

## Configuração

| Variável | Descrição | Default |
|----------|-----------|---------|
| `DRAWING_PDF_LIBRARY_DIR` | Diretório raiz dos PDFs | `/app/data/drawing-pdfs` |
| `DESENHOS_PDF_DIR` | Alias legado da variável acima | — |

### Homologação / dev (Docker)

No `infra/docker-compose.dev.yml`, a pasta local `minha-delpi-ai-api/desenhos` é montada em `/drawing-pdfs` (read-only).

Em produção, monte o compartilhamento do FILESERVER (ex.: `X:\DESENHOS DELPI EM PDF`) no mesmo path do container ou ajuste `DRAWING_PDF_LIBRARY_DIR`.

Exemplo WSL (quando `/mnt/x` estiver disponível):

```bash
export DRAWING_PDF_LIBRARY_DIR="/mnt/x/DESENHOS DELPI EM PDF"
```

## Rotas

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/products/{code}/drawing` | Metadados (filename, revisão, tamanho) |
| `GET` | `/products/{code}/drawing/pdf` | Download inline do PDF |

Permissão: `api-delpi.access` (`API_DELPI_ACCESS`).

## Convenção de arquivos

O resolvedor procura, nesta ordem de prioridade:

1. `{codigo}.pdf` — match exato
2. `{codigo_base}.pdf` — quando o código pedido tem sufixo variante
3. `{codigo_base}_R{NN}.pdf` — maior revisão numérica
4. `{codigo_base}-{N}.pdf` — variantes

Exemplos: `90262957.pdf`, `90261040_R10.pdf`, `90264227-1.pdf`.

## operationId

- `get_product_drawing` — envelope JSON (`product_drawing`, `scalar`)
- `get_product_drawing_pdf` — binário PDF (`product_drawing`, `document_export`)

## Integração com o Minha DELPI Chat

A skill **`drawing-analysis-delpi`** consome estas rotas quando o usuário pede análise de desenho **sem anexar PDF**, desde que informe o **código DELPI na mensagem** ou em chip de contexto (`userContextItems`).

| Etapa | Módulo (minha-delpi-ai-api) |
|-------|-----------------------------|
| Intent + gate de código | `ChatDrawingAnalysisTurnService` · `ChatDrawingProductCodeResolutionService.resolve_explicit_codes_without_attachment` |
| HTTP → api-delpi | `ChatDrawingLibraryService` (`DELPI_API_URL`, token do usuário ou `API_DELPI_INTERNAL_SERVICE_TOKEN`) |
| Cache local | `{CHAT_ATTACHMENT_STORAGE_PATH}/drawing-library-cache/{code}/` |
| Extração OCR | `ChatDocumentVisionTurnService.run_drawing_vision_from_storage_path` |
| Validação × API | `get_product_analyser` + `ChatDrawingValidationOrchestrationService` |

**Regras do chat (sem anexo):**

- Código **obrigatório** na mensagem ou em chip de contexto — não herda código do histórico.
- Vários códigos na mensagem (`90262957 e 90263489`): neste turno analisa o **primeiro** (cada PDF é por produto).
- PDF inexistente na biblioteca → resposta `drawingLibraryNotFound` em `drawing_query_intent.json`.

**Variáveis no container do chat** (`infra/docker-compose.dev.yml`):

| Variável | Uso |
|----------|-----|
| `DELPI_API_URL` | Base HTTP (ex.: `http://delpi-api-delpi:8000`) |
| `API_DELPI_INTERNAL_SERVICE_TOKEN` | Fallback server-to-server quando não há JWT do usuário |
| `CHAT_ATTACHMENT_STORAGE_PATH` | Raiz do cache `drawing-library-cache` |

Doc chat: [`minha-delpi-ai-api/docs/architecture/chat-pdf-document-extraction.md`](../../../minha-delpi-ai-api/docs/architecture/chat-pdf-document-extraction.md) · playbook: [`playbook_skill_analise_desenhos_delpi.md`](../../../minha-delpi-ai-api/docs/roadmap/melhorias/playbook_skill_analise_desenhos_delpi.md).

## Testes

```bash
# api-delpi
pytest api-delpi/tests/test_drawing_pdf_library_storage.py api-delpi/tests/test_product_drawing_routes.py -q

# chat (library + turn)
pytest minha-delpi-ai-api/tests/unit/domain/services/test_chat_drawing_library_service.py \
       minha-delpi-ai-api/tests/unit/domain/services/test_chat_drawing_analysis_turn_service.py -q
```
