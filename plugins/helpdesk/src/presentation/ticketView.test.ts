import { describe, expect, it } from "vitest";

import {
  absoluteDateTimeLabel,
  conversationAuthorSrc,
  conversationMessages,
  detailRecordHeading,
  detailRecordSubtitle,
  hasVisibleRichText,
  isTicketFilterActive,
  listHelpdeskAttachmentIdsInHtml,
  nextTicketSort,
  parseObserverIdsInput,
  parseTicketListFilters,
  parseTicketSort,
  relativeTimeLabel,
  statusBadgeVariant,
  ticketListSearch,
  ticketRecordFields,
  viewForTicketLoad,
} from "./ticketView";

describe("viewForTicketLoad", () => {
  it("mostra a lista quando há chamados", () => {
    expect(viewForTicketLoad({ loading: false, itemCount: 2 })).toBe("list");
  });

  it("mostra vazio só quando a resposta é uma lista sem itens", () => {
    expect(viewForTicketLoad({ loading: false, itemCount: 0 })).toBe("empty");
  });

  it("não apresenta proibição do helpdesk como lista vazia", () => {
    expect(viewForTicketLoad({ loading: false, errorCode: "glpi_forbidden", itemCount: 0 })).toBe(
      "forbidden",
    );
    expect(viewForTicketLoad({ loading: false, errorCode: "forbidden", itemCount: 0 })).toBe(
      "forbidden",
    );
  });

  it("pede vínculo quando a sessão do helpdesk ainda não existe", () => {
    expect(
      viewForTicketLoad({ loading: false, errorCode: "glpi_link_required", itemCount: 0 }),
    ).toBe("link");
  });
});

describe("statusBadgeVariant", () => {
  it("marca chamado novo e solucionado pelo id", () => {
    expect(statusBadgeVariant(1)).toBe("info");
    expect(statusBadgeVariant(5)).toBe("success");
  });

  it("trata atendimento e aprovação pelo id, sem ler o rótulo", () => {
    expect(statusBadgeVariant(2)).toBe("warning");
    expect(statusBadgeVariant(3)).toBe("warning");
    expect(statusBadgeVariant(10)).toBe("warning");
  });

  it("não promove id desconhecido nem ausência de id", () => {
    expect(statusBadgeVariant(99)).toBe("neutral");
    expect(statusBadgeVariant()).toBe("neutral");
  });
});

describe("ticketRecordFields", () => {
  it("esconde a categoria quando o helpdesk não tem nome", () => {
    const fields = ticketRecordFields({ id: 2, category: "", urgency: "Baixa" });
    expect(fields.find((field) => field.id === "category")?.present).toBe(false);
    expect(fields.find((field) => field.id === "urgency")?.present).toBe(true);
    expect(fields.find((field) => field.id === "id")?.value).toBe("2");
  });

  it("mostra categoria e urgência quando as duas existem", () => {
    const fields = ticketRecordFields({ id: 4, category: "Rede", urgency: "Média" });
    expect(fields.find((field) => field.id === "category")?.present).toBe(true);
    expect(fields.find((field) => field.id === "urgency")?.present).toBe(true);
  });

  it("não mostra urgência vazia", () => {
    const fields = ticketRecordFields({ id: 4, category: "Rede", urgency: " " });
    expect(fields.find((field) => field.id === "urgency")?.present).toBe(false);
    expect(fields.find((field) => field.id === "assigned")?.present).toBe(false);
  });

  it("usa data-hora absoluta e observador só quando existem", () => {
    const fields = ticketRecordFields({
      id: 8,
      category: "Rede",
      urgency: "Alta",
      created_at: "2026-09-21T15:30:00Z",
      updated_at: "2026-09-21T16:00:00Z",
      solved_at: "2026-09-21T17:00:00Z",
      observers_display_name: "Maria Observadora",
    });
    expect(fields.find((field) => field.id === "created_at")?.value).toMatch(/21\/09\/2026/);
    expect(fields.find((field) => field.id === "observers")?.value).toBe("Maria Observadora");
    expect(fields.find((field) => field.id === "closed_at")?.present).toBe(false);
  });
});

describe("detailRecordHeading", () => {
  it("usa a categoria como título quando ela existe", () => {
    expect(detailRecordHeading("Rede", "Baixa")).toEqual({ title: "Rede", subtitle: "Baixa" });
  });

  it("não usa categoria vazia como título do detalhe", () => {
    expect(detailRecordHeading("", "Baixa")).toEqual({ title: "Baixa" });
  });

  it("não inventa categoria quando os dois campos vêm vazios", () => {
    expect(detailRecordHeading(" ", "")).toEqual({ title: "Chamado" });
  });
});

describe("detailRecordSubtitle", () => {
  it("monta #id · urgência · técnico sem partes vazias", () => {
    expect(
      detailRecordSubtitle({
        id: 1120,
        urgency: "Média",
        assigned_display_name: "Ana",
      }),
    ).toBe("#1120 · Média · Ana");
    expect(detailRecordSubtitle({ id: 3, urgency: "", assigned_display_name: "  " })).toBe("#3");
    expect(detailRecordSubtitle({ id: 0, urgency: "Alta" })).toBe("Alta");
  });
});

describe("conversationMessages", () => {
  const now = new Date("2026-09-21T12:00:00Z");

  it("não marca a abertura como minha só porque o chamado tem solicitante", () => {
    const messages = conversationMessages(
      {
        title: "Renovação da assinatura do DraftSight",
        description: "Peço a renovação",
        created_at: "2026-09-21T10:00:00Z",
        requester_display_name: "William Ricardo Jacomini",
        timeline: [],
        attachments: [{ document_id: 2 }, { document_id: 4 }],
      },
      now,
    );
    expect(messages[0]).toMatchObject({
      id: "opening",
      kind: "opening",
      headingText: "Renovação da assinatura do DraftSight",
      bodyText: "Peço a renovação",
      createdAtLabel: "Criado em 2 horas atrás",
      authorName: "William Ricardo Jacomini",
      mine: false,
      attachmentIds: [2, 4],
    });
    expect(conversationAuthorSrc(messages[0].mine, "blob:me")).toBeUndefined();
  });

  it("marca a abertura como minha só quando o BFF identifica o solicitante pelo id ou e-mail", () => {
    const messages = conversationMessages(
      {
        title: "Chamado teste Api Minha delpi",
        description: "Esse chamado é um teste",
        created_at: "2026-09-21T10:00:00Z",
        requester_display_name: "Roberio",
        requester_mine: true,
        timeline: [],
        attachments: [{ document_id: 2 }],
      },
      now,
    );
    expect(messages[0]?.mine).toBe(true);
    expect(conversationAuthorSrc(messages[0].mine, "blob:me")).toBe("blob:me");
  });

  it("carimba data-attachment-id no HTML sanitizado do BFF", () => {
    const messages = conversationMessages(
      {
        title: "Foto",
        description: "placa",
        description_html:
          '<p><img src="/apps/helpdesk-api/tickets/1108/attachments/391" alt="placa" /></p>',
        created_at: "2026-09-21T10:00:00Z",
        requester_display_name: "Ana",
        timeline: [
          {
            id: 12,
            kind: "followup",
            content: "mesma",
            content_html:
              '<p><img src="/apps/helpdesk-api/tickets/1108/attachments/391" alt="mesma" /></p>',
            created_at: "2026-09-21T11:00:00Z",
            author_display_name: "Ana",
            mine: false,
          },
        ],
        attachments: [{ document_id: 391 }],
      },
      now,
    );
    expect(messages[0].bodyHtml).toContain('data-attachment-id="391"');
    expect(listHelpdeskAttachmentIdsInHtml(messages[0].bodyHtml)).toEqual([391]);
    expect(messages[1].bodyHtml).toContain('data-attachment-id="391"');
    expect(messages[1].attachmentIds).toEqual([]);
  });

  it("escreve a data calendário quando o chamado é antigo", () => {
    const messages = conversationMessages(
      {
        title: "Monitor falhando",
        description: "Tela piscando",
        created_at: "2026-02-19T10:00:00Z",
        requester_display_name: "Robério Teixeira",
        timeline: [],
        attachments: [],
      },
      now,
    );
    expect(messages[0].createdAtLabel).toBe("Criado em 19/02/2026");
  });

  it("só usa a foto da Minha DELPI na mensagem do próprio usuário", () => {
    expect(conversationAuthorSrc(true, "blob:me")).toBe("blob:me");
    expect(conversationAuthorSrc(false, "blob:me")).toBeUndefined();
    expect(conversationAuthorSrc(true, "  ")).toBeUndefined();
  });

  it("mostra o acompanhamento de outra pessoa do outro lado, sem anexo", () => {
    const messages = conversationMessages(
      {
        title: "Rede",
        description: "Sem internet",
        created_at: "2026-09-21T10:00:00Z",
        requester_display_name: "Robério Teixeira",
        timeline: [
          {
            id: 9,
            kind: "followup",
            content: "Cabo ok",
            created_at: "2026-09-21T11:00:00Z",
            author_display_name: "Ana",
          },
        ],
        attachments: [{ document_id: 2 }],
      },
      now,
    );
    expect(messages[1]).toMatchObject({
      id: "9",
      kind: "followup",
      authorName: "Ana",
      mine: false,
      bodyText: "Cabo ok",
      createdAtLabel: "1 hora atrás",
      attachmentIds: [],
    });
    expect(messages[0]?.attachmentIds).toEqual([2]);
  });

  it("não marca ninguém como meu quando o solicitante vem vazio e ignora tarefa", () => {
    const messages = conversationMessages(
      {
        title: "Rede",
        description: "Sem internet",
        created_at: "",
        requester_display_name: " ",
        timeline: [
          {
            id: 3,
            kind: "task",
            content: "interno",
            created_at: "2026-09-21T11:00:00Z",
            author_display_name: "Técnico",
          },
        ],
        attachments: [],
      },
      now,
    );
    expect(messages).toHaveLength(1);
    expect(messages[0]?.mine).toBe(false);
    expect(messages[0]?.createdAtLabel).toBe("");
    expect(messages.some((message) => message.kind === "followup" && message.bodyText === "interno")).toBe(
      false,
    );
    expect(messages.map((message) => message.kind)).not.toContain("task");
  });

  it("mostra a solução da timeline com título Solução e ignora validation", () => {
    const messages = conversationMessages(
      {
        title: "VPN",
        description: "Sem acesso",
        created_at: "2026-09-21T10:00:00Z",
        requester_display_name: "Ana",
        requester_mine: true,
        timeline: [
          {
            id: 10,
            kind: "followup",
            content: "Reinicie o cliente",
            created_at: "2026-09-21T11:00:00Z",
            author_display_name: "Técnico",
          },
          {
            id: 11,
            kind: "solution",
            content: "Cliente reiniciado; VPN ok.",
            content_html: "<p>Cliente reiniciado; VPN ok.</p>",
            created_at: "2026-09-21T12:00:00Z",
            author_display_name: "Técnico",
          },
          {
            id: 12,
            kind: "validation",
            content: "pedido interno",
            created_at: "2026-09-21T12:05:00Z",
            author_display_name: "Chefe",
          },
        ],
        attachments: [],
      },
      now,
    );
    expect(messages.map((message) => message.kind)).toEqual(["opening", "followup", "solution"]);
    expect(messages[2]?.headingText).toBe("Solução");
    expect(messages[2]?.bodyText).toBe("Cliente reiniciado; VPN ok.");
    expect(messages.some((message) => message.bodyText === "pedido interno")).toBe(false);
  });

  it("não usa o nome do autor para decidir o lado da bolha", () => {
    const messages = conversationMessages(
      {
        title: "Chamado teste Api Minha delpi",
        description: "Esse chamado é um teste",
        created_at: "2026-09-21T10:00:00Z",
        requester_display_name: "Roberio",
        requester_mine: false,
        timeline: [
          {
            id: 12,
            kind: "followup",
            content: "olola",
            created_at: "2026-09-21T11:10:00Z",
            author_display_name: "Roberio",
            mine: true,
          },
        ],
        attachments: [],
      },
      now,
    );
    expect(messages[0]?.mine).toBe(false);
    expect(messages[1]?.mine).toBe(true);
    expect(conversationAuthorSrc(messages[1].mine, "blob:me")).toBe("blob:me");
  });
});

describe("relativeTimeLabel", () => {
  const now = new Date("2026-09-21T12:00:00Z");

  it("usa o calendário a partir de sete dias", () => {
    const label = relativeTimeLabel("2026-09-14T12:00:00Z", now);
    const date = new Date("2026-09-14T12:00:00Z");
    const expected = `${String(date.getDate()).padStart(2, "0")}/${String(date.getMonth() + 1).padStart(2, "0")}/${date.getFullYear()}`;
    expect(label).toBe(expected);
    expect(label).not.toBe("7 dias atrás");
  });

  it("não inventa tempo para uma data ilegível", () => {
    expect(relativeTimeLabel("não é data", now)).toBe("");
  });
});

describe("absoluteDateTimeLabel", () => {
  it("mostra dia e hora do instante", () => {
    const label = absoluteDateTimeLabel("2026-09-21T15:30:00Z");
    const date = new Date("2026-09-21T15:30:00Z");
    const expected = `${String(date.getDate()).padStart(2, "0")}/${String(date.getMonth() + 1).padStart(2, "0")}/${date.getFullYear()} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
    expect(label).toBe(expected);
  });

  it("não inventa rótulo para data ilegível", () => {
    expect(absoluteDateTimeLabel("")).toBe("");
    expect(absoluteDateTimeLabel("ontem")).toBe("");
  });
});

describe("ticket list filters", () => {
  it("guarda o recorte na URL e detecta filtro ativo", () => {
    const search = ticketListSearch({
      q: "Monitor falhando",
      status: "in_progress",
      urgency_id: "3",
      category_id: "",
      assignee_id: "",
      updated_from: "",
      updated_to: "",
      created_from: "2026-01-01",
      created_to: "2026-01-31",
      sort: "updated_at:desc",
      page: 1,
      page_size: 10,
    });
    expect(search).toContain("q=Monitor");
    expect(search).toContain("status=in_progress");
    expect(search).toContain("created_from=2026-01-01");
    expect(search).toContain("created_to=2026-01-31");
    expect(search).toContain("page_size=10");
    const parsed = parseTicketListFilters(search);
    expect(parsed.created_from).toBe("2026-01-01");
    expect(parsed.page_size).toBe(10);
    expect(isTicketFilterActive(parsed)).toBe(true);
    expect(isTicketFilterActive(parseTicketListFilters(""))).toBe(false);
  });

  it("não trata página sozinha como recorte", () => {
    expect(isTicketFilterActive(parseTicketListFilters("?page=2&sort=title:asc"))).toBe(false);
  });

  it("ignora page_size fora de 10/20/50", () => {
    expect(parseTicketListFilters("?page_size=15").page_size).toBe(20);
    expect(parseTicketListFilters("?page_size=50").page_size).toBe(50);
  });

  it("ordena pela coluna no helpdesk e inverte a mesma coluna", () => {
    expect(parseTicketSort("updated_at:desc")).toEqual({ key: "updated_at", direction: "desc" });
    expect(parseTicketSort("updated_at:desc,title:asc")).toEqual({
      key: "updated_at",
      direction: "desc",
    });
    expect(nextTicketSort("updated_at:desc", "updated_at")).toBe("updated_at:asc");
    expect(nextTicketSort("updated_at:desc", "title")).toBe("title:asc");
    expect(nextTicketSort("title:asc", "created_at")).toBe("created_at:desc");
    expect(nextTicketSort("updated_at:desc", "solved_at")).toBe("solved_at:desc");
    expect(nextTicketSort("updated_at:desc", "closed_at")).toBe("closed_at:desc");
    expect(nextTicketSort("updated_at:desc", "assigned")).toBe("assigned:asc");
  });
});

describe("hasVisibleRichText", () => {
  it("aceita HTML com texto e rejeita vazio ou só tags", () => {
    expect(hasVisibleRichText("<p><strong>ok</strong></p>")).toBe(true);
    expect(hasVisibleRichText("texto puro")).toBe(true);
    expect(hasVisibleRichText("<p></p>")).toBe(false);
    expect(hasVisibleRichText("<p><br></p>")).toBe(false);
    expect(hasVisibleRichText("")).toBe(false);
  });
});

describe("parseObserverIdsInput", () => {
  it("lê ids positivos únicos e ignora lixo", () => {
    expect(parseObserverIdsInput("15, 15;22 abc -3")).toEqual([15, 22]);
    expect(parseObserverIdsInput("")).toEqual([]);
  });
});
