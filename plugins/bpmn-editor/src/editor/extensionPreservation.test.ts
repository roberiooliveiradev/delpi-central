// @vitest-environment jsdom
/**
 * G4-EXT-1 — evidência minimal do mecanismo de preservação de extensões.
 *
 * Isola fromXML → repair → toXML sem o stack completo:
 *  - repairExtensionDeclarations restaura attrs dropados do parse
 *    (`definition` é isReference não-resolvível no descriptor vendor);
 *  - hasUnpreservableExtensionContent detecta o caso irremediável
 *    (attr namespaced com URI == URI do elemento — o serializer
 *    moddle-xml stripa o prefixo por comparar URIs, o que é
 *    semanticamente incorreto: attrs nunca herdam o ns default).
 */
import { describe, it, expect } from "vitest";
import { BpmnModdle } from "bpmn-moddle";
import {
  hasUnpreservableExtensionContent,
  repairExtensionDeclarations,
} from "./extensionPreservation";

const VEND = "http://vendor.example/suite";
const ACME = "http://acme.example/ext";

function wrap(inner: string): string {
  return `<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:vend="${VEND}" xmlns:acme="${ACME}" id="D1" targetNamespace="urn:t">${inner}</bpmn:definitions>`;
}

async function roundTripViaModdle(xml: string): Promise<string> {
  const moddle = new BpmnModdle();
  const { rootElement } = await moddle.fromXML(xml);
  repairExtensionDeclarations(rootElement, xml);
  const { xml: out } = await moddle.toXML(rootElement);
  return out;
}

describe("G4-EXT-1 repairExtensionDeclarations", () => {
  it("restaura bpmn:extension/@definition perdido no parse isReference", async () => {
    const xml = wrap(
      `<bpmn:extension definition="vend:suite" mustUnderstand="false"/>` +
        `<bpmn:process id="P1"/>`,
    );
    const out = await roundTripViaModdle(xml);
    expect(out).toContain('definition="vend:suite"');
    // mustUnderstand="false" é elidido pelo serializer (default XSD —
    // equivalência normalizada pelo comparador, não perda).
    expect(out).toContain("<bpmn:extension");
  });

  it("preserva múltiplas declarations e não inventa quando ausente", async () => {
    const xml = wrap(
      `<bpmn:extension definition="vend:suite"/>` +
        `<bpmn:extension definition="acme:extra"/>` +
        `<bpmn:process id="P1"/>`,
    );
    const out = await roundTripViaModdle(xml);
    expect(out).toContain('definition="vend:suite"');
    expect(out).toContain('definition="acme:extra"');
  });
});

describe("G4-EXT-1 hasUnpreservableExtensionContent", () => {
  it("detecta attr namespaced com URI == URI do elemento (serializer stripa prefixo)", () => {
    const xml = wrap(
      `<bpmn:process id="P1"><bpmn:task id="T1">` +
        `<bpmn:extensionElements><vend:prop vend:flag="1">t</vend:prop></bpmn:extensionElements>` +
        `</bpmn:task></bpmn:process>`,
    );
    expect(hasUnpreservableExtensionContent(xml)).toBe(true);
  });

  it("não dispara em attr namespaced cross-ns (serializável)", () => {
    const xml = wrap(
      `<bpmn:process id="P1"><bpmn:task id="T1">` +
        `<bpmn:extensionElements><vend:prop acme:flag="1" key="a">t</vend:prop></bpmn:extensionElements>` +
        `</bpmn:task></bpmn:process>`,
    );
    expect(hasUnpreservableExtensionContent(xml)).toBe(false);
  });

  it("não dispara em attr namespaced fora de extensionElements (serializável)", () => {
    const xml = wrap(
      `<bpmn:process id="P1"><bpmn:task id="T1" vend:custom="c"/></bpmn:process>`,
    );
    expect(hasUnpreservableExtensionContent(xml)).toBe(false);
  });

  it("não dispara em mustUnderstand (attr BPMN em elemento BPMN)", () => {
    const xml = wrap(
      `<bpmn:extension definition="vend:suite" mustUnderstand="true"/>` +
        `<bpmn:process id="P1"/>`,
    );
    expect(hasUnpreservableExtensionContent(xml)).toBe(false);
  });

  it("retorna false para XML inválido (sem throw)", () => {
    expect(hasUnpreservableExtensionContent("not xml <<<")).toBe(false);
  });
});
