import { describe, expect, it } from "vitest";

import {
  COMPOSER_PANEL_ANCHOR_GAP,
  estimateChatInputPlusMenuItemCount,
  estimateComposerOptionMenuHeight,
  estimateComposerPanelMenuHeight,
  resolveActionMenuPosition,
  resolveComposerOptionMenuPosition,
  resolveComposerPanelMenuPosition,
  resolveContextMenuPosition,
  resolveMenuPositionInContainer,
} from "./menuPositionUtils";

describe("resolveContextMenuPosition", () => {
  it("usa coordenadas do container quando o portal está contido", () => {
    const containerRect = {
      left: 240,
      top: 0,
      right: 1040,
      bottom: 800,
      width: 800,
      height: 800,
    };

    const position = resolveContextMenuPosition({
      anchor: {
        rect: { left: 300, top: 400, right: 380, bottom: 428, width: 80, height: 28 },
      },
      itemCount: 3,
      contained: true,
      containerRect,
    });

    expect(position.left).toBe(60);
    expect(position.top).toBeGreaterThanOrEqual(428 - containerRect.top + 6);
  });

  it("posiciona por ponto relativo ao container quando contido", () => {
    const containerRect = {
      left: 100,
      top: 50,
      right: 900,
      bottom: 650,
      width: 800,
      height: 600,
    };

    const position = resolveContextMenuPosition({
      anchor: { point: { x: 220, y: 300 } },
      itemCount: 2,
      contained: true,
      containerRect,
    });

    expect(position.left).toBe(120);
    expect(position.top).toBe(250);
  });
});

describe("resolveMenuPositionInContainer", () => {
  it("converte coordenadas da viewport para o container do chat", () => {
    const containerRect = {
      left: 240,
      top: 0,
      right: 1040,
      bottom: 800,
      width: 800,
      height: 800,
    };

    const position = resolveMenuPositionInContainer({
      rect: { left: 300, top: 400, right: 380, bottom: 428, width: 80, height: 28 },
      containerRect,
      itemCount: 3,
    });

    expect(position.left).toBe(60);
    expect(position.top).toBeGreaterThanOrEqual(428 - containerRect.top + 6);
  });
});

describe("resolveActionMenuPosition", () => {
  it("abre à direita do gatilho quando há espaço", () => {
    const layout = resolveActionMenuPosition({
      rect: { left: 48, top: 120, right: 80, bottom: 148, width: 32, height: 28 },
      itemCount: 3,
      viewport: { width: 800, height: 600 },
    });

    expect(layout.left).toBe(86);
    expect(layout.top).toBe(120);
  });
});

describe("estimateChatInputPlusMenuItemCount", () => {
  it("conta anexo, agentes, projetos e cabeçalhos", () => {
    expect(
      estimateChatInputPlusMenuItemCount({ agentCount: 4, projectCount: 10 }),
    ).toBe(1 + 4 + 8 + 3);
  });
});

describe("resolveComposerPanelMenuPosition", () => {
  it("limita altura do painel largo no rodapé", () => {
    const viewportHeight = 520;
    const itemCount = estimateChatInputPlusMenuItemCount({
      agentCount: 6,
      projectCount: 8,
    });

    const layout = resolveComposerPanelMenuPosition({
      rect: { left: 24, top: 460, right: 60, bottom: 496, width: 36, height: 36 },
      itemCount,
      viewport: { width: 390, height: viewportHeight },
    });

    expect(layout.top).toBeLessThan(460);
    expect(layout.anchorAbove).toBe(true);
    expect(layout.top).toBeLessThanOrEqual(496 - COMPOSER_PANEL_ANCHOR_GAP);
    expect(layout.maxHeight).toBeLessThanOrEqual(viewportHeight - 8);
  });

  it("ancora acima do + com gap legado e borda esquerda alinhada", () => {
    const itemCount = 3;
    const rect = { left: 48, top: 460, right: 84, bottom: 496, width: 36, height: 36 };

    const layout = resolveComposerPanelMenuPosition({
      rect,
      itemCount,
      viewport: { width: 800, height: 600 },
    });

    expect(layout.left).toBe(48);
    expect(layout.top).toBe(rect.top - COMPOSER_PANEL_ANCHOR_GAP);
    expect(layout.anchorAbove).toBe(true);
  });
});

describe("resolveComposerOptionMenuPosition", () => {
  it("limita altura e posiciona acima quando o composer está no rodapé", () => {
    const viewportHeight = 480;

    const layout = resolveComposerOptionMenuPosition({
      rect: { left: 48, top: 420, right: 168, bottom: 456, width: 120, height: 36 },
      itemCount: 7,
      viewport: { width: 390, height: viewportHeight },
    });

    expect(layout.top).toBeLessThan(420);
    expect(layout.top).toBeGreaterThanOrEqual(8);
    expect(layout.anchorAbove).toBe(true);
    expect(layout.maxHeight).toBeLessThan(estimateComposerOptionMenuHeight(7));
  });

  it("usa coordenadas relativas ao #mdc-modal-root quando contido", () => {
    const containerRect = {
      left: 240,
      top: 0,
      right: 1040,
      bottom: 800,
      width: 800,
      height: 800,
    };

    const layout = resolveComposerOptionMenuPosition({
      rect: { left: 288, top: 720, right: 408, bottom: 756, width: 120, height: 36 },
      itemCount: 3,
      contained: true,
      containerRect,
    });

    expect(layout.left).toBe(48);
    expect(layout.top).toBeLessThan(720 - containerRect.top);
    expect(layout.anchorAbove).toBe(true);
    expect(layout.maxHeight).toBeLessThanOrEqual(containerRect.height - 8);
  });
});
