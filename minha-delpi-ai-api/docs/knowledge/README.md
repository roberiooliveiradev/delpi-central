# Documentos para inteligência de agentes

Arquivos desta pasta são pensados para **ingestão na base de conhecimento** (`POST /knowledge/documents` ou upload no painel admin) e vinculação ao escopo RAG do agente.

## Documentos disponíveis

| Arquivo | Uso |
|---------|-----|
| [api-delpi-rotas-agente.md](./api-delpi-rotas-agente.md) | Agente com provider OpenAPI **api-delpi** — mapa intenção → rota, sinônimos e exemplos |

## Como anexar a um agente

1. **Admin → Conhecimento** — faça upload do `.md` ou cole o conteúdo em ingestão de texto.
2. Metadados sugeridos:
   - `tags`: `api-delpi`, `operacional`, `rotas`
   - `categories`: `operacional` (ou domínio do seu catálogo)
   - `namespaces`: conforme especialização do agente (ex.: `global:operacional`)
3. Na **especialização do agente**, inclua os `knowledgeTags` / `knowledgeCategories` que filtram esse documento.
4. Vincule o provider **api-delpi** ao agente e reimporte o OpenAPI após deploy.

O arquivo `app/domain/prompt_policies/api-delpi-routes.md` é injetado automaticamente no prompt quando uma ferramenta `execute_external_action` da API DELPI é executada (complementa o RAG).

## Atualização

Sempre que rotas ou `operationId` mudarem na api-delpi:

1. Deploy da api-delpi
2. Reimport OpenAPI no agente
3. Reindexar este documento na base de conhecimento
