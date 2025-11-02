# 🚀 Guida Installazione Rapida

## Step 1: Aggiorna pip (Raccomandato)

```bash
python -m pip install --upgrade pip
```

## Step 2: Installa Dipendenze

### Opzione A: Installazione Standard (Raccomandato)

```bash
pip install -r requirements.txt
```

### Opzione B: Installazione Step-by-Step (se Option A fallisce)

Se incontri errori con `requirements.txt`, installa i componenti separatamente:

```bash
# 1. Core dependencies
pip install gradio flask flask-cors

# 2. Ollama client
pip install ollama

# 3. LlamaIndex (può richiedere tempo)
pip install llama-index llama-index-core
pip install llama-index-embeddings-huggingface
pip install llama-index-vector-stores-chroma

# 4. Vector database
pip install chromadb

# 5. Document processing
pip install pypdf python-docx

# 6. NLP & Embeddings
pip install sentence-transformers transformers

# 7. Text similarity
pip install fuzzywuzzy python-Levenshtein

# 8. Additional
pip install requests markdown numpy pandas
```

### Opzione C: Versione Minima (Solo componenti essenziali)

Se hai problemi di compatibilità, installa solo l'essenziale:

```bash
pip install gradio flask flask-cors ollama
pip install llama-index chromadb
pip install pypdf python-docx
pip install sentence-transformers
```

## Step 3: Setup Ollama

### Installa Ollama

**macOS:**
```bash
brew install ollama
# oppure scarica da https://ollama.ai
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
- Scarica installer da: https://ollama.ai/download

### Scarica Modello Mistral

```bash
ollama pull mistral
```

**Nota:** Download ~4GB, può richiedere 10-30 minuti

### Avvia Ollama Server

**In un terminal separato (lasciarlo aperto):**
```bash
ollama serve
```

## Step 4: Verifica Installazione

```bash
# Test Ollama
ollama list

# Dovresti vedere:
# NAME           	ID          	SIZE  	MODIFIED
# mistral:latest	...         	4.1 GB	X days ago

# Test Python imports
python -c "import gradio; import ollama; import chromadb; print('✅ All OK!')"
```

## Step 5: Avvia Applicazione

```bash
python main.py
```

Apri browser: **http://localhost:7860**

---

## 🔧 Troubleshooting

### Errore: "No module named 'llama_index'"

```bash
pip install llama-index-core
pip install llama-index-embeddings-huggingface
pip install llama-index-vector-stores-chroma
```

### Errore: "Cannot import chromadb"

```bash
pip uninstall chromadb
pip install chromadb --no-cache-dir
```

### Errore: "Ollama connection failed"

```bash
# Verifica Ollama in esecuzione
ps aux | grep ollama

# Se non c'è, avvia:
ollama serve
```

### Errore: Versioni incompatibili

```bash
# Crea nuovo virtual environment
python -m venv venv_new
source venv_new/bin/activate  # Linux/macOS
# venv_new\Scripts\activate  # Windows

# Installa da zero
pip install --upgrade pip
pip install -r requirements.txt
```

### Per M1/M2 Mac

```bash
# Usa conda invece di venv
conda create -n tutorial-rag python=3.10
conda activate tutorial-rag
pip install -r requirements.txt
```

---

## 📦 Requisiti Minimi Sistema

- **Python**: 3.10+
- **RAM**: 8GB (16GB raccomandato)
- **Storage**: 10GB libero
- **OS**: Linux, macOS, Windows

---

## ✅ Checklist Installazione

- [ ] pip aggiornato (`pip --version` >= 24.0)
- [ ] Python 3.10+ (`python --version`)
- [ ] Virtual environment attivato
- [ ] requirements.txt installato senza errori
- [ ] Ollama installato e funzionante (`ollama list`)
- [ ] Modello Mistral scaricato (~4GB)
- [ ] Ollama server in esecuzione (`ollama serve`)
- [ ] Applicazione avviata (`python main.py`)
- [ ] Browser aperto su http://localhost:7860

---

## 🆘 Hai ancora problemi?

1. Controlla logs: `tail -f app.log`
2. Riavvia Ollama: `pkill ollama && ollama serve`
3. Verifica versione Python: `python --version` (deve essere >= 3.10)
4. Prova versione minima (Opzione C sopra)

---

**Supporto**: Vedi README.md sezione Troubleshooting
