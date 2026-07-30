# Unidades de medida (Protheus Delpi)

Parte da [biblioteca de padrões TOTVS](./README.md).

**Detalhe canônico (playbook completo):** [playbook-conversao-unidades-protheus.md](../../roadmaps/playbook-conversao-unidades-protheus.md)  
Resumo operacional abaixo — **não** duplicar o playbook nesta seção.

---

## Resumo produtivo

| Convenção | Significado |
|-----------|-------------|
| `B1_UM = MI` (PA) | Na Delpi, **1 MI = 1000 peças** no contexto produtivo das rotas api-delpi que aplicam a conversão |
| Contextos distintos | Cadastro, BOM/estrutura, fiscal e apontamento podem divergir — ver playbook §§ 1–3 |
| Rotas consumidoras | Listadas no playbook (§ 3.2) — estrutura, estoque, simulador de impacto, etc. |

---

## O que fazer

1. Antes de expor quantidade/custo por UM, ler o playbook e o serviço de conversão já usado no módulo.
2. Documentar na rota se a quantidade está em UM cadastral ou já convertida para peça.
3. Preferir serviço de domínio existente a `if um == 'MI'` espalhado.

### O que NÃO fazer

| Anti-padrão | Por quê |
|-------------|---------|
| Assumir que toda UM é peça | MI e outras unidades quebram ranking/custo |
| Reimplementar fator 1000 só no MFE | Fonte de verdade na API |

---

## Referências

- [02-produtos.md](../02-produtos.md) (ponte ao playbook)
- Playbook: [playbook-conversao-unidades-protheus.md](../../roadmaps/playbook-conversao-unidades-protheus.md)
