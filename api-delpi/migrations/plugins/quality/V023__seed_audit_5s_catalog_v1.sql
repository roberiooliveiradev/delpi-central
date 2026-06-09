-- Seed catálogo Auditoria 5S v1 + sequências por filial
INSERT INTO quality.audit_5s_sensos (sort_order, name)
VALUES
    (1, 'Utilização'),
    (2, 'Ordenação'),
    (3, 'Limpeza'),
    (4, 'Padronização'),
    (5, 'Disciplina')
ON CONFLICT (sort_order) DO NOTHING;

INSERT INTO quality.document_sequences (sequence_key, prefix, current_value, padding_length, active)
VALUES
    ('audit_5s_branch_01', '01', 0, 6, TRUE),
    ('audit_5s_branch_02', '02', 0, 6, TRUE)
ON CONFLICT (sequence_key) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'U01', 'Há somente materiais, ferramentas, equipamentos, documentos e objetos necessários para a atividade da área.', 1, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 1
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'U02', 'Não existem materiais obsoletos, danificados, vencidos, sem identificação ou sem previsão de uso.', 2, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 1
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'U03', 'Os itens pessoais estão controlados e não interferem na organização, segurança ou aparência da área.', 3, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 1
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'U04', 'Não há acúmulo de caixas, embalagens, papéis, sucatas, peças, amostras ou objetos sem finalidade definida.', 4, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 1
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'U05', 'Materiais de uso eventual estão separados dos materiais de uso frequente.', 5, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 1
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'U06', 'Produtos, materiais ou documentos retidos, segregados ou aguardando decisão estão identificados e em local adequado.', 6, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 1
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'U07', 'A área não possui equipamentos, móveis ou dispositivos quebrados, inutilizados ou aguardando manutenção sem identificação.', 7, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 1
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'U08', 'O espaço disponível é utilizado de forma adequada, sem ocupação desnecessária de corredores, bancadas, armários ou áreas de circulação.', 8, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 1
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O01', 'Materiais, ferramentas, equipamentos, documentos e objetos possuem local definido para armazenamento.', 1, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O02', 'Os itens estão armazenados nos locais corretos e de forma organizada.', 2, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O03', 'As identificações de armários, prateleiras, gavetas, caixas, áreas, bancadas ou posições estão visíveis e atualizadas.', 3, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O04', 'Os materiais de maior uso estão posicionados de forma acessível e prática para a rotina da área.', 4, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O05', 'Corredores, acessos, portas, extintores, painéis elétricos e rotas de fuga estão livres e desobstruídos.', 5, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O06', 'Há separação adequada entre materiais aprovados, reprovados, em análise, aguardando uso, descarte ou devolução.', 6, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O07', 'Documentos, registros, formulários e instruções de trabalho estão disponíveis, organizados e protegidos contra danos.', 7, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O08', 'A disposição dos itens favorece a segurança, o fluxo de trabalho e a produtividade.', 8, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O09', 'Não há mistura de materiais, ferramentas, documentos ou produtos de diferentes finalidades no mesmo local.', 9, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'O10', 'As demarcações de piso, áreas de armazenamento, circulação, descarte ou segurança estão visíveis e sendo respeitadas.', 10, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 2
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L01', 'Piso, bancadas, mesas, prateleiras, armários, equipamentos e máquinas estão limpos.', 1, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L02', 'Não há acúmulo de poeira, resíduos, aparas, óleo, graxa, restos de materiais, alimentos ou sujeira visível.', 2, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L03', 'Lixeiras, coletores ou recipientes de descarte estão disponíveis, identificados e em boas condições de uso.', 3, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L04', 'Os resíduos são descartados corretamente, sem mistura indevida ou acúmulo fora dos locais determinados.', 4, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L05', 'A área não apresenta vazamentos, infiltrações, mau cheiro, presença de insetos, umidade excessiva ou sinais de deterioração.', 5, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L06', 'Equipamentos, instrumentos, máquinas ou ferramentas estão limpos e conservados após o uso.', 6, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L07', 'A limpeza da área não depende apenas de ações pontuais antes da auditoria, demonstrando manutenção contínua.', 7, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L08', 'Os materiais de limpeza, quando existentes na área, estão armazenados corretamente e identificados.', 8, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L09', 'Não há risco de contaminação, dano ao produto, dano a documentos ou comprometimento de equipamentos por falta de limpeza.', 9, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'L10', 'A aparência geral da área transmite cuidado, conservação e zelo pelo ambiente de trabalho.', 10, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 3
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P01', 'Existem padrões visuais claros para organização, armazenamento, identificação e limpeza da área.', 1, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P02', 'As identificações, etiquetas, placas, sinalizações e demarcações estão padronizadas e legíveis.', 2, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P03', 'O padrão definido é seguido por todos os colaboradores da área, sem variações indevidas entre turnos ou pessoas.', 3, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P04', 'Há definição clara dos locais para materiais, ferramentas, documentos, produtos, resíduos, EPIs e objetos de uso comum.', 4, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P05', 'Procedimentos, instruções, quadros, formulários ou orientações aplicáveis estão disponíveis e atualizados.', 5, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P06', 'A área possui rotina definida para limpeza, organização, descarte ou inspeção dos itens críticos.', 6, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P07', 'Os padrões de segurança, qualidade, meio ambiente e organização estão integrados ao 5S da área.', 7, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P08', 'Os itens fora do padrão são facilmente identificáveis pelo auditor ou pelos colaboradores.', 8, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P09', 'As informações expostas em murais, quadros, placas ou documentos são necessárias, atuais e bem conservadas.', 9, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'P10', 'O padrão da área contribui para evitar erros, perdas, retrabalhos, acidentes ou dificuldades na execução das atividades.', 10, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 4
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D01', 'Os colaboradores demonstram conhecimento básico sobre os padrões de 5S aplicáveis à sua área.', 1, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D02', 'A área mantém a organização durante a rotina normal de trabalho, e não apenas em momentos de auditoria.', 2, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D03', 'Os itens são devolvidos aos locais corretos após o uso.', 3, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D04', 'As regras de descarte, armazenamento, identificação, limpeza e segurança são respeitadas.', 4, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D05', 'Não há evidência de reincidência de problemas já apontados em auditorias anteriores.', 5, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D06', 'Os responsáveis pela área acompanham e cobram a manutenção dos padrões estabelecidos.', 6, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D07', 'As ações corretivas de auditorias anteriores foram tratadas dentro dos prazos definidos.', 7, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D08', 'Os colaboradores demonstram cuidado com o ambiente, equipamentos, materiais e áreas comuns.', 8, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D09', 'O comportamento da equipe contribui para manter a limpeza, organização, segurança e boa imagem da área.', 9, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;

INSERT INTO quality.audit_5s_criteria (senso_id, code, description, sort_order, catalog_version)
SELECT s.id, 'D10', 'A área demonstra evolução em relação ao ciclo anterior do programa 5S.', 10, 1
FROM quality.audit_5s_sensos s WHERE s.sort_order = 5
ON CONFLICT (code, catalog_version) DO NOTHING;

