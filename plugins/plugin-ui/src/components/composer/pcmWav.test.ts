import { describe, expect, it } from "vitest";
import { pcmToWavBlob } from "./pcmWav";

describe("pcmToWavBlob", () => {
  it("produces a valid mono 16-bit RIFF/WAVE header", async () => {
    const samples = new Float32Array(16000).fill(0.5); // 1s @16kHz
    const blob = pcmToWavBlob([samples], {
      sourceRate: 16000,
      targetRate: 16000,
    });
    expect(blob.type).toBe("audio/wav");
    const buf = await blob.arrayBuffer();
    const view = new DataView(buf);
    const ascii = (o: number, n: number) =>
      String.fromCharCode(...new Uint8Array(buf, o, n));
    expect(ascii(0, 4)).toBe("RIFF");
    expect(ascii(8, 4)).toBe("WAVE");
    expect(ascii(12, 4)).toBe("fmt ");
    expect(view.getUint16(20, true)).toBe(1); // PCM
    expect(view.getUint16(22, true)).toBe(1); // mono
    expect(view.getUint32(24, true)).toBe(16000);
    expect(view.getUint16(34, true)).toBe(16);
    expect(ascii(36, 4)).toBe("data");
    expect(view.getUint32(40, true)).toBe(16000 * 2);
    expect(buf.byteLength).toBe(44 + 16000 * 2);
  });

  it("downsamples to the target rate", async () => {
    const samples = new Float32Array(48000); // 1s @48kHz
    const blob = pcmToWavBlob([samples], { sourceRate: 48000 });
    const buf = await blob.arrayBuffer();
    const view = new DataView(buf);
    expect(view.getUint32(24, true)).toBe(16000);
    expect(view.getUint32(40, true)).toBe(16000 * 2);
  });

  it("merges multiple chunks into one segment", async () => {
    const a = new Float32Array(8000);
    const b = new Float32Array(8000);
    const blob = pcmToWavBlob([a, b], { sourceRate: 16000 });
    const buf = await blob.arrayBuffer();
    expect(new DataView(buf).getUint32(40, true)).toBe(16000 * 2);
  });
});
