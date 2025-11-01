"""
Citation Verifier per verifica accuratezza citazioni nei tutorial.
Confronta citazioni generate dall'LLM con chunk originali dai documenti.
"""

import logging
from typing import List, Dict, Tuple, Any, Optional
from difflib import SequenceMatcher
import re

try:
    from fuzzywuzzy import fuzz
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    print("Warning: fuzzywuzzy not available. Using basic similarity.")

import config
from rag_engine import extract_page_number_from_text

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)


class CitationVerifier:
    """
    Verifica accuratezza citazioni nei tutorial.

    Features:
    - Confronto semantico tra citazioni e chunk originali
    - Validazione numero pagina
    - Calcolo accuracy score
    - Generazione report dettagliati
    - Flag citazioni dubbie
    """

    def __init__(self):
        """Inizializza Citation Verifier."""
        self.threshold = config.CITATION_VERIFICATION_THRESHOLD
        logger.info(f"CitationVerifier inizializzato (threshold: {self.threshold:.0%})")

    def verify_all_citations(
        self,
        tutorial_json: Dict,
        original_chunks: List[Tuple[str, Dict, float]]
    ) -> Dict[str, Any]:
        """
        Verifica tutte le citazioni nel tutorial.

        Args:
            tutorial_json: Tutorial in formato JSON
            original_chunks: Lista di (chunk_text, metadata, score) originali

        Returns:
            Dict con report verifica: {
                'total': int,
                'verified': int,
                'uncertain': int,
                'failed': int,
                'accuracy': float,
                'details': List[Dict],
                'issues': List[str]
            }
        """
        logger.info("Verifica citazioni in corso...")

        report = {
            'total': 0,
            'verified': 0,
            'uncertain': 0,
            'failed': 0,
            'accuracy': 0.0,
            'details': [],
            'issues': []
        }

        # Estrai tutte le citazioni dal tutorial
        citations = self._extract_all_citations(tutorial_json)

        report['total'] = len(citations)

        # Verifica ogni citazione
        for citation in citations:
            verification = self._verify_single_citation(citation, original_chunks)

            report['details'].append(verification)

            if verification['verified']:
                report['verified'] += 1
            elif verification['uncertain']:
                report['uncertain'] += 1
                report['issues'].append(
                    f"⚠️ Citazione incerta: '{citation['text'][:50]}...' - "
                    f"{verification['issue']}"
                )
            else:
                report['failed'] += 1
                report['issues'].append(
                    f"✗ Citazione non verificata: '{citation['text'][:50]}...' - "
                    f"{verification['issue']}"
                )

        # Calcola accuracy
        if report['total'] > 0:
            report['accuracy'] = report['verified'] / report['total']

        logger.info(
            f"Verifica completata: {report['verified']}/{report['total']} verificate "
            f"({report['accuracy']:.0%} accuracy)"
        )

        return report

    def _extract_all_citations(self, tutorial_json: Dict) -> List[Dict[str, Any]]:
        """
        Estrae tutte le citazioni dal tutorial JSON.

        Returns:
            Lista di dict con: {
                'text': str,
                'fonte': str,
                'pagina': int|str,
                'type': str (prerequisito, step, nota, avvertimento)
            }
        """
        citations = []

        # Prerequisiti
        for prereq in tutorial_json.get('prerequisiti', []):
            if isinstance(prereq, dict):
                citations.append({
                    'text': prereq.get('testo', ''),
                    'fonte': prereq.get('fonte', ''),
                    'pagina': prereq.get('pagina', '?'),
                    'type': 'prerequisito'
                })

        # Steps
        for step in tutorial_json.get('steps', []):
            if isinstance(step, dict):
                # Concatena descrizione e dettagli per verifica
                text_parts = []
                if 'descrizione' in step:
                    text_parts.append(step['descrizione'])
                if 'dettagli' in step:
                    text_parts.append(step['dettagli'])

                citations.append({
                    'text': ' '.join(text_parts),
                    'fonte': step.get('fonte', ''),
                    'pagina': step.get('pagina', '?'),
                    'type': f"step_{step.get('numero', '?')}"
                })

        # Note
        for nota in tutorial_json.get('note', []):
            if isinstance(nota, dict):
                citations.append({
                    'text': nota.get('testo', ''),
                    'fonte': nota.get('fonte', ''),
                    'pagina': nota.get('pagina', '?'),
                    'type': 'nota'
                })

        # Avvertimenti
        for avv in tutorial_json.get('avvertimenti', []):
            if isinstance(avv, dict):
                citations.append({
                    'text': avv.get('testo', ''),
                    'fonte': avv.get('fonte', ''),
                    'pagina': avv.get('pagina', '?'),
                    'type': 'avvertimento'
                })

        logger.debug(f"Estratte {len(citations)} citazioni")
        return citations

    def _verify_single_citation(
        self,
        citation: Dict[str, Any],
        original_chunks: List[Tuple[str, Dict, float]]
    ) -> Dict[str, Any]:
        """
        Verifica una singola citazione.

        Returns:
            Dict con:
            - verified: bool
            - uncertain: bool
            - similarity_score: float
            - matched_chunk: str (preview)
            - page_match: bool
            - issue: str (descrizione problema se presente)
        """
        citation_text = citation['text']
        citation_fonte = citation['fonte']
        citation_pagina = citation['pagina']

        result = {
            'citation': citation,
            'verified': False,
            'uncertain': False,
            'similarity_score': 0.0,
            'matched_chunk': None,
            'page_match': False,
            'issue': None
        }

        # Trova chunk più simile
        best_match = None
        best_score = 0.0
        best_chunk = None

        for chunk_text, metadata, rag_score in original_chunks:
            # Filtra per fonte
            chunk_fonte = metadata.get('source_file', '')
            if citation_fonte not in chunk_fonte:
                continue

            # Calcola similarità
            similarity = self._calculate_similarity(citation_text, chunk_text)

            if similarity > best_score:
                best_score = similarity
                best_chunk = (chunk_text, metadata)
                best_match = chunk_text

        if best_match is None:
            result['issue'] = f"Fonte '{citation_fonte}' non trovata nei chunk"
            result['verified'] = False
            return result

        result['similarity_score'] = best_score
        result['matched_chunk'] = best_match[:200]  # Preview

        # Verifica threshold
        if best_score >= self.threshold:
            result['verified'] = True

            # Verifica pagina se specificata
            if citation_pagina != '?':
                chunk_text, metadata = best_chunk
                chunk_pagina = extract_page_number_from_text(chunk_text)

                if chunk_pagina:
                    # Confronta pagine (tolleranza ±1)
                    try:
                        cit_pag = int(citation_pagina)
                        if abs(chunk_pagina - cit_pag) <= 1:
                            result['page_match'] = True
                        else:
                            result['page_match'] = False
                            result['uncertain'] = True
                            result['verified'] = False
                            result['issue'] = (
                                f"Pagina non corrisponde: citata {cit_pag}, "
                                f"trovata {chunk_pagina}"
                            )
                    except ValueError:
                        result['page_match'] = False
                        result['uncertain'] = True
                else:
                    # Pagina non estratta dal chunk
                    result['page_match'] = False
                    result['uncertain'] = True

        elif best_score >= 0.5:
            # Similarità media -> incerta
            result['uncertain'] = True
            result['issue'] = f"Similarità bassa ({best_score:.0%})"
        else:
            # Troppo diverso
            result['verified'] = False
            result['issue'] = f"Contenuto non trovato nel documento (sim: {best_score:.0%})"

        return result

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcola similarità tra due testi.

        Usa fuzzywuzzy se disponibile, altrimenti SequenceMatcher.

        Returns:
            Score 0.0-1.0
        """
        # Normalizza testi
        text1 = self._normalize_text(text1)
        text2 = self._normalize_text(text2)

        if not text1 or not text2:
            return 0.0

        if FUZZYWUZZY_AVAILABLE:
            # Usa token_set_ratio per gestire ordine parole
            score = fuzz.token_set_ratio(text1, text2) / 100.0
        else:
            # Fallback a SequenceMatcher
            score = SequenceMatcher(None, text1, text2).ratio()

        return score

    def _normalize_text(self, text: str) -> str:
        """Normalizza testo per confronto."""
        # Lowercase
        text = text.lower()

        # Rimuovi marker pagina
        text = re.sub(r'\[PAGE \d+\]', '', text)

        # Rimuovi spazi multipli
        text = re.sub(r'\s+', ' ', text)

        # Rimuovi punteggiatura extra
        text = text.strip()

        return text

    def generate_verification_report(self, verifications: Dict) -> str:
        """
        Genera report HTML verifica citazioni.

        Args:
            verifications: Dict da verify_all_citations()

        Returns:
            HTML report formattato
        """
        html_parts = []

        html_parts.append("<div class='verification-report'>")
        html_parts.append(f"<h3>📊 Report Verifica Citazioni</h3>")

        total = verifications['total']
        verified = verifications['verified']
        uncertain = verifications['uncertain']
        failed = verifications['failed']
        accuracy = verifications['accuracy']

        html_parts.append(f"<p><strong>Accuracy Complessiva: {accuracy:.0%}</strong></p>")
        html_parts.append(f"<p>Verificate: {verified} | Incerte: {uncertain} | Non verificate: {failed}</p>")

        # Tabella dettagli
        html_parts.append("<table border='1' style='width:100%; border-collapse:collapse;'>")
        html_parts.append("<tr><th>#</th><th>Tipo</th><th>Testo</th><th>Status</th><th>Score</th></tr>")

        for i, detail in enumerate(verifications['details'], 1):
            citation = detail['citation']
            status = "✓" if detail['verified'] else ("⚠️" if detail['uncertain'] else "✗")
            status_color = "green" if detail['verified'] else ("orange" if detail['uncertain'] else "red")
            score = detail['similarity_score']

            html_parts.append(
                f"<tr>"
                f"<td>{i}</td>"
                f"<td>{citation['type']}</td>"
                f"<td>{citation['text'][:50]}...</td>"
                f"<td style='color:{status_color}'>{status}</td>"
                f"<td>{score:.0%}</td>"
                f"</tr>"
            )

        html_parts.append("</table>")

        # Issues
        if verifications['issues']:
            html_parts.append("<h4>⚠️ Problemi Rilevati</h4>")
            html_parts.append("<ul>")
            for issue in verifications['issues']:
                html_parts.append(f"<li>{issue}</li>")
            html_parts.append("</ul>")

        html_parts.append("</div>")

        return "".join(html_parts)

    def flag_uncertain_citations(self, verifications: Dict) -> List[str]:
        """
        Ritorna lista citazioni che necessitano revisione manuale.

        Args:
            verifications: Dict da verify_all_citations()

        Returns:
            Lista di messaggi per citazioni da verificare
        """
        uncertain = []

        for detail in verifications['details']:
            if detail['uncertain'] or not detail['verified']:
                citation = detail['citation']
                issue = detail.get('issue', 'Citazione dubbia')

                uncertain.append(
                    f"{citation['type']}: '{citation['text'][:50]}...' - {issue}"
                )

        return uncertain


if __name__ == "__main__":
    # Test Citation Verifier
    print("Testing Citation Verifier...")

    verifier = CitationVerifier()

    # Mock data
    mock_tutorial = {
        'prerequisiti': [
            {
                'testo': 'Accesso fisico al dispositivo',
                'fonte': 'Manuale.pdf',
                'pagina': 2
            }
        ],
        'steps': [
            {
                'numero': 1,
                'titolo': 'Reset',
                'descrizione': 'Tenere premuto pulsante Power per 10 secondi',
                'fonte': 'Manuale.pdf',
                'pagina': 14
            }
        ]
    }

    mock_chunks = [
        (
            "[PAGE 2]\nPer accedere al dispositivo è necessario avere accesso fisico.",
            {'source_file': 'Manuale.pdf'},
            0.95
        ),
        (
            "[PAGE 14]\nPer resettare tenere premuto il pulsante Power per 10 secondi.",
            {'source_file': 'Manuale.pdf'},
            0.90
        )
    ]

    report = verifier.verify_all_citations(mock_tutorial, mock_chunks)

    print(f"\n✓ Verifica completata!")
    print(f"Total: {report['total']}")
    print(f"Verified: {report['verified']}")
    print(f"Accuracy: {report['accuracy']:.0%}")

    if report['issues']:
        print("\nIssues:")
        for issue in report['issues']:
            print(f"  - {issue}")
