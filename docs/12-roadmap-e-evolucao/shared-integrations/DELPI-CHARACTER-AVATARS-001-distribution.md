# DELPI-CHARACTER-AVATARS-001 — Distribuição pública dos avatares oficiais

Status: implementado em código (sem deploy produtivo nesta execução).

## Decisões de produto

- **D01** — Distribuição pública aprovada para DAVI, CLARA, TÉO e VISTA
  (somente os retratos fictícios aprovados).
- **D02** — Arquitetura distribuída: cada API owner serve o próprio avatar.
- **D03** — Assets preservados: bytes intocados (sha256 provado).
- **D04** — Sem serviço central, sem registry, sem duplicação de arquivos.
- **D05 (R01)** — EVA: ficha e avatar existem no `engineering-api`;
  publicação pública **ratificada pelo PO** na revisão R01 — gate aberto.
- **D06** — Deploy produtivo não autorizado nesta task.

## Contrato HTTP

```text
GET /apps/<api>/public/characters/{character_id}/avatar/{versioned_filename}
```

| Especialista | Owner | URL pública alvo | Status |
|---|---|---|---|
| DAVI | api-delpi | `/apps/api-delpi/public/characters/davi/avatar/avatar-v1.png` | ATIVO |
| CLARA | controllership-finance-api | `/apps/controllership-finance-api/public/characters/clara/avatar/avatar-v1.jpg` | ATIVO |
| TÉO | transformometro-api | `/apps/transformometro-api/public/characters/teo/avatar/avatar-v2.png` | ATIVO |
| VISTA | tv-dashboard-api | `/apps/tv-dashboard-api/public/characters/vista/avatar/avatar-v2.jpg` | ATIVO |
| EVA | engineering-api | `/apps/engineering-api/public/characters/eva/avatar/avatar-v1.jpg` | ATIVO (R01) |

O prefixo `/public/` segue a convenção de superfície pública já existente
(`jwt_middleware` por API). O path canônico do brief (`/characters/...`)
foi ajustado para o padrão vigente da plataforma.

Política pública por owner (R01 — endurecimento da CLARA):
- api-delpi: prefixo `/public/characters/` em `_PUBLIC_PREFIXES`.
- controllership-finance-api: **allowlist exata** — apenas
  `/public/characters/clara/avatar/avatar-v1.jpg`; nenhum prefixo genérico.
- transformometro-api / tv-dashboard-api: convenção preexistente
  `PUBLIC_PREFIXES = ("/public/",)`.
- engineering-api: **allowlist exata** — apenas
  `/public/characters/eva/avatar/avatar-v1.jpg` (+ variante root_path).

## Controles de segurança (por owner)

- Mapeamento restrito: `character_id` deve ser o do especialista local e
  `filename` deve ser **idêntico** ao basename do `avatar_reference`
  declarado na ficha canônica — sem resolução de caminho arbitrária,
  sem directory listing, sem file server genérico.
- Publicação só ocorre se `appearance.avatar_status ==
  "OFFICIAL_AVATAR_APPROVED"`; qualquer outro caso responde 404.
- Versões substituídas (ex.: `teo/avatar-v1.png`) não são servidas (404).
- `X-Content-Type-Options: nosniff`; MIME derivado de mapa estático por
  extensão — nunca do conteúdo livre.
- Nenhum fallback: asset ausente/não aprovado → 404, nunca imagem genérica.
- AuthZ de negócio inalterada: a exceção pública é circunscrita ao prefixo
  `/public/characters/` no middleware do owner.

## Cache e versionamento

- `Cache-Control: public, max-age=300` (padrão da plataforma — mesmo do
  precedente `mural_acessos`).
- Filenames versionados (`avatar-vN`): nova versão = novo nome = nova URL.
- Conteúdo sob a mesma URL versionada é imutável; substituição exige novo
  arquivo versionado + atualização do `avatar_reference` na ficha.

## Integração com CharacterProfile

- `avatar_reference` permanece a referência canônica interna (path de
  pacote) — **não** é URL pública.
- Nenhuma mudança no contrato compartilhado `delpi_character_profiles`.
- Projeção da URL para consumidores (Nível 2 — descoberta) fica para
  decisão posterior (`DECISION_REQUIRED` se exigir bump de schema/projeção).

## Níveis de experiência ChatGPT (testados separadamente)

| Nível | Escopo | Estado |
|---|---|---|
| 1 — Distribuição | HTTP serve bytes oficiais | **PASS** (TestClient end-to-end por owner) |
| 2 — Descoberta | consumidor conhece a URL | TEST_NOT_RUN (depende de projeção/publicação) |
| 3 — Apresentação | ChatGPT renderiza a imagem | TEST_NOT_RUN (capability do provider) |

Ícone nativo do aplicativo ChatGPT é gerenciado pelo provider — fora de
escopo e sem promessa de integração automática.

## Evidências por especialista

| Campo | DAVI | CLARA | TÉO | VISTA | EVA |
|---|---|---|---|---|---|
| asset | `app/assets/characters/davi/avatar-v1.png` | `controllership_finance_app/assets/characters/clara/avatar-v1.jpg` | `tm_app/assets/characters/teo/avatar-v2.png` | `tv_app/content/characters/vista/avatar-v2.jpg` | `engineering_app/assets/characters/eva/avatar-v1.jpg` |
| container | `/app/app/...` | `/app/controllership_finance_app/...` | `/app/tm_app/...` | `/app/tv_app/...` | `/app/engineering_app/...` |
| MIME | image/png | image/jpeg | image/png | image/jpeg | image/jpeg |
| dimensões | 512×512 | 1024×1024 | 1024×1024 | 1024×1024 | 1024×1024 |
| sha256 | `94494e3a…b98e` | `967e79b8…140f` | `51f5bab4…8c8b` | `8d4879cc…d155` | `18d9e05f…e6fc` |
| aprovação | OFFICIAL_AVATAR_APPROVED | OFFICIAL_AVATAR_APPROVED | OFFICIAL_AVATAR_APPROVED | OFFICIAL_AVATAR_APPROVED | OFFICIAL_AVATAR_APPROVED |
| GET público | 200 + bytes idênticos | 200 + bytes idênticos | 200 + bytes idênticos | 200 + bytes idênticos | 200 + bytes idênticos |

## Procedimento de atualização / revogação

- **Atualizar avatar:** novo arquivo `avatar-vN+1` no diretório do owner +
  `avatar_version`/`reference` atualizados no content canônico + ficha
  derivada + testes → URL muda automaticamente (cache-bust por versão).
- **Revogar:** mudar `avatar_status` na ficha para status não aprovado →
  a rota passa a responder 404 imediatamente (ficha é a fonte única).
- **Nunca** editar bytes sob o mesmo filename publicado.

## Matriz de testes executada

| ID | Escopo | Resultado |
|---|---|---|
| T01–T04 | asset aprovado, GET 200, sha256 idêntico, MIME correto | PASS (5 owners) |
| T05–T07 | versão/character_id inválido, owner incorreto → 404 | PASS |
| T08 | path traversal (`../`, `..%2F`) → 404 | PASS |
| T09 | não aprovado → não publicado (gate por ficha) | PASS (EVA prova) |
| T10 | cache público + versionamento por filename | PASS |
| T11–T12 | AuthZ de negócio e contratos MCP intactos | PASS (regressão por owner) |
| T13 | gateway externo | TEST_NOT_RUN (deploy não autorizado) |
| T14–T15 | descoberta/render no ChatGPT | TEST_NOT_RUN |
| T16 | sem fallback genérico | PASS |
| T17 | EVA: publicação ratificada (R01) → serve bytes oficiais; allowlist exata; MCP/AuthZ intactos | PASS (200 + sha256; paths não autorizados → 401) |
