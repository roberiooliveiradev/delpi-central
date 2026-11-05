import { beforeEach } from "vitest";
import { notifyManager } from "@tanstack/query-core";

import { resetReportQueryCacheForTests } from "../app/reportQueryCache";

notifyManager.setScheduler((callback) => {
  callback();
});

beforeEach(() => {
  resetReportQueryCacheForTests();
});
