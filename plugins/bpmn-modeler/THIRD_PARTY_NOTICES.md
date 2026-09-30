# Third-Party Notices — BPMN Modeler (Meu Modelador de Processos)

Componentes de terceiros distribuídos com este plugin e respectivas
licenças/obrigações, conforme conjunto congelado da V1
(FRONTEND-EDITOR-UX-SPEC-FREEZE / SECURITY-PERSISTENCE-RUNTIME-SPEC-FREEZE).

## Runtime / shipped dependencies

| Pacote | Versão | Licença | Observações |
|---|---|---|---|
| `bpmn-js` | 18.30.1 | bpmn.io License (ver LICENSE do pacote) | **Obrigatório manter o badge "Powered by bpmn.io" visível no canvas.** É proibido remover, ocultar ou ofuscar o watermark. |
| `bpmn-moddle` | 10.3.1 | MIT | Serialização BPMN 2.0 XML. |
| `bpmn-js-properties-panel` | 5.65.1 | MIT | Properties panel do editor. |
| `@bpmn-io/properties-panel` | 3.55.0 | MIT | Base do properties panel (peer). |
| `diagram-js` | 15.27.1 | MIT | Transitivo via `bpmn-js`. |
| `camunda-bpmn-js-behaviors` | 1.18.0 | MIT | Transitivo via `bpmn-js-properties-panel`. |
| `elkjs` | 0.12.0 | EPL-2.0 (eleita sobre GPL-3.0-or-later do dual license) | Execução exclusiva em Web Worker (`src/layout/`). |
| `@originjs/vite-plugin-federation` | 1.4.1 | MIT | Module Federation — implementação canônica da plataforma DELPI (ver nota abaixo). |
| `react` / `react-dom` | 19.2.7 | MIT | Singleton via Module Federation do host. |
| `lucide-react` | ^0.576.0 | ISC | Ícones. |

## Tooling / dev dependencies (não distribuídos no bundle)

| Pacote | Versão | Licença |
|---|---|---|
| `@playwright/test` | 1.62.1 | Apache-2.0 |
| `vite` | ^7 | MIT |
| `typescript` | ~5.9 | Apache-2.0 |
| `eslint` + plugins | ^9 | MIT |

## Obrigações específicas

- **bpmn.io attribution**: o editor renderizado pelo `bpmn-js` exibe o badge
  "Powered by bpmn.io". Esta atribuição é condição de uso da bpmn.io
  License e **não pode ser removida, coberta ou ofuscada** por CSS,
  overlay ou patch de renderização.
- **elkjs (EPL-2.0)**: uso como biblioteca (dynamic import em Web Worker);
  modificações ao elkjs exigiriam publicação do código alterado — não
  modificamos o pacote.
- **MIT/ISC/Apache-2.0**: copyright notices preservados nos pacotes
  distribuídos (`node_modules`) e reproduzidos aqui.

## Nota — Module Federation

O freeze P6 lista `@module-federation/vite@1.4.1`. A implementação segue a
convenção canônica do monorepo: `@originjs/vite-plugin-federation@1.4.1`
(mesma versão), compartilhada por todos os MFEs via
`plugins/vite/federation.shared.ts` + `federationReactProxyFix`. A divergência
de nome de pacote está registrada como EXECUTION_DRIFT no corrective gate —
a troca de implementação exigiria decisão explícita e invalidaria a
integração compartilhada com o portal.
