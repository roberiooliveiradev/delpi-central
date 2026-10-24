# Vocabulário normativo de produtos DELPI — interpretação READ (DAVI)

**Escopo:** interpretação de termos naturais para consulta de catálogo (`search_products` e rotas correlatas). Este documento **não** autoriza escrita, não redefine descrições cadastradas e não é permissão.

## Proveniência e governança

| Campo | Valor |
|---|---|
| Fonte primária | `minha-delpi-ai-api/docs/knowledge/sources/gpt-instructions/Normas_Tecnicas_DELPI.md` (blob `aa8ec68879ae73ce83155f291e697e2f88416ebd`) |
| Fonte auxiliar (50xx) | `minha-delpi-ai-api/docs/knowledge/domains/agents/minha-delpi-chat/engenharia-codigos-intermediarios-delpi.md` |
| Origem normativa | ENGENHARIA — elaboração Robério Oliveira, revisão José, 05/06/2025 |
| Status normativo | `BUSINESS_OWNER=TO_INVENTORY` — cópia controlada de interpretação; a norma-fonte no repositório do Chat AI permanece a referência documental até ratificação formal do owner |
| Comparação das cópias | Revalidada em `ae2e82a4fbf2f7f1c44a8426d4ddec0d73c43143`: `domains/global/normas-tecnicas-delpi.md` adiciona cabeçalho de proveniência e difere na quebra final; nenhuma divergência normativa identificada. Usar `sources/gpt-instructions` como referência desta cópia. Isso não substitui ratificação do owner. |
| Classificação | document_guidance — orienta interpretação; não é verdade de domínio nem AuthZ |
| Política de atualização | reincorporar ao mudar a fonte; manter apenas extrato de interpretação READ (não regras de criação de descrição) |

## Regra geral de interpretação

Descrições cadastradas seguem **prefixo normativo + tipo** no início. Termos naturais do usuário raramente coincidem com a forma cadastral. Ao pesquisar por descrição:

1. Tente o termo literal informado.
2. Se não retornar o esperado, planeje a variante normativa documentada abaixo.
3. Valide relevância pela **descrição retornada** — `total` de busca parcial não é contagem de correspondências válidas.
4. Nunca invente equivalências fora deste documento; miss não prova ausência no ERP.

## Grupo 1008 — Terminais (prefixo fixo `TERM.`)

Todo terminal cadastrado usa `TERM.` + tipo:

| Tipo normativo | Termos naturais típicos |
|---|---|
| `TERM. PINO` | terminal pino, pino terminal |
| `TERM. FORQUILHA` | terminal forquilha, garfo |
| `TERM. LINGUETA` | terminal lingueta |
| `TERM. FASTON` | terminal faston |
| `TERM. BANDEIRA` | terminal bandeira (saída 90°) |
| `TERM. OLHAL` | terminal olhal |
| `TERM. ANZOL` | terminal anzol |
| `TERM. ILHOS` | terminal ilhós |
| `TERM. TUBULAR` | terminal tubular |
| `TERM. LUVA`, `TERM. EMENDA` | luva, emenda |
| `TERM. BALA` | tipo técnico genérico (ex.: bala) |

Atributos subsequentes seguem a estrutura normativa (bitola MM2, banho ESTANHADO/NIQUELADO, `C/ISOLACAO`/`S/ISOLACAO`, embalagem GRANEL/FITADO/BLISTER, trava, normas ROHS/UL).

## Outros prefixos normativos documentados

| Grupo | Prefixo do item |
|---|---|
| 1001–1005, 1006, 1007 | `CABO`, `CABO PP ...` |
| 1009 | `ISOLADOR`, `INSERTO`, `CONECTOR` |
| 1012 | tubos isolantes/corrugados conforme seção própria |

## Família 50xx — códigos intermediários

Códigos intermediários seguem composição documentada: `50xx` (família) + sequência + tipo/bitola do cabo (`CA`=PVC, `CB`=EPR, `CF`=Silicone, `CT`=Teflon, `CV`=Especial) + cor de 4 letras (`AZUL`, `BRAN`, `VERD`, `AMAR`, `PRET`, `VERM`, …) + comprimento mm + decape `E/D` + terminais/isoladores `E/D`. Interpretar códigos 50xx somente conforme esta estrutura — não inferir campos não documentados.

## Anti-padrões

- `PINO DE AJUSTE` não é `TERM. PINO` — não confundir o substantivo "pino" com o tipo de terminal.
- Não derivar permissão, grupo autorizado ou filtro AuthZ a partir deste documento.
- Não tratar a regra de criação de descrição da norma como contrato de leitura obrigatório para itens legados fora do padrão.
