"""Constantes e textos da skill. O motor não importa pandas nem o script de referência."""

TOLERANCE = 0.05
SEVERITY_ORDER = {"Alta": 0, "Depende da TES": 1, "Média": 2, "Baixa": 3, "Info": 4, "OK": 5}
CRT_NAME = {"1": "Simples Nacional", "2": "Simples (excesso)", "3": "Regime normal", "4": "MEI"}
SUPPLY_SUFFIXES = {"101", "102", "401", "403", "151", "152", "122", "124", "125", "126"}
CONSUMPTION_OR_ASSET = ("551", "556", "407", "406", "653")
SALE = set("101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 122 123 124 125 401 402 403 404 405 651 652 653 654 655 656 929 922".split())
SALE_IN = set("101 102 111 113 116 117 118 120 121 122 124 125 126 128 401 403 406 407 551 556 651 652 653".split())
TRANSFER = set("151 152 153 155 156 408 409 552 557 659".split())
TRANSFER_IN = set("151 152 153 154 155 156 408 409 552 557 658 659".split())
RETURN = set("201 202 203 204 205 206 207 208 209 210 410 411 412 413 503 553 555 556 660 661 662 918 919".split())
RETURN_IN = set("201 202 203 204 208 209 410 411 503 553 554 555 660 661 662 918 919".split())
CFOP_GROUPS = [
    (SALE, SALE_IN, "compra"),
    (TRANSFER, TRANSFER_IN, "transferência"),
    (RETURN, RETURN_IN, "devolução"),
    ({"915", "916"}, {"915", "916"}, "conserto"),
    ({"901", "902", "903", "924", "925"}, {"901", "902", "903", "924", "925", "949"}, "industrialização por encomenda"),
    ({"910"}, {"910"}, "bonificação"),
    ({"911"}, {"911"}, "amostra grátis"),
    ({"920", "921"}, {"920", "921"}, "vasilhame/sacaria"),
    ({"912", "913"}, {"912", "913"}, "demonstração"),
    ({"908", "909"}, {"908", "909"}, "comodato"),
]
ST_CST = {"10", "30", "60", "61", "70"}
ST_CSOSN = {"201", "202", "203", "500"}
EXCLUDED_BY_SPECIES = {
    "CTE": "CT-e (frete), conferido na aba CT-e Comparativo",
    "CTEOS": "CT-e (frete), conferido na aba CT-e Comparativo",
    "NFS": "Nota de serviço (ISS)",
    "NFSE": "Nota de serviço (ISS)",
    "RPS": "Nota de serviço (ISS)",
    "NFCOM": "NFCom (comunicação)",
    "NF3E": "NF3e (energia elétrica)",
    "NFCE": "NFC-e (cupom)",
}
EXCLUDED_BY_SUFFIX = {
    "352": "CT-e (frete), conferido na aba CT-e Comparativo",
    "933": "Nota de serviço (ISS)",
    "302": "NFCom (comunicação)",
    "301": "NFCom (comunicação)",
    "252": "NF3e (energia elétrica)",
    "251": "NF3e (energia elétrica)",
    "253": "NF3e (energia elétrica)",
}
OTHER_EXCLUDED = "Outros documentos fora das DANFE (recibos, cupons, notas não eletrônicas)"
ANNEX = {
    "I": [(180000, 0.040, 0, 0.34), (360000, 0.073, 5940, 0.34), (720000, 0.095, 13860, 0.335), (1800000, 0.107, 22500, 0.335), (3600000, 0.143, 87300, 0.335)],
    "II": [(180000, 0.045, 0, 0.32), (360000, 0.078, 5940, 0.32), (720000, 0.100, 13860, 0.32), (1800000, 0.112, 22500, 0.32), (3600000, 0.147, 85500, 0.32)],
}
SUBLIMIT = 3_600_000
SUBLIMIT_ALERT = 3_000_000
INDUSTRY_SUFFIXES = {"101", "103", "105", "109", "401"}
PRESUMED = {"state": "SC", "rate": 0.07, "tes": "004"}
FUEL_NCM = ("2710", "2711", "2207", "3826")
FUEL_SUFFIXES = {"653", "656", "667", "661", "662", "663", "664"}
NATURE = {
    "consumo": {"556", "407", "653"},
    "ativo": {"551", "406"},
    "insumo/revenda": {"101", "102", "401", "403", "122", "124", "125", "126"},
}
MODEL_SPECIES = {
    "55": ({"SPED", "NFE", "NF-E"}, "SPED (NF-e)"),
    "57": ({"CTE", "CT-E"}, "CTE"),
    "67": ({"CTEOS"}, "CTEOS"),
    "66": ({"NF3E"}, "NF3E (energia elétrica)"),
    "62": ({"NFCOM"}, "NFCOM (comunicação)"),
    "65": ({"NFCE"}, "NFCE"),
}
ELECTRONIC_SPECIES = {"SPED", "NFE", "CTE", "CTEOS", "NF3E", "NFCOM", "NFCE"}
TAKER_ROLE = {"rem": "remetente", "dest": "destinatário", "exped": "expedidor", "receb": "recebedor", "outros": "outro"}

LABEL_ICMS_WITHOUT_CREDIT = "ICMS calculado em TES sem crédito (não vai para o SPED)"
LABEL_HEADER_BASE = "Base de ICMS diferente em nota sem crédito"
LABEL_IPI_TOTAL_OK = "IPI diferente do XML com total conferindo (TES sem crédito de IPI ou IPI em outro campo)"
LABEL_CST_090 = "CST 090 em TES sem crédito (padrão da empresa)"
LABEL_CST_060 = "CST 060 em combustível ou item com ST (padrão da empresa)"
LABEL_RATE_OR_BASE = "Alíquota/base de ICMS diferente em TES sem crédito"
LABEL_IPI_WITHOUT_CREDIT = "IPI diferente do XML em TES sem crédito de IPI (não vai para o SPED)"

# Leitura curta da planilha (relatorio.LEIT): o «por quê». O «o que fazer» é o texto montado em cada regra.
WHY = {
    "Crédito de ICMS sem destaque no XML": "Crédito tomado em TES que credita, sem ICMS no documento. Estornar.",
    "Crédito de ICMS acima do XML": "Crédito acima do destacado (ou do crédito SN) em TES que credita. Estornar o excedente.",
    "ICMS calculado sem destaque no XML": "ICMS calculado sem ICMS no documento. Só é crédito indevido se a TES creditar (aba TES).",
    "ICMS calculado acima do XML": "ICMS calculado acima do destacado. Só é crédito a maior se a TES creditar (aba TES).",
    "Item sem registro no livro fiscal (SFT)": "Item da SD1 sem linha na SFT: não vai para o SPED. Reprocessar os livros (MATA930).",
    "Crédito no livro fiscal em TES que não credita": "O livro (SFT) tem crédito que a TES não prevê: TES alterada depois ou ajuste manual. Vai para a apuração.",
    "Crédito previsto na TES fora do livro fiscal": "A TES credita, mas o livro (SFT) está sem crédito: crédito não aproveitado.",
    "ICMS do livro fiscal diferente do item": "Valor creditado no livro (SFT) diferente do calculado na SD1.",
    "IPI destacado no XML não escriturado": "TES sem cálculo de IPI: o total da nota e o título ficam menores que o documento.",
    "Valor total da nota diverge": "Total escriturado diferente do vNF. Em geral acompanha o IPI não escriturado.",
    "Base de ICMS divergente": "Acompanha a divergência de ICMS da mesma nota.",
    "ICMS do XML não creditado": "ICMS destacado zerado no Protheus em nota que não é só de consumo/ativo.",
    "Data de emissão divergente": "Data digitada errada no documento de entrada.",
    "Base de ICMS divergente (ICMS confere)": "Sem impacto no imposto.",
    "Acessório lançado em campo diferente (total confere)": "Frete como despesa, ou composição de importação. Sem impacto no total.",
    "Crédito de ICMS em CFOP de uso e consumo": "Uso e consumo creditando ICMS em TES que credita. Estornar e corrigir a TES.",
    "ICMS calculado em CFOP de uso e consumo": "Uso e consumo com ICMS calculado. Só é crédito indevido se a TES creditar.",
    "Crédito de ICMS com CST sem tributação": "CST 40/41/50/60 com crédito em TES que credita. Estornar.",
    "ICMS calculado com CST sem tributação": "CST sem ICMS próprio com ICMS calculado. Depende da TES.",
    "Crédito de IPI em material de uso e consumo": "TES de material de consumo creditando IPI. IPI só gera crédito em MP, PI e embalagem.",
    "Crédito do Simples não aproveitado (TES sem crédito)": "Compra para industrialização/revenda de fornecedor do Simples com crédito SN no XML, em TES que não credita.",
    "ICMS destacado não creditado em insumo/revenda (TES sem crédito)": "CFOP com direito a crédito em TES que não credita.",
    "IPI do XML não escriturado": "TES sem cálculo de IPI.",
    "NF de entrada do fornecedor lançada como compra": "XML com CFOP de entrada emitido pelo fornecedor: a empresa é remetente.",
    "Item com ST no XML lançado em CFOP sem ST": "Itens com ICMS-ST lançados em CFOP sem ST: o correto é x407 (uso e consumo), x403 (revenda), x401 (industrialização) ou x406 (ativo).",
    "CFOP de ST sem ST no XML": "CFOP de ST em item sem ST no documento.",
    "CST diverge do documento": "Tributação lançada diferente da nota (ex.: CST 61 de combustível gravado como 60).",
    "Origem da mercadoria divergente": "Primeiro dígito do CST diferente do XML. Impacta a regra dos 4% e o cadastro do produto.",
    "CFOP de entrada incompatível com a UF do fornecedor": "Primeiro dígito do CFOP não bate com a UF (1 interna, 2 interestadual, 3 exterior).",
    "Alíquota de crédito SN acima do teto do Simples": "pCredSN acima do máximo possível dentro do sublimite (3,94% indústria / 3,98% comércio): fornecedor acima do sublimite ou cálculo errado.",
    "Fornecedor do Simples perto do sublimite": "pCredSN indica faturamento (RBT12) a partir de R$ 3 mi. Acompanhar.",
    "CSOSN com permissão de crédito sem alíquota informada": "CSOSN 101/201 sem pCredSN: sem alíquota no documento não há crédito.",
    "Indústria do Simples (SC) fora da TES de crédito presumido": "Compra interna de indústria do Simples de SC fora da TES do presumido: fornecedor sem cadastro no Configurador de Tributos.",
    "Crédito presumido com fornecedor acima do sublimite": "Presumido de 7% em fornecedor com pCredSN acima do teto: possível sublimite ultrapassado.",
    "Valor no item diferente do crédito presumido de 7%": "Valor calculado no item diferente de 7% do valor da aquisição.",
    "TES de crédito presumido em nota sem direito": "TES do presumido usada em nota que não é de indústria do Simples de SC.",
    "Natureza do CFOP incompatível com o documento": "Compra, transferência, devolução, conserto etc. lançada em CFOP de outra natureza.",
    "Chave de acesso divergente do XML": "Chave digitada diferente da do XML de mesmo número e valor. O SPED leva um documento que não existe.",
    "Documento eletrônico sem chave de acesso": "Espécie eletrônica (SPED, CTE, NF3E...) lançada sem a chave.",
    "Chave de acesso inválida": "Dígito verificador não confere: chave digitada errada.",
    "Chave de acesso não confere com o número do documento": "O número embutido na chave é outro (sem XML para comparar).",
    "Série divergente da chave de acesso": "A série embutida na chave é outra (sem XML para comparar).",
    "Espécie do documento incompatível com a chave": "Modelo da chave (55 NF-e, 57 CT-e, 66 NF3e, 62 NFCom) diferente da espécie lançada.",
    "Fornecedor do lançamento com CNPJ diferente do emitente": "Código/loja do fornecedor de outro CNPJ: participante errado no SPED e título no fornecedor errado.",
    "Série divergente do XML": "Série digitada diferente da do documento.",
    "Produto lançado com natureza de CFOP diferente do usual": "Mesmo produto entrando como consumo, insumo ou ativo em notas diferentes: conferir a destinação.",
    "Base de IPI divergente": "IPI confere, mas a base escriturada difere da do documento (C170).",
    "Crédito de IPI abaixo do XML": "TES que credita IPI com valor menor que o destacado: crédito perdido.",
    "Crédito de IPI acima do XML": "TES que credita IPI com valor maior que o destacado: estornar.",
    "Alíquota de ICMS divergente (valor confere)": "Valor confere, mas a alíquota gravada difere (C170).",
    "CT-e: valor da prestação diverge": "Valor escriturado diferente do vTPrest do CT-e.",
    "CT-e: CFOP divergente": "Frete de estabelecimento industrial: 1352 quando o transporte começa na UF da empresa, 2352 quando começa em outra UF.",
    "CT-e: crédito de ICMS em frete sem direito": "Frete de uso e consumo/ativo ou CT-e sem ICMS lançado em TES que credita: zerar base, alíquota e ICMS, CST 090.",
    "CT-e: ICMS do frete não creditado": "Frete com direito a crédito (venda ou compra de insumo) em TES sem crédito: lançar base, alíquota e ICMS do CT-e.",
    "CT-e: crédito de ICMS acima do XML": "Crédito maior que o ICMS do CT-e.",
    "CT-e: crédito de ICMS abaixo do XML": "Crédito menor que o ICMS do CT-e.",
    "CT-e: alíquota de ICMS divergente": "Alíquota escriturada diferente da do CT-e.",
    "CT-e: base de ICMS divergente": "Base escriturada diferente da do CT-e.",
    "CT-e: CST divergente": "Com crédito, CST do CT-e (000); sem crédito, 090.",
    "CT-e: ICMS calculado em frete sem direito": "TES com crédito e livro desencontrados: só a SFT diz se foi para o SPED.",
    "CT-e: ICMS calculado diferente do XML": "TES com crédito e livro desencontrados: só a SFT diz se foi para o SPED.",
    "CT-e escriturado sem a empresa ser a tomadora": "O tomador do CT-e é outro CNPJ: só o tomador escritura e credita.",
    "Valor das mercadorias diverge": "Quantidade/preço digitado diferente do XML.",
    "ICMS ST diverge": "Conferir ST na TES.",
    "ICMS ST divergente": "Rever ST na TES.",
    "Desconto classificado diferente": "Total confere.",
    "Combustível fora do CFOP x653": "Venda de combustível a consumidor final: entrada usual em 1653/2653.",
    "Valor do item diverge": "Quantidade ou preço digitado diferente do XML.",
    "CFOP diferente do documento emitido": "Formulário próprio: o CFOP lançado tem de ser o do XML.",
    "CFOP com origem trocada (interna × interestadual)": "O primeiro dígito da entrada não corresponde à origem do CFOP do fornecedor.",
    "Crédito de ICMS a menor": "ICMS no Protheus menor que o do XML: conferir alíquota/redução na TES.",
    "IPI escriturado sem destaque no XML": "Protheus calcula IPI que o documento não traz.",
    "IPI escriturado sem destaque no XML": "Rever a TES.",
    "Base de ICMS divergente (ICMS confere)": "ICMS igual ao XML, mas a base escriturada difere.",
}
