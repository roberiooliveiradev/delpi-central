# External Data API — arquitetura e roadmap MVP (2026-10-22)

> **DECISION / PLANNED — PO escolheu a opção C:** serviço reutilizável para aquisição e tratamento técnico de dados externos na Minha DELPI. **Nome técnico proposto:** `external-data-api` (identidade a validar contra catálogo e regras antes de criar serviço). **Nome de produto:** External Data API / Serviço de Dados Externos. Esta decisão documenta a direção arquitetural; **não prova que o serviço existe, não autoriza deploy e não substitui gates de infraestrutura/segurança**.

## 1. Objetivo e limite do MVP
Entregar a menor API backend funcional que consulta CNPJ pela **BrasilAPI CNPJ v1**, valida e minimiza resposta, controla limites e expõe contrato interno reutilizável. Permitir que `supplies-api` consuma-a para compor `ExternalRegistrySnapshot` e usar S1/S2 já implementados. Expandir para CEP, IBGE ou outros provedores **apenas mediante demanda, contrato e owner comprovados**; não construir plataforma genérica, UI, CRUD administrativo, job crawler ou catálogo de providers antecipadamente.

## 2. Nome e ownership
- Candidato preferido: `external-data-api`, endpoint interno **TARGET** `/internal/external-data/v1/cnpj/{cnpj}`; confirmar namespaces e gateway existentes no HEAD antes de congelar rota. Alternativas `public-data-api` (mais restritiva) e `registry-data-api` (demasiado CNPJ-específica). Não confundir com API pública externa: este é **serviço interno**, não endpoint público irrestrito.
- **Owner da integração transversal:** novo bounded context External Data; HTTP externo, adapter BrasilAPI, normalização independente do consumidor, erros/limites/cache/evidência de origem e observabilidade.
- **Owner do negócio de fornecedores:** `supplies-api` mantém leitura canônica por `api-delpi`, mapeamento SA2, comparação S1, revisão/decisões S2, autorização de recurso e draft sem ERP PUT.
- **Core:** identidade contextual e permissões efetivas de plataforma; **Keycloak:** SSO; **api-delpi:** SQL/regras TOTVS, proveniência e gravação canônicas.
- Integração entre contextos via HTTP/S2S, nunca import de `domain/application` de outro serviço nem acesso direto ao banco de outro contexto.

## 3. Baseline reportado e fatos a revalidar
- S1 `aeb4e18b20`: engine de comparação aceita.
- S2 `f68b1e2604`: persistência V002/V003, decisões e idempotência aceitas em código com residuais.
- S3 `cd5ca80bf8`: Serpro inventariado; direito DELPI não provado.
- S3.1 `33af5ac20d`: BrasilAPI adapter e normalizador na `supplies-api`.
- S3.2 `f28e769f44`: Redis rate limiter distribuído implementado em código.
- S3.3 `85805eb7d5`: hardening da configuração, sem deploy. **GATE-R1 INCONCLUSIVE** por não existir Redis DELPI autorizado; `evolution-redis` pertence a outro produto, não reutilizar sem contrato; banco de destino reportado somente V001; backend atual ainda não está em runtime validado.
- **Não reatribuir ou copiar migrations/reviews à API compartilhada.**
- Documentos anteriores Serpro/BrasilAPI continuam como trilha de decisão; esta ADR de direção **supersede somente ownership do transporte de consulta externa**, não a escolha BrasilAPI nem o fluxo de revisão.

## 4. Arquitetura-alvo enxuta

```text
Portal/MFE supplies
    -> supplies-api (Core-effective AuthZ + supplier scope + SA2 comparison/reviews/decisions)
       -> api-delpi (supplier canonical reads, no writes in MVP)
       -> external-data-api (internal S2S, allowlisted consumer)
          -> BrasilAPI CNPJ v1 (GET only; third-party source)
          -> shared Redis limiter (only when authorized/provisioned)
```

NUNCA: MFE -> BrasilAPI; MFE -> api-delpi; external-data-api -> banco SA2; external-data-api -> banco supplies; `external-data-api` decidir campos editáveis do fornecedor.

## 5. Contrato mínimo candidato
**GET** `/internal/external-data/v1/cnpj/{cnpj}` (**TARGET**, não criar sem inventariar padrão de rotas do gateway). Consumer-to-provider autenticado via identidade de serviço verificável, permissões Core conforme authority vigente, allowlist de consumidores e propósito; sem permissão de usuário por botão/endpoint. Suprimentos resolve autorização do usuário/recurso antes da chamada.

Resposta mínima, sem dados brutos do provedor:
```json
{
  "identity": {"tax_id": "14-digit numeric CNPJ"},
  "company": {"legal_name": "...", "trade_name": null},
  "address": {"street": "...", "number": "...", "district": "...", "postal_code": "...", "city": "...", "state": "...", "ibge_city_code": null},
  "contact": {"area_code": null, "phone": null, "email": null},
  "information": {"registration_status": null, "main_cnae": null, "legal_nature": null, "opening_date": null},
  "source": {"provider_id": "brasilapi-cnpj-v1", "source_type": "THIRD_PARTY_API", "retrieved_at": "...", "correlation_id": "...", "schema_version": "v1"}
}
```
Formato é **PROPOSED**, não schema congelado: antes da implementação verificar campos efetivos e minimização LGPD. Dados de contato podem exigir omissão até enquadramento. Nunca retornar ou persistir `qsa`, CPF/sócios, raw payload, credentials. Recusar CNPJ não suportado; garantir igualdade de identidade; erros tipados para inválido/não encontrado/429/indisponível/schema inesperado, sem false success. Proveniência da fonte indica terceiro, **não** atesta aprovação de PUT da `api-delpi`.

## 6. Contrato operacional mínimo
- Provider configurável `unavailable|brasilapi`; por padrão `unavailable`.
- Limite por consumidor/ator quando disponível, por CNPJ hash e global no **owner externo**, não duplicar contadores incoerentes; Redis distribuído apenas quando infraestrutura DELPI for autorizada. Falha do rate limiter impede consulta externa, não derruba aplicações consumidoras; timeout curto e sem retry abusivo.
- Correlation ID e logs sem CNPJ cru, QSA, CPF, payload ou secrets. Não guardar resposta bruta; cache e persistência **não obrigatórios** no MVP e só após contrato LGPD/fair-use.
- Autenticação S2S e autorização de consumidores fail-closed; nenhum endpoint público anônimo interno; não confiar em headers de identidade forjáveis.
- Termos/uso justo BrasilAPI e ROPA/DPO precisam de classificação atualizada; tratar pendências como gates operacionais, não como justificativa para reinventar integrações.
- Rollback: desabilitar provider externo; `supplies-api` preserva reviews existentes e falha explicitamente para novas consultas.
- Serpro: provider futuro substituível sem alterar domínio de Suprimentos, apenas após contratação.

## 7. Plano bounded de entrega — uma capacidade por vez
**X0 — P0 ownership/contract freeze:** inventário no HEAD de `api-delpi`, INT-CEP-01, padrões de microserviços e S2S, gateway, compose, observabilidade, Redis e LGPD; confirmar nome `external-data-api` e paths; formalizar owner e RQ/AC; capturar incompatibilidades como `EXECUTION_DRIFT`. Documentação não autoriza novas telas ou alteração de manifesto.

**X1 — Bootstrap + CNPJ funcional isolado:** serviço Python/Flask mínimo conforme padrão real; health, S2S, adapter BrasilAPI allowlisted, normalizador com fixtures e endpoint interno; teste 200/400/404/429/5xx, timeout, mismatch, segurança/negativos; sem Postgres se nenhum estado próprio for exigido. Não fazer deploy automático sem gate. Reuso de código existente como referência/adaptação, não import cross-context.

**X2 — Paridade e cutover do consumidor Suprimentos:** adaptar `CompanyRegistryProvider` em `supplies-api` para chamar HTTP S2S da `external-data-api`; preservar DTO `ExternalRegistrySnapshot`, comparador S1, revisões/decisões S2, AuthZ e ergonomia de erros. Provas positivas, sibling, negativas, concorrência, source_id e smoke; feature switch `unavailable|local-legacy|external-data-api` provisório apenas se rollback justificar; remover adapter BrasilAPI local somente após paridade e runtime saudável.

**X3 — Infra, Redis DELPI e runtime gate:** autorização do owner de infraestrutura para Redis, config, build/deploy restrito, migrations Suprimentos V002/V003 sob backup, smokes autenticados end-to-end, prova de origens, rollback; nunca usar Redis de outro produto silenciosamente. Código verde não implica runtime PASS.

**X4 — UX Suprimentos:** etapa separada dependente do GATE-FEATURE/página autorizada; kit-first, Help e smoke federado. Nenhuma escrita Protheus sem proveniência v2 verificável.

**Expansão:** nova fonte/capacidade só quando houver consumidor real, contrato e valor comprovados; nada de marketplace de providers ou CRUD genérico no MVP.

## 8. Gates
- `GATE-OWNER`: ownership transversal congelado pelas autoridades, sem conflito com `api-delpi` ou INT-CEP-01.
- `GATE-CONTRACT`: endpoint, DTO, auth S2S e source semantics aprovados.
- `GATE-SECURITY`: minimização, auth, quotas, LGPD e termos; no-source fail-closed.
- `GATE-INFRA`: Redis DELPI de fato autorizado/provisionado ou alternativa comprovada, sem depender de Redis de outro produto.
- `GATE-CONSUMER-PARITY`: supplies-api não perde S1/S2, e não escreve no ERP.
- `GATE-RUNTIME`: deploy, SHA, image digest, migrations/smokes, rollback comprovados.

Stop: `EXECUTION_DRIFT` para premissa de owner invalidada; sem autorização de nova infraestrutura, sem deploy; `TEST_NOT_RUN` e `INCONCLUSIVE` não se transformam em PASS.

## 9. Próxima task sugerida
`SHARED-INTEGRATIONS-01 / X0 — Ownership & Contract Freeze`: inventariar authorities e produtores/consumidores em HEAD, definir serviço mínimo, contrato S2S e plano X1/X2 com evidências; terminar com relatório. PO decidiu **direção C e MVP**, mas implementação do serviço fica condicionada ao contrato X0 e revisão; não iniciar UX, PUT Protheus ou novo Redis produtivo nesta etapa.

> **X0 executado:** contrato congelado em `EXTERNAL-DATA-API-CONTRACT-FREEZE-X0.md`
> (owner proposto `external-data-api` novo bounded context, rota `GET /v1/cnpj/{cnpj}`
> S2S-only, DTO v1, erros `EXTERNAL_DATA_*`, plano X1–X4, GATE-INFRA INCONCLUSIVE
> por Redis DELPI inexistente). Próxima task: `X1 — Foundation + BrasilAPI CNPJ`.
>
> **X1 executado:** serviço `external-data-api/` implementado (Flask+gunicorn,
> `delpi_auth`, `GET /v1/cnpj/{cnpj}` com allowlist `supplies-api`, adapter
> BrasilAPI reimplementado, normalizador allowlist, limiter consumer/cnpj/global
> com Lua atômico, compose aditivo sem porta pública). 67 testes PASS incluindo
> Redis 7 real multi-processo; `contact` mantido `null` por política LGPD.
> Runtime produtivo **não** verificado; `GATE-INFRA` (Redis DELPI) continua
> INCONCLUSIVE. Próxima task: `X2 — Supplies Consumer Integration & Parity`.
