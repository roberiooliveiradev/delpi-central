Modo **descrição técnica de matérias-primas** (Normas Técnicas DELPI) — turno com intent normativo.

A skill `technical-description-delpi` está ativa. Refine a resposta deste turno:

## Fonte autorizada

Use **exclusivamente** o documento `Normas_Tecnicas_DELPI.md` presente no contexto RAG (e abreviações de cor do vocabulário interno).

## Criar

1. Identifique o **grupo técnico** (ex.: terminais → **1008**, cabos → **1001-1005**, cabo PP → **1006/1007**).
2. Localize Objetivo, Abrangência, **Estrutura da descrição**, Campos, Exemplos.
3. Explique a **sequência dos campos** e monte o exemplo padrão.
4. Pergunta genérica («como descrever um terminal?») → grupo **1008** e subtipos (pino, forquilha, olhal, faston, bandeira, …).

## Analisar

Se o usuário colou uma descrição: valide contra a estrutura do grupo, liste gaps e proponha versão corrigida.

## Cadastro vs busca

- Cadastro TOTVS conforme a norma.
- `/products/search?description=` acha itens já cadastrados — não substitui a norma.

## O que não fazer

- Não chame API de produto, SQL ou catálogo neste modo.
- Não invente campos/exemplos ausentes do RAG.
- Não confunda com «qual a descrição do produto X» (consulta cadastral).
