# Wireframes — Despesas de Viagem (P0)

## Hub (`/apps/travel-expenses`)

```text
+----------------------------------------------------------+
| Despesas de Viagem          [Nova prestação]             |
| KPIs: este mês | rascunhos | total BRL | sem cupom       |
+------------------+---------------------------------------+
| Atalhos          | Recentes (tabela densa)               |
| Minhas           | TE-2026-0003  SP  4 desp  R$ 1.280    |
| Unidade (manage) | TE-2026-0001  ES  2 desp  R$   340    |
+------------------+---------------------------------------+
```

## Workspace (`/reports/{id}`)

```text
+----------------------------------------------------------+
| TE-2026-0003  Rascunho          [Ver pacote] [Salvar]    |
| Destino · Período · Filial · Motivo · CC                 |
+---------------------------+------------------------------+
| Despesas                  | Prontidão do pacote          |
| [+] Nova despesa          | 3/4 cupons · 1 data fora     |
| 12/08  Almoço   R$ 48  [img]                             |
| 13/08  Uber     R$ 32  !sem cupom                        |
+---------------------------+------------------------------+
| Drawer: data, categoria, estabelecimento, valor, nota    |
| [Tirar foto] [Galeria] thumbs → FilePreviewModal         |
+----------------------------------------------------------+
```

## Pacote (`/reports/{id}/package`)

```text
Capa Delpi · viajante · período · totais por categoria
Tabela de linhas · cupom por linha
Rodapé paginado · [Baixar PDF]
(Sem CTA de envio)
```
