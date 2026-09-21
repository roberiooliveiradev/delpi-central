import { describe, expect, it } from "vitest";

import {
  conversationAuthorSrc,
  conversationMessages,
  detailRecordHeading,
  isTicketFilterActive,
  nextTicketSort,
  parseTicketListFilters,
  parseTicketSort,
  relativeTimeLabel,
  statusBadgeVariant,
  ticketListSearch,
  ticketRecordFields,
  viewerNameAliasesFromToken,
  viewForTicketLoad,
  writtenByViewer,
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
      ["João Silva"],
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

  it("marca a abertura como minha quando o solicitante é o usuário logado", () => {
    const messages = conversationMessages(
      {
        title: "Chamado teste Api Minha delpi",
        description: "Esse chamado é um teste",
        created_at: "2026-09-21T10:00:00Z",
        requester_display_name: "Robério Teixeira",
        timeline: [],
        attachments: [{ document_id: 2 }],
      },
      now,
      ["Robério Teixeira"],
    );
    expect(messages[0]?.mine).toBe(true);
    expect(conversationAuthorSrc(messages[0].mine, "blob:me")).toBe("blob:me");
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
      ["Robério Teixeira"],
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

  it("marca como minhas as mensagens em que o GLPI só mandou o prenome do usuário logado", () => {
    const messages = conversationMessages(
      {
        title: "Chamado teste Api Minha delpi",
        description: "Esse chamado é um teste",
        created_at: "2026-09-21T10:00:00Z",
        requester_display_name: "Roberio",
        timeline: [
          {
            id: 12,
            kind: "followup",
            content: "olola",
            created_at: "2026-09-21T11:10:00Z",
            author_display_name: "Roberio",
          },
        ],
        attachments: [],
      },
      now,
      ["Robério Oliveira"],
    );
    expect(messages[0]?.mine).toBe(true);
    expect(messages[1]?.mine).toBe(true);
    expect(conversationAuthorSrc(messages[1].mine, "blob:me")).toBe("blob:me");
  });

  it("marca o acompanhamento escrito pelo usuário logado, mesmo quando ele não é o solicitante", () => {
    const messages = conversationMessages(
      {
        title: "Rede",
        description: "Sem internet",
        created_at: "2026-09-21T10:00:00Z",
        requester_display_name: "William Ricardo Jacomini",
        timeline: [
          {
            id: 11,
            kind: "followup",
            content: "Já estou vendo",
            created_at: "2026-09-21T11:00:00Z",
            author_display_name: "João Silva",
          },
        ],
        attachments: [],
      },
      now,
      ["João Silva"],
    );
    expect(messages[0]?.mine).toBe(false);
    expect(messages[1]).toMatchObject({ id: "11", mine: true, authorName: "João Silva" });
  });
});

describe("writtenByViewer", () => {
  it("iguala nome com acento e nome sem acento", () => {
    expect(writtenByViewer("João Silva", ["Joao Silva"])).toBe(true);
  });

  it("reconhece nome completo do GLPI a partir de prenome e sobrenome do JWT", () => {
    expect(writtenByViewer("William Ricardo Jacomini", ["William Jacomini"])).toBe(true);
  });

  it("reconhece o prenome do GLPI quando o JWT tem o nome completo", () => {
    expect(writtenByViewer("Roberio", ["Robério Oliveira"])).toBe(true);
    expect(writtenByViewer("William", ["William Ricardo Jacomini"])).toBe(true);
  });

  it("não trata prenome sozinho do JWT como a mesma pessoa", () => {
    expect(writtenByViewer("William Ricardo Jacomini", ["William"])).toBe(false);
    expect(writtenByViewer("Ana Paula", ["Ana"])).toBe(false);
  });

  it("não junta duas pessoas que só compartilham o prenome", () => {
    expect(writtenByViewer("Robério Teixeira", ["Robério Oliveira"])).toBe(false);
    expect(writtenByViewer("Ana Silva", ["Ana Paula"])).toBe(false);
  });
});

describe("viewerNameAliasesFromToken", () => {
  it("lê o nome completo e o prenome+sobrenome do JWT", () => {
    expect(viewerNameAliasesFromToken(jwtToken({ name: "João Silva", given_name: "João", family_name: "Silva" }))).toEqual([
      "João Silva",
    ]);
    expect(viewerNameAliasesFromToken(jwtToken({ given_name: "William", family_name: "Jacomini" }))).toEqual([
      "William Jacomini",
    ]);
  });

  it("não inventa identidade sem token ou com payload ilegível", () => {
    expect(viewerNameAliasesFromToken(undefined)).toEqual([]);
    expect(viewerNameAliasesFromToken("not-a-jwt")).toEqual([]);
    expect(viewerNameAliasesFromToken(jwtToken({ preferred_username: "denha", email: "denha@delpi.com" }))).toEqual([]);
  });
});

function jwtToken(claims: Record<string, string>): string {
  const json = JSON.stringify(claims);
  const bytes = new TextEncoder().encode(json);
  let binary = "";
  bytes.forEach((byte) => {
    binary += String.fromCharCode(byte);
  });
  const payload = btoa(binary).replace(/=+$/, "").replace(/\+/g, "-").replace(/\//g, "_");
  return `hdr.${payload}.sig`;
}

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

  it("ordena pela coluna no helpdesk e inverte a mesma coluna", () => {
    expect(parseTicketSort("updated_at:desc")).toEqual({ key: "updated_at", direction: "desc" });
    expect(nextTicketSort("updated_at:desc", "updated_at")).toBe("updated_at:asc");
    expect(nextTicketSort("updated_at:desc", "title")).toBe("title:asc");
    expect(nextTicketSort("title:asc", "created_at")).toBe("created_at:desc");
    expect(nextTicketSort("updated_at:desc", "assigned")).toBe("updated_at:desc");
  });
});
