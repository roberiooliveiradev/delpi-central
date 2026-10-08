/**
 * G4 — RT-ART-*: round-trip CREATE_EDIT artifacts/data.
 * DataObject(Reference), DataStoreReference, TextAnnotation(+texto),
 * Group, Association, DataInputAssociation/DataOutputAssociation.
 */
import { test } from "../helpers";
import { readFixture, roundTripNoEdit } from "../rt-helpers";

const CE_ART = readFixture("ce-artifacts.bpmn");

test("RT-ART-01 artifacts: data + annotation + group + associations", async ({
  page,
}) => {
  await roundTripNoEdit(page, "editor", CE_ART, {
    name: "RT-ART-01",
    renderIds: ["DOR1", "DOR2", "DSR1", "ANN1", "GRP1", "ASOC1", "DIA1"],
  });
});
