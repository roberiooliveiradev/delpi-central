// @vitest-environment jsdom
/**
 * G9-LAYOUT-1 §41/§47 — prova de read-only do preview compartilhado:
 * a superfície de preview monta NavigatedViewer (não Modeler), então
 * NÃO EXISTE caminho de mutação — nenhum serviço de edição está
 * registrado (modeling, contextPad, palette, directEditing, replace,
 * clipboard, distribute, align, autoScroll é navegação — permitido).
 * Não é "botão escondido": é ausência de capability no container DI.
 */
import { beforeAll, describe, expect, it } from "vitest";
import NavigatedViewer from "bpmn-js/lib/NavigatedViewer";

import { installCanvasDomStubs } from "./canvasTestSetup";

const MUTATION_SERVICES = [
  "modeling",
  "contextPad",
  "palette",
  "directEditing",
  "bpmnReplace",
  "replaceMenuProvider",
  "copyPaste",
  "clipboard",
  "create",
  "distributeElements",
  "alignElements",
  "bpmnOrdering",
  "spaceTool",
  "lassoTool",
  "handTool",
  "globalConnect",
  "connect",
  "resize",
  "bendpoints",
];

const NAVIGATION_SERVICES = [
  "canvas",
  "zoomScroll",
  "moveCanvas",
  "elementRegistry",
];

describe("BpmnReadonlyViewer — NavigatedViewer sem capability de edição", () => {
  beforeAll(() => {
    installCanvasDomStubs();
  });

  it("nenhum serviço de mutação está registrado", () => {
    const container = document.createElement("div");
    document.body.appendChild(container);
    const viewer = new NavigatedViewer({ container });
    try {
      for (const svc of MUTATION_SERVICES) {
        expect(
          () => viewer.get(svc),
          `serviço de edição disponível: ${svc}`,
        ).toThrow();
      }
    } finally {
      viewer.destroy();
      container.remove();
    }
  });

  it("serviços de navegação presentes (pan/zoom/fit funcionais)", () => {
    const container = document.createElement("div");
    document.body.appendChild(container);
    const viewer = new NavigatedViewer({ container });
    try {
      for (const svc of NAVIGATION_SERVICES) {
        expect(
          viewer.get(svc),
          `serviço de navegação ausente: ${svc}`,
        ).toBeTruthy();
      }
    } finally {
      viewer.destroy();
      container.remove();
    }
  });
});
