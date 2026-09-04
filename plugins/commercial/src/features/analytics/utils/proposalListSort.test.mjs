import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  DEFAULT_PROPOSAL_SORT_DIR,
  DEFAULT_PROPOSAL_SORT_KEY,
  PROPOSAL_COLUMN_TO_SORT_BY,
  proposalApiSortParams,
} from "./proposalListSort.ts";

describe("proposalListSort", () => {
  it("maps UI columns to api-delpi sort_by", () => {
    assert.equal(PROPOSAL_COLUMN_TO_SORT_BY.ov, "proposal_number");
    assert.equal(PROPOSAL_COLUMN_TO_SORT_BY.date, "proposal_date");
    assert.equal(PROPOSAL_COLUMN_TO_SORT_BY.stage, "stage");
    assert.equal(PROPOSAL_COLUMN_TO_SORT_BY.status, "status_code");
  });

  it("builds API params with fallback to proposal_date", () => {
    assert.deepEqual(proposalApiSortParams("ov", "asc"), {
      sort_by: "proposal_number",
      sort_dir: "asc",
    });
    assert.deepEqual(proposalApiSortParams("unknown", "desc"), {
      sort_by: "proposal_date",
      sort_dir: "desc",
    });
    assert.equal(DEFAULT_PROPOSAL_SORT_KEY, "date");
    assert.equal(DEFAULT_PROPOSAL_SORT_DIR, "desc");
  });
});
