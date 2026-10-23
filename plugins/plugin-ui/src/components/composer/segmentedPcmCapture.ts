/**
 * Segmented PCM capture — the incremental mode of the composer audio
 * recorder family (VD-F06). Same mic/permission/graph lifecycle as
 * `useLocalAudioRecorder`, but instead of one opaque MediaRecorder
 * blob it slices real PCM (AudioWorklet) into self-contained WAV
 * segments — each independently transcribable while speech continues.
 *
 * Delivers real PCM only: no fabricated frames, no timer-driven text.
 * Pause suspends the audio context honestly (no frames are captured
 * while suspended); `stop` flushes the trailing slice so the last
 * words are not lost; `abort` closes without flushing (cancel).
 */

import { pcmToWavBlob } from "./pcmWav";

export type SegmentedPcmCapture = {
  /** True when AudioWorklet + getUserMedia exist in this context. */
  readonly supported: boolean;
  start(onSegment: (blob: Blob, durationMs: number) => void): Promise<void>;
  pause(): void;
  resume(): void;
  stop(): void;
  abort(): void;
};

export type SegmentedPcmCaptureOptions = {
  /** Slice length in ms (default 4000). */
  segmentMs?: number;
  /** WAV output sample rate (default 16000). */
  targetRate?: number;
  /** Discard trailing slices shorter than this (default 300ms). */
  minSegmentMs?: number;
  /** Real RMS amplitude samples for the waveform (0..1). */
  onLevel?: (level: number) => void;
};

const WORKLET_SOURCE = `
class PcmCaptureProcessor extends AudioWorkletProcessor {
  process(inputs) {
    const input = inputs[0];
    if (input && input[0] && input[0].length > 0) {
      this.port.postMessage(input[0].slice(0));
    }
    return true;
  }
}
registerProcessor('delia-pcm-capture', PcmCaptureProcessor);
`;

/** Feature check owned by plugin-ui — consumers ask, never probe. */
export function isSegmentedPcmCaptureSupported(): boolean {
  return (
    typeof navigator !== "undefined" &&
    typeof navigator.mediaDevices?.getUserMedia === "function" &&
    typeof AudioContext !== "undefined" &&
    typeof AudioWorkletNode !== "undefined"
  );
}

export function createSegmentedPcmCapture(
  options: SegmentedPcmCaptureOptions = {},
): SegmentedPcmCapture {
  const segmentMs = options.segmentMs ?? 4000;
  const targetRate = options.targetRate ?? 16000;
  const minSegmentMs = options.minSegmentMs ?? 300;

  const supported = isSegmentedPcmCaptureSupported();

  let stream: MediaStream | null = null;
  let ctx: AudioContext | null = null;
  let node: AudioWorkletNode | null = null;
  let workletUrl: string | null = null;
  let chunks: Float32Array[] = [];
  let chunkFrames = 0;
  let segmentStartedAt = 0;
  let closed = true;
  let emit: ((blob: Blob, durationMs: number) => void) | null = null;

  const sourceRate = () => ctx?.sampleRate ?? targetRate;

  const flushSegment = () => {
    if (!ctx || chunkFrames === 0 || !emit) {
      chunks = [];
      chunkFrames = 0;
      return;
    }
    const durationMs = (chunkFrames / sourceRate()) * 1000;
    if (durationMs >= minSegmentMs) {
      const blob = pcmToWavBlob(chunks, {
        sourceRate: sourceRate(),
        targetRate,
      });
      emit(blob, durationMs);
    }
    chunks = [];
    chunkFrames = 0;
    segmentStartedAt = performance.now();
  };

  const teardown = () => {
    closed = true;
    emit = null;
    if (node) {
      try {
        node.port.onmessage = null;
        node.disconnect();
      } catch {
        /* already closed */
      }
      node = null;
    }
    if (ctx) {
      const c = ctx;
      ctx = null;
      void c.close().catch(() => undefined);
    }
    if (stream) {
      for (const track of stream.getTracks()) track.stop();
      stream = null;
    }
    if (workletUrl) {
      URL.revokeObjectURL(workletUrl);
      workletUrl = null;
    }
    chunks = [];
    chunkFrames = 0;
  };

  return {
    supported,

    async start(onSegment) {
      if (!supported) {
        throw new Error("segmented capture unsupported");
      }
      teardown();
      closed = false;
      emit = onSegment;
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
        video: false,
      });
      ctx = new AudioContext();
      workletUrl = URL.createObjectURL(
        new Blob([WORKLET_SOURCE], { type: "application/javascript" }),
      );
      await ctx.audioWorklet.addModule(workletUrl);
      const source = ctx.createMediaStreamSource(stream);
      node = new AudioWorkletNode(ctx, "delia-pcm-capture");
      node.port.onmessage = (event: MessageEvent) => {
        if (closed || !(event.data instanceof Float32Array)) return;
        const frames = event.data as Float32Array;
        chunks.push(frames);
        chunkFrames += frames.length;
        let sum = 0;
        for (let i = 0; i < frames.length; i += 1) {
          sum += frames[i] * frames[i];
        }
        const rms = Math.sqrt(sum / frames.length);
        options.onLevel?.(Math.min(1, Math.max(0.06, rms * 4)));
        if (performance.now() - segmentStartedAt >= segmentMs) {
          flushSegment();
        }
      };
      source.connect(node);
      node.connect(ctx.destination); // required for the graph to pull
      segmentStartedAt = performance.now();
    },

    pause() {
      if (!closed && ctx?.state === "running") {
        void ctx.suspend();
      }
    },

    resume() {
      if (!closed && ctx?.state === "suspended") {
        segmentStartedAt = performance.now();
        void ctx.resume();
      }
    },

    stop() {
      if (closed) return;
      flushSegment();
      teardown();
    },

    abort() {
      if (closed) return;
      teardown();
    },
  };
}
