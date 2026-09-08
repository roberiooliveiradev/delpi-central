import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  beginSidebarDesktopCollapse,
  beginSidebarDesktopExpand,
  finishSidebarDesktopEnter,
  finishSidebarDesktopExit,
  isSidebarDesktopSlideTransformEnd,
  markSidebarDesktopExitLeaving,
  resolveSidebarDesktopSlideClassNames,
  shouldRenderSidebarPanelContent,
  shouldShowSidebarEdgeHotspot,
  shouldUseSidebarDesktopSlide,
  SIDEBAR_DESKTOP_ENTER_CLASS,
  SIDEBAR_DESKTOP_EXIT_CLASS,
  SIDEBAR_DESKTOP_EXIT_LEAVING_CLASS,
} from "./sidebarDesktopSlide";

const openIdle = {
  collapsed: false,
  exit: false,
  exitLeaving: false,
  enter: false,
};

describe("sidebarDesktopSlide", () => {
  it("usa slide só em desktop sem reduced motion", () => {
    assert.equal(
      shouldUseSidebarDesktopSlide({
        isNarrowViewport: false,
        prefersReducedMotion: false,
      }),
      true,
    );
    assert.equal(
      shouldUseSidebarDesktopSlide({
        isNarrowViewport: true,
        prefersReducedMotion: false,
      }),
      false,
    );
    assert.equal(
      shouldUseSidebarDesktopSlide({
        isNarrowViewport: false,
        prefersReducedMotion: true,
      }),
      false,
    );
  });

  it("collapse com slide: flex colapsa e inicia exit overlay", () => {
    const next = beginSidebarDesktopCollapse(openIdle, true);
    assert.deepEqual(next, {
      collapsed: true,
      exit: true,
      exitLeaving: false,
      enter: false,
    });
  });

  it("collapse sem slide: só collapsed (mobile / reduced motion)", () => {
    const next = beginSidebarDesktopCollapse(openIdle, false);
    assert.deepEqual(next, {
      collapsed: true,
      exit: false,
      exitLeaving: false,
      enter: false,
    });
  });

  it("collapse é no-op se já colapsada ou em exit", () => {
    assert.deepEqual(
      beginSidebarDesktopCollapse({ ...openIdle, collapsed: true }, true),
      { ...openIdle, collapsed: true },
    );
    assert.deepEqual(
      beginSidebarDesktopCollapse(
        { collapsed: false, exit: true, exitLeaving: false, enter: false },
        true,
      ),
      { collapsed: false, exit: true, exitLeaving: false, enter: false },
    );
  });

  it("exit leaving e finish fecham o overlay", () => {
    const exiting = beginSidebarDesktopCollapse(openIdle, true);
    const leaving = markSidebarDesktopExitLeaving(exiting);
    assert.equal(leaving.exitLeaving, true);
    assert.deepEqual(finishSidebarDesktopExit(leaving), {
      collapsed: true,
      exit: false,
      exitLeaving: false,
      enter: false,
    });
  });

  it("expand com slide: abre e marca enter", () => {
    const next = beginSidebarDesktopExpand(
      { collapsed: true, exit: false, exitLeaving: false, enter: false },
      true,
    );
    assert.deepEqual(next, {
      collapsed: false,
      exit: false,
      exitLeaving: false,
      enter: true,
    });
    assert.deepEqual(finishSidebarDesktopEnter(next), {
      collapsed: false,
      exit: false,
      exitLeaving: false,
      enter: false,
    });
  });

  it("classes e visibilidade do painel/hotspot", () => {
    assert.deepEqual(
      resolveSidebarDesktopSlideClassNames({
        exit: true,
        exitLeaving: true,
        enter: false,
      }),
      [SIDEBAR_DESKTOP_EXIT_CLASS, SIDEBAR_DESKTOP_EXIT_LEAVING_CLASS],
    );
    assert.deepEqual(
      resolveSidebarDesktopSlideClassNames({
        exit: false,
        exitLeaving: false,
        enter: true,
      }),
      [SIDEBAR_DESKTOP_ENTER_CLASS],
    );
    assert.equal(
      shouldRenderSidebarPanelContent({ collapsed: true, exit: true }),
      true,
    );
    assert.equal(
      shouldRenderSidebarPanelContent({ collapsed: true, exit: false }),
      false,
    );
    assert.equal(
      shouldShowSidebarEdgeHotspot({ collapsed: true, exit: false }),
      true,
    );
    assert.equal(
      shouldShowSidebarEdgeHotspot({ collapsed: true, exit: true }),
      false,
    );
  });

  it("transition end só no transform do próprio painel", () => {
    const panel = { id: "panel" } as unknown as EventTarget;
    const child = { id: "child" } as unknown as EventTarget;
    assert.equal(
      isSidebarDesktopSlideTransformEnd({
        target: panel,
        currentTarget: panel,
        propertyName: "transform",
      }),
      true,
    );
    assert.equal(
      isSidebarDesktopSlideTransformEnd({
        target: panel,
        currentTarget: panel,
        propertyName: "opacity",
      }),
      false,
    );
    assert.equal(
      isSidebarDesktopSlideTransformEnd({
        target: child,
        currentTarget: panel,
        propertyName: "transform",
      }),
      false,
    );
  });
});
