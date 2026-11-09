import { describe, expect, it, vi } from "vitest";

import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";
import {
  buildMeetingMinuteDetailPagePath,
  buildMeetingMinuteEditorPagePath,
  buildMeetingMinuteSignPagePath,
  buildMeetingMinutesListPagePath,
  buildMeetingMinutesPendingPagePath,
  buildMySignaturePagePath,
  buildRootSectionPagePath,
  buildSettingsEntityPagePath,
  buildSettingsSectionPagePath,
  isLikelyUuidLabel,
  safeEntityPathLabel,
  truncatePathLabel,
} from "./tmPagePath";

describe("tmPagePath helpers", () => {
  it("truncates long labels without exposing raw UUID as preferred label", () => {
    expect(truncatePathLabel("a".repeat(50)).endsWith("…")).toBe(true);
    expect(isLikelyUuidLabel("550e8400-e29b-41d4-a716-446655440000")).toBe(true);
    expect(safeEntityPathLabel("550e8400-e29b-41d4-a716-446655440000", "Ata")).toBe("Ata");
    expect(safeEntityPathLabel("Kickoff Q1", "Ata")).toBe("Kickoff Q1");
  });
});

describe("tmPagePath builders", () => {
  const onNavigate = vi.fn();

  it("root section: Início → current", () => {
    const path = buildRootSectionPagePath("Atas", onNavigate);
    expect(path.back.label).toBe("Início");
    expect(path.back.href).toBe(TRANSFORMOMETRO_ROUTES.home);
    expect(path.items).toEqual([]);
    expect(path.current).toBe("Atas");
  });

  it("atas family hierarchy", () => {
    expect(buildMeetingMinutesListPagePath(onNavigate).current).toBe("Atas");

    const detail = buildMeetingMinuteDetailPagePath({ onNavigate, label: "Reunião X" });
    expect(detail.back.label).toBe("Atas");
    expect(detail.current).toBe("Reunião X");

    const create = buildMeetingMinuteEditorPagePath({ onNavigate, mode: "new" });
    expect(create.back.label).toBe("Atas");
    expect(create.current).toBe("Nova ata");

    const edit = buildMeetingMinuteEditorPagePath({
      onNavigate,
      mode: "edit",
      ataId: "ata-1",
      label: "Reunião X",
    });
    expect(edit.back.label).toBe("Atas");
    expect(edit.items?.[0]?.label).toBe("Reunião X");
    expect(edit.current).toBe("Editar");

    const sign = buildMeetingMinuteSignPagePath({
      onNavigate,
      ataId: "ata-1",
      label: "Reunião X",
    });
    expect(sign.items?.[0]?.label).toBe("Reunião X");
    expect(sign.current).toBe("Assinar");

    expect(buildMeetingMinutesPendingPagePath(onNavigate).current).toBe("Pendências");
    expect(buildMySignaturePagePath(onNavigate).current).toBe("Minha assinatura");
  });

  it("settings hierarchy", () => {
    const section = buildSettingsSectionPagePath("unidades", onNavigate);
    expect(section.back.label).toBe("Início");
    expect(section.items?.[0]?.label).toBe("Configurações");
    expect(section.current).toBe("Unidades");

    const create = buildSettingsEntityPagePath({
      section: "unidades",
      onNavigate,
      create: true,
    });
    expect(create.back.label).toBe("Configurações");
    expect(create.items?.[0]?.label).toBe("Unidades");
    expect(create.current).toBe("Nova unidade");

    const detail = buildSettingsEntityPagePath({
      section: "departamentos",
      onNavigate,
      label: "TI — Tecnologia",
    });
    expect(detail.current).toBe("TI — Tecnologia");
  });
});
