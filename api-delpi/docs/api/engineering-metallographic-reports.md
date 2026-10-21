# Relatórios metalográficos — contrato implementado

Chamado Helpdesk **#1400**. Owner HTTP: serviço **`api-delpi`** existente, prefixo `/engineering/metallographic-reports`. Gateway: `/apps/api-delpi/engineering/metallographic-reports`.

`EXISTING_EQUIVALENT = NO` para CRUD de relatório metalográfico.  
`REUSE_DECISION = EXTEND` — schema `engineering` no PostgreSQL de plugins, volume de upload da api-delpi e PDF com ReportLab (já dependência). Não há API, container ou banco novos.

O MFE Metalografia DELPI consome este contrato em `/apps/metalography`. Não há BFF próprio: o plugin não tem API de módulo, e o CRUD permanece na api-delpi. A folha do MFE foi comparada ao HTML de referência no Chrome, com diferença zero na região da folha. O PDF desta API segue as coordenadas em milímetros desse HTML.

## Rotas

| Método | Caminho | operationId | Permissão |
|---|---|---|---|
| POST | `/engineering/metallographic-reports` | `engineering_create_metallographic_report` | `metalography.create` |
| GET | `/engineering/metallographic-reports` | `engineering_list_metallographic_reports` | `metalography.view` |
| GET | `/engineering/metallographic-reports/{report_id}` | `engineering_get_metallographic_report` | `metalography.view` |
| PATCH | `/engineering/metallographic-reports/{report_id}` | `engineering_update_metallographic_report` | `metalography.edit` |
| DELETE | `/engineering/metallographic-reports/{report_id}` | `engineering_delete_metallographic_report` | `metalography.delete` |
| POST | `/engineering/metallographic-reports/{report_id}/copies` | `engineering_copy_metallographic_report` | `metalography.create` |
| PUT | `/engineering/metallographic-reports/{report_id}/images/{slot}` | `engineering_put_metallographic_image` | `metalography.edit` |
| GET | `/engineering/metallographic-reports/{report_id}/images/{slot}` | `engineering_get_metallographic_image` | `metalography.view` |
| DELETE | `/engineering/metallographic-reports/{report_id}/images/{slot}` | `engineering_delete_metallographic_image` | `metalography.edit` |
| GET | `/engineering/metallographic-reports/{report_id}/pdf` | `engineering_export_metallographic_report_pdf` | `metalography.export` |

`report_id` é UUID. `slot` é `original` ou `measured`. O número `MET-{ano}-{sequência}` é gerado no servidor.

JSON de sucesso usa o envelope `api_delpi_success` (**HTTP 200**), com `meta.operationId` igual ao `operationId` do OpenAPI e `ETag` da versão nas respostas de um relatório. Imagem e PDF são binários (`image/jpeg` ou `image/png`, `application/pdf`) com `Cache-Control: private, no-store`.

## Diferenças em relação à proposta

| Proposta | Implementação |
|---|---|
| POST 201 e DELETE 204 sem corpo | HTTP 200 com envelope, como as demais rotas da api-delpi |
| 401/403 no envelope de domínio | 401/403 no corpo do `delpi_auth` (`detail`), padrão vigente |
| Filtro de número do relatório ausente na proposta | Query `report_number` (contém, sem diferenciar maiúsculas), exigido pelo chamado |
| Tamanho de imagem “a aprovar” | 8 MB e no máximo 6000 px por lado; JPEG e PNG; regravação para remover metadados |
| Data vazia no filtro de período | Se `report_date` for nula, o período usa a data de `created_at` em `America/Sao_Paulo` |
| Cópia com revisão “a validar” | A cópia nasce com revisão `00`, novo número, nova autoria e as duas micrografias |
| `analyst.user_id` institucional | Coluna existe; o cliente não envia identidade. A API grava `user_id` nulo |
| Registro das permissões no Core | Códigos declarados e cobrados na api-delpi. O Core recebe permissão de plugin pelo manifesto do MFE, que ficou fora desta entrega |
| 429 por rota | Não há limitador canônico por rota na api-delpi; não foi criado um limitador só desta coleção |
| Fidelidade visual ao HTML | HTML de referência em `docs/12-roadmap-e-evolucao/quality/reference/` (SHA-256 `13ba5eb7033afa616bf542ac6f7a6df5c67a0d318d2ea898caa4fb368220b820`). A folha do MFE coincidiu pixel a pixel nessa captura. O PDF usa a mesma composição em milímetros; a marca RASCUNHO continua só no rascunho |

## Persistência

Migration `api-delpi/migrations/plugins/engineering/V010__metallographic_reports.sql`.

- `engineering.metallographic_reports` — dados, versão otimista, exclusão lógica
- `engineering.metallographic_report_counters` — numeração transacional por ano
- `engineering.metallographic_report_images` — metadado das micrografias
- `engineering.metallographic_report_idempotency` — `Idempotency-Key` por ator e operação (`create`, `copy`)
- `engineering.metallographic_report_audit` — operação, ator e nomes de campos; sem texto de observações e sem binário

Binário: `METALLOGRAPHIC_IMAGE_UPLOAD_DIR` (default `/app/data/metallographic-images`), volume `${DELPI_DATA_HOST_DIR}/metallographic-images`.

`If-Match` é obrigatório em PATCH, DELETE e mutações de imagem. Ausência responde 428. Versão divergente responde 412. Replay da mesma chave e do mesmo conteúdo devolve o mesmo relatório. Chave reutilizada com outro conteúdo responde 409.

A exportação PDF não altera versão, revisão, status nem conclusão. Rascunho sai com a marca “RASCUNHO”. A API não calcula conformidade.

## Escopo de autorização

Quem tem a permissão correspondente enxerga o acervo. Não há recorte por filial nem por autor: o contrato do chamado não definiu esse eixo. Usuário sem a permissão recebe 403 mesmo conhecendo o UUID.

## O que esta entrega não faz

- MFE, manifesto, Ajuda in-app e registro das permissões no Core
- Deploy
- Importação de IndexedDB/localStorage
- Aprovação, assinatura ou publicação além de `draft`
