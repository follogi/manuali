# 🐛 Guida Debug VSCode

Guida completa per debuggare l'applicazione Tutorial Generator RAG in VSCode.

---

## 🚀 Quick Start

### 1. Apri VSCode nel Progetto

```bash
cd /path/to/manuali
code .
```

### 2. Configurazioni di Debug Disponibili

Apri **Run and Debug** (Ctrl+Shift+D / Cmd+Shift+D) e scegli:

| Configurazione | Descrizione | Usa Per |
|----------------|-------------|---------|
| 🚀 **Debug: Main App** | App completa con checks | Debug normale |
| 🐛 **Debug: Main App (Skip Checks)** | Salta verifica Ollama | Debug veloce |
| 🔬 **Debug: RAG Engine Only** | Solo RAG Engine | Test indicizzazione |
| 🤖 **Debug: LLM Handler Only** | Solo LLM Handler | Test generazione |
| ✅ **Debug: Citation Verifier** | Solo verifica citazioni | Test verifica |
| 📄 **Debug: PDF Viewer** | Solo PDF viewer | Test viewer |
| ⚙️ **Debug: Config Test** | Test configurazioni | Verifica config |

### 3. Avvia Debug

**Opzione A: Menu**
1. Seleziona configurazione dal dropdown
2. Premi **F5** (o click su ▶️)

**Opzione B: Keyboard**
- **F5**: Start debugging
- **Ctrl+F5** (Cmd+F5): Run without debugging

---

## 🎯 Come Usare i Breakpoints

### Aggiungere Breakpoint

**Metodo 1: Click**
- Click sulla barra a sinistra del numero di riga (appare pallino rosso 🔴)

**Metodo 2: Keyboard**
- Posiziona cursore sulla riga
- Premi **F9**

### Tipi di Breakpoint

#### 1. Breakpoint Semplice
```python
def upload_documents(self, files):
    logger.info("Upload documenti...")  # ← Click qui
    results = {'success': True}
```

#### 2. Conditional Breakpoint
```python
for i, file in enumerate(files):
    # Right-click breakpoint → Edit Breakpoint → Add Condition
    # Condition: i == 2
    process_file(file)  # Si ferma solo quando i == 2
```

#### 3. Logpoint (No Stop, Solo Log)
```python
def query(self, question):
    # Right-click → Add Logpoint
    # Message: Query ricevuta: {question}
    results = self.search(question)
```

---

## 🔍 Debugging Step-by-Step

### Comandi Base

| Comando | Shortcut | Descrizione |
|---------|----------|-------------|
| **Continue** | F5 | Continua fino a prossimo breakpoint |
| **Step Over** | F10 | Esegui riga corrente, salta dentro funzioni |
| **Step Into** | F11 | Entra dentro funzione chiamata |
| **Step Out** | Shift+F11 | Esci da funzione corrente |
| **Restart** | Ctrl+Shift+F5 | Riavvia debug |
| **Stop** | Shift+F5 | Ferma debug |

### Esempio Pratico

```python
# 1. Metti breakpoint qui ⬇️
def generate_tutorial(self, question, context_chunks):
    # 2. F5 per avviare debug
    # 3. Esecuzione si ferma qui ⬆️

    # 4. Ispeziona variabili nel panel VARIABLES
    prompt = self._build_prompt(question, context_chunks)

    # 5. F11 per entrare dentro _build_prompt
    # 6. F10 per andare alla riga successiva
    response = self._call_ollama(prompt)

    # 7. Shift+F11 per uscire
    return response
```

---

## 📊 Panel di Debug

### 1. **VARIABLES** (Variabili)

Mostra tutte le variabili nello scope corrente:
```
Local:
  question = "Come resettare dispositivo?"
  context_chunks = [(chunk1, metadata1, 0.95), ...]
  self = <TutorialGenerator object>

Global:
  config = <module 'config'>
  logger = <Logger object>
```

**Tip**: Right-click → **Add to Watch** per monitorare variabile specifica

### 2. **WATCH** (Osservatori)

Aggiungi espressioni da monitorare:
```
question.upper()
len(context_chunks)
config.OLLAMA_MODEL
self.model
```

### 3. **CALL STACK** (Stack Chiamate)

Mostra la catena di chiamate:
```
generate_tutorial_handler (gradio_ui.py:345)
  ↓
generate_tutorial (llm_handler.py:78)
  ↓
_call_ollama (llm_handler.py:156)  ← Sei qui
```

Click su qualsiasi frame per vedere variabili in quel contesto.

### 4. **DEBUG CONSOLE**

Console interattiva durante debug:
```python
# Esegui codice al volo
>>> question
'Come resettare dispositivo?'

>>> len(context_chunks)
5

>>> context_chunks[0][2]
0.95

# Chiama funzioni
>>> self._normalize_text(question)
'come resettare dispositivo'
```

---

## 🎨 Debug Scenari Comuni

### Scenario 1: Debug Upload Documenti

**File**: `rag_engine.py`

```python
def upload_documents(self, files):
    # Breakpoint 1: Inizio funzione
    logger.info(f"Upload di {len(files)} documenti...")

    for file_path in files:
        # Breakpoint 2: Ogni file
        validation = self._validate_file(file_path)

        if not validation['valid']:
            # Breakpoint 3: Solo se errore
            # Condition: validation['valid'] == False
            logger.error(validation['error'])
```

**Run**: 🚀 Debug: Main App → Upload file in UI → Si ferma ai breakpoint

### Scenario 2: Debug Ricerca RAG

**File**: `rag_engine.py`

```python
def query(self, question, top_k=5):
    # Breakpoint 1: Inizio query
    logger.info(f"Query: '{question}'")

    retriever = self.index.as_retriever(similarity_top_k=top_k)

    # Breakpoint 2: Prima di retrieve
    nodes = retriever.retrieve(question)

    # Breakpoint 3: Dopo retrieve
    # Watch: len(nodes), nodes[0].score
    for node in nodes:
        chunk_text = node.node.text
        # Breakpoint 4: Dentro loop
        # Condition: node.score > 0.8
```

**Run**: 🚀 Debug: Main App → Fai ricerca in UI

### Scenario 3: Debug Generazione Tutorial

**File**: `llm_handler.py`

```python
def generate_tutorial(self, question, context_chunks):
    # Breakpoint 1
    source_map = self._create_source_map(context_chunks)

    # Breakpoint 2
    prompt = self._build_prompt(question, context_chunks)

    # Breakpoint 3: Prima chiamata Ollama
    response_text = self._call_ollama(prompt)

    # Breakpoint 4: Dopo risposta
    # Watch: len(response_text), response_text[:100]
    tutorial_json = self._parse_json_response(response_text)
```

**Run**: 🤖 Debug: LLM Handler Only

### Scenario 4: Debug Errori Ollama

**File**: `llm_handler.py`

```python
def _call_ollama(self, prompt):
    try:
        # Breakpoint 1: Prima chiamata
        response = ollama.chat(model=self.model, messages=[...])

        # Breakpoint 2: Dopo risposta
        return response['message']['content']

    except Exception as e:
        # Breakpoint 3: Solo su errore
        logger.error(f"Errore Ollama: {e}")
        raise
```

**Watch Expressions**:
```
self.model
len(prompt)
response.keys()  # Dopo breakpoint 2
```

---

## 🔧 Configurazioni Avanzate

### Debug con Args Personalizzati

Edit `.vscode/launch.json`:

```json
{
    "name": "Debug: Custom Port",
    "type": "debugpy",
    "request": "launch",
    "program": "${workspaceFolder}/main.py",
    "args": [
        "--port", "8080",
        "--skip-checks"
    ]
}
```

### Debug con Environment Variables

```json
{
    "name": "Debug: Custom Env",
    "env": {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "LOG_LEVEL": "DEBUG",
        "DEBUG_RAG_ENGINE": "true"
    }
}
```

### Debug Attach (App Già in Esecuzione)

**1. Modifica `main.py` (temporaneo)**:
```python
# Aggiungi all'inizio di main()
import debugpy
debugpy.listen(5678)
print("⏸️ Waiting for debugger...")
debugpy.wait_for_client()  # Opzionale: aspetta connessione
```

**2. Avvia app normalmente**:
```bash
python main.py
```

**3. In VSCode**: Seleziona **🔗 Debug: Attach to Running App** e premi F5

---

## 💡 Tips & Tricks

### 1. Logging Durante Debug

```python
# Invece di breakpoint, usa logging temporaneo
import logging
logger = logging.getLogger(__name__)

def some_function(data):
    logger.debug(f"🐛 DEBUG: data = {data}")  # Solo in debug mode
    # ...
```

### 2. pdb Breakpoint (Alternativa)

```python
def problematic_function():
    # Hard-coded breakpoint
    import pdb; pdb.set_trace()  # Si ferma qui sempre
    # oppure (Python 3.7+):
    breakpoint()
```

### 3. Conditional Import per Debug

```python
# config.py
DEBUG_MODE = True  # Cambia a False in produzione

# main.py
if config.DEBUG_MODE:
    import debugpy
    debugpy.listen(5678)
```

### 4. Pretty Print nel Debug Console

```python
# Nel DEBUG CONSOLE:
>>> import pprint
>>> pprint.pprint(tutorial_json)
{
    'titolo': 'Tutorial Reset',
    'steps': [
        {'numero': 1, 'descrizione': '...'},
        ...
    ]
}
```

### 5. Inspect Objects

```python
# Nel DEBUG CONSOLE:
>>> dir(self)  # Tutti i metodi/attributi
>>> vars(self)  # Tutti gli attributi come dict
>>> type(context_chunks)
>>> isinstance(question, str)
```

---

## 🚨 Troubleshooting Debug

### Problema: "debugpy not found"

```bash
pip install debugpy
```

### Problema: Breakpoint Ignorati

**Cause**:
1. `justMyCode: true` in launch.json → Cambia a `false`
2. Codice non raggiunto (logica prima del breakpoint)
3. File non salvato → Salva (Ctrl+S)

### Problema: Variabili Non Visibili

- Controlla che `justMyCode: false` in launch.json
- Clicca su frame corretto in CALL STACK

### Problema: Debug Lento

- Rimuovi breakpoint inutilizzati
- Usa Logpoints invece di breakpoint + print
- Disabilita auto-reload: rimuovi `"autoReload": {"enable": true}`

---

## 📚 Risorse VSCode

- [VSCode Python Debugging](https://code.visualstudio.com/docs/python/debugging)
- [Debugpy Documentation](https://github.com/microsoft/debugpy)
- Keyboard Shortcuts: **Ctrl+K Ctrl+S** (Cmd+K Cmd+S su Mac)

---

## 🎓 Workflow Consigliato

1. **Identifica Problema**: Errore specifico o comportamento inatteso?
2. **Breakpoint Strategico**: Metti breakpoint PRIMA del codice sospetto
3. **Avvia Debug**: F5 con configurazione appropriata
4. **Ispeziona Variabili**: Controlla valori nel panel VARIABLES
5. **Step Through**: F10/F11 per seguire esecuzione
6. **Fix & Test**: Correggi codice e riavvia debug
7. **Rimuovi Breakpoint**: Quando risolto

---

**Happy Debugging!** 🐛🔍
