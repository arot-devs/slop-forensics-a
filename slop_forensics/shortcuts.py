import os
import json
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict
import tempfile
import shutil

from . import config
from .analysis import analyze_texts
from .slop_lists import create_slop_lists
from .phylogeny import generate_phylogenetic_trees
from .utils import setup_logging, save_json_file, save_jsonl_file, sanitize_filename

logger = logging.getLogger(__name__)


def analyze_sentences(
    sentences: List[str],
    output_dir: str,
    model_name: str = "custom_input",
    generate_phylogeny: bool = True,
    cleanup_temp: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive slop analysis for a list of sentences.
    
    This function performs all the analyses that the original 4 scripts do:
    1. Text analysis (repetitive words, n-grams, metrics)
    2. Slop list generation
    3. Phylogenetic tree generation (optional)
    
    Args:
        sentences: List of text sentences to analyze
        output_dir: Directory to save all analysis results
        model_name: Name to use for this analysis (default: "custom_input")
        generate_phylogeny: Whether to generate phylogenetic trees (default: True)
        cleanup_temp: Whether to clean up temporary files (default: True)
        
    Returns:
        Dictionary containing paths to all generated files and summary statistics
    """
    setup_logging()
    logger.info(f"Starting comprehensive slop analysis for {len(sentences)} sentences")
    
    if not sentences:
        raise ValueError("sentences list cannot be empty")
    
    # Create output directories
    os.makedirs(output_dir, exist_ok=True)
    dataset_dir = os.path.join(output_dir, "datasets")
    analysis_dir = os.path.join(output_dir, "analysis") 
    slop_lists_dir = os.path.join(output_dir, "slop_lists")
    phylogeny_dir = os.path.join(output_dir, "phylogeny")
    
    for dir_path in [dataset_dir, analysis_dir, slop_lists_dir, phylogeny_dir]:
        os.makedirs(dir_path, exist_ok=True)
    
    results = {
        "model_name": model_name,
        "num_sentences": len(sentences),
        "output_paths": {},
        "statistics": {}
    }
    
    # Step 1: Create dataset file (mimicking the original dataset format)
    logger.info("Creating dataset file...")
    dataset_items = []
    for i, sentence in enumerate(sentences):
        dataset_items.append({
            "model": model_name,
            "source": "custom_input", 
            "id": f"sentence_{i:04d}",
            "output": sentence,
            "prompt": f"Custom input sentence {i+1}"
        })
    
    dataset_filename = os.path.join(dataset_dir, f"generated_{sanitize_filename(model_name)}.jsonl")
    save_jsonl_file(dataset_items, dataset_filename)
    results["output_paths"]["dataset"] = dataset_filename
    logger.info(f"Saved dataset to: {dataset_filename}")
    
    # Step 2: Perform comprehensive text analysis
    logger.info("Performing text analysis...")
    
    # Prepare data for analysis
    texts_with_ids = [(item["output"], f"{item['source']}_{item['id']}") for item in dataset_items]
    prompts_data = defaultdict(list)
    for item in dataset_items:
        prompt_id = f"{item['source']}_{item['id']}"
        prompts_data[prompt_id].append(item["output"])
    
    # Run analysis
    analysis_results = analyze_texts(model_name, texts_with_ids, dict(prompts_data))
    
    # Save analysis results
    analysis_filename = os.path.join(analysis_dir, f"slop_profile__{sanitize_filename(model_name)}.json")
    save_json_file(analysis_results, analysis_filename)
    results["output_paths"]["analysis"] = analysis_filename
    
    # Also save as combined metrics file for phylogeny
    combined_metrics_file = os.path.join(output_dir, "slop_profile_results.json")
    combined_metrics = {model_name: analysis_results}
    save_json_file(combined_metrics, combined_metrics_file)
    results["output_paths"]["combined_metrics"] = combined_metrics_file
    
    logger.info(f"Saved analysis results to: {analysis_filename}")
    
    # Extract key statistics
    stats = results["statistics"]
    stats["avg_length"] = analysis_results.get("avg_length", 0)
    stats["vocab_complexity"] = analysis_results.get("vocab_complexity", 0)
    stats["slop_score"] = analysis_results.get("slop_score", 0)
    stats["repetition_score"] = analysis_results.get("repetition_score", 0)
    stats["num_repetitive_words"] = len(analysis_results.get("top_repetitive_words", []))
    stats["num_top_bigrams"] = len(analysis_results.get("top_bigrams", []))
    stats["num_top_trigrams"] = len(analysis_results.get("top_trigrams", []))
    
    # Step 3: Generate slop lists
    logger.info("Generating slop lists...")
    
    # Update config to use our temporary directories
    original_analysis_dir = config.ANALYSIS_OUTPUT_DIR
    original_dataset_dir = config.DATASET_OUTPUT_DIR
    
    config.ANALYSIS_OUTPUT_DIR = analysis_dir
    config.DATASET_OUTPUT_DIR = dataset_dir
    
    try:
        create_slop_lists(
            analysis_files_dir=analysis_dir,
            output_dir=slop_lists_dir,
            max_items_per_model=len(sentences)
        )
        
        # Record slop list files
        slop_files = []
        for filename in os.listdir(slop_lists_dir):
            if filename.startswith("slop_list"):
                slop_files.append(os.path.join(slop_lists_dir, filename))
        
        results["output_paths"]["slop_lists"] = slop_files
        logger.info(f"Generated {len(slop_files)} slop list files")
        
    except Exception as e:
        logger.error(f"Error generating slop lists: {e}", exc_info=True)
        results["output_paths"]["slop_lists"] = []
    finally:
        # Restore original config
        config.ANALYSIS_OUTPUT_DIR = original_analysis_dir
        config.DATASET_OUTPUT_DIR = original_dataset_dir
    
    # Step 4: Generate phylogenetic trees (optional)
    if generate_phylogeny:
        logger.info("Generating phylogenetic trees...")
        
        try:
            generate_phylogenetic_trees(
                metrics_file=combined_metrics_file,
                output_dir=phylogeny_dir,
                charts_dir=os.path.join(phylogeny_dir, "charts"),
                top_n_features=config.PHYLO_TOP_N_FEATURES,
                models_to_ignore=[]  # Don't ignore our single model
            )
            
            # Record phylogeny files
            phylo_files = []
            for root, dirs, files in os.walk(phylogeny_dir):
                for file in files:
                    phylo_files.append(os.path.join(root, file))
            
            results["output_paths"]["phylogeny"] = phylo_files
            logger.info(f"Generated {len(phylo_files)} phylogeny files")
            
        except Exception as e:
            logger.error(f"Error generating phylogenetic trees: {e}", exc_info=True)
            results["output_paths"]["phylogeny"] = []
    else:
        logger.info("Skipping phylogenetic tree generation")
        results["output_paths"]["phylogeny"] = []
    
    # Step 5: Generate summary report
    logger.info("Generating summary report...")
    summary_report = generate_summary_report(results, analysis_results)
    summary_filename = os.path.join(output_dir, "analysis_summary.json")
    save_json_file(summary_report, summary_filename)
    results["output_paths"]["summary"] = summary_filename
    
    logger.info(f"Analysis complete! Results saved to: {output_dir}")
    logger.info(f"Summary report: {summary_filename}")
    
    return results


def generate_summary_report(results: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a human-readable summary report of the analysis."""
    
    summary = {
        "overview": {
            "model_name": results["model_name"],
            "sentences_analyzed": results["num_sentences"],
            "analysis_timestamp": analysis_results.get("analysis_timestamp"),
        },
        "key_metrics": {
            "average_sentence_length": results["statistics"].get("avg_length", 0),
            "vocabulary_complexity": results["statistics"].get("vocab_complexity", 0),
            "slop_score": results["statistics"].get("slop_score", 0),
            "repetition_score": results["statistics"].get("repetition_score", 0),
        },
        "patterns_found": {
            "repetitive_words_count": results["statistics"].get("num_repetitive_words", 0),
            "top_bigrams_count": results["statistics"].get("num_top_bigrams", 0), 
            "top_trigrams_count": results["statistics"].get("num_top_trigrams", 0),
        },
        "top_repetitive_words": [
            w["word"] for w in analysis_results.get("top_repetitive_words", [])[:20]
        ],
        "top_bigrams": [
            b["ngram"] for b in analysis_results.get("top_bigrams", [])[:20]
        ],
        "top_trigrams": [
            t["ngram"] for t in analysis_results.get("top_trigrams", [])[:20]
        ],
        "output_files": results["output_paths"]
    }
    
    return summary


def analyze_multiple_models(
    model_sentences: Dict[str, List[str]],
    output_dir: str,
    generate_phylogeny: bool = True
) -> Dict[str, Any]:
    """
    Analyze multiple sets of sentences from different models/sources.
    
    Args:
        model_sentences: Dict mapping model names to lists of sentences
        output_dir: Directory to save all analysis results
        generate_phylogeny: Whether to generate phylogenetic trees
        
    Returns:
        Dictionary containing analysis results for all models
    """
    setup_logging()
    logger.info(f"Starting multi-model analysis for {len(model_sentences)} models")
    
    os.makedirs(output_dir, exist_ok=True)
    
    all_results = {}
    combined_metrics = {}
    
    # Analyze each model individually
    for model_name, sentences in model_sentences.items():
        logger.info(f"Analyzing model: {model_name}")
        
        model_output_dir = os.path.join(output_dir, sanitize_filename(model_name))
        
        try:
            model_results = analyze_sentences(
                sentences=sentences,
                output_dir=model_output_dir,
                model_name=model_name,
                generate_phylogeny=False,  # We'll generate combined phylogeny later
                cleanup_temp=False
            )
            
            all_results[model_name] = model_results
            
            # Load the analysis results for combined metrics
            analysis_file = model_results["output_paths"].get("analysis")
            if analysis_file and os.path.exists(analysis_file):
                with open(analysis_file, 'r') as f:
                    combined_metrics[model_name] = json.load(f)
                    
        except Exception as e:
            logger.error(f"Error analyzing model {model_name}: {e}", exc_info=True)
            continue
    
    # Save combined metrics
    combined_metrics_file = os.path.join(output_dir, "combined_metrics.json")
    save_json_file(combined_metrics, combined_metrics_file)
    
    # Generate combined slop lists
    logger.info("Generating combined slop lists...")
    combined_analysis_dir = os.path.join(output_dir, "combined_analysis")
    combined_slop_dir = os.path.join(output_dir, "combined_slop_lists")
    os.makedirs(combined_analysis_dir, exist_ok=True)
    
    # Copy individual analysis files to combined directory
    for model_name, results in all_results.items():
        analysis_file = results["output_paths"].get("analysis")
        if analysis_file and os.path.exists(analysis_file):
            dest_file = os.path.join(combined_analysis_dir, os.path.basename(analysis_file))
            shutil.copy2(analysis_file, dest_file)
    
    # Generate combined dataset directory
    combined_dataset_dir = os.path.join(output_dir, "combined_datasets")
    os.makedirs(combined_dataset_dir, exist_ok=True)
    
    for model_name, results in all_results.items():
        dataset_file = results["output_paths"].get("dataset")
        if dataset_file and os.path.exists(dataset_file):
            dest_file = os.path.join(combined_dataset_dir, os.path.basename(dataset_file))
            shutil.copy2(dataset_file, dest_file)
    
    # Update config temporarily
    original_analysis_dir = config.ANALYSIS_OUTPUT_DIR
    original_dataset_dir = config.DATASET_OUTPUT_DIR
    
    config.ANALYSIS_OUTPUT_DIR = combined_analysis_dir
    config.DATASET_OUTPUT_DIR = combined_dataset_dir
    
    try:
        create_slop_lists(
            analysis_files_dir=combined_analysis_dir,
            output_dir=combined_slop_dir
        )
    except Exception as e:
        logger.error(f"Error generating combined slop lists: {e}", exc_info=True)
    finally:
        config.ANALYSIS_OUTPUT_DIR = original_analysis_dir
        config.DATASET_OUTPUT_DIR = original_dataset_dir
    
    # Generate phylogenetic trees if requested
    if generate_phylogeny and len(combined_metrics) > 1:
        logger.info("Generating phylogenetic trees for multiple models...")
        phylogeny_dir = os.path.join(output_dir, "phylogeny")
        
        try:
            generate_phylogenetic_trees(
                metrics_file=combined_metrics_file,
                output_dir=phylogeny_dir,
                charts_dir=os.path.join(phylogeny_dir, "charts")
            )
        except Exception as e:
            logger.error(f"Error generating phylogenetic trees: {e}", exc_info=True)
    
    # Generate combined summary
    combined_summary = {
        "models_analyzed": list(model_sentences.keys()),
        "total_sentences": sum(len(sentences) for sentences in model_sentences.values()),
        "individual_results": all_results,
        "combined_files": {
            "metrics": combined_metrics_file,
            "slop_lists": combined_slop_dir,
            "phylogeny": os.path.join(output_dir, "phylogeny") if generate_phylogeny else None
        }
    }
    
    summary_file = os.path.join(output_dir, "multi_model_summary.json")
    save_json_file(combined_summary, summary_file)
    
    logger.info(f"Multi-model analysis complete! Results saved to: {output_dir}")
    
    return combined_summary 