# 159 — Ocorrência operacional Filial 01 em outubro/2026 e continuidade da revisão com setembro/2026

**Data:** 09/11/2026 · **Processo:** PROC-0072 · **Produto:** Portal Controladoria & Finanças · **Estado:** EVIDÊNCIA OPERACIONAL RECEBIDA / REVALIDAÇÃO PENDING / AUDITORIA CONTINUA. **Sem alteração de ERP, API, CLARA ou Portal.**

## 1. Resposta recebida por e-mail — origem e alcance

- **Assunto:** `RES: Verificação do fechamento de estoque e custos — Filial 01 (Outubro/2026)`.
- **Recebimento:** 09/11/2026, 13h21 (horário de Brasília), na conversa de e-mail disparada para Joici e Michael. A resposta recebida está assinada por **Marjory Alves**; não atribuir citação literal à Joici sem verificar remetente/assinatura. **Fonte privada:** Outlook, thread de mesmo assunto; não versionar e-mail nem dados pessoais.
- **Conteúdo pertinente, transcrição curta da resposta:** “Na matriz o estoque teve que ser reaberto para correção de NF.”
- **Classificação:** `PROVEN_EMAIL_STATEMENT` de que houve reabertura para correção de nota fiscal. A resposta **não** confirma número da NF, data de correção, conclusão do reprocessamento nem existência atual de posição histórica de 31/10/2026.
- **Impacto na investigação:** evidência compatível com a falta de posição de outubro da Matriz; **não prova sozinho** causa técnica exclusiva nem que a correção esteja concluída. Não converter hipótese em resolução nem `PASS`.

## 2. Confronto com dados anteriormente observados

| Checagem anterior | Filial 01 — Matriz | Filial 02 | Interpretação |
|---|---|---|---|
| `SB9010`, posição 30/09/2026 | 4.812 linhas | 3.117 linhas | `PROVEN` na consulta anterior |
| `SB9010`, posição 31/10/2026 | sem linhas encontradas | 3.366 linhas | ausência não equivale a saldo 0 |
| `SX6010/MV_ULMES` | `20260930` | `20261031` | Matriz sem avanço de fechamento materializado |
| R03/P7, R05, R08 outubro | `SOURCE_MISSING`/parcial | dados operacionais disponíveis | consulta operacional ≠ paridade oficial |

**Status outubro/Filial 01:** `PENDING` aguardando confirmação de correção da NF, reexecução/encerramento do fechamento e avanço comprovado da data-base. Não modificar SQL nem preencher dados artificiais. **Revalidação somente após novo aviso do owner**, por leitura novamente de `SB9010`, `MV_ULMES` e endpoints governados R03/R05/R08, verificando Filial 01, Filial 02 e consolidado e distinguindo `SOURCE_MISSING`, dados parciais e paridade.

## 3. Plano de retomada do fechamento outubro

1. Solicitar confirmação operacional sobre correção da NF e fechamento posterior (Joici / Michael / área responsável).
2. No retorno, consultar `MV_ULMES` por filial e presença/histórico `SB9` em 31/10/2026; comparar ao estado-base acima, sem writes.
3. Consultar a CLARA/Portal para R03/P7, R05 e R08 por filial e consolidado; preservar as flags de paridade `PENDING` e conciliação `IDENTITY_ONLY` quando aplicáveis.
4. Confrontar resultados com emissão oficial Protheus na **mesma competência/data-base/filtros/universo**. Sem relatório oficial, declarar `INCONCLUSIVE`.
5. Registrar resultados, owner, evidência, data, testes e SHAs; corrigir somente divergência comprovada do Portal após gate de implementação.

## 4. Decisão operacional: continuar auditoria com setembro/2026

**PO decision 09/11/2026:** enquanto outubro/Filial 01 está em reprocessamento, **prosseguir normalmente na revisão do Portal usando competência 09/2026**, que possui posição histórica de ambas as filiais e arquivos históricos nas fontes privadas deste projeto. Outubro não deve bloquear revisão independente de setembro.

**Corpus de comparação disponível no projeto (não publicar bytes/linhas sensíveis no Git):**
- Estoques: `Estoque.pdf`, `Resumo Estoque.pdf` (P7/MATR460, validar identificação por filial em cada arquivo), `Entradas e saidas.pdf` (MATR320/R05), `Material em processo.xlsb` (MATR989/R08), `Invent.xlsb` (R07).
- Custos e finanças: `cpv 09 26 matriz.xlsb`, `CC matriz.xlsb`, `Fat x MOD.xlsb`, `Analise.xlsx`, `Pagos por dt.pdf`, `Pagos por nat.pdf`, `Recebidos.pdf`, `A pagar.xlsb`, `A Receber.xlsb` e outros documentos da pasta. Cada arquivo deve ser classificado quanto a relatório, filial, período e universo **antes** de comparar.
- Referências do repositório: [doc 83](./83-ciclo2-crosswalk-evidencias-r01-r15.md) (matriz de arquivos e seus metadados), [doc 84](./84-ciclo2-paridade-relatorios-r01-r02-e-protocolo-testes.md) quando disponível, [doc 157](./157-design-gate-conciliacao-estoque-por-unidade-relatorios-divergencias-2026-11-09.md) e [doc 150](./150-plano-unico-correcao-integral-portal-ux-funcional-2026-11-02.md).

**Protocolo de revisão de setembro — para cada página/relatório:**
1. Identificar arquivo-modelo, código da rotina TOTVS e produtor real; verificar filial 01/02, competência, data-base e filtros, granulação, moeda e layout.
2. Coletar resultado live da CLARA/BFF e evidência da UI com sessão autorizada; comparar **linha a linha quando cabível** e totais com os documentos privados, evitando somas de universos diferentes.
3. Marcar cada dimensão `PROVEN / TO_INVENTORY` e resultado `PASS / FAIL / PENDING / INCONCLUSIVE / TEST_NOT_RUN`; uma captura ou HTTP 200 não comprova paridade.
4. Abrir novo achado no plano único doc 150 para qualquer diferença real: valor, universo, filtro, UX, indisponibilidade, exportação ou autorização; registrar evidência, owner, RQ/AC e trilha de correção, **sem executar correções antes do encerramento da auditoria integral**.
5. Evitar reclassificar falta de outubro como defeito da página de setembro.

## 5. Pendências e limites

- **Owner de negócio:** Controladoria/operador do Protheus precisa confirmar conclusão da correção e novo fechamento de outubro.
- **Evidência outubro:** `PENDING`, sem reconsulta nesta anotação.
- **Revisão setembro:** `PLANNED / IN_PROGRESS` por decisão de escopo; disponibilidade de anexos e metadados não equivale a valores já comparados.
- **Produção:** nenhuma mutation de ERP, nenhum novo item/checklist, nenhum deploy nesta entrega documental.

**Próximo passo:** abrir o Portal em setembro/2026, selecionar cada relatório e confrontar com a fonte correspondente por filial, começando por P7/R03, R05 e R08; registrar resultados progressivamente no doc 150. Outubro retoma após resposta e revalidação técnica.
