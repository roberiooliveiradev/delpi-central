---
name: "auditoria-entradas-nfe-protheus"
description: Cruzamento mensal das notas de entrada do Protheus (SF1, SD1 e SF4) com os XML de NF-e e CT-e para achar inconsistências de valores, chave de acesso, espécie, série, fornecedor (CNPJ), CFOP, CST, origem, base de cálculo, ICMS, IPI, ST e crédito pela TES, incluindo o crédito de ICMS dos fretes (CT-e). Gera uma planilha de auditoria com resumo, divergências por nota, por item e por CT-e, notas sem par e a configuração das TES. Use SEMPRE que o usuário enviar um ZIP/pasta de XML de NF-e (com ou sem CT-e) junto com relatórios do Protheus (SF1, SD1, SF4 ou arquivos exportados com nomes como scahgx*.xlsx) e pedir cruzamento, conferência, confronto, auditoria, batimento ou "a mesma análise de outro mês", mesmo que não cite os nomes das tabelas. Para só consolidar XML em planilha, sem Protheus, use consolidado-xml-cte-nfe.
---

# Auditoria de entradas: Protheus × XML de NF-e e CT-e

Confronta o que foi escriturado no Protheus com o que está no XML do fornecedor, nota a nota (SF1), item a item (SD1) e CT-e a CT-e, e usa a SF4 para dizer se o ICMS/IPI calculado vira crédito de fato. O resultado é uma planilha no layout do escritório.

## Foco: o que a contabilidade devolve todo mês

O cruzamento existe para pegar antes da contabilidade os erros que ela mais aponta. Pela lista que ela manda, são estes, e cada um tem regra na skill:

| O que a contabilidade aponta | Regra que pega |
|---|---|
| CT-e com alíquota/ICMS a informar (ex.: "Alíquota 7% / ICMS R$ 530,36") | CT-e: ICMS do frete não creditado (frete de venda ou de compra de insumo em TES sem crédito) |
| CT-e "zerar BC, alíquota e ICMS / CST 090" | CT-e: crédito de ICMS em frete sem direito (frete de consumo/ativo ou sem ICMS em TES que credita) |
| CT-e com BC, alíquota, ICMS ou CST 000 diferentes | CT-e: base/alíquota/crédito/CST divergente |
| CT-e com CFOP 1.352 / 2.352 | CT-e: CFOP divergente (1 se o transporte começa na UF da empresa, 2 se começa em outra) |
| NF com CFOP (1.556, 1.407, 2.552...) | CFOP × UF, origem trocada, ST × CFOP sem ST, natureza do CFOP, produto com natureza diferente do usual |
| NF com BC IPI / ICMS diferente | Base de IPI divergente, crédito de ICMS/IPI acima ou abaixo do XML |
| NF com CST 290 (origem) | Origem da mercadoria divergente |
| Chave de acesso errada | Chave divergente do XML (casada pelo número e valor), chave inválida, chave × número/série |
| CNPJ do fornecedor | Fornecedor do lançamento com CNPJ diferente do emitente |
| Espécie (ex.: NF3E) | Espécie do documento incompatível com a chave |
| Série / data de emissão | Série divergente, data de emissão divergente |

Ao apresentar o resultado, comece por esses grupos.

## Regras da empresa: o que NÃO apontar

O usuário já sabe que estes casos não vão para o SPED quando a TES está certa, então a skill não os lista (só conta, no fim do Resumo, em "Não apontado"):

- ICMS ou IPI calculado/destacado em nota lançada em TES de consumo ou de insumo **que não credita**: o livro fica em Outras/Isentas. Também não aponta base ou alíquota diferentes nesses itens, nem IPI diferente do XML quando o total da nota confere.
- **CST 090** nas TES sem crédito (padrão das notas de consumo).
- **CST 060** em combustível (NCM 2710/2711/2207/3826, CFOP x653/x656/x667 ou CST 61 no XML) e em item com ST.

Continua apontando quando a TES está errada: TES que credita onde não devia (inclusive a TES de material de consumo com `Credita IPI? = Sim` e livro IPI Tributado, que leva o IPI para o SPED), CFOP de insumo em TES sem crédito e o CT-e de frete sem direito creditado.

## Entradas

| Arquivo | Obrigatório | Como reconhecer |
|---|---|---|
| XML de NF-e (ZIP, pasta ou XML soltos) | sim | arquivos `NFe-<chave>.xml`; eventos de cancelamento são lidos |
| XML de CT-e | recomendado | `CTe-<chave>.xml` no mesmo ZIP/pasta ou em outro `--xml`; sem eles, o CT-e só passa pelas conferências de chave, espécie e fornecedor |
| SF1 (cabeçalho das entradas) | sim | colunas `Chave NFe`, `Vlr.Bruto`, `Base p/ICMS`, `Dt. Receb.` |
| SD1 (itens das entradas) | recomendado | colunas `Item NF`, `Cod. Fiscal`, `Sit.Tribut.`, `Tipo Entrada` |
| SF4 (cadastro de TES) | não (já vem guardada na skill) | colunas `Cod. do Tipo`, `Cred. ICMS ?`, `L.Fisc. ICMS`, `Credita IPI?` |
| SFT (livro fiscal por item) | opcional | colunas de documento, série, cli/for, loja, item e `Valor ICMS` (ou nomes técnicos `FT_NFISCAL`, `FT_ITEM`, `FT_VALICM`…) |

Os relatórios do Protheus costumam vir em xlsx "Strict OOXML", que o pandas não abre; o script converte sozinho com o LibreOffice. Os nomes dos arquivos não importam: identifique cada um pelas colunas (o script também valida e avisa se trocar a ordem). A SF4 vai inteira, sem filtro.

Se faltar a SD1, o cruzamento fica só no cabeçalho (sem CFOP, CST e itens).

## Crédito: TES × livro fiscal (SFT)

O SPED não lê a SD1 nem a TES: lê o livro fiscal (SFT/SF3), gravado na classificação com a TES daquele momento. `D1_VALICM` preenchido não é crédito. A skill decide o crédito nesta ordem:

1. **SFT, quando informada** (`--sft`): crédito é o `FT_VALICM`/`FT_VALIPI` do item. ICMS só em Outras/Isentas não vai para o C190/E110. É a resposta definitiva. Com a SFT vêm também quatro conferências: item sem linha no livro, crédito no livro em TES que não credita (TES alterada depois ou ajuste manual), TES que credita com livro sem crédito, e valor do livro diferente da SD1.
2. **TES coerente**: `Cred. ICMS ?` e `L.Fisc. ICMS` batendo (Sim × Tributado; Nao × Outros/Isento). Vale a TES.
3. **TES incoerente** (crédito e livro desencontrados, com cálculo ligado) ou fora da SF4: fica "Depende da TES" e a aba TES usadas marca a coluna **Crédito × livro na TES** em vermelho. Só a SFT resolve; peça-a ao usuário. O IPI segue a mesma lógica com `Credita IPI?` × `L.Fiscal IPI`.

A SFT deve ser extraída da mesma filial e do mesmo período de entrada da SD1; senão aparecem itens "sem registro no livro" que são só filtro. Se a SFT vier com títulos que o script não reconhece, ele para e lista as colunas: acrescente o título em `SFT_COLS` (`scripts/regras.py`). O mapeamento foi escrito antes de ver uma SFT real da Delpi; na primeira SFT recebida, confira se as colunas casaram (log mostra `SFT n itens`).

## CT-e (frete)

O CT-e é casado com a SF1 pela chave (modelo 57/67) e conferido contra a SD1 do próprio CT-e. Aba **CT-e Comparativo**; as ocorrências vão para **Divergências** com o prefixo "CT-e:".

- **Direito ao crédito** vem das NF-e transportadas (`infDoc` do CT-e): NF-e da própria empresa (raiz do CNPJ na chave) = frete de venda/transferência, com crédito; NF-e de terceiro lançada na SD1 com CFOP de insumo/revenda = com crédito; só consumo/ativo (x556, x407, x653, x551, x406) = sem crédito; transportadora do Simples ou CT-e sem ICMS = sem crédito. Sem NF vinculada na SD1, fica "Indefinido" e só se comparam os valores.
- **Crédito tomado** vem da SFT (se veio) ou da TES. As TES de frete com e sem crédito são listadas pela SF4 (CFOP x352) e citadas na correção.
- **CFOP esperado**: 1 + `352` quando a prestação começa na UF da empresa (`UFIni`), 2 + `352` quando começa em outra UF, 3 no exterior. `--cfop-frete` troca o final (padrão 352, estabelecimento industrial).
- Com crédito: base, alíquota, ICMS e CST (0 + CST do CT-e, ex.: 000) iguais ao XML. Sem crédito: CST 090.
- CT-e no XML e fora da SF1: Média se a empresa é a tomadora; Info se o tomador é outro CNPJ (quem paga o frete é quem escritura). CT-e escriturado sem a empresa ser a tomadora: Média.
- A TES 036 (FRETE S/ VENDAS) credita com livro Outros: sem SFT, os CT-e dela ficam "Depende da TES".

## Chave, espécie, série e fornecedor

Valem para todos os documentos da SF1, com ou sem XML:

- Chave que não está nos XML, mas há um XML (NF-e ou CT-e) de **mesmo número e valor**: Alta "Chave de acesso divergente do XML", e o cruzamento segue pela chave do XML.
- Chave com dígito verificador errado; espécie eletrônica sem chave; número ou série da chave diferentes do lançamento (quando não há XML).
- Espécie × modelo da chave: 55 SPED, 57 CTE, 67 CTEOS, 66 NF3E, 62 NFCOM, 65 NFCE.
- Fornecedor: o código/loja usado na nota é, nas outras notas do mês, de outro CNPJ (ou a SF1 traz uma coluna CNPJ diferente do emitente). Pega a nota lançada na matriz do fornecedor quando o emitente é a filial (e o inverso).

## SF4 guardada na skill

A SF4 é cadastro, não movimento: só muda quando alguém cria ou edita uma TES. Por isso uma cópia fica em `references/sf4/` (`SF4.csv` + `sf4_info.json` com a data de extração) e o `auditoria.py` usa essa cópia sempre que `--sf4` não é informado. **Não peça a SF4 ao usuário a cada mês.**

- Se o usuário mandar uma SF4 nova, passe `--sf4`: ela vale para aquela execução. Depois ofereça gravá-la na skill (ver abaixo).
- O script avisa no log e no Resumo (linha 2, em vermelho) quando: (a) a SD1 usa uma TES que não está na SF4 guardada (TES nova); os itens dela ficam "Depende da TES" e a aba TES usadas mostra "NÃO ESTÁ NA SF4"; (b) a SF4 guardada tem mais de 90 dias. Repasse esses avisos ao usuário e peça a SF4 atualizada.
- O que o script não detecta: TES existente que foi **editada** (a SF4 não traz data de alteração). Se o usuário disser que mexeu em TES, peça a SF4 nova.
- `--sem-sf4` ignora a cópia guardada (aba **TES a confirmar**, com colunas amarelas para preencher).

Para atualizar a cópia guardada: copie a skill para uma pasta gravável, rode `python scripts/atualizar_sf4.py <SF4.xlsx>` dentro da cópia (a data de extração vem da data de criação do xlsx; `--data AAAA-MM-DD` força), empacote com o `package_skill.py` do skill-creator mantendo o nome `auditoria-entradas-nfe-protheus` e entregue o `.skill` para o usuário reinstalar.

## Como rodar

1. Liste `/mnt/user-data/uploads` e identifique XML, SF1, SD1 e, se vier, SF4 (abra o cabeçalho se o nome não disser). Se vierem matriz e filial juntas, rode uma vez por unidade, cada SF1/SD1 com o ZIP do próprio CNPJ (confira o destinatário dos XML) e com `--cnpj`.
2. Rode:
   ```bash
   cd <pasta desta skill>/scripts
   python auditoria.py --xml <zip_ou_pasta> [--xml <zip_ou_pasta_CTe>] --sf1 <SF1> [--sd1 <SD1>] [--sf4 <SF4>] [--sft <SFT>] --out /mnt/user-data/outputs
   ```
   - `--filial` só é necessário se a SF1 tiver mais de uma filial e a detecção automática (filial com mais chaves batendo com os XML) não servir.
   - `--cnpj` força o CNPJ da empresa; por padrão é o destinatário mais frequente dos XML. `--uf` força a UF da empresa.
   - `--tes-presumido` define a TES do crédito presumido de 7% de SC (padrão `004`).
   - Vários `--xml` podem ser passados (ex.: download do mês e do mês anterior).
3. Confira o log: filial, CNPJ/UF, período, contagens (NF-e, CT-e, chaves corrigidas), a linha da SF4 (origem, data e `AVISO SF4`) e a da SFT (se veio, quantos itens leu). **Se a SD1 vier de outra filial que a SF1, nada liga**: o script mostra `SD1 0 itens`; avise o usuário e peça a extração da filial certa.
4. Recalcule as fórmulas: `python /mnt/skills/public/xlsx/scripts/recalc.py <arquivo> 90` (deve dar 0 erros).
5. Apresente o arquivo com `present_files`. Matriz e filial saem em planilhas separadas: entregue as duas.
6. Feche a entrega com o link do painel **Raio-X das Entradas** (ver seção abaixo). Não renomeie o arquivo de saída: o painel tira a unidade (`filial<FF>`) e o mês (`<mmmAAAA>`) do nome.

Saída: `cruzamento_entradas_filial<FF>_<mmmAAAA>.xlsx`.

## Painel Raio-X das Entradas

O usuário acompanha o resultado de todo mês no painel interativo **Raio-X das Entradas**: https://claude.ai/artifact/Xb4J8PH8f52AjVyHfp4XkM

Ao final de cada cruzamento, depois de apresentar as planilhas, escreva uma linha com o link e o passo: abrir o painel, clicar em **Abrir planilhas** e selecionar a planilha do mês (matriz e filial podem ir juntas). O painel lê as abas Comparativo, Divergências, Itens Divergências, Só no XML e Só no SF1, guarda cada mês no histórico do usuário por unidade e compara com o mês anterior. Se o layout dessas abas mudar (nomes de abas ou de colunas), avise que o painel precisa ser ajustado. As ocorrências de CT-e e de chave/espécie/fornecedor entram na aba Divergências com as mesmas colunas, então aparecem no painel; a aba CT-e Comparativo ainda não é lida por ele.

## O que a planilha traz

- **Resumo**: bases, ocorrências por tipo e severidade (com contagem e soma por fórmula) e impacto financeiro.
- **TES usadas** (ou **TES a confirmar**): configuração da SF4 de cada TES do período; destaca em vermelho TES de material de consumo que credita IPI.
- **Divergências / Comparativo**: cabeçalho SF1 × totais do XML.
- **Só no XML / Só no SF1**: notas sem par, com o motivo (fora do período, saída própria, cancelada, não escriturada, XML faltando).
- **Itens Divergências / Itens Comparativo**: SD1 × itens do XML.
- **Itens Agrupados**: notas lançadas com quantidade de itens diferente do XML (conferidas pelo total).
- **CT-e Comparativo**: cada CT-e escriturado × XML, com direito ao crédito, CFOP esperado, base, alíquota, ICMS e CST.
- **Itens Excluídos**: CT-e (conferidos na aba própria), serviço, NFCom, NF3e e documentos que não são DANFE. Item a item, só NF-e modelo 55.

As regras, severidades e a lógica de cada ocorrência estão em `references/regras.md`. Leia quando precisar explicar uma ocorrência ou ajustar uma regra.

## Como apresentar o resultado

Escreva em português, direto, explicando o porquê de cada ponto (o usuário gosta que "dê a letra"). Estrutura sugerida:

1. Uma linha com o casamento: quantas notas e CT-e casaram, quantas sem divergência, filial e período.
2. **O que pede ação** (Alta), com fornecedor, NF e valor. Agrupe por causa: o que interessa é a TES ou o cadastro que gera o erro, não a lista de itens.
3. **Para corrigir/verificar** (Média).
4. **Sem impacto** (Baixa), numa frase. Não comente o bloco "Não apontado" a não ser que o usuário pergunte.
5. Notas sem par: só os casos que não se explicam pela diferença de período (data de recebimento × data de emissão).

## Fornecedores do Simples: sublimite e crédito presumido de SC

Sempre que houver fornecedor do Simples, a skill aponta:

- **pCredSN acima do teto possível**: pelas tabelas da LC 123, o maior percentual de ICMS dentro do sublimite (RBT12 de R$ 3,6 mi) é **3,94%** no Anexo II (indústria) e **3,98%** no Anexo I (comércio). Acima disso, o fornecedor ultrapassou o sublimite (o ICMS sai do DAS e vai por fora, sem crédito SN) ou calculou errado. Exemplo: 4,06% numa indústria.
- **Fornecedor perto do sublimite**: o pCredSN é convertido em faturamento estimado; a partir de R$ 3 mi, aviso.
- **CSOSN 101/201 sem alíquota**: sem pCredSN no documento não há crédito.

Quando a empresa é de **SC**, vale também o **crédito presumido de 7%** do RICMS/SC (Anexo 2, art. 15, XXVI): compra interna de indústria do Simples de SC (CFOP 5101, 5103, 5105, 5109 ou 5401 no XML), calculado sobre o valor da aquisição, em substituição ao crédito do art. 23 (COPAT 84/2025) e sem direito se o fornecedor passou do sublimite (COPAT 75/2022). Regras do usuário:

- Essas notas **têm de estar na TES 004**. Em outra TES, o fornecedor **não está cadastrado no Configurador de Tributos** do Protheus: aponte com o valor de 7% esperado e diga que é preciso cadastrar o fornecedor. Severidade Alta; Média quando a entrada é de uso e consumo/ativo, porque o alcance do presumido para esse destino precisa ser confirmado (§ 25).
- TES 004 com pCredSN acima do teto: Alta, presumido possivelmente indevido.
- TES 004 com valor no item diferente de 7%: Média, conferir a regra no Configurador de Tributos.
- TES 004 em nota sem direito (não Simples, fora de SC, ou CFOP que não é de produção própria): Média.

O fornecedor não informa os 7% na nota; o que vem nos dados adicionais é sempre o pCredSN do art. 23. Explique isso se o usuário estranhar.

Pontos que já geraram correção do usuário e não podem ser esquecidos:

- `D1_VALICM`/`F1_VALICM` preenchido **não** significa crédito. Quem decide é o livro fiscal (SFT); sem ela, a TES (`F4_CREDICM` e `F4_LFICM` coerentes). Nunca afirme crédito indevido sem a SF4; sem ela (ou para TES ausente da SF4 guardada), fale em "ICMS calculado" e "depende da TES".
- A SF1 não tem CFOP nem CST; isso vem da SD1.
- Diferença de período é normal: SF1 é filtrada por recebimento e o download de XML por emissão. Notas de um mês emitidas no mês anterior aparecem como "Só no SF1" com situação Info.
- Uso e consumo sem crédito, ICMS/IPI calculado em TES sem crédito, CST 090 nas TES sem crédito e CST 060 em combustível são padrão da empresa: não apontar (ver "Regras da empresa").

Se a SD1 ou a SF4 trouxerem colunas com nomes diferentes (outra versão do relatório), ajuste os nomes em `scripts/regras.py` (listas `SF1_NUM`/`SD1_NUM` e acessos às colunas) em vez de renomear à mão no Excel.
