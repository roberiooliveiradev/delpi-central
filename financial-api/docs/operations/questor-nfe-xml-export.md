# Exportação automática de XML de NF-e (Questor → Protheus)

## Objetivo

Eliminar o processo manual de baixar NF-e recebidas no Questor e copiá-las para a pasta lida pelo importador XML do Protheus.

Contrato desta integração:

```text
Questor
→ XML de NF-e modelo 55 válido
→ diretório local montado no container
→ importador do Protheus
```

O exporter não chama API do Protheus, não executa rotina, não grava SQL Server e não insere nota.

Filiais: `01` (Jaraguá do Sul) e `02` (Rio Bananal). Uma falha em uma filial não cancela a outra.

Documentos fora deste worker: NFS-e e CT-e.

Não depende de manifestação, ciência, confirmação, lançamento no Protheus, solicitação no Minha DELPI, fornecedor ou valor.

## Arquitetura

```text
financial_app/jobs/questor_nfe_xml_export.py
→ application/services/questor_nfe_xml_export_service.py
→ QuestorCompanySession da filial
→ GET /cliente/nfe/listagem
→ GET /cliente/transferenciaArquivo/download
→ parser NF-e
→ gravação atômica no diretório
→ ledger financial.questor_nfe_xml_exports
```

O processo HTTP do FastAPI não executa o loop. O worker usa a mesma imagem do `financial-api` e não publica porta.

O `document_id` público da NF-e continua sendo o `XmlFilename` usado pelo DANFE. O exporter guarda os dois identificadores do portal num DTO interno:

| Campo interno | Origem Questor | Uso no download |
|---|---|---|
| `provider_file_id` | `row.XmlFilename` | `Id` |
| `provider_entity_id` | `row.Id` | `IdEntity` |
| `access_key` | `row.Number` | nome `NFe-<chave>.xml` e validação do XML |

## Contrato Questor

`GET /cliente/transferenciaArquivo/download` é endpoint interno do portal Questor, identificado empiricamente. Não é API pública versionada.

```text
GET /cliente/transferenciaArquivo/download?Id=<XmlFilename>&IdEntity=<row.Id>
```

A listagem continua `GET /cliente/nfe/listagem` com `type=NFe-0`, `Entry=True` e `orderGroup=Emission`.

A sessão é a `QuestorCompanySession` da filial. Não há login, token ou cookie jar separado para o exporter.

A ordenação efetiva dessa listagem não está comprovada por teste, então o ciclo não interrompe ao ver uma página antiga. O `iTotalRecords` observado no portal também não é a contagem real: ele cresce com o offset (página 1 reporta 101, página 3 reporta 301). A paginação segue até uma página incompleta. `FIN_QUESTOR_NFE_EXPORT_MAX_PAGES` só evita um ciclo infinito; se estourar, a filial fica `truncated`.

## Corte fiscal

`FIN_QUESTOR_NFE_EXPORT_START_DATE=2026-10-02`

A comparação usa a data de emissão da NF-e no calendário `America/Sao_Paulo`.

- emissão anterior a 2026-10-02: ignorada, sem arquivo final;
- emissão em 2026-10-02 ou depois: candidata.

A listagem evita download de histórico já datado. Depois do download, a data dentro do XML é a validação final. Horário em UTC é convertido para São Paulo antes de extrair o dia. Data sem fuso é tratada como horário de São Paulo.

## Ledger e idempotência

Tabela `financial.questor_nfe_xml_exports`, chave única `access_key`.

Estados: `processing`, `success`, `failed`, `ignored`.

`success` não é exportado de novo, mesmo que o arquivo não esteja mais na pasta. O importador do Protheus pode consumir ou mover o XML. Arquivo ausente com ledger `success` não é falha.

Se o arquivo final existe e o ledger ainda não está `success`, o ciclo valida o arquivo e, se a chave e a data estiverem corretas, reconcilia para `success` sem gravar outra cópia. Isso cobre falha de banco depois do rename.

`failed` entra de novo no ciclo seguinte. Uma NF-e com falha não bloqueia as demais.

Dois workers ao mesmo tempo: `pg_try_advisory_lock` no início do ciclo. Se o lock não for obtido, o ciclo registra `status=skipped_lock` e encerra. A unique da chave é a segunda proteção. O lock é liberado em `finally`; se a conexão cair, o PostgreSQL solta o lock.

O banco não guarda XML, token, cookie ou sessão.

## Arquivo

Nome final, construído da chave validada:

```text
NFe-<44 dígitos>.xml
```

O `Content-Disposition` do Questor não define o nome.

Gravação no mesmo filesystem do destino:

```text
download completo
→ validação
→ .NFe-<chave>.<uuid>.part
→ flush + fsync
→ rename atômico
→ fsync do diretório
→ só então success no ledger
```

## Configuração

| Variável | Default | Função |
|---|---|---|
| `FIN_QUESTOR_NFE_EXPORT_ENABLED` | `false` | Liga o ciclo. Deploy não exporta sozinho. |
| `FIN_QUESTOR_NFE_EXPORT_DIR` | vazio no processo; `/exports/protheus-nfe` no container | Diretório absoluto, existente e gravável. |
| `FIN_QUESTOR_NFE_EXPORT_INTERVAL_SECONDS` | `900` | Espera do worker. Mínimo aceito quando ligado: 30. |
| `FIN_QUESTOR_NFE_EXPORT_START_DATE` | obrigatória quando ligado | `YYYY-MM-DD`. Operação: `2026-10-02`. |
| `FIN_QUESTOR_NFE_EXPORT_SCAN_PAGE_SIZE` | `100` | Página da listagem. |
| `FIN_QUESTOR_NFE_EXPORT_MAX_PAGES` | `1000` | Teto defensivo. |
| `FIN_QUESTOR_NFE_XML_MAX_BYTES` | `10485760` | Teto do XML. |

Também usa `FIN_QUESTOR_BASE_URL`, `FIN_QUESTOR_API_TOKEN`, `FIN_QUESTOR_COMPANY_01_ID`, `FIN_QUESTOR_COMPANY_02_ID`, `FIN_QUESTOR_TIMEOUT_SECONDS` e `PLUGINS_DB_*`.

Não há senha SMB, cliente SMB nem montagem CIFS no Python. A aplicação só enxerga o diretório do bind mount.

Com exportação ligada, o diretório precisa existir antes do processo. O worker não cria a pasta. Rejeita `/`, caminho relativo, diretório ausente e diretório da própria aplicação.

## Comandos

Um ciclo:

```bash
python -m financial_app.jobs.questor_nfe_xml_export run-once
```

Worker:

```bash
python -m financial_app.jobs.questor_nfe_xml_export worker
```

`run-once` encerra com 0 quando está desligado, quando o lock foi pulado, ou quando o ciclo terminou sem falha de filial/documento. Encerra com 1 se alguma filial ou NF-e falhou. Encerra com 2 se a configuração é inválida.

O worker em `ENABLED=false` permanece no ar sem baixar XML e encerra em SIGTERM/SIGINT. Com configuração inválida e exportação ligada, encerra com código 2.

## Desenvolvimento local

A pasta de smoke é `.local/nfe-export-smoke`, já coberta por `.local/` no `.gitignore`. O container a vê como `/exports/protheus-nfe`.

Não usar `/mnt/protheus-impxml` nem o UNC `\\192.168.1.231\d` na máquina local.

```bash
mkdir -p .local/nfe-export-smoke
docker compose -f infra/docker-compose.dev.yml --profile nfe-export run --rm \
  -e FIN_QUESTOR_NFE_EXPORT_ENABLED=true \
  financial-nfe-exporter \
  python -m financial_app.jobs.questor_nfe_xml_export run-once
```

O serviço `financial-nfe-exporter` está no profile `nfe-export`. O `up` local padrão não o inicia. `FIN_QUESTOR_NFE_EXPORT_ENABLED` continua `false` se a variável não for passada.

Sem credenciais Questor no ambiente local, o smoke ao vivo fica para o `srv-api`.

## Deploy no srv-api

Estes comandos não foram executados por esta implementação. Rodar no clone do servidor, depois do push.

1. Atualizar o código e construir a imagem:

```bash
git pull
docker compose -f infra/docker-compose.yml build financial-api financial-nfe-exporter
docker compose -f infra/docker-compose.yml up -d financial-api
```

2. Aplicar a migration `V002__questor_nfe_xml_exports.sql`:

```bash
docker exec delpi-financial-api python -m financial_app.infrastructure.persistence.migrations_runner status
docker exec delpi-financial-api python -m financial_app.infrastructure.persistence.migrations_runner up
```

3. Subir o exporter ainda desligado. O bind default do compose de produção é a pasta de teste, não `inn`:

```text
/mnt/protheus-impxml/Protheus/ProtheusData/impxml/delpi-test → /exports/protheus-nfe
```

```bash
docker compose -f infra/docker-compose.yml --profile nfe-export up -d financial-nfe-exporter
docker logs --tail 50 delpi-financial-nfe-exporter
```

O log esperado contém `status=disabled`.

## Smoke em delpi-test

Ainda no servidor, com o bind em `delpi-test`:

```bash
docker compose -f infra/docker-compose.yml --profile nfe-export run --rm \
  -e FIN_QUESTOR_NFE_EXPORT_ENABLED=true \
  financial-nfe-exporter \
  python -m financial_app.jobs.questor_nfe_xml_export run-once
```

Conferir na pasta de teste:

- só NF-e;
- nome `NFe-<chave>.xml`;
- emissão a partir de 2026-10-02;
- filiais 01 e 02;
- quantidade compatível com o Questor.

Rodar o mesmo `run-once` outra vez. Nenhuma chave com `success` pode gerar outro arquivo. O resumo deve mostrar `already_success` e `exported=0` para o que já entrou.

## Ativação em inn

Só depois do smoke aprovado:

```bash
FIN_QUESTOR_NFE_EXPORT_ENABLED=true \
FIN_QUESTOR_NFE_EXPORT_HOST_DIR=/mnt/protheus-impxml/Protheus/ProtheusData/impxml/inn \
docker compose -f infra/docker-compose.yml --profile nfe-export up -d --force-recreate financial-nfe-exporter
docker logs -f delpi-financial-nfe-exporter
```

O worker passa a repetir o ciclo a cada 900 segundos. O importador do Protheus continua dono do processamento.

## Rollback

Desligar só o exporter. Não é preciso parar `financial-api`, o portal, a API DELPI nem o Protheus.

```bash
FIN_QUESTOR_NFE_EXPORT_ENABLED=false \
docker compose -f infra/docker-compose.yml --profile nfe-export up -d --force-recreate financial-nfe-exporter
```

Ou parar apenas o container:

```bash
docker stop delpi-financial-nfe-exporter
```

## Troubleshooting

| Sintoma | Leitura |
|---|---|
| `status=disabled` | Exportação desligada. É o estado seguro. |
| `status=invalid_configuration` | Data inicial ausente, diretório inexistente, relativo, sem escrita, `/` ou dentro da aplicação. |
| `status=skipped_lock` | Outro ciclo ainda está com o advisory lock. |
| `status=truncated` | A listagem passou de `MAX_PAGES`. Nada foi marcado success sem ter sido visto; o próximo ciclo relê a janela. |
| `status=ignored reason=before_start_date` | Emissão fiscal anterior a 2026-10-02. |
| `error_code=access_key_mismatch` | Chave do XML diferente da listagem ou divergente dentro do XML. Arquivo final não é criado. |
| `status=reconcile_pending` | O XML foi renomeado e o ledger não chegou a `success`. O ciclo seguinte reconcilia se o arquivo ainda estiver válido. |
| `already_success` com pasta vazia | Esperado depois que o Protheus consome o XML. Não reexportar. |
| Filial `questor_unavailable` | Só essa filial falhou. A outra segue. O próximo ciclo tenta de novo. |
