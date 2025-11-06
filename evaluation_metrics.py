"""
Evaluation metrics for LLM confidence and calibration analysis.
"""

import numpy as np
from typing import Dict, List, Tuple
from sklearn.metrics import (
    accuracy_score, f1_score, confusion_matrix, 
    classification_report
)


class CalibrationMetrics:
    """Compute calibration metrics for confidence analysis."""
    
    @staticmethod
    def expected_calibration_error(
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        confidence: np.ndarray,
        num_bins: int = 10
    ) -> Tuple[float, Dict]:
        """
        Compute Expected Calibration Error (ECE).
        
        ECE measures the difference between predicted confidence and actual accuracy.
        Lower ECE indicates better calibration.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            confidence: Predicted confidence (0-100 or 0-1)
            num_bins: Number of bins for calibration
        
        Returns:
            ece: float - Expected Calibration Error
            details: Dict with bin-wise breakdown
        """
        # Normalize confidence to 0-1 if needed
        if confidence.max() > 1:
            confidence = confidence / 100.0
        
        # Compute correctness
        correct = (y_true == y_pred).astype(float)
        
        # Initialize bin tracking
        bin_accs = []
        bin_confs = []
        bin_counts = []
        
        # Create bins
        bin_boundaries = np.linspace(0, 1, num_bins + 1)
        ece = 0.0
        
        for i in range(num_bins):
            lower = bin_boundaries[i]
            upper = bin_boundaries[i + 1]
            
            # Find samples in this bin
            in_bin = (confidence > lower) & (confidence <= upper)
            
            if in_bin.sum() > 0:
                bin_acc = correct[in_bin].mean()
                bin_conf = confidence[in_bin].mean()
                bin_count = in_bin.sum()
                
                bin_accs.append(bin_acc)
                bin_confs.append(bin_conf)
                bin_counts.append(bin_count)
                
                # Add weighted difference to ECE
                ece += (bin_count / len(y_true)) * abs(bin_acc - bin_conf)
        
        details = {
            'bin_accuracies': bin_accs,
            'bin_confidences': bin_confs,
            'bin_counts': bin_counts,
            'num_bins_with_data': len(bin_accs),
        }
        
        return ece, details
    
    @staticmethod
    def brier_score(
        y_true: np.ndarray,
        y_pred_proba: np.ndarray
    ) -> float:
        """
        Compute Brier Score.
        
        Measures mean squared error between predicted probabilities and actual outcomes.
        Lower is better (range 0-1).
        
        Args:
            y_true: True binary labels (0/1)
            y_pred_proba: Predicted probabilities (0-1)
        
        Returns:
            Brier score
        """
        return np.mean((y_pred_proba - y_true) ** 2)
    
    @staticmethod
    def overconfidence_rate(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        confidence: np.ndarray,
        threshold: float = 70
    ) -> Tuple[float, int]:
        """
        Compute fraction of incorrect predictions with high confidence.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            confidence: Predicted confidence (0-100)
            threshold: Confidence threshold (default 70%)
        
        Returns:
            rate: float - fraction of incorrect with high confidence
            count: int - number of such cases
        """
        incorrect = y_true != y_pred
        high_conf = confidence >= threshold
        
        overconfident = (incorrect & high_conf).sum()
        
        if incorrect.sum() == 0:
            return 0.0, 0
        
        rate = overconfident / incorrect.sum()
        return rate, overconfident
    
    @staticmethod
    def confidence_by_correctness(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        confidence: np.ndarray
    ) -> Dict[str, float]:
        """
        Compare average confidence for correct vs incorrect predictions.
        
        Returns:
            Dict with metrics for both cases
        """
        correct = y_true == y_pred
        incorrect = y_true != y_pred
        
        results = {
            'correct_mean_confidence': confidence[correct].mean() if correct.sum() > 0 else None,
            'correct_std_confidence': confidence[correct].std() if correct.sum() > 0 else None,
            'correct_count': correct.sum(),
            'incorrect_mean_confidence': confidence[incorrect].mean() if incorrect.sum() > 0 else None,
            'incorrect_std_confidence': confidence[incorrect].std() if incorrect.sum() > 0 else None,
            'incorrect_count': incorrect.sum(),
            'confidence_gap': (confidence[correct].mean() - confidence[incorrect].mean()) if correct.sum() > 0 and incorrect.sum() > 0 else None,
        }
        
        return results


class ContextSensitivityMetrics:
    """Compute metrics for context ablation analysis."""
    
    @staticmethod
    def marginal_improvement(
        baseline_metrics: Dict,
        variant_metrics: Dict,
        metric_name: str = 'accuracy'
    ) -> float:
        """
        Compute improvement from adding a context layer.
        
        Args:
            baseline_metrics: Metrics dict for baseline (e.g., 'T')
            variant_metrics: Metrics dict for variant (e.g., 'T+C')
            metric_name: Metric to compare
        
        Returns:
            Improvement delta
        """
        baseline = baseline_metrics.get(metric_name, 0)
        variant = variant_metrics.get(metric_name, 0)
        return variant - baseline
    
    @staticmethod
    def context_sensitivity_analysis(
        results_by_variant: Dict[str, Dict]
    ) -> Dict:
        """
        Analyze sensitivity across context variants.
        
        Args:
            results_by_variant: Dict mapping variant names to metric dicts
                {
                    'T': {'accuracy': 0.7, 'ece': 0.15, ...},
                    'T+C': {'accuracy': 0.75, 'ece': 0.12, ...},
                    ...
                }
        
        Returns:
            Sensitivity analysis with marginal improvements
        """
        baseline = results_by_variant.get('T', {})
        
        analysis = {
            'baseline_metrics': baseline,
            'marginal_improvements': {},
            'cumulative_improvements': {},
        }
        
        # Compute marginal improvements for each variant
        for variant, metrics in results_by_variant.items():
            if variant == 'T':
                continue
            
            improvements = {}
            for metric_name in baseline.keys():
                improvements[metric_name] = metrics.get(metric_name, 0) - baseline.get(metric_name, 0)
            
            analysis['marginal_improvements'][variant] = improvements
        
        return analysis
    
    @staticmethod
    def diminishing_returns_analysis(
        results_by_variant: Dict[str, Dict]
    ) -> Dict:
        """
        Analyze diminishing returns as context depth increases.
        
        Context depth ordering:
            T (depth 1) < T+X (depth 2) < T+X+Y (depth 3) < FULL (depth 4)
        
        Returns:
            Analysis of improvement rate by depth
        """
        # Map variants to depths
        depth_map = {
            'T': 1,
            'T+C': 2, 'T+B': 2, 'T+M': 2,
            'T+C+B': 3, 'T+C+M': 3, 'T+B+M': 3,
            'FULL': 4,
        }
        
        # Group by depth
        by_depth = {}
        for variant, metrics in results_by_variant.items():
            depth = depth_map.get(variant)
            if depth not in by_depth:
                by_depth[depth] = []
            by_depth[depth].append(metrics)
        
        # Compute average accuracy by depth
        depth_analysis = {}
        for depth in sorted(by_depth.keys()):
            metrics_list = by_depth[depth]
            if metrics_list:
                avg_accuracy = np.mean([m.get('accuracy', 0) for m in metrics_list])
                depth_analysis[f'depth_{depth}'] = {
                    'avg_accuracy': avg_accuracy,
                    'num_variants': len(metrics_list),
                }
        
        # Compute improvements between depths
        depth_improvements = {}
        depths = sorted(depth_analysis.keys())
        for i in range(len(depths) - 1):
            curr_depth = depths[i]
            next_depth = depths[i + 1]
            improvement = (
                depth_analysis[next_depth]['avg_accuracy'] - 
                depth_analysis[curr_depth]['avg_accuracy']
            )
            depth_improvements[f"{curr_depth}_to_{next_depth}"] = improvement
        
        return {
            'by_depth': depth_analysis,
            'improvements_between_depths': depth_improvements,
        }


class ComprehensiveMetrics:
    """Compute all metrics for a complete evaluation."""
    
    @staticmethod
    def compute_all_metrics(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        confidence: np.ndarray,
        labels: List[str] = None,
    ) -> Dict:
        """
        Compute comprehensive metrics for a result set.
        
        Args:
            y_true: True labels
            y_pred: Predicted labels
            confidence: Model confidence (0-100)
            labels: Class names for F1 computation
        
        Returns:
            Dict with all computed metrics
        """
        # Normalize confidence if needed
        if confidence.max() > 1:
            confidence_normalized = confidence / 100.0
        else:
            confidence_normalized = confidence
        
        # Classification metrics
        acc = accuracy_score(y_true, y_pred)
        
        # F1 score (weighted for multi-class)
        if len(np.unique(y_true)) > 2:
            f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        else:
            f1 = f1_score(y_true, y_pred, average='binary', zero_division=0)
        
        # Calibration metrics
        ece, ece_details = CalibrationMetrics.expected_calibration_error(
            y_true, y_pred, confidence
        )
        
        # Confidence analysis
        conf_by_correct = CalibrationMetrics.confidence_by_correctness(
            y_true, y_pred, confidence
        )
        
        # Overconfidence
        overconf_rate, overconf_count = CalibrationMetrics.overconfidence_rate(
            y_true, y_pred, confidence, threshold=70
        )
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        
        metrics = {
            'accuracy': float(acc),
            'f1_weighted': float(f1),
            'ece': float(ece),
            'ece_details': ece_details,
            'confidence_by_correctness': conf_by_correct,
            'overconfidence_rate': float(overconf_rate),
            'overconfidence_count': int(overconf_count),
            'confusion_matrix': cm.tolist(),
            'total_samples': len(y_true),
            'mean_confidence': float(confidence.mean()),
            'std_confidence': float(confidence.std()),
            'min_confidence': float(confidence.min()),
            'max_confidence': float(confidence.max()),
        }
        
        if labels:
            metrics['classification_report'] = classification_report(
                y_true, y_pred, target_names=labels, output_dict=True
            )
        
        return metrics


if __name__ == "__main__":
    # Test metrics
    y_true = np.array([0, 1, 1, 0, 1, 0, 1, 1, 0, 0])
    y_pred = np.array([0, 1, 1, 0, 1, 1, 1, 0, 0, 0])
    confidence = np.array([95, 88, 92, 90, 85, 65, 91, 72, 88, 94])
    
    metrics = ComprehensiveMetrics.compute_all_metrics(y_true, y_pred, confidence)
    import json
    print(json.dumps(metrics, indent=2))
