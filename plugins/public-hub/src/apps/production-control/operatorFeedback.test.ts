import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  ApiError,
  createOperatorFeedback,
  fetchActiveOperatorFeedbacks,
  isAuthError,
  type PublicOperatorFeedback,
} from "./api.ts";
import {
  DEFAULT_FEEDBACK_REASON,
  DEFAULT_FEEDBACK_TYPE,
  MATERIAL_SELECTION_REQUIRED,
  feedbackReasonLabel,
  feedbackStatusPresentation,
  feedbackSubmitErrorMessage,
  feedbackTypeLabel,
  firstActiveFeedback,
  isFeedbackEventForOperation,
  materialStatusLabel,
  resolveFeedbackPanelState,
} from "./operatorFeedback.ts";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime.ts";

function feedback(partial: Partial<PublicOperatorFeedback> = {}): PublicOperatorFeedback {
  return {
    id: "f-1",
    productionOrder: "24640401002",
    operationCode: "03",
    reportedWorkCenter: "CT-02",
    feedbackType: "cannot_produce",
    reasonCode: "missing_material",
    note: null,
    status: "open",
    createdAt: "2026-10-07T10:00:00+00:00",
    acknowledgedAt: null,
    resolvedAt: null,
    ...partial,
  };
}

// --- presentation ------------------------------------------------------------

describe("operator feedback presentation", () => {
  it("maps open to PCP informado", () => {
    const p = feedbackStatusPresentation("open");
    assert.equal(p.label, "PCP informado");
    assert.equal(p.tone, "informed");
  });

  it("maps acknowledged to PCP em tratativa", () => {
    const p = feedbackStatusPresentation("acknowledged");
    assert.equal(p.label, "PCP em tratativa");
    assert.equal(p.tone, "treating");
  });

  it("falls back safely on unknown status", () => {
    const p = feedbackStatusPresentation("weird_future_status");
    assert.equal(p.label, "Aviso registrado");
    assert.equal(p.tone, "muted");
  });

  it("labels the C1 catalog without MES downtime vocabulary", () => {
    assert.equal(feedbackTypeLabel("cannot_produce"), "Não será possível produzir");
    assert.equal(feedbackReasonLabel("missing_material"), "Falta de matéria-prima");
    assert.equal(DEFAULT_FEEDBACK_TYPE, "cannot_produce");
    assert.equal(DEFAULT_FEEDBACK_REASON, "missing_material");
  });
});

// --- active feedback ----------------------------------------------------------

describe("firstActiveFeedback", () => {
  it("returns the open feedback", () => {
    assert.equal(firstActiveFeedback([feedback()])?.id, "f-1");
  });

  it("returns acknowledged as still active", () => {
    const item = feedback({ status: "acknowledged" });
    assert.equal(firstActiveFeedback([item])?.status, "acknowledged");
  });

  it("ignores resolved — a new report must be possible", () => {
    assert.equal(firstActiveFeedback([feedback({ status: "resolved" })]), null);
    assert.equal(firstActiveFeedback([]), null);
    assert.equal(firstActiveFeedback(null), null);
  });
});

// --- realtime filtering ---------------------------------------------------------

function event(partial: Partial<MachineLoadRealtimeEvent> = {}): MachineLoadRealtimeEvent {
  return {
    type: "operator_feedback_updated",
    reason: "created",
    branch: "01",
    feedbackId: "f-1",
    productionOrder: "24640401002",
    operationCode: "03",
    status: "open",
    ...partial,
  };
}

describe("operator_feedback_updated filtering", () => {
  it("accepts the event for the open operation", () => {
    assert.equal(
      isFeedbackEventForOperation(event(), "24640401002", "03"),
      true,
    );
  });

  it("normalizes padded operation codes", () => {
    assert.equal(
      isFeedbackEventForOperation(event({ operationCode: "003" }), "24640401002", "03"),
      true,
    );
  });

  it("ignores another production order", () => {
    assert.equal(
      isFeedbackEventForOperation(
        event({ productionOrder: "99900011122" }),
        "24640401002",
        "03",
      ),
      false,
    );
  });

  it("ignores another operation", () => {
    assert.equal(
      isFeedbackEventForOperation(event({ operationCode: "05" }), "24640401002", "03"),
      false,
    );
  });

  it("ignores non-feedback events", () => {
    assert.equal(
      isFeedbackEventForOperation(
        { ...event(), type: "machine_load_updated" },
        "24640401002",
        "03",
      ),
      false,
    );
    assert.equal(isFeedbackEventForOperation(null, "24640401002", "03"), false);
  });
});

// --- panel state machine ---------------------------------------------------------

describe("resolveFeedbackPanelState", () => {
  const base = { loading: false, error: null as string | null };

  it("restoring session", () => {
    assert.equal(
      resolveFeedbackPanelState({ sessionStatus: "restoring", ...base, active: null }),
      "restoring",
    );
  });

  it("anonymous operator — identify CTA", () => {
    assert.equal(
      resolveFeedbackPanelState({ sessionStatus: "anonymous", ...base, active: null }),
      "anonymous",
    );
  });

  it("loading while identified without feedback yet", () => {
    assert.equal(
      resolveFeedbackPanelState({
        sessionStatus: "identified",
        loading: true,
        error: null,
        active: null,
      }),
      "loading",
    );
  });

  it("no active feedback → CTA state", () => {
    assert.equal(
      resolveFeedbackPanelState({ sessionStatus: "identified", ...base, active: null }),
      "none",
    );
  });

  it("open and acknowledged map to their visual states", () => {
    assert.equal(
      resolveFeedbackPanelState({
        sessionStatus: "identified",
        ...base,
        active: feedback(),
      }),
      "open",
    );
    assert.equal(
      resolveFeedbackPanelState({
        sessionStatus: "identified",
        ...base,
        active: feedback({ status: "acknowledged" }),
      }),
      "acknowledged",
    );
  });

  it("resolved disappears — CTA returns", () => {
    assert.equal(
      resolveFeedbackPanelState({
        sessionStatus: "identified",
        ...base,
        active: feedback({ status: "resolved" }),
      }),
      "none",
    );
  });

  it("error without active feedback", () => {
    assert.equal(
      resolveFeedbackPanelState({
        sessionStatus: "identified",
        loading: false,
        error: "falhou",
        active: null,
      }),
      "error",
    );
  });
});

// --- submit error messages ---------------------------------------------------------

describe("feedbackSubmitErrorMessage", () => {
  it("409 is friendly, not scary", () => {
    assert.equal(
      feedbackSubmitErrorMessage(409),
      "O PCP já foi informado sobre este impedimento.",
    );
  });

  it("404 does not reveal other work centers", () => {
    const msg = feedbackSubmitErrorMessage(404);
    assert.match(msg, /não está mais disponível neste posto/);
    assert.doesNotMatch(msg, /CT-\d/);
  });

  it("401 asks to identify again", () => {
    assert.match(feedbackSubmitErrorMessage(401), /expirou/);
  });
});

// --- api layer -----------------------------------------------------------------

type RecordedCall = { url: string; init?: RequestInit };

function stubFetch(
  status: number,
  body: unknown,
): { calls: RecordedCall[]; restore: () => void } {
  const calls: RecordedCall[] = [];
  const original = globalThis.fetch;
  globalThis.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), init });
    return new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  }) as typeof fetch;
  return { calls, restore: () => (globalThis.fetch = original) };
}

describe("operator feedback api", () => {
  it("POST hits the C2 endpoint with bench session and only operator-chosen fields", async () => {
    const { calls, restore } = stubFetch(200, {
      success: true,
      message: "OK",
      data: feedback(),
    });
    try {
      await createOperatorFeedback("cockpit-token", "sess-token", {
        productionOrder: "24640401002",
        operationCode: "03",
        feedbackType: "cannot_produce",
        reasonCode: "missing_material",
        note: "Falta terminal",
      });
    } finally {
      restore();
    }
    const call = calls[0];
    assert.match(call.url, /\/operator-feedbacks$/);
    assert.match(call.url, /cockpit-token/);
    const headers = call.init?.headers as Record<string, string>;
    assert.equal(headers["X-Delpi-Bench-Session"], "sess-token");
    const payload = JSON.parse(String(call.init?.body));
    assert.deepEqual(Object.keys(payload).sort(), [
      "feedbackType",
      "materialCodes",
      "note",
      "operationCode",
      "productionOrder",
      "reasonCode",
      "website",
    ]);
    // C5: só códigos — nunca snapshots (descrição/unidade/saldo)
    assert.deepEqual(payload.materialCodes, []);
    assert.equal(payload.feedbackType, "cannot_produce");
    assert.equal(payload.reasonCode, "missing_material");
    // identidade/filial/posto NUNCA saem do frontend
    assert.equal(payload.branch, undefined);
    assert.equal(payload.workCenter, undefined);
    assert.equal(payload.operatorCode, undefined);
    assert.equal(payload.operatorName, undefined);
    assert.equal(payload.benchSessionId, undefined);
    assert.equal(payload.runId, undefined);
  });

  it("GET queries the active endpoint with op params and session header", async () => {
    const { calls, restore } = stubFetch(200, {
      success: true,
      message: "OK",
      data: { items: [feedback()] },
    });
    try {
      const items = await fetchActiveOperatorFeedbacks(
        "cockpit-token",
        "sess-token",
        "24640401002",
        "03",
      );
      assert.equal(items.length, 1);
    } finally {
      restore();
    }
    const call = calls[0];
    assert.match(call.url, /\/operator-feedbacks\/active\?/);
    assert.match(call.url, /productionOrder=24640401002/);
    assert.match(call.url, /operationCode=03/);
    const headers = call.init?.headers as Record<string, string>;
    assert.equal(headers["X-Delpi-Bench-Session"], "sess-token");
  });

  it("401 surfaces as auth error for session invalidation", async () => {
    const { restore } = stubFetch(401, {
      success: false,
      message: "Sessão expirada.",
      data: null,
    });
    try {
      await fetchActiveOperatorFeedbacks("t", "sess", "OP", "03").then(
        () => assert.fail("should throw"),
        (err) => {
          assert.equal(isAuthError(err), true);
          assert.equal((err as ApiError).status, 401);
        },
      );
    } finally {
      restore();
    }
  });

  it("409 surfaces the ApiError status for friendly handling", async () => {
    const { restore } = stubFetch(409, {
      success: false,
      message: "O PCP já foi informado sobre este impedimento.",
      data: null,
    });
    try {
      await createOperatorFeedback("t", "sess", {
        productionOrder: "OP",
        operationCode: "03",
        feedbackType: "cannot_produce",
        reasonCode: "missing_material",
      }).then(
        () => assert.fail("should throw"),
        (err) => {
          assert.equal((err as ApiError).status, 409);
        },
      );
    } finally {
      restore();
    }
  });
});


// --- C5: materiais estruturados ------------------------------------------------

describe("material status label (C5)", () => {
  it("maps pending to Aguardando separação", () => {
    assert.equal(materialStatusLabel("pending"), "Aguardando separação");
  });

  it("maps picked to Em separação", () => {
    assert.equal(materialStatusLabel("picked"), "Em separação");
  });

  it("maps delivered to Entregue", () => {
    assert.equal(materialStatusLabel("delivered"), "Entregue");
  });

  it("falls back to pending label on unknown status", () => {
    assert.equal(materialStatusLabel("future_status"), "Aguardando separação");
    assert.equal(materialStatusLabel(null), "Aguardando separação");
  });

  it("selection required message is the contract copy", () => {
    assert.equal(
      MATERIAL_SELECTION_REQUIRED,
      "Selecione pelo menos um material que está impedindo a produção.",
    );
  });
});

describe("operator feedback api — materialCodes (C5)", () => {
  it("POST sends only material codes, never snapshots", async () => {
    const { calls, restore } = stubFetch(200, {
      success: true,
      message: "OK",
      data: feedback({ materials: [] }),
    });
    try {
      await createOperatorFeedback("cockpit-token", "sess-token", {
        productionOrder: "24640401002",
        operationCode: "03",
        feedbackType: "cannot_produce",
        reasonCode: "missing_material",
        materialCodes: ["10081234", "10085678"],
        note: "Falta terminal",
      });
    } finally {
      restore();
    }
    const payload = JSON.parse(String(calls[0].init?.body));
    assert.deepEqual(payload.materialCodes, ["10081234", "10085678"]);
    // nenhum campo de snapshot sai do navegador
    for (const key of [
      "materials",
      "description",
      "unit",
      "openQty",
      "open_qty",
      "workCenter",
      "branch",
    ]) {
      assert.equal(payload[key], undefined, key);
    }
  });

  it("GET parses materials with status for the panel", async () => {
    const { calls, restore } = stubFetch(200, {
      success: true,
      message: "OK",
      data: {
        items: [
          feedback({
            materials: [
              {
                productCode: "10081234",
                description: "TERMINAL FASTON",
                unit: "PC",
                status: "picked",
              },
            ],
          }),
        ],
      },
    });
    try {
      const items = await fetchActiveOperatorFeedbacks(
        "cockpit-token",
        "sess-token",
        "24640401002",
        "03",
      );
      assert.equal(items[0].materials?.[0].status, "picked");
      assert.equal(items[0].materials?.[0].productCode, "10081234");
    } finally {
      restore();
    }
    assert.ok(calls.length === 1);
  });

  it("legacy feedback without materials keeps materials undefined", async () => {
    const { restore } = stubFetch(200, {
      success: true,
      message: "OK",
      data: { items: [feedback()] },
    });
    try {
      const items = await fetchActiveOperatorFeedbacks(
        "cockpit-token",
        "sess-token",
        "24640401002",
        "03",
      );
      assert.equal(items[0].materials, undefined);
    } finally {
      restore();
    }
  });
});
