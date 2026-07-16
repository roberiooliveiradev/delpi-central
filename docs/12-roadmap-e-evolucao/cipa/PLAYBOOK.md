# Playbook CIPA — atas e assinaturas

> **Status:** implementação inicial (fases 2–7 scaffold + fluxo v1)  
> **Data:** 2026-07-16

## Decisões

| Tema | Escolha |
|------|---------|
| API | `cipa-api` dedicada |
| Unidade | Filiais `01` / `02` |
| MFE | `plugins/cipa` federado |
| Editor | `RichTextEditor` em `@delpi/plugin-ui` (contentEditable + toolbar) |
| Assinatura | `SignaturePad` PNG + hash SHA-256 da versão |
| PDF | ReportLab |
| Notificações | Core API `/integrations/notifications` |

## Numeração de atas

Sequencial por unidade e ano: `YYYY/NNN` (ex.: `2026/001`).

## Aceite v1

Criar → editar → participantes/signatários → enviar → assinar (mobile) → acompanhar → finalizar → PDF → auditoria → RBAC: ações globais + escopo por unidade (`cipa.unit.filial-*`).

## Backlog (§23)

Modelos de ata, pauta estruturada, plano de ação completo, QR de validação, MFA na assinatura, dashboard CIPA.
