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

## UX V4 aprovada — entrada e métodos

A decisão visual do Product Owner em **2026-11-18** foi documentada em [UX V4: cards de origem e sidebar retrátil](docs/ux-v4-study-entry-and-method-sidebar.md). O início do Studio terá **dois cards grandes com ícones próprios** (`Produto DELPI` / `Estudo manual`), uma **sidebar secundária interna e recolhível** com ícone de cada método M1–M6, e **contexto de estudo compartilhado** entre métodos. Após iniciar um estudo, os cards dão lugar a um cabeçalho compacto e ao workspace. Os métodos planejados ficam em grupo discreto e não são executáveis. **Status: APPROVED_PRODUCT_DESIGN / TARGET_IMPLEMENTATION / TEST_NOT_RUN** — não é funcionalidade já entregue pela v0.1.

**Inventário Plugin UI para UX V4:** [componentes existentes, lacunas, fronteiras e ordem de desenvolvimento](docs/plugin-ui-v4-component-inventory.md). Esta etapa define contratos candidatos e não altera a interface executável.

## UX V4.1 — bancada unificada

A evolução V4.1 está documentada em [UX V4.1: bancada unificada](docs/ux-v41-unified-workspace.md). A bancada ocupa a largura útil do host (sem limite de 1280px), concentra contexto, ações (`Mais ações`), KPIs, método ativo, detalhes oficiais do roteiro e a análise oficial M1 **dentro** do Studio. O host deixa de renderizar cartões de conteúdo ao redor do elemento e passa a operar por contrato público: `analysisState`, `officialOperations`, `draftSave` e os eventos `studio-analysis-run`, `studio-export` e `studio-clear-study` (ver [contracts.md](docs/contracts.md)). O cálculo oficial M1 permanece no BFF/domínio do host.
