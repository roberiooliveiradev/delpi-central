# PR.IDENTITY.S1 — Resolução do solicitante via vínculo Core↔TOTVS

**Data:** 2026-10-23 · **Status:** PROVEN · **Página:** Solicitações de Compras (`/apps/supplies/purchase-requests`)

## Problema

A coluna **Solicitante** exibia o nome textual que vem do TOTVS (`C1_SOLICIT`/`USR_NOME` — ex.: "ELAINE"), não o nome oficial do usuário na Minha DELPI.

## Vínculo comprovado (fonte autorizada)

| Conceito | Valor |
|---|---|
| Identificador do solicitante na origem | `SC1.C1_USER` → `requester.protheus_user_id` (`USR_ID`) |
| Vínculo canônico | Core `user_protheus_identities` (`protheus_user_id` → `user_id`), apenas `mapping_status = "mapped"` |
| Contrato de resolução | `POST /integrations/protheus-identities/lookup` (S2S, batch ≤ 50 ids) |
| Nome oficial | `POST /me/directory/users/lookup` (Bearer do usuário, batch `ids[]` → `name`) |

Join determinístico: `protheus_user_id` exato → mapeamento `mapped` → nome Core. **Sem** similaridade de nome, fuzzy matching, e-mail ou inferência do usuário logado.

## Fluxo implementado

```text
purchase-requests-api (items[].requester / detail.requester + lines[].requester)
        ↓
supplies-api RequesterIdentityService
   1. coleta protheus_user_id distintos da página (dedup)
   2. POST /integrations/protheus-identities/lookup  (S2S, chunks de 50)
   3. POST /me/directory/users/lookup                (Bearer do usuário, ids únicos)
   4. injeta requester.display_name somente quando os dois hops resolvem
        ↓
plugins/supplies SuppliesPersonIdentity → display_name || name || code
```

## Propriedades

- **Sem N+1:** máximo 2 chamadas Core por página independente do número de linhas (dedup + batch; chunks de 50 quando > 50 solicitantes distintos).
- **Fallback honesto:** vínculo ausente, não-`mapped`, ambíguo ou Core indisponível → `display_name` ausente e a UI exibe `name`/`code` de origem. A listagem nunca falha por causa da resolução (soft-fail + warning).
- **Resposta minimizada:** apenas `display_name` é adicionado ao contrato público; `user_id` Core, e-mail e metadados do mapeamento não saem do BFF.
- **AuthZ preservada:** nenhuma permission nova; nenhum endpoint novo; universo de registros inalterado; falha de auth na Core não derruba a listagem.
- **Avatar coerente:** iniciais derivam do mesmo nome exibido (`SuppliesEntityAvatarLabel`).

## Contrato público (adição backward-compatible)

`requester.display_name` — `string | null` — nome oficial Minha DELPI quando o vínculo existe e resolve; ausente caso contrário. Campos `protheus_user_id`, `code`, `name` inalterados.

## Testes

- `supplies-api/tests/application/test_requester_identity.py` — 9 casos: resolução exata, múltiplos solicitantes, dedup, fallback sem vínculo, Core indisponível, resposta parcial, header+lines do detalhe, ausência de token, sem requester.
- `PurchaseRequests.structural.test.ts` — guard de preferência `display_name` e presença do campo no contrato MFE.
- Suítes completas verdes (backend e MFE) em ambos os HEADs do deploy.

## Arquivos

| Arquivo | Mudança |
|---|---|
| `supplies-api/app/application/services/requester_identity_service.py` | novo — composição da resolução |
| `supplies-api/app/interfaces/http/routes/purchase_requests_routes.py` | wiring lista + detalhe |
| `supplies-api/app/infrastructure/gateways/core_api_http_gateway.py` | `lookup_protheus_identities` (S2S batch) |
| `plugins/supplies/src/features/purchase-requests/types.ts` | `PersonRef.display_name` |
| `plugins/supplies/src/app/SuppliesDirectoryIdentity.tsx` | precedência `display_name` |
| `docs/12-roadmap-e-evolucao/solicitacoes-compras/01-contrato-api.md` | campo documentado |
| Help/manual | tooltip da coluna + Q&A "De onde vem o nome do solicitante?" |

## Evidência de produção (2026-10-23)

- Lista `/purchase-requests?branch=01&branch=02&page_size=20`: **20/20 itens com `display_name`** — latência ~0,90 s (baseline pré-mudança ~0,90 s; custo da resolução ≈ 0 perceptível).
- 3 solicitantes distintos resolvidos: `000304` "ELAINE"→"Elaine Gracielle Gracielle Romig", `000313` "ADRIANO C"→"Adriano de Placido de Carvalho", `000159` "YURI"→"Yuri Barbeito".
- Detalhe `/purchase-requests/01/178729`: `lines[].requester.display_name` resolvido em 0,17 s.
- Imagens: `infra-supplies-api@d32b749b4f3f` (healthy), `infra-supplies@148fe6253d02`; bundle `App-CF9eSRmv.js` com `display_name`.
- Logs `delpi-supplies-api`: zero warnings de lookup no smoke.

## Residual

- O diretório retorna `name` oficial; usuários desativados mapeados continuam exibindo o nome (o vínculo é histórico do registro — comportamento contratado, não filtrado).
- Facets/endpoint `/requesters` não são consumidos pelo MFE e não receberam enriquecimento nesta fatia.


## Revisão GPT — PR.IDENTITY.S1 (2026-10-23)

**Veredito:** `ACCEPT_WITH_RESIDUAL` em código e deploy técnico; `VISUAL_AUTHENTICATED=INCONCLUSIVE`. Inspecionados em GitHub o documento e o `RequesterIdentityService` na main após execução; 2 hops Core determinísticos por `protheus_user_id` (S2S de mapeamento e diretório com Bearer do usuário), `display_name` aditivo, origem preservada como fallback, sem matching por nome e sem Core IDs no contrato exibido. Fonte SC1 `C1_USER` documentada. Testes, smoke, latências e imagens são **reportados pelo executor**, não reexecutados pelo GPT.

**Evidência reportada:** 20/20 linhas da listagem com `display_name`, três solicitantes distintos reconciliados, detalhe com `lines[].requester.display_name`, tempo de listagem ~0,9s antes/depois, MFE 384 PASS e BFF suíte verde; deploy `b22ebec23e`. `VISUAL_AUTHENTICATED=TEST_NOT_RUN`: confirmar no navegador coluna + avatar, Cards, detalhe, paginação/F5 e nomes oficiais de diferentes solicitantes.

**Residuais de revisão:** (1) validar que falhas 401/403 do lookup de diretório não ampliam o universo de dados: o soft-fail de enriquecimento é aceitável **somente depois** de o BFF autorizar/listar as SCs com Core effective permissions, unidade/recurso e ownership; (2) o relatório diz '≤2 chamadas por página', válido quando até 50 usuários TOTVS distintos; para >50, o gateway faz chunks e o número de chamadas pode subir: ajustar alegações de performance à cardinalidade real; (3) verificar se name oficial retornado pelo diretório para usuário desativado é comportamento desejado do histórico; (4) conferir que documentação canônica da página permanece coerente com o HEAD e não promete enriquecimento do endpoint `/requesters` ainda não alterado.

**Gate formal:** `PR.IDENTITY.S1_CODE=ACCEPT_WITH_RESIDUAL`; `RUNTIME_API_SMOKE=PASS (executor-reported)`; `VISUAL=INCONCLUSIVE`. Não reabrir alteração de origem TOTVS nem acesso direto MFE→Core. Esta entrega não altera o bloqueio `X4.PROD-C1` aguardando Gabriel.
