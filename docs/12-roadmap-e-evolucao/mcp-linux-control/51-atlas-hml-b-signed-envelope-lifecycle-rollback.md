# ATLAS | Etapa 60: envelope assinado, continuidade persistente, lifecycle e rollback (Arquitetura B)

**17/11/2026 | SOURCE-ONLY | Issue [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232) | Sem instalação, deploy ou operação no srv-api**

## Resultado técnico verificável

Pacote consolidado na Draft PR #261, evoluindo a preparação source-only da arquitetura B:

1. **Envelope versionado** (`atlas_hml_b_snapshot_envelope.py`): geração monotônica, alvo HML inequívoco, digest do payload e recusa de JSON legado como autenticado.
2. **Confiança Ed25519** (`atlas_hml_b_snapshot_trust.py`): assinatura/verificação com keyring público, rotação e revogação; chave privada apenas injetada em fixture — nunca no Git. Verificação bem-sucedida **não** declara autenticidade independente do domínio do produtor root.
3. **Continuidade persistente** (`atlas_hml_b_continuity_store.py`): estado fail-closed em diretórios descartáveis, escrita atômica+fsync, detecção de replay entre reinícios simulados, regressão/gap de contador e corrupção.
4. **Lifecycle** (`atlas_hml_b_lifecycle.py`): estados init/available/degraded/failed/stopped/recovery_blocked, timeouts/backpressure, latch de integridade sem fallback Docker/PROD/PREPARE/ACT.
5. **Produtor assinado** (`atlas_hml_b_signed_producer.py`): compõe claim HML + envelope + publicação atômica em tmp; escopo fixo ao hub HML.
6. **Rollback review** (`atlas_hml_b_rollback_review.py`): baseline tipada, inventário dos componentes `.review`, abort conditions, simulação só em fixture; matriz SEC-01..10 referenciada sem atestar.
7. **Guarda do presenter**: inventário de FDs, sockets inesperados e consistência de socket activation (`LISTEN_*`).
8. **E2E descartável**: cadeia positiva/negativa/adversarial cobrindo publish→trust→FD→continuidade→UDS→denials→latch.

## Limites explícitos de confiança

| Afirmação | Status |
|---|---|
| Assinatura Ed25519 válida no runner | Demonstrável em fixture |
| Autenticidade independente de root no mesmo host | **Não** — domínio compartilhado |
| Anti-replay após restart (store descartável) | Demonstrável em tmp |
| Anti-replay operacional em `/run` do srv-api | **Não instalado** |
| SEC-01..10 / change-control / piloto | **Pendentes** |
| PREPARE/ACT | **OFF** |

## Contrato preservado

- Quatro ferramentas MCP READ; status sempre `blocked`.
- Sem systemd instalável, sem Docker no presenter, sem segredos no Git.
- CI descartável ≠ atestação do processo systemd futuro no `srv-api`.
- **NÃO** executar pull/deploy por este pacote.

## Progresso

**55%** (avanço técnico source-only material: assinatura, store persistente, lifecycle, E2E e rollback tipado). Operação HML continua bloqueada.
