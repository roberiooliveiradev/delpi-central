# ATLAS | Etapas 66–69: pacote de pré-ativação HML (source-only)

**18/11/2026 | SOURCE-ONLY | Issue [#232](https://github.com/roberiooliveiradev/delpi-central/issues/232)**  
Sem instalação, chave real, deploy, merge automático ou alteração do Docker compartilhado.

## 1. Escopo do lote

| Etapa | Entrega |
|---|---|
| 66 | Cadeia claim→bridge→signer listen→envelope→signed presenter; bind pós-non-root |
| 67 | Bootstrap controlado (ausência≠genesis), recovery de contador, ciclo de chaves efêmeras |
| 68 | `candidate-units/*.candidate` separados de `review-only/`; anti-install estático |
| 69 | Preflight estruturado, handoff checklist, runbook operacional futuro |

## 2. Fluxo técnico

```text
Docker HML (produtor root, allowlist)
  → snapshot claim atômico (FD/ACL)
  → bridge non-root (sem Docker/chave)
  → signer non-root (bind próprio, SO_PEERCRED, checkpoint)
  → envelope Ed25519
  → presenter verifica assinatura + continuidade
  → MCP READ (4 tools) / status=blocked
```

## 3. Bootstrap e recovery

- `atlas_hml_b_bootstrap_control.py`: dossier com âncora externa + change record; **ENOENT nunca é gen1**.
- `disposable_genesis` permanece só em fixtures.
- `atlas_hml_b_counter_recovery.py`: backup antigo não reduz o piso; falhas → `BLOCKED_RECONCILE_REQUIRED`.
- Chaves: `ATLAS-HML-ED25519-PRIVATE-V1` documentado; sem escrita GLPI/Git.

## 4. Systemd

- `review-only/*.review` continuam não instaláveis (`ExecStart=/usr/bin/false`).
- `candidate-units/*.candidate`: área separada, `RefuseManualStart=yes`, sentinel impossível, sem `[Install]`, `ExecStart=/usr/bin/false` até packaging autorizado.
- Deploy geral **não** deve copiar candidatos para `/etc/systemd/system`.

## 5. Preflight / handoff (futuro srv-api)

1. Autorização + change-control  
2. Baseline host/PROD  
3. UIDs/GIDs/dirs/ACLs  
4. Artefatos revisados  
5. Bootstrap gen1 com âncora  
6. Chave + GLPI + frase segregada  
7. Ativação só HML  
8. Testes funcionais + isolamento  
9. Validar PROD intacto  
10. Rollback só ATLAS  

STOP se Docker Engine, PROD ou SEC gates forem impactados.

## 6. Invariantes

- Quatro MCP READ; PREPARE/ACT OFF; `can_execute=False`; `status=blocked`
- Sem chave real; sem socket root-prebound no signer
- Progresso de referência: **60%** (desenvolvimento pré-ativação); host ainda pendente

## 7. SEC matrix (resumo)

| Classe | Itens |
|---|---|
| Código/CI | cadeia disposable, peer UID, anti-replay, candidate anti-install |
| Só fixture | bind signer, PKCS#8, continuity flock |
| Host pendente | UIDs reais, LSM/ACL/FD, systemd efetivo |
| Autorização | bootstrap, chave, install units, change window |
| Residual aceito | root same-host / Docker compartilhado |
| Bloqueio | SEC-01..10 ou exceção formal |
