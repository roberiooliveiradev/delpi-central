# SUPPLIES-ENRICHMENT-01 — decisão MVP BrasilAPI CNPJ (2026-10-22)

> **Decisão do Product Owner: APPROVED FOR IMPLEMENTATION, etapa bounded S3.1 BrasilAPI.** Primeiro tornar a consulta CNPJ assistida funcional via BrasilAPI; Serpro permanece opção futura e não bloqueia o MVP. Este registro de decisão não substitui gates de segurança, runtime, feature, documentação canônica nem autoriza PUT Protheus. Rebaseline no HEAD antes do diff.

## Contexto comprovado
- S1 domain/comparison aceito, source SHA reportado `aeb4e18b20`.
- S2 reviews/decisions persistentes e V003 de idempotência por operação aceitos em código com residual, source SHA reportado `f68b1e2604`. Runtime federado/produtivo não validado.
- S3 inventário público Serpro documentado em `supplies-api/docs/supplier-enrichment-company-registry-inventory.md`, source SHA reportado `cd5ca80bf8`; `CONTRACT_FREEZE=INCONCLUSIVE` por ausência de evidência de contratação pela DELPI.
- `UnavailableCompanyRegistryProvider` é o adapter fail-closed atual; criação de review devolve 503 enquanto indisponível.
- A política institucional LGPD e o ROPA existem; enquadramento específico, prazo final, eventual endosso DPO e política para registros de consulta permanecem residuais.
- O `api-delpi` possui proveniência v1, mas não aceita ainda `THIRD_PARTY_API` ou modo de sugestão externa como gravação comprovada.
- DOCUMENTATION: BrasilAPI CNPJ endpoint público `GET https://brasilapi.com.br/api/cnpj/v1/{cnpj}`, fonte de dados intermediária Minha Receita; contrato no GitHub: https://github.com/BrasilAPI/BrasilAPI/blob/main/pages/docs/doc/cnpj.json; documentação https://brasilapi.com.br/docs.
- CNPJ endpoint pode retornar informação de QSA e pessoa natural: resposta externa precisa de allowlist e minimização em backend. A documentação atual também aceita CNPJ alfanumérico, ao passo que o domínio S1 foi construído para CNPJ numérico; validar escopo e reportar incompatibilidade em vez de alterar proteção de identidade silenciosamente.
- A API pública pode aplicar mitigação/rate limiting sem SLA. Evidência comunitária: https://github.com/BrasilAPI/BrasilAPI/issues/835 . Não contornar controles anti-bot.

## Decisão vinculante
1. **Fonte MVP = BrasilAPI CNPJ v1** por consulta sob demanda, para comparação cadastral assistida. É **provedor intermediário comunitário**, não sistema oficial Receita/Serpro. `provider_id=brasilapi-cnpj-v1`; `source_type=THIRD_PARTY_API` como conceito de evidência, nunca `GOVERNMENT_API`.
2. **Serpro = FUTURE/OPTIONAL**, condicionado à contratação. A falta de Serpro não bloqueia adapter BrasilAPI, testes ou entrega incremental desta task.
3. O fluxo MVP: MFE→`supplies-api`→GET canônico `api-delpi` + GET BrasilAPI → normalização allowlisted para `ExternalRegistrySnapshot`→engine S1→review S2→decisões usuário→`prepare-update` **draft only**. Sem writes automáticos ou manuais originados da sugestão externa nessa etapa.
4. Reusar contrato/rota `POST /suppliers/{code}/{store}/enrichment-reviews`; não permitir que browser injete snapshot, actor ou fonte. Browser não chama BrasilAPI diretamente.
5. Configuração via `COMPANY_REGISTRY_PROVIDER=unavailable|brasilapi`, com default `unavailable`, switch independente de gates TOTVS; ativação mediante ambiente autorizado e smoke controlado.
6. Falhas explícitas e fail-closed: 400/404/429/5xx, timeout, response parcial/inválida, mismatch de CNPJ, PII em payload inesperado. Zero escrita, nenhuma inferência de sucesso de ERP. TTL/cache/retry definidos conforme termos de uso e sem burlar rate limiting.
7. Campos de QSA/sócios/CPF e informações pessoais não entram em projeção, persistência ou logs. Telefone/email potencialmente pessoais exigem filtragem e revisão conforme ROPA. Nenhum raw payload salvo.
8. `X-Request-Tag` do Serpro **não** se aplica à BrasilAPI; não transportar pressupostos de billing/autenticação Serpro ao adapter BrasilAPI.
9. Não criar permissions por endpoint/botão; Core continua authority efetiva. Ownership de reviews por ator preservado, unit scope residual explícito.
10. Se prova nova invalidar source/mapping/terms, classificar `EXECUTION_DRIFT`. Nenhum contorno via scraping, proxy clandestino ou trocar endpoint silenciosamente.

## Gates revisados
| Gate | Estado/decisão |
|---|---|
| Serpro entitlement | DEFERRED / NOT BLOCKING BrasilAPI MVP |
| BrasilAPI public contract | PROVEN documentation; validar schema e disponibilidade no trabalho S3.1 |
| BrasilAPI terms / fair use | TO_VERIFY; sem exploração abusiva |
| S1/S2 compatibility | TO_VERIFY in HEAD and tests |
| LGPD institucional | PROVEN docs; aplicação à projeção/consulta e ROPA específicos devem ser comprovadas |
| Provider adapter implementation | AUTHORIZED limited S3.1 |
| External GET smoke | Authorized only with test CNPJ and bounded traffic after verification of rules; never log personal data |
| Production enable/deploy | SEPARATE RUNTIME GATE; do not infer PASS |
| `api-delpi` third-party provenance PUT | BLOCKED; separate trusted-evidence v2 contract |
| Protheus POST/PUT | OFF; not in S3.1 |

## Next task
`SUPPLIES-ENRICHMENT-01 / S3.1 — BrasilAPI CNPJ Adapter & Assisted Review`: read HEAD, freeze real BrasilAPI v1 schema and permissible use, implement minimal HTTP adapter behind configurable fail-closed flag, map only S1 fields, tests offline positive/sibling/negative, S2 review creation integration, error/quotas, bounded isolated smoke if authorized, report outcomes. No MFE yet unless separate page authorization/gate; no changes to api-delpi, migrations or ERP writes.

**Decision: GO S3.1 (bounded); NO GO for Serpro, external-source provenance writes, Protheus PUT, automatic rollout/deploy or page promotion.**

## Addendum (X0 — 2026-10-22)
O transporte de consulta externa migra conceitualmente para o novo owner
compartilhado **`external-data-api`** — ver
`docs/12-roadmap-e-evolucao/shared-integrations/EXTERNAL-DATA-API-MVP-ARCHITECTURE.md`
(ADR de direção) e `EXTERNAL-DATA-API-CONTRACT-FREEZE-X0.md` (contrato
congelado). Esta decisão BrasilAPI **permanece vigente** para o provider;
só o transporte muda de owner (cutover em X2, após paridade e runtime
saudável). O adapter local `brasilapi` da supplies-api não é removido
antes da paridade comprovada.
