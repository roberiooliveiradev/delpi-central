# Prompt para o Cursor — UI review, U14 (refinamento visual e defeitos da seleção)

> Versão 2 (15/11/2026): substitui a versão com Y1–Y6. O conteúdo é o mesmo, agora organizado em
> requisitos com AC em [review-3.md](../review-3.md), em fases, com verificação independente.

```text
PROMPT CURSOR — UI REVIEW · U14 — refinamento visual da Auditoria de Entradas, defeitos da seleção
nos gráficos e saída da CLARA de dentro do Portal — com o verificador (delpi-verifier) em cada fase

CONTEXTO
O Claude inspecionou em PROD a entrada da Auditoria e a análise 07–13/11 depois da U13. O owner aprovou
os apontamentos, achou o defeito do «Limpar seleção» e decidiu: a CLARA é um MCP usado no ChatGPT/
Claude, não um assistente dentro do Portal.

FONTE DE VERDADE
docs/12-roadmap-e-evolucao/controllership-finance/ui-review/
  review-3.md  ← requisitos RQ-U14-* com AC-* (problema medido, causa no código, critério)
  track.md §11 ← fases, gates e verificação
Padrão visual (§9.3, §14, §15, §16, §18, §22), reuse map, Comercial como referência viva
(CustomersPage para filtros no hero; SatisfactionSurveysPage para tabela). AGENTS.md § Verificação
e agent-kit/verifier/project-contract.md (ciclo do executor).

FASES — executar F0 → F5 sem parar entre fases (só nas paradas), na ordem:

F0  Rebaseline: HEAD, git status (há WIP de outros agentes — não tocar), suítes do MFE e da BFF.
    Reproduzir o defeito RQ-U14-SEL em HML e tirar os screenshots «antes» (1440/1024/390).
F1  Defeito da seleção — MFE (AC-SEL-1, -2, -4, -5 parte MFE). Pequeno e de alto impacto: vai sozinho.
    → verificação → commit → HML → PROD (tag rollback-ui-review-u14-f1-controllership-finance).
F2  BFF aditiva (AC-BFF-1..4) e o lado MFE de AC-SEL-3 (gráfico de seleção não filtra a si mesmo)
    → verificação → commit → HML.
F3  Entrada + indicadores + hero (RQ-U14-ENT, RQ-U14-KPI) → verificação → commit → HML.
F4  Gráficos + abas + tabela (RQ-U14-GRA, RQ-U14-TAB) → verificação → commit → HML.
F5  CLARA fora do Portal (RQ-U14-CLARA) + README realKit (AC-DOD-5) → verificação → commit → HML;
    depois PROD de F2–F5: tags rollback-ui-review-u14-controllership-finance-api e
    -controllership-finance; BFF primeiro, depois MFE. Parar e pedir os prints ao owner.

VERIFICAÇÃO (AC-DOD-4) — obrigatória em cada fase, ANTES do commit/push e do deploy
1. Gravar o pedido em <git-dir>/delpi-verifier/requests/u14-f<N>-r<rodada>.md (nunca no working tree):
     PEDIDO DE VERIFICAÇÃO
     objetivo: U14 fase F<N> — <RQ-U14-* da fase> com os AC-* copiados de review-3.md
     escopo: working tree (só os caminhos da fase; listar)
     alegacoes: o que mudou, testes rodados e resultado, screenshots/HML feitos
     modelo_executor: <seu modelo>
     rodada: 1
2. Rodar: python ~/.delpi-agent-kit/verify.py --request-file <arquivo>
3. OC-*: corrigir no código de produção ou contestar com evidência (arquivo:linha, comando, saída).
   Nunca alterar teste, runner ou limite para passar. Rodada + 1 com ordens_anteriores; máximo 3.
4. DECISION_REQUIRED ou EXECUTION_DRIFT → PARAR e devolver ao owner.
5. Veredito sem edição e tabela de rodadas no report de cada fase.
O verificador não faz deploy, não sobe container e não escreve em HML/PROD (AGENTS.md B).
Se o verify.py ficar indisponível (exit 3, INCONCLUSIVE «verificador indisponível»), registrar e PARAR
— não seguir sem verificação.

REGRAS INEGOCIÁVEIS
1. main, sem branch/worktree; git add só com caminhos explícitos (nunca -A, ., commit -a); push por fase.
2. Componentes do kit pelos adaptadores Cf*; não mexer no plugin-ui (faltou algo → registrar e PARAR, V3).
3. Sem mudança de regra de negócio nem de permissão; contrato só aditivo, documentado no §6.
4. Sem dado real no repositório; screenshots fora do git.
5. Paradas V1–V6 do track §2. Página não aberta = INCONCLUSIVE. Smoke não executado ≠ PASS.

REPORT (ao parar)
Por fase: o que mudou, SHA, testes, antes/depois nos três tamanhos, veredito do verificador sem edição
e tabela de rodadas. Quadro final com cada AC-* de review-3.md: PASS | FAIL | INCONCLUSIVE + evidência.
F4: largura da tabela de ocorrências em 1440 antes/depois. F2: como a descrição da TES chegou.
```
