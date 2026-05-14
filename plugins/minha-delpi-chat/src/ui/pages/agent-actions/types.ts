import type {
  ChatActionCatalogItem,
  ChatActionTestLog,
  ChatActionTestResult,
} from "../../../data/api/chatTypes";

export type ActionTestPayload = {
  pathParams: Record<string, string>;
  query: Record<string, string>;
  body?: unknown;
};

export type ActionTestPanelProps = {
  action: ChatActionCatalogItem;
  isRunning: boolean;
  result: ChatActionTestResult | null;
  logs: ChatActionTestLog[];
  onRun: (payload: ActionTestPayload) => Promise<void>;
  onClose: () => void;
};
