# Atas Transforma+ — MFE (`plugins/transformometro`)

Atualizado: **ago/2026**

Implementação de UI do módulo de atas no plugin Transformômetro.

- Produto / fluxo: [ATAS-TRANSFORMA-MAIS.md](../../../docs/12-roadmap-e-evolucao/transformometro-app/ATAS-TRANSFORMA-MAIS.md)
- API + Kimi: [transformometro-api/docs/atas-kimi.md](../../../transformometro-api/docs/atas-kimi.md)
- Magic link: [public-hub](../../public-hub/README.md) → `/p/transformometro/sign/{token}`

---

## Rotas

Definidas em `src/constants/routes.ts` e registradas no manifesto / router do app:

| Path | Componente |
|------|------------|
| `/apps/transformometro/meeting-minutes` | `AtasPage` |
| `/apps/transformometro/meeting-minutes/new` · `…/{id}/edit` | `AtaEditorPage` |
| `/apps/transformometro/meeting-minutes/{id}` | `AtaDetailPage` |
| `/apps/transformometro/meeting-minutes/{id}/sign` | `AtaSignPage` |
| `/apps/transformometro/meeting-minutes/pending` | `AtasPendingPage` |
| `/apps/transformometro/my-signature` | `MinhaAssinaturaPage` |

Assinatura **sem** login no módulo: `/p/transformometro/sign/{token}` (public-hub).

Nav: item **Atas** em `TransformometroNav`.

### Signatários

- Usuários Minha Delpi (`UserDirectoryPicker`) com flag **Assina**
- Convidados externos: nome + e-mail + **Assina** → `invite_email` na API; recebem magic link no e-mail Graph

No envio para assinatura: notificação portal (se `user_id`) + e-mail com link público.
---

## Estrutura de código

```text
src/
  ai/
    ataGenerationPort.ts       # port + stub; requestAtaGenerationFromTranscript
    httpAtaGenerationPort.ts   # implementa o port via HTTP
  data/api/
    transformometroAtaApi.ts   # cliente REST /atas e /signatures
  ui/
    pages/
      AtasPage.tsx
      AtaEditorPage.tsx
      AtaDetailPage.tsx
      AtaSignPage.tsx
      AtasPendingPage.tsx
      MinhaAssinaturaPage.tsx
    atas/
      AtaDocumentView.tsx      # DocumentReader + marca
      ataBrand.tsx             # logo embutida + faixa 4 cores
      ataContent.ts            # merge das 5 seções HTML
      ataLabels.ts / ataStatusUi.ts
  assets/
    logoTransformaMaisDelpi.svg
```

Estilos scoped em `src/index.css` (`tm-atas-*`, `tm-ata-*`, tokens `--tm-brand-blue-*`).

---

## Cliente HTTP

`transformometroAtaApi.ts` usa `TRANSFORMOMETRO_API_BASE` + `buildAuthHeaders` / `parseApiEnvelope`.

Principais funções: `listAtas`, `getAta`, `createAta`, `updateAta`, `generateAtaFromTranscript`, `sendAtaForSignature`, `signAta`, `exportAtaPdf`, perfil `/signatures/me`, etc.

Base pública típica: `/apps/transformometro-api/transformometro`.

---

## Geração com IA (port)

Padrão **port** para desacoplar a UI do transporte:

| Peça | Papel |
|------|--------|
| `AtaGenerationPort` | Interface `generateFromTranscript` |
| `stubAtaGenerationPort` | Default; lança mensagem de indisponibilidade |
| `createHttpAtaGenerationPort(getAccessToken)` | Chama `POST …/atas/generate-from-transcript` |
| `setAtaGenerationPort` / `resetAtaGenerationPort` | Wiring no mount do editor |

Em `AtaEditorPage`, no `useEffect` de mount:

```ts
setAtaGenerationPort(createHttpAtaGenerationPort(getAccessToken));
return () => resetAtaGenerationPort();
```

Fluxo UX (modo **Importar transcrição**):

1. Upload `.docx` → preview HTML editável
2. Botão **Gerar ata com IA** → port → API → Kimi
3. Merge das 5 seções no estado do editor (`mergeAtaContentHtml` / seções)
4. Usuário revisa e **salva** (persistência só no save CRUD)

A geração **não** cria rascunho sozinha. Evitar F5 durante a chamada.

Pré-requisitos de UI: `unitCode`, `meetingDate` e texto de transcrição não vazio; permissão `manage` na API.

---

## Documento de leitura (marca)

`AtaDocumentView` monta `@delpi/plugin-ui` `DocumentReader` / `DocumentPage`:

- **Cabeçalho:** logo Transforma+ Delpi (`import` de `src/assets/logoTransformaMaisDelpi.svg` — bundle Vite; não depende de `/public` do remote) + título «Ata de reunião»
- **Rodapé:** `DocumentFooter` (data / DELPI+unidade / número) + **faixa de 4 cores** da marca (`AtaBrandBar`), full-bleed no limite inferior da folha A4 (`tm-ata-brand-bar`, mesmas cores do header de inspeções-entrada: `#013866` → `#30b8ec`)
- Watermark RASCUNHO / CANCELADA conforme status
- Assinaturas via `DocumentSignatureBlock` + fetch das imagens PNG

Impressão: `printDocumentReader()`; PDF oficial continua no endpoint `export.pdf` da API quando finalizado.

---

## Editor — modos

| Modo | Comportamento |
|------|----------------|
| Preencher | Cabeçalho + `RichTextEditor` (Visual / HTML / Markdown); persistência sempre HTML (`body_html`) |
| Importar | DOCX → HTML; opcional IA; rich text |
| Signatários | `UserDirectoryPicker` + flag «Assina»; externo só nome |

Markdown: colar GFM ou modo fonte Markdown no kit `@delpi/plugin-ui` (conversão → HTML sanitizado). Sem campos `*_md` na API.

Após salvar: atalhos para enviar / ver ata / continuar editando.

---

## Permissões (manifesto)

```text
transformometro.meeting-minutes.view
transformometro.meeting-minutes.manage
transformometro.meeting-minutes.sign
```

Menu Atas exige `.view`. Detalhe no README do plugin e em `transformometro.manifest.json`.

---

## Rebuild

```bash
./infra/scripts/up-dev-sequential.sh --fase mfe --build transformometro
```

Smoke: abrir `/apps/transformometro/meeting-minutes`, criar rascunho, importar DOCX curto, gerar com IA (com `KIMI_API_KEY` na API), conferir logo + faixa no detalhe.
