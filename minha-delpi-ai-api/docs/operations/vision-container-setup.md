# Visão/OCR no container — minha-delpi-ai-api

## O que está habilitado por padrão (dev)

A imagem `Dockerfile.dev` instala:

| Camada | Pacotes |
|--------|---------|
| Sistema | `tesseract-ocr` (por+eng), `poppler-utils`, `libgl1`, `libgomp1` |
| Python base | `requirements.txt` (PyMuPDF, pytesseract, …) |
| Python visão | `requirements-vision.txt` — **EasyOCR**, **Docling** |

Na subida do container, o entrypoint **não** instala pacotes — apenas avisa se EasyOCR faltar. Instalação manual:

```bash
docker exec -e CHAT_VISION_EXTRAS_RUNTIME_INSTALL=true delpi-minha-delpi-ai-api sh /app/scripts/install_vision_extras.sh
```

## Motores OCR regional (desenho DELPI)

Config: `app/content/pt-BR/assistant/document_vision.json` → `pdfExtraction.regionOcr.engines`

```json
["tesseract", "easyocr", "paddleocr"]
```

| Motor | Uso | Módulo |
|-------|-----|--------|
| `tesseract` | Sempre (CPU) | `ChatPdfRegionOcrEngineService` |
| `easyocr` | Regiões carimbo/BOM — **habilitado no container dev** | idem |
| `paddleocr` | Opcional — descomente em `requirements-vision.txt` | idem |
| `docling` | Documento inteiro (`CHAT_DOCUMENT_VISION_BACKEND=docling`) | `ChatDocumentVisionService` |

Fusão multi-motor: `ChatPdfRegionOcrFusionService` (linhas com mais códigos de componente prevalecem).

## Variáveis de ambiente

| Variável | Default dev | Descrição |
|----------|-------------|-----------|
| `CHAT_VISION_EXTRAS_WARN` | `true` | Aviso no log se EasyOCR não estiver na imagem |
| `CHAT_VISION_EXTRAS_RUNTIME_INSTALL` | `false` | `true` só no script manual `install_vision_extras.sh` |
| `CHAT_DOCUMENT_VISION_ENABLED` | `true` | Master switch visão |
| `CHAT_DOCUMENT_VISION_BACKEND` | `auto` | `native`, `tesseract`, `docling`, `ollama_vlm`, … |
| `CHAT_DOCUMENT_VISION_TESSERACT_LANG` | `por+eng` | Idiomas Tesseract |

## Comandos

```bash
# Rebuild dev (primeira vez ou após alterar requirements-vision.txt)
cd infra
docker compose -f docker-compose.dev.yml --profile chat build minha-delpi-ai-api
docker compose -f docker-compose.dev.yml --profile chat up -d --force-recreate minha-delpi-ai-api

# Verificar motores no container
docker exec delpi-minha-delpi-ai-api python3 scripts/check_vision_profile_deps.py

# Teste live desenho
docker exec delpi-minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_chat_drawing_pdf_extraction_90264227_live.py -v

# Script manual (dentro do container)
docker exec delpi-minha-delpi-ai-api sh /app/scripts/install_vision_extras.sh
```

## Produção

`Dockerfile.prod` mantém extras opcionais via build arg:

```bash
INSTALL_VISION_EXTRAS=true docker compose -f infra/docker-compose.yml build minha-delpi-ai-api
```

Ou override: `infra/docker-compose.prod.vision.yml`.

## PaddleOCR (opcional)

Descomente em `requirements-vision.txt`:

```
paddlepaddle>=2.6.0
paddleocr>=2.7.0
```

Rebuild da imagem. Imagem significativamente maior; preferível em hosts com GPU.

## Referência arquitetural

- [chat-pdf-document-extraction.md](../architecture/chat-pdf-document-extraction.md)
- [playbook_skill_visao_documentos_ocr_delpi.md](../roadmap/melhorias/playbook_skill_visao_documentos_ocr_delpi.md)
