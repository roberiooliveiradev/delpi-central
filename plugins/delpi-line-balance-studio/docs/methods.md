# Catálogo único — seis métodos

**Decisão:** todos pertencem ao Studio; primeiro desenvolvimento funcional = M5 Yamazumi. **Estado atual no Studio: TARGET para todos**, independentemente de implementações em outro produto.

| Método | Objetivo | Insumos exigidos | Saída / limite |
|---|---|---|---|
| M1 Capacidade/takt | Diagnosticar ritmo, carga, gargalo candidato | operações, tempos, demanda, tempo disponível | takt, conteúdo, mínimo teórico; não viabilidade real |
| M2 FFD / Largest Candidate | Distribuir tarefas pela carga | tempos/takt; para LCR precedências válidas | alocação simulada; FFD sem precedência é limitado |
| M3 RPW | Priorizar peso da operação e de sucessoras | DAG, tempos, ciclo | ranking e alocação restrita; não ótimo garantido |
| M4 Kilbridge-Wester | Agrupar por colunas de precedência | DAG e tempos | grupos/estações e folgas; heurística |
| M5 Yamazumi | Visualizar e manipular carga por posto | operações, posto, tempo, takt quando disponível | gráfico interativo; não solver |
| M6 Recursos | Dimensionar operadores/máquinas e paralelismo | tempos manual/automático, recursos, simultaneidade | cenários qualificados; não inferir produtividade |

**Regra:** catálogo pode mostrar Planejado, mas não ação de cálculo não implementada. Não tratar os seis como algoritmos equivalentes. Cada método versiona seu contrato de entradas, saídas, caveats e testes. Os cálculos pertencem ao domínio competente.
