# G1_HOLDOUT_PROTECTION_PLAN

## Declaração obrigatória

```text
TRUE_UNSEEN_HOLDOUT=NOT_AVAILABLE
```

Motivo: todos os 13 PDFs do Doc 120 e os diagnósticos `90264026` / `90264135` foram usados em medição e/ou ajuste DEC-040–043. Declará-los como holdout “cego” falsificaria generalização.

## Split proposto (sujeito a aprovação do owner)

| Split | Códigos | Uso permitido |
|---|---|---|
| **development** | `90264026`, `90264004`, `90264017`, `90264135` | Diagnóstico, fixtures, overlays G1; **não** medir generalização final |
| **validation_exposed** | Demais 11 do Doc 120 | Regressão / sanidade após mudança; **não** substituem holdout cego |
| **holdout_true_unseen** | *(vazio)* | Bloqueado até novos PDFs |

**Regra de proteção:** após este registro, **proibido** mover PDF de `validation_exposed` → `development` silenciosamente, ou promover `validation_exposed` a holdout inédito. Qualquer reclassificação exige Coordination + Engenharia.

## Solicitação ao owner — novos PDFs (se necessário)

| Item | Proposta |
|---|---|
| Famílias faltantes | Holdout cego: tabela simples inédita; hierarquia com rowspan; multipágina densa; código-em-descrição |
| Quantidade mínima | 3–6 desenhos oficiais **não** presentes no Doc 120 |
| Critério de seleção | Distintos dos layouts já usados em DEC-040–043; SHA e revisão registráveis |
| Acesso | Mesmo canal Domain API / fileserver autorizado; sem cópia em Git |
| Responsável disponibilizar | Engenharia / custódia documental DELPI |
| Critério de aprovação | Owner confirma família, SHA, split=holdout **antes** de qualquer tuning G4 |

## Contaminação

```text
HOLDOUT_CONTAMINATED=false
```

porque o plano **não finge** holdout inédito. Contaminação ocorreria se alguém rotulasse os 11 `validation_exposed` como holdout cego.
