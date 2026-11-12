# F5a Passo 0 — smoke MFE HML (shell federado)

Executado em 2026-11-12 no portal `https://192.168.1.237:18443` com corte de flags ativo, depois rollback.

## Resultados

| Perfil | Ação | Resultado |
|---|---|---|
| P11 | fila filial-01 | PASS |
| P11 | filtros | PASS |
| P11 | abrir criar | PASS |
| P11 | filial-02 bloqueada | PASS |
| P2 | fila filial-01 | PASS |
| P2 | não vê filial-02 | PASS |
| P6 | shell filial-01 | EXPECTED_FAIL (rota exige `view.filial-01`) |
| P6B | fila / detalhe / iniciar / bloquear / comentar / retomar | PASS |

## Network

- Chamadas de negócio: somente `/apps/controllership-finance-api/lancamento-notas-fiscais`
- Nenhuma chamada para `/apps/api-delpi/lancamento-notas-fiscais`
- Ver `summary.json` / `network.json`

## Nota

Onboarding HML exige Política de Privacidade → Consentimentos → «Aceitar e continuar» antes do shell.
