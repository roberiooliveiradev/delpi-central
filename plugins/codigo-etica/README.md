# Código de Ética — plugin Minha DELPI

Microfrontend (Module Federation) para consulta ao **Código de Ética** institucional da DELPI (leitura de PDF no navegador).

## Visão geral

| Camada | Responsabilidade |
|--------|------------------|
| **MFE** `codigo-etica` | Cabeçalho institucional + visualização do PDF |

```text
Portal → /apps/codigo-etica
           ↓ Module Federation (remoteEntry.js)
         MFE codigo-etica
           ↓ iframe (leitor nativo)
         /apps/codigo-etica/documents/codigo-de-etica.pdf
```

## Permissão

| Código | Uso |
|--------|-----|
| `codigo-etica.access` | Abrir o app e consultar o Código de Ética |

## Documento PDF

Arquivo esperado em `public/documents/codigo-de-etica.pdf` (ver README nessa pasta).

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

Container previsto: `delpi-codigo-etica` (Compose ainda não configurado nesta etapa).
