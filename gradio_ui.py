"""
Interfaccia Gradio per Tutorial Generator RAG.
Interfaccia completa con upload, ricerca, generazione tutorial e viewer PDF.
"""

import logging
import os
from typing import List, Tuple, Optional
import datetime

try:
    import gradio as gr
except ImportError:
    print("Error: gradio not installed. Install with: pip install gradio")
    exit(1)

import config
from rag_engine import RAGEngine
from llm_handler import TutorialGenerator
from pdf_viewer import PDFViewer

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)


class GradioUI:
    """
    Interfaccia Gradio completa per Tutorial Generator.

    Features:
    - Tab Upload documenti
    - Tab Ricerca semantica
    - Tab Generazione tutorial
    - Tab Viewer PDF
    - Tab Report citazioni
    """

    def __init__(self, rag_engine: RAGEngine, tutorial_generator: TutorialGenerator):
        """
        Inizializza interfaccia Gradio.

        Args:
            rag_engine: Istanza RAGEngine
            tutorial_generator: Istanza TutorialGenerator
        """
        self.rag_engine = rag_engine
        self.tutorial_generator = tutorial_generator
        self.pdf_viewer = PDFViewer()

        # State per sessione
        self.last_search_results = []
        self.tutorial_history = []

        logger.info("Gradio UI inizializzata")

    def create_interface(self) -> gr.Blocks:
        """
        Crea interfaccia Gradio completa.

        Returns:
            gr.Blocks interface
        """
        with gr.Blocks(
            title=config.APP_TITLE,
            theme=config.GRADIO_THEME
        ) as interface:

            # Header
            gr.Markdown(f"# {config.APP_TITLE}")
            gr.Markdown(config.APP_DESCRIPTION)

            # Tabs
            with gr.Tabs():

                # ============================================================
                # TAB 1: Upload Documenti
                # ============================================================
                with gr.Tab(config.TAB_UPLOAD):
                    gr.Markdown("### Carica Manuali Tecnici")
                    gr.Markdown("Supporta PDF, DOCX, TXT. Max 50MB per file.")

                    upload_files = gr.File(
                        label="Seleziona Documenti",
                        file_count="multiple",
                        file_types=[".pdf", ".docx", ".txt"]
                    )

                    upload_btn = gr.Button("📤 Carica e Indicizza", variant="primary")

                    upload_status = gr.Markdown("")

                    # Lista documenti caricati
                    gr.Markdown("### Documenti Indicizzati")
                    docs_list = gr.Dataframe(
                        headers=["Filename", "Tipo", "Dimensione", "Chunks", "Data Upload"],
                        datatype=["str", "str", "str", "number", "str"],
                        label="Documenti nel Database"
                    )

                    refresh_docs_btn = gr.Button("🔄 Aggiorna Lista")

                    # Eventi
                    upload_btn.click(
                        fn=self.upload_documents_handler,
                        inputs=[upload_files],
                        outputs=[upload_status, docs_list]
                    )

                    refresh_docs_btn.click(
                        fn=self.refresh_documents_list,
                        inputs=[],
                        outputs=[docs_list]
                    )

                    # Load iniziale
                    interface.load(
                        fn=self.refresh_documents_list,
                        inputs=[],
                        outputs=[docs_list]
                    )

                # ============================================================
                # TAB 2: Ricerca nel Manuale
                # ============================================================
                with gr.Tab(config.TAB_SEARCH):
                    gr.Markdown("### Ricerca Semantica nei Documenti")

                    with gr.Row():
                        search_query = gr.Textbox(
                            label="Domanda / Query",
                            placeholder="Es: Come resettare il dispositivo?",
                            lines=2
                        )

                    with gr.Row():
                        search_top_k = gr.Slider(
                            label="Numero Risultati",
                            minimum=3,
                            maximum=10,
                            value=5,
                            step=1
                        )

                    search_btn = gr.Button("🔍 Ricerca", variant="primary")

                    search_results = gr.Markdown("")

                    # Eventi
                    search_btn.click(
                        fn=self.search_documents_handler,
                        inputs=[search_query, search_top_k],
                        outputs=[search_results]
                    )

                # ============================================================
                # TAB 3: Genera Tutorial
                # ============================================================
                with gr.Tab(config.TAB_GENERATE):
                    gr.Markdown("### Genera Tutorial Passo-Passo")

                    tutorial_question = gr.Textbox(
                        label="Problema / Domanda",
                        placeholder="Es: Dammi una guida passo-passo per resettare il dispositivo",
                        lines=3
                    )

                    with gr.Row():
                        use_last_search = gr.Checkbox(
                            label="Usa risultati ultima ricerca",
                            value=False
                        )
                        verify_citations_check = gr.Checkbox(
                            label="Verifica citazioni automaticamente",
                            value=True
                        )

                    generate_btn = gr.Button("🤖 Genera Tutorial", variant="primary")

                    tutorial_output = gr.Markdown("")

                    with gr.Accordion("⚙️ Opzioni Export", open=False):
                        export_format = gr.Radio(
                            choices=["Markdown", "HTML", "PDF"],
                            value="Markdown",
                            label="Formato Export"
                        )
                        export_btn = gr.Button("💾 Esporta Tutorial")
                        export_status = gr.Markdown("")

                    # Eventi
                    generate_btn.click(
                        fn=self.generate_tutorial_handler,
                        inputs=[tutorial_question, use_last_search, verify_citations_check],
                        outputs=[tutorial_output]
                    )

                    export_btn.click(
                        fn=self.export_tutorial_handler,
                        inputs=[tutorial_output, export_format],
                        outputs=[export_status]
                    )

                # ============================================================
                # TAB 4: Viewer PDF
                # ============================================================
                with gr.Tab(config.TAB_VIEWER):
                    gr.Markdown("### Visualizza Documenti PDF")

                    doc_selector = gr.Dropdown(
                        label="Seleziona Documento",
                        choices=[],
                        interactive=True
                    )

                    page_selector = gr.Slider(
                        label="Pagina",
                        minimum=1,
                        maximum=100,
                        value=1,
                        step=1
                    )

                    open_viewer_btn = gr.Button("📄 Apri PDF Viewer", variant="primary")

                    viewer_output = gr.HTML("")

                    # Refresh document list for viewer
                    interface.load(
                        fn=self.get_pdf_list,
                        inputs=[],
                        outputs=[doc_selector]
                    )

                    open_viewer_btn.click(
                        fn=self.open_pdf_viewer_handler,
                        inputs=[doc_selector, page_selector],
                        outputs=[viewer_output]
                    )

                # ============================================================
                # TAB 5: Report Citazioni
                # ============================================================
                with gr.Tab(config.TAB_REPORT):
                    gr.Markdown("### Storico Tutorial e Verifica Citazioni")

                    refresh_history_btn = gr.Button("🔄 Aggiorna Storico")

                    history_table = gr.Dataframe(
                        headers=["Data", "Domanda", "Fonti Usate", "Citazioni Verificate", "Accuracy"],
                        datatype=["str", "str", "str", "str", "str"],
                        label="Storico Tutorial Generati"
                    )

                    export_report_btn = gr.Button("📊 Esporta Report CSV")
                    export_report_status = gr.Markdown("")

                    # Eventi
                    refresh_history_btn.click(
                        fn=self.refresh_history_handler,
                        inputs=[],
                        outputs=[history_table]
                    )

                    export_report_btn.click(
                        fn=self.export_report_handler,
                        inputs=[],
                        outputs=[export_report_status]
                    )

            # Footer
            gr.Markdown("---")
            gr.Markdown(
                f"**{config.APP_TITLE}** v{config.APP_VERSION} | "
                f"Powered by Ollama + Mistral | "
                f"Build: {config.BUILD_DATE}"
            )

        return interface

    # ========================================================================
    # Event Handlers
    # ========================================================================

    def upload_documents_handler(self, files: List) -> Tuple[str, List]:
        """Handler per upload documenti."""
        if not files:
            return "⚠️ Nessun file selezionato", []

        try:
            # Ottieni path dei file
            file_paths = [f.name for f in files]

            # Upload
            result = self.rag_engine.upload_documents(file_paths)

            # Crea messaggio status
            status_md = f"### {result['message']}\n\n"
            status_md += f"**Documenti elaborati:** {result['documents_processed']}\n\n"
            status_md += f"**Chunks creati:** {result['chunks_created']}\n\n"

            # Dettagli
            status_md += "#### Dettagli:\n"
            for detail in result['details']:
                status = "✅" if detail['status'] == 'success' else "❌"
                status_md += f"- {status} **{detail['file']}**"
                if detail['status'] == 'success':
                    status_md += f" ({detail['chunks']} chunks, {detail['time']})"
                else:
                    status_md += f" - {detail.get('message', 'Errore')}"
                status_md += "\n"

            # Refresh lista
            docs_list = self.refresh_documents_list()

            return status_md, docs_list

        except Exception as e:
            logger.error(f"Errore upload: {e}")
            return f"❌ Errore: {str(e)}", []

    def refresh_documents_list(self) -> List:
        """Aggiorna lista documenti indicizzati."""
        docs = self.rag_engine.get_indexed_docs()

        rows = []
        for doc_id, info in docs.items():
            rows.append([
                info['filename'],
                info['file_type'],
                f"{info['file_size'] / 1024:.1f} KB",
                info['chunks_count'],
                info['upload_timestamp'][:10]  # Solo data
            ])

        return rows

    def search_documents_handler(self, query: str, top_k: int) -> str:
        """Handler per ricerca documenti."""
        if not query or len(query.strip()) < 3:
            return config.ERROR_MESSAGES['query_empty']

        try:
            # Esegui ricerca
            results = self.rag_engine.query(query, top_k=top_k)

            # Salva per uso in generazione tutorial
            self.last_search_results = results

            if not results:
                return "⚠️ Nessun risultato trovato. Prova con una query diversa."

            # Formatta risultati
            output_md = f"### 🔍 Risultati Ricerca: '{query}'\n\n"
            output_md += f"**{len(results)} risultati rilevanti**\n\n"
            output_md += "---\n\n"

            for i, (chunk_text, metadata, score) in enumerate(results, 1):
                fonte = metadata.get('source_file', 'unknown')
                page = metadata.get('page_number', '?')

                output_md += f"#### Risultato {i} - Rilevanza: {score:.0%}\n\n"
                output_md += f"**Fonte:** {fonte}\n\n"
                if page and page != '?':
                    output_md += f"**Pagina:** {page}\n\n"

                # Preview chunk (primi 300 caratteri)
                preview = chunk_text[:300].replace('[PAGE', '').replace(']', '')
                output_md += f"**Contenuto:**\n> {preview}...\n\n"

                # Link viewer
                if fonte.endswith('.pdf'):
                    output_md += f"[📄 Apri in Viewer](/view_pdf?doc={fonte}&page={page})\n\n"

                output_md += "---\n\n"

            return output_md

        except Exception as e:
            logger.error(f"Errore ricerca: {e}")
            return f"❌ Errore: {str(e)}"

    def generate_tutorial_handler(
        self,
        question: str,
        use_last_search: bool,
        verify_citations: bool
    ) -> str:
        """Handler per generazione tutorial."""
        if not question or len(question.strip()) < 5:
            return config.ERROR_MESSAGES['query_empty']

        try:
            # Ottieni contesto
            if use_last_search and self.last_search_results:
                context_chunks = self.last_search_results
            else:
                # Nuova ricerca
                context_chunks = self.rag_engine.query(question, top_k=5)

            if not context_chunks:
                return config.ERROR_MESSAGES['no_documents']

            # Genera tutorial
            result = self.tutorial_generator.generate_tutorial(
                question,
                context_chunks,
                verify_citations=verify_citations
            )

            if not result['success']:
                return f"❌ {result['message']}"

            # Salva in history
            self.tutorial_history.append({
                'timestamp': datetime.datetime.now().isoformat(),
                'question': question,
                'tutorial_md': result['tutorial_markdown'],
                'sources': [m.get('source_file', '') for _, m, _ in context_chunks],
                'verification': result.get('verification_report')
            })

            return result['tutorial_markdown']

        except Exception as e:
            logger.error(f"Errore generazione tutorial: {e}")
            return f"❌ Errore: {str(e)}"

    def export_tutorial_handler(self, tutorial_md: str, export_format: str) -> str:
        """Handler per export tutorial."""
        if not tutorial_md:
            return "⚠️ Nessun tutorial da esportare"

        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tutorial_{timestamp}"

            if export_format == "Markdown":
                filepath = os.path.join(config.EXPORT_PATH, f"{filename}.md")
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(tutorial_md)

            elif export_format == "HTML":
                filepath = os.path.join(config.EXPORT_PATH, f"{filename}.html")
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Tutorial</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
    </style>
</head>
<body>
{tutorial_md}
</body>
</html>
                """
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)

            else:  # PDF
                # Requires additional library (reportlab or weasyprint)
                return "⚠️ Export PDF non ancora implementato. Usa Markdown o HTML."

            return f"✅ Tutorial esportato: `{filepath}`"

        except Exception as e:
            logger.error(f"Errore export: {e}")
            return f"❌ Errore export: {str(e)}"

    def get_pdf_list(self) -> List[str]:
        """Ottieni lista PDF caricati."""
        docs = self.rag_engine.get_indexed_docs()
        pdf_list = [
            info['filename']
            for doc_id, info in docs.items()
            if info['filename'].endswith('.pdf')
        ]
        return pdf_list

    def open_pdf_viewer_handler(self, doc_name: str, page: int) -> str:
        """Handler per apertura PDF viewer."""
        if not doc_name:
            return "<p>⚠️ Seleziona un documento</p>"

        try:
            # Genera HTML viewer
            html = self.pdf_viewer.generate_pdf_js_html(doc_name, page)
            return html

        except Exception as e:
            logger.error(f"Errore viewer: {e}")
            return f"<p>❌ Errore: {str(e)}</p>"

    def refresh_history_handler(self) -> List:
        """Aggiorna storico tutorial."""
        rows = []

        for entry in self.tutorial_history:
            timestamp = entry['timestamp'][:19]  # Rimuovi millisecondi
            question = entry['question'][:50] + "..." if len(entry['question']) > 50 else entry['question']
            sources = ", ".join(set(entry['sources']))

            verification = entry.get('verification')
            if verification:
                verified = f"{verification['verified']}/{verification['total']}"
                accuracy = f"{verification['accuracy']:.0%}"
            else:
                verified = "N/A"
                accuracy = "N/A"

            rows.append([timestamp, question, sources, verified, accuracy])

        return rows

    def export_report_handler(self) -> str:
        """Handler per export report CSV."""
        if not self.tutorial_history:
            return "⚠️ Nessun tutorial generato"

        try:
            import csv

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(config.EXPORT_PATH, f"report_{timestamp}.csv")

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'Question', 'Sources', 'Verified', 'Accuracy'])

                for entry in self.tutorial_history:
                    timestamp = entry['timestamp']
                    question = entry['question']
                    sources = ", ".join(set(entry['sources']))

                    verification = entry.get('verification')
                    if verification:
                        verified = f"{verification['verified']}/{verification['total']}"
                        accuracy = f"{verification['accuracy']:.0%}"
                    else:
                        verified = "N/A"
                        accuracy = "N/A"

                    writer.writerow([timestamp, question, sources, verified, accuracy])

            return f"✅ Report esportato: `{filepath}`"

        except Exception as e:
            logger.error(f"Errore export report: {e}")
            return f"❌ Errore: {str(e)}"


if __name__ == "__main__":
    print("Gradio UI module loaded")
    print("Run main.py to start the application")
