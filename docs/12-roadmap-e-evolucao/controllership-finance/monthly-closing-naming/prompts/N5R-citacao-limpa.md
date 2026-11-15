# Prompt para o Cursor — Monthly closing naming, N5R (citação sem número de documento)

```text
PROMPT CURSOR — MONTHLY CLOSING NAMING · N5R — citação mostrada ao usuário sem referência interna

CONTEXTO
Verificação do Claude pela CLARA em PROD (14/11/2026, corpus ad25f991…, 121 fontes, 2637 itens):
ACCEPT_WITH_RESIDUAL. PASS: instruções do conector sem o código; título «Ficha do Fechamento mensal
da Controladoria»; PROC-0072 só em §Identificação («Código no Transformômetro (TÉO)») e a pergunta
pelo código do TÉO acha essa linha; display_citation e source_title presentes.

RESIDUAIS
R1 display_citation carrega referência interna que vem do título da seção:
   «Ficha do Fechamento mensal da Controladoria › Modelo operacional (doc 118 §2)»,
   «Ficha R10 — Despesas por Centro de Custo › Regras de negócio (doc 85 §10 + doc 126 §§14–19)».
   A diretiva da CLARA proíbe mostrar número de documento de projeto, mas o campo feito para o
   usuário mostra.
R2 Segmento repetido quando a seção é o próprio título:
   «Ficha do Fechamento mensal da Controladoria › Ficha do Fechamento mensal da Controladoria».

MISSÃO
1. display_citation: tirar da parte da seção os parênteses com referência interna
   (padrões «(doc …)», «(docs …)», «(GATE …)», «(D-…)»); se a seção ficar igual ao source_title ou
   vazia, mostrar só o source_title. Não mudar heading_path nem citation_locator (auditoria).
2. Teste: os dois exemplos acima e um sem parênteses; e um teste que percorre os itens publicados e
   falha se display_citation contiver «doc », «GATE», «CF-», «PROC-» ou caminho de arquivo.
3. HML → PROD da BFF (tag rollback-monthly-closing-naming-n5r-controllership-finance-api). Se o
   display_citation é calculado na leitura, não precisa republicar o corpus; se é gravado, republicar.
4. Registro no track.md.

REGRAS
As da trilha (main sem branch; git add só com caminhos explícitos; sem migration aplicada editada;
sem tool nova). Parar ao concluir.
```
