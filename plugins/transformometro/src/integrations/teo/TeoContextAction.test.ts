import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = dirname(fileURLToPath(import.meta.url));

const action = readFileSync(join(root, "TeoContextAction.tsx"), "utf8");
const manual = readFileSync(
  join(root, "../../content/userManualContent.ts"),
  "utf8",
);

describe("TÉO Portal Context — botão sem fluxo manual de cópia", () => {
  it("clique principal não escreve no clipboard", () => {
    const clickBlock = action.match(
      /function handleClick\(\) \{[\s\S]*?\n  \}/,
    );
    expect(clickBlock).not.toBeNull();
    expect(clickBlock![0]).not.toMatch(/clipboard/);
    expect(clickBlock![0]).toMatch(/variant:\s*"info"/);
    expect(clickBlock![0]).toMatch(/notice\(/);
  });

  it("aviso informa que o contexto já é compartilhado e orienta a conversa", () => {
    expect(action).toMatch(/O TÉO já sabe onde você está/);
    expect(action).toMatch(/compartilhado automaticamente/);
    expect(action).toMatch(/analise este processo/);
    // Persistente: o usuário precisa ler e pode usar o fallback.
    expect(action).toMatch(/autoDismissMs:\s*null/);
  });

  it("fallback 'Copiar contexto' é explícito e dentro do aviso", () => {
    expect(action).toMatch(/label:\s*"Copiar contexto"/);
    expect(action).toMatch(
      /async function copyContextFallback\(\)[\s\S]*clipboard\.writeText\(buildTeoContextClipboardText\(context\)\)/,
    );
  });

  it("continua oculto fora do workspace de processo", () => {
    expect(action).toMatch(/if \(!context\.process_id\) return null/);
  });

  it("manual do usuário não ensina mais copiar/colar como fluxo principal", () => {
    const teoSection = manual.match(/id: "teo",[\s\S]*?\],\n    \},/);
    expect(teoSection).not.toBeNull();
    expect(teoSection![0]).toMatch(/compartilha automaticamente/);
    expect(teoSection![0]).not.toMatch(/Cole o contexto no ChatGPT\./);
    // Fallback documentado como alternativa explícita, não jornada.
    expect(teoSection![0]).toMatch(/Copiar contexto.*alternativa explícita/);
  });
});
