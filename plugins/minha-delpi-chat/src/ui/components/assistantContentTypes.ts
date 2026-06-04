import type { ChatPresentation } from "../../data/api/chatTypes";

import type { StackSectionChrome } from "./presentationStackSections";

export type AssistantContentSegment =
  | { kind: "stackSection"; section: StackSectionChrome }
  | { kind: "markdown"; markdown: string }
  | { kind: "code"; language: string; code: string }
  | { kind: "table"; presentation: Extract<ChatPresentation, { type: "table" }> }
  | { kind: "chart"; presentation: Extract<ChatPresentation, { type: "chart" }> }
  | { kind: "tree"; presentation: Extract<ChatPresentation, { type: "tree" }> }
  | { kind: "kpi"; presentation: Extract<ChatPresentation, { type: "kpi" }> }
  | { kind: "dashboard"; presentation: Extract<ChatPresentation, { type: "dashboard" }> };
