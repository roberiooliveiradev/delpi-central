# Gates e evidências do agente D20

## G0 — Antes de alterar
- Ler `AGENTS.md`, rules relevantes e autoridades; confirmar HEAD, branch, status, worktrees, origem, mudanças concorrentes e RQ/AC.
- Inventariar apenas libs genéricas e contratos oficiais. **Não abrir o código legado do Yamazumi da Engenharia para derivar implementação.**
- Definir interfaces, erros, limites, AuthZ, provenance, rollback antes do código.

## G1 — Isolamento
- Nenhum import de `plugins/engineering` ou `features/products/routing` no Studio.
- Domain/Application puros, nenhum solver escrito dentro do MFE/Plugin UI.
- Estudo manual com identificação própria; nunca fingir código oficial.
- Port/adapters explícitos para fontes, motor, contexto e draft.

## G2 — Testes
- Modelo/contrato: IDs, duplicidades, provenance, tempo `null` ≠ zero, setup e lote.
- Turnos: horários/minutos, pausas múltiplas, sobreposição, meia-noite, inválidos.
- Yamazumi: atribuição exclusiva, operação não atribuída, sobre-takt, categorias reais/UNKNOWN, sincronia tabela↔visual.
- Segurança: 403/404, AuthZ revogada, segredo/token ausente do estado e export.
- UX: 1440/1024/390/320, teclado, dark/light, sem overflow, focus e labels.

## G3 — Verify
Executor testa seu trabalho, mas **não é o verificador independente**. Seguir `agent-kit/README.md` e `agent-kit/verifier/project-contract.md`: pedido ao `delpi-verifier`, até 3 ciclos de correção, saída literal do veredito. Sem auth: `INCONCLUSIVE`, não PASS.

## G4 — Entrega
Commit/push, HML e PROD apenas conforme `AGENTS.md` e gates de risco. Logs/evidências no SHA correto. Sem login humano no PROD: `PENDING_USER_SMOKE`; não declarar aceite. Relatório final com diffs, testes, Verify, DRIFT, residuals e rollback.
