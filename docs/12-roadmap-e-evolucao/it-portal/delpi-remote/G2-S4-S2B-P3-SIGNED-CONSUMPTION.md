# G2-S4-S2b-P3 | Vinculo de prova assinada a ticket de uso unico

**Estado:** EM REVISAO (14/11/2026). Codigo interno, nao conectado a rotas HTTP, Keycloak ou agentes.

## Entrega e limites

- V015 e aditiva. Cria `workstation_trusted_device_keys`, armazenando apenas chave publica de 32 bytes, estado inicial **pending**, ID da workstation e campos de aprovacao/revogacao. Sem chaves privadas nem credenciais em banco. O sistema nao possui rota nem servico para registrar ou aprovar chaves.
- V015 vincula opcionalmente a tabela de tickets V014 a `trusted_key_id`, nonce e janela de desafio assinada. A restricao FK garante que a chave pertence ao equipamento; a janela nao excede o prazo do ticket.
- `PostgresSignedBootstrapStore.bind_pretrusted` so associa tickets ainda pendentes a chaves `trusted` ja aprovadas em processo privado. Testes sinteticos inserem chaves aprovadas **somente no banco descartavel**.
- `verify_and_spend` revalida desafio original, assinatura Ed25519 da chave armazenada, status atual da chave, prazo, hash de token, identidade nao revogada, workstation operacional, e encerra o ticket em uma transacao. Concorrencia e reuso devem produzir apenas um sucesso. Nenhuma operacao concede `ingest_authorized` ou altera Keycloak.
- O consumo legado de ticket por token recusa qualquer ticket com `trusted_key_id` vinculado, bloqueando downgrade silencioso. Tickets legados sem vinculo continuam internos e sem endpoints.
- Correcao no P2: `create_challenge` normaliza microssegundos para timestamp UTC integral. O formato canonico rejeita microssegundos, portanto uma chamada real precisa produzir desafio assinavel sem falhar.

## Verificacao

```bash
cd it-portal-api
python -m pytest -q tests/test_workstation_bootstrap_tickets.py tests/test_workstation_device_proof.py
python -m it_portal_app.domain.workstation_bootstrap_readiness --repo-root ..
# Apenas em PostgreSQL descartavel (como no GitHub Actions):
IT_PORTAL_TEST_DSN=postgresql://postgres:test-password@localhost:5432/postgres python -m pytest -q tests/test_postgres_integration.py tests/test_postgres_bootstrap_tickets.py tests/test_postgres_signed_bootstrap.py
```

Resultados de CI devem ser verificados no commit final; conclusao do pipeline e diferente de homologacao presencial.

## Gates pendentes (NAO ATIVAR)

1. Processo de ancoragem de confianca de chave publica do agente Windows, assinatura do instalador, revogacao/rotacao, politica TPM/mTLS e testes contra clonagem.
2. Processos TI/RH/Seguranca para aprovacao em ambiente privado, MFA recente, consentimento e auditoria por equipamento.
3. Canal de transferencia seguro para ticket (nunca browser, URL, ticket GLPI ou logs); prova de dispositivo antes de associar grant S2S.
4. Reconciliacao de falhas de Keycloak, concorrencia de revogacao, backup e rollback.
5. Testes Windows/Keycloak HML antes de habilitar qualquer flag. G0-SEC continua bloqueando controle remoto.

**Sem deploy:** nao executar migrations de V012-V015 em producao nesta entrega. Se houver rollout futuro, seguir runbooks de backup, restauracao e flags false antes da janela de mudanca.

[Roadmap](README.md) | [P2](G2-S4-S2B-P2-DEVICE-PROOF.md) | [Issue #179](https://github.com/roberiooliveiradev/delpi-central/issues/179).

## Evidencias automatizadas finais (14/11/2026)

- [CI da API, PostgreSQL V015 e regressao G0: SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43649344462)
- [Architecture Enforcement: SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43649344458)
- [Governance: SUCCESS](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43649344455)
- Commit P3: `81c9dd08f7c5`, correção de fixtures: `251dc18283e4`. Aprovacao de CI valida testes automatizados e banco descartavel; **nao** e aceite de hardware, Keycloak ou operacao remota.
