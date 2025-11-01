#!/usr/bin/env python3
"""
Tutorial Generator RAG - Entry Point
Avvia Flask + Gradio per applicazione completa.

Usage:
    python main.py

Prerequisites:
    - Ollama deve essere in esecuzione: ollama serve
    - Modello Mistral scaricato: ollama pull mistral
"""

import sys
import logging
import argparse

try:
    from flask import Flask
    from flask_cors import CORS
except ImportError:
    print("Error: Flask not installed. Install with: pip install flask flask-cors")
    sys.exit(1)

import config
from rag_engine import RAGEngine
from llm_handler import TutorialGenerator
from pdf_viewer import PDFViewer
from gradio_ui import GradioUI

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def print_banner():
    """Stampa banner applicazione."""
    banner = f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║           📚 TUTORIAL GENERATOR RAG                           ║
    ║                                                               ║
    ║           Genera tutorial da manuali con AI locale           ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝

    Version: {config.APP_VERSION}
    Build:   {config.BUILD_DATE}
    Author:  {config.AUTHOR}

    Stack:
    - LLM:       Ollama + {config.OLLAMA_MODEL}
    - Embedding: {config.EMBEDDING_MODEL}
    - RAG:       LlamaIndex + Chroma
    - UI:        Gradio
    - Backend:   Flask

    """
    print(banner)


def check_prerequisites() -> bool:
    """
    Verifica prerequisiti applicazione.

    Returns:
        True se tutto OK, False se mancano prerequisiti
    """
    logger.info("Verifica prerequisiti...")

    all_ok = True

    # Check Ollama
    try:
        import ollama
        ollama.list()
        logger.info("✓ Ollama connesso")
    except Exception as e:
        logger.error(f"✗ Ollama non raggiungibile: {e}")
        logger.error("  Avvia Ollama: 'ollama serve'")
        all_ok = False

    # Check cartelle
    import os
    for path in [config.CHROMA_DB_PATH, config.UPLOADS_PATH, config.EXPORT_PATH]:
        if not os.path.exists(path):
            logger.warning(f"⚠ Cartella {path} non esiste, creazione...")
            os.makedirs(path, exist_ok=True)

    logger.info("✓ Cartelle verificate")

    return all_ok


def create_flask_app() -> Flask:
    """
    Crea e configura Flask app.

    Returns:
        Flask app configurata
    """
    app = Flask(__name__)

    # CORS
    if config.ENABLE_CORS:
        CORS(app)

    # Configurazione
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE_MB * 1024 * 1024

    logger.info("Flask app creata")

    return app


def main():
    """Entry point principale."""
    # Parse args
    parser = argparse.ArgumentParser(description="Tutorial Generator RAG")
    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help='Skip prerequisiti checks'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=config.GRADIO_PORT,
        help=f'Gradio port (default: {config.GRADIO_PORT})'
    )
    parser.add_argument(
        '--share',
        action='store_true',
        help='Create public Gradio share link'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )

    args = parser.parse_args()

    # Banner
    print_banner()

    # Check prerequisiti
    if not args.skip_checks:
        if not check_prerequisites():
            logger.error("\n❌ Prerequisiti mancanti. Correggi gli errori e riprova.")
            logger.error("\nSetup richiesto:")
            logger.error("1. Installa Ollama: https://ollama.ai")
            logger.error("2. Scarica modello: ollama pull mistral")
            logger.error("3. Avvia Ollama: ollama serve")
            logger.error("\nPer saltare il check: python main.py --skip-checks")
            sys.exit(1)

    logger.info("\n" + "="*70)
    logger.info("Inizializzazione componenti...")
    logger.info("="*70)

    # Inizializza componenti
    try:
        logger.info("1/4 Inizializzazione RAG Engine...")
        rag_engine = RAGEngine()
        logger.info("    ✓ RAG Engine pronto")

        logger.info("2/4 Inizializzazione Tutorial Generator...")
        tutorial_generator = TutorialGenerator()
        logger.info("    ✓ Tutorial Generator pronto")

        logger.info("3/4 Inizializzazione Flask app...")
        flask_app = create_flask_app()

        # Registra PDF viewer routes
        pdf_viewer = PDFViewer()
        pdf_viewer.create_flask_routes(flask_app)
        logger.info("    ✓ Flask app pronta")

        logger.info("4/4 Inizializzazione Gradio UI...")
        gradio_ui = GradioUI(rag_engine, tutorial_generator)
        interface = gradio_ui.create_interface()
        logger.info("    ✓ Gradio UI pronta")

    except Exception as e:
        logger.error(f"\n❌ Errore inizializzazione: {e}")
        logger.exception("Stack trace:")
        sys.exit(1)

    # Monta Gradio su Flask
    try:
        logger.info("\n" + "="*70)
        logger.info("Avvio server...")
        logger.info("="*70)

        # Mount Gradio app on Flask
        app = interface.mount_app(flask_app, path="/")

        # Configurazione server
        server_config = {
            'host': config.FLASK_HOST,
            'port': args.port,
            'debug': args.debug or config.DEBUG
        }

        logger.info(f"\n✅ Server pronto!")
        logger.info(f"\n🌐 Apri nel browser:")
        logger.info(f"   → http://localhost:{args.port}")
        if config.FLASK_HOST == "0.0.0.0":
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            logger.info(f"   → http://{local_ip}:{args.port}")

        logger.info(f"\n📚 Documentazione:")
        logger.info(f"   Upload manuali → Tab 'Carica Documenti'")
        logger.info(f"   Ricerca        → Tab 'Cerca nel Manuale'")
        logger.info(f"   Tutorial       → Tab 'Genera Tutorial'")
        logger.info(f"   PDF Viewer     → Tab 'Viewer PDF'")

        logger.info(f"\n⚙️ Configurazione:")
        logger.info(f"   Ollama Model:  {config.OLLAMA_MODEL}")
        logger.info(f"   Embedding:     {config.EMBEDDING_MODEL}")
        logger.info(f"   Chunk Size:    {config.CHUNK_SIZE}")
        logger.info(f"   Top-K:         {config.TOP_K_RETRIEVAL}")
        logger.info(f"   DB Path:       {config.CHROMA_DB_PATH}")

        logger.info(f"\n💡 Tips:")
        logger.info(f"   - Assicurati che Ollama sia in esecuzione")
        logger.info(f"   - Carica almeno un manuale prima di generare tutorial")
        logger.info(f"   - Le citazioni vengono verificate automaticamente")

        logger.info(f"\n🛑 Per fermare: Ctrl+C\n")
        logger.info("="*70 + "\n")

        # Avvia server
        flask_app.run(**server_config)

    except KeyboardInterrupt:
        logger.info("\n\n🛑 Server fermato dall'utente")
        sys.exit(0)

    except Exception as e:
        logger.error(f"\n❌ Errore server: {e}")
        logger.exception("Stack trace:")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"\n❌ Errore fatale: {e}")
        logger.exception("Stack trace:")
        sys.exit(1)
