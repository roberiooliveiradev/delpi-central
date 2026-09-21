import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function listSourceFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    if (entry === "node_modules" || entry === "dist" || entry === "test-stubs") continue;
    const full = path.join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      out.push(...listSourceFiles(full));
      continue;
    }
    if (/\.(test|spec)\./.test(entry)) continue;
    if (/\.(tsx?|jsx?|css)$/.test(entry)) out.push(full);
  }
  return out;
}

describe("C1 independence and media safety", () => {
  const sources = listSourceFiles(path.join(root, "src"));

  it("has no Chat runtime dependency", () => {
    const forbidden = [
      "minha-delpi-chat",
      "minha-delpi-ai-api",
      "minha_delpi_chat",
      "minha_delpi_ai",
    ];
    for (const file of sources) {
      const text = readFileSync(file, "utf8");
      for (const term of forbidden) {
        expect(text.includes(term), `${file} contains ${term}`).toBe(false);
      }
    }
  });

  it("does not auto-start media capture APIs", () => {
    const forbidden = [
      "getUserMedia",
      "MediaRecorder",
      "getDisplayMedia",
      "SpeechRecognition",
      "webkitSpeechRecognition",
      "navigator.mediaDevices",
    ];
    for (const file of sources) {
      const text = readFileSync(file, "utf8");
      for (const term of forbidden) {
        expect(text.includes(term), `${file} contains ${term}`).toBe(false);
      }
    }
  });

  it("does not persist or decode tokens locally", () => {
    for (const file of sources) {
      if (file.endsWith(".test.ts") || file.endsWith(".test.tsx")) continue;
      const text = readFileSync(file, "utf8");
      expect(text.includes("localStorage")).toBe(false);
      expect(text.includes("sessionStorage")).toBe(false);
      expect(text.includes("indexedDB")).toBe(false);
      expect(text.includes("caches.")).toBe(false);
      expect(text.includes("serviceWorker")).toBe(false);
      expect(text.includes("jwt.decode")).toBe(false);
      expect(text.includes("atob(")).toBe(false);
    }
  });
});
