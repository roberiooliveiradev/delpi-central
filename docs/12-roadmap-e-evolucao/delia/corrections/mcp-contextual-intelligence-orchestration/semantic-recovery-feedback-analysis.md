# Feedback model-visible — análise do caminho B1 (sem mudança funcional)

TASK_ID: DELIA-C3-PYDANTIC-AI-SEMANTIC-RECOVERY-AND-NONPROGRESS-REMEDIATION-01
BASE_HEAD: 3f9f3c7f3279f8c7ae844177bf914ee2cd1287ff

## Cadeia verificada

Owner 400 → GovernedCapabilityAttempt(status, error_code, content,
limitations) → _attempt_projection (pydantic_ai_investigation.py:377)
→ tool result ao modelo contendo:

- `status` (tentativa falha)
- `error_code` (p.ex. validation/400 family)
- `content` — mensagem sanitizada do owner: "visão departamento exige
  filial_id e setor_id" (cap 2000 chars)
- `limitations` (bounded)
- `root_code` extraído de data.root.code
- `evidence_citable: false` para erros (classificação correta)
- `observation_index` / provenance / action_id

## Veredicto Fase A

FEEDBACK_PROJECTION_DEFECT = NOT_PROVEN. O modelo recebeu: (a) erro
recuperável classificado, (b) nome dos campos ausentes, (c) contexto
da chamada, (d) histórico preservado, (e) catálogo com teo.read
entity=branch disponível para obter filial_id. A informação era
suficiente para reconsiderar estratégia; o modelo não o fez.

## Causa

H4 MODEL_BEHAVIOR: limitação do modelo (re-tenta mesma classe de erro
varrendo variantes de args em vez de resolver o identificador
ausente via READ ou mudar de view) + H1 OWNER_CONTRACT (requisito
condicional só no erro runtime — já documentado na proposta TÉO).

## Fase F — dedup por error-class

O fingerprint atual bloqueia chamada IDÊNTICA — correto: mesmo
error_code ≠ mesma tentativa (escopos diferentes são legítimos).
Estender para "N falhas consecutivas mesma error_class" exige
política de execução (arbitrar N, distinguir correção parcial de
repetição) = decisão de produto → ARCHITECTURE_DECISION_REQUIRED,
não implementável como bugfix pontual.

## Conclusão

Nenhuma correção local comprovada. Alternativas já documentadas:
(1) proposta contratual TÉO analyze (owner approval pendente),
(2) política de dedup por classe de erro (decisão arquitetural).
