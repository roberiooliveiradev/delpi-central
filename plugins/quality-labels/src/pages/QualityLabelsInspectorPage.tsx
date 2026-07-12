import { useEffect, useRef, useState } from "react";
import {
  Eraser,
  Loader2,
  Lock,
  PenLine,
  Save,
  Upload,
  UserCheck,
} from "lucide-react";

import {
  fetchMySignatureBlob,
  getMyInspector,
  saveMyInspector,
  uploadMySignature,
} from "../api/qualityLabelsApi";
import { QlNativeTextField } from "../components/qlFormFields";

const CANVAS_WIDTH = 640;
const CANVAS_HEIGHT = 220;

export function QualityLabelsInspectorPage() {
  const [displayName, setDisplayName] = useState("");
  const [roleTitle, setRoleTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingSignature, setSavingSignature] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [hasDrawing, setHasDrawing] = useState(false);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const lastPoint = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    getMyInspector(controller.signal)
      .then((data) => {
        setDisplayName(data.displayName ?? "");
        setRoleTitle(data.roleTitle ?? "");
        if (data.hasSignature) {
          void loadPreview(controller.signal);
        }
      })
      .catch((err) => {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setError(err instanceof Error ? err.message : "Erro ao carregar o inspetor.");
        }
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadPreview(signal?: AbortSignal) {
    try {
      const blob = await fetchMySignatureBlob(signal);
      setPreview((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return URL.createObjectURL(blob);
      });
    } catch {
      // sem assinatura ainda
    }
  }

  function getContext(): CanvasRenderingContext2D | null {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.lineWidth = 2.4;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#0f172a";
    return ctx;
  }

  function pointFromEvent(event: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    return {
      x: ((event.clientX - rect.left) / rect.width) * canvas.width,
      y: ((event.clientY - rect.top) / rect.height) * canvas.height,
    };
  }

  function handlePointerDown(event: React.PointerEvent<HTMLCanvasElement>) {
    event.preventDefault();
    canvasRef.current?.setPointerCapture(event.pointerId);
    drawing.current = true;
    lastPoint.current = pointFromEvent(event);
  }

  function handlePointerMove(event: React.PointerEvent<HTMLCanvasElement>) {
    if (!drawing.current) return;
    const ctx = getContext();
    const point = pointFromEvent(event);
    if (ctx && lastPoint.current) {
      ctx.beginPath();
      ctx.moveTo(lastPoint.current.x, lastPoint.current.y);
      ctx.lineTo(point.x, point.y);
      ctx.stroke();
      setHasDrawing(true);
    }
    lastPoint.current = point;
  }

  function handlePointerUp() {
    drawing.current = false;
    lastPoint.current = null;
  }

  function clearCanvas() {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (canvas && ctx) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      setHasDrawing(false);
    }
  }

  async function handleSaveProfile() {
    if (!displayName.trim()) {
      setError("Informe o nome do inspetor.");
      return;
    }
    setSavingProfile(true);
    setError(null);
    setSuccess(null);
    try {
      await saveMyInspector({
        displayName: displayName.trim(),
        roleTitle: roleTitle.trim() || null,
      });
      setSuccess("Perfil do inspetor salvo.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar o perfil.");
    } finally {
      setSavingProfile(false);
    }
  }

  async function uploadBlob(blob: Blob) {
    setSavingSignature(true);
    setError(null);
    setSuccess(null);
    try {
      await uploadMySignature(blob);
      setSuccess("Assinatura registrada com sucesso.");
      await loadPreview();
      clearCanvas();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao registrar a assinatura.");
    } finally {
      setSavingSignature(false);
    }
  }

  function handleSaveDrawing() {
    const canvas = canvasRef.current;
    if (!canvas || !hasDrawing) {
      setError("Desenhe a assinatura antes de salvar.");
      return;
    }
    canvas.toBlob((blob) => {
      if (blob) void uploadBlob(blob);
    }, "image/png");
  }

  function handleUploadFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const img = new Image();
    const reader = new FileReader();
    reader.onload = () => {
      img.onload = () => {
        // Normaliza para PNG com fundo transparente, mantendo proporção.
        const canvas = document.createElement("canvas");
        canvas.width = CANVAS_WIDTH;
        canvas.height = CANVAS_HEIGHT;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;
        const ratio = Math.min(canvas.width / img.width, canvas.height / img.height);
        const w = img.width * ratio;
        const h = img.height * ratio;
        ctx.drawImage(img, (canvas.width - w) / 2, (canvas.height - h) / 2, w, h);
        canvas.toBlob((blob) => {
          if (blob) void uploadBlob(blob);
        }, "image/png");
      };
      img.src = reader.result as string;
    };
    reader.readAsDataURL(file);
  }

  return (
    <>
      {error && <div className="ql-state ql-state--error"><p>{error}</p></div>}
      {success && <div className="ql-state ql-state--success"><p>{success}</p></div>}

      <div className="ql-info-note">
        <Lock className="ql-icon" />
        <span>
          Este perfil e a assinatura estão vinculados ao seu login na Minha Delpi.
          Apenas você pode editá-los, e a assinatura usada nos certificados que você
          emitir é sempre a sua.
        </span>
      </div>

      <section className="ql-card ql-card--pad">
        <div className="ql-card__accent" />
        <div className="ql-card__head">
          <UserCheck className="ql-icon" />
          <div>
            <h2 className="ql-card__title">Perfil do inspetor</h2>
            <p className="ql-card__subtitle">
              Nome e cargo usados nos certificados de qualidade que você emitir.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="ql-state"><p><Loader2 className="ql-icon ql-spin" /> Carregando...</p></div>
        ) : (
          <>
            <div className="ql-field-row">
              <QlNativeTextField
                id="ql-inspector-display-name"
                label="Nome do inspetor"
                value={displayName}
                onChange={setDisplayName}
                placeholder="Nome completo"
                controlClassName="ql-input"
              />
              <QlNativeTextField
                id="ql-inspector-role-title"
                label="Cargo (opcional)"
                value={roleTitle}
                onChange={setRoleTitle}
                placeholder="Ex.: Inspetor da Qualidade"
                controlClassName="ql-input"
              />
            </div>
            <div className="ql-form__actions">
              <button
                type="button"
                className="ql-btn ql-btn--primary"
                onClick={() => void handleSaveProfile()}
                disabled={savingProfile}
              >
                {savingProfile ? <Loader2 className="ql-icon ql-spin" /> : <Save className="ql-icon" />}
                Salvar perfil
              </button>
            </div>
          </>
        )}
      </section>

      <section className="ql-card ql-card--pad">
        <div className="ql-card__accent" />
        <div className="ql-card__head">
          <PenLine className="ql-icon" />
          <div>
            <h2 className="ql-card__title">Assinatura</h2>
            <p className="ql-card__subtitle">
              Desenhe com o mouse ou caneta/tablet, ou envie uma imagem da sua assinatura.
            </p>
          </div>
        </div>

        {preview && (
          <div className="ql-signature-preview">
            <span className="ql-label-text">Assinatura atual</span>
            <img src={preview} alt="Assinatura atual do inspetor" />
          </div>
        )}

        <div className="ql-signature-pad">
          <canvas
            ref={canvasRef}
            width={CANVAS_WIDTH}
            height={CANVAS_HEIGHT}
            className="ql-signature-canvas"
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerLeave={handlePointerUp}
          />
          <p className="ql-signature-hint">Assine dentro da área acima</p>
        </div>

        <div className="ql-signature-actions">
          <div className="ql-signature-actions__group">
            <button type="button" className="ql-btn ql-btn--ghost" onClick={clearCanvas}>
              <Eraser className="ql-icon" /> Limpar
            </button>
            <button
              type="button"
              className="ql-btn ql-btn--primary"
              onClick={handleSaveDrawing}
              disabled={savingSignature}
            >
              {savingSignature ? (
                <Loader2 className="ql-icon ql-spin" />
              ) : (
                <Save className="ql-icon" />
              )}
              Salvar assinatura
            </button>
          </div>
          <span className="ql-signature-actions__sep">ou</span>
          <label className="ql-btn ql-btn--ghost ql-upload-btn">
            <Upload className="ql-icon" /> Enviar imagem
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={handleUploadFile}
              hidden
            />
          </label>
        </div>
      </section>
    </>
  );
}
