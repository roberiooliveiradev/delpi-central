# Prompt para o Cursor — Monthly closing naming, N0 a N5

```text
PROMPT CURSOR — MONTHLY CLOSING NAMING · N0 → N5 (CLARA e Portal: «Fechamento mensal da Controladoria» no lugar de PROC-0072)

CONTEXTO
PROC-0072 é o código do macroprocesso no Transformômetro (TÉO), não o nome. O nome é
«Fechamento mensal da Controladoria». A CLARA mostra o código ao usuário porque ele está nas
instruções do conector MCP, na descrição da tool knowledge, na inteligência da CLARA e em 76 das
115 fontes da base de conhecimento. Os documentos são legítimos e continuam na base: muda o texto.

FONTE DE VERDADE
docs/12-roadmap-e-evolucao/controllership-finance/monthly-closing-naming/
  plan.md   ← origens O1–O7, decisões D1–D6, regras S1–S7, exceções §5, critério de aceite §7
  track.md  ← etapas N0–N5, regras, paradas Y1–Y6, rollback, quadro e registro
Autoridade: instruções oficiais do arquiteto e .cursor > track.md > plan.md.

MISSÃO
Executar N0 → N5 sem parar entre etapas, documentando cada etapa no mesmo commit (quadro e
registro do track.md), publicando em HML e depois em PROD com a republicação governada do corpus.
Parar SOMENTE numa parada Y1–Y6 ou ao concluir N5.

REGRAS INEGOCIÁVEIS
1. main, sem branch; commits só com os arquivos da etapa; push a cada etapa.
2. Nunca editar migration aplicada nem renomear arquivo (Y3). Identificadores de execução
   (CF-PROC0072-…), nomes de teste, SHAs e comentários de código ficam como estão (D6).
3. Troca por leitura de contexto, nunca troca cega: cada ocorrência segue S1–S7; frase redundante é
   reescrita; troca que muda o sentido → Y4 (listar e perguntar).
4. PROC-0072 fica uma única vez no texto: ficha do fechamento, §Identificação,
   «Código no Transformômetro (TÉO): PROC-0072» (D3).
5. "Central de Fechamento" continua como nome da área do Portal (D4).
6. Sem tool nova; sem mudar as seis tools da CLARA além de texto e campos aditivos
   (source_title, display_citation). Sem permission nova. Sem dado real no repo.
7. Suíte inteira da BFF comparada ao commit pai; falha nova = Y2.

REPORT (ao parar)
Por etapa: o que mudou (arquivo:linha ou contagens), SHA, testes (PASS/FAIL), evidência.
N0: tabela de ocorrências por classe (a/b/c/d) e as listadas em Y4.
N5: tag de rollback, imagens HML/PROD, versão do corpus antes/depois (fontes e itens),
critério de aceite §7 itens 1–3 com evidência. Quadro de status final.
```
