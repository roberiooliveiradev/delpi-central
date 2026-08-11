# Código de Ética — plugin Minha DELPI

Microfrontend (Module Federation) para consulta ao **Código de Ética** institucional da DELPI (leitura de PDF no navegador).

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `codigo-etica` | Cabeçalho institucional + visualização do PDF |

```text
Portal (com conta)
  → /apps/codigo-etica
      → PDF /apps/codigo-etica/documents/codigo-de-etica.pdf

Público (sem conta)
  → /p/codigo-etica/codigo/aberto
      → o mesmo PDF, sem login
```

## Permissão

| Código | Uso |
|--------|-----|
| `codigo-etica.access` | Abrir o app e consultar o Código de Ética |

## Documento PDF

Arquivo esperado em `public/documents/codigo-de-etica.pdf` (ver README nessa pasta).

Link público: `/p/codigo-etica/codigo/aberto` (copiável no próprio plugin). O PDF em `/apps/codigo-etica/documents/` já é servido pelo gateway sem JWT.

## Desenvolvimento local

```bash
cd plugins/codigo-etica
npm install
npm run lint
npm run build
```

Standalone: `npm run dev` → `http://localhost:5173/apps/codigo-etica/`.

Registrar manifesto (quando autorizado — etapa futura):

```bash
TOKEN=$(bash infra/scripts/get-dev-token.sh) bash plugins/codigo-etica/scripts/register-manifest.sh
```

## Docker

Container: `delpi-codigo-etica` (Compose profile `plugins` em dev).
