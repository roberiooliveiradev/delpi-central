# Contrato REST candidato — product-suppliers (SA5)

Status: `PROVEN_RUNTIME` (TST01 `:8701`, 2026-11-19) — `DLP04I02.PRW`
versão `0.7.1` tem o CRUD completo provado pelo modelo oficial
`MATA061` (fallback `DMATA061`), mesma cadeia headless do POST.
Nenhuma rota REST SA5 existe em 527/526 classes RESTALL (G0-B/C).

## Superfície conceitual

| Op | Verbo/path conceitual | Mecanismo | Estado |
|---|---|---|---|
| CREATE | `POST /v1/ProdForn/incluir` | FWLoadModel('MATA061') insert (fallback DMATA061) | **PROVEN_RUNTIME** TST01 2026-11-19 — POST gravou SA5 `10080010×999999/01`, read-back confirmou |
| READ | `GET /v1/ProdForn/consultar` | modelo — op VIEW: posiciona SA5 (índice 2) no produto, Activate, localiza a linha pela identidade, GetValue | **PROVEN_RUNTIME** TST01 `0.7.0`/`0.7.1` — 200 `data{}` completo; 404 correto pós-delete |
| UPDATE | `PUT /v1/ProdForn/alterar` | modelo — op UPDATE: mesma carga, GoLine na linha, SetValue só nos atributos editáveis | **PROVEN_RUNTIME** TST01 `0.7.0` — 200 + read-back `A5_NOMEFOR` alterado |
| DELETE | `DELETE /v1/ProdForn/excluir` | modelo — op UPDATE + `DeleteLine()` na linha | **PROVEN_RUNTIME** TST01 `0.7.0` — 200 + read-back ausência. **Limite oficial:** `a060VldGrv` rejeita modelo sem linhas ativas → último vínculo não removível (fail-closed por desenho; TO_INVENTORY) |

Identidade composta na rota: **não usar path único** — proposta:
`{product}` no path + `fornece/loja/fabr/faloja/refgrd` como query ou
subresource (`/v1/products/{B1_COD}/suppliers/{FORNECE}-{LOJA}-{FABR}-{FALOJA}[?refgrd=]`).
Formato final com a api-delpi facade — não embutir no `.PRW` decisão de
URI da superfície Python.

## Payloads (esboço sem dados reais)

CREATE/PUT body — identidade + atributos editáveis:
```json
{"A5_PRODUTO":"…","A5_FORNECE":"…","A5_LOJA":"…","A5_FABR":"…",
 "A5_FALOJA":"…","A5_REFGRD":"…","A5_NOMEFOR":"…","A5_CODPRF":"…",
 "A5_DESCPRF":"…"}
```
Respostas no padrão `RETOBJ` `{code,message,detailedMessage,id,errorType}` +
HTTP 200/400/500 — 4xx = rejeição determinística, 5xx = exceção interna ou
commit ambíguo (indeterminado). `id` carrega a tag de versão do fonte
(`dlp04i02-<versão>`). `errorType` segue o enum do sibling:
`client_error | official_validation | server_error | not_homologated`
(erros oficiais via log do modelo, análogo a GetAutoGrLog —
`VALIDAR NO TST01` a API de erro do MPFormModel).

## Regras de validação de entrada (fachada)
- Tipos estritos (mesma política do G2-A: N para numéricos, C para texto;
  ausente/nulo rejeitado; identidade completa obrigatória).
- Identidade imutável em UPDATE (campos de chave diferentes → rejeitar
  ou tratar como delete+create explícito — nunca silencioso).
- Sem preenchimento de identidade a partir de defaults inventados.

## Idempotência / timeout / authN-Z / auditoria
- Idempotência: ledger pré-envio na api-delpi + chave oficial completa +
  read-back — zero retry pós-timeout (playbook de escrita).
- AuthN Keycloak; `codusr` via Core — nunca do body. Gate OFF default +
  pin de ambiente (TST01/PRD) — mesma receita do product-master.
- Auditoria: caller-app no ledger; read-back pela chave integral
  (requer FABR/FALOJA/REFGRD projetados — gap G0-C).
- Confirmação pós-op: read-after-write pela PK completa; 2xx =
  `ACKNOWLEDGED`, não `CONFIRMED` sem read-back.

## READ — decisão de superfície (G2-B3, registro aditivo + atualização 0.7.0)

Decisão técnica aprovada para a superfície de **leitura** canônica:
adapter SQL read-only na `api-delpi`
(`ProductSuppliersRepository.get_supplier_link` + projeções aditivas de
`A5_FILIAL/A5_FABR/A5_FALOJA/A5_REFGRD`), compartilhando a seleção
governada de ambiente (`TOTVS_TARGET_ENV`).

**Atualização 0.7.x (PO 2026-11-19, pedido "CRUD completo no PRW") —
PROVEN_RUNTIME:** o `GET /v1/ProdForn/consultar` funciona na fachada
ADVPL **via modelo oficial** (operação VIEW + carga por posição de
alias + navegação da grade) — provado TST01 `:8701` (200 `data{}` em
vínculo real com `FABR`/`FALOJA` vazios, build `0.7.1`; 404 correto
pós-delete). A superfície SQL da api-delpi permanece a leitura
canônica para consumidores; o GET ADVPL existe para completude do
CRUD governado e evidência do mecanismo.
