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
    
    def __init__(self, config_path: str = "experiment_config.yaml"):
        """Initialize experiment runner with config."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.results_dir = Path(self.config['execution']['output_dir'])
        self.results_dir.mkdir(exist_ok=True)
        
        logger.info(f"Experiment configuration loaded from {config_path}")
        logger.info(f"Output directory: {self.results_dir}")
    
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
    
    def step_2_generate_context_variants(self, loader: DataLoader, num_samples: int = 100):
        """Step 2: Generate context variants for sample posts."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: CONTEXT VARIANT GENERATION")
        logger.info("=" * 80)
        
        generator = ContextVariantGenerator(loader)
        
        # Load sample posts
        loader.load_all()
        posts = loader.posts.head(num_samples)
        
        samples_with_variants = []
        
        for idx, (_, post) in enumerate(posts.iterrows()):
            if idx % 20 == 0:
                logger.info(f"Processing sample {idx}/{len(posts)}")
            
            # Get full context
            sample = loader.get_post_with_all_context(post['id'])
            
            if sample is None:
                continue
            
            # Generate variants
            variants = generator.generate_variants(sample)
            
            samples_with_variants.append({
                'sample_id': post['id'],
                'post_text': sample['post_text'],
                'context_variants': variants,
                'ground_truth': None,  # TODO: Add ground truth labels
            })
        
        logger.info(f"Generated variants for {len(samples_with_variants)} samples")
        
        # Save sample structure
        sample_file = self.results_dir / "sample_variants.json"
        with open(sample_file, 'w') as f:
            json.dump(
                [samples_with_variants[0]],  # Save just first for reference
                f, indent=2, default=str
            )
        logger.info(f"Sample variant structure saved to {sample_file}")
        
        return samples_with_variants
    
    def step_3_llm_inference(self, samples: List[Dict]) -> Dict:
        """Step 3: Run LLM inference across all models and variants."""
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: LLM INFERENCE")
        logger.info("=" * 80)
        
        pipeline = InferencePipeline(self.config)
        
        logger.info(f"Initialized {len(pipeline.models)} LLM models")
        for model_name in pipeline.models.keys():
            logger.info(f"  - {model_name}")
        
        # Prepare task config
        task = self.config['tasks'][0]  # First task
        target_entity = task['target_entities'][0]
        stance_options = task['stance_options']
        
        logger.info(f"Task: {task['task_name']}")
        logger.info(f"Target entity: {target_entity}")
        logger.info(f"Stance options: {', '.join(stance_options)}")
        
        # Run inference
        evaluator = BatchEvaluator(pipeline)
        results = evaluator.evaluate_batch(
            samples=samples[:10],  # Start with small batch for testing
            target_entity=target_entity,
            stance_options=stance_options,
            save_interval=5,
            output_file=str(self.results_dir / "inference_results.json")
        )
        
        logger.info(f"Completed inference for {len(results)} samples")
        
        return results
    
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
            
            if 'variants' in steps and loader:
                samples = self.step_2_generate_context_variants(loader)
            
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
        '--dry-run',
        action='store_true',
        help='Run with minimal data for testing'
    )
    
    args = parser.parse_args()
    
    runner = ExperimentRunner(args.config)
    runner.run(steps=args.steps)


if __name__ == "__main__":
    main()
