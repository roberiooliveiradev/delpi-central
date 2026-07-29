# Atas Transforma+ (Transformômetro)

Atualizado: **jul/2026**

Documentação de produto e implementação do módulo de **atas oficiais Transforma+** no Transformômetro (API + MFE), incluindo geração assistida por **Kimi** (OpenAI-compatible / OpenRouter).

| Documento | Conteúdo |
|-----------|----------|
| **Este arquivo** | Visão, fluxo, RBAC, pacotes, status |
| [plugins/transformometro/docs/atas.md](../../../plugins/transformometro/docs/atas.md) | MFE — rotas, UI, port de IA, marca visual |
| [transformometro-api/docs/atas-kimi.md](../../../transformometro-api/docs/atas-kimi.md) | API HTTP, Kimi/env, smoke, troubleshooting |
| [infra/README-ambiente.md](../../../infra/README-ambiente.md) § Atas | Volumes de assinatura/PDF |

---

## Objetivo

Registrar atas de reunião do programa Transforma+ **dentro** do Transformômetro (schema Postgres `transformometro`, migration **V042**), com ciclo de vida semelhante à CIPA, **sem** reutilizar tabelas `cipa.*`.

Fluxo núcleo:

1. Criar/editar ata — **preencher** ou **importar transcrição DOCX**
2. Opcional: **Gerar ata com IA** (Kimi) a partir da transcrição — **não persiste**; o usuário revisa e salva
3. Definir signatários via diretório Minha Delpi (`UserDirectoryPicker`)
4. Enviar para assinatura → assinar (PNG + hash da versão) ou recusar
5. Finalizar PDF + download
6. Pendências do signatário + perfil de assinatura pessoal (`/minha-assinatura`)

---

## Arquitetura

```text
Portal ──► MFE transformometro (/apps/transformometro/atas*)
              │  JWT
              ▼
         transformometro-api
              │  /transformometro/atas/*
              ├─► Postgres (tm_meeting_minutes*)
              ├─► disco (assinaturas PNG / PDF)  ← volumes DELPI_DATA_HOST_DIR
              └─► OpenRouter / Kimi  (só POST …/generate-from-transcript)
```

| Camada | Pacote / módulo |
|--------|-----------------|
| MFE | `plugins/transformometro` — páginas `Ata*`, `src/ui/atas/*`, `src/ai/*`, `transformometroAtaApi.ts` |
| API | `MeetingMinutesService`, `minutes_routes.py`, `KimiLlmGateway` |
| Persistência | `MeetingMinuteRepository` + migration `V042__meeting_minutes_transforma_mais.sql` |
| Storage | `TM_ATA_SIGNATURE_UPLOAD_DIR`, `TM_ATA_PDF_UPLOAD_DIR` (Compose prod+dev) |
| Notificações | `TmPortalNotificationService` → Core API (padrão CIPA) |
| UI documento | `@delpi/plugin-ui` — `DocumentReader` / `DocumentPage` / `DocumentHeader` / `DocumentFooter` |

---

## Status da entrega (jul/2026)

| Item | Estado |
|------|--------|
| CRUD ata + versões + participantes/signatários | ✅ |
| Import DOCX no editor | ✅ (parse no browser; sem storage DOCX no servidor) |
| Geração Kimi (`generate-from-transcript`) | ✅ — exige `KIMI_API_KEY` |
| Leitura Fluent + logo Transforma+ + faixa de marca | ✅ |
| Assinatura / recusa / finalize PDF / pendências | ✅ |
| Perfil de assinatura (`/signatures/me`) | ✅ |
| Storage DOCX no servidor, plano de ação, anexos, ZIP, vínculo a processo, ICP-Brasil | ❌ fora do escopo atual |

**Importante:** a geração por IA **não grava** no banco. Se o usuário atualizar a página no meio da chamada, o resultado se perde (tokens já consumidos no provedor).

---

## Rotas UI

| Path | Página |
|------|--------|
| `/apps/transformometro/atas` | Lista (filtros, badges de status) |
| `/apps/transformometro/atas/new` · `…/{id}/edit` | Editor (preencher / importar + IA + signatários) |
| `/apps/transformometro/atas/{id}` | Detalhe — leitor de documento + ações |
| `/apps/transformometro/atas/{id}/sign` | Assinatura |
| `/apps/transformometro/atas/pending` | Pendências do usuário |
| `/apps/transformometro/minha-assinatura` | Perfil de assinatura |

---

## RBAC

Códigos no manifesto (`transformometro.manifest.json`):

| Código | Uso |
|--------|-----|
| `transformometro.atas.view` | Listar / ler |
| `transformometro.atas.manage` | Criar, editar, enviar, cancelar, gerar com IA, finalizar |
| `transformometro.atas.sign` | Assinar / recusar (signatário) |

Escopo de filial: `transformometro.view.filial-*` / `manage.filial-*` (mesmo mecanismo do restante do plugin). Atribuir na **Core API** RBAC, não no Keycloak.

---

## Seções de conteúdo (HTML)

Versão da ata persiste cinco campos HTML (sanitizados na API):

| Campo | Uso |
|-------|-----|
| `agenda_html` | Pauta |
| `body_html` | Andamento / discussão |
| `decisions_html` | Decisões |
| `pending_html` | Pendências |
| `observations_html` | Observações |

A resposta do Kimi usa as mesmas chaves em snake_case; o MFE mapeia para camelCase no port (`agendaHtml`, …).

---

## Rebuild / deploy

```bash
# API (após mudança em Kimi/rotas/migrations)
./infra/scripts/up-dev-sequential.sh --fase api --build transformometro-api

# MFE
./infra/scripts/up-dev-sequential.sh --fase mfe --build transformometro
```

Produção: `./infra/scripts/up-prod-sequential.sh` com `--build` nos mesmos serviços. Configurar `KIMI_*` em `infra/.env` antes do recreate da API — ver [atas-kimi.md](../../../transformometro-api/docs/atas-kimi.md).

---

## Fora do escopo (backlog)

- Persistência da transcrição DOCX no servidor
- Membros permanentes / templates de ata
- Plano de ação estruturado e anexos
- Export ZIP / vínculo explícito a processo Transformômetro
- Assinatura ICP-Brasil
