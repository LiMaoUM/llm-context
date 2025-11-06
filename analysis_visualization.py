"""
Analysis and visualization for LLM context experiment results.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from evaluation_metrics import ComprehensiveMetrics, ContextSensitivityMetrics


class ResultsAnalyzer:
    """Analyze experiment results."""
    
    def __init__(self, results_dir: str = "./results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
    
    def load_results(self, filename: str) -> List[Dict]:
        """Load JSON results file."""
        filepath = self.results_dir / filename
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def extract_model_performance(
        self,
        results: List[Dict],
        variant_name: str,
        model_name: str
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extract predictions, confidence, and ground truth for a model and variant.
        
        Returns:
            (y_true, y_pred, confidence)
        """
        y_true = []
        y_pred = []
        confidence = []
        
        for sample in results:
            gt = sample.get('ground_truth')
            if not gt:
                continue
            
            variant_result = sample.get('variants', {}).get(variant_name)
            if not variant_result:
                continue
            
            model_result = variant_result.get('model_results', {}).get(model_name)
            if not model_result or not model_result.get('success'):
                continue
            
            # Extract prediction from response
            response_text = model_result.get('response_text', '')
            conf = model_result.get('confidence')
            
            if conf is None:
                continue
            
            y_true.append(gt)
            confidence.append(conf)
            # TODO: Extract prediction from response text
            # y_pred.append(extracted_pred)
        
        return np.array(y_true), np.array(y_pred), np.array(confidence)
    
    def compute_model_metrics_by_variant(
        self,
        results: List[Dict],
        model_name: str,
        stance_options: List[str]
    ) -> Dict[str, Dict]:
        """Compute metrics for all context variants for a model."""
        variants = set()
        for sample in results:
            variants.update(sample.get('variants', {}).keys())
        
        metrics_by_variant = {}
        
        for variant in sorted(variants):
            y_true, y_pred, confidence = self.extract_model_performance(
                results, variant, model_name
            )
            
            if len(y_true) == 0:
                continue
            
            metrics = ComprehensiveMetrics.compute_all_metrics(
                y_true, y_pred, confidence, stance_options
            )
            metrics_by_variant[variant] = metrics
        
        return metrics_by_variant
    
    def compute_all_models_metrics(
        self,
        results: List[Dict],
        model_names: List[str],
        stance_options: List[str]
    ) -> Dict[str, Dict]:
        """Compute metrics for all models across all variants."""
        all_metrics = {}
        
        for model in model_names:
            all_metrics[model] = self.compute_model_metrics_by_variant(
                results, model, stance_options
            )
        
        return all_metrics
    
    def extract_calibration_data(
        self,
        results: List[Dict],
        model_name: str,
        variant_name: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Extract confidence and correctness for calibration curve."""
        confidence_vals = []
        correctness = []
        
        for sample in results:
            gt = sample.get('ground_truth')
            if not gt:
                continue
            
            variant_result = sample.get('variants', {}).get(variant_name)
            if not variant_result:
                continue
            
            model_result = variant_result.get('model_results', {}).get(model_name)
            if not model_result or not model_result.get('success'):
                continue
            
            conf = model_result.get('confidence')
            if conf is None:
                continue
            
            # TODO: Extract prediction and compute correctness
            confidence_vals.append(conf)
            # correctness.append(pred == gt)
        
        return np.array(confidence_vals), np.array(correctness)


class ResultsVisualizer:
    """Create visualizations for experiment results."""
    
    def __init__(self, output_dir: str = "./figures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        sns.set_style("whitegrid")
    
    def plot_accuracy_by_context(
        self,
        metrics_by_model: Dict[str, Dict],
        figsize: Tuple = (12, 6),
        save_name: str = "accuracy_by_context.png"
    ):
        """Plot accuracy for each context variant across models."""
        data = []
        
        for model, variants in metrics_by_model.items():
            for variant, metrics in variants.items():
                data.append({
                    'Model': model,
                    'Context': variant,
                    'Accuracy': metrics.get('accuracy', 0) * 100,
                })
        
        df = pd.DataFrame(data)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot by model
        for model in df['Model'].unique():
            model_data = df[df['Model'] == model]
            ax.plot(
                model_data['Context'],
                model_data['Accuracy'],
                marker='o',
                label=model,
                linewidth=2
            )
        
        ax.set_xlabel('Context Variant', fontsize=12)
        ax.set_ylabel('Accuracy (%)', fontsize=12)
        ax.set_title('Accuracy vs Context Type', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_calibration_curve(
        self,
        confidence: np.ndarray,
        accuracy: np.ndarray,
        model_name: str,
        figsize: Tuple = (8, 6),
        save_name: str = "calibration_curve.png"
    ):
        """Plot calibration curve."""
        # Bin confidence values
        n_bins = 10
        bins = np.linspace(0, 100, n_bins + 1)
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        bin_accuracy = []
        bin_confidence = []
        bin_counts = []
        
        for i in range(n_bins):
            in_bin = (confidence > bins[i]) & (confidence <= bins[i + 1])
            if in_bin.sum() > 0:
                bin_accuracy.append(accuracy[in_bin].mean() * 100)
                bin_confidence.append(confidence[in_bin].mean())
                bin_counts.append(in_bin.sum())
            else:
                bin_accuracy.append(None)
                bin_confidence.append(None)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Plot perfect calibration line
        ax.plot([0, 100], [0, 100], 'k--', label='Perfect Calibration', linewidth=2)
        
        # Plot calibration curve
        ax.scatter(bin_confidence, bin_accuracy, s=np.array(bin_counts) * 10, alpha=0.6)
        
        ax.set_xlabel('Predicted Confidence (%)', fontsize=12)
        ax.set_ylabel('Actual Accuracy (%)', fontsize=12)
        ax.set_title(f'Calibration Curve - {model_name}', fontsize=14, fontweight='bold')
        ax.set_xlim([0, 100])
        ax.set_ylim([0, 100])
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_ece_by_context(
        self,
        metrics_by_model: Dict[str, Dict],
        figsize: Tuple = (12, 6),
        save_name: str = "ece_by_context.png"
    ):
        """Plot Expected Calibration Error across contexts."""
        data = []
        
        for model, variants in metrics_by_model.items():
            for variant, metrics in variants.items():
                data.append({
                    'Model': model,
                    'Context': variant,
                    'ECE': metrics.get('ece', 0),
                })
        
        df = pd.DataFrame(data)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        for model in df['Model'].unique():
            model_data = df[df['Model'] == model]
            ax.plot(
                model_data['Context'],
                model_data['ECE'],
                marker='o',
                label=model,
                linewidth=2
            )
        
        ax.set_xlabel('Context Variant', fontsize=12)
        ax.set_ylabel('Expected Calibration Error', fontsize=12)
        ax.set_title('Calibration Error vs Context Type', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_overconfidence_rate(
        self,
        metrics_by_model: Dict[str, Dict],
        figsize: Tuple = (12, 6),
        save_name: str = "overconfidence_by_context.png"
    ):
        """Plot overconfidence rate across contexts."""
        data = []
        
        for model, variants in metrics_by_model.items():
            for variant, metrics in variants.items():
                data.append({
                    'Model': model,
                    'Context': variant,
                    'Overconfidence Rate': metrics.get('overconfidence_rate', 0) * 100,
                })
        
        df = pd.DataFrame(data)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        for model in df['Model'].unique():
            model_data = df[df['Model'] == model]
            ax.plot(
                model_data['Context'],
                model_data['Overconfidence Rate'],
                marker='o',
                label=model,
                linewidth=2
            )
        
        ax.set_xlabel('Context Variant', fontsize=12)
        ax.set_ylabel('Overconfidence Rate (%)', fontsize=12)
        ax.set_title('Overconfidence vs Context Type (>70% confidence on wrong predictions)', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_context_sensitivity_heatmap(
        self,
        metrics_by_model: Dict[str, Dict],
        figsize: Tuple = (10, 8),
        save_name: str = "context_sensitivity_heatmap.png"
    ):
        """Heatmap of accuracy across models and context types."""
        # Create matrix
        models = list(metrics_by_model.keys())
        variants = None
        
        for model in models:
            if variants is None:
                variants = list(metrics_by_model[model].keys())
            break
        
        if not variants:
            return
        
        accuracy_matrix = np.zeros((len(models), len(variants)))
        
        for i, model in enumerate(models):
            for j, variant in enumerate(variants):
                acc = metrics_by_model[model][variant].get('accuracy', 0) * 100
                accuracy_matrix[i, j] = acc
        
        fig, ax = plt.subplots(figsize=figsize)
        
        sns.heatmap(
            accuracy_matrix,
            xticklabels=variants,
            yticklabels=models,
            annot=True,
            fmt='.1f',
            cmap='RdYlGn',
            vmin=0,
            vmax=100,
            ax=ax,
            cbar_kws={'label': 'Accuracy (%)'}
        )
        
        ax.set_xlabel('Context Variant', fontsize=12)
        ax.set_ylabel('Model', fontsize=12)
        ax.set_title('Accuracy Heatmap: Models vs Context Types', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_marginal_improvements(
        self,
        metrics_by_model: Dict[str, Dict],
        figsize: Tuple = (12, 6),
        save_name: str = "marginal_improvements.png"
    ):
        """Plot marginal improvement from adding each context type."""
        data = []
        
        for model, variants in metrics_by_model.items():
            analysis = ContextSensitivityMetrics.context_sensitivity_analysis(variants)
            
            for variant, improvements in analysis['marginal_improvements'].items():
                data.append({
                    'Model': model,
                    'Context Addition': variant,
                    'Accuracy Improvement': improvements.get('accuracy', 0) * 100,
                })
        
        df = pd.DataFrame(data)
        
        fig, ax = plt.subplots(figsize=figsize)
        
        x = np.arange(len(df['Context Addition'].unique()))
        width = 0.15
        
        for i, model in enumerate(df['Model'].unique()):
            model_data = df[df['Model'] == model].set_index('Context Addition').loc[df['Context Addition'].unique()]
            ax.bar(x + i * width, model_data['Accuracy Improvement'], width, label=model)
        
        ax.set_xlabel('Context Addition', fontsize=12)
        ax.set_ylabel('Accuracy Improvement (%)', fontsize=12)
        ax.set_title('Marginal Improvement from Adding Context', fontsize=14, fontweight='bold')
        ax.set_xticks(x + width * len(df['Model'].unique()) / 2)
        ax.set_xticklabels(df['Context Addition'].unique(), rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / save_name, dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_all_plots(self, metrics_by_model: Dict[str, Dict]):
        """Generate all standard plots."""
        print("Generating plots...")
        
        self.plot_accuracy_by_context(metrics_by_model)
        print("  ✓ Accuracy by context")
        
        self.plot_ece_by_context(metrics_by_model)
        print("  ✓ ECE by context")
        
        self.plot_overconfidence_rate(metrics_by_model)
        print("  ✓ Overconfidence rate")
        
        self.plot_context_sensitivity_heatmap(metrics_by_model)
        print("  ✓ Context sensitivity heatmap")
        
        self.plot_marginal_improvements(metrics_by_model)
        print("  ✓ Marginal improvements")


if __name__ == "__main__":
    # Example usage
    print("Analysis and Visualization Module")
    print("Use this module to analyze and visualize experiment results.")
