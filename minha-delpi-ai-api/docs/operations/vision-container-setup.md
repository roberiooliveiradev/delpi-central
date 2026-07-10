# Visão/OCR no container — minha-delpi-ai-api

## O que está habilitado por padrão (dev e prod)

As imagens `Dockerfile.dev` e `Dockerfile.prod` instalam **no build** (camada permanente da imagem):

| Camada | Pacotes / artefatos |
|--------|---------------------|
| Sistema | `tesseract-ocr` (por+eng), `poppler-utils`, `libgl1`, `libgomp1` |
| Python base | `requirements.txt` (PyMuPDF, pytesseract, …) |
| Python visão | `requirements-vision.txt` — **EasyOCR**, **Docling** |
| Modelos EasyOCR | Prefetch em `/opt/delpi-vision/easyocr` (`CHAT_EASYOCR_MODEL_DIR`) |

O build usa `scripts/docker_install_vision_extras.sh` e **falha** se EasyOCR não importar após o `pip install` — evita imagem cacheada sem extras.

Na subida do container, o entrypoint **não** instala pacotes — apenas avisa se EasyOCR ou modelos faltarem. Instalação manual (emergência):

```bash
docker exec -e CHAT_VISION_EXTRAS_RUNTIME_INSTALL=true delpi-minha-delpi-ai-api sh /app/scripts/install_vision_extras.sh
```

Rebuild recomendado (dev):

```bash
./minha-delpi-ai-api/scripts/build_vision_profile.sh dev
```

## Motores OCR regional (desenho DELPI)

Config: `app/content/pt-BR/assistant/document_vision.json` → `pdfExtraction.regionOcr.engines`

```json
["tesseract", "easyocr", "paddleocr"]
```

| Motor | Uso | Módulo |
|-------|-----|--------|
| `tesseract` | Sempre (CPU) | `ChatPdfRegionOcrEngineService` |
| `easyocr` | Regiões carimbo/BOM — **habilitado nas imagens dev e prod** | idem |
| `paddleocr` | Opcional — descomente em `requirements-vision.txt` | idem |
| `docling` | Documento inteiro (`CHAT_DOCUMENT_VISION_BACKEND=docling`) | `ChatDocumentVisionService` |

Fusão multi-motor: `ChatPdfRegionOcrFusionService` — regiões gerais mesclam linhas únicas; **BOM** usa `fuse_bom` (`tesseract`+`easyocr`, pesos em `document_vision.json` → `regionOcr.bomFusion`) e voto por dígito com confiança OCR.

## Variáveis de ambiente

| Variável | Default dev | Descrição |
|----------|-------------|-----------|
| `CHAT_VISION_EXTRAS_WARN` | `true` | Aviso no log se EasyOCR não estiver na imagem |
| `CHAT_EASYOCR_MODEL_DIR` | `/opt/delpi-vision/easyocr` | Pesos EasyOCR prefetch no build |
| `CHAT_VISION_EXTRAS_RUNTIME_INSTALL` | `false` | `true` só no script manual `install_vision_extras.sh` |
| `CHAT_DOCUMENT_VISION_ENABLED` | `true` | Master switch visão |
| `CHAT_DOCUMENT_VISION_BACKEND` | `auto` | `native`, `tesseract`, `docling`, `ollama_vlm`, … |
| `CHAT_DOCUMENT_VISION_TESSERACT_LANG` | `por+eng` | Idiomas Tesseract |
| `CHAT_EASYOCR_ENABLED` | `true` | `false` desliga EasyOCR (BOM e tentativa 5 usam só Tesseract) |

## Comandos

```bash
# Rebuild dev (primeira vez ou após alterar requirements-vision.txt)
./minha-delpi-ai-api/scripts/build_vision_profile.sh dev

# Ou manualmente:
cd infra
docker compose -f docker-compose.dev.yml --profile chat build --no-cache minha-delpi-ai-api
docker compose -f docker-compose.dev.yml --profile chat up -d --force-recreate minha-delpi-ai-api

# Verificar motores e modelos no container
docker exec delpi-minha-delpi-ai-api python3 scripts/check_vision_profile_deps.py --require-easyocr --require-easyocr-models

# Teste live desenho
docker exec delpi-minha-delpi-ai-api pytest \
  tests/unit/domain/services/test_chat_drawing_pdf_extraction_90264227_live.py -v

# Script manual (dentro do container)
docker exec delpi-minha-delpi-ai-api sh /app/scripts/install_vision_extras.sh
```

## Produção

`Dockerfile.prod` e `infra/docker-compose.yml` fixam `INSTALL_VISION_EXTRAS=true` — mesmo pipeline do dev (`docker_install_vision_extras.sh`, PyTorch CPU, prefetch EasyOCR, build falha se incompleto).

Para imagem **mínima** (sem EasyOCR/Docling), passe explicitamente no build:

```bash
docker compose -f infra/docker-compose.yml build --build-arg INSTALL_VISION_EXTRAS=false minha-delpi-ai-api
```

### Servidor — verificar antes de instalar

Sempre verifique se os pacotes já estão na imagem **antes** de rebuildar:

```bash
docker exec delpi-minha-delpi-ai-api python3 scripts/check_vision_profile_deps.py
```

Saída esperada quando **nada falta**:

```
OK tesseract
OK easyocr
OK docling
SKIP paddleocr (não instalado)
OK easyocr models (N arquivo(s) em /opt/delpi-vision/easyocr)
OK pytesseract
```

Verificação estrita (exit `1` se faltar EasyOCR ou modelos):

```bash
docker exec delpi-minha-delpi-ai-api python3 scripts/check_vision_profile_deps.py \
  --require-easyocr --require-easyocr-models
echo "exit=$?"
```

| Resultado | Ação |
|-----------|------|
| `exit=0` | Nada a fazer |
| `SKIP easyocr` ou modelos ausentes | Rebuild com visão (abaixo) |
| `⚠️ EasyOCR ausente` nos logs do entrypoint | Imagem buildada sem `requirements-vision.txt` |

### Servidor — instalar na imagem (recomendado)

Instalação **permanente** — sobrevive a `docker compose up --force-recreate`:

```bash
# Na raiz do repositório no servidor
./minha-delpi-ai-api/scripts/build_vision_profile.sh prod
```

Equivalente manual:

```bash
cd infra
docker compose -f docker-compose.yml build minha-delpi-ai-api
docker compose -f docker-compose.yml up -d --force-recreate minha-delpi-ai-api

docker exec delpi-minha-delpi-ai-api python3 scripts/check_vision_profile_deps.py \
  --require-easyocr --require-easyocr-models
```

Build leva ~5–10 min (torch, EasyOCR, Docling, prefetch dos pesos em `/opt/delpi-vision/easyocr`).

Variáveis úteis no `.env` do servidor:

```env
CHAT_DOCUMENT_VISION_ENABLED=true
CHAT_DOCUMENT_VISION_BACKEND=auto
CHAT_EASYOCR_MODEL_DIR=/opt/delpi-vision/easyocr
```

### Servidor — emergência (sem rebuild)

**Não recomendado em produção** — pacotes ficam só no filesystem do container atual:

```bash
docker exec -e CHAT_VISION_EXTRAS_RUNTIME_INSTALL=true \
  delpi-minha-delpi-ai-api bash /app/scripts/install_vision_extras.sh
```

O script é idempotente: pula `pip install` se `easyocr` já importar; roda prefetch de modelos se necessário.

Override legado: `infra/docker-compose.prod.vision.yml` (redundante desde jun/2026).

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
