# G2-S4-S2b-P1 | Ledger interno de tickets efemeros para enrollment

**Data:** 14/11/2026. **Estado:** EM REVISAO (codigo inerte, HML real pendente).
**Requisito:** permitir preparacao transacional e revogavel de um desafio de uso unico para o futuro agente Windows, sem permitir ativacao prematura.

## Entrega

- `domain/workstation_bootstrap_tickets.py` cria valor aleatorio criptograficamente seguro de 256 bits com `secrets.token_urlsafe(32)`, TTL de 1 a 10 minutos, UUID de ticket e UUID canonico do equipamento. Retorna **dois objetos separados**: metadados sem segredo e valor efemero. Nenhum print, logger, persistencia ou transporte do segredo.
- `V014__workstation_bootstrap_tickets.sql` e aditiva e imutavel. Salva somente SHA-256 do valor de alta entropia, identificador de equipamento, criador, prazo, estado (pending/consumed/cancelled/expired) e eventos de auditoria. Nao armazena senha Keycloak nem token bruto. Um indice parcial permite apenas um convite pendente por equipamento.
- `PostgresWorkstationBootstrapTicketStore` e uma classe interna **nao ligada a qualquer rota**. Verifica se ativo esta operacional, nao arquivado, identidade preparada e sem grants. Expira pendentes antigos durante nova emissao, rejeita segundo pendente, consome por uma unica operacao condicional UPDATE de banco (retorno booleano), permite cancelamento, e retorna apenas metadados em status.
- Testes unitarios do gerador e integracao PostgreSQL descartavel exercitam validade, replay, documento sem segredo, concorrencia e protecao fail-closed da identidade.
- A migracao V014 **nao concede `ingest_authorized`**; o consumo prova somente conhecimento do token e nunca attestation nem autenticacao forte do dispositivo.

## Gates que continuam fechados

- Sem `@router` para ticket, sem operacao de Keycloak Admin para habilitacao, sem canal de segredo no navegador, sem mudanca de Docker/Compose/env e sem instalador novo.
- Flags de ingestao, provisionamento, modo DB e revogacao continuam FALSE por default. G0-SEC e G3-ENGINE (acesso remoto) continuam bloqueados.
- Nenhum ticket pode ser emitido em producao pelo MFE/API atual, ja que a classe nao possui chamadas no runtime. Migracao em producao, se algum dia ocorrer, sera apenas estrutura inerte e exige backup/rollout coordenado.

## Testes e criterios

```bash
cd it-portal-api
python -m pytest -q tests/test_workstation_bootstrap_tickets.py
python -m it_portal_app.domain.workstation_bootstrap_readiness --repo-root ..
# Apenas CI / PostgreSQL descartavel:
IT_PORTAL_TEST_DSN=postgresql://postgres:test-password@localhost:5432/postgres python -m pytest -q tests/test_postgres_integration.py tests/test_postgres_bootstrap_tickets.py
```

Critérios: 19 testes unitarios PASS; testes Postgres reais com V014, expiracao, cancelamento, rejeicao de duplicidade, concorrencia (1 TRUE, 1 FALSE), e ingest_authorized segue FALSE. Preflight G2-S4-S2b deve continuar `BLOCKED` com exit 0 e G0-SEC nao pode autorizar remote.

**Limitacoes:** SHA-256 e suficiente somente por token aleatorio de 256 bits; nao usar com codigos curtos. Nao habilitar rotas ate existir entrega segura e auditavel de token, prova de dispositivo, vinculo transacional de attestation e revisao do protocolo em HML. A transicao `consumed` nao implica grant; apenas prova de posse do valor. Controle anti-abuso/rate limit de um endpoint futuro permanece necessario.

**Proximo passo:** validar CI, depois desenhar protocolo de attestation em HML com TPM/mTLS ou alternativa equivalente aprovada pela Seguranca antes da ativacao real.

[Roadmap](README.md) | [Preflight P0](G2-S4-S2B-PREFLIGHT.md) | [Issue #179](https://github.com/roberiooliveiradev/delpi-central/issues/179)

## Correcao de fixtures de CI (14/11/2026)

O primeiro CI V014 [43646928157](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43646928157) apresentou quatro erros de **setup de pytest**: `migrated` nao estava disponivel no modulo `test_postgres_bootstrap_tickets.py`. Foram importadas explicitamente as fixtures `database` e `migrated` juntamente com `pg_client`. Testes de banco continuam pendentes de novo workflow apos o fix; nao declarar V014 validada pelo CI anterior.

## Progresso seguinte: P2 (14/11/2026)

A biblioteca offline [G2-S4-S2b-P2](G2-S4-S2B-P2-DEVICE-PROOF.md) valida assinatura Ed25519 vinculada a ticket e workstation, mas continua **sem registro de chave, attestation Windows, endpoint ou ativacao**. O resultado do CI V014 apos o fix das fixtures deve ser conferido antes da homologacao.
