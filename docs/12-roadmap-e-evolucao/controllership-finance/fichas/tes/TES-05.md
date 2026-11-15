# TES-05 — Pendências, manutenção e como a CLARA responde sobre TES

Versão da ficha: 1.0 · 14/11/2026.

## Identificação

- Código: **TES-05** — o que ainda não está confirmado sobre TES, como manter o catálogo e como a CLARA deve responder.
- Implementação: **IMPLEMENTED** (conhecimento citável).
- Evidência: itens em aberto são TO_INVENTORY até a Controladoria ou o fiscal confirmar.

## Como a CLARA responde sobre TES

- Identifique a TES pelo **código** e cite a descrição, o CFOP e os atributos que explicam a resposta (estoque, duplicata, crédito, livro, poder de terceiros). A descrição sozinha não identifica: há descrições repetidas.
- Diga a data do cadastro: «pelo cadastro de TES de 09/11/2026». TES criada ou editada depois não está no catálogo.
- Separe TES de CFOP: o CFOP diz a operação ao fisco; a TES diz o que o Protheus faz. Mesmo CFOP pode ter TES com efeitos diferentes.
- 499 e 999 (ajustes de inventário) são tipos de movimento da SD3, não TES.
- Para dizer **em qual relatório** a TES pesa, use a ficha TES-01 e cite a ficha do relatório. Para dizer **o que a TES faz**, use TES-03 ou TES-04.
- TES bloqueada em nota antiga é histórico, não erro.
- Configuração estranha (ficha TES-02, pontos A1–A6) é POSSIBLE_DIVERGENCE a verificar com o fiscal, nunca erro confirmado. Correção de cadastro é feita no Protheus por quem tem acesso.
- Crédito de imposto: quem decide é o livro fiscal (SFT); a TES confirma (ficha AE-10). Nunca afirme crédito indevido só pela TES.
- Se a TES não está no catálogo: diga que ela não consta na extração de 09/11/2026 e que pode ser TES nova; não invente o comportamento.
- A CLARA não lê a SF4 ao vivo. Movimento real (quais notas usaram a TES) vem das leituras dos relatórios e da auditoria (`entry_audit.tes` lista as TES usadas numa análise).

## Perguntas em aberto

| # | Pergunta | Para quem | Situação |
|---|---|---|---|
| P-TES-01 | A lista do R10 tem 12 ou 13 TES? (016 e 159 entram no conjunto que reproduz o relatório, mas não na lista narrada) | Controladoria | TO_INVENTORY (LISTA-13) |
| P-TES-02 | A seleção do R11 é «grupo 9035 ∩ TES 594» como critério oficial, ou avaliação por documento? | Controladoria | TO_INVENTORY (E11b) |
| P-TES-03 | Quais TES de poder de terceiros entram no saldo em poder de terceiros do P7 e no material em processo? | Controladoria / custos | TO_INVENTORY |
| P-TES-04 | Descrição e filial dos tipos de movimento 499 e 999 (SF5) | Responsável pelo estoque | TO_INVENTORY |
| P-TES-05 | Os pontos A1 (consumo com crédito de IPI) e A2 (crédito × livro desencontrados) da ficha TES-02 são intencionais? | Fiscal | TO_INVENTORY |
| P-TES-06 | Frete com «Atualiza estoque = Sim» (040, 042, 158, 180): qual o efeito pretendido no custo? | Fiscal / custos | TO_INVENTORY |
| P-TES-07 | Quais TES tiveram movimento nos últimos 12 meses (para separar TES ativa em uso de TES ativa parada)? | Levantamento em dados | TO_INVENTORY |
| P-TES-08 | As demais TES sem estoque nos CFOPs do CPV (505, 619, 716, 511, 671, 756) saem com custo zero como a 594? | Levantamento em dados | TO_INVENTORY |

## Respondidas

- **TES de frete e TES 036** (P5 da auditoria de entradas, 14/11/2026): o frete é identificado pelo CFOP terminado em 352 e o crédito sai do cadastro da TES. A 036 está **bloqueada** no cadastro de 09/11/2026; CT-e antigo nela fica «Depende da TES» sem o livro fiscal.

## Manutenção do catálogo

- Fonte: `fonte/sf4-2026-11-09.csv` (20 colunas da SF4). Os catálogos TES-03 e TES-04 são gerados por `fonte/gerar_catalogo_tes.py`; TES-00, TES-01, TES-02 e TES-05 são escritas à mão.
- Quando atualizar: TES criada, editada ou bloqueada; regra de relatório que passe a usar TES; resposta a uma pergunta em aberto.
- Como atualizar: extrair a SF4 vigente com as mesmas colunas, salvar como `fonte/sf4-AAAA-MM-DD.csv`, rodar o gerador com `--csv` e `--data-extracao`, revisar o diff, atualizar números das fichas escritas à mão (`--resumo`) e republicar o corpus da CLARA.
- A cópia da SF4 usada pela auditoria de entradas e a deste catálogo devem ser da mesma data.

## Governança

- Owner do conhecimento: Controladoria. Owner técnico: `controllership-finance-api` (corpus da CLARA).
- Resposta a pergunta em aberto entra nesta ficha e, se mudar regra de relatório, na ficha do relatório.
