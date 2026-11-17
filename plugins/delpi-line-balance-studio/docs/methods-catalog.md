# Catálogo único dos seis métodos

**Status:** documentação autorizada; implementação de cada método somente quando houver evidência. O catálogo persiste mesmo com releases parciais.

| ID | Método | Dados indispensáveis | Resultado esperado | Estado atual |
|---|---|---|---|---|
| M1 | Capacidade/takt | Tempo padrão por operação, demanda, disponibilidade | Takt, conteúdo, mínimo teórico, bottleneck, ops acima do takt | PROVEN no motor atual para roteiro oficial |
| M2 | FFD/LCR | Tempos e takt; para LCR, grafo e regras | Distribuição hipotética, carga e folga | FFD PROVEN limitado; LCR TARGET |
| M3 | RPW | DAG de precedências, tempos, ciclo | Ranking de peso posicional, alocação e violações | TARGET |
| M4 | Kilbridge-Wester | Grafo acíclico e tempos | Níveis/colunas de precedência e alocação | TARGET |
| M5 | Yamazumi | Operações, postos hipotéticos, tempo, takt quando existir | Gráfico e organização interativa, comparação | V3 implementada no Portal Engenharia; extração Studio V4 TARGET |
| M6 | Dimensionamento de recursos | Tempos manual/automático, operadores, máquinas, disponibilidade e simultaneidade | Carga por recurso, capacidades e alternativas | TARGET |

## Modelo comum de capability
Cada método deve declarar: `id`, `version`, `status`, `inputRequirements`, `analysisPort`, `outputSchema`, `visualizationModes`, `caveats`, `supportsManualStudy`, `supportsOfficialRouting`. Não permitir status `available` sem contrato/teste real.

## Regras específicas
### M1
`takt=available_minutes/demand`; `ceil(work_content/takt)` é mínimo **teórico**, não postos reais; `bottleneck_candidate` não equivale gargalo observado em chão de fábrica. Setup por lote só quando tamanho é conhecido.

### M2
FFD atual considera somente capacidade total do posto; sem precedência; operação individual >takt compromete viabilidade de posto único. LCR requer regra de elegibilidade de predecessoras e desempates determinísticos.

### M3
Peso = tempo próprio + soma dos tempos de sucessoras **únicas** alcançáveis. Necessário DAG; ciclos, tarefas faltantes ou arestas inventadas bloqueiam análise qualificada.

### M4
Derivar colunas por precedência e preencher postos sob ciclo alvo; desempates e evidência de elegibilidade devem ser auditáveis. Heurística não implica ótimo global.

### M5
Yamazumi **não é solver**. Vista `Tabela` e `Visual` mantêm a mesma atribuição. Categoria de tempo agregada desconhecida não se transforma em manual/automática sem evidência. Detalhes em [yamazumi-spec.md](yamazumi-spec.md).

### M6
Dimensões de operadores e máquinas exigem tempos de intervenção, paralelismo, restrições e disponibilidades. Um CT pode representar múltiplos recursos; não igualar CT a operador, equipamento ou posto.

## Roadmap
**Agora:** M5 V4 reutilizável + origem manual + UX/turnos + M1 existente.  
**Depois:** M2 hardening/LCR, M3, M4, M6 quando dados/contratos do domínio estiverem aprovados.  
A ordem após M5 é referência, não rollout implícito.
