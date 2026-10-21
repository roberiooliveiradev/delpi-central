# F02-A-R1 — Starter suggestions visíveis em produção — evidência de execução

- **Data:** 2026-10-21
- **Task:** DELIA-UX-F02A-R1-PRODUCTION-DEFAULT-STARTERS-01
- **Spec:** 93 §16 (decisão de produto — quatro perguntas por padrão)
- **Base de reancoragem:**  (worktree rebased sobre origin/main após  e )
- **SHA testado (impl):** 
- **Evidência anterior:** starter-suggestions-f02a-evidence.md (F02-A, gate QA)

## 1. Correção aplicada (menor diff)

 deixou de depender de  e retorna a lista congelada  para todo usuário admitido à aplicação. O seam permanece como ponto único para a futura projeção de elegibilidade por sessão (spec §16). Arquivos tocados:

-  — resolver sem parâmetro; comentários atualizados (§16).
-  — chamada sem ; comentário atualizado.  segue usado apenas para os turns demo.
-  — testes reescritos para o comportamento padrão + gate de ocultação após turn.

**Não tocado:**  (admissão  +  intacta), plugin-ui (componente render-only sem mudança), backend, Core/RBAC, Keycloak, MCPs, VD-F05, qualquer contrato de sugestões.

## 2. Resultados de teste (medidos)

| Verificação | Resultado |
|---|---|
| Vitest plugins/delia | **276/276** (22 arquivos; inclui 8 testes starter-suggestions e suíte demo-mode completa — outros gates preservados) |
| Typecheck plugins/delia | PASS |
| Build plugins/delia | PASS |
| Browser QA local em bundle de produção (sem , sem ) | **40/40 PASS** |

## 3. Browser QA — produção-paridade (localhost, sem parâmetros)

Contextos executados com a imagem  reconstruída **sem**  (paridade com produção) e URL  pura:

-  +  — seção visível com URL limpa.
- ,  — 4 cards, grid 2 colunas em 1440px.
- , ,  — rótulo Explore
