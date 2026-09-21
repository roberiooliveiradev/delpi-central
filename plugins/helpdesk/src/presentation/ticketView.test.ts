import { describe, expect, it } from "vitest";

import {
  conversationMessages,
  detailRecordHeading,
  isTicketFilterActive,
  parseTicketListFilters,
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
  it("marca chamado novo e solucionado com tons diferentes", () => {
    expect(statusBadgeVariant("Novo")).toBe("info");
    expect(statusBadgeVariant("Solucionado")).toBe("success");
  });

  it("trata atendimento atribuído como o mesmo tom de em andamento", () => {
    expect(statusBadgeVariant("Em atendimento (atribuído)")).toBe("warning");
  });

  it("não promove status desconhecido", () => {
    expect(statusBadgeVariant("Aguardando peça")).toBe("neutral");
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

describe("conversationMessages", () => {
  const now = new Date("2026-09-21T12:00:00Z");

  it("abre com o solicitante, o título e o tempo relativo", () => {
    const messages = conversationMessages(
      {
        title: "Chamado teste Api Minha delpi",
        description: "Esse chamado é um teste",
        created_at: "2026-09-21T10:00:00Z",
        requester_display_name: "Robério Teixeira",
        timeline: [],
        attachments: [{ document_id: 2 }, { document_id: 4 }],
      },
      now,
    );
    expect(messages[0]).toMatchObject({
      id: "opening",
      kind: "opening",
      headingText: "Chamado teste Api Minha delpi",
      bodyText: "Esse chamado é um teste",
      createdAtLabel: "Criado em 2 horas atrás",
      authorName: "Robério Teixeira",
      mine: true,
      attachmentIds: [2, 4],
    });
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

describe("ticket list filters", () => {
  it("guarda o recorte na URL e detecta filtro ativo", () => {
    const search = ticketListSearch({
      q: "Monitor falhando",
      status: "in_progress",
      urgency_id: "3",
      category_id: "",
      updated_from: "",
      updated_to: "",
      sort: "updated_at:desc",
      page: 1,
    });
    expect(search).toContain("q=Monitor");
    expect(search).toContain("status=in_progress");
    expect(isTicketFilterActive(parseTicketListFilters(search))).toBe(true);
    expect(isTicketFilterActive(parseTicketListFilters(""))).toBe(false);
  });

  it("não trata página sozinha como recorte", () => {
    expect(isTicketFilterActive(parseTicketListFilters("?page=2&sort=title:asc"))).toBe(false);
  });
});
