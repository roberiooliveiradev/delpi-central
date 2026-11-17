# DELPI Line Balance Studio

**Decisão vinculante — 2026-11-17:** ferramenta **GREENFIELD**, independente, reutilizável em portais Minha DELPI. **Estado: AUTHORIZED / DOCUMENTED / IMPLEMENTATION_NOT_STARTED**.

## Regra de isolamento

**Não reutilizar a implementação existente de balanceamento do Portal Engenharia.** Proibido copiar, extrair, portar, adaptar ou importar a lógica, os modelos, hooks, componentes específicos, estados, UX ou helpers de `plugins/engineering` (inclusive `LineBalancingPage.tsx`, `yamazumi.ts`, `PostConfigurator` e `ProductRoutingTab.tsx`). Essa implementação continua em produção como LEGACY, intocada, e não serve como blueprint do novo Studio. A autorização do PO é para **construção do zero nesta pasta**.

São permitidos e incentivados: `@delpi/plugin-ui` (design system corporativo e componentes **genéricos públicos**), padrões transversais e **contratos oficiais** de domínio e fonte de dados, sem acoplamento ao código da experiência antiga.

## Escopo integrado

Um único Studio para escolher entre **M1 Capacidade e takt**, **M2 FFD/LCR**, **M3 RPW**, **M4 Kilbridge-Wester**, **M5 Yamazumi interativo**, **M6 Dimensionamento de recursos**. M5 é a primeira entrega; os demais mantêm status verdadeiro de planejamento/capability.

### Experiência inicial
- Criar estudo por produto oficial, processo **manual sem SKU** ou importação futura.
- Editar operações, elementos, tempos e origens em **tabela e visual sincronizados**.
- Configurar turnos por horários ou minutos, adicionar múltiplas pausas, demanda, lote e postos.
- Montar postos, atribuir tarefas e visualizar Yamazumi contra takt, com cenários A/B.
- UI clean, responsiva e acessível; dados `OBSERVED/PROVIDED/CALCULATED/SIMULATION/UNKNOWN` honestos.

### Ownership
- **Studio:** aplicação/workspace reutilizável com API pública.
- **Plugin UI:** gráficos, tabelas, controles genéricos, exportações e tema.
- **Engineering/EVA domain:** matemática, métodos, restrições e viabilidade.
- **API-DELPI:** dados oficiais; **Keycloak/Core:** AuthN/AuthZ; **Engenharia:** aprovação de processos oficiais.
- **Portais:** adapters de integração/autorização e navegação; Portal Engenharia é o primeiro consumidor **futuro**, nunca dependência do Studio.

**Não criar um motor de cálculo ou source of truth em React/Plugin UI.** Estudos manuais são `DRAFT`; não fingir cálculo oficial sem contrato do domínio.

## Documentação

[Índice e documentos](docs/INDEX.md): arquitetura, modelo, wireframes, seis métodos, Yamazumi e roadmap.

Estrutura de código **planejada, ainda não criada**: `src/app/`, `src/model/`, `src/ports/`, `src/methods/catalog/`, `src/methods/yamazumi/`, `src/features/{study-origin,operation-editor,shift-editor,station-editor,scenario-comparison}/`, `src/ui/`, `tests/`.

A distribuição futura (bundled/remote) depende do inventário de convenções oficiais do monorepo. **Sem package.json ou build fictício nesta entrega documental.**

## Evidência

Este README e os documentos **não** são teste, código executável, verify ou deploy. Manter status `DOCUMENTED / TEST_NOT_RUN` até implementação real com SHA e resultado.
