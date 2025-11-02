# 🎯 Diversificazione Risultati RAG

Guida alla configurazione del sistema di diversificazione risultati per bilanciare relevance e diversity tra documenti.

---

## 🐛 Il Problema

### Scenario Tipico

Hai caricato 3 manuali:
```
├── ManualeLungo.pdf    → 500 chunks
├── ManualeCorto.pdf    → 50 chunks
└── Guida.pdf           → 30 chunks
```

**Query**: "Come cambiare olio motore"

**PRIMA (senza diversificazione)**:
```
Top-5 Risultati:
1. ManualeLungo.pdf - chunk 234 (score: 0.85)
2. ManualeLungo.pdf - chunk 235 (score: 0.84)
3. ManualeLungo.pdf - chunk 236 (score: 0.83)
4. ManualeLungo.pdf - chunk 233 (score: 0.82)
5. ManualeCorto.pdf - chunk 12  (score: 0.81)
```

**Problema**: 4/5 risultati dallo stesso documento!

### Perché Succede?

1. **Statistica**: Più chunks = più probabilità di match
2. **Clustering**: Chunks vicini nel testo hanno scores simili
3. **Nessuna diversità**: Il retriever ordina solo per score

---

## ✅ La Soluzione

### DOPO (con diversificazione):
```
Top-5 Risultati:
1. ManualeLungo.pdf - chunk 234 (score: 0.85)  ← Migliore assoluto
2. ManualeCorto.pdf - chunk 12  (score: 0.81)  ← Diverso documento
3. ManualeLungo.pdf - chunk 235 (score: 0.84)  ← Max 2 per documento
4. Guida.pdf        - chunk 8   (score: 0.75)  ← Terzo documento
5. ManualeCorto.pdf - chunk 13  (score: 0.73)  ← Diversità
```

**Risultato**: 2 chunks per 3 documenti diversi! 🎉

---

## ⚙️ Configurazione

### File: `config.py`

```python
# Diversificazione risultati
ENABLE_RESULT_DIVERSIFICATION = True  # On/off
DIVERSIFICATION_PENALTY = 0.3         # Penalty duplicati (0-1)
MAX_CHUNKS_PER_DOCUMENT = 2           # Max chunk per documento
```

### Parametri Spiegati

#### 1. `ENABLE_RESULT_DIVERSIFICATION`

**Tipo**: Boolean
**Default**: `True`
**Descrizione**: Abilita/disabilita diversificazione

```python
# Disabilita per avere solo i top-K per score (comportamento originale)
ENABLE_RESULT_DIVERSIFICATION = False

# Abilita per bilanciare tra documenti
ENABLE_RESULT_DIVERSIFICATION = True
```

**Quando disabilitare**:
- Hai un solo documento caricato
- Vuoi massima relevance senza diversity
- Testing/debugging

#### 2. `DIVERSIFICATION_PENALTY`

**Tipo**: Float (0.0 - 1.0)
**Default**: `0.3`
**Descrizione**: Penalty applicato a chunks duplicati dallo stesso documento

**Funzionamento**:
```python
# Primo chunk da ManualeLungo.pdf
chunk1_score = 0.85
adjusted_score = 0.85 * (1 - 0) = 0.85  # Nessuna penalty

# Secondo chunk da ManualeLungo.pdf
chunk2_score = 0.84
adjusted_score = 0.84 * (1 - 0.3*1) = 0.588  # -30% penalty

# Terzo chunk da ManualeLungo.pdf
chunk3_score = 0.83
adjusted_score = 0.83 * (1 - 0.3*2) = 0.332  # -60% penalty
```

**Valori Consigliati**:
- `0.1-0.2`: Penalty leggera (poca diversificazione)
- `0.3`: **Bilanciato** (default) ✅
- `0.4-0.6`: Penalty forte (massima diversità)
- `0.7-1.0`: Penalty molto forte (quasi 1 chunk per documento)

**Esempio**:
```python
# Poca diversificazione
DIVERSIFICATION_PENALTY = 0.1

# Molta diversificazione
DIVERSIFICATION_PENALTY = 0.5
```

#### 3. `MAX_CHUNKS_PER_DOCUMENT`

**Tipo**: Integer (1-10)
**Default**: `2`
**Descrizione**: Numero massimo di chunks dallo stesso documento

**Esempi**:
```python
# Massimo 1 chunk per documento (massima diversità)
MAX_CHUNKS_PER_DOCUMENT = 1
# Risultato: ogni documento compare max 1 volta

# Massimo 2 chunks per documento (bilanciato)
MAX_CHUNKS_PER_DOCUMENT = 2  # ✅ Default
# Risultato: ogni documento compare max 2 volte

# Massimo 3 chunks per documento
MAX_CHUNKS_PER_DOCUMENT = 3
# Risultato: permette più chunks da stesso documento se molto rilevanti
```

**Quando modificare**:
- **=1**: Vuoi vedere tanti documenti diversi
- **=2**: Bilanciamento ideale ✅
- **=3+**: Hai pochi documenti o vuoi privilegiare relevance

---

## 🔬 Come Funziona l'Algoritmo

### Step-by-Step

```python
def _diversify_results(all_results, top_k=5):
    """
    Input: 15 risultati ordinati per score
    Output: 5 risultati diversificati
    """

    # 1. Per ogni chunk, calcola adjusted_score
    for chunk in all_results:
        count = quanti_chunks_gia_selezionati(chunk.documento)

        if count > 0:
            penalty = DIVERSIFICATION_PENALTY * count
            adjusted_score = chunk.score * (1 - penalty)
        else:
            adjusted_score = chunk.score  # Nessuna penalty

    # 2. Riordina per adjusted_score
    all_results.sort(by=adjusted_score, reverse=True)

    # 3. Seleziona top-K rispettando MAX_CHUNKS_PER_DOCUMENT
    results = []
    doc_count = {}

    for chunk in all_results:
        if doc_count[chunk.documento] < MAX_CHUNKS_PER_DOCUMENT:
            results.append(chunk)
            doc_count[chunk.documento] += 1

        if len(results) >= top_k:
            break

    return results
```

### Esempio Pratico

**Input**: 15 risultati
```
1. DocA chunk1: 0.85
2. DocA chunk2: 0.84
3. DocB chunk1: 0.81
4. DocA chunk3: 0.83
5. DocC chunk1: 0.75
6. DocB chunk2: 0.73
...
```

**Dopo adjustment** (penalty=0.3, max=2):
```
1. DocA chunk1: 0.85 (no penalty)           ← Selezionato #1
2. DocB chunk1: 0.81 (no penalty)           ← Selezionato #2
3. DocC chunk1: 0.75 (no penalty)           ← Selezionato #3
4. DocA chunk2: 0.588 (0.84 * 0.7)          ← Selezionato #4
5. DocB chunk2: 0.511 (0.73 * 0.7)          ← Selezionato #5
6. DocA chunk3: 0.332 (0.83 * 0.4)          ← Skip (DocA già 2)
```

**Output**: 5 risultati da 3 documenti diversi!

---

## 📊 Esempi Configurazioni

### Caso 1: Massima Relevance

**Scenario**: Hai un solo documento molto grande, vuoi i migliori risultati assoluti

```python
ENABLE_RESULT_DIVERSIFICATION = False
# Oppure:
MAX_CHUNKS_PER_DOCUMENT = 5
DIVERSIFICATION_PENALTY = 0.1
```

**Risultato**: Top-5 migliori chunks per score, anche dallo stesso documento

---

### Caso 2: Bilanciato (Default) ✅

**Scenario**: Hai 3-5 documenti, vuoi bilanciare relevance e diversity

```python
ENABLE_RESULT_DIVERSIFICATION = True
DIVERSIFICATION_PENALTY = 0.3
MAX_CHUNKS_PER_DOCUMENT = 2
```

**Risultato**: Max 2 chunks per documento, buon bilanciamento

---

### Caso 3: Massima Diversity

**Scenario**: Hai 10+ documenti, vuoi vedere tutti i documenti diversi

```python
ENABLE_RESULT_DIVERSIFICATION = True
DIVERSIFICATION_PENALTY = 0.5
MAX_CHUNKS_PER_DOCUMENT = 1
```

**Risultato**: 1 chunk per documento, massima varietà

---

### Caso 4: Pochi Documenti Rilevanti

**Scenario**: Hai 2 documenti molto rilevanti, altri meno

```python
ENABLE_RESULT_DIVERSIFICATION = True
DIVERSIFICATION_PENALTY = 0.2  # Penalty bassa
MAX_CHUNKS_PER_DOCUMENT = 3    # Permetti più chunks
```

**Risultato**: Privilegia documenti rilevanti ma con un po' di diversity

---

## 🧪 Testing Configurazioni

### Come Testare

1. **Carica documenti di test**:
   ```
   - Manuale1.pdf (grande, ~500 chunks)
   - Manuale2.pdf (medio, ~100 chunks)
   - Guida.pdf (piccola, ~30 chunks)
   ```

2. **Fai query di test**:
   ```
   "come configurare wifi"
   "reset dispositivo"
   "cambiare batteria"
   ```

3. **Controlla logs**:
   ```bash
   tail -f app.log | grep "Query completata"

   # Output:
   # Query completata: 5 risultati da 3 documenti diversi
   ```

4. **Verifica risultati nell'UI**:
   - Tab "Cerca nel Manuale"
   - Controlla quanti documenti diversi nei top-5

### Debug Mode

Aggiungi in `config.py`:
```python
DEBUG_RAG_ENGINE = True
LOG_LEVEL = "DEBUG"
```

Vedrai nei logs:
```
DEBUG - Diversificazione: da 15 risultati a 5, 3 documenti diversi
```

---

## 📈 Metriche di Valutazione

### Diversity Score

**Formula**: `unique_docs / top_k`

**Esempi**:
```python
# Top-5 risultati
5 documenti diversi → diversity = 5/5 = 100%  # Massimo
3 documenti diversi → diversity = 3/5 = 60%   # Buono
1 documento         → diversity = 1/5 = 20%   # Cattivo
```

### Relevance Score

**Formula**: Media degli score

**Esempi**:
```python
# Senza diversificazione
scores = [0.85, 0.84, 0.83, 0.82, 0.81]
avg = 0.83  # Alto ma tutti stesso documento

# Con diversificazione
scores = [0.85, 0.81, 0.84, 0.75, 0.73]
avg = 0.796  # Leggermente più basso ma più diverso
```

### Trade-off

```
Diversification ON:
  + Maggiore diversity (60-80%)
  - Relevance leggermente più bassa (-5%)

Diversification OFF:
  + Massima relevance (100%)
  - Bassa diversity (20-40%)
```

---

## 🎯 Raccomandazioni Finali

### Per la Maggior Parte degli Utenti

```python
# Configurazione ottimale
ENABLE_RESULT_DIVERSIFICATION = True
DIVERSIFICATION_PENALTY = 0.3
MAX_CHUNKS_PER_DOCUMENT = 2
TOP_K_RETRIEVAL = 5
```

**Motivo**: Bilanciamento ideale tra qualità e varietà

### Se Non Funziona Bene

**Problema**: Troppi risultati da stesso documento

**Soluzione**:
```python
DIVERSIFICATION_PENALTY = 0.4  # Aumenta penalty
MAX_CHUNKS_PER_DOCUMENT = 1    # Riduci max chunks
```

**Problema**: Risultati poco rilevanti

**Soluzione**:
```python
DIVERSIFICATION_PENALTY = 0.2  # Riduci penalty
MAX_CHUNKS_PER_DOCUMENT = 3    # Aumenta max chunks
TOP_K_RETRIEVAL = 7            # Recupera più risultati
```

---

## 📚 Risorse

- **Algoritmo**: Ispirato a MMR (Maximal Marginal Relevance)
- **Paper**: [The Use of MMR, Diversity-Based Reranking](https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf)
- **Codice**: `rag_engine.py` → `_diversify_results()`

---

**Happy diversification!** 🎯📚
