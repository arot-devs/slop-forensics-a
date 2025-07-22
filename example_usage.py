#!/usr/bin/env python3
"""
Example usage of the slop-forensics shortcuts module.
This demonstrates how to use the unified analyze_sentences function.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from slop_forensics.shortcuts import analyze_sentences, analyze_multiple_models

def main():
    # Example 1: Analyze a single set of sentences
    print("=== Example 1: Single Model Analysis ===")
    
    # Sample sentences that might contain "slop" (repetitive AI-generated text patterns)
    sample_sentences = [
        "The sun was setting over the horizon, casting a warm glow across the landscape.",
        "In conclusion, it's important to note that this matter requires careful consideration.",
        "The atmosphere was filled with palpable tension as the characters navigated their journey.",
        "It's worth mentioning that the situation demanded immediate attention and careful analysis.",
        "The protagonist found themselves in a precarious situation that would test their resolve.",
        "Furthermore, the implications of this decision would reverberate throughout the narrative.",
        "The complex web of relationships added layers of depth to the unfolding drama.",
        "As the story progressed, it became increasingly clear that the stakes were higher than anticipated.",
        "The intricate plot threads began to weave together in unexpected ways.",
        "Ultimately, the resolution provided a satisfying conclusion to the elaborate tale."
    ]
    
    # Analyze the sentences
    results = analyze_sentences(
        sentences=sample_sentences,
        output_dir="./analysis_results/example_1",
        model_name="sample_text",
        generate_phylogeny=False  # Skip phylogeny for single model
    )
    
    print(f"Analysis complete! Results saved to: ./analysis_results/example_1")
    print(f"Summary statistics:")
    print(f"  - Average length: {results['statistics'].get('avg_length', 0)}")
    print(f"  - Slop score: {results['statistics'].get('slop_score', 0)}")
    print(f"  - Repetitive words found: {results['statistics'].get('num_repetitive_words', 0)}")
    print(f"  - Output files: {len(results['output_paths'])} files generated")
    print()
    
    # Example 2: Analyze multiple models/sources
    print("=== Example 2: Multi-Model Analysis ===")
    
    # Sample data from different "models" or sources
    model_data = {
        "chatgpt_style": [
            "I'd be happy to help you with that! Here's what you need to know about this topic.",
            "It's important to note that there are several key considerations to keep in mind.",
            "In summary, the best approach would be to carefully evaluate your options.",
            "I hope this information helps! Let me know if you have any other questions.",
        ],
        "academic_style": [
            "This research demonstrates significant implications for future studies in the field.",
            "The methodology employed in this investigation follows established protocols.",
            "Furthermore, the results indicate a strong correlation between the variables.",
            "In conclusion, these findings contribute to our understanding of the phenomenon.",
        ],
        "creative_writing": [
            "The moonlight danced across the rippling water, creating patterns of silver and shadow.",
            "Her heart pounded with anticipation as she approached the mysterious door.",
            "The ancient forest whispered secrets that only the wind could understand.",
            "Time seemed to stand still in that magical moment of discovery.",
        ]
    }
    
    # Analyze multiple models
    multi_results = analyze_multiple_models(
        model_sentences=model_data,
        output_dir="./analysis_results/example_2",
        generate_phylogeny=True  # Generate phylogeny for multiple models
    )
    
    print(f"Multi-model analysis complete!")
    print(f"Models analyzed: {multi_results['models_analyzed']}")
    print(f"Total sentences: {multi_results['total_sentences']}")
    print(f"Results saved to: ./analysis_results/example_2")
    print()
    
    print("=== Analysis Complete ===")
    print("Check the output directories for detailed results:")
    print("  - analysis_summary.json: Human-readable summary")
    print("  - slop_lists/: Generated slop word lists")
    print("  - phylogeny/: Phylogenetic tree visualizations (if generated)")
    print("  - analysis/: Detailed analysis metrics")


def quick_analyze(sentences, output_dir="./quick_analysis"):
    """Quick analysis function for simple use cases."""
    results = analyze_sentences(
        sentences=sentences,
        output_dir=output_dir,
        model_name="quick_analysis",
        generate_phylogeny=False
    )
    
    # Print quick summary
    print("Quick Analysis Results:")
    print(f"  Sentences analyzed: {len(sentences)}")
    print(f"  Average length: {results['statistics'].get('avg_length', 0):.1f} characters")
    print(f"  Slop score: {results['statistics'].get('slop_score', 0):.3f}")
    print(f"  Repetitive words: {results['statistics'].get('num_repetitive_words', 0)}")
    
    # Show top repetitive words if any
    analysis_file = results["output_paths"].get("analysis")
    if analysis_file and os.path.exists(analysis_file):
        import json
        with open(analysis_file, 'r') as f:
            analysis_data = json.load(f)
        
        top_words = analysis_data.get("top_repetitive_words", [])[:5]
        if top_words:
            print("  Top repetitive words:")
            for word_data in top_words:
                word = word_data.get("word", "")
                score = word_data.get("score", 0)
                print(f"    - '{word}' (score: {score:.2f})")
    
    return results


if __name__ == "__main__":
    main() 