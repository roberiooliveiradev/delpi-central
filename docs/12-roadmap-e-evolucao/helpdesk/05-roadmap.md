# 05 — Roadmap

> **Primeira entrega (E1…E5):** [`06-plano-execucao.md`](./06-plano-execucao.md) — **não reabrir**.
> **Paridade do solicitante (E6…E12):** [`16-plano-paridade.md`](./16-plano-paridade.md).
> **Inventários:** [`12`](./12-conteudo-da-mensagem.md) · [`13`](./13-listagem-de-chamados.md) · [`14`](./14-pagina-e-estados-do-chamado.md) · [`15`](./15-capacidades-glpi.md).
> **Requisitos:** `HD-001…HD-026` em [`07-requisitos.md`](./07-requisitos.md).
> Este arquivo é a evolução macro. Não marca fase como feita.

```text
H0  Fundação GLPI                          PROVEN
H1  BFF e sessão OAuth                     PROVEN
H2  Leitura da lista                       PROVEN
H3  Abertura e acompanhamento              PLANNED  (código na tela; ledger ao vivo aberto)
H4  Tela nativa no lugar do iframe         PROVEN
H6  Investigação HLAPI (gates)             TARGET   ← começa a paridade
H7  Estados e lista do solicitante         TARGET
H8  Corpo rico da mensagem                 TARGET
H9  Página do chamado                      TARGET
H10 Solução, reabrir, satisfação           TARGET   (ex-H5 do solicitante)
H11 Condicionais (TTR, vínculo, Forms)     TARGET   só se H6 provar
H12 Upload de arquivo novo                 BLOQUEADO até decisão + API
—   Bancada / outro itemtype / HD-011      FORA
```

O antigo **H5** foi fatiado: download de anexo já é H4; o que restava virou H10 (solicitante), H12 (upload) e FORA (bancada).

## O que «implementar tudo» significa

Tudo o que o **solicitante** já tem no GLPI e a Minha DELPI ainda não entrega, **desde que** a HLAPI 2.2 e as regras da plataforma deixem.

Não entra, mesmo neste roadmap:

| Fica fora | Por quê |
|---|---|
| Formulário de três colunas, abas, Kanban, PDF, massa, export, saved search | console — [`15`](./15-capacidades-glpi.md) X-60…X-76, X-82 |
| Mudança, problema, inventário, entidade, delegação, anônimo | FORA / HD-011 |
| PATCH de status, tarefa, privado, excluir Novo | console — [`14`](./14-pagina-e-estados-do-chamado.md) |
| API legada / `password` grant | proibido |
| Filtrar 128 128 no browser | invariante |

## H0…H4 — Primeira entrega

Sem mudança de escopo. Fechar **H3 no ledger** (abrir + acompanhar ao vivo) é pré-requisito de E5.S2 e **não bloqueia** H6: a tela já posta. Ordem: registrar H3 no ledger na primeira janela de homologação, em paralelo com H6 se preciso.

Detalhe das etapas: [`06`](./06-plano-execucao.md).

## H6 — Investigação (obrigatória, sem UI nova)

Sem isto, H8 imagem, H11 e parte de H7/H9 são `NOT_READY`.

Captura **só de chaves e formatos**, sem corpo pessoal em log e sem senha em commit. Chamados de referência: 6288, 1114, 1101.

| Gate | Decide | Bloqueia se falhar |
|---|---|---|
| 12-H1…H4 | URL da `<img>`, data-URI, Document vs HTML, A-07 | H8 imagem inline / anexo por bolha |
| 13-H1 | `content=like` | busca no texto (G-21) |
| 13-H2 | `date_solve` / `date_close` no GET da lista | colunas `solved_at` / `closed_at` |
| 14-H1 | follow-up em status 5/6 → 403? | esconder Responder |
| 15-HX1…HX4 | Form API, observer no POST, TTR/SLA, linked tickets | H11 inteiro |

Saída: atualizar 12–15 (HIPOTESE → PROVEN ou FORA) **antes** da etapa de código dependente.

## H7 — Estados e lista

Pronto em grande parte sem H6. Campos condicionais só depois do gate.

| Entrega | Fonte | HD |
|---|---|---|
| `status_id` + badge/filtro por id | [`14`](./14-pagina-e-estados-do-chamado.md) S-01…S-07 | HD-019 |
| Grupos `pending` e `approval`; `open` ainda inclui 10 | 14 + 13 G-23 | HD-019 |
| Data-hora absoluta; `created_from`/`created_to`; `page_size` 10/20/50 | [`13`](./13-listagem-de-chamados.md) G-02, G-25, G-31 | HD-020 |
| `solved_at` / `closed_at` e busca no `content` | 13 G-03, G-21 **se** H6 | HD-020 |
| Ajuda da lista | HD-016 estendido | HD-016 |

## H8 — Corpo da mensagem

Depende de H6 para imagem. Leitura HTML e escrita rica **não** dependem da imagem.

| Entrega | Fonte | HD |
|---|---|---|
| Allowlist no BFF + `description_html` / `content_html` | [`12`](./12-conteudo-da-mensagem.md) M-01…M-06 | HD-021 |
| Modo HTML no `MessageThread` do kit | 12 M-30 | HD-021 |
| `RichTextEditor` em abrir e responder; POST HTML | 12 M-20…M-22, M-28 | HD-022 |
| Rewrite de `document.send.php` + modal | 12 M-08 **se** 12-H1/H2 | HD-021 |
| Menção por `data-user-id`; `@` só com catálogo | 12 M-07, M-23 | HD-022 |
| Sem colar imagem / upload | A-08 | HD-026 |

## H9 — Página do chamado

| Entrega | Fonte | HD |
|---|---|---|
| Datas absolutas no cartão | 14 P-04 | HD-023 |
| `can_followup` esconde Responder | 14 P-06 **se** 14-H1 | HD-023 |
| Observador só leitura | 14 P-05 **se** team.observer | HD-023 |
| Sem três colunas / PATCH | invariante | — |

## H10 — Fechar o ciclo (solicitante)

Ex-H5 que **é** do colaborador, não da bancada.

| Entrega | Fonte | HD |
|---|---|---|
| Ver solução e aprovar/recusar | 14 P-07, 15 X-46 | HD-024 |
| Reabrir se a matriz simplificada deixar | 14 P-08 | HD-024 |
| Pesquisa de satisfação | 15 X-51 | HD-024 |

Cada item exige operação HLAPI (Solution / Validation / Satisfaction). Se H6 não achar a operação, a linha volta a CONSOLE e não se inventa tela.

## H11 — Condicionais

Só depois de H6. Uma linha morta **some do plano**, não vira tela vazia.

| Entrega | Gate | HD |
|---|---|---|
| TTR visível | H-X3 | HD-025 |
| Vínculos do próprio chamado (id + tipo) | H-X4 | HD-025 |
| Observador na abertura | H-X2 | HD-025 |
| Entrar num Form/catálogo já existente no GLPI | H-X1 | HD-025 |

Sem reimplementar Formcreator. Sem criar vínculo, SLA ou item de inventário no MFE.

## H12 — Upload

BLOQUEADO. Desbloqueia só com decisão explícita de (a) ligar API legada — hoje proibida — ou (b) HLAPI passar a aceitar multipart. Até lá: N-01, M-24, M-25, A-08.

## Dependências

```text
H0 → H1 → H2 → H3/H4
                ↓
               H6 ─────┬→ H8 (imagem) → H9
                       ├→ H7 (solved_at / q no content)
                       ├→ H10 (se houver operation)
                       └→ H11 (se houver campo)
H7 (status_id, datas absolutas, page_size) não espera H6
H12 isolado
```

## Protocolo

Cada subetapa de [`16`](./16-plano-paridade.md): revalidar → implementar o menor escopo correto → teste positive/irmão/negativo → ajuda se user-facing → commit helpdesk → push. Se H6 invalidar premissa: STOP-THE-LINE no subgrafo, corrigir 12–16, não forçar a tela.

## Fora como autorização automática

Bancada (X-61…X-76), Change/Problem, entidade, delegação, coletor, recorrente, anônimo, lixeira, Kanban. Continuam no host do GLPI com `helpdesk.console`.
