# Atas — Comitê de Ética e Conduta

Fluxo espelhado do Transformômetro / CIPA, com comitê **único corporativo** (`unit_code = 00`).

## Estados

```text
draft / in_review
  → send-for-signature (+ notifica signatários)
  → awaiting_signatures / partially_signed
  → signed (+ notifica gestores) | refuse → in_review (+ notifica gestores)
  → finalize → PDF + finalized
```

## Rotas UI

| Path | Página |
|------|--------|
| `/atas` | Lista |
| `/atas/new`, `/atas/{id}/edit` | Editor |
| `/atas/{id}` | Leitura |
| `/atas/{id}/sign` | Assinatura |
| `/atas/pending` | Pendências |
| `/membros` | Cadastro do comitê |
| `/minha-assinatura` | Perfil PNG |

## Notificações

Contrato Core (`userIds` + `action.type=portal_route`):

- Pendente → `/apps/comite-etica-conduta/atas/{id}/sign`
- Assinada / recusada → `/apps/comite-etica-conduta/atas/{id}`

## Tipagem de reunião

`ordinary` | `extraordinary` | `other`

Numeração global `YYYY/NNN` (sem filial).
