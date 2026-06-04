# Screenshots de baseline (Fase 0)

Esta pasta guarda capturas **antes/depois** da refatoração do Playbook 12.

## Estrutura

```
screenshots/
  1440/
    overview-main.png
    knowledge-documents.png
    agents-specialization.png
    quality-metrics.png
    platform-tools.png
    governance-audit.png
  768/
    (mesmos nomes)
```

## Procedimento manual (DevTools)

1. Abrir o admin no Portal com tema escuro.
2. Ajustar viewport: **1440×900** ou **768×1024** (Responsive mode).
3. Navegar para cada seção/sub-aba do [CHECKLIST.md](../CHECKLIST.md).
4. Captura de página visível (`Ctrl+Shift+P` → “Capture screenshot”).
5. Salvar com o nome sugerido na subpasta do viewport.

## Script automatizado (opcional)

No plugin:

```bash
cd plugins/minha-delpi-chat
export ADMIN_BASE_URL="http://localhost:5173/apps/minha-delpi-chat/admin"
./scripts/capture-admin-baseline.sh
```

Requer Portal/MFE no ar e sessão autenticada (o script documenta limitações).

## Estado jun/2026

As imagens PNG **não estão versionadas** neste repositório (ambiente local/staging). Após capturar no seu ambiente, adicione os arquivos aqui ou anexe ao PR de baseline.
