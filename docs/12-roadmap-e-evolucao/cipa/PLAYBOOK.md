# Playbook CIPA — atas e assinaturas

> **Status:** implementação inicial (fases 2–7 scaffold + fluxo v1)  
> **Data:** 2026-07-16

## Decisões

| Tema | Escolha |
|------|---------|
| API | `cipa-api` dedicada |
| Unidade | Filiais `01` / `02` |
| MFE | `plugins/cipa` federado |
| Editor | `RichTextEditor` em `@delpi/plugin-ui` — tela única estilo e-mail (configurações, participantes, signatários, corpo) |
| Assinatura | `SignaturePad` PNG + hash SHA-256 da versão; perfil pessoal em `/signatures/me` (`cipa.sign`) |
| PDF | ReportLab autoritativo; leitura/print usa `DocumentReader` do `plugin-ui` |
| Notificações | Core API `/integrations/notifications` |

## Numeração de atas

Sequencial por unidade e ano: `YYYY/NNN` (ex.: `2026/001`).

## Aceite v1

Criar → editar → participantes/signatários → enviar → assinar (mobile) → acompanhar → finalizar → PDF → auditoria → RBAC: ações globais + escopo por unidade (`cipa.unit.filial-*`).

### Assinatura pessoal (entregue)

- Página `/apps/cipa/my-signature` (gate `cipa.sign`)
- API `GET/PUT /signatures/me` e `POST/GET /signatures/me/image`
- Storage estável em `cipa/signatures/profiles/{user_id}.png`
- Na assinatura da ata: pré-preencher nome + **Usar assinatura cadastrada**

### Modo de leitura e PDF formal (entregue)

- Detalhe da ata em papel A4 responsivo com logo, cabeçalho, marca d'água,
  conteúdo, participantes, papéis e assinaturas.
- Primitivos transversais no `plugin-ui`: `DocumentReader`, `DocumentPage`,
  `DocumentHeader`, `DocumentFooter`, `DocumentSignatureBlock` e
  `printDocumentReader`.
- Participantes registram papel na reunião; horários de início e término
  alimentam o texto formal.
- PDF oficial no backend com ReportLab, rodapé paginado, PNGs das assinaturas,
  hash e código de validação.
- `validation_code` é criado antes do PDF final e o artefato persistido continua
  sendo a fonte oficial; impressão HTML é apenas conveniência.

## Backlog (§23)

Modelos de ata, pauta estruturada, plano de ação completo, QR de validação, MFA na assinatura, dashboard CIPA.
