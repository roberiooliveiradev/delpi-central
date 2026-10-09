/**
 * ELK Web Worker — entry canônico elkjs (P5 §5/§9).
 *
 * `elk-worker.min.js` auto-instala `self.onmessage` com o dispatcher
 * nativo do elk (`{cmd:'layout'|'register'|...}`) quando avaliado em
 * contexto de worker real. O protocolo request/response é propriedade
 * do `elk-api.js` (PromisedWorker) — este arquivo existe apenas para
 * produzir o chunk de worker dedicado via `new URL(..., import.meta.url)`.
 */
import "elkjs/lib/elk-worker.min.js";
