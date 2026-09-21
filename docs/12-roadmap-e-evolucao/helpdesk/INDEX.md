# Índice — Meus Chamados de TI

Entrada: [`README.md`](./README.md).

## Authorities para implementar

1. Instruções oficiais e regras `.cursor` da plataforma — autoridade superior a esta pasta.
2. [`06-plano-execucao.md`](./06-plano-execucao.md) — ordem `E1…E5` (primeira entrega, não reabrir).
2b. [`16-plano-paridade.md`](./16-plano-paridade.md) — ordem `E6…E13` (paridade do solicitante, **concluída**).
2c. [`evidence/e14-mentions.md`](./evidence/e14-mentions.md) — menção leitura (M-07); M-23 park.
3. [`02-arquitetura.md`](./02-arquitetura.md) — ownership e estado `PROVEN`.
4. [`03-contrato.md`](./03-contrato.md) — contrato do BFF e mapa para a HLAPI.
5. [`04-seguranca.md`](./04-seguranca.md) — OAuth, sessão e segredos.
6. [`07-requisitos.md`](./07-requisitos.md) — `HD-001…HD-027`.
7. [`08-definition-of-done.md`](./08-definition-of-done.md) e [`09-testes-e-aceite.md`](./09-testes-e-aceite.md).
8. [`evidence/execution-ledger.md`](./evidence/execution-ledger.md) — o que está `PROVEN`.

Visão e ondas: [`01-visao-produto.md`](./01-visao-produto.md), [`05-roadmap.md`](./05-roadmap.md).
Telas e componentes: [`WIREFRAMES.md`](./WIREFRAMES.md).
Conversa do chamado: [`10-conversa-do-chamado.md`](./10-conversa-do-chamado.md). A tela publicada está em [`WIREFRAMES.md`](./WIREFRAMES.md).
Lacunas da experiência (inventário; estados sincronizados com o código): [`11-lacunas-da-experiencia.md`](./11-lacunas-da-experiencia.md).
Conteúdo da mensagem (formatação, imagem, HTML): [`12-conteudo-da-mensagem.md`](./12-conteudo-da-mensagem.md).
Listagem de chamados (colunas, filtros, paridade GLPI): [`13-listagem-de-chamados.md`](./13-listagem-de-chamados.md).
Página do chamado e estados (formulário GLPI × detalhe; ciclo ITIL): [`14-pagina-e-estados-do-chamado.md`](./14-pagina-e-estados-do-chamado.md).
Capacidades do GLPI Assistência (Forms, SLA, vínculos, abas; matriz): [`15-capacidades-glpi.md`](./15-capacidades-glpi.md).
Plano de paridade `E6…E13` (concluído): [`16-plano-paridade.md`](./16-plano-paridade.md).

## Roteamento rápido

```text
o que a pessoa vê?          → 01 e WIREFRAMES.md
de quem é o chamado?        → 02
qual URL e qual JSON?       → 03
o corpo da mensagem?        → 12 (HTML, formatação, imagem; E14 menção)
a listagem de chamados?     → 13 (colunas, filtros, builder AND)
a página e os estados?      → 14 (detalhe do solicitante + ciclo ITIL)
o que o GLPI tem além disso? → 15 (matriz Assistência)
onde fica o segredo?        → 04
ondas do produto?           → 05 (H0…H14)
o que implementar agora?    → G-05 entregue; próximo só com decisão nova (M-23, H12, H10 se HLAPI)
qual HD?                    → 07
como fechar a etapa?        → 08 e 09
já está em produção?        → evidence/execution-ledger
```

O ledger em `evidence/` prova runtime. Inventários 12–15 descrevem o alvo **e** o estado vigente (IMPLEMENTADO / CONSOLE / BLOQUEADO). Código da primeira entrega: [`06`](./06-plano-execucao.md). Código da paridade: [`16`](./16-plano-paridade.md) (histórico). Menção: [`e14-mentions.md`](./evidence/e14-mentions.md).
