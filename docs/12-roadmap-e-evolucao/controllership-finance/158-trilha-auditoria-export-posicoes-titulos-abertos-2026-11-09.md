# 158 — Trilha de auditoria e correção futura: posições de títulos em aberto (FINR150 / FINR130)

**Data:** 2026-11-09 · **Processo:** PROC-0072 · **Produto:** Portal Controladoria & Finanças · **Estado:** DOCUMENTATION_ONLY / DISCOVERY / TO_INVENTORY · **Gate de runtime:** NÃO AUTORIZADO.
**Registro central:** [doc 150](./150-plano-unico-correcao-integral-portal-ux-funcional-2026-11-02.md). Este documento é a trilha detalhada do achado e não modifica contratos de produção.

## 1. Evidência e lacuna observada

- Na reunião **“Fechamento Mensal — Apresentação de soluções”**, 03/11/2026, perto do minuto 50–52, a Joici descreveu o conjunto de documentos enviados à Contabilidade externa, incluindo **títulos a pagar e a receber em aberto** como entregas obrigatórias. Horários/palavras exigem confronto com a transcrição original para citação literal: o documento não representa transcrição autenticada.
- A versão **V2 DRAFT** do template `monthly-closing-checklist` foi atualizada via CLARA em 09/11/2026: revisão **9**, 16 itens; `FIN-PAGAR-ABERTO` / `FIN-RECEBER-ABERTO` cadastrados, `recipient_area=CONTABIL`, `applicability=REQUIRED`, `branch_scope=BOTH`; **V1 continua publicada; V2 NÃO PUBLICADA**. Inclusão documental no checklist ≠ geração/exportação funcional.
- Referências privadas de formato real (não copiar dados sensíveis para Git): `A pagar.xlsb`, `A Receber.xlsb`, anexadas ao projeto. Doc 69 registra posição de pagar com 15 colunas; doc 83 registra receber com 17 colunas e arquivos de 30/09/2026. O usuário exige que exportação futura **reproduza o padrão funcional, estrutura, semântica e formatação dos modelos reais**, não CSV genérico com colunas aproximadas.
- A página existente `/closing/monthly-closing/{period}/reports/financial-settlements` possui **“Baixas a pagar”** e **“Baixas a receber”**; fontes `FinancialSettlementsPage.tsx`, `financialSettlementsApi.ts`, BFF `GET /closing/financial-settlements` e `/summary`, eventos de liquidação. **Baixa financeira não é posição de título em aberto**. Agrupamentos / “Ver registros” / PDF placeholder não provam exportação dos dois documentos.
- O catálogo de capacidades atuais da CLARA inclui `report.settlements` e `report.settlements_summary`; não foi identificada capacidade específica de consulta/exportação oficial FINR150/FINR130. **Search miss não prova ausência universal**: inventariar todos os consumidores/produtores/rotas antes de firmar gap físico.
- Não está comprovada, no código consultado, funcionalidade da página para gerar/baixar exportação oficial de **títulos em aberto** de ambos os lados. **Achado CF-UX-052: lacuna de produto / TO_INVENTORY quanto ao produtor; sem alegar defeito de execução de rota existente.**

## 2. Inventário inicial por rotina (não equivale a paridade)

| Tema | Pagar | Receber | Evidência / estado |
|---|---|---|---|
| Artefato de referência | `A pagar.xlsb` | `A Receber.xlsb` | `PROVEN_DOCUMENT` — docs 69, 83; bytes privados |
| Identificador funcional | `FINR150` | `FINR130` | `DOCUMENTED` em `Contabilidade liberações.xlsx` / doc 60; **binding executável→arquivo `TO_INVENTORY`** |
| Tipo de resultado | posição de obrigações em aberto | posição de direitos em aberto | `PROVEN_DOCUMENT` |
| Fonte candidata | `SE2` e correlatas | `SE1` e correlatas | `TO_INVENTORY` para seleção e cálculos; não usar SQL de baixas como substituto |
| Emissão | recorte da data-base, histórico, filiais, exportação XLSB | idem | parâmetros exatos e evidência por versão `TO_INVENTORY` |
| Paridade colunas/linhas/totais | `TEST_NOT_RUN` | `TEST_NOT_RUN` | comparação deve ser contra **nova emissão oficial de MESMA data-base e mesmas opções** |

**Cuidado com código de mesmo nome:** doc 80 §17 registra `finr130_dlp.prx`/`FINR130D.PRX` como relação SE1, enquanto `finr150_dlp.prx` foi identificado como customização de cheques, não automaticamente o arquivo `A pagar.xlsb`. Validar programa, release, menu, versão, parâmetros, fontes e eventual customização **antes** de eleger produtor canônico. FINR190 e os produtores das baixas não substituem FINR150/130.

## 3. Trilha coordenada de levantamento → contrato → implementação futura

| Gate | ID | Passo / responsável a confirmar | Evidência exigida | Estado |
|---|---|---|---|---|
| DISCOVERY | CF-UX-052-A | Inventariar chamadas da página, BFF, api-delpi, integração TOTVS e ferramentas CLARA que possam produzir posição em aberto. Owner TI/ERP + arquitetura Portal. | Código/contratos no HEAD, mapa producer-consumer, negativa fundamentada ou reutilização comprovada | `TO_INVENTORY` |
| ERP | CF-UX-052-B | Com Joici e TI/ERP, capturar telas e parâmetros efetivos de **FINR150 e FINR130**: menu/versão, data-base civil, filiais/seleção consolidada, intervalo histórico, em aberto vencido/a vencer, ordenação, colunas, idioma/formato, quebra de páginas/linhas em branco. | Emissão controlada, registros de parâmetros, exemplos sanitizados | `PENDING` |
| DATA | CF-UX-052-C | Inventariar registros e regras do Protheus: SE2/SE1, situação aberta, vencimento original/real, saldo parcial, compensação, abatimentos, juros/multas, estorno, cancelamento, provisórios, corte retrospectivo, títulos reabertos e moeda. | Dicionário, código produtor, SQL readonly autorizado, owner de regra; zero não inferido de ausência | `TO_INVENTORY` |
| CONTRACT | CF-UX-052-D | Separar **novo contrato de posições em aberto** de `financial-settlements`; definir granularidade/chaves/filtros, resource scope, freshness, erros, autorização Core fail-closed e proveniência; decidir ownership e possibilidade de reuso de API existente. | RQ/AC versionados, ADR/contrato aprovados, `DECISION_REQUIRED` para integração/persistência/route material | `PENDING` |
| FORMAT | CF-UX-052-E | Homologar formato de **cada Excel** contra `A pagar.xlsb` e `A Receber.xlsb`: planilhas, cabeçalhos, ordem/nome dos campos, datas, percentuais/valores monetários, nulos, totais, prefixo, parcelas, nomes, natureza, filtros, abrangência e metadados da competência. CSV/PDF alternativos só mediante decisão. | Golden files privados, comparação de esquema e valores linha a linha, diferenças documentadas; sem dados reais no Git | `PENDING` |
| UX | CF-UX-052-F | Revisar a experiência dentro de Relatórios e divergências e localização dos downloads, rótulos que distingam **baixas** × **em aberto**, feedback de indisponibilidade, permissão e documentação Ajuda. Padrão `@delpi/plugin-ui` first, desktop/mobile/teclado. | Wireframe aprovado, mapa componentes, estados de erro, AC de exportação por lado | `PENDING` |
| DELIVERY | CF-UX-052-G | **Somente após gate transversal explícito** e revisão integral do Portal: implementação incremental e testes por página; não chamar `api-delpi` do browser. | PR/diff mínimo, testes + smoke autenticado, comparação de export oficial, revisão e rollback | `BLOCKED — NO_RUNTIME` |
| VERIFY | CF-UX-052-H | Com Joici/Contabilidade, homologar resultados, acesso e inclusão no fluxo P2/P5; publicar checklist V2 apenas via workflow próprio aprovado. | Assinatura de owner, outcomes verificáveis, relatório de residuais, commit/SHA | `PENDING` |

## 4. RQ / AC candidatos (a validar com a área)

- **RQ-CF-OPEN-001 (TARGET):** pessoa autorizada consulta a posição completa de títulos **a pagar em aberto**, referida ao corte escolhido e ao escopo autorizado, sem misturar eventos de baixa.
- **RQ-CF-OPEN-002 (TARGET):** idem **a receber em aberto**.
- **RQ-CF-OPEN-003 (TARGET):** cada posição admite **exportação de Excel homologado no padrão dos anexos**, com data-base, filtros e trilha de proveniência consistentes. O formato exato (`.xlsb` nativo versus alternativa equivalente) é **DECISION_REQUIRED** se a plataforma não reproduzir o binário oficialmente; não converter silenciosamente.
- **AC-CF-OPEN-001 (PENDING):** controle diferencia posições em aberto e baixas; ambos os lados acessíveis independentemente, com consulta e exportação somente no contexto autorizado.
- **AC-CF-OPEN-002 (PENDING):** export usa o mesmo universo/filtros da consulta; nada é exportado sem autorização backend; erro/ausência nunca vira planilha de zeros.
- **AC-CF-OPEN-003 (PENDING):** confronto linha a linha e totalização com relatórios oficiais FINR150/130 da mesma data-base; divergências explicitadas, nunca `PASS` por HTTP 200 ou pela mera geração de arquivo.
- **AC-CF-OPEN-004 (PENDING):** documento entregue à Contabilidade conforme `recipient_area=CONTABIL`, escopo e ciclo P2/P5; anexar ≠ validar ≠ enviar.

## 5. Decisões e limites

**DECISION_REQUIRED antes de runtime:** (i) export gerado pelo próprio serviço com regra homologada versus arquivo nativo do Protheus por integração suportada versus upload manual; (ii) nível de fidelidade `.xlsb` / arquivo homologado, layout, metadados e autoria; (iii) contrato/owner de leitura se não houver capacidade central reusável. **Recomendação:** inventorizar primeiro produtores e integrações já existentes e definir formato homologado com Joici, evitando implementação concorrente ao TOTVS.

**Sem mudança agora:** nenhuma alteração em frontend, BFF, api-delpi, SQL, permissões, template publicado, publicação da V2 ou rotina Protheus. Esta trilha é para o ciclo de correções **após revisar o Portal inteiro**. Preservar informações financeiras individuais exclusivamente em evidências privadas autorizadas.

## 6. Referências

- Docs [60](./60-ciclo1-rotinas-contabeis-fiscais-totvs.md), [69](./69-ciclo1-contas-a-pagar-posicao-titulos.md), [80](./80-ciclo2-registro-vivo-investigacao-devin.md), [83](./83-ciclo2-crosswalk-evidencias-r01-r15.md), [117](./117-analysis-001-inventario-processo-real-joyce.md), [118](./118-base-canonica-processo-fechamento-mensal-proc0072.md).
- `plugins/controllership-finance/src/features/closing/FinancialSettlementsPage.tsx` e `src/api/financialSettlementsApi.ts`; `plugins/controllership-finance/README.md`.
- Artefatos privados do projeto: `A pagar.xlsb`, `A Receber.xlsb`, `Contabilidade liberações.xlsx` (NÃO COMMITAR).
