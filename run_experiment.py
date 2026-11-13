#!/usr/bin/env python3
"""
Main experiment runner for LLM context & confidence analysis.

This script orchestrates the entire pipeline:
1. Data loading and exploration
2. Context variant generation
3. LLM inference across multiple models
4. Metrics computation and analysis
5. Visualization generation
"""

import argparse
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np
import multiprocessing
from datetime import datetime
import shutil

# CRITICAL: Set multiprocessing start method BEFORE importing any CUDA-dependent libraries
# This is required for vLLM with tensor parallelism
if __name__ == '__main__':
    multiprocessing.set_start_method('spawn', force=True)

from data_loader import DataLoader, ContextVariantGenerator
from llm_inference import InferencePipeline, BatchEvaluator
from evaluation_metrics import ComprehensiveMetrics
from analysis_visualization import ResultsAnalyzer, ResultsVisualizer


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExperimentRunner:
    """Run the complete experiment."""
    
    def __init__(self, config_path: str = "experiment_config.yaml", num_samples: int = None, confidence_only: bool = False, timestamp: str = None):
        """Initialize experiment runner with config."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.num_samples = num_samples
        self.confidence_only = confidence_only
        self.timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        base_results_dir = self.config['execution']['output_dir']
        self.results_dir = Path(base_results_dir) / self.timestamp
        self.results_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Experiment configuration loaded from {config_path}")
        logger.info(f"Output directory: {self.results_dir}")
        if self.num_samples:
            logger.info(f"Number of samples: {self.num_samples}")
        else:
            logger.info(f"Number of samples: ALL")
        if self.confidence_only:
            logger.info(f"Mode: Confidence only (skip full predictions)")
    
    def step_1_explore_data(self):
        """Step 1: Load and explore the data."""
        logger.info("=" * 80)
        logger.info("STEP 1: DATA EXPLORATION")
        logger.info("=" * 80)
        
        loader = DataLoader("./data")
        summary = loader.get_data_summary()
        
        # Save summary
        summary_file = self.results_dir / "data_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Data summary saved to {summary_file}")
        
        # Print overview
        for dataset_name, dataset_info in summary.items():
            logger.info(f"\n{dataset_name}:")
            logger.info(f"  Total count: {dataset_info.get('total_count', 'N/A')}")
            if 'columns' in dataset_info:
                logger.info(f"  Columns: {', '.join(dataset_info['columns'][:5])}...")
        
        return loader, summary
    
    def step_2_generate_context_variants(self, loader: DataLoader, num_samples: int = None):
        """Step 2: Generate context variants for sample posts."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: CONTEXT VARIANT GENERATION")
        logger.info("=" * 80)
        
        generator = ContextVariantGenerator(loader)
        
        # Load sample posts
        loader.load_all()
        
        # Use provided num_samples or default to all
        if num_samples is None:
            num_samples = len(loader.posts)
        
        posts = loader.posts.head(num_samples)
        logger.info(f"Processing {len(posts)} samples")
        
        samples_with_variants = []
        
        for idx, (_, post) in enumerate(posts.iterrows()):
            if idx % 20 == 0:
                logger.info(f"Processing sample {idx}/{len(posts)}")
            
            # Get post ID from Series (use post_id or id)
            post_id = post.get('post_id') if 'post_id' in post.index else post.get('id')
            if post_id is None:
                logger.warning(f"Sample {idx} has no ID column, skipping")
                continue
            
            # Get full context
            sample = loader.get_post_with_all_context(post_id)
            
            if sample is None:
                continue
            
            # Generate variants
            variants = generator.generate_variants(sample)
            
            samples_with_variants.append({
                'sample_id': post_id,
                'post_text': sample['post_text'],
                'context_variants': variants,
                'ground_truth': None,  # TODO: Add ground truth labels
            })
        
        logger.info(f"Generated variants for {len(samples_with_variants)} samples")
        
        # Save sample structure
        sample_file = self.results_dir / "sample_variants.json"
        with open(sample_file, 'w') as f:
            json.dump(
                [samples_with_variants[0]] if samples_with_variants else [],  # Save just first for reference
                f, indent=2, default=str
            )
        logger.info(f"Sample variant structure saved to {sample_file}")
        
        return samples_with_variants
    
    def step_3_llm_inference(self, samples: List[Dict]) -> Dict:
        """Step 3: Run LLM inference across all models and variants."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: LLM INFERENCE")
        logger.info("=" * 80)
        
        # Load config models
        config_models = self.config.get('models', [])
        logger.info(f"Total models to evaluate: {len(config_models)}")
        
        # Prepare task config
        task = self.config['tasks'][0]  # First task
        target_entity = task.get('target_entities', task.get('figures', ['Biden', 'Trump']))[0]
        stance_options = task['stance_options']
        figures = task.get('figures', ['Biden', 'Trump'])
        
        logger.info(f"Task: {task['task_name']}")
        logger.info(f"Figures: {', '.join(figures)}")
        logger.info(f"Stance options: {', '.join(stance_options)}")
        
        if self.confidence_only:
            logger.info("Mode: Recording CONFIDENCE ONLY")
        
        # Setup combined response logging
        combined_responses_jsonl = str(self.results_dir / "model_responses.jsonl")
        logger.info(f"Combined model responses will be saved to: {combined_responses_jsonl}")
        
        # Initialize results structure
        all_results = []
        for i, sample in enumerate(samples):
            all_results.append({
                'sample_id': sample.get('sample_id'),
                'target_entity': target_entity,
                'ground_truth': sample.get('ground_truth'),
                'variants': {},
            })
        
        # Run inference for each model independently
        for model_idx, model_config in enumerate(config_models, 1):
            model_name = model_config['name']
            logger.info(f"\n{'='*80}")
            logger.info(f"[{model_idx}/{len(config_models)}] Processing Model: {model_name}")
            logger.info(f"{'='*80}")
            
            pipeline = None  # Initialize before try block
            
            try:
                # Initialize pipeline with only this model
                single_model_config = {**self.config, 'models': [model_config]}
                pipeline = InferencePipeline(single_model_config)
                
                logger.info(f"Loaded model: {model_name}")
                
                # Create separate JSONL file for this model
                model_responses_jsonl = str(self.results_dir / f"{model_name}_responses.jsonl")
                logger.info(f"Model responses will be saved to: {model_responses_jsonl}")
                
                # Run inference for this model
                evaluator = BatchEvaluator(pipeline, responses_jsonl=model_responses_jsonl)
                model_results = evaluator.evaluate_batch(
                    samples=samples,
                    target_entity=target_entity,
                    stance_options=stance_options,
                    save_interval=10,
                    output_file=None,  # Don't save intermediate files per model
                    confidence_only=self.confidence_only
                )
                
                # Also append to combined responses file
                with open(model_responses_jsonl, 'r') as f_model:
                    with open(combined_responses_jsonl, 'a') as f_combined:
                        for line in f_model:
                            f_combined.write(line)
                
                # Merge results into all_results
                for i, model_result in enumerate(model_results):
                    for variant_name, variant_result in model_result.get('variants', {}).items():
                        if variant_name not in all_results[i]['variants']:
                            all_results[i]['variants'][variant_name] = {}
                        all_results[i]['variants'][variant_name][model_name] = variant_result
                
                # Save model-specific inference results
                model_inference_file = str(self.results_dir / f"{model_name}_inference_results.json")
                with open(model_inference_file, 'w') as f:
                    json.dump(model_results, f, indent=2, default=str)
                logger.info(f"✓ Completed {model_name}")
                logger.info(f"  - Responses: {model_responses_jsonl}")
                logger.info(f"  - Results: {model_inference_file}")
                
            except Exception as e:
                logger.error(f"✗ Failed to process {model_name}: {e}", exc_info=True)
                # Continue with next model instead of crashing
                continue
            
            finally:
                # Explicitly cleanup the model to free GPU memory
                logger.info(f"Cleaning up {model_name}...")
                self._cleanup_model(pipeline)
                
                # Force garbage collection
                import gc
                gc.collect()
                
                # Empty CUDA cache if using GPU
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        logger.info(f"Cleared CUDA cache after {model_name}")
                except Exception as e:
                    logger.debug(f"Could not clear CUDA cache: {e}")
        
        # Final save - combined results
        output_file = str(self.results_dir / "inference_results.json")
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        # Create summary file listing all outputs
        summary_file = str(self.results_dir / "results_manifest.json")
        manifest = {
            'total_samples': len(all_results),
            'total_models': len(config_models),
            'combined_results': output_file,
            'combined_responses': combined_responses_jsonl,
            'model_files': {}
        }
        for model_config in config_models:
            model_name = model_config['name']
            manifest['model_files'][model_name] = {
                'responses': f"{model_name}_responses.jsonl",
                'inference_results': f"{model_name}_inference_results.json"
            }
        
        with open(summary_file, 'w') as f:
            json.dump(manifest, f, indent=2, default=str)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✓ INFERENCE COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Completed inference for {len(all_results)} samples across all models")
        logger.info(f"\n📁 Output Files:")
        logger.info(f"  Combined results: {output_file}")
        logger.info(f"  Combined responses: {combined_responses_jsonl}")
        logger.info(f"  Results manifest: {summary_file}")
        logger.info(f"\n  Per-model files:")
        for model_config in config_models:
            model_name = model_config['name']
            logger.info(f"    - {model_name}_responses.jsonl")
            logger.info(f"    - {model_name}_inference_results.json")
        
        return all_results
    
    def _cleanup_model(self, pipeline):
        """Explicitly cleanup model to free GPU memory."""
        if pipeline is None:
            return
        
        try:
            # Delete all models in the pipeline
            for model_name, model in pipeline.models.items():
                try:
                    # For vLLM models, explicitly shutdown
                    if hasattr(model, 'llm'):
                        logger.debug(f"Shutting down vLLM engine for {model_name}")
                        if hasattr(model.llm, '_run_engine'):
                            # Try to stop the engine
                            model.llm = None
                    
                    # Delete model reference
                    del model
                except Exception as e:
                    logger.debug(f"Error cleaning up model {model_name}: {e}")
            
            # Clear pipeline models
            pipeline.models.clear()
            del pipeline
            
        except Exception as e:
            logger.debug(f"Error during pipeline cleanup: {e}")
        
        # Shutdown Ray if it's initialized to prevent "ray.init twice" errors
        try:
            import ray
            if ray.is_initialized():
                logger.debug("Shutting down Ray instance")
                ray.shutdown()
        except Exception as e:
            logger.debug(f"Could not shutdown Ray: {e}")
    
    def step_4_compute_metrics(self, results: Dict) -> Dict:
        """Step 4: Compute evaluation metrics."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 4: METRICS COMPUTATION")
        logger.info("=" * 80)
        
        task = self.config['tasks'][0]
        stance_options = task['stance_options']
        
        analyzer = ResultsAnalyzer(str(self.results_dir))
        
        # Get model names
        model_names = list(self.config['models'])
        model_names = [m['name'] for m in model_names]
        
        logger.info(f"Computing metrics for {len(model_names)} models")
        
        metrics_by_model = {}
        
        for model_name in model_names:
            logger.info(f"  Processing {model_name}...")
            try:
                metrics = analyzer.compute_model_metrics_by_variant(
                    results, model_name, stance_options
                )
                metrics_by_model[model_name] = metrics
            except Exception as e:
                logger.warning(f"    Error computing metrics: {e}")
        
        # Save metrics
        metrics_file = self.results_dir / "metrics_by_model.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics_by_model, f, indent=2, default=str)
        
        logger.info(f"Metrics saved to {metrics_file}")
        
        return metrics_by_model
    
    def step_5_analysis_and_visualization(self, metrics_by_model: Dict):
        """Step 5: Generate analysis and visualizations."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 5: ANALYSIS & VISUALIZATION")
        logger.info("=" * 80)
        
        visualizer = ResultsVisualizer(str(self.results_dir / "figures"))
        visualizer.generate_all_plots(metrics_by_model)
        
        logger.info(f"Figures saved to {visualizer.output_dir}")
    
    def step_6_generate_report(self, metrics_by_model: Dict):
        """Step 6: Generate summary report."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 6: REPORT GENERATION")
        logger.info("=" * 80)
        
        report = {
            'experiment_config': self.config,
            'summary_statistics': {},
            'key_findings': [],
        }
        
        # Compute summary statistics
        for model_name, variants in metrics_by_model.items():
            model_stats = {
                'variants': len(variants),
                'avg_accuracy': np.mean([m.get('accuracy', 0) for m in variants.values()]),
                'avg_ece': np.mean([m.get('ece', 0) for m in variants.values()]),
                'avg_overconfidence_rate': np.mean([m.get('overconfidence_rate', 0) for m in variants.values()]),
            }
            report['summary_statistics'][model_name] = model_stats
        
        # Save report
        report_file = self.results_dir / "experiment_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Report saved to {report_file}")
        
        # Print summary
        logger.info("\nSummary Statistics:")
        for model_name, stats in report['summary_statistics'].items():
            logger.info(f"\n{model_name}:")
            logger.info(f"  Avg Accuracy: {stats['avg_accuracy']:.3f}")
            logger.info(f"  Avg ECE: {stats['avg_ece']:.3f}")
            logger.info(f"  Avg Overconfidence Rate: {stats['avg_overconfidence_rate']:.3f}")
    
    def run(self, steps: List[str] = None):
        """Run the complete experiment pipeline."""
        if steps is None:
            steps = ['explore', 'variants', 'inference', 'metrics', 'analysis', 'report']
        
        logger.info("Starting LLM Context & Confidence Experiment")
        logger.info(f"Configuration: {self.config['reproducibility']['version']}")
        
        loader = None
        samples = None
        results = None
        metrics = None
        
        try:
            if 'explore' in steps:
                loader, _ = self.step_1_explore_data()
            
            # If variants or inference step is requested but loader not initialized, load data
            if ('variants' in steps or 'inference' in steps) and loader is None:
                logger.info("Loading data for variant generation...")
                from data_loader import DataLoader
                loader = DataLoader()
                loader.load_all()
            
            if 'variants' in steps and loader:
                samples = self.step_2_generate_context_variants(loader, num_samples=self.num_samples)
            
            if 'inference' in steps and samples:
                results = self.step_3_llm_inference(samples)
            
            if 'metrics' in steps and results:
                metrics = self.step_4_compute_metrics(results)
            
            if 'analysis' in steps and metrics:
                self.step_5_analysis_and_visualization(metrics)
            
            if 'report' in steps and metrics:
                self.step_6_generate_report(metrics)
            
            logger.info("\n" + "=" * 80)
            logger.info("EXPERIMENT COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            logger.info(f"Results saved to: {self.results_dir}")
        
        except Exception as e:
            logger.error(f"Experiment failed with error: {e}", exc_info=True)
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run LLM Context & Confidence Experiment"
    )
    parser.add_argument(
        '--config',
        default='experiment_config.yaml',
        help='Path to experiment config file'
    )
    parser.add_argument(
        '--steps',
        nargs='+',
        default=['explore', 'variants', 'inference', 'metrics', 'analysis', 'report'],
        choices=['explore', 'variants', 'inference', 'metrics', 'analysis', 'report'],
        help='Steps to run'
    )
    parser.add_argument(
        '--num-samples',
        type=int,
        default=None,
        help='Number of samples to process (None for all)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run with minimal data for testing'
    )
    parser.add_argument(
        '--confidence-only',
        action='store_true',
        help='Only record model confidence, skip full predictions'
    )
    parser.add_argument(
        '--gpus',
        type=str,
        default='0,1',
        help='GPU devices to use (comma-separated, e.g., "1,2")'
    )
    
    args = parser.parse_args()
    
    # Set CUDA_VISIBLE_DEVICES globally before loading any models
    import os
    os.environ['CUDA_VISIBLE_DEVICES'] = args.gpus
    logger.info(f"Setting global CUDA_VISIBLE_DEVICES={args.gpus}")
    
    runner = ExperimentRunner(
        config_path=args.config,
        num_samples=args.num_samples,
        confidence_only=args.confidence_only,
        timestamp=None  # Auto-generate timestamp
    )
    runner.run(steps=args.steps)


if __name__ == "__main__":
    main()
