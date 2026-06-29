# Catálogo de critérios — Auditoria 5S (filial 01)

> **Arquivo:** `docs/12-roadmap-e-evolucao/auditoria-5s/CRITERIOS-CATALOGO-FILIAL-01.md`  
> **Versão do catálogo:** `2`  
> **Filial:** `01` (SC)  
> **Uso:** migration `V028__seed_audit_5s_catalog_v2_filial_01.sql`; filial 02 permanece em `catalog_version=1`

---

## Resumo

| Senso | Ordem | Código prefixo | Qtd critérios |
|-------|-------|----------------|---------------|
| Utilização | 1 | `U` | 3 |
| Ordenação | 2 | `O` | 3 |
| Limpeza | 3 | `L` | 3 |
| Padronização | 4 | `P` | 3 |
| Autodisciplina | 5 | `D` | 3 |
| **Total** | | | **15** |

**Nota por critério:** 1 (Ruim), 3 (Médio), 5 (Bom) ou NA (não se aplica).

Mapeamento operacional: `quality.audit_5s_branch_catalog` — filial `01` → versão `2`; filial `02` → versão `1`.

---

## 1. Senso — Utilização

| Código | Ordem | Descrição |
|--------|-------|-----------|
| `U01` | 1 | Existem materiais, ferramentas ou equipamentos sem uso no local? |
| `U02` | 2 | Os materiais e ferramentas estão em boas condições de uso? |
| `U03` | 3 | Há falta de ferramentas, equipamentos ou recursos necessários para o trabalho? |

---

## 2. Senso — Ordenação

| Código | Ordem | Descrição |
|--------|-------|-----------|
| `O01` | 1 | Os materiais, armários, bancadas, mesas e ferramentas estão organizados e de fácil acesso? |
| `O02` | 2 | Os locais dos materiais e equipamentos estão identificados e sinalizados corretamente? |
| `O03` | 3 | Os itens mais utilizados estão em locais de fácil acesso? |

---

## 3. Senso — Limpeza

| Código | Ordem | Descrição |
|--------|-------|-----------|
| `L01` | 1 | Piso, paredes e estruturas estão limpos e conservados? |
| `L02` | 2 | Máquinas, ferramentas e bancadas estão limpas e organizadas? |
| `L03` | 3 | Corredores e áreas comuns estão limpos e organizados? |

---

## 4. Senso — Padronização

| Código | Ordem | Descrição |
|--------|-------|-----------|
| `P01` | 1 | As identificações, etiquetas, demarcações e centros de trabalho estão padronizadas e atualizadas? |
| `P02` | 2 | As proteções e identificações de segurança estão visíveis e em boas condições? |
| `P03` | 3 | Os resíduos estão identificados e separados corretamente? (terminais, fios, palhas, borra de estanho, papel, plástico) |

---

## 5. Senso — Autodisciplina

| Código | Ordem | Descrição |
|--------|-------|-----------|
| `D01` | 1 | As pendências do 5S estão sendo tratadas dentro do prazo? |
| `D02` | 2 | A equipe conhece e pratica as regras do 5S? |
| `D03` | 3 | O setor mantém o 5S conforme os padrões definidos pela Delpi? |

---

## Referências

- Catálogo filial 02 / legado: [CRITERIOS-CATALOGO.md](./CRITERIOS-CATALOGO.md) (v1, 48 critérios)
- Migration: `api-delpi/migrations/plugins/quality/V028__seed_audit_5s_catalog_v2_filial_01.sql`
