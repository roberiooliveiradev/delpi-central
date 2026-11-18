# DELPI Line Balance Studio

Ferramenta greenfield para estudos de balanceamento de linha na Minha DELPI. O Portal Engenharia é o primeiro consumidor previsto. A biblioteca mantém o modelo de estudo e a entrada pública para futuros editores e portais.

A v0.1 inclui criação de estudos manuais, operações com tempos informados ou desconhecidos, postos, cenários, condições de produção, resumo de turnos e catálogo M1–M6. A próxima interface a desenvolver é o Yamazumi, com visual e tabela sobre o mesmo estudo.

Veja o [contrato público e os critérios de aceite](docs/contracts.md).

## Validação

Com Node.js 22 ou superior e npm, execute na pasta do pacote:

```sh
npm ci
npm test
```

A suite compila TypeScript e verifica a API pública de `@delpi/line-balance-studio`. O código distribuível e as declarações ficam em `dist/`.

## Interface e demonstração

O subpath `@delpi/line-balance-studio/ui` exporta o elemento reutilizável. Consulte o [contrato da interface](docs/preview.md) para integrá-lo a outro host. A demonstração usa somente dados fictícios e mantém alterações em memória.

Para validar a demo sem containers:

```sh
npm ci
npm run build:preview
python -m http.server 8080 --directory preview-dist
```

Abra `http://localhost:8080`. No GitHub, selecione **GitHub Actions** em **Settings → Pages → Source**. O workflow **Line Balance Studio · GitHub Pages** publica somente `preview-dist` e pode ser disparado novamente a partir da `main`.
