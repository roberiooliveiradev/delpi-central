import type { PublicNewsBoard } from "./types";

/** Fixture da prova visual — espelha itens `published` do contrato futuro. */
export const MOCK_PUBLIC_NEWS_BOARD: PublicNewsBoard = {
  board_id: "board-demo-delpi-news",
  title: "DELPI News",
  subtitle: "Notícias selecionadas para as TVs corporativas",
  rotation_interval_sec: 12,
  items: [
    {
      id: "item-001",
      title: "DELPI amplia capacidade produtiva com novo centro de usinagem",
      summary:
        "Investimento reforça a linha de chicotes e reduz lead time para clientes da indústria automotiva e de máquinas.",
      canonical_url: "https://example.com/delpi/capacidade-usinagem",
      image_url: null,
      category_name: "Empresa",
      source_name: "Comunicação DELPI",
      published_at: "2026-10-20T11:00:00-03:00",
      is_featured: true,
    },
    {
      id: "item-002",
      title: "Indústria brasileira registra avanço na produção de transformadores",
      summary:
        "Dados setoriais apontam crescimento da demanda por equipamentos de média tensão e maior foco em eficiência energética.",
      canonical_url: "https://example.com/setor/transformadores",
      image_url: null,
      category_name: "Mercado",
      source_name: "Agência Setorial",
      published_at: "2026-10-19T08:30:00-03:00",
      is_featured: false,
    },
    {
      id: "item-003",
      title: "Segurança no trabalho: campanha reforça uso correto de EPIs",
      summary:
        "Ações de conscientização nas plantas SC e ES destacam inspeções de rotina e reporte de quase-acidentes.",
      canonical_url: "https://example.com/delpi/campanha-epi",
      image_url: null,
      category_name: "Pessoas",
      source_name: "SESMT DELPI",
      published_at: "2026-10-18T15:45:00-03:00",
      is_featured: false,
    },
    {
      id: "item-004",
      title: "Tecnologia: automação industrial acelera digitalização das fábricas",
      summary:
        "Sensores, MES e dashboards em tempo real passam a integrar a rotina de centros de trabalho e planejamento.",
      canonical_url: "https://example.com/tech/automacao-mes",
      image_url: null,
      category_name: "Tecnologia",
      source_name: "Radar Indústria 4.0",
      published_at: "2026-10-17T09:10:00-03:00",
      is_featured: true,
    },
    {
      id: "item-005",
      title: "Exportações de componentes elétricos mantêm ritmo no trimestre",
      summary:
        "Análise de comércio exterior mostra estabilidade nos embarques para América Latina e novos pedidos na Europa.",
      canonical_url: "https://example.com/comercio/exportacoes-eletricos",
      image_url: null,
      category_name: "Mercado",
      source_name: "Boletim Comércio Exterior",
      published_at: "2026-10-16T07:00:00-03:00",
      is_featured: false,
    },
  ],
};
