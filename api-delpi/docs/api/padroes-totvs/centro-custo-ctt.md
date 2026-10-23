# Centro de custo (CTT010)

Parte da [biblioteca de padrões TOTVS](./README.md).

---

## Tabela e campos

| Campo | Significado |
|-------|-------------|
| `CTT010` | Cadastro de centros de custo |
| `CTT_CUSTO` | Código do centro de custo (chave lógica usada nos módulos, ex.: `SC1.C1_CC`) |
| `CTT_FILIAL` | Filial do cadastro — **em branco = cadastro global** (válido para todas as filiais) |
| `CTT_DESC01` | Descrição do centro de custo |
| `D_E_L_E_T_` | `'*'` = excluído |

## Filial em branco = cadastro global

Na Delpi, a maior parte dos centros de custo está cadastrada com `CTT_FILIAL` **vazia** (cadastro compartilhado entre filiais). Um join estrito `CTT.CTT_FILIAL = <filial do documento>` **não encontra esses registros** e devolve descrição nula.

Join correto (prefere cadastro da filial quando existir, cai no global):

```sql
OUTER APPLY (
    SELECT TOP 1 RTRIM(CTT.CTT_DESC01) AS descr
    FROM CTT010 CTT WITH (NOLOCK)
    WHERE CTT.CTT_CUSTO = SC1.C1_CC
      AND CTT.D_E_L_E_T_ = ''
      AND (CTT.CTT_FILIAL = SC1.C1_FILIAL OR RTRIM(CTT.CTT_FILIAL) = '')
    ORDER BY CASE WHEN CTT.CTT_FILIAL = SC1.C1_FILIAL THEN 0 ELSE 1 END
) CC
```

`OUTER APPLY`/`TOP 1` garante no máximo uma linha por documento mesmo se houver cadastro global + por-filial.

### O que NÃO fazer

| Anti-padrão | Por quê |
|-------------|---------|
| `JOIN CTT010 ON CTT_FILIAL = C1_FILIAL` apenas | Retorna descrição nula para todos os CCs globais (o mais comum na Delpi) |
| Join aceitando global **e** filial sem `TOP 1`/dedup | Multiplica linhas do documento quando os dois cadastros existem |
| Assumir `C1_CC` vazio como `NULL` | Campo vem `''`/espaços — filtrar com `RTRIM(ISNULL(C1_CC,'')) <> ''` |

---

## Referências

- Uso real: `purchase_request_lines_sql.py` (lista SC + facet `/supplies/purchase-requests/cost-centers`) — PR.FILTERS.S1, 2026-10.
