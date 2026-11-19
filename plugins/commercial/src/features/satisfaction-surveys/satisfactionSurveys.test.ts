import { describe, expect, it } from "vitest";

import { resolveHubSections, type HubCapabilities } from "../../content/pluginRouteCatalog";
import {
  buildPluginPath,
  buildSatisfactionCampaignDetailPath,
  buildSatisfactionRecipientDetailPath,
  resolveActiveNavId,
  resolvePluginRoute,
} from "../../app/pluginRoutes";
import type {
  SatisfactionAddRecipientsResult,
  SatisfactionCampaign,
  SatisfactionRecipient,
} from "../../types/satisfactionSurvey";
import { describeAddRecipientsResult } from "./addRecipientsResult";
import { validateCampaignForm } from "./campaignForm";
import {
  buildInviteHtml,
  escapeHtml,
  insertTokenAtSelection,
  INVITE_COMPANY_TOKEN,
  INVITE_LINK_TOKEN,
  missingInvitePlaceholders,
  replaceInvitePlaceholders,
  unknownInvitePlaceholders,
} from "./inviteMessage";
import { absolutizeInvite } from "./inviteLink";
import {
  formatSurveyUpdatedAt,
  isoToLocalInput,
  localInputToIso,
  surveyYearOf,
} from "./satisfactionDates";
import { SATISFACTION_CONTENT } from "../../content/satisfactionSurveysContent";
import { resolveCanManageSatisfaction } from "./satisfactionAccess";
import {
  campaignYearOptions,
  EMPTY_CAMPAIGN_FILTERS,
  filterCampaigns,
  filterRecipients,
  hasActiveCampaignFilters,
  recipientKeys,
} from "./satisfactionFilters";
import {
  EMPTY_CAMPAIGN_SORT,
  isCampaignSortKey,
  nextCampaignSortState,
  sortCampaigns,
} from "./satisfactionSort";

const BASE = "/apps/commercial";

function campaign(overrides: Partial<SatisfactionCampaign>): SatisfactionCampaign {
  return {
    id: "c1",
    name: "Pesquisa 2026",
    starts_at: "2026-03-01T03:00:00Z",
    ends_at: "2026-03-31T02:59:00Z",
    status: "open",
    questionnaire_version: "v1",
    invite_subject: "",
    invite_body: "",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    version: 1,
    counts: { participants: 0, responded: 0, pending: 0 },
    response_rate: null,
    ...overrides,
  };
}

function recipient(overrides: Partial<SatisfactionRecipient>): SatisfactionRecipient {
  return {
    id: "r1",
    campaign_id: "c1",
    customer_code: "000123",
    customer_store: "1",
    customer_name: "Cliente Alfa",
    contact_name: null,
    contact_email: null,
    status: "pending",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    version: 1,
    ...overrides,
  };
}

describe("rotas da Pesquisa de Satisfação", () => {
  it("resolve lista, detalhe da campanha e detalhe do participante", () => {
    expect(resolvePluginRoute(`${BASE}/satisfaction-surveys`, BASE).view).toBe("satisfaction_surveys");
    const detail = resolvePluginRoute(`${BASE}/satisfaction-surveys/camp-1`, BASE);
    expect(detail.view).toBe("satisfaction_campaign_detail");
    expect(detail.campaignId).toBe("camp-1");
    const rec = resolvePluginRoute(`${BASE}/satisfaction-surveys/camp-1/recipients/rec-9`, BASE);
    expect(rec.view).toBe("satisfaction_recipient_detail");
    expect(rec.campaignId).toBe("camp-1");
    expect(rec.recipientId).toBe("rec-9");
  });

  it("round-trip de build/resolve preserva ids com caracteres especiais", () => {
    const path = buildSatisfactionRecipientDetailPath(BASE, "a b", "c/d");
    expect(path).not.toBeNull();
    const route = resolvePluginRoute(path ?? "", BASE);
    expect(route.view).toBe("satisfaction_recipient_detail");
    expect(route.campaignId).toBe("a b");
    expect(route.recipientId).toBe("c/d");
  });

  it("caso negativo: ids vazios não geram path e rotas irmãs não colidem", () => {
    expect(buildSatisfactionCampaignDetailPath(BASE, "  ")).toBeNull();
    expect(buildSatisfactionRecipientDetailPath(BASE, "c1", "")).toBeNull();
    expect(resolvePluginRoute(`${BASE}/open-orders`, BASE).view).toBe("open_orders");
    expect(resolvePluginRoute(`${BASE}/satisfaction-surveys/c1/other`, BASE).view).toBe("not_found");
  });

  it("buildPluginPath da lista e item de navegação neutro", () => {
    expect(buildPluginPath("satisfaction_surveys", BASE)).toBe(`${BASE}/satisfaction-surveys`);
    expect(resolveActiveNavId("satisfaction_surveys")).toBeNull();
    expect(resolveActiveNavId("satisfaction_campaign_detail")).toBeNull();
  });
});

describe("acesso e caminho no hub", () => {
  const caps: HubCapabilities = {
    analytics: false,
    worklist: false,
    proposals: false,
    customers: false,
    satisfaction: false,
    admin: false,
  };

  it("seção Marketing só aparece com a capability satisfaction", () => {
    expect(resolveHubSections(caps).some((s) => s.id === "marketing")).toBe(false);
    const visible = resolveHubSections({ ...caps, satisfaction: true });
    const section = visible.find((s) => s.id === "marketing");
    expect(section?.routes[0]?.viewId).toBe("satisfaction_surveys");
  });

  it("resolveCanManageSatisfaction aceita satisfaction_manage, marketing ou manage", () => {
    expect(resolveCanManageSatisfaction({ manage: false })).toBe(false);
    expect(resolveCanManageSatisfaction({ manage: false, marketing: true })).toBe(true);
    expect(resolveCanManageSatisfaction({ manage: false, satisfaction_manage: true })).toBe(true);
    expect(resolveCanManageSatisfaction({ manage: true })).toBe(true);
  });
});

describe("datas no fuso do Portal", () => {
  it("converte datetime-local (UTC-03) para ISO UTC e volta", () => {
    expect(localInputToIso("2026-03-01T00:00")).toBe("2026-03-01T03:00:00.000Z");
    expect(isoToLocalInput("2026-03-01T03:00:00Z")).toBe("2026-03-01T00:00");
  });

  it("rejeita entradas inválidas e usa o ano do Portal (virada de ano)", () => {
    expect(localInputToIso("")).toBeNull();
    expect(localInputToIso("2026-13-40T99:99")).toBeNull();
    expect(isoToLocalInput(null)).toBe("");
    // 2027-01-01T01:00Z ainda é 31/12/2026 em São Paulo.
    expect(surveyYearOf("2027-01-01T01:00:00Z")).toBe(2026);
  });
});

describe("validateCampaignForm", () => {
  it("aceita dados válidos e normaliza o nome", () => {
    const result = validateCampaignForm({
      name: "  Campanha  ",
      startsAtLocal: "2026-03-01T08:00",
      endsAtLocal: "2026-03-31T18:00",
    });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.values.name).toBe("Campanha");
      expect(result.values.startsAtIso).toBe("2026-03-01T11:00:00.000Z");
    }
  });

  it("rejeita nome vazio, datas ausentes e início >= término", () => {
    expect(validateCampaignForm({ name: " ", startsAtLocal: "2026-03-01T08:00", endsAtLocal: "2026-03-02T08:00" }).ok).toBe(false);
    expect(validateCampaignForm({ name: "x", startsAtLocal: "", endsAtLocal: "2026-03-02T08:00" }).ok).toBe(false);
    expect(validateCampaignForm({ name: "x", startsAtLocal: "2026-03-02T08:00", endsAtLocal: "2026-03-02T08:00" }).ok).toBe(false);
  });
});

describe("mensagem do convite", () => {
  it("escapa HTML digitado pelo usuário (anti-XSS) e não cria link com javascript:", () => {
    const html = buildInviteHtml('<img src=x onerror=alert(1)> javascript:alert(1) "oi"', { linkify: true });
    expect(html).not.toContain("<img");
    expect(html).toContain("&lt;img");
    expect(html).not.toMatch(/<a /);
    expect(escapeHtml("<&>\"'")).toBe("&lt;&amp;&gt;&quot;&#39;");
  });

  it("linkifica apenas http(s) e preserva pontuação final fora do link", () => {
    const html = buildInviteHtml("Acesse https://exemplo.com/p/abc.", { linkify: true });
    expect(html).toContain('<a href="https://exemplo.com/p/abc" target="_blank" rel="noopener noreferrer">');
    expect(html).toContain("</a>.");
    expect(buildInviteHtml("https://exemplo.invalid/x", { linkify: false })).not.toMatch(/<a /);
  });

  it("parágrafos e quebras simples", () => {
    expect(buildInviteHtml("a\nb\n\nc")).toBe("<p>a<br>b</p><p>c</p>");
  });

  it("substitui e detecta placeholders ausentes; insere token na seleção", () => {
    const template = `Olá ${INVITE_COMPANY_TOKEN}, responda: ${INVITE_LINK_TOKEN}`;
    expect(replaceInvitePlaceholders(template, { company: "Alfa", link: "https://x/y" })).toBe(
      "Olá Alfa, responda: https://x/y",
    );
    expect(missingInvitePlaceholders("sem campos")).toEqual([INVITE_COMPANY_TOKEN, INVITE_LINK_TOKEN]);
    expect(missingInvitePlaceholders(template)).toEqual([]);
    expect(unknownInvitePlaceholders("Olá {nome_empresa} e {foo}")).toEqual(["{foo}"]);
    expect(unknownInvitePlaceholders(template)).toEqual([]);
    const inserted = insertTokenAtSelection("abcd", "{x}", 1, 3);
    expect(inserted).toEqual({ text: "a{x}d", cursor: 4 });
    expect(insertTokenAtSelection("ab", "{x}", null, null).text).toBe("ab{x}");
  });

  it("absolutiza link relativo no corpo e no link; mantém link absoluto intacto", () => {
    const relative = { subject: "s", body: "Veja /p/commercial/form/tok", link_url: "/p/commercial/form/tok" };
    const result = absolutizeInvite(relative, "https://portal.delpi.com/");
    expect(result.link_url).toBe("https://portal.delpi.com/p/commercial/form/tok");
    expect(result.body).toBe("Veja https://portal.delpi.com/p/commercial/form/tok");
    const absolute = { subject: "s", body: "b", link_url: "https://x.com/p/t" };
    expect(absolutizeInvite(absolute, "https://portal.delpi.com")).toBe(absolute);
    expect(absolutizeInvite({ ...relative, link_url: "//evil.com/x" }, "https://portal.delpi.com").link_url).toBe("//evil.com/x");
  });
});

describe("filtros de apresentação", () => {
  const list = [
    campaign({ id: "a", name: "Pesquisa Verão", starts_at: "2026-02-01T03:00:00Z", status: "closed" }),
    campaign({ id: "b", name: "Satisfação Inverno", starts_at: "2025-07-01T03:00:00Z", status: "open" }),
  ];

  it("filtra por ano, situação (da API) e busca sem acento, ordenando por início desc", () => {
    expect(campaignYearOptions(list)).toEqual(["2026", "2025"]);
    expect(filterCampaigns(list, EMPTY_CAMPAIGN_FILTERS).map((c) => c.id)).toEqual(["a", "b"]);
    expect(filterCampaigns(list, { year: "2025", status: "", search: "" }).map((c) => c.id)).toEqual(["b"]);
    expect(filterCampaigns(list, { year: "", status: "closed", search: "" }).map((c) => c.id)).toEqual(["a"]);
    expect(filterCampaigns(list, { year: "", status: "", search: "satisfacao" }).map((c) => c.id)).toEqual(["b"]);
    expect(hasActiveCampaignFilters(EMPTY_CAMPAIGN_FILTERS)).toBe(false);
    expect(hasActiveCampaignFilters({ year: "", status: "", search: " x " })).toBe(true);
  });

  it("filtra participantes e gera chaves canônicas para excluir do seletor", () => {
    const items = [
      recipient({ id: "1" }),
      recipient({ id: "2", customer_code: "000999", customer_name: "Beta", status: "responded", contact_email: "ana@beta.com" }),
    ];
    expect(filterRecipients(items, { status: "responded", search: "" }).map((r) => r.id)).toEqual(["2"]);
    expect(filterRecipients(items, { status: "", search: "ANA@BETA" }).map((r) => r.id)).toEqual(["2"]);
    // loja "1" é normalizada para "01" pelo customerKey canônico do picker.
    expect(recipientKeys(items).has("000123|01")).toBe(true);
  });
});

describe("resultado parcial da inclusão em lote", () => {
  const base: SatisfactionAddRecipientsResult = {
    campaign_id: "c1",
    included: [],
    already_existing: [],
    failed: [],
    counts: { included: 0, already_existing: 0, failed: 0 },
  };

  it("separa incluídas, preservadas e falhas por item", () => {
    const feedback = describeAddRecipientsResult({
      ...base,
      counts: { included: 2, already_existing: 1, failed: 1 },
      failed: [{ customer_code: "9", customer_store: "01", reason: "blocked", message: "Cliente bloqueado" }],
    });
    expect(feedback.success).toBe("2 empresas incluídas.");
    expect(feedback.info).toContain("1 empresa já estava");
    expect(feedback.failures).toEqual(["9/01: Cliente bloqueado"]);
  });

  it("nada incluído gera feedback vazio (a tela avisa separadamente)", () => {
    expect(describeAddRecipientsResult(base)).toEqual({ success: null, info: null, failures: [] });
  });
});

describe("ordenação da lista de campanhas (UI-02 P2)", () => {
  const a = campaign({ id: "a", name: "Água viva", starts_at: "2026-01-10T03:00:00Z", status: "scheduled", counts: { participants: 5, responded: 1, pending: 4 }, response_rate: 20 });
  const b = campaign({ id: "b", name: "banana", starts_at: "2026-02-10T03:00:00Z", status: "open", counts: { participants: 30, responded: 20, pending: 10 }, response_rate: null });
  const c = campaign({ id: "c", name: "campanha 10", starts_at: "2026-03-10T03:00:00Z", status: "closed", counts: { participants: 8, responded: 8, pending: 0 }, response_rate: 100 });
  const d = campaign({ id: "d", name: "campanha 2", starts_at: "2026-04-10T03:00:00Z", status: "closed", counts: { participants: 8, responded: 4, pending: 4 }, response_rate: 50 });

  const ids = (rows: readonly SatisfactionCampaign[]) => rows.map((row) => row.id);

  it("sem chave preserva a ordem recebida (a do filterCampaigns)", () => {
    const rows = [d, a, c, b];
    expect(ids(sortCampaigns(rows, null, "asc"))).toEqual(["d", "a", "c", "b"]);
    expect(ids(sortCampaigns(rows, null, "desc"))).toEqual(["d", "a", "c", "b"]);
  });

  it("nome usa collation pt-BR (acentos e números) nas duas direções", () => {
    const rows = [a, b, c, d];
    expect(ids(sortCampaigns(rows, "name", "asc"))).toEqual(["a", "b", "d", "c"]);
    expect(ids(sortCampaigns(rows, "name", "desc"))).toEqual(["c", "d", "b", "a"]);
  });

  it("período ordena pelo início nas duas direções", () => {
    const rows = [c, a, d, b];
    expect(ids(sortCampaigns(rows, "period", "asc"))).toEqual(["a", "b", "c", "d"]);
    expect(ids(sortCampaigns(rows, "period", "desc"))).toEqual(["d", "c", "b", "a"]);
  });

  it("situação segue o ciclo Agendada → Aberta → Encerrada (empate estável)", () => {
    const rows = [d, b, a, c];
    // c e d são ambas «closed»: a ordem de entrada é preservada no empate.
    expect(ids(sortCampaigns(rows, "status", "asc"))).toEqual(["a", "b", "d", "c"]);
    expect(ids(sortCampaigns(rows, "status", "desc"))).toEqual(["d", "c", "b", "a"]);
  });

  it("participantes e respostas ordenam numericamente", () => {
    const rows = [b, a, c];
    expect(ids(sortCampaigns(rows, "participants", "asc"))).toEqual(["a", "c", "b"]);
    expect(ids(sortCampaigns(rows, "participants", "desc"))).toEqual(["b", "c", "a"]);
    expect(ids(sortCampaigns(rows, "responded", "asc"))).toEqual(["a", "c", "b"]);
    expect(ids(sortCampaigns(rows, "responded", "desc"))).toEqual(["b", "c", "a"]);
  });

  it("taxa de resposta ordena numericamente e vazia fica sempre por último", () => {
    const rows = [b, c, a, d];
    expect(ids(sortCampaigns(rows, "response_rate", "asc"))).toEqual(["a", "d", "c", "b"]);
    expect(ids(sortCampaigns(rows, "response_rate", "desc"))).toEqual(["c", "d", "a", "b"]);
  });

  it("clique na mesma chave inverte; chave nova começa ascendente", () => {
    expect(nextCampaignSortState(EMPTY_CAMPAIGN_SORT, "status")).toEqual({
      sortKey: "status",
      sortDirection: "asc",
    });
    expect(nextCampaignSortState({ sortKey: "status", sortDirection: "asc" }, "status")).toEqual({
      sortKey: "status",
      sortDirection: "desc",
    });
    expect(nextCampaignSortState({ sortKey: "status", sortDirection: "desc" }, "name")).toEqual({
      sortKey: "name",
      sortDirection: "asc",
    });
    expect(isCampaignSortKey("period")).toBe(true);
    expect(isCampaignSortKey("hack")).toBe(false);
  });
});

describe("preferências salvas da DataTableSection (formato vigente)", () => {
  const LAYOUT_KEY = "commercial:satisfaction-campaigns:layout";
  const COLUMNS_KEY = "commercial:satisfaction-campaigns:columns:v1";
  const FONT_KEY = "commercial:satisfaction-campaigns:table-font-size:v1";

  it("lê visão cards, coluna oculta e fonte gravados pela Section", async () => {
    // React/react-dom resolvidos do plugin-ui: mesma instância usada pelos hooks do kit
    // (senão o dispatcher de hooks vem nulo — "two Reacts").
    const { createElement } = await import("../../../../plugin-ui/node_modules/react/index.js");
    const { renderToString } = await import(
      "../../../../plugin-ui/node_modules/react-dom/server.js"
    );
    const { usePersistedViewLayout } = await import(
      "../../../../plugin-ui/src/hooks/usePersistedViewLayout"
    );
    const { useTableColumnVisibility } = await import(
      "../../../../plugin-ui/src/hooks/useTableColumnVisibility"
    );
    const { useTableFontSize } = await import(
      "../../../../plugin-ui/src/hooks/useTableFontSize"
    );

    const store = new Map<string, string>([
      [LAYOUT_KEY, "cards"],
      [
        COLUMNS_KEY,
        JSON.stringify({
          visibility: {
            name: true,
            status: true,
            participants: true,
            responded: false,
            response_rate: true,
          },
          order: ["name", "status", "participants", "responded", "response_rate"],
        }),
      ],
      [FONT_KEY, "15"],
    ]);
    const fakeWindow = {
      localStorage: {
        getItem: (key: string) => store.get(key) ?? null,
        setItem: () => undefined,
        removeItem: () => undefined,
      },
      matchMedia: () => ({ matches: false }),
    };
    (globalThis as Record<string, unknown>).window = fakeWindow;

    const catalog = [
      { key: "name", label: "Campanha / período" },
      { key: "status", label: "Situação" },
      { key: "participants", label: "Participantes" },
      { key: "responded", label: "Respostas" },
      { key: "response_rate", label: "Taxa de resposta" },
    ];

    let captured: { layout?: string; respondedVisible?: boolean; fontSize?: number } = {};
    function Probe() {
      const { layout } = usePersistedViewLayout({
        storageKey: LAYOUT_KEY,
        defaultMode: "table",
        mobileMaxWidthPx: 768,
      });
      const { visibility } = useTableColumnVisibility({
        storageKey: COLUMNS_KEY,
        columns: catalog,
      });
      const { fontSize } = useTableFontSize({ storageKey: FONT_KEY });
      captured = { layout, respondedVisible: visibility.responded, fontSize };
      return null;
    }

    try {
      renderToString(createElement(Probe));
      expect(captured.layout).toBe("cards");
      expect(captured.respondedVisible).toBe(false);
      expect(captured.fontSize).toBe(15);
    } finally {
      delete (globalThis as Record<string, unknown>).window;
    }
  });
});

describe("«Atualizado em» / «Atualizando…» (UI-02 P2 §5)", () => {
  it("updatedAt monta «Atualizado em dd/mm/aaaa, hh:mm» e updating é «Atualizando…»", () => {
    expect(SATISFACTION_CONTENT.updatedAt("18/11/2026, 14:35")).toBe(
      "Atualizado em 18/11/2026, 14:35",
    );
    expect(SATISFACTION_CONTENT.updating).toBe("Atualizando…");
  });

  it("formatSurveyUpdatedAt formata no fuso do Portal em dd/mm/aaaa, hh:mm", () => {
    expect(formatSurveyUpdatedAt("2026-11-18T17:35:00Z")).toMatch(
      /^\d{2}\/\d{2}\/\d{4}, \d{2}:\d{2}$/,
    );
    expect(formatSurveyUpdatedAt("2026-11-18T17:35:00Z")).toBe("18/11/2026, 14:35");
    expect(formatSurveyUpdatedAt(null)).toBe("—");
    expect(formatSurveyUpdatedAt("lixo")).toBe("—");
  });
});
