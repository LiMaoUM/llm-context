"""
Split model results from model_responses.jsonl into separate files by model.
"""

import json
from pathlib import Path
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def split_results_by_model(jsonl_file: str, output_dir: str = "results"):
    """
    Split model_responses.jsonl into separate files by model.
    
    Args:
        jsonl_file: Path to model_responses.jsonl
        output_dir: Directory to save split results
    """
    jsonl_path = Path(jsonl_file)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not jsonl_path.exists():
        logger.error(f"JSONL file not found: {jsonl_file}")
        return
    
    # Group results by model
    model_results = defaultdict(list)
    model_stats = defaultdict(lambda: {"total": 0, "success": 0, "failed": 0})
    
    try:
        with open(jsonl_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    record = json.loads(line)
                    model_name = record.get('model', 'unknown')
                    model_results[model_name].append(record)
                    
                    # Update stats
                    model_stats[model_name]["total"] += 1
                    if record.get('success'):
                        model_stats[model_name]["success"] += 1
                    else:
                        model_stats[model_name]["failed"] += 1
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line {line_num}: {e}")
    except Exception as e:
        logger.error(f"Error reading JSONL file: {e}")
        return
    
    logger.info(f"Read {line_num} records from {jsonl_file}")
    logger.info(f"Found {len(model_results)} unique models")
    
    # Save separate files for each model
    for model_name, records in model_results.items():
        output_file = output_path / f"{model_name}_responses.jsonl"
        
        try:
            with open(output_file, 'w') as f:
                for record in records:
                    f.write(json.dumps(record, default=str) + '\n')
            
            stats = model_stats[model_name]
            logger.info(f"✓ {model_name}: {len(records)} records "
                       f"(success={stats['success']}, failed={stats['failed']}) "
                       f"→ {output_file}")
        except Exception as e:
            logger.error(f"Failed to write {output_file}: {e}")
    
    # Also create a summary file
    summary_file = output_path / "models_summary.json"
    summary = {}
    for model_name, records in model_results.items():
        stats = model_stats[model_name]
        summary[model_name] = {
            "total_records": len(records),
            "successful": stats['success'],
            "failed": stats['failed'],
            "success_rate": stats['success'] / stats['total'] if stats['total'] > 0 else 0,
            "output_file": f"{model_name}_responses.jsonl"
        }
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"\nSummary saved to: {summary_file}")
    logger.info("\n=== Model Summary ===")
    for model_name in sorted(summary.keys()):
        s = summary[model_name]
        logger.info(f"{model_name}:")
        logger.info(f"  Total: {s['total_records']}")
        logger.info(f"  Success: {s['successful']}/{s['total_records']} ({s['success_rate']*100:.1f}%)")


def analyze_model_results(model_name: str, jsonl_file: str):
    """
    Analyze results for a specific model.
    
    Args:
        model_name: Name of the model to analyze
        jsonl_file: Path to model_responses.jsonl
    """
    results_by_variant = defaultdict(lambda: {"total": 0, "success": 0, "avg_confidence": 0})
    confidences = defaultdict(list)
    
    try:
        with open(jsonl_file, 'r') as f:
            for line in f:
                record = json.loads(line)
                if record.get('model') != model_name:
                    continue
                
                variant = record.get('variant', 'unknown')
                success = record.get('success', False)
                
                results_by_variant[variant]["total"] += 1
                if success:
                    results_by_variant[variant]["success"] += 1
                
                if record.get('confidence') is not None:
                    confidences[variant].append(record.get('confidence'))
    except Exception as e:
        logger.error(f"Error analyzing results: {e}")
        return
    
    logger.info(f"\n=== Analysis for {model_name} ===")
    for variant in sorted(results_by_variant.keys()):
        stats = results_by_variant[variant]
        variant_confidences = confidences[variant]
        avg_conf = sum(variant_confidences) / len(variant_confidences) if variant_confidences else 0
        
        logger.info(f"\n{variant}:")
        logger.info(f"  Total: {stats['total']}")
        logger.info(f"  Success: {stats['success']}/{stats['total']} ({stats['success']*100/stats['total']:.1f}%)")
        logger.info(f"  Avg Confidence: {avg_conf:.1f}%")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        jsonl_file = sys.argv[1]
    else:
        jsonl_file = "results/model_responses.jsonl"
    
    # Split results by model
    split_results_by_model(jsonl_file)
    
    # Optionally analyze specific model
    if len(sys.argv) > 2:
        model_name = sys.argv[2]
        analyze_model_results(model_name, jsonl_file)
