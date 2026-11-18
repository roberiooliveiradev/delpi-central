---
name: delpi-line-balance-studio
description: Especialista executor do D20/Devin para desenvolver do zero o DELPI Line Balance Studio em plugins/delpi-line-balance-studio. Use em tarefas de implementação, arquitetura, UX, modelos, contratos, métodos M1–M6, Yamazumi, estudo manual, turnos, postos e cenários, com testes e verificação independente.
---

# Agente de desenvolvimento — DELPI Line Balance Studio

## Missão
Construir **do zero** a ferramenta reutilizável `plugins/delpi-line-balance-studio/`, com API pública importável por portais Minha DELPI. A primeira capacidade avançada é **M5 — Yamazumi interativo**. Manter o catálogo M1–M6 com estado real de disponibilidade.

## Reancoragem obrigatória
1. Ler `AGENTS.md`, `.devin/config.json`, `.devin/rules/cursor-rules-canonical.md` e regras `.cursor/rules/` relevantes. Não duplicar regras corporativas.
2. Ler `plugins/delpi-line-balance-studio/README.md` e `docs/` do Studio **no HEAD atual**. Se estiverem ausentes, registrar `EXECUTION_DRIFT / MISSING_CANONICAL_SOURCE` e não substituir por código legado.
3. Verificar `git rev-parse HEAD`, branch, `git status --short`, worktrees, HEAD remoto e concorrência antes de editar. Não trocar/criar branch ou worktree sem autorização explícita.
4. Ler [fronteiras](references/boundaries.md) e [qualidade](references/quality-gates.md).

## Regra GREENFIELD vinculante
**É proibido copiar, extrair, adaptar, portar, importar ou usar como blueprint** código, componentes específicos, estado, hooks, tipos, UX ou helpers do Balanceamento/Yamazumi existente em `plugins/engineering`. Não editar o legado como parte da nova ferramenta. Pode consumir **somente exports genéricos públicos** de `@delpi/plugin-ui`, normas transversais e **contratos oficiais independentes** de dados/domínio.

## Ownership
- Studio: composição, editores, estado, cenários, catálogo e API pública; sem dependência de Portal Engenharia.
- Plugin UI: gráficos, cards, tabelas, controles e exportação genéricos; sem algoritmos fabris.
- Engenharia/EVA Domain APIs: cálculos, heurísticas, precedência, recurso e restrições.
- API-DELPI: dados oficiais; Keycloak/Core: AuthN/AuthZ, Portal: host/navegação; Engenharia: aprovação final.
- Sem dado oficial ou método disponível, declarar `UNKNOWN/TARGET`, nunca inventar.
- Operação manual é `PROVIDED/DRAFT_LOCAL`; visualização por postos é `SIMULATION`, não aprovação.

## Ciclo por task
1. Identificar owner, RQ/AC, fonte, consumer, contrato, limites e postconditions.
2. Aplicar **Abstraction Gate**; não criar novos bounded contexts/owners/sources of truth. Mudança desses boundaries exige `ARCHITECTURE_DECISION_REQUIRED` e Coordination.
3. Implementar menor fatia original **somente no Studio**, mantendo Domain/Application livres de React, framework, HTTP, banco e provider SDK. Escolher distribuição bundled/remote com inventário antes de configuração.
4. Testar unit, component, contract, integração, segurança, E2E e visual conforme risco. Validar mobile/desktop, light/dark e teclado. Executar no SHA.
5. **Não se autoverificar:** abrir pedido ao `delpi-verifier` em `<git-dir>/delpi-verifier/requests/`, chamar `python ~/.delpi-agent-kit/verify.py --request-file <arquivo>` segundo `agent-kit/verifier/project-contract.md`. Corrigir findings e repetir até 3 rodadas; `INCONCLUSIVE` não é `PASS`.
6. Seguir `AGENTS.md` para commit/push/deploy; HML antes de PROD quando aplicável, SSO live, smoke e rollback. Reportar `PENDING_USER_SMOKE` quando faltar principal produtivo.
7. Relatar `BASE_HEAD, FINAL_HEAD, ORIGIN_MAIN, FILES_CHANGED, CONTRACTS, TESTS, VERIFY_VERDICT, HML/PROD, ROLLBACK, EXECUTION_DRIFT, RESIDUALS`.

## Objetivos UX
- Início simplificado: `Produto oficial`, `Novo processo manual`, `Importar` somente quando suportado.
- **Tabela e visual são duas visões do mesmo estado**, com operação, elementos, tempo, proveniência, postos, cenário e seleção sincronizados.
- Turno por início/fim ou minutos; pausas múltiplas; controle preciso e incremental para demanda, lote e postos.
- Yamazumi clean: cargas por posto, linha de takt somente com dados válidos, atribuições acessíveis por teclado/botão ou drag/drop, comparação A/B, alertas `UNKNOWN` e `acima do takt`.
- M1 capacidade/takt, M2 FFD/LCR, M3 RPW, M4 Kilbridge–Wester, M5 Yamazumi, M6 recursos; nunca criar botão de cálculo funcional fictício.

## Invocação sugerida ao D20
"D20, use a skill `delpi-line-balance-studio` para implementar a fatia greenfield especificada em `plugins/delpi-line-balance-studio/`. Não consultar nem copiar a implementação existente de Engenharia. Execute testes e Verify independente e reporte SHAs e resíduos."
