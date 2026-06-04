# Aprendizagem contínua — Fase 1 (fundação)

Implementação inicial do playbook `docs/roadmap/playbook-aprendizagem-continua.md`.
O objetivo é deixar o chat mais inteligente com o uso, **sem contaminar** o modelo:
aprender = observar + validar + armazenar + recuperar (playbook §2).

Esta fase entrega a **fundação não paramétrica**: candidatos de conhecimento
revisáveis, glossário/typos aprendidos por escopo, governança (safety + human-in-the-loop)
e aplicação das regras aprovadas na normalização base. Tudo atrás de feature flags,
**desligado por padrão**.

## Componentes

| Camada | Componente | Papel |
|---|---|---|
| Domínio | `ChatVocabularyLearningService` | Detecta definição explícita ("quando eu falar X é Y", "X significa Y") e candidatos de normalização (typos). Puro/sem DB. |
| Domínio | `ChatLearningSafetyGuard` | Bloqueia aprendizado tóxico/sensível: segredos, PII (CPF/CNPJ/e-mail/telefone), códigos operacionais e dados de preço/cliente (playbook §7, §26). |
| Domínio | `ChatMessageNormalizationService` | Ganhou registro de **regras aprendidas** (`set_learned_rules`/`clear_learned_rules`) aplicadas após as regras estáticas. Permanece puro. |
| Aplicação | `ChatKnowledgeCandidateService` | Orquestra captura: safety → dedup/evidência → confiança → status. Promove candidato a termo de vocabulário (playbook §14, §15, §27). |
| Aplicação | `ChatLearningCaptureService` | Captura candidatos a partir de **feedback negativo** e de **definições explícitas ditas no turno** ("quando eu falar X é Y"), com isolamento por SAVEPOINT. |
| Aplicação | `ChatLearnedNormalizationService` | Carrega termos aprovados (cache TTL) e injeta as regras no normalizador base. |
| Infra | `PostgresLearningCandidateRepository` / `PostgresVocabularyTermRepository` | Persistência. |
| Infra | Tabelas `ai_learning_candidates`, `ai_vocabulary_terms` | Migração `r0s1t2u3v4w5`. |
| Interface | `GET/POST /admin/learning/candidates*`, `GET/POST /admin/learning/vocabulary` | Revisão (aprovar/rejeitar/promover) e CRUD de termos. |

## Fluxo (Fase 1)

```
Captura (best-effort):
 a) Feedback negativo  (flag CHAT_LEARNING_CAPTURE_FROM_FEEDBACK)
    → detecta definição explícita OU candidato de normalização
 b) Turno (send/stream) (flag CHAT_LEARNING_CAPTURE_FROM_TURN)
    → detecta definição explícita dita pelo usuário, isolada em SAVEPOINT
 → ChatLearningSafetyGuard (bloqueia sensível)
 → ChatKnowledgeCandidateService.register (dedup + evidência + confiança)
   → ai_learning_candidates (status: pending)

Admin revisa em /admin/learning/candidates
 → approve | reject | promote
   → promote cria ai_vocabulary_terms (approved=true)
     → ChatLearnedNormalizationService.refresh()
       → ChatMessageNormalizationService.set_learned_rules(...)

Próximos turnos (send/stream)
 → _warm_learned_normalization() (flag CHAT_LEARNING_ENABLED + APPLY_VOCABULARY)
   → normalização passa a corrigir o typo/abreviação aprendido
```

## Confiança e governança

- Confiança em `[0, 0.95]`. Evidência repetida sobe a confiança (dedup incremental).
- Status: `pending → approved/rejected → promoted` (e `auto_approved` quando habilitado).
- **Human-in-the-loop por padrão**: auto-aprovação exige `CHAT_LEARNING_AUTO_APPROVE_ENABLED=true`
  e confiança ≥ `CHAT_LEARNING_AUTO_APPROVE_MIN_CONFIDENCE` (0.95) com risco baixo.
- Toda captura no caminho de feedback é **best-effort** (try/except): nunca quebra o feedback nem o turno.

## Feature flags (`Settings`)

| Flag | Default | Efeito |
|---|---|---|
| `CHAT_LEARNING_ENABLED` | `false` | Liga a camada (captura + aplicação). |
| `CHAT_LEARNING_APPLY_VOCABULARY` | `true` | Aplica termos aprovados na normalização (se a camada estiver ligada). |
| `CHAT_LEARNING_CAPTURE_FROM_FEEDBACK` | `true` | Captura candidatos a partir de feedback negativo. |
| `CHAT_LEARNING_CAPTURE_FROM_TURN` | `true` | Captura definição explícita dita durante o turno. |
| `CHAT_LEARNING_AUTO_APPROVE_ENABLED` | `false` | Auto-aprovar candidatos de altíssima confiança. |
| `CHAT_LEARNING_AUTO_APPROVE_MIN_CONFIDENCE` | `0.95` | Limiar de auto-aprovação. |
| `CHAT_LEARNING_VOCABULARY_MAX_RULES` | `500` | Teto de regras aprendidas aplicadas. |

## Endpoints admin

- `GET /admin/learning/candidates?status=&type=&limit=&offset=`
- `POST /admin/learning/candidates/{id}/review` — body `{ "action": "approve|reject|promote", "term?", "normalizedTerm?", "meaning?" }`
- `GET /admin/learning/vocabulary?scope=&approved=&type=&limit=&offset=`
- `POST /admin/learning/vocabulary` — cria/edita termo aprovado (ex.: regra de typo `como vc s chama → como voce se chama`).

## Não coberto nesta fase (próximas)

- KPIs de aprendizagem no painel admin (taxa de aprovação, typos corrigidos, etc.).
- `memory_items` cross-usuário/projeto com embedding, `evaluation_cases`, eventos/workers,
  pesquisa web de significado e fine-tuning offline (Fases 4–7 do roadmap).
