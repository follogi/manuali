"""
RAG Engine per indicizzazione documenti e ricerca semantica.
Gestisce upload, chunking, embedding e retrieval con metadata tracking completo.
"""

import os
import shutil
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Any, Optional
import re

# Document processing
import pypdf
from docx import Document as DocxDocument

# LlamaIndex imports
try:
    from llama_index.core import (
        VectorStoreIndex,
        Document,
        StorageContext,
        Settings
    )
    from llama_index.core.node_parser import SimpleNodeParser
    from llama_index.vector_stores.chroma import ChromaVectorStore
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    import chromadb
except ImportError as e:
    print(f"Warning: LlamaIndex imports failed: {e}")
    print("Install with: pip install llama-index llama-index-vector-stores-chroma llama-index-embeddings-huggingface")

import config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Motore RAG per gestione documenti e ricerca semantica.

    Features:
    - Upload e indicizzazione documenti (PDF, DOCX, TXT)
    - Chunking intelligente con overlap
    - Estrazione metadata completi
    - Ricerca semantica con similarity scores
    - Source tracking per ogni chunk
    - Persistenza su Chroma DB
    """

    def __init__(self):
        """Inizializza il RAG Engine con Chroma DB e embedding model."""
        logger.info("Inizializzazione RAG Engine...")

        # Setup embedding model
        self.embedding_model = HuggingFaceEmbedding(
            model_name=config.EMBEDDING_MODEL
        )

        # Configure LlamaIndex settings
        Settings.embed_model = self.embedding_model
        Settings.chunk_size = config.CHUNK_SIZE
        Settings.chunk_overlap = config.CHUNK_OVERLAP

        # IMPORTANTE: Disabilita LLM di default (usiamo solo embeddings per RAG)
        # L'LLM (Ollama) viene usato solo in llm_handler.py per generazione tutorial
        Settings.llm = None

        # Initialize Chroma DB
        self.chroma_client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)

        try:
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="documents",
                metadata={"description": "Tutorial documents collection"}
            )
        except Exception as e:
            logger.warning(f"Collection già esistente o errore: {e}")
            self.chroma_collection = self.chroma_client.get_collection("documents")

        # Create vector store
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)

        # Create storage context
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )

        # Try to load existing index or create new one
        try:
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store,
                storage_context=self.storage_context
            )
            logger.info("Indice esistente caricato")
        except Exception as e:
            logger.info(f"Creazione nuovo indice: {e}")
            self.index = VectorStoreIndex(
                [],
                storage_context=self.storage_context
            )

        # Document tracking
        self.indexed_docs: Dict[str, Dict[str, Any]] = {}
        self._load_indexed_docs()

        logger.info(f"RAG Engine inizializzato. Documenti caricati: {len(self.indexed_docs)}")

    def upload_documents(self, files: List[str]) -> Dict[str, Any]:
        """
        Carica e indicizza documenti con metadata completi.

        Args:
            files: Lista di percorsi file da caricare

        Returns:
            Dict con risultati: {
                'success': bool,
                'message': str,
                'documents_processed': int,
                'chunks_created': int,
                'details': List[Dict]
            }
        """
        logger.info(f"Upload di {len(files)} documenti...")

        results = {
            'success': True,
            'message': '',
            'documents_processed': 0,
            'chunks_created': 0,
            'details': []
        }

        for file_path in files:
            try:
                # Validazione file
                validation = self._validate_file(file_path)
                if not validation['valid']:
                    results['details'].append({
                        'file': os.path.basename(file_path),
                        'status': 'error',
                        'message': validation['error']
                    })
                    continue

                # Estrai testo e metadata
                start_time = datetime.now()
                text_content = self._extract_text(file_path)

                if not text_content or len(text_content.strip()) < 10:
                    results['details'].append({
                        'file': os.path.basename(file_path),
                        'status': 'error',
                        'message': 'Contenuto vuoto o troppo breve'
                    })
                    continue

                # Estrai metadata
                metadata = self._extract_metadata(file_path)

                # Copia file nella cartella uploads
                dest_path = os.path.join(config.UPLOADS_PATH, os.path.basename(file_path))
                if file_path != dest_path:
                    shutil.copy2(file_path, dest_path)

                # Crea documento LlamaIndex
                doc = Document(
                    text=text_content,
                    metadata=metadata
                )

                # Aggiungi al index
                self.index.insert(doc)

                # Calcola chunks creati (stima)
                chunks_count = len(text_content) // config.CHUNK_SIZE + 1

                # Tracking
                doc_id = metadata['doc_id']
                self.indexed_docs[doc_id] = {
                    'filename': metadata['source_file'],
                    'filepath': dest_path,
                    'file_type': metadata['file_type'],
                    'file_size': metadata['file_size'],
                    'upload_timestamp': metadata['upload_timestamp'],
                    'chunks_count': chunks_count,
                    'page_count': metadata.get('page_count', 0)
                }

                processing_time = (datetime.now() - start_time).total_seconds()

                results['documents_processed'] += 1
                results['chunks_created'] += chunks_count
                results['details'].append({
                    'file': metadata['source_file'],
                    'status': 'success',
                    'chunks': chunks_count,
                    'time': f"{processing_time:.2f}s"
                })

                logger.info(f"✓ {metadata['source_file']} indicizzato ({chunks_count} chunks, {processing_time:.2f}s)")

            except Exception as e:
                logger.error(f"Errore durante upload di {file_path}: {e}")
                results['details'].append({
                    'file': os.path.basename(file_path),
                    'status': 'error',
                    'message': str(e)
                })
                results['success'] = False

        # Salva tracking
        self._save_indexed_docs()

        if results['documents_processed'] > 0:
            results['message'] = config.SUCCESS_MESSAGES['upload_complete']
        else:
            results['message'] = "Nessun documento elaborato con successo"
            results['success'] = False

        return results

    def query(self, question: str, top_k: int = None) -> List[Tuple[str, Dict, float]]:
        """
        Esegue ricerca RAG e ritorna chunk con metadata e scores.

        Args:
            question: Query dell'utente
            top_k: Numero di risultati da ritornare (default: config.TOP_K_RETRIEVAL)

        Returns:
            Lista di tuple: [(chunk_text, metadata, similarity_score), ...]
        """
        if top_k is None:
            top_k = config.TOP_K_RETRIEVAL

        logger.info(f"Query: '{question}' (top_k={top_k})")

        try:
            # Recupera più risultati del necessario per diversificazione
            if config.ENABLE_RESULT_DIVERSIFICATION:
                # Recupera 3x per avere scelta
                retrieval_k = top_k * 3
            else:
                retrieval_k = top_k

            # Usa retriever invece of query_engine (non serve LLM)
            retriever = self.index.as_retriever(
                similarity_top_k=retrieval_k
            )

            # Execute retrieval (solo similarity search, no LLM)
            nodes = retriever.retrieve(question)

            # Extract results with metadata
            all_results = []

            for node in nodes:
                chunk_text = node.node.text
                metadata = node.node.metadata
                similarity_score = node.score if hasattr(node, 'score') else 0.0

                # Filter by threshold
                if similarity_score >= config.MIN_RELEVANCE_THRESHOLD:
                    all_results.append((chunk_text, metadata, similarity_score))

            # Diversifica risultati se abilitato
            if config.ENABLE_RESULT_DIVERSIFICATION and len(all_results) > top_k:
                results = self._diversify_results(all_results, top_k)
            else:
                results = all_results[:top_k]

            # Log con conteggio documenti diversi
            unique_docs = len(set(r[1].get('source_file', '') for r in results))
            logger.info(f"Query completata: {len(results)} risultati da {unique_docs} documenti diversi")
            return results

        except Exception as e:
            logger.error(f"Errore durante query: {e}")
            return []

    def get_indexed_docs(self) -> Dict[str, Dict[str, Any]]:
        """
        Ritorna lista documenti indicizzati con metadata.

        Returns:
            Dict con doc_id -> metadata
        """
        return self.indexed_docs

    def delete_document(self, doc_id: str) -> bool:
        """
        Rimuove documento dall'indice.

        Args:
            doc_id: ID del documento da rimuovere

        Returns:
            True se rimosso con successo
        """
        try:
            if doc_id in self.indexed_docs:
                # Rimuovi file
                filepath = self.indexed_docs[doc_id]['filepath']
                if os.path.exists(filepath):
                    os.remove(filepath)

                # Rimuovi da tracking
                del self.indexed_docs[doc_id]
                self._save_indexed_docs()

                logger.info(f"Documento {doc_id} rimosso")
                return True
            return False
        except Exception as e:
            logger.error(f"Errore rimozione documento: {e}")
            return False

    # ========================================================================
    # Private Methods
    # ========================================================================

    def _diversify_results(
        self,
        all_results: List[Tuple[str, Dict, float]],
        top_k: int
    ) -> List[Tuple[str, Dict, float]]:
        """
        Diversifica risultati bilanciando relevance e diversity per documento.

        Algoritmo:
        1. Seleziona chunk con score più alto
        2. Per prossimi chunk, applica penalty se dallo stesso documento
        3. Continua fino a raggiungere top_k risultati

        Args:
            all_results: Tutti i risultati ordinati per relevance
            top_k: Numero di risultati finali desiderati

        Returns:
            Lista diversificata di top_k risultati
        """
        if len(all_results) <= top_k:
            return all_results

        diversified = []
        doc_count = {}  # Conta chunk per documento

        for chunk_text, metadata, score in all_results:
            source_file = metadata.get('source_file', 'unknown')

            # Conta chunk già selezionati da questo documento
            count = doc_count.get(source_file, 0)

            # Applica penalty se già abbiamo chunk da questo documento
            if count > 0:
                penalty = config.DIVERSIFICATION_PENALTY * count
                adjusted_score = score * (1 - penalty)
            else:
                adjusted_score = score

            # Aggiungi a lista con score aggiustato
            diversified.append((chunk_text, metadata, adjusted_score, score))  # score originale come ultimo elemento

        # Riordina per adjusted score
        diversified.sort(key=lambda x: x[2], reverse=True)

        # Seleziona top_k rispettando max_chunks_per_document
        final_results = []
        doc_count = {}

        for chunk_text, metadata, adjusted_score, original_score in diversified:
            source_file = metadata.get('source_file', 'unknown')
            count = doc_count.get(source_file, 0)

            # Controlla limite per documento
            if count < config.MAX_CHUNKS_PER_DOCUMENT:
                final_results.append((chunk_text, metadata, original_score))  # Usa score originale
                doc_count[source_file] = count + 1

                if len(final_results) >= top_k:
                    break

        logger.debug(
            f"Diversificazione: da {len(all_results)} risultati a {len(final_results)}, "
            f"{len(doc_count)} documenti diversi"
        )

        return final_results

    def _validate_file(self, file_path: str) -> Dict[str, Any]:
        """Valida file prima dell'upload."""
        result = {'valid': True, 'error': None}

        # Check esistenza
        if not os.path.exists(file_path):
            result['valid'] = False
            result['error'] = "File non trovato"
            return result

        # Check estensione
        ext = Path(file_path).suffix.lower()
        if ext not in config.SUPPORTED_FILE_TYPES:
            result['valid'] = False
            result['error'] = config.ERROR_MESSAGES['unsupported_format']
            return result

        # Check dimensione
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > config.MAX_FILE_SIZE_MB:
            result['valid'] = False
            result['error'] = config.ERROR_MESSAGES['file_too_large']
            return result

        return result

    def _extract_text(self, file_path: str) -> str:
        """Estrae testo da file (PDF, DOCX, TXT)."""
        ext = Path(file_path).suffix.lower()

        try:
            if ext == '.pdf':
                return self._extract_pdf_text(file_path)
            elif ext == '.docx':
                return self._extract_docx_text(file_path)
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError(f"Formato non supportato: {ext}")
        except Exception as e:
            logger.error(f"Errore estrazione testo da {file_path}: {e}")
            raise

    def _extract_pdf_text(self, file_path: str) -> str:
        """Estrae testo da PDF con PyPDF."""
        text_parts = []

        with open(file_path, 'rb') as f:
            pdf_reader = pypdf.PdfReader(f)

            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    # Aggiungi marker pagina per tracking
                    text_parts.append(f"\n[PAGE {page_num}]\n{page_text}")

        return "\n".join(text_parts)

    def _extract_docx_text(self, file_path: str) -> str:
        """Estrae testo da DOCX."""
        doc = DocxDocument(file_path)
        text_parts = []

        for para_num, para in enumerate(doc.paragraphs, 1):
            if para.text.strip():
                text_parts.append(para.text)

        return "\n".join(text_parts)

    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Estrae metadata completi dal file.

        Returns:
            Dict con metadata: source_file, doc_id, file_type, file_size,
            upload_timestamp, page_count, ecc.
        """
        filename = os.path.basename(file_path)
        file_ext = Path(file_path).suffix.lower()
        file_size = os.path.getsize(file_path)

        # Genera ID univoco per documento
        doc_id = self._generate_doc_id(file_path)

        metadata = {
            'source_file': filename,
            'doc_id': doc_id,
            'file_type': file_ext[1:],  # senza punto
            'file_size': file_size,
            'upload_timestamp': datetime.now().isoformat(),
        }

        # Estrai page count se PDF
        if file_ext == '.pdf':
            try:
                with open(file_path, 'rb') as f:
                    pdf_reader = pypdf.PdfReader(f)
                    metadata['page_count'] = len(pdf_reader.pages)
            except:
                metadata['page_count'] = 0
        else:
            metadata['page_count'] = 0

        return metadata

    def _generate_doc_id(self, file_path: str) -> str:
        """Genera ID univoco per documento basato su nome e timestamp."""
        filename = os.path.basename(file_path)
        timestamp = datetime.now().isoformat()
        hash_input = f"{filename}_{timestamp}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]

    def _create_source_reference(self, doc_name: str, chunk_id: str, page_num: int = None) -> str:
        """
        Crea reference tracciabile per un chunk.

        Returns:
            String formato: "doc_name - pag X" oppure "doc_name"
        """
        if page_num:
            return f"{doc_name} - pag {page_num}"
        return doc_name

    def _load_indexed_docs(self):
        """Carica lista documenti indicizzati da file."""
        tracking_file = os.path.join(config.CHROMA_DB_PATH, "indexed_docs.json")

        if os.path.exists(tracking_file):
            try:
                import json
                with open(tracking_file, 'r') as f:
                    self.indexed_docs = json.load(f)
                logger.info(f"Caricati {len(self.indexed_docs)} documenti dal tracking")
            except Exception as e:
                logger.warning(f"Errore caricamento tracking: {e}")
                self.indexed_docs = {}

    def _save_indexed_docs(self):
        """Salva lista documenti indicizzati su file."""
        tracking_file = os.path.join(config.CHROMA_DB_PATH, "indexed_docs.json")

        try:
            import json
            with open(tracking_file, 'w') as f:
                json.dump(self.indexed_docs, f, indent=2)
            logger.debug("Tracking documenti salvato")
        except Exception as e:
            logger.error(f"Errore salvataggio tracking: {e}")


def extract_page_number_from_text(text: str) -> Optional[int]:
    """
    Estrae il numero di pagina dal testo che contiene marker [PAGE X].

    Args:
        text: Testo del chunk

    Returns:
        Numero pagina o None
    """
    # Cerca pattern [PAGE X]
    match = re.search(r'\[PAGE (\d+)\]', text)
    if match:
        return int(match.group(1))
    return None


if __name__ == "__main__":
    # Test RAG Engine
    print("Testing RAG Engine...")

    engine = RAGEngine()

    print(f"\nDocumenti indicizzati: {len(engine.get_indexed_docs())}")
    for doc_id, info in engine.get_indexed_docs().items():
        print(f"  - {info['filename']} ({info['chunks_count']} chunks)")

    print("\nRAG Engine ready!")
