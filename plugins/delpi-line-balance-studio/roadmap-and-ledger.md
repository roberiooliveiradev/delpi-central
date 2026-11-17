# Roadmap operacional e ledger de evidências

**Produto:** DELPI Line Balance Studio. **Data inicial:** 2026-11-17. **Fase:** DOCUMENTATION / DESIGN / READY_FOR_BOUNDED_TASKS.

## Marco de produto
O Product Owner autorizou criar `plugins/delpi-line-balance-studio/` como ferramenta reutilizável com seleção dos métodos M1–M6. Portal Engenharia é primeiro consumer. A implementação existente na rota `/apps/engineering/processes/line-balancing` é baseline V3, não Studio V4 importável.

## Fases
| Marco | Entrega | Estado | Evidência requerida |
|---|---|---|---|
| D0 | Pasta e contrato inicial | PROVEN no GitHub | README + commit |
| D1 | Docs de arquitetura, UX, contratos, métodos, testes | DOCUMENTED | estes arquivos + SHA |
| I0 | Inventário técnico e API pública validada | PLANNED | source inventory + tests |
| I1 | Extração sem regressão + primeiro consumer real | TARGET | build + E2E |
| I2 | Entrada MANUAL e editor de operações | TARGET | tests + provenance |
| I3 | Turnos e pausas interativos | TARGET | schedule tests |
| I4 | Tabela e Yamazumi sincronizados | TARGET | component E2E |
| I5 | Comparador e exportações multi-origem | TARGET | screenshots + exports |
| I6 | HML→PROD, Verify, smoke | TARGET | SHA, URL, AuthZ, Verify |
| M2+ | Métodos avançados incrementais | TARGET | novas tasks e contratos de domínio |

## Escopo de primeiras tasks
**STUDIO-I0:** inventário concreto, identificar pontos de acoplamento e decidir consumption mode por evidência.
**STUDIO-I1:** criar exports públicos tipados, migrar Portal Engenharia para consumer, regressão total.
**STUDIO-I2:** dados MANUAL e tabela de operações, tempos e atributos.
**STUDIO-I3:** ShiftScheduleEditor, pausas múltiplas, prévia.
**STUDIO-I4:** Yamazumi visual/tabela + cenários; Verify, HML, PROD.

Esses IDs são sugestões para tracking, não issues já criadas.

## Log inicial
- **2026-11-17:** D0: `plugins/delpi-line-balance-studio/README.md` criado. `PROVEN`.
- **2026-11-17:** Master V3 atualizado para reconhecer novo Studio reutilizável. `PROVEN`.
- **2026-11-17:** D1: documentação e estrutura de pastas (esta execução). `DOCUMENTED`; nenhum runtime criado.

## Residuais
- Prova de segundo consumidor: `PENDING`.
- Definição de empaquetamento: `TO_INVENTORY`.
- Contrato real de estudo MANUAL: `TARGET`.
- Tempo por categoria e precedências oficiais: `UNKNOWN` até inventário.
- Verify/CI e HML/PROD da versão Studio V4: `TEST_NOT_RUN`.

**Nunca transformar documentação em estado DELIVERED.**
