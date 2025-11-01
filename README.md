# 📚 Tutorial Generator RAG

**Genera tutorial passo-passo da manuali tecnici usando AI locale (Ollama + Mistral)**

Un'applicazione web completa per creare tutorial interattivi basata su RAG (Retrieval-Augmented Generation) con stack 100% gratuito e open-source.

---

## ✨ Features

- 📤 **Upload e Indicizzazione Documenti**: Carica PDF, DOCX, TXT con drag-and-drop
- 🔍 **Ricerca Semantica**: Trova informazioni rilevanti nei manuali con AI
- 🤖 **Generazione Tutorial**: Crea guide passo-passo con citazioni verificate
- ✅ **Verifica Citazioni**: Validazione automatica delle fonti
- 📄 **PDF Viewer Integrato**: Visualizza documenti con highlighting
- 📊 **Report & Export**: Storico tutorial e export in Markdown/HTML
- 🚀 **100% Locale**: Nessun costo API, tutto offline

---

## 🛠️ Stack Tecnologico

| Componente | Tecnologia |
|------------|------------|
| **Frontend** | Gradio 4.32 |
| **Backend** | Flask 3.0 + Python 3.10+ |
| **LLM** | Ollama + Mistral 7B |
| **RAG Framework** | LlamaIndex |
| **Embedding** | all-MiniLM-L6-v2 (HuggingFace) |
| **Vector DB** | Chroma (persistente) |
| **PDF Processing** | PyPDF + PDF.js |

---

## 📋 Prerequisiti

### Sistema
- **Python**: 3.10 o superiore
- **RAM**: 8GB minimo (16GB raccomandato)
- **Storage**: 10GB spazio libero
- **OS**: Linux, macOS, Windows

### Software Richiesto

1. **Python 3.10+**
   ```bash
   python --version  # Verifica versione
   ```

2. **Ollama** (per LLM locale)
   - Scarica da: https://ollama.ai
   - Installa seguendo le istruzioni per il tuo OS

---

## 🚀 Setup e Installazione

### Step 1: Clone Repository

```bash
cd /path/to/your/projects
# Repository già presente in /home/user/manuali
cd manuali
```

### Step 2: Crea Virtual Environment (Raccomandato)

```bash
python -m venv venv

# Attiva environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### Step 3: Installa Dipendenze Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Nota**: L'installazione può richiedere 5-10 minuti.

### Step 4: Setup Ollama

#### 4.1 Installa Ollama

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
brew install ollama
# oppure scarica .dmg da https://ollama.ai
```

**Windows:**
- Scarica installer da: https://ollama.ai/download

#### 4.2 Scarica Modello Mistral

```bash
ollama pull mistral
```

**Nota**: Download ~4GB, può richiedere tempo.

#### 4.3 Avvia Ollama Server

**In un terminale separato:**
```bash
ollama serve
```

**Lascia questo terminale aperto!** Ollama deve rimanere in esecuzione.

### Step 5: Verifica Setup

```bash
# Verifica Ollama
ollama list

# Dovresti vedere:
# NAME           	ID          	SIZE  	MODIFIED
# mistral:latest	...         	4.1 GB	X days ago
```

---

## 🎯 Avvio Applicazione

### Avvio Standard

```bash
# Terminal 1: Ollama (se non già avviato)
ollama serve

# Terminal 2: Applicazione
python main.py
```

### Output Atteso

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           📚 TUTORIAL GENERATOR RAG                           ║
║                                                               ║
║           Genera tutorial da manuali con AI locale           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

✅ Server pronto!

🌐 Apri nel browser:
   → http://localhost:7860
```

### Opzioni Avvio

```bash
# Porta custom
python main.py --port 8080

# Debug mode
python main.py --debug

# Skip prerequisiti check
python main.py --skip-checks

# Share pubblico (link Gradio)
python main.py --share
```

---

## 📖 Utilizzo

### 1. Carica Documenti

1. Apri browser: http://localhost:7860
2. Vai alla tab **"📤 Carica Documenti"**
3. Trascina file PDF/DOCX/TXT (max 50MB per file)
4. Click **"Carica e Indicizza"**
5. Attendi elaborazione (progress real-time)

**Formati supportati:**
- PDF (`.pdf`)
- Word (`.docx`)
- Testo (`.txt`)

### 2. Ricerca nei Manuali

1. Tab **"🔍 Cerca nel Manuale"**
2. Inserisci query (es: "Come resettare il dispositivo?")
3. Seleziona numero risultati (3-10)
4. Click **"Ricerca"**
5. Visualizza risultati con:
   - Testo rilevante
   - Fonte + pagina
   - Similarity score
   - Link PDF viewer

### 3. Genera Tutorial

1. Tab **"🤖 Genera Tutorial"**
2. Inserisci problema/domanda
3. Opzioni:
   - ☑️ Usa risultati ultima ricerca
   - ☑️ Verifica citazioni automaticamente
4. Click **"Genera Tutorial"**
5. Attendi generazione (30-60 secondi)

**Output include:**
- Tutorial passo-passo strutturato
- Citazioni con link cliccabili
- Fonti utilizzate
- Report verifica citazioni
- Accuracy score

### 4. Visualizza PDF

1. Tab **"📄 Viewer PDF"**
2. Seleziona documento
3. Scegli pagina
4. Click **"Apri PDF Viewer"**

**Features viewer:**
- Navigazione pagine (◀ ▶)
- Zoom (+/-)
- Ricerca testo
- Highlighting

### 5. Report & Export

**Export Tutorial:**
- Tab "Genera Tutorial" → Sezione "Export"
- Formati: Markdown, HTML
- File salvati in `./export/`

**Report Citazioni:**
- Tab **"📊 Report Citazioni"**
- Storico tutorial generati
- Export CSV con statistiche

---

## 📁 Struttura Progetto

```
manuali/
├── main.py                 # Entry point
├── config.py               # Configurazioni
├── rag_engine.py          # RAG e indicizzazione
├── llm_handler.py         # Generazione tutorial
├── citation_verifier.py   # Verifica citazioni
├── citation_link_gen.py   # Link PDF cliccabili
├── pdf_viewer.py          # Viewer PDF integrato
├── gradio_ui.py           # Interfaccia Gradio
├── requirements.txt       # Dipendenze Python
├── README.md              # Questa guida
│
├── uploads/               # Documenti caricati (auto-generato)
├── chroma_db/             # Vector database (auto-generato)
├── export/                # Tutorial esportati (auto-generato)
├── static/                # Assets statici
│   └── pdf.js/           # PDF.js library
│
└── app.log               # Log applicazione
```

---

## ⚙️ Configurazione

Modifica `config.py` per personalizzare:

```python
# Modello LLM
OLLAMA_MODEL = "mistral"  # o "llama2", "codellama", ecc.

# Parametri RAG
CHUNK_SIZE = 512          # Dimensione chunk testo
CHUNK_OVERLAP = 50        # Overlap tra chunk
TOP_K_RETRIEVAL = 5       # Numero risultati RAG

# Verifica citazioni
ENABLE_CITATION_VERIFICATION = True
CITATION_VERIFICATION_THRESHOLD = 0.80

# Server
FLASK_PORT = 5000
GRADIO_PORT = 7860
```

---

## 🔧 Troubleshooting

### Problema: "Ollama non raggiungibile"

**Soluzione:**
```bash
# Verifica Ollama in esecuzione
ps aux | grep ollama

# Avvia Ollama
ollama serve

# Testa connessione
ollama list
```

### Problema: "Modello non trovato"

**Soluzione:**
```bash
# Scarica Mistral
ollama pull mistral

# Verifica download
ollama list
```

### Problema: "Out of Memory"

**Cause**: Mistral 7B richiede ~8GB RAM

**Soluzioni:**
1. Chiudi altre applicazioni
2. Usa modello più leggero:
   ```bash
   ollama pull mistral:7b-instruct-q4_0  # Quantizzato
   ```
3. Modifica `config.py`:
   ```python
   OLLAMA_MODEL = "mistral:7b-instruct-q4_0"
   ```

### Problema: "ChromaDB errore"

**Soluzione:**
```bash
# Reinstalla ChromaDB
pip uninstall chromadb
pip install chromadb --no-cache-dir

# Reset database (ATTENZIONE: cancella documenti indicizzati)
rm -rf chroma_db/
```

### Problema: "Import Error: llama_index"

**Soluzione:**
```bash
# Reinstalla LlamaIndex componenti
pip install llama-index-core==0.10.0
pip install llama-index-embeddings-huggingface
pip install llama-index-vector-stores-chroma
```

### Problema: "Tutorial non generato"

**Possibili cause:**
1. Nessun documento caricato → Carica almeno 1 manuale
2. Query troppo generica → Sii più specifico
3. Ollama timeout → Aumenta `OLLAMA_TIMEOUT` in `config.py`

---

## 📊 Performance

### Tempi Medi (Hardware: 16GB RAM, CPU i7)

| Operazione | Tempo |
|------------|-------|
| Upload PDF 10 pagine | ~3-5 secondi |
| Ricerca semantica | <1 secondo |
| Generazione tutorial | 30-60 secondi |
| Verifica citazioni | 2-5 secondi |

### Ottimizzazione

**Per velocizzare generazione:**
1. Usa GPU (se disponibile):
   ```bash
   # Install PyTorch con CUDA
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

2. Riduci `TOP_K_RETRIEVAL` in `config.py`:
   ```python
   TOP_K_RETRIEVAL = 3  # invece di 5
   ```

3. Usa modello quantizzato:
   ```bash
   ollama pull mistral:7b-instruct-q4_0
   ```

---

## 🧪 Testing

### Test Componenti Individuali

```bash
# Test RAG Engine
python rag_engine.py

# Test LLM Handler
python llm_handler.py

# Test Citation Verifier
python citation_verifier.py

# Test PDF Viewer
python pdf_viewer.py
```

---

## 🔒 Sicurezza e Privacy

- ✅ **100% Locale**: Nessun dato inviato a servizi esterni
- ✅ **Offline**: Funziona senza internet (dopo download modelli)
- ✅ **Privacy**: Manuali aziendali rimangono sul tuo computer
- ✅ **Open Source**: Codice completamente ispezionabile

---

## 🛣️ Roadmap

### Fase 2 (Prossimi Sviluppi)

- [ ] Export PDF con link embedded funzionanti
- [ ] Multi-lingua (EN, ES, FR, DE)
- [ ] Fine-tuning prompt per dominio specifico
- [ ] Analytics dashboard (documenti più usati, query frequenti)
- [ ] Integrazione OCR per PDF scansionati
- [ ] API REST per integrazione esterna
- [ ] Supporto video tutorial (YouTube search correlati)
- [ ] Collaborative editing (condivisione tutorial con team)

---

## 🤝 Contributi

Contributi benvenuti! Per proporre modifiche:

1. Fork repository
2. Crea branch: `git checkout -b feature/nuova-funzionalità`
3. Commit: `git commit -m "Aggiunta nuova funzionalità"`
4. Push: `git push origin feature/nuova-funzionalità`
5. Apri Pull Request

---

## 📝 Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi `LICENSE` per dettagli.

---

## 🙏 Crediti

### Tecnologie Utilizzate

- **Ollama**: https://ollama.ai
- **LlamaIndex**: https://www.llamaindex.ai
- **Gradio**: https://gradio.app
- **Chroma**: https://www.trychroma.com
- **HuggingFace**: https://huggingface.co
- **PDF.js**: https://mozilla.github.io/pdf.js

### Autore

**Claude Code** - Tutorial Generator RAG
Build Date: 2025-11-01
Version: 1.0.0

---

## 📞 Supporto

### Documentazione

- **LlamaIndex Docs**: https://docs.llamaindex.ai
- **Ollama Docs**: https://github.com/ollama/ollama
- **Gradio Docs**: https://gradio.app/docs

### Problemi?

1. Controlla logs: `tail -f app.log`
2. Verifica prerequisiti: `python main.py` (check automatico)
3. Consulta sezione Troubleshooting

---

## 🎓 Tutorial Quick Start

### Esempio: Manuale Dispositivo IoT

```bash
# 1. Avvia applicazione
python main.py

# 2. Browser → http://localhost:7860

# 3. Tab "Carica Documenti"
#    - Upload: manuale_dispositivo_iot.pdf

# 4. Tab "Genera Tutorial"
#    - Query: "Come configurare WiFi sul dispositivo?"
#    - ☑️ Verifica citazioni
#    - Click "Genera Tutorial"

# 5. Output:
#    ✅ Tutorial con 5 step
#    ✅ Citazioni verificate: 12/12 (100%)
#    ✅ Fonti: manuale_dispositivo_iot.pdf (pag 14, 15, 18)
```

---

**Buon lavoro! 🚀**
