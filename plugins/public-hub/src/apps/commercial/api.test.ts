import assert from "node:assert/strict";
import { afterEach, describe, it } from "node:test";
import {
  classifySubmitFailure,
  fetchPublicSurvey,
  parsePublicSurvey,
  submitPublicSurvey,
} from "./api.ts";
import { rawQuestionnaire } from "./testFixtures.ts";

const TOKEN = "tok_ABCDEFGHIJKLMNOP";
const realFetch = globalThis.fetch;

type Call = { url: string; init: RequestInit };

function stubFetch(status: number, body: unknown, calls: Call[] = []) {
  globalThis.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), init: init ?? {} });
    return new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;
  return calls;
}

afterEach(() => {
  globalThis.fetch = realFetch;
});

describe("GET público", () => {
  it("open traz questionário e empresa; demais estados não carregam perguntas", () => {
    const open = parsePublicSurvey(TOKEN, {
      status: "open",
      campaign_name: "Pesquisa 2026",
      starts_at: "2026-03-01T03:00:00Z",
      ends_at: "2026-03-31T03:00:00Z",
      company_name: "Alfa",
      questionnaire: rawQuestionnaire(),
    });
    assert.equal(open.status, "open");
    if (open.status === "open") {
      assert.equal(open.companyName, "Alfa");
      assert.equal(open.questionnaire.items.length, 15);
    }
    for (const status of ["not_open", "closed", "already_submitted"] as const) {
      const state = parsePublicSurvey(TOKEN, { status, campaign_name: "X", starts_at: "", ends_at: "" });
      assert.equal(state.status, status);
      assert.equal("questionnaire" in state, false);
    }
  });

  it("open sem catálogo íntegro vira temporary_error; status desconhecido idem", () => {
    assert.equal(parsePublicSurvey(TOKEN, { status: "open", questionnaire: { items: [] } }).status, "temporary_error");
    assert.equal(parsePublicSurvey(TOKEN, { status: "???" }).status, "temporary_error");
    assert.equal(parsePublicSurvey(TOKEN, null).status, "temporary_error");
  });

  it("chama a commercial-api sem credenciais e sem referrer; 404 e rede mapeiam estados seguros", async () => {
    const calls = stubFetch(404, { success: false, message: "x", data: { code: "invalid_token" } });
    assert.equal((await fetchPublicSurvey(TOKEN)).status, "invalid");
    assert.equal(calls[0].url, `/apps/commercial-api/public/satisfaction-surveys/${TOKEN}`);
    assert.equal(calls[0].init.credentials, "omit");
    assert.equal(calls[0].init.referrerPolicy, "no-referrer");
    const headers = calls[0].init.headers as Record<string, string>;
    assert.equal(headers.Authorization, undefined);

    stubFetch(503, { success: false, data: { code: "temporary_error" } });
    assert.equal((await fetchPublicSurvey(TOKEN)).status, "temporary_error");

    globalThis.fetch = (async () => {
      throw new TypeError("network");
    }) as typeof fetch;
    assert.equal((await fetchPublicSurvey(TOKEN)).status, "temporary_error");
  });
});

describe("POST público", () => {
  const payload = {
    overall_score: 5,
    recommendation_score: 0,
    dimensions: { quality: null },
    strengths: null,
    improvements: null,
    unmet_needs: null,
  };

  it("sucesso apenas com 2xx; envia JSON sem identificação do respondente", async () => {
    const calls = stubFetch(201, { success: true, data: {} });
    assert.deepEqual(await submitPublicSurvey(TOKEN, payload), { outcome: "submitted" });
    assert.equal(calls[0].init.method, "POST");
    assert.match(calls[0].url, /\/response$/);
    assert.deepEqual(JSON.parse(String(calls[0].init.body)), payload);
  });

  it("409 já respondida / encerrada / ainda não aberta; 404 inválido", async () => {
    stubFetch(409, { success: false, message: "m", data: { code: "already_submitted" } });
    assert.equal((await submitPublicSurvey(TOKEN, payload)).outcome, "already_submitted");
    stubFetch(409, { success: false, message: "m", data: { code: "closed" } });
    assert.equal((await submitPublicSurvey(TOKEN, payload)).outcome, "closed");
    stubFetch(409, { success: false, message: "m", data: { code: "not_open" } });
    assert.equal((await submitPublicSurvey(TOKEN, payload)).outcome, "not_open");
    stubFetch(404, { success: false, data: { code: "invalid_token" } });
    assert.equal((await submitPublicSurvey(TOKEN, payload)).outcome, "invalid");
  });

  it("falha de rede/5xx nunca confirma envio e preserva retentativa explícita", async () => {
    globalThis.fetch = (async () => {
      throw new TypeError("network");
    }) as typeof fetch;
    assert.equal((await submitPublicSurvey(TOKEN, payload)).outcome, "temporary_error");
    assert.equal(classifySubmitFailure(503, null).outcome, "temporary_error");
    assert.equal(classifySubmitFailure(422, { message: "inválido" }).outcome, "rejected");
  });
});
