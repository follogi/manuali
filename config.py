"""
Configurazione centrale per l'applicazione RAG Tutorial Generator.
Contiene tutte le impostazioni per LLM, RAG, tracking delle fonti, e viewer PDF.
"""

import os
from pathlib import Path

# ==============================================================================
# LLM Configuration
# ==============================================================================

# Ollama server configuration
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral"
OLLAMA_TIMEOUT = 60  # secondi

# Embedding model configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_PROVIDER = "huggingface"

# ==============================================================================
# RAG Configuration
# ==============================================================================

# Text splitting parameters
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

# Retrieval parameters
TOP_K_RETRIEVAL = 5
MIN_RELEVANCE_THRESHOLD = 0.3

# ==============================================================================
# Source Tracking & Verification
# ==============================================================================

# Enable/disable source tracking features
ENABLE_SOURCE_TRACKING = True
INCLUDE_PAGE_NUMBERS = True
INCLUDE_CHAPTER_EXTRACTION = True
INCLUDE_SIMILARITY_SCORES = True

# Citation verification settings
ENABLE_CITATION_VERIFICATION = True
CITATION_VERIFICATION_THRESHOLD = 0.80  # Minima similarità per citazione verificata
MAX_SOURCES_PER_TUTORIAL = 10

# ==============================================================================
# Paths Configuration
# ==============================================================================

# Base paths
BASE_DIR = Path(__file__).parent
CHROMA_DB_PATH = str(BASE_DIR / "chroma_db")
UPLOADS_PATH = str(BASE_DIR / "uploads")
STATIC_PATH = str(BASE_DIR / "static")
PDF_JS_PATH = str(BASE_DIR / "static" / "pdf.js")
EXPORT_PATH = str(BASE_DIR / "export")

# Crea le cartelle se non esistono
for path in [CHROMA_DB_PATH, UPLOADS_PATH, STATIC_PATH, EXPORT_PATH]:
    os.makedirs(path, exist_ok=True)

# ==============================================================================
# Server Configuration
# ==============================================================================

FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
GRADIO_PORT = 7860
DEBUG = False
ENABLE_CORS = True

# ==============================================================================
# PDF Viewer Configuration
# ==============================================================================

ENABLE_PDF_VIEWER = True
PDF_VIEWER_MODE = "pdfjs"  # "pdfjs" o "embed"
PDF_MAX_PAGES_CACHED = 50

# ==============================================================================
# File Upload Configuration
# ==============================================================================

# Supported file types
SUPPORTED_FILE_TYPES = [".pdf", ".docx", ".txt"]
MAX_FILE_SIZE_MB = 50
MAX_FILES_PER_UPLOAD = 10

# ==============================================================================
# Logging Configuration
# ==============================================================================

LOG_LEVEL = "INFO"
LOG_FILE = str(BASE_DIR / "app.log")
ENABLE_CITATION_AUDIT_LOG = True
CITATION_AUDIT_LOG = str(BASE_DIR / "citations_audit.log")

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ==============================================================================
# Tutorial Generation Configuration
# ==============================================================================

# Tutorial formatting
TUTORIAL_LANGUAGE = "italiano"
TUTORIAL_TONE = "professionale ma accessibile"

# JSON structure enforcement
ENFORCE_JSON_OUTPUT = True
MAX_TUTORIAL_LENGTH = 10000  # caratteri

# ==============================================================================
# Performance Configuration
# ==============================================================================

# Caching
ENABLE_EMBEDDING_CACHE = True
ENABLE_QUERY_CACHE = True
CACHE_TTL_SECONDS = 3600  # 1 ora

# Async processing
ENABLE_ASYNC_INDEXING = False  # Set to True for large documents

# ==============================================================================
# UI Configuration
# ==============================================================================

# Gradio theme
GRADIO_THEME = "default"

# Interface titles
APP_TITLE = "Tutorial Generator RAG"
APP_DESCRIPTION = """
Genera tutorial passo-passo da manuali tecnici usando AI locale.
Upload documenti, cerca informazioni, e genera tutorial con citazioni verificate.
"""

# Tab names
TAB_UPLOAD = "📤 Carica Documenti"
TAB_SEARCH = "🔍 Cerca nel Manuale"
TAB_GENERATE = "🤖 Genera Tutorial"
TAB_VIEWER = "📄 Viewer PDF"
TAB_REPORT = "📊 Report Citazioni"

# ==============================================================================
# Error Messages (Italiano)
# ==============================================================================

ERROR_MESSAGES = {
    "no_ollama": "❌ Ollama non è in esecuzione. Avvia 'ollama serve' in un terminale.",
    "file_too_large": f"❌ File troppo grande. Dimensione massima: {MAX_FILE_SIZE_MB}MB",
    "unsupported_format": f"❌ Formato non supportato. Formati accettati: {', '.join(SUPPORTED_FILE_TYPES)}",
    "no_documents": "⚠️ Nessun documento caricato. Carica almeno un documento prima di continuare.",
    "query_empty": "⚠️ Query vuota. Inserisci una domanda.",
    "generation_failed": "❌ Generazione fallita. Riprova o controlla i log.",
    "pdf_not_found": "❌ File PDF non trovato.",
    "citation_verification_failed": "⚠️ Verifica citazioni fallita, ma il tutorial è stato generato."
}

# ==============================================================================
# Success Messages (Italiano)
# ==============================================================================

SUCCESS_MESSAGES = {
    "upload_complete": "✅ Documenti caricati e indicizzati con successo!",
    "search_complete": "✅ Ricerca completata.",
    "tutorial_generated": "✅ Tutorial generato con successo!",
    "citation_verified": "✅ Citazioni verificate.",
    "export_complete": "✅ Export completato."
}

# ==============================================================================
# Development Configuration
# ==============================================================================

# Debug flags
DEBUG_RAG_ENGINE = False
DEBUG_LLM_HANDLER = False
DEBUG_CITATION_VERIFIER = False

# Verbose output
VERBOSE_LOGGING = False

# ==============================================================================
# Metadata Configuration
# ==============================================================================

# Metadata fields to extract from documents
METADATA_FIELDS = [
    "source_file",
    "chunk_id",
    "page_number",
    "character_offset",
    "upload_timestamp",
    "file_size",
    "file_type"
]

# ==============================================================================
# Tutorial Template Configuration
# ==============================================================================

TUTORIAL_JSON_SCHEMA = {
    "titolo": "str",
    "problema": "str",
    "prerequisiti": "list[dict]",
    "steps": "list[dict]",
    "note": "list[dict]",
    "avvertimenti": "list[dict]",
    "tempo_stimato": "str",
    "riferimenti": "list[dict]"
}

# ==============================================================================
# Export Configuration
# ==============================================================================

EXPORT_FORMATS = ["markdown", "html", "pdf", "json"]
DEFAULT_EXPORT_FORMAT = "markdown"

# PDF export settings
PDF_EXPORT_FONT = "DejaVuSans"
PDF_EXPORT_FONT_SIZE = 11
PDF_EXPORT_MARGIN = 20

# ==============================================================================
# Version Info
# ==============================================================================

APP_VERSION = "1.0.0"
BUILD_DATE = "2025-11-01"
AUTHOR = "Claude Code"

if __name__ == "__main__":
    print("=" * 70)
    print(f"RAG Tutorial Generator Configuration")
    print("=" * 70)
    print(f"Version: {APP_VERSION}")
    print(f"Build Date: {BUILD_DATE}")
    print()
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    print(f"Model: {OLLAMA_MODEL}")
    print(f"Embedding: {EMBEDDING_MODEL}")
    print(f"Chunk Size: {CHUNK_SIZE}")
    print(f"Top-K Retrieval: {TOP_K_RETRIEVAL}")
    print(f"Citations Verification: {'Enabled' if ENABLE_CITATION_VERIFICATION else 'Disabled'}")
    print(f"PDF Viewer: {'Enabled' if ENABLE_PDF_VIEWER else 'Disabled'}")
    print()
    print(f"Paths:")
    print(f"  - Chroma DB: {CHROMA_DB_PATH}")
    print(f"  - Uploads: {UPLOADS_PATH}")
    print(f"  - Export: {EXPORT_PATH}")
    print(f"  - Logs: {LOG_FILE}")
    print("=" * 70)
