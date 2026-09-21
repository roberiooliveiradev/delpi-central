import { describe, expect, it } from "vitest";

import { viewForTicketLoad, statusBadgeVariant } from "./ticketView";

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
