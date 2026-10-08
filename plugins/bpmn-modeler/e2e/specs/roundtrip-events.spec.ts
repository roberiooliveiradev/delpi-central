/**
 * G4 — RT-EVT-*: round-trip CREATE_EDIT events (position × definition).
 * Corpus: start None/Msg/Timer/Signal · catch Msg/Timer/Signal/Link ·
 * boundary Msg/Timer/Error/Signal/Esc int+non-int · throw None/Msg/Signal/
 * Esc/Link · end None/Msg/Error/Signal/Esc/Terminate — com refs reais
 * (messageRef/errorRef/signalRef/escalationRef) e cancelActivity.
 */
import { test } from "../helpers";
import { readFixture, roundTripNoEdit } from "../rt-helpers";

const CE_EVT = readFixture("ce-events.bpmn");

test("RT-EVT-01 events: todas as posições × definições CREATE_EDIT", async ({
  page,
}) => {
  await roundTripNoEdit(page, "editor", CE_EVT, {
    name: "RT-EVT-01",
    renderIds: [
      "S_NONE",
      "S_MSG",
      "S_TIMER",
      "S_SIG",
      "B_ERR",
      "B_NI_MSG",
      "C_LINK",
      "TH_ESC",
      "E_TERM",
      "E_ERR",
    ],
  });
});
