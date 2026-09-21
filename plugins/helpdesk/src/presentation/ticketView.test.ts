import { describe, expect, it } from "vitest";

import { detailRecordHeading, statusBadgeVariant, ticketRecordFields, viewForTicketLoad } from "./ticketView";

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
    const fields = ticketRecordFields("", "Baixa");
    expect(fields.find((field) => field.id === "category")?.present).toBe(false);
    expect(fields.find((field) => field.id === "urgency")?.present).toBe(true);
  });

  it("mostra categoria e urgência quando as duas existem", () => {
    const fields = ticketRecordFields("Rede", "Média");
    expect(fields.every((field) => field.present)).toBe(true);
  });

  it("não mostra urgência vazia", () => {
    const fields = ticketRecordFields("Rede", " ");
    expect(fields.find((field) => field.id === "urgency")?.present).toBe(false);
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
