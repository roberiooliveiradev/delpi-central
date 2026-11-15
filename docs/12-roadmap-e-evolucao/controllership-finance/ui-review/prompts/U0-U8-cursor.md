# Prompt para o Cursor — UI review, U0 a U8

```text
PROMPT CURSOR — UI REVIEW · U0 → U8 (Portal Controladoria & Finanças no padrão visual dos Portais)

CONTEXTO
O owner revisou em PROD o Início e a Auditoria de Entradas e pediu: componentes do plugin-ui,
alinhamento e dimensionamento corretos, desktop/tablet/celular, visual limpo, ícones, ajuda nos
botões, hero nas páginas e o mesmo padrão do restante do Portal. O diagnóstico está em review.md:
as páginas já usam os adaptadores Cf* do plugin-ui; o problema é composição, vocabulário
(cte/item/header/CTE/NFE na tela), formatação (170.00 em vez de R$ 170,00), severidade só em texto,
donut em azul, estados (página só com «Carregando análise…»), dimensionamento (form em largura
total, KPI órfão, gráficos soltos, metade da tela vazia) e falta de PagePath, ícones e ajuda.

FONTE DE VERDADE
docs/12-roadmap-e-evolucao/controllership-finance/ui-review/
  review.md  ← diagnóstico G1–G9, H1–H3, E1–E3, A1–A9, O, F
  track.md   ← etapas U0–U8, regras, paradas V1–V6, layout alvo da análise, HML, PROD
Padrão: docs/11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md (§8–§24),
docs/12-roadmap-e-evolucao/controllership-finance/30-plugin-ui-reuse-map.md,
entry-audit/frontend/01–04 e o Portal Comercial como referência viva.
Autoridade: instruções oficiais do arquiteto e .cursor > padrão visual > reuse map > docs do front >
track.md > review.md.

MISSÃO
Executar U0 → U8 sem parar entre etapas, um commit por etapa (U6: um por página), documentando no
track.md, publicando em HML e depois em PROD. Parar SOMENTE em V1–V6 ou ao concluir U8.

REGRAS INEGOCIÁVEIS
1. main, sem branch; git add só com caminhos explícitos (nunca -A, ., commit -a); push a cada etapa.
2. Componente do kit pelo adaptador Cf*; nada de tabela, card, hero, badge ou gráfico em CSS local.
   Mudança no plugin-ui só aditiva, com caracterização e prova dos consumidores.
3. Sem mudança de regra, contrato ou permissão. Dado que a BFF não entrega → V4 (listar).
4. DoD por página: 1440/1024/390, claro e escuro, teclado e foco, estados do §16, ajuda no mesmo gate.
5. Evidência: screenshots (no report, não commitados), Playwright, axe sem violação séria nova.
6. U7: criar no Keycloak de HML usuários de teste por perfil (access; access+manage; access+LNF;
   DRE) com senha só no .env.hml; nunca em PROD; nunca copiar segredo de PROD.
7. Página não aberta = INCONCLUSIVE. Sem dado real no repositório.

REPORT (ao parar)
Por etapa: o que mudou, SHA, testes, evidência. U0: matriz de conformidade e tempo de abertura da
análise. U4: antes/depois do resultado da análise nos três tamanhos. U6: lista de páginas corrigidas
e lista de decisão (V5). U7: resultado por perfil. U8: tags, imagens, páginas abertas em PROD,
números da análise iguais aos da CLARA. Quadro final.
```
