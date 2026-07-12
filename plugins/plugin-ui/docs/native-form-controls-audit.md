# Varredura — controles nativos fora de `@delpi/plugin-ui`

> Snapshot: jul/2026 · Gate CI: `scripts/ci/audit_plugin_ui_native_form_controls.py --check`

## Resumo

| Métrica | Valor |
|---------|------:|
| `<select>` / `<textarea>` nativos em plugins MFE (escopo) | **0** |
| `<input>` texto/número/search/checkbox em `tv-dashboard` (4N.7) | **0** |
| Allowlist documentada | 0 |
| **Novos bloqueantes** (`--check`) | **0** |

### Plugins excluídos da varredura

| Plugin | Motivo |
|--------|--------|
| `plugin-ui` | Canônico |
| `api-delpi-console` | Fora de escopo MFE dashboard |
| `public-hub` | Runtime público (form visitante) |
| `portal` | Shell legado |

### Input estrito (Onda 4N.7)

Só `tv-dashboard` entra no gate de `<input>` (exceto `file` / `hidden` / `range` / `radio` / `submit` / `button` / `image`).
Outros plugins: ainda só `<select>` / `<textarea>`.

## Status por plugin (escopo MFE dashboard)

| Plugin | Status |
|--------|--------|
| minha-delpi-chat | ✅ composer, edição, canvas → `ChatNativeTextAreaControl` |
| strategic-indicators | ✅ `SiNativeTextAreaControl` |
| customer-experience | ✅ `CxNativeTextAreaField` |
| quality-action-plans | ✅ `NativeTextAreaControl` |
| cultura-delpi | ✅ `CulturaNativeTextAreaControl` |
| propostas-comerciais | ✅ `PcNativeTextAreaControl` |
| tv-dashboard | ✅ select/textarea + input FormatPane/ribbon (`NativeTextControl` / `NativeCheckboxControl`) |
| auditoria-5s | ✅ catálogo → `NativeTextControl` / `NativeTextAreaControl` |

## Kits locais (wrappers finos)

| Plugin | Arquivo | Export |
|--------|---------|--------|
| minha-delpi-chat | `chatNativeFormFields.ts` | `ChatNativeTextAreaControl` |
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

Nova ocorrência de `<select>` / `<textarea>` (qualquer MFE) ou `<input>` auditável em `tv-dashboard` → **bloqueante**.
Documentar exceção temporária só em `KNOWN_ALLOWLIST` com motivo explícito.

## Referências

- [refactoring-roadmap.md](./refactoring-roadmap.md) §7
- Canônicos: `NativeSelectControl`, `NativeTextControl`, `NativeCheckboxControl`, `NativeTextAreaControl`, `createDashboardNativeFormFields`
- Playbook TV §19.17 (Onda 4N)
