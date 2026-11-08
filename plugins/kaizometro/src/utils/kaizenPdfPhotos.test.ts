import { describe, expect, it } from "vitest";
import type { KaizenEvidence } from "../types/kaizen";
import { selectKaizenPdfPhotos } from "./kaizenPdfPhotos";

function photo(id: string, stage: KaizenEvidence["stage"], revision_id: string | null): KaizenEvidence {
  return {
    id,
    kaizen_id: "kaizen-1",
    revision_id,
    type: "photo",
    stage,
    file_name: `${id}.jpg`,
    stored_name: `${id}.jpg`,
    mime_type: "image/jpeg",
    size_bytes: 100,
    description: null,
    external_url: null,
    uploaded_by_user_id: "user-1",
    uploaded_by_name: null,
    created_at: "2026-09-03T00:00:00Z",
  };
}

describe("selectKaizenPdfPhotos", () => {
  it("prioriza Antes e Depois e limita a duas imagens", () => {
    const list = [
      photo("general", "geral", "rev-1"),
      photo("before", "antes", "rev-1"),
      photo("after", "depois", "rev-1"),
      photo("other", "antes", "rev-2"),
    ];
    expect(selectKaizenPdfPhotos(list, "rev-1").map((item) => item.id)).toEqual(["before", "after"]);
  });

  it("não mistura revisões ou inclui anexos não fotográficos", () => {
    const pdf = { ...photo("pdf", "antes", null), type: "document" as const, mime_type: "application/pdf" };
    const list = [photo("before", "antes", null), photo("other", "depois", "rev-2"), pdf];
    expect(selectKaizenPdfPhotos(list, null).map((item) => item.id)).toEqual(["before"]);
  });
});
