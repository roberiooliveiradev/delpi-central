"""Architecture / Abstraction Gate tests for C3-MEDIA-FOUNDATION-01."""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from app.domain.media.model import (
    MediaObservation,
    MediaRef,
    MediaRegion,
    MediaTimeRange,
)


FORBIDDEN_IMPORT_FRAGMENTS = (
    "openai",
    "anthropic",
    "gemini",
    "google.generativeai",
    "google.cloud.vision",
    "azure",
    "boto3",
    "rekognition",
    "ollama",
    "openrouter",
    "flask",
    "fastapi",
    "sqlalchemy",
    "httpx",
    "requests",
    "chromadb",
    "faiss",
    "langchain",
    "pinecone",
    "qdrant",
    "pgvector",
    "kafka",
    "celery",
    "cv2",
    "opencv",
    "ffmpeg",
    "pytesseract",
    "speech_recognition",
    "pyttsx3",
    "whisper",
    "minha_delpi",
    "minha-delpi",
)

FORBIDDEN_TYPE_NAMES = (
    "MediaEngine",
    "MultimodalEngine",
    "VisionEngine",
    "VisionRouter",
    "MediaRouter",
    "MultimodalRouter",
    "ProviderRouter",
    "MediaRegistry",
    "MediaPipeline",
    "VisionPipeline",
    "GenericObservationEngine",
    "MediaRepository",
    "MediaStore",
    "MediaService",
    "VisionService",
    "CaptureRuntime",
    "CameraRuntime",
    "MicrophoneRuntime",
    "VideoRuntime",
    "ScreenShareRuntime",
    "SpeechToTextPort",
    "TextToSpeechPort",
    "VisionModelPort",
    "BiometricIdentifier",
    "FaceRecognizer",
    "FaceVerification",
    "SpeakerRecognizer",
    "VoiceBiometric",
    "LivenessDetector",
    "AntiSpoofDetector",
    "PersonIdentifier",
    "EmotionClassifier",
    "EmploymentScorer",
    "EntityMatcher",
    "ObjectIdentityResolver",
    "QualityApprovalEngine",
    "QualityDispositionService",
    "KnowledgeRetrievalPort",
    "VectorStore",
    "RAGService",
    "ModelRouter",
    "ConversationEngine",
    "ChatEngine",
    "MediaEvidenceRef",
    "VisionEvidenceRef",
    "MultimodalEvidenceRef",
    "ImageSourceRef",
    "VideoSourceRef",
    "AudioSourceRef",
)

FORBIDDEN_FIELD_NAMES = {
    "file_path",
    "url",
    "bucket_path",
    "provider_media_id",
    "camera_id",
    "codec",
    "file_extension",
    "is_authorized",
    "can_execute",
    "permission_granted",
    "access_token",
    "api_key",
    "password",
    "client_secret",
    "credential",
    "chain_of_thought",
    "cot",
    "private_reasoning",
    "hidden_reasoning",
    "reasoning_trace",
    "scratchpad",
    "face_id",
    "voiceprint",
    "biometric_template",
    "emotion",
    "personality",
    "employment_score",
    "tool_call",
    "function_call",
    "plc_command",
    "cnc_command",
    "robot_command",
    "machine_command",
}

APP_ROOT = Path(__file__).resolve().parents[1] / "app"


def _python_files(*relative: str) -> list[Path]:
    root = APP_ROOT.joinpath(*relative)
    return [path for path in root.rglob("*.py") if path.name != "__pycache__"]


def test_media_domain_has_no_provider_or_runtime_imports():
    for path in _python_files("domain", "media"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.lower() for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [(node.module or "").lower()]
            else:
                continue
            joined = " ".join(names)
            for fragment in FORBIDDEN_IMPORT_FRAGMENTS:
                assert fragment not in joined, f"{path} imports {fragment}"


def test_no_speculative_media_or_biometric_abstractions():
    for path in APP_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                assert node.name not in FORBIDDEN_TYPE_NAMES, path


def test_media_model_fields_exclude_mechanics_and_authority():
    for cls in (MediaRef, MediaRegion, MediaTimeRange, MediaObservation):
        for field_ in fields(cls):
            assert field_.name not in FORBIDDEN_FIELD_NAMES, (
                f"{cls.__name__}.{field_.name} must not exist"
            )


def test_media_domain_has_no_application_or_infra_leakage():
    for path in _python_files("domain", "media"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
            elif isinstance(node, ast.Import):
                module = " ".join(a.name for a in node.names)
            else:
                continue
            assert "infrastructure" not in module, path
            assert "application" not in module, path
