# Slop Forensics Shortcuts

This document describes the simplified shortcuts module that allows you to perform comprehensive slop analysis with just a single function call.

## Overview

Instead of running 4 separate scripts (`create_slop_lists.py`, `generate_dataset.py`, `generate_phylo_trees.py`, `slop_profile.py`), you can now use the shortcuts module to perform all analyses at once.

## Key Functions

### `analyze_sentences(sentences, output_dir, model_name="custom_input", generate_phylogeny=True)`

Performs comprehensive slop analysis on a list of sentences and outputs everything to a specified directory.

**What it does:**
1. **Text Analysis**: Calculates metrics like slop score, vocabulary complexity, repetitive words, n-grams
2. **Slop List Generation**: Creates word/bigram/trigram slop lists 
3. **Phylogenetic Trees**: Generates evolutionary relationship visualizations (optional)
4. **Summary Reports**: Creates human-readable analysis summaries

**Parameters:**
- `sentences`: List of text strings to analyze
- `output_dir`: Directory where all results will be saved
- `model_name`: Name for this analysis (default: "custom_input")
- `generate_phylogeny`: Whether to create phylogenetic trees (default: True)

**Returns:**
Dictionary containing file paths and summary statistics.

### `analyze_multiple_models(model_sentences, output_dir, generate_phylogeny=True)`

Analyzes multiple sets of sentences from different models/sources and creates comparative analyses.

**Parameters:**
- `model_sentences`: Dict mapping model names to lists of sentences
- `output_dir`: Directory where all results will be saved  
- `generate_phylogeny`: Whether to create comparative phylogenetic trees

## Quick Start

### Simple Analysis

```python
from slop_forensics.shortcuts import analyze_sentences

# Your sentences to analyze
sentences = [
    "The sun was setting over the horizon, casting a warm glow.",
    "It's important to note that this requires careful consideration.",
    # ... more sentences
]

# Run comprehensive analysis
results = analyze_sentences(
    sentences=sentences,
    output_dir="./my_analysis",
    model_name="my_text"
)

print(f"Slop score: {results['statistics']['slop_score']}")
print(f"Files generated: {results['output_paths']}")
```

### Multi-Model Comparison

```python
from slop_forensics.shortcuts import analyze_multiple_models

# Data from different sources
model_data = {
    "chatgpt": ["I'd be happy to help...", "It's important to note..."],
    "claude": ["I can assist you with...", "Let me explain this..."],
    "human": ["Here's my take...", "What I think is..."]
}

# Compare all models
results = analyze_multiple_models(
    model_sentences=model_data,
    output_dir="./comparison_analysis"
)
```

## Output Structure

When you run `analyze_sentences()`, it creates the following directory structure:

```
output_dir/
├── analysis_summary.json          # Human-readable summary
├── slop_profile_results.json      # Combined metrics
├── datasets/                      # Generated dataset files
│   └── generated_model_name.jsonl
├── analysis/                      # Detailed analysis results  
│   └── slop_profile__model_name.json
├── slop_lists/                    # Generated slop lists
│   ├── slop_list_words.json
│   ├── slop_list_bigrams.json
│   ├── slop_list_trigrams.json
│   └── slop_phrases.jsonl
└── phylogeny/                     # Phylogenetic trees (if generated)
    ├── charts/
    └── *.tree files
```

## Key Metrics Explained

- **Slop Score**: Higher values indicate more AI-like repetitive patterns
- **Repetition Score**: Measures word repetition frequency  
- **Vocabulary Complexity**: Lexical diversity and sophistication
- **Top Repetitive Words**: Words that appear unusually often
- **N-grams**: Common 2-word and 3-word phrases

## Example Usage

See `example_usage.py` for complete working examples:

```bash
cd slop-forensics-a
python example_usage.py
```

This will create sample analyses in `./analysis_results/` showing both single-model and multi-model analysis.

## Quick Analysis Function

For simple use cases, there's also a `quick_analyze()` function in the example:

```python
from example_usage import quick_analyze

sentences = ["Your text here...", "More text..."]
quick_analyze(sentences)  # Prints summary to console
```

## Requirements

Make sure you have installed the requirements:

```bash
pip install -r requirements.txt
```

You'll also need to download NLTK data:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

## Notes

- For phylogenetic analysis, you need multiple models/sources to compare
- Large datasets may take some time to process
- Results are saved in JSON format for easy programmatic access
- The analysis uses the same algorithms as the original 4-script workflow
- Temporary files are automatically cleaned up unless `cleanup_temp=False`

## Advanced Usage

You can also import individual functions from the original modules if needed:

```python
from slop_forensics.analysis import analyze_texts
from slop_forensics.slop_lists import create_slop_lists  
from slop_forensics.phylogeny import generate_phylogenetic_trees
```

But the shortcuts module provides the most convenient interface for most use cases. 