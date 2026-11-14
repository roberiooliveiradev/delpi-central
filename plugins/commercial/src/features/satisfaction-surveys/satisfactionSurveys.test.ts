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
} from "./inviteMessage";
import { absolutizeInvite } from "./inviteLink";
import {
  isoToLocalInput,
  localInputToIso,
  surveyYearOf,
} from "./satisfactionDates";
import { resolveCanManageSatisfaction } from "./satisfactionAccess";
import {
  campaignYearOptions,
  EMPTY_CAMPAIGN_FILTERS,
  filterCampaigns,
  filterRecipients,
  hasActiveCampaignFilters,
  recipientKeys,
} from "./satisfactionFilters";

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
