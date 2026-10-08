/**
 * G4 — RT-COL-*: round-trip CREATE_EDIT collaboration.
 * participant expanded (processRef + laneSet + childLaneSet + flowNodeRef),
 * black-box pool, messageFlow cross-pool com BPMNEdge + BPMNLabel.
 */
import { test } from "../helpers";
import { readFixture, roundTripNoEdit } from "../rt-helpers";

const CE_COL = readFixture("ce-collaboration.bpmn");

test("RT-COL-01 collaboration: pools + nested lanes + messageFlow", async ({
  page,
}) => {
  await roundTripNoEdit(page, "editor", CE_COL, {
    name: "RT-COL-01",
    renderIds: ["P1", "L1", "L1_N", "L2", "T_INNER", "P_BB", "MF1"],
  });
});
