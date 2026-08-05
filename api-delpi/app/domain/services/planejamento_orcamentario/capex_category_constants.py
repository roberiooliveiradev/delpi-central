"""Constantes — catálogo de categorias CAPEX (Fase 2A.3).

Não confundir com contas contábeis do ERP: aqui são categorias de investimento
administráveis no módulo de planejamento orçamentário.
"""

from __future__ import annotations

# Seed canônico (espelha V003). Usado em testes de regressão / documentação.
DEFAULT_CAPEX_CATEGORIES: tuple[tuple[str, str, int], ...] = (
    ("COMPUTADORES_PERIFERICOS", "Computadores e Periféricos", 10),
    ("FERRAMENTAS", "Ferramentas", 20),
    ("INSTALACOES", "Instalações", 30),
    ("INSTRUMENTOS_TESTE_CONTROLE", "Instrumentos de Teste e Controle", 40),
    ("MAQUINAS_EQUIPAMENTOS_INDUSTRIAIS", "Máquinas e Equipamentos Industriais", 50),
    ("MOVEIS_UTENSILIOS", "Móveis e Utensílios", 60),
    ("OBRAS_CONSTRUCAO_CIVIL", "Obras e Construção Civil", 70),
    ("SOFTWARES_LICENCAS_SISTEMAS", "Softwares, Licenças e Sistemas", 80),
    ("VEICULOS", "Veículos", 90),
    ("GABARITOS_DISPOSITIVOS_BANCADAS", "Gabaritos, Dispositivos e Bancadas", 100),
    ("EQUIPAMENTOS_CORTE_DOCAPE", "Equipamentos de Corte e Docape", 110),
    ("EQUIPAMENTOS_CRIMPAGEM", "Equipamentos de Crimpagem", 120),
    ("EQUIPAMENTOS_TESTE_ELETRICO", "Equipamentos de Teste Elétrico", 130),
    ("AUTOMACAO_INDUSTRIAL_ROBOTICA", "Automação Industrial e Robótica", 140),
    ("METROLOGIA_CALIBRACAO", "Metrologia e Calibração", 150),
    ("LABORATORIO_CONTROLE_QUALIDADE", "Laboratório e Controle da Qualidade", 160),
    ("MOVIMENTACAO_ARMAZENAGEM", "Movimentação e Armazenagem de Materiais", 170),
    ("SEGURANCA_ERGONOMIA_MEIO_AMBIENTE", "Segurança, Ergonomia e Meio Ambiente", 180),
    ("INFRAESTRUTURA_ELETRICA_UTILIDADES", "Infraestrutura Elétrica e Utilidades", 190),
    ("EFICIENCIA_ENERGETICA_SUSTENTABILIDADE", "Eficiência Energética e Sustentabilidade", 200),
    ("TELECOMUNICACOES_INFRA_TI", "Telecomunicações e Infraestrutura de TI", 210),
    ("EQUIPAMENTOS_MANUTENCAO", "Equipamentos de Manutenção", 220),
    ("EQUIPAMENTOS_LOGISTICA_INTERNA", "Equipamentos de Logística Interna", 230),
    ("CLIMATIZACAO_VENTILACAO_INDUSTRIAL", "Climatização e Ventilação Industrial", 240),
)

ENTITY_TYPE_CAPEX_CATEGORY = "capex_category"
