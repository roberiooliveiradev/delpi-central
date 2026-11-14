# Regras do cruzamento

Tolerância de R$ 0,05 em todos os valores. Casamento SF1 × XML pela chave de acesso (NF-e 55, CT-e 57/67); SD1 × SF1 por Filial + Documento + Série + Fornecedor + Loja. Chave da SF1 que não está nos XML é trocada pela do XML de mesmo número e mesmo valor total (se houver um só), e a troca vira ocorrência Alta.

## Não apontado (regra da empresa)
Contados no fim do Resumo, sem linha nas abas de divergência:
- ICMS calculado (sem destaque, acima do XML, em CFOP de consumo ou com CST sem tributação) quando a TES/livro não credita.
- Base ou alíquota de ICMS diferentes, com ICMS conferindo, em item de TES sem crédito; base de ICMS do cabeçalho em nota sem crédito.
- IPI diferente do XML em TES que não credita IPI; IPI em outro campo com total conferindo.
- CST 090 em TES sem crédito; CST 060 em combustível ou item com ST.
- "ICMS do XML não creditado" do cabeçalho (com SD1 vale a regra do item, que só aponta CFOP de insumo em TES sem crédito).

## Severidades
- **Alta**: erro com efeito em imposto ou no valor a pagar.
- **Depende da TES**: aparece sem SF4 (`--sem-sf4`), para TES ausente da SF4 ou para TES com crédito e livro desencontrados quando não há SFT. Com SFT, decide o livro: Alta se o item tem `FT_VALICM`, Baixa se está em Outras/Isentas. Sem SFT e com TES coerente, Alta (TES credita) ou Baixa (não credita).
- **Média**: classificação fiscal errada ou crédito perdido; precisa correção, mas não gera débito.
- **Baixa**: diferença de forma, sem impacto no imposto.
- **Info**: explicação de nota sem par (período, saída própria, cancelada).

## Referência do ICMS
- Fornecedor regime normal (CRT 3): `vICMS` do XML.
- Fornecedor Simples/MEI (CRT 1/4): `vCredICMSSN` (crédito SN permitido). Base e CST do Simples não são comparadas; só a origem.

## Cabeçalho (SF1 × totais do XML)
| Ocorrência | Regra | Sev. |
|---|---|---|
| ICMS calculado sem destaque / acima do XML | `F1_VALICM` > referência | Depende da TES → Alta se alguma TES da nota credita, senão Baixa |
| ICMS do XML não creditado | `F1_VALICM` = 0, XML com ICMS, e a nota não é só de TES de consumo/ativo | Média |
| Crédito de ICMS a menor | 0 < Protheus < XML | Média |
| Base de ICMS divergente | acompanha o ICMS; se o ICMS confere e a nota credita, Média | — |
| IPI não escriturado / sem destaque | `F1_VALIPI` × (vIPI + vIPIDevol dos itens), com total divergente | Alta |
| Série divergente do XML | `F1_SERIE` × serie | Média |
| Valor total / mercadorias / ST | `F1_VALBRUT`×vNF, `F1_VALMERC`×vProd, ST | Alta |
| Acessório em campo diferente | frete×despesa trocados, total confere; em importação, vOutro soma II/PIS/COFINS | Baixa |
| Data de emissão divergente | `F1_EMISSAO` × dhEmi | Média |

## Itens (SD1 × det do XML)
Pareamento: mesma quantidade de itens → pela ordem (`Item NF` × `nItem`); se os valores não batem, tenta casar pelo valor. Quantidade diferente → aba Itens Agrupados.

| Ocorrência | Regra | Sev. |
|---|---|---|
| Valor do item diverge | `D1_TOTAL` × vProd | Alta |
| CFOP com origem trocada | 5→1, 6→2, 7→3 | Alta |
| NF de entrada do fornecedor lançada como compra | CFOP do XML começa com 1/2/3 e o emitente é terceiro | Alta |
| CFOP diferente do documento emitido | formulário próprio com CFOP ≠ XML | Alta |
| Natureza do CFOP incompatível | grupo do CFOP de saída (compra, transferência, devolução, conserto, industrialização, bonificação, amostra, vasilhame, demonstração, comodato) × CFOP de entrada | Média |
| Item com ST no XML em CFOP sem ST | CST 10/30/60/61/70, CSOSN 201/202/203/500 ou CFOP x401–x405, lançado em x101/x102/x556/x551 (sugere x401/x403/x407/x406) | Média |
| CFOP de ST sem ST no XML | o inverso | Média |
| Origem divergente | 1º dígito do `D1_CLASFIS` × orig | Média |
| CST diverge do documento | últimos 2 dígitos × CST (só CRT 3) | Média |
| CST 090 / 060 no lugar do CST do documento | 090 em TES sem crédito; 060 em combustível ou item com ST | não apontado |
| ICMS calculado sem destaque / acima do XML | como no cabeçalho, por item; mostra alíquotas | Depende da TES |
| Crédito do Simples não aproveitado | CRT 1/4 com vCredICMSSN, CFOP de insumo/revenda, TES com Credita ICMS = Não | Média |
| ICMS destacado não creditado em insumo/revenda | CRT 3, CFOP de insumo/revenda, TES sem crédito | Média |
| IPI do XML não escriturado / escriturado sem destaque | `D1_VALIPI` × vIPI + vIPIDevol, sem SF4 para decidir | Alta |
| Crédito de IPI abaixo / acima do XML | TES (ou livro) credita IPI e o valor difere | Média / Alta |
| Base de IPI divergente | IPI confere, TES credita IPI, `D1_BASEIPI` × vBC do IPI | Média |
| ICMS ST divergente | `D1_ICMSRET` × vICMSST | Alta |
| Alíquota/base de ICMS divergente com ICMS conferindo | só em item com crédito | Média |
| Produto lançado com natureza de CFOP diferente do usual | o mesmo produto entra no mês ≥ 2 vezes numa natureza (consumo, insumo/revenda, ativo) e nesta nota em outra | Média |

### Coerência interna (vale também para itens sem XML)
| Ocorrência | Regra | Sev. |
|---|---|---|
| CFOP × UF do fornecedor | 1 = mesma UF da empresa, 2 = outra UF, 3 = EX (exceto formulário próprio) | Alta |
| Crédito de IPI em material de uso e consumo | TES com `Mat.Consumo` = Sim e `Credita IPI?` = Sim, item com IPI | Alta |
| ICMS calculado em CFOP de uso e consumo | x556/x407 com `D1_VALICM` > 0 | Depende da TES |
| ICMS calculado com CST sem tributação | CST 40/41/50/60/61 com ICMS > 0 | Depende da TES |

### Simples Nacional: sublimite e presumido de SC
Teto do pCredSN dentro do sublimite: [(alíq. nominal da 5ª faixa − parcela a deduzir / 3.600.000) × % do ICMS na partilha] → Anexo II: (14,7% − 2,375%) × 32% = **3,944%**; Anexo I: (14,3% − 2,425%) × 33,5% = **3,978%**. O anexo é escolhido pelo CFOP do fornecedor (x101, x103, x105, x109, x401 = indústria, Anexo II). A RBT12 estimada inverte a fórmula na faixa em que o pCredSN cai: RBT12 = PD / (alíq. nominal − pCredSN / %ICMS).

| Ocorrência | Regra | Sev. |
|---|---|---|
| Alíquota de crédito SN acima do teto do Simples | pCredSN > teto do anexo | Média (nota) |
| Fornecedor do Simples perto do sublimite | RBT12 estimada ≥ R$ 3 mi | Baixa (nota) |
| CSOSN com permissão de crédito sem alíquota informada | CSOSN 101/201 com pCredSN = 0 | Baixa (nota) |
| Indústria do Simples (SC) fora da TES de crédito presumido | empresa em SC, fornecedor SC, CRT 1, CFOP 5101/5103/5105/5109/5401, TES ≠ 004 | Alta; Média se entrada de consumo/ativo |
| Crédito presumido com fornecedor acima do sublimite | idem, TES 004 e pCredSN > teto | Alta |
| Valor no item diferente do crédito presumido de 7% | TES 004, `D1_VALICM` > 0 e ≠ 7% × (vProd − vDesc) | Média |
| TES de crédito presumido em nota sem direito | empresa em SC, TES 004, e o item não cumpre as condições | Média |

Nos itens com direito ao presumido, as regras gerais de ICMS e de "crédito do Simples não aproveitado" não são aplicadas (o crédito de referência passa a ser 7%, e não o vCredICMSSN). No cabeçalho, a comparação de ICMS e base dessas notas também é pulada.

CFOPs de insumo/revenda (dão direito a crédito): x101, x102, x122, x124, x125, x126, x151, x152, x401, x403.

## Notas sem par
- **Só no XML**: cancelada (evento 110111 ou cStat 101/135/151/155) → Info; saída própria → Info (vai na SF2); entrada de formulário próprio sem lançamento → Alta; destinatário de outro CNPJ → Info; terceiro não escriturado → Média (com aviso de "em trânsito" para emissões dos últimos 3 dias do download).
- **Só no SF1**: emissão anterior ao primeiro XML do download → Info (diferença de período); dentro do período → Média (baixar o XML).

## Exclusões da SD1
Itens cuja nota não é DANFE (pela espécie na SF1 ou pela chave). Classificação: espécie (CTE, NFS, NFCOM, NF3E, NFCE) ou, sem espécie, CFOP x352 (CT-e), x933 (serviço), x301/x302 (NFCom), x251–x253 (NF3e); o resto entra como "outros documentos".

## Conferências do livro fiscal (só com `--sft`)

| Ocorrência | Quando | Severidade |
|---|---|---|
| Item sem registro no livro fiscal (SFT) | item de DANFE na SD1 sem linha na SFT (mesma filial/doc/série/fornecedor/loja/item) | Média |
| Crédito no livro fiscal em TES que não credita | TES coerente sem crédito e `FT_VALICM` > 0 (se o item já tem Alta de crédito indevido, a explicação vai nela) | Alta |
| Crédito previsto na TES fora do livro fiscal | TES credita, SD1 calculou ICMS e o livro está sem crédito | Média |
| ICMS do livro fiscal diferente do item | livro e SD1 com crédito, valores diferentes | Média |

Com SFT, o crédito indevido e o crédito de IPI em uso e consumo usam o valor do livro, não o da SD1.

## CT-e (aba CT-e Comparativo; ocorrências em Divergências com prefixo "CT-e:")
Direito ao crédito pelo `infDoc`: NF-e com a raiz do CNPJ da empresa na chave (venda/transferência) ou NF-e de terceiro na SD1 com CFOP de insumo/revenda = Sim; NF-e de terceiro só com CFOP de consumo/ativo = Não; Simples (ICMSSN) ou CT-e sem ICMS = Não; ICMS60 ou sem NF na SD1 = Indefinido. Crédito tomado: SFT, senão TES, senão (sem SD1) ICMS da SF1.

| Ocorrência | Regra | Sev. |
|---|---|---|
| CT-e: valor da prestação diverge | `F1_VALBRUT` × vTPrest | Alta |
| CT-e: CFOP divergente | CFOP da SD1 ≠ (1 se UFIni = UF da empresa, 2 outra UF, 3 EX) + `--cfop-frete` | Média |
| CT-e: crédito de ICMS em frete sem direito | TES/livro credita e direito = Não | Alta |
| CT-e: ICMS do frete não creditado | TES/livro não credita e direito = Sim | Média |
| CT-e: crédito de ICMS acima / abaixo do XML | credita e ICMS ≠ vICMS (ICMSOutraUF: vICMSOutraUF) | Alta / Média |
| CT-e: alíquota / base de ICMS divergente | credita e pICMS/vBC diferentes | Média |
| CT-e: CST divergente | com crédito ≠ 0 + CST do CT-e; sem crédito ≠ x90 | Média |
| CT-e: ICMS calculado em frete sem direito / diferente do XML | TES com crédito e livro desencontrados, sem SFT | Depende da TES |
| CT-e escriturado sem a empresa ser a tomadora | tomador (toma3/toma4) com outro CNPJ | Média |
| Só no XML (CT-e) | empresa tomadora e sem lançamento → Média; tomador outro CNPJ ou cancelado → Info | — |

## Chave, espécie e fornecedor (todos os documentos da SF1)
| Ocorrência | Regra | Sev. |
|---|---|---|
| Chave de acesso divergente do XML | chave fora dos XML e um único XML com mesmo número e valor total | Alta |
| Documento eletrônico sem chave de acesso | espécie SPED/CTE/CTEOS/NF3E/NFCOM/NFCE com chave vazia | Alta |
| Chave de acesso inválida | 44 dígitos e DV módulo 11 | Alta |
| Chave de acesso não confere com o número do documento | sem XML: nNF da chave (posições 26–34) ≠ número | Alta |
| Série divergente da chave de acesso | sem XML: série da chave (23–25) ≠ série | Média |
| Espécie do documento incompatível com a chave | modelo da chave (21–22) × espécie: 55 SPED, 57 CTE, 67 CTEOS, 66 NF3E, 62 NFCOM, 65 NFCE | Média |
| Fornecedor do lançamento com CNPJ diferente do emitente | coluna CNPJ da SF1, se houver; senão, o código/loja tem outro CNPJ em ≥ 2 notas do mês e em mais notas que o emitente desta (CNPJ do XML, ou o da chave sem XML) | Alta |
