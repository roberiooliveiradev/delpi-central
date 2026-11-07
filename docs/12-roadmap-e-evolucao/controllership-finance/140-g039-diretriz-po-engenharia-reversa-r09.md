# Gate 039 — Diretriz do PO: engenharia reversa R09 orientada por evidência

Data: 2026-11-01. Origem: manifestação explícita do PO, posterior ao Gate 038. Escopo: PROC-0072 / R09 Faturamento × MOD (DLP204). **Registro documental; sem runtime ou deploy.**

## Diretriz autorizada

1. **Engenharia reversa antes de implementação:** reconstruir regras e o grão do R09 por triangulação entre (i) vídeo da operação e competência realmente utilizada pela operadora, (ii) DLP204.prw e rotinas/fontes TOTVS, (iii) tabelas/SQL em consultas read-only e operações/rotas existentes da api-delpi, (iv) planilha de saída Fat x MOD.xlsb. O mês/filiais/filtros vistos no vídeo precisam ser comprovados, não presumidos iguais a setembro/2026.
2. **Método:** formar hipóteses rastreáveis por campo (PA, COMP, níveis, SG1/SGG, SG2/SHY, MOD, horas, quantidade, custo) e validá-las contra linhas reais do artefato, filtros, parâmetros e exemplos obtidos na gravação; pesquisar SP em acervos/RPO/backups autorizados; evitar ajustes ad hoc para atingir contagens.
3. **Critério de sucesso:** demonstrar paridade **informacional** campo a campo e por chave/grão no período de referência do vídeo; identificar divergências, casos sem evidência e limites da reconstrução. Paridade visual não é objetivo.
4. **Fallback autorizado de produto:** caso não seja possível recuperar/comprovar todos os cálculos, oferecer apenas informações operacionalmente comprovadas como `OPERATIONAL_VIEW`, `official_parity=PENDING`, com fonte, limitações e dados não disponíveis explicitados ao usuário (nunca converter ausência/erro em zero).
5. **DR2 MOD:** não escolher SG1 ou SG2 por inferência. Verificar no vídeo a seleção e terminologia da MOD, e em SQL/ADVPL/artefato o vínculo SG1/SGG e SG2/SHY/roteiro; confirmar a semântica de COMP e a diferença entre 521 PAs distintos e 1.767 contagens históricas.
6. **DR3 arquitetura existente:** inventariar e **reutilizar** contratos, padrões de comunicação S2S e credenciais técnicas existentes entre api-delpi e controllership-finance-api. O BFF governa acesso do usuário por effective permissions via Core, resource_scope e regra de negócio; a api-delpi mantém seu controle técnico S2S conforme padrão vigente. MFE e CLARA usam a BFF; não criar autenticação ou integrações exclusivas e não expor token ao browser. Se for necessária uma nova rota de domínio na api-delpi, ela deve usar o padrão existente e não pressupõe nova arquitetura.
7. **Sequenciamento:** documentar a engenharia reversa, a matriz de correspondência e o design/contrato antes de implementar. Reuso/pequena alteração compatível preferidos quando comprovados; nova operação específica se reuso prejudicar semântica. Alteração material de algoritmo, contrato, owner, integração, segurança ou breaking change requer gate e aprovação explícitos antes do código. Implementação incremental só após esse gate; deploy produtivo somente com autorização separada.
8. **Resíduos mantidos:** SP não localizada no escopo conhecido, IAM persona negativa `INCONCLUSIVE` com owner IAM, paridade humana `PENDING`; não declarar PASS por smoke não executado.

## Entregáveis exigidos no Gate 039

- Linha temporal de extração do vídeo: competência, filiais, opções de seleção, valor da opção MOD, passos, arquivo gerado, com timestamps e nível de confiança.
- Inventário DLP204/SP/RPO, endpoints atuais de estrutura e onde-usado, suas queries, consumidores e padrões de AuthN/AuthZ S2S+BFF.
- Matriz campo a campo `video ↔ ADVPL ↔ SQL/TOTVS ↔ XLSB ↔ api-delpi` com `PROVEN/TO_INVENTORY`, diferenças de grão, nulidade, origem de MOD, COMP, horas e custos.
- Comparação determinística por chave/filial/competência (linhas, chaves faltantes/excedentes, valores com tolerância justificada), sem falsificar cobertura.
- Alternativas reuso compatível vs rota específica na api-delpi e impacto nos consumidores; contrato e plano de testes; limites explícitos do fallback.
- Relatório `DECISION_REQUIRED` apenas para decisões materiais não cobertas e autorização pré-implementação correspondente.

Este documento registra **a direção do PO**, não declara reconstrução/paridade concluída e não autoriza código, deploy nem alteração material automática.
