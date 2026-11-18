# Contrato REST candidato — product-suppliers (SA5)

Status: `PLANNED` — sujeito a ratificação (ver architecture-decision).
Sem handler implementado; `DLP04I02.PRW` = `SOURCE_NAME_AVAILABLE=INCONCLUSIVE`
(sem colisão no delpi-central/espelho; repo ERP não revalidado).
Nenhuma rota REST SA5 existe em 527/526 classes RESTALL (G0-B/C).

## Superfície conceitual

| Op | Verbo/path conceitual | Mecanismo | Estado |
|---|---|---|---|
| CREATE | `POST /v1/product-suppliers` | FWLoadModel('DMATA061') insert | candidato — VALIDAR TST01 |
| READ | `GET /v1/product-suppliers/{id}` | **fora do .PRW** — leitura api-delpi governada (estender FABR/FALOJA/REFGRD) ou via modelo | DECISION_REQUIRED |
| UPDATE | `PUT /v1/product-suppliers/{id}` | modelo — linha pela PK | candidato — VALIDAR TST01 |
| DELETE | `DELETE /v1/product-suppliers/{id}` | modelo — bloqueio do último vínculo pendente | BLOCKED até semântica+política |

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
Respostas no padrão `RETOBJ` `{code,message,detailedMessage,id}` +
HTTP 200/400 (erros oficiais via log do modelo, análogo a GetAutoGrLog —
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
