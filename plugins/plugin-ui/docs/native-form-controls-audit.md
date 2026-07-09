# Varredura — controles nativos fora de `@delpi/plugin-ui`

> Snapshot: jul/2026 · Gate CI: `scripts/ci/audit_plugin_ui_native_form_controls.py --check`

## Resumo

| Métrica | Valor |
|---------|------:|
| `<select>` / `<textarea>` nativos em plugins (exc. `plugin-ui`) | **4** |
| Allowlist documentada (domínio permanente) | 4 |
| **Novos bloqueantes** (`--check`) | **0** |
| `<select>` restantes | **0** (fora plugins excluídos) |

### Plugins excluídos da varredura

| Plugin | Motivo | Ocorrências (info) |
|--------|--------|-------------------:|
| `plugin-ui` | Canônico | — |
| `api-delpi-console` | Fora de escopo MFE dashboard | 1 `<select>`, 1 `<textarea>` |
| `public-hub` | Runtime público (form visitante) | 1 `<textarea>` |
| `portal` | Shell legado | — |

## Por plugin

| Plugin | `<textarea>` | `<select>` | Status |
|--------|-------------:|-----------:|--------|
| **minha-delpi-chat** | 4 | 0 | Domínio permanente (composer, edição, canvas, shortcut) |
| **strategic-indicators** | 0 | 0 | ✅ migrado |
| **customer-experience** | 0 | 0 | ✅ migrado |
| **quality-action-plans** | 0 | 0 | ✅ migrado |
| **cultura-delpi** | 0 | 0 | ✅ migrado (`CulturaNativeTextAreaControl`) |
| **propostas-comerciais** | 0 | 0 | ✅ migrado (`PcNativeTextAreaControl`) |
| **tv-dashboard** | 0 | 0 | ✅ migrado (`TdNativeTextAreaControl`) |

## Domínio permanente (não migrar para FormFieldShell)

| Arquivo | Motivo |
|---------|--------|
| `minha-delpi-chat/.../ChatInput.tsx` | Composer — autosize, stream, atalhos |
| `minha-delpi-chat/.../ChatMessageEditField.tsx` | Edição inline de bolha |
| `minha-delpi-chat/.../ChatCanvas.tsx` | Editor markdown do canvas |
| `minha-delpi-chat/.../ChatShortcutPromptDialog.tsx` | Prompt modal compacto |

Estes permanecem nativos; podem evoluir para `NativeTextAreaControl` **sem** shell se quiser DRY no import.

## Kits locais (wrappers finos)

| Plugin | Arquivo | Export |
|--------|---------|--------|
| minha-delpi-chat | `chatAdminFormFields.ts` | `ChatAdminNativeTextAreaField`, `ChatNativeTextAreaControl` |
| strategic-indicators | `siNativeFormFields.ts` | `SiNativeTextAreaControl` |
| customer-experience | `cxFormFields.ts` | `CxNativeTextAreaField` |
| cultura-delpi | `culturaFormFields.ts` | `CulturaNativeTextAreaControl` |
| propostas-comerciais | `pcFormFields.ts` | `PcNativeTextAreaControl` |
| tv-dashboard | `tdFormFields.ts` | `TdNativeTextAreaField`, `TdNativeTextAreaControl` |

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
