import type { PublicNewsBoard } from "./types";

function demoCoverUrl(): string {
  const base = import.meta.env.BASE_URL || "/";
  return `${base.endsWith("/") ? base : `${base}/`}delpi-news/demo-cover.svg`;
}

const DEMO_COVER = demoCoverUrl();

/**
 * Fixture da prova visual — textos neutros e explicitamente fictícios.
 * Não representa operações, investimentos ou campanhas reais da DELPI.
 */
export const MOCK_PUBLIC_NEWS_BOARD: PublicNewsBoard = {
  board_id: "board-demo-delpi-news",
  title: "DELPI News — Demonstração",
  subtitle: "Prova visual de layout para TVs. Conteúdo fictício; não é canal editorial.",
  is_demo: true,
  rotation_interval_sec: 8,
  items: [
    {
      id: "item-001",
      title: "Exemplo A — manchete curta com imagem de demonstração",
      summary:
        "Texto fictício usado apenas para validar tipografia, contraste e área de imagem no kiosk.",
      canonical_url: null,
      image_url: DEMO_COVER,
      category_name: "Demo",
      source_name: "Fonte de exemplo",
      published_at: "2026-10-20T11:00:00-03:00",
      is_featured: true,
    },
    {
      id: "item-002",
      title: "Exemplo B — manchete sem imagem para testar o estado alternativo do palco",
      summary:
        "Quando não há imagem autorizada, o layout deve permanecer legível e estável em 16:9.",
      canonical_url: null,
      image_url: null,
      category_name: "Demo",
      source_name: "Fonte de exemplo",
      published_at: "2026-10-19T08:30:00-03:00",
      is_featured: false,
    },
    {
      id: "item-003",
      title:
        "Exemplo C — manchete propositalmente longa para validar truncamento e proteção contra overflow em telas de TV corporativa com proporção dezesseis por nove e tipografia ampliada",
      summary:
        "Resumo também alongado de propósito: o componente deve limitar linhas e evitar rolagem indesejada no Adeus Pendrive, mantendo hierarquia visual entre título, resumo e metadados sem invadir a área de navegação lateral.",
      canonical_url: null,
      image_url: null,
      category_name: null,
      source_name: "Fonte de exemplo",
      published_at: null,
      is_featured: false,
    },
    {
      id: "item-004",
      title: "Exemplo D — item com categoria e data para a faixa «A seguir»",
      summary: "Conteúdo neutro de demonstração para a lista lateral de próximas manchetes.",
      canonical_url: null,
      image_url: DEMO_COVER,
      category_name: "Layout",
      source_name: "Fonte de exemplo",
      published_at: "2026-10-17T09:10:00-03:00",
      is_featured: true,
    },
  ],
};
