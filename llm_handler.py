"""
LLM Handler per generazione tutorial usando Ollama.
Gestisce prompt engineering, parsing JSON, citazioni e verifica fonti.
"""

import json
import logging
import re
from typing import List, Dict, Tuple, Any, Optional

try:
    import ollama
except ImportError:
    print("Warning: ollama package not found. Install with: pip install ollama")

import config
from rag_engine import extract_page_number_from_text

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)


class TutorialGenerator:
    """
    Generatore di tutorial passo-passo usando Ollama.

    Features:
    - Connessione a Ollama locale
    - Prompt engineering per tutorial strutturati
    - Parsing JSON robusto
    - Source mapping e citation injection
    - Verifica citazioni (opzionale)
    - Generazione link cliccabili
    """

    def __init__(self):
        """Inizializza il generatore con client Ollama."""
        logger.info("Inizializzazione Tutorial Generator...")

        self.ollama_client = None
        self.model = config.OLLAMA_MODEL

        # Test connessione Ollama
        self._test_ollama_connection()

        logger.info(f"Tutorial Generator inizializzato (model: {self.model})")

    def _test_ollama_connection(self) -> bool:
        """Testa connessione a Ollama."""
        try:
            # Test if Ollama is running
            response = ollama.list()
            logger.info(f"✓ Ollama connesso. Modelli disponibili: {len(response.get('models', []))}")
            return True
        except Exception as e:
            logger.warning(f"⚠ Ollama non raggiungibile: {e}")
            logger.warning(f"Assicurati che Ollama sia in esecuzione: 'ollama serve'")
            return False

    def generate_tutorial(
        self,
        question: str,
        context_chunks: List[Tuple[str, Dict, float]],
        verify_citations: bool = True
    ) -> Dict[str, Any]:
        """
        Genera tutorial strutturato basato su query e contesto RAG.

        Args:
            question: Domanda/problema dell'utente
            context_chunks: Lista di (chunk_text, metadata, score) dal RAG
            verify_citations: Se True, verifica le citazioni

        Returns:
            Dict con:
            - tutorial_json: Tutorial in formato JSON
            - tutorial_markdown: Tutorial formattato in markdown
            - source_map: Mapping chunk -> documento
            - verification_report: Report verifica citazioni (se abilitato)
        """
        logger.info(f"Generazione tutorial per: '{question}'")

        try:
            # Crea source map
            source_map = self._create_source_map(context_chunks)

            # Costruisci prompt
            prompt = self._build_prompt(question, context_chunks)

            # Chiama Ollama
            response_text = self._call_ollama(prompt)

            # Parse JSON
            tutorial_json = self._parse_json_response(response_text)

            if not tutorial_json:
                raise ValueError("Impossibile parsare la risposta JSON")

            # Inject citations
            tutorial_json = self._inject_citations(tutorial_json, source_map)

            # Verifica citazioni (opzionale)
            verification_report = None
            if verify_citations and config.ENABLE_CITATION_VERIFICATION:
                verification_report = self._verify_citations_wrapper(
                    tutorial_json,
                    context_chunks
                )

            # Genera markdown
            tutorial_markdown = self._format_tutorial_markdown(
                tutorial_json,
                verification_report
            )

            # Genera link cliccabili
            tutorial_markdown = self._generate_citation_links_wrapper(tutorial_markdown)

            result = {
                'success': True,
                'tutorial_json': tutorial_json,
                'tutorial_markdown': tutorial_markdown,
                'source_map': source_map,
                'verification_report': verification_report,
                'message': config.SUCCESS_MESSAGES['tutorial_generated']
            }

            logger.info("✓ Tutorial generato con successo")
            return result

        except Exception as e:
            logger.error(f"Errore generazione tutorial: {e}")
            return {
                'success': False,
                'message': f"Errore: {str(e)}",
                'tutorial_json': None,
                'tutorial_markdown': None
            }

    def _build_prompt(self, question: str, context_chunks: List[Tuple[str, Dict, float]]) -> str:
        """
        Costruisce prompt per Ollama con engineering ottimizzato.

        Il prompt richiede:
        - Output JSON strutturato
        - Citazioni ESATTE per ogni informazione
        - Numero pagina ESATTO o '?' se incerto
        - Lingua italiana
        """
        system_prompt = f"""Sei un esperto tecnico che crea tutorial passo-passo basati su manuali.

REGOLE IMPORTANTI:
1. Rispondi SEMPRE in {config.TUTORIAL_LANGUAGE}
2. Usa SOLO informazioni dai documenti forniti
3. CITA SEMPRE il documento sorgente ESATTO per ogni passo, prerequisito e nota
4. Se non sei sicuro del numero di pagina, scrivi '?' al posto del numero
5. Sii {config.TUTORIAL_TONE}

Rispondi in JSON con questa struttura ESATTA:
{{
  "titolo": "Titolo del tutorial",
  "problema": "Descrizione del problema",
  "prerequisiti": [
    {{
      "testo": "Descrizione prerequisito",
      "fonte": "nome_documento.pdf",
      "pagina": 5
    }}
  ],
  "steps": [
    {{
      "numero": 1,
      "titolo": "Titolo step",
      "descrizione": "Descrizione dettagliata",
      "dettagli": "Ulteriori dettagli",
      "fonte": "nome_documento.pdf",
      "pagina": 5
    }}
  ],
  "note": [
    {{
      "testo": "Nota importante",
      "fonte": "nome_documento.pdf",
      "pagina": 3
    }}
  ],
  "avvertimenti": [
    {{
      "testo": "Avvertimento",
      "fonte": "nome_documento.pdf",
      "pagina": 8
    }}
  ],
  "tempo_stimato": "Es: 15-20 minuti",
  "riferimenti": [
    {{
      "documento": "nome_file.pdf",
      "pagine_citate": [5, 8, 12],
      "capitoli": ["Capitolo 2"],
      "relevance_score": 0.95
    }}
  ]
}}

Rispondi SOLO con il JSON, senza altro testo."""

        # Costruisci contesto dai chunks
        context_text = "\n\n---\n\n"

        for i, (chunk_text, metadata, score) in enumerate(context_chunks, 1):
            source_file = metadata.get('source_file', 'documento_sconosciuto')
            page_num = extract_page_number_from_text(chunk_text) or '?'

            context_text += f"""DOCUMENTO {i}:
Fonte: {source_file}
Pagina: {page_num}
Rilevanza: {score:.0%}

Contenuto:
{chunk_text}

---

"""

        user_prompt = f"""Domanda utente:
{question}

Documenti disponibili:
{context_text}

Ricorda:
- Cita SEMPRE fonte esatta e pagina
- Se incerto sulla pagina, usa '?'
- Rispondi SOLO in JSON valido
"""

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        if config.DEBUG_LLM_HANDLER:
            logger.debug(f"Prompt costruito ({len(full_prompt)} caratteri)")

        return full_prompt

    def _call_ollama(self, prompt: str) -> str:
        """Chiama Ollama API e ritorna la risposta."""
        try:
            logger.info(f"Chiamata a Ollama (model: {self.model})...")

            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.3,  # Più deterministico per JSON
                    'top_p': 0.9,
                }
            )

            response_text = response['message']['content']

            logger.info(f"✓ Risposta ricevuta ({len(response_text)} caratteri)")

            return response_text

        except Exception as e:
            logger.error(f"Errore chiamata Ollama: {e}")
            raise

    def _parse_json_response(self, response_text: str) -> Optional[Dict]:
        """
        Parse risposta JSON da Ollama.

        Gestisce casi in cui l'LLM aggiunge testo extra prima/dopo JSON.
        """
        try:
            # Prova parsing diretto
            return json.loads(response_text)

        except json.JSONDecodeError:
            # Cerca JSON nel testo
            logger.warning("JSON parsing fallito, tentativo estrazione...")

            # Cerca pattern ```json ... ```
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    pass

            # Cerca primo { fino ultimo }
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')

            if start_idx != -1 and end_idx != -1:
                try:
                    json_str = response_text[start_idx:end_idx+1]
                    return json.loads(json_str)
                except:
                    pass

            logger.error("Impossibile estrarre JSON valido dalla risposta")
            return None

    def _create_source_map(self, context_chunks: List[Tuple[str, Dict, float]]) -> Dict[str, Any]:
        """
        Crea mapping chunk -> documento + pagina.

        Returns:
            Dict con mapping per tracking fonti
        """
        source_map = {}

        for i, (chunk_text, metadata, score) in enumerate(context_chunks):
            source_file = metadata.get('source_file', 'unknown')
            page_num = extract_page_number_from_text(chunk_text)

            source_map[f"chunk_{i}"] = {
                'source_file': source_file,
                'page': page_num,
                'score': score,
                'chunk_preview': chunk_text[:200]  # Preview per debug
            }

        return source_map

    def _inject_citations(self, tutorial_json: Dict, source_map: Dict) -> Dict:
        """
        Aggiunge informazioni di citazione al tutorial JSON.

        Nota: Le citazioni sono già nel JSON generato dall'LLM,
        questa funzione può validarle o arricchirle.
        """
        # Le citazioni sono già nel JSON dal prompt
        # Qui potremmo fare validazione o enrichment

        return tutorial_json

    def _verify_citations_wrapper(
        self,
        tutorial_json: Dict,
        original_chunks: List[Tuple[str, Dict, float]]
    ) -> Optional[Dict]:
        """
        Wrapper per verifica citazioni.

        Importa e usa citation_verifier se disponibile.
        """
        try:
            from citation_verifier import CitationVerifier

            verifier = CitationVerifier()
            report = verifier.verify_all_citations(tutorial_json, original_chunks)

            logger.info(f"Verifica citazioni completata: {report.get('accuracy', 0):.0%} accuracy")
            return report

        except ImportError:
            logger.warning("CitationVerifier non disponibile, skip verifica")
            return None
        except Exception as e:
            logger.error(f"Errore verifica citazioni: {e}")
            return None

    def _generate_citation_links_wrapper(self, tutorial_markdown: str) -> str:
        """
        Wrapper per generazione link cliccabili.

        Importa e usa citation_link_gen se disponibile.
        """
        try:
            from citation_link_gen import CitationLinkGenerator

            link_gen = CitationLinkGenerator()
            tutorial_markdown = link_gen.create_clickable_citations(tutorial_markdown)

            logger.info("Link citazioni generati")
            return tutorial_markdown

        except ImportError:
            logger.warning("CitationLinkGenerator non disponibile, skip link generation")
            return tutorial_markdown
        except Exception as e:
            logger.error(f"Errore generazione link: {e}")
            return tutorial_markdown

    def _format_tutorial_markdown(
        self,
        tutorial_json: Dict,
        verification_report: Optional[Dict] = None
    ) -> str:
        """
        Formatta tutorial JSON in markdown leggibile.

        Args:
            tutorial_json: Tutorial in formato JSON
            verification_report: Report verifica citazioni (opzionale)

        Returns:
            Tutorial formattato in markdown
        """
        md_parts = []

        # Titolo
        md_parts.append(f"# {tutorial_json.get('titolo', 'Tutorial')}\n")

        # Problema
        if 'problema' in tutorial_json:
            md_parts.append(f"## Problema\n{tutorial_json['problema']}\n")

        # Prerequisiti
        if 'prerequisiti' in tutorial_json and tutorial_json['prerequisiti']:
            md_parts.append("## Prerequisiti\n")
            for prereq in tutorial_json['prerequisiti']:
                fonte = prereq.get('fonte', '')
                pagina = prereq.get('pagina', '?')
                md_parts.append(f"- {prereq['testo']} [📄 {fonte} - pag {pagina}]\n")

        # Steps
        if 'steps' in tutorial_json and tutorial_json['steps']:
            md_parts.append("\n## Step-by-Step\n")
            for step in tutorial_json['steps']:
                num = step.get('numero', '?')
                titolo = step.get('titolo', '')
                descrizione = step.get('descrizione', '')
                dettagli = step.get('dettagli', '')
                fonte = step.get('fonte', '')
                pagina = step.get('pagina', '?')

                md_parts.append(f"\n### Passaggio {num}: {titolo}\n")
                md_parts.append(f"{descrizione}\n")
                if dettagli:
                    md_parts.append(f"\n{dettagli}\n")
                md_parts.append(f"\n**Fonte:** [📄 {fonte} - pag {pagina}]\n")

        # Note
        if 'note' in tutorial_json and tutorial_json['note']:
            md_parts.append("\n## 📝 Note Importanti\n")
            for nota in tutorial_json['note']:
                fonte = nota.get('fonte', '')
                pagina = nota.get('pagina', '?')
                md_parts.append(f"- {nota['testo']} [📄 {fonte} - pag {pagina}]\n")

        # Avvertimenti
        if 'avvertimenti' in tutorial_json and tutorial_json['avvertimenti']:
            md_parts.append("\n## ⚠️ Avvertimenti Importanti\n")
            for avv in tutorial_json['avvertimenti']:
                fonte = avv.get('fonte', '')
                pagina = avv.get('pagina', '?')
                md_parts.append(f"- **ATTENZIONE:** {avv['testo']} [📄 {fonte} - pag {pagina}]\n")

        # Tempo stimato
        if 'tempo_stimato' in tutorial_json:
            md_parts.append(f"\n## ⏱️ Tempo Stimato\n{tutorial_json['tempo_stimato']}\n")

        # Riferimenti
        if 'riferimenti' in tutorial_json and tutorial_json['riferimenti']:
            md_parts.append("\n---\n\n## 📚 Fonti Utilizzate\n")
            for rif in tutorial_json['riferimenti']:
                documento = rif.get('documento', '')
                pagine = rif.get('pagine_citate', [])
                capitoli = rif.get('capitoli', [])
                relevance = rif.get('relevance_score', 0)

                md_parts.append(f"\n**{documento}**\n")
                if pagine:
                    md_parts.append(f"- Pagine: {', '.join(map(str, pagine))}\n")
                if capitoli:
                    md_parts.append(f"- Capitoli: {', '.join(capitoli)}\n")
                md_parts.append(f"- Rilevanza: {relevance:.0%}\n")

        # Aggiungi report verifica se disponibile
        if verification_report:
            md_parts.append(self._format_verification_report(verification_report))

        return "".join(md_parts)

    def _format_verification_report(self, report: Dict) -> str:
        """Formatta report verifica citazioni in markdown."""
        md_parts = ["\n---\n\n## 📊 Verifica Citazioni\n"]

        total = report.get('total', 0)
        verified = report.get('verified', 0)
        accuracy = report.get('accuracy', 0)

        md_parts.append(f"\n**Accuracy Complessiva: {accuracy:.0%} ({verified}/{total} citazioni verificate)**\n")

        if 'issues' in report and report['issues']:
            md_parts.append("\n### ⚠️ Citazioni da Verificare\n")
            for issue in report['issues']:
                md_parts.append(f"- {issue}\n")

        return "".join(md_parts)


if __name__ == "__main__":
    # Test Tutorial Generator
    print("Testing Tutorial Generator...")

    gen = TutorialGenerator()
    print("✓ Tutorial Generator initialized")

    # Test con mock data
    mock_chunks = [
        (
            "[PAGE 5]\nPer resettare il dispositivo, tenere premuto il pulsante Power per 10 secondi.",
            {'source_file': 'Manuale.pdf'},
            0.95
        )
    ]

    result = gen.generate_tutorial(
        "Come resettare il dispositivo?",
        mock_chunks,
        verify_citations=False
    )

    if result['success']:
        print("\n✓ Tutorial generato con successo!")
        print("\n" + "="*70)
        print(result['tutorial_markdown'][:500])
        print("="*70)
    else:
        print(f"\n✗ Errore: {result['message']}")
