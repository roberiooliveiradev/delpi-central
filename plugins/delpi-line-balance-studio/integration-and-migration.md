# Integração e extração progressiva

**Status:** IMPLEMENTATION_PLAN / NOT_EXECUTED. Primeira integração: Portal Engenharia > Processos > Balanceamento.

## Inventário observado
- `plugins/engineering/src/features/processes/line-balancing/LineBalancingPage.tsx` é implementação atual do workspace V3, acoplada a `../../products/api/productApi`, tipos e componentes de routing.
- `plugins/engineering/src/features/processes/line-balancing/yamazumi.ts` implementa helpers puros de apresentação, mas tipa entradas com `HypotheticalPost` e `RoutingOperationView` da área de Produto.
- `plugins/engineering/src/features/processes/line-balancing/methodCatalog.ts` já enumera M1–M6.
- `plugins/plugin-ui/package.json` contém `recharts` e componentes genéricos; `plugins/shared-libraries.manifest.json` cadastra Plugin UI (federation-remote) e outras bibliotecas bundled.
- Não existe ainda implementação da API pública do Studio, build, pacote npm validado ou conexão de segundo consumer.

## Sequência de menor risco
1. Congelar baseline do MFE Processos e Ficha do Produto (SHA, visual, E2E).
2. Definir adaptadores tipados e testes de contrato; test consumer real antes de elevar abstrações.
3. Extrair modelos neutros de operações/postos/métodos, sem import de `features/products` no Studio.
4. Extrair composição das views mantendo funcionamento em V3; condicionar feature V4 por capability real, sem quebrar rotas existentes.
5. Integrar primeira origem oficial pelo adapter do Portal Engenharia usando BFF, sem SDK HTTP no Studio.
6. Implementar origem MANUAL com edição/validação, sem invocar endpoints do produto para simular cálculo.
7. Implementar turno/pausas e tabela/visual unificados.
8. Testar concorrência, identidade, cenários, storage, exportações e rollback.
9. Definir forma de distribuição com evidência (`bundled` ou `federation-remote`), **só então** atualizar manifest/build se necessário.
10. HML + Verify + produção na sequência permitida, smoke humano quando exigido.

## Contrato entre host e Studio
Host fornece adapters autorizados e contexto; recebe eventos de navegação/seleção e draft. Studio não importa `engineeringUi`, `productApi`, tokens nem route catalog do host. UI compartilhada não sabe qual portal consome.

## Rollback
Reverter apenas a integração para o workspace V3 comprovado, sem remover contratos existentes nem tocar no cálculo oficial. Logs e exports não devem conter token ou informações fora da sessão autorizada.

## Bloqueios de capability
Se análise de estudo manual não tiver contrato de domínio, mostrar edição/visualização honesta, bloquear resultados oficiais e reportar `METHOD_UNAVAILABLE`. Se não houver drag-drop genérico acessível, usar botões até a extensão justificada do Plugin UI.

## Regra de deploy
Esta entrega de documentação **não** implanta runtime novo. Futuras entregas seguem AGENTS.md e gates HML→PROD conforme escopo, com teste no SHA e Verify independente.
