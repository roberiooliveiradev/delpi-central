# Armazenamento persistente — anexos de chat e fontes de projeto

## Problema

Por padrão (sem Docker), a API grava uploads em `/tmp/minha-delpi-chat-attachments` e `/tmp/minha-delpi-chat-sources`. Dentro do container isso é **efêmero**: rebuild ou `docker compose up --force-recreate` apaga os bytes no disco.

Metadados (`ai_chat_attachments`, chunks RAG, `metadata.documentVision`) permanecem no Postgres — o download falha com «Attachment file is missing on storage» quando o arquivo sumiu.

## Solução (Docker)

O compose monta pastas **no host, fora do repositório**, em caminhos fixos dentro do container:

| Host (padrão) | Container | Variável |
|---------------|-----------|----------|
| `${DELPI_DATA_HOST_DIR:-$HOME/.delpi}/chat-attachments` | `/data/delpi/chat-attachments` | `CHAT_ATTACHMENT_STORAGE_PATH` |
| `${DELPI_DATA_HOST_DIR:-$HOME/.delpi}/chat-sources` | `/data/delpi/chat-sources` | `CHAT_SOURCE_STORAGE_PATH` |

Arquivos afetados: `infra/docker-compose.yml`, `infra/docker-compose.dev.yml`.

### Configuração

1. Copie o exemplo de env (`infra/.env.dev.example` ou `.env.prod.example`).
2. Opcional — pasta base no host:

```bash
# infra/.env
DELPI_DATA_HOST_DIR=/var/lib/delpi
# ou WSL/dev:
DELPI_DATA_HOST_DIR=${HOME}/.delpi
```

3. Recrie o serviço:

```bash
docker compose -f infra/docker-compose.yml up -d --force-recreate minha-delpi-ai-api
```

4. Verifique:

```bash
docker inspect delpi-minha-delpi-ai-api --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
docker exec delpi-minha-delpi-ai-api printenv CHAT_ATTACHMENT_STORAGE_PATH
```

## Layout no disco

### Anexos de sessão (`CreateChatAttachmentUseCase`)

```
{CHAT_ATTACHMENT_STORAGE_PATH}/{user_id}/{session_id}/{uuid}{ext}
```

Subpastas adicionais (mesma raiz):

- `drawing-library-cache/{product_code}/` — cache da biblioteca FILESERVER (`ChatDrawingLibraryService`).

### Fontes de projeto/agente (`ChatSourceFileStorage`)

```
{CHAT_SOURCE_STORAGE_PATH}/{user_id}/{scope}/{owner_id}/{uuid}{ext}
```

`scope`: `project`, `agent`, etc.

## Código de referência

| Componente | Caminho |
|------------|---------|
| Upload anexo | `app/application/use_cases/chat_attachments_use_cases.py` |
| Upload fonte | `app/application/use_cases/chat_sources_use_cases.py` |
| Download | `app/application/use_cases/download_chat_file_use_cases.py` |
| Cache desenho | `app/domain/services/chat_drawing_library_service.py` |

Fallback sem env: `/tmp/minha-delpi-chat-attachments` (adequado só para testes locais fora do Docker).

## Migração / anexos antigos

Registros gravados antes desta configuração apontam `storage_path` em `/tmp/...`. Esses arquivos **não** são migrados automaticamente — o usuário precisa reenviar o anexo.

Backup recomendado da pasta `${DELPI_DATA_HOST_DIR}` junto com dumps do Postgres em ambientes de homologação/produção.

## Documentação relacionada

- API REST (anexos/fontes): `docs/api/05-projetos-fontes-anexos-artefatos.md`
- Ambiente Docker: `infra/README-ambiente.md` § «Anexos e fontes persistentes»
- Biblioteca PDF (FILESERVER, outro volume): `api-delpi/docs/api/14-desenhos-pdf.md`
