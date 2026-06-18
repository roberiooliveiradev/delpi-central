import { describe, expect, it } from "vitest";

import {
  COMPOSER_PANEL_ANCHOR_GAP,
  estimateChatInputPlusMenuItemCount,
  estimateComposerOptionMenuHeight,
  estimateComposerPanelMenuHeight,
  isMenuAnchorOutsideContainer,
  resolveActionMenuPosition,
  resolveComposerMentionMenuPosition,
  resolveComposerMentionMenuWidth,
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
    expect(layout.top).toBe(154);
  });

  it("faz flip horizontal quando não há espaço à direita", () => {
    const layout = resolveActionMenuPosition({
      rect: { left: 700, top: 120, right: 732, bottom: 148, width: 32, height: 28 },
      itemCount: 3,
      menuWidth: 224,
      viewport: { width: 800, height: 600 },
    });

    expect(layout.left).toBe(470);
    expect(layout.top).toBe(154);
  });

  it("não usa preferredLeft negativo quando o gatilho está fora do container", () => {
    const layout = resolveActionMenuPosition({
      rect: { left: -46, top: 500, right: -18, bottom: 528, width: 28, height: 28 },
      itemCount: 4,
      menuWidth: 224,
      viewport: { width: 800, height: 900 },
    });

    expect(layout.left).toBeGreaterThanOrEqual(8);
  });

  it("alinha a borda direita do menu ao gatilho quando horizontalAlign é end", () => {
    const rect = { left: 210, top: 500, right: 238, bottom: 528, width: 28, height: 28 };

    const layout = resolveActionMenuPosition({
      rect,
      itemCount: 4,
      menuWidth: 224,
      horizontalAlign: "end",
      viewport: { width: 800, height: 900 },
    });

    expect(layout.left).toBe(rect.right - 224);
    expect(layout.top).toBe(rect.bottom + 6);
  });

  it("abre no canto inferior direito ou superior direito com flip", () => {
    const rect = { left: 210, top: 820, right: 238, bottom: 848, width: 28, height: 28 };

    const belowLayout = resolveActionMenuPosition({
      rect,
      itemCount: 4,
      menuWidth: 224,
      horizontalAlign: "end",
      verticalAlign: "corner",
      viewport: { width: 800, height: 900 },
    });

    expect(belowLayout.left).toBe(rect.right - 224);
    expect(belowLayout.anchorAbove).toBe(true);
    expect(belowLayout.top).toBe(rect.top - 6);
  });

  it("posiciona menu ⋯ da sidebar à direita do gatilho", () => {
    const sidebarRect = {
      left: 0,
      top: 56,
      right: 272,
      bottom: 900,
      width: 272,
      height: 844,
    };

    const trigger = {
      left: 228,
      top: 420,
      right: 256,
      bottom: 448,
      width: 28,
      height: 28,
    };

    const layout = resolveActionMenuPosition({
      rect: trigger,
      itemCount: 4,
      menuWidth: 224,
      contained: true,
      containerRect: sidebarRect,
      horizontalAlign: "start",
      verticalAlign: "beside",
    });

    expect(layout.left).toBe(trigger.right - sidebarRect.left + 6);
    expect(layout.top).toBe(trigger.top - sidebarRect.top);
    expect(layout.anchorAbove).toBeFalsy();
  });
});

describe("isMenuAnchorOutsideContainer", () => {
  it("detecta gatilho na sidebar à esquerda do #mdc-modal-root", () => {
    const containerRect = {
      left: 276,
      top: 0,
      right: 1076,
      bottom: 900,
      width: 800,
      height: 900,
    };

    expect(
      isMenuAnchorOutsideContainer(
        { left: 230, top: 500, right: 258, bottom: 528, width: 28, height: 28 },
        containerRect,
      ),
    ).toBe(true);
  });
});

describe("composer mobile viewports", () => {
  it("mantém menu + rolável em 390×844", () => {
    const itemCount = estimateChatInputPlusMenuItemCount({
      agentCount: 2,
      projectCount: 4,
    });

    const layout = resolveComposerPanelMenuPosition({
      rect: { left: 16, top: 780, right: 52, bottom: 816, width: 36, height: 36 },
      itemCount,
      viewport: { width: 390, height: 844 },
    });

    expect(layout.anchorAbove).toBe(true);
    expect(layout.top).toBeGreaterThanOrEqual(8);
    expect(layout.maxHeight).toBeGreaterThan(0);
  });

  it("mantém selector de formato acima do gatilho em 360×640", () => {
    const layout = resolveComposerOptionMenuPosition({
      rect: { left: 72, top: 592, right: 180, bottom: 628, width: 108, height: 36 },
      itemCount: 6,
      viewport: { width: 360, height: 640 },
    });

    expect(layout.anchorAbove).toBe(true);
    expect(layout.top).toBeLessThan(592);
    expect(layout.maxHeight).toBeLessThanOrEqual(640 - 8);
  });
});

describe("estimateChatInputPlusMenuItemCount", () => {
  it("conta anexo, agentes, projetos, cabeçalhos e hints", () => {
    expect(
      estimateChatInputPlusMenuItemCount({ agentCount: 4, projectCount: 10 }),
    ).toBe(1 + 4 + 8 + 5);
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

  it("não excede o espaço acima do gatilho quando o composer está no rodapé", () => {
    const rect = { left: 16, top: 780, right: 52, bottom: 816, width: 36, height: 36 };
    const gap = COMPOSER_PANEL_ANCHOR_GAP;
    const spaceAbove = rect.top - 8;

    const layout = resolveComposerPanelMenuPosition({
      rect,
      itemCount: 12,
      viewport: { width: 390, height: 844 },
    });

    expect(layout.anchorAbove).toBe(true);
    expect(layout.maxHeight).toBe(spaceAbove - gap);
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

  it("não converte duas vezes rect já relativo ao container", () => {
    const containerRect = {
      left: 240,
      top: 0,
      right: 1040,
      bottom: 800,
      width: 800,
      height: 800,
    };

    const layout = resolveComposerOptionMenuPosition({
      rect: { left: 48, top: 720, right: 168, bottom: 756, width: 120, height: 36 },
      itemCount: 3,
      contained: true,
      containerRect,
    });

    expect(layout.left).not.toBe(48);
    expect(layout.left).toBe(8);
  });
});

describe("resolveComposerMentionMenuPosition", () => {
  it("ancora no @ com largura limitada ao espaço à direita", () => {
    const width = resolveComposerMentionMenuWidth({
      anchorLeft: 720,
      viewport: { width: 800, height: 600 },
    });

    expect(width).toBe(168);

    const layout = resolveComposerMentionMenuPosition({
      rect: { left: 720, top: 420, right: 720, bottom: 440, width: 0, height: 20 },
      itemCount: 3,
      menuWidth: width,
      viewport: { width: 800, height: 600 },
    });

    expect(layout.left).toBe(624);
    expect(layout.anchorAbove).toBe(true);
    expect(layout.maxHeight).toBeGreaterThan(0);
  });

  it("ajusta a borda esquerda quando o menu ultrapassa a viewport", () => {
    const width = resolveComposerMentionMenuWidth({
      anchorLeft: 40,
      viewport: { width: 320, height: 640 },
    });

    const layout = resolveComposerMentionMenuPosition({
      rect: { left: 40, top: 500, right: 40, bottom: 520, width: 0, height: 20 },
      itemCount: 2,
      menuWidth: width,
      viewport: { width: 320, height: 640 },
    });

    expect(layout.left).toBe(40);
    expect(width).toBeLessThanOrEqual(280);
  });

  it("converte coordenadas do caret apenas uma vez no portal contido", () => {
    const containerRect = {
      left: 240,
      top: 64,
      right: 1040,
      bottom: 864,
      width: 800,
      height: 800,
    };
    const caretRect = {
      left: 320,
      top: 720,
      right: 320,
      bottom: 740,
      width: 0,
      height: 20,
    };

    const layout = resolveComposerMentionMenuPosition({
      rect: caretRect,
      itemCount: 3,
      contained: true,
      containerRect,
    });

    expect(layout.left).toBe(80);
    expect(layout.top).toBeLessThan(656);
    expect(layout.anchorAbove).toBe(true);
  });
});
