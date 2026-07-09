# Varredura — controles nativos fora de `@delpi/plugin-ui`

> Snapshot: jul/2026 · Gate CI: `scripts/ci/audit_plugin_ui_native_form_controls.py --check`

## Resumo

| Métrica | Valor |
|---------|------:|
| `<select>` / `<textarea>` nativos em plugins (exc. `plugin-ui`) | **22** |
| Allowlist documentada (backlog + domínio) | 22 |
| **Novos bloqueantes** (`--check`) | **0** |
| `<select>` restantes | **0** (fora plugins excluídos) |

### Plugins excluídos da varredura

| Plugin | Motivo | Ocorrências (info) |
|--------|--------|-------------------:|
| `plugin-ui` | Canônico | — |
| `api-delpi-console` | Fora de escopo MFE dashboard | 1 `<select>`, 1 `<textarea>` |
| `public-hub` | Runtime público (form visitante) | 1 `<textarea>` |
| `portal` | Shell legado | — |

## Por plugin (actionable backlog)

| Plugin | `<textarea>` | `<select>` | Prioridade sugerida |
|--------|-------------:|-----------:|---------------------|
| **strategic-indicators** | 0 | 0 | ✅ migrado (`SiNativeTextAreaControl`) |
| **minha-delpi-chat** | 15 | 0 | Média — 4 domínio permanente, 11 admin/workspace |
| **cultura-delpi** | 3 | 0 | Média — kit `plugin-ui` + alias Vite |
| **propostas-comerciais** | 2 | 0 | Média — inline table + modal |
| **customer-experience** | 1 | 0 | Baixa — `ParticipantsPanel` |
| **tv-dashboard** | 1 | 0 | Baixa — `ComunicadoEditorTextBlock` |

## Domínio permanente (não migrar para FormFieldShell)

| Arquivo | Motivo |
|---------|--------|
| `minha-delpi-chat/.../ChatInput.tsx` | Composer — autosize, stream, atalhos |
| `minha-delpi-chat/.../ChatMessageEditField.tsx` | Edição inline de bolha |
| `minha-delpi-chat/.../ChatCanvas.tsx` | Editor markdown do canvas |
| `minha-delpi-chat/.../ChatShortcutPromptDialog.tsx` | Prompt modal compacto |

Estes permanecem nativos; podem evoluir para `NativeTextAreaControl` **sem** shell se quiser DRY no import.

## Backlog de migração (por lote)

### Lote A — strategic-indicators ✅
- Migrado para `SiNativeTextAreaControl` (`siNativeFormFields.ts`)

### Lote B — minha-delpi-chat admin/workspace (11)
- Admin: evaluations, guidelines test, security, skills
- Workspace: context dialog, project settings, source note, icebreakers, agent builder residual, action test
- **Kit:** estender `chatAdminFormFields` ou `NativeTextAreaControl` onde há `ref`/`onKeyDown`

### Lote C — plugins menores (7)
- `cultura-delpi/AdminCulturaPage` (3)
- `propostas-comerciais` ItensTable + PdfExportModal (2)
- `customer-experience/ParticipantsPanel` (1)
- `tv-dashboard/ComunicadoEditorTextBlock` (1)

## Uso do gate CI

```bash
# Relatório humano
python3 scripts/ci/audit_plugin_ui_native_form_controls.py

# Falha se surgir ocorrência NOVA (fora de KNOWN_ALLOWLIST no script)
python3 scripts/ci/audit_plugin_ui_native_form_controls.py --check

# JSON (dashboards / automação)
python3 scripts/ci/audit_plugin_ui_native_form_controls.py --json
```

Ao migrar um arquivo, **remover** a entrada correspondente de `KNOWN_ALLOWLIST` em
`scripts/ci/audit_plugin_ui_native_form_controls.py` — o `--check` deve continuar verde.

## Referências

- [refactoring-roadmap.md](./refactoring-roadmap.md) §7
- [migration-catalog.md](./migration-catalog.md)
- Canônicos: `NativeSelectControl`, `SelectControl`, `NativeTextAreaControl`, `createDashboardNativeFormFields`
