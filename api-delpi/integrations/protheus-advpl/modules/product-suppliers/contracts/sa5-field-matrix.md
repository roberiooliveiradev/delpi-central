# Matriz de campos SA5 — Produto × Fornecedor

Status: `SUPPORTED` (evidência de modelo/contrato) · `REQUIRES_VALIDATION`
(fonte/SX3 sem prova de fluxo REST) · `IDENTITY` (chave primária do modelo).
Não é autorização para expor a tabela física inteira.

| Field | Tipo* | Model | Papel | CREATE | UPDATE | IDENTITY | Status |
|---|---|---|---|---|---|---|---|
| A5_FILIAL | C | relation (`xFilial`) | filial do vínculo | derivado ctx | imutável | ✓ | IDENTITY |
| A5_PRODUTO | C | header+relation | produto (→B1_COD) | requerido | imutável | ✓ | IDENTITY |
| A5_FORNECE | C | grid | cód. fornecedor (→SA2) | requerido | imutável | ✓ | IDENTITY |
| A5_LOJA | C | grid | loja do fornecedor | requerido | imutável | ✓ | IDENTITY |
| A5_FABR | C | grid | fabricante | requerido | imutável | ✓ | IDENTITY |
| A5_FALOJA | C | grid | loja do fabricante | requerido | imutável | ✓ | IDENTITY |
| A5_REFGRD | C | header+relation | referência de grade | condicional `MV_GRADE` | imutável | ✓ | IDENTITY |
| A5_NOMEFOR | C | grid (SX3 obrig.) | nome do fornecedor | requerido SX3 | editável | | REQUIRES_VALIDATION (derivável via trigger?) |
| A5_CODPRF | C | grid (SX3 obrig.) | código do produto no fornecedor | requerido SX3 | editável | | REQUIRES_VALIDATION |
| A5_DESCPRF | C | grid (SX3 obrig.) | descrição do produto p/ fornecedor | requerido SX3 | editável | | REQUIRES_VALIDATION |
| A5_NOMPROD | C | header (view) | nome produto (display) | derivado ERP | derivado | | REQUIRES_VALIDATION |
| A5_DESREF | C | header (view) | descr. ref. grade (display) | derivado ERP | derivado | | REQUIRES_VALIDATION |
| A5_SITU | C | view (excluído do model quando nModulo≠21) | situação QIE | condicional módulo 21 | condicional | | REQUIRES_VALIDATION |
| A5_SKPLOT | C | view/CQ | skip lote (módulo 21) | condicional módulo 21 | condicional | | REQUIRES_VALIDATION |

\* Tipos exatos de SX3 (len/decimals) = reaproveitar inventário SX3 já
publicado no playbook SB1/SX3/SA5 — não duplicado aqui.

Obrigatórios SX3 já comprovados (G0-C): `FILIAL, FORNECE, LOJA, NOMEFOR,
PRODUTO, CODPRF, REFGRD, DESCPRF`. `X3_OBRIGAT` ≠ obrigação universal da
REST — confirmar obrigatoriedade por fluxo no TST01.

## Provas de runtime — TST01 2026-11-19

| Campo | Achado runtime | Evidência |
|---|---|---|
| `A5_REFGRD` | `X3_WHEN` rejeita atribuição **até de `""`** — `SetValue` omitido quando vazio; modelo deriva. Produto sem grade: enviar `""` e deixar omitido | `FWWHEN "Modo edicao nao respeitado"` no console (build diag) |
| `A5_PRODUTO` | header `MdFieldSA5` aceita `SetValue` normalmente | write provado |
| demais identidade/atributos | `SetValue` em grid `MdGridSA5` aceitos | SA5 gravado e read-back íntegro |
