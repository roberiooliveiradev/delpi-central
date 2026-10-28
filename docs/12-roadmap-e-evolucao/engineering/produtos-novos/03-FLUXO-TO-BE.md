# 03 — Fluxo TO-BE candidato v0.2

**Estado:** PROPOSED; não é o BPMN AS-IS oficial.

```mermaid
flowchart TD
 A["Programação Carga Máquina / OP"] --> B["Selecionar OPs de produtos novos (regra oficial a definir)"]
 B --> C["Fila antecipada: semana, mês, período livre"]
 C --> D["Previsão de acompanhamento"]
 D --> E{"Início efetivo confirmado?"}
 L["Líder abre chamado manual vinculado à OP"] --> E
 E -->|Não| D
 E -->|Sim| F{"Unidade"}
 F -->|Matriz| G["Engenharia executa checklist por operação"]
 F -->|Filial| H["Qualidade executa checklist por operação"]
 G --> I{"Divergência?"}
 H --> I
 I -->|Sim| J["Ocorrência rastreável; Engenharia da matriz corrige"]
 J --> K["Reverificação / liberação conforme autoridade formal"]
 K --> I
 I -->|Não| M{"Etapas aplicáveis concluídas?"}
 M -->|Não| N["Manter pendência / acompanhar retomada"]
 N --> G
 M -->|Sim| O["Engenharia confirma conclusão"]
 O --> P["Owner oficial retira indicativo Produto Novo por revisão controlada"]
 P --> Q["Acompanhamento concluído"]
```

## Distinções obrigatórias
- **Programado** é previsão; solicitação do líder e início efetivo são eventos distintos.
- **Corrigir, liberar, revisar e publicar** exigem autoridade do domínio; não criar bloqueio automático sem contrato/decisão.
- Filial tem checklist equivalente ao da matriz; Engenharia da matriz recebe tanto resultado divergente quanto conforme e efetua correção/encerramento técnico.
- OP pausada, reprogramada, cancelada ou concluída sem verificação não deve apagar histórico ou falsamente encerrar.
- Estado de conclusão depende de todas as operações aplicáveis, evidência e owner autorizado.

## Estados candidatos
PREVISTO, SOLICITADO, INICIADO, EM_ACOMPANHAMENTO, PENDENTE_CORRECAO, PAUSADO, CONCLUIDO, REPROGRAMADO, CANCELADO. Nomes, transições e persistência devem ser inventariados no domínio antes de implementar.
