# Varredura — controles nativos fora de `@delpi/plugin-ui`

> Snapshot: jul/2026 · Gate CI: `scripts/ci/audit_plugin_ui_native_form_controls.py --check`

## Resumo

| Métrica | Valor |
|---------|------:|
| `<select>` / `<textarea>` nativos em plugins MFE (escopo) | **0** |
| Allowlist documentada | 0 |
| **Novos bloqueantes** (`--check`) | **0** |

### Plugins excluídos da varredura

| Plugin | Motivo | Ocorrências (info) |
|--------|--------|-------------------:|
| `plugin-ui` | Canônico | — |
| `api-delpi-console` | Fora de escopo MFE dashboard | 1 `<select>`, 1 `<textarea>` |
| `public-hub` | Runtime público (form visitante) | 1 `<textarea>` |
| `portal` | Shell legado | — |

## Status por plugin (escopo MFE dashboard)

| Plugin | Status |
|--------|--------|
| minha-delpi-chat | ✅ composer, edição, canvas, shortcut → `ChatNativeTextAreaControl` |
| strategic-indicators | ✅ `SiNativeTextAreaControl` |
| customer-experience | ✅ `CxNativeTextAreaField` |
| quality-action-plans | ✅ `NativeTextAreaControl` |
| cultura-delpi | ✅ `CulturaNativeTextAreaControl` |
| propostas-comerciais | ✅ `PcNativeTextAreaControl` |
| tv-dashboard | ✅ `TdNativeTextAreaControl` |

## Kits locais (wrappers finos)

| Plugin | Arquivo | Export |
|--------|---------|--------|
| minha-delpi-chat | `chatNativeFormFields.ts` | `ChatNativeTextAreaControl` |
| minha-delpi-chat | `chatAdminFormFields.ts` | `ChatAdminNativeTextAreaField` (+ re-export) |
| strategic-indicators | `siNativeFormFields.ts` | `SiNativeTextAreaControl` |
| customer-experience | `cxFormFields.ts` | `CxNativeTextAreaField` |
| cultura-delpi | `culturaFormFields.ts` | `CulturaNativeTextAreaControl` |
| propostas-comerciais | `pcFormFields.ts` | `PcNativeTextAreaControl` |
| tv-dashboard | `tdFormFields.ts` | `TdNativeTextAreaField`, `TdNativeTextAreaControl` |

## Uso do gate CI

```bash
python3 scripts/ci/audit_plugin_ui_native_form_controls.py
python3 scripts/ci/audit_plugin_ui_native_form_controls.py --check
python3 scripts/ci/audit_plugin_ui_native_form_controls.py --json
```

Nova ocorrência de `<select>` ou `<textarea>` nativo inline em plugin MFE → **bloqueante** (`--check` exit 1).
Documentar exceção temporária só em `KNOWN_ALLOWLIST` com motivo explícito.

## Referências

- [refactoring-roadmap.md](./refactoring-roadmap.md) §7
- [migration-catalog.md](./migration-catalog.md)
- Canônicos: `NativeSelectControl`, `SelectControl`, `NativeTextAreaControl`, `createDashboardNativeFormFields`
