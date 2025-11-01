"""
PDF Viewer integrato per visualizzazione documenti con highlighting.
Fornisce routes Flask e HTML embedding per viewer PDF.js.
"""

import os
import logging
from typing import Optional
from pathlib import Path

try:
    import pypdf
except ImportError:
    print("Warning: pypdf not available. Install with: pip install pypdf")

import config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)


class PDFViewer:
    """
    Viewer PDF integrato con Flask.

    Features:
    - Serving file PDF
    - Estrazione metadata (page count, ecc.)
    - Generazione HTML per embedding PDF.js
    - Route Flask per viewer
    - Highlighting testo
    """

    def __init__(self):
        """Inizializza PDF Viewer."""
        self.uploads_path = config.UPLOADS_PATH
        logger.info("PDFViewer inizializzato")

    def get_pdf_bytes(self, doc_name: str) -> Optional[bytes]:
        """
        Legge file PDF e ritorna bytes.

        Args:
            doc_name: Nome documento

        Returns:
            Bytes del PDF o None se non trovato
        """
        doc_path = os.path.join(self.uploads_path, doc_name)

        if not os.path.exists(doc_path):
            logger.warning(f"PDF non trovato: {doc_path}")
            return None

        try:
            with open(doc_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Errore lettura PDF: {e}")
            return None

    def get_pdf_path(self, doc_name: str) -> Optional[str]:
        """
        Ritorna path assoluto del PDF se esiste.

        Args:
            doc_name: Nome documento

        Returns:
            Path assoluto o None
        """
        doc_path = os.path.join(self.uploads_path, doc_name)

        if os.path.exists(doc_path):
            return doc_path
        return None

    def extract_page_count(self, doc_name: str) -> int:
        """
        Estrae numero pagine dal PDF.

        Args:
            doc_name: Nome documento

        Returns:
            Numero pagine o 0 se errore
        """
        doc_path = self.get_pdf_path(doc_name)

        if not doc_path:
            return 0

        try:
            with open(doc_path, 'rb') as f:
                pdf_reader = pypdf.PdfReader(f)
                return len(pdf_reader.pages)
        except Exception as e:
            logger.error(f"Errore estrazione page count: {e}")
            return 0

    def generate_pdf_js_html(
        self,
        doc_name: str,
        page: int = 1,
        highlight_text: str = ""
    ) -> str:
        """
        Genera HTML per embedding PDF con PDF.js.

        Args:
            doc_name: Nome documento
            page: Pagina da aprire
            highlight_text: Testo da evidenziare

        Returns:
            HTML completo per viewer
        """
        # URL per servire il PDF
        pdf_url = f"/serve_pdf/{doc_name}"

        # Genera HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Viewer - {doc_name}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: #525659;
        }}
        .viewer-container {{
            width: 100%;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        .toolbar {{
            background: #323639;
            color: white;
            padding: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .toolbar button {{
            background: #0a84ff;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        .toolbar button:hover {{
            background: #0066cc;
        }}
        .toolbar input {{
            padding: 6px;
            border-radius: 4px;
            border: 1px solid #555;
            width: 60px;
            text-align: center;
        }}
        .toolbar span {{
            color: #ccc;
        }}
        #pdf-container {{
            flex: 1;
            overflow: auto;
            background: #525659;
            display: flex;
            justify-content: center;
            padding: 20px;
        }}
        #pdf-canvas {{
            box-shadow: 0 0 10px rgba(0,0,0,0.5);
            max-width: 100%;
            height: auto;
        }}
        .search-highlight {{
            background: yellow;
            padding: 2px;
        }}
    </style>
</head>
<body>
    <div class="viewer-container">
        <div class="toolbar">
            <button onclick="previousPage()">◀ Prev</button>
            <span>Pagina</span>
            <input type="number" id="page-num" value="{page}" min="1" onchange="goToPage(this.value)">
            <span>/</span>
            <span id="page-count">-</span>
            <button onclick="nextPage()">Next ▶</button>

            <div style="flex: 1;"></div>

            <input type="text" id="search-text" placeholder="Cerca nel PDF..." value="{highlight_text}" style="width: 200px;">
            <button onclick="searchInPDF()">🔍 Cerca</button>

            <button onclick="zoomIn()">🔍+</button>
            <button onclick="zoomOut()">🔍-</button>
        </div>

        <div id="pdf-container">
            <canvas id="pdf-canvas"></canvas>
        </div>
    </div>

    <!-- PDF.js Library (CDN) -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>

    <script>
        // Configurazione PDF.js
        const pdfjsLib = window['pdfjs-dist/build/pdf'];
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

        let pdfDoc = null;
        let pageNum = {page};
        let pageRendering = false;
        let pageNumPending = null;
        let scale = 1.5;
        const canvas = document.getElementById('pdf-canvas');
        const ctx = canvas.getContext('2d');

        // Carica PDF
        pdfjsLib.getDocument('{pdf_url}').promise.then(function(pdfDoc_) {{
            pdfDoc = pdfDoc_;
            document.getElementById('page-count').textContent = pdfDoc.numPages;
            renderPage(pageNum);
        }});

        function renderPage(num) {{
            pageRendering = true;

            pdfDoc.getPage(num).then(function(page) {{
                const viewport = page.getViewport({{scale: scale}});
                canvas.height = viewport.height;
                canvas.width = viewport.width;

                const renderContext = {{
                    canvasContext: ctx,
                    viewport: viewport
                }};

                const renderTask = page.render(renderContext);

                renderTask.promise.then(function() {{
                    pageRendering = false;
                    if (pageNumPending !== null) {{
                        renderPage(pageNumPending);
                        pageNumPending = null;
                    }}
                }});
            }});

            document.getElementById('page-num').value = num;
        }}

        function queueRenderPage(num) {{
            if (pageRendering) {{
                pageNumPending = num;
            }} else {{
                renderPage(num);
            }}
        }}

        function previousPage() {{
            if (pageNum <= 1) {{
                return;
            }}
            pageNum--;
            queueRenderPage(pageNum);
        }}

        function nextPage() {{
            if (pageNum >= pdfDoc.numPages) {{
                return;
            }}
            pageNum++;
            queueRenderPage(pageNum);
        }}

        function goToPage(num) {{
            num = parseInt(num);
            if (num < 1 || num > pdfDoc.numPages) {{
                return;
            }}
            pageNum = num;
            queueRenderPage(pageNum);
        }}

        function zoomIn() {{
            scale += 0.2;
            queueRenderPage(pageNum);
        }}

        function zoomOut() {{
            if (scale > 0.5) {{
                scale -= 0.2;
                queueRenderPage(pageNum);
            }}
        }}

        function searchInPDF() {{
            const searchText = document.getElementById('search-text').value;
            if (!searchText) return;

            // Simple search: loop through pages
            // Note: Full text search requires more complex implementation
            alert('Ricerca: "' + searchText + '"\\nFunzionalità in sviluppo');
        }}

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowLeft') previousPage();
            if (e.key === 'ArrowRight') nextPage();
            if (e.key === '+') zoomIn();
            if (e.key === '-') zoomOut();
        }});
    </script>
</body>
</html>
        """

        return html

    def create_flask_routes(self, app):
        """
        Crea routes Flask per il viewer PDF.

        Args:
            app: Flask app instance
        """
        from flask import send_file, request, Response

        @app.route('/view_pdf')
        def view_pdf():
            """Route per visualizzare PDF con viewer integrato."""
            doc_name = request.args.get('doc', '')
            page = request.args.get('page', 1, type=int)
            highlight = request.args.get('highlight', '')

            if not doc_name:
                return "Documento non specificato", 400

            # Genera HTML viewer
            html = self.generate_pdf_js_html(doc_name, page, highlight)

            return Response(html, mimetype='text/html')

        @app.route('/serve_pdf/<path:doc_name>')
        def serve_pdf(doc_name):
            """Route per servire file PDF."""
            doc_path = self.get_pdf_path(doc_name)

            if not doc_path:
                return config.ERROR_MESSAGES['pdf_not_found'], 404

            try:
                return send_file(
                    doc_path,
                    mimetype='application/pdf',
                    as_attachment=False,
                    download_name=doc_name
                )
            except Exception as e:
                logger.error(f"Errore serving PDF: {e}")
                return "Errore serving PDF", 500

        @app.route('/pdf_info/<path:doc_name>')
        def pdf_info(doc_name):
            """Route per ottenere info PDF (numero pagine, ecc.)."""
            page_count = self.extract_page_count(doc_name)
            doc_path = self.get_pdf_path(doc_name)

            if not doc_path:
                return {"error": "PDF not found"}, 404

            return {
                "doc_name": doc_name,
                "page_count": page_count,
                "exists": True
            }

        logger.info("✓ Flask routes per PDF viewer registrate")


def create_simple_pdf_embed(doc_url: str, width: str = "100%", height: str = "600px") -> str:
    """
    Crea semplice iframe per embedding PDF.

    Fallback per browser che non supportano PDF.js.

    Args:
        doc_url: URL del PDF
        width: Larghezza iframe
        height: Altezza iframe

    Returns:
        HTML iframe
    """
    html = f"""
    <iframe src="{doc_url}"
            width="{width}"
            height="{height}"
            style="border: 1px solid #ccc;">
        <p>Il tuo browser non supporta PDF embeddati.
           <a href="{doc_url}">Scarica il PDF</a>
        </p>
    </iframe>
    """
    return html


if __name__ == "__main__":
    # Test PDF Viewer
    print("Testing PDF Viewer...")

    viewer = PDFViewer()

    # Test HTML generation
    html = viewer.generate_pdf_js_html("test.pdf", page=5, highlight_text="esempio")

    print(f"\n✓ HTML generato ({len(html)} caratteri)")
    print("\nPreview:")
    print(html[:500])
    print("...")

    print("\n✓ PDF Viewer OK")
