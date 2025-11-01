"""
Citation Link Generator per creare link cliccabili ai PDF con highlighting.
Supporta link file:// e URL per viewer integrato.
"""

import os
import re
import logging
from typing import Optional
from urllib.parse import quote

import config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)


class CitationLinkGenerator:
    """
    Generatore di link cliccabili per citazioni PDF.

    Features:
    - Link file:// per apertura locale
    - URL viewer integrato con parametri (pagina, highlight)
    - Validazione esistenza file
    - Supporto multi-formato
    """

    def __init__(self):
        """Inizializza Link Generator."""
        self.uploads_path = config.UPLOADS_PATH
        logger.info("CitationLinkGenerator inizializzato")

    def generate_pdf_link(
        self,
        doc_name: str,
        page_number: Optional[int] = None,
        search_text: Optional[str] = None,
        use_viewer: bool = True
    ) -> str:
        """
        Genera link cliccabile per documento PDF.

        Args:
            doc_name: Nome del documento (es: "Manuale.pdf")
            page_number: Numero pagina da aprire (opzionale)
            search_text: Testo da evidenziare (opzionale)
            use_viewer: Se True usa viewer integrato, altrimenti file://

        Returns:
            URL formattato come markdown link
        """
        # Verifica esistenza file
        doc_path = os.path.join(self.uploads_path, doc_name)

        if not os.path.exists(doc_path):
            logger.warning(f"File non trovato: {doc_path}")
            return f"[{doc_name}](file_not_found)"

        if use_viewer and config.ENABLE_PDF_VIEWER:
            # URL viewer integrato
            url = self.generate_viewer_url(doc_name, page_number, search_text)
        else:
            # URL file:// locale
            url = self._generate_file_url(doc_path, page_number, search_text)

        return url

    def generate_viewer_url(
        self,
        doc_name: str,
        page: Optional[int] = None,
        highlight: Optional[str] = None
    ) -> str:
        """
        Genera URL per viewer integrato.

        Args:
            doc_name: Nome documento
            page: Numero pagina
            highlight: Testo da evidenziare

        Returns:
            URL formato: /view_pdf?doc=X&page=Y&highlight=Z
        """
        # Encode parametri
        doc_encoded = quote(doc_name)

        url_parts = [f"/view_pdf?doc={doc_encoded}"]

        if page is not None and page != '?':
            try:
                page_num = int(page)
                url_parts.append(f"page={page_num}")
            except (ValueError, TypeError):
                pass

        if highlight:
            highlight_encoded = quote(highlight)
            url_parts.append(f"highlight={highlight_encoded}")

        url = "&".join(url_parts)

        logger.debug(f"Generated viewer URL: {url}")
        return url

    def _generate_file_url(
        self,
        file_path: str,
        page: Optional[int] = None,
        search_text: Optional[str] = None
    ) -> str:
        """
        Genera URL file:// per apertura locale.

        Args:
            file_path: Path assoluto al file
            page: Numero pagina
            search_text: Testo da cercare

        Returns:
            URL file:// con parametri
        """
        # Converti path in URL
        file_url = f"file://{file_path}"

        # Aggiungi parametri pagina (standard PDF)
        if page is not None and page != '?':
            try:
                page_num = int(page)
                file_url += f"#page={page_num}"
            except (ValueError, TypeError):
                pass

        # Note: highlight non è supportato in file:// standard
        # ma alcuni viewer lo supportano con #search=text

        return file_url

    def create_clickable_citations(self, tutorial_md: str) -> str:
        """
        Trasforma citazioni testuali in link cliccabili nel markdown.

        Cerca pattern: [📄 Documento.pdf - pag 5]
        Trasforma in: [📄 Documento.pdf - pag 5](/view_pdf?doc=Documento.pdf&page=5)

        Args:
            tutorial_md: Tutorial in markdown con citazioni

        Returns:
            Tutorial con link cliccabili
        """
        logger.info("Generazione link cliccabili per citazioni...")

        # Pattern per citazioni: [📄 filename - pag X]
        pattern = r'\[📄 ([^\]]+?) - pag ([^\]]+?)\]'

        def replace_citation(match):
            fonte_text = match.group(1).strip()
            page_text = match.group(2).strip()

            # Estrai nome file (potrebbe contenere path)
            doc_name = os.path.basename(fonte_text)

            # Parse numero pagina
            try:
                page_num = int(page_text) if page_text != '?' else None
            except ValueError:
                page_num = None

            # Genera link
            link_url = self.generate_pdf_link(
                doc_name,
                page_num,
                use_viewer=True
            )

            # Formato markdown con link
            return f"[📄 {fonte_text} - pag {page_text}]({link_url})"

        # Sostituisci tutte le citazioni
        result = re.sub(pattern, replace_citation, tutorial_md)

        # Conta sostituzioni
        citations_count = len(re.findall(pattern, tutorial_md))
        logger.info(f"✓ {citations_count} citazioni convertite in link")

        return result

    def generate_export_links(
        self,
        tutorial_md: str,
        export_format: str = "html"
    ) -> str:
        """
        Genera link per export (PDF, HTML, ecc.).

        Per HTML: link relativi funzionanti
        Per PDF export: link assoluti o embedded

        Args:
            tutorial_md: Tutorial markdown
            export_format: Formato export (html, pdf, markdown)

        Returns:
            Tutorial con link adattati per export
        """
        if export_format == "html":
            # HTML può usare link relativi
            return self.create_clickable_citations(tutorial_md)

        elif export_format == "pdf":
            # PDF export: mantieni testo citazione ma rimuovi link
            # (i link nei PDF generati potrebbero non funzionare)
            pattern = r'\[📄 ([^\]]+?)\]\([^\)]+\)'
            result = re.sub(pattern, r'[📄 \1]', tutorial_md)
            return result

        else:
            # Markdown o altri: mantieni come è
            return tutorial_md


def create_pdf_viewer_button(doc_name: str, page: int = 1) -> str:
    """
    Crea HTML button per aprire PDF viewer.

    Args:
        doc_name: Nome documento
        page: Pagina da aprire

    Returns:
        HTML button
    """
    url = CitationLinkGenerator().generate_viewer_url(doc_name, page)

    button_html = f"""
    <button onclick="window.open('{url}', '_blank')"
            style="padding:5px 10px; background:#007bff; color:white; border:none; border-radius:3px; cursor:pointer;">
        📄 Apri {doc_name} (pag {page})
    </button>
    """

    return button_html


def extract_citations_from_tutorial(tutorial_md: str) -> list:
    """
    Estrae tutte le citazioni dal tutorial markdown.

    Returns:
        Lista di dict: [{'fonte': str, 'pagina': str}, ...]
    """
    pattern = r'\[📄 ([^\]]+?) - pag ([^\]]+?)\]'
    matches = re.findall(pattern, tutorial_md)

    citations = []
    for fonte, pagina in matches:
        citations.append({
            'fonte': fonte.strip(),
            'pagina': pagina.strip()
        })

    return citations


if __name__ == "__main__":
    # Test Citation Link Generator
    print("Testing Citation Link Generator...")

    link_gen = CitationLinkGenerator()

    # Test link generation
    doc_name = "Manuale.pdf"
    page = 14

    # Test viewer URL
    viewer_url = link_gen.generate_viewer_url(doc_name, page, "reset")
    print(f"\nViewer URL: {viewer_url}")

    # Test clickable citations
    test_md = """
    # Tutorial Test

    Prerequisito: Accesso fisico [📄 Manuale.pdf - pag 2]

    Step 1: Reset dispositivo [📄 Manuale.pdf - pag 14]

    Nota: Fare backup [📄 Guida.pdf - pag 5]
    """

    result_md = link_gen.create_clickable_citations(test_md)
    print("\n" + "="*70)
    print("Markdown con link:")
    print("="*70)
    print(result_md)
    print("="*70)

    # Test extract citations
    citations = extract_citations_from_tutorial(test_md)
    print(f"\nCitazioni estratte: {len(citations)}")
    for cit in citations:
        print(f"  - {cit['fonte']} pag {cit['pagina']}")

    print("\n✓ Citation Link Generator OK")
