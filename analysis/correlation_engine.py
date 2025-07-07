"""
Correlation engine for computing diagnostic-vs-outcome metric relationships.

Analyzes relationships between performance diagnostics and game outcomes,
providing comparative analysis across multiple runs.
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from utils.log_parser import LogParser, GameOutcomeMetrics, DiagnosticMetrics


@dataclass
class CorrelationResult:
    """Result of correlation analysis between diagnostics and outcomes"""
    metric_name: str
    correlation_coefficient: float
    p_value: float
    significance: str  # "strong", "moderate", "weak", "none"


@dataclass
class RunComparison:
    """Comparison between two runs showing metric differences"""
    run1_id: str
    run2_id: str
    outcome_differences: Dict[str, float]
    diagnostic_differences: Dict[str, float]
    significant_changes: List[str]


@dataclass
class AnalysisReport:
    """Complete analysis report for one or more runs"""
    game_id: str
    run_count: int
    outcome_summary: Dict[str, Any]
    diagnostic_summary: Dict[str, Any]
    correlations: List[CorrelationResult]
    comparisons: List[RunComparison]
    recommendations: List[str]


class CorrelationEngine:
    """Engine for analyzing correlations between diagnostics and outcomes"""
    
    def __init__(self):
        self.log_parser = LogParser()
        
    def analyze_single_run(self, debug_path: Path, game_id: str) -> AnalysisReport:
        """
        Analyze a single run and provide basic metrics report.
        
        Args:
            debug_path: Path to debug directory  
            game_id: Game ID to analyze
            
        Returns:
            Analysis report for the single run
        """
        runs = self.log_parser.parse_multiple_runs(debug_path, game_id)
        
        if not runs:
            return AnalysisReport(
                game_id=game_id,
                run_count=0,
                outcome_summary={},
                diagnostic_summary={},
                correlations=[],
                comparisons=[],
                recommendations=["No valid runs found for analysis"]
            )
            
        if len(runs) == 1:
            outcome, diagnostic = runs[0]
            return self._create_single_run_report(game_id, outcome, diagnostic)
        else:
            return self._create_multi_run_report(game_id, runs)
    
    def analyze_multiple_runs(self, debug_path: Path, game_id: str) -> AnalysisReport:
        """
        Analyze multiple runs for the same game ID and provide comparison.
        
        Args:
            debug_path: Path to debug directory
            game_id: Game ID to analyze
            
        Returns:
            Analysis report comparing multiple runs
        """
        runs = self.log_parser.parse_multiple_runs(debug_path, game_id)
        
        if len(runs) < 2:
            return self.analyze_single_run(debug_path, game_id)
            
        return self._create_multi_run_report(game_id, runs)
    
    def _create_single_run_report(self, game_id: str, outcome: GameOutcomeMetrics, 
                                diagnostic: DiagnosticMetrics) -> AnalysisReport:
        """Create analysis report for a single run"""
        
        outcome_summary = asdict(outcome)
        
        # Summarize diagnostic metrics
        diagnostic_summary = {
            "gamestate": self._summarize_metrics(diagnostic.gamestate_metrics),
            "move_executor": self._summarize_metrics(diagnostic.move_executor_metrics),
            "position_evaluator": self._summarize_metrics(diagnostic.position_evaluator_metrics),
            "search": self._summarize_metrics(diagnostic.search_metrics)
        }
        
        # Generate recommendations based on single run
        recommendations = self._generate_single_run_recommendations(outcome, diagnostic)
        
        return AnalysisReport(
            game_id=game_id,
            run_count=1,
            outcome_summary=outcome_summary,
            diagnostic_summary=diagnostic_summary,
            correlations=[],  # No correlations for single run
            comparisons=[],   # No comparisons for single run
            recommendations=recommendations
        )
    
    def _create_multi_run_report(self, game_id: str, 
                               runs: List[Tuple[GameOutcomeMetrics, DiagnosticMetrics]]) -> AnalysisReport:
        """Create analysis report for multiple runs with correlations and comparisons"""
        
        outcomes = [run[0] for run in runs]
        diagnostics = [run[1] for run in runs]
        
        # Calculate aggregate outcome summary
        outcome_summary = self._aggregate_outcomes(outcomes)
        
        # Calculate aggregate diagnostic summary
        diagnostic_summary = self._aggregate_diagnostics(diagnostics)
        
        # Calculate correlations between diagnostics and outcomes
        correlations = self._calculate_correlations(outcomes, diagnostics)
        
        # Generate pairwise comparisons
        comparisons = self._generate_comparisons(runs)
        
        # Generate recommendations based on analysis
        recommendations = self._generate_multi_run_recommendations(outcomes, diagnostics, correlations)
        
        return AnalysisReport(
            game_id=game_id,
            run_count=len(runs),
            outcome_summary=outcome_summary,
            diagnostic_summary=diagnostic_summary,
            correlations=correlations,
            comparisons=comparisons,
            recommendations=recommendations
        )
    
    def _summarize_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize a collection of metrics with basic statistics"""
        summary = {}
        for metric_name, values in metrics.items():
            if isinstance(values, list) and values:
                if len(values) == 1:
                    summary[metric_name] = {
                        "value": values[0],
                        "count": 1
                    }
                else:
                    summary[metric_name] = {
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values),
                        "stdev": statistics.stdev(values) if len(values) > 1 else 0
                    }
            else:
                summary[metric_name] = {"value": values, "count": 0}
        return summary
    
    def _aggregate_outcomes(self, outcomes: List[GameOutcomeMetrics]) -> Dict[str, Any]:
        """Aggregate outcome metrics across multiple runs"""
        if not outcomes:
            return {}
            
        aggregated = {}
        
        # Win rate
        wins = sum(1 for o in outcomes if o.win_status)
        aggregated["win_rate"] = wins / len(outcomes)
        
        # Average metrics
        aggregated["avg_total_moves"] = statistics.mean([o.total_moves for o in outcomes])
        aggregated["avg_redeals_used"] = statistics.mean([o.redeals_used for o in outcomes])
        aggregated["avg_final_placed_cards"] = statistics.mean([o.final_placed_cards_count for o in outcomes])
        aggregated["avg_sequence_length"] = statistics.mean([o.average_sequence_length_per_row for o in outcomes])
        aggregated["avg_run_duration"] = statistics.mean([o.run_duration for o in outcomes])
        
        # Min/Max metrics
        aggregated["best_final_placed_cards"] = max([o.final_placed_cards_count for o in outcomes])
        aggregated["worst_final_placed_cards"] = min([o.final_placed_cards_count for o in outcomes])
        aggregated["fastest_run"] = min([o.run_duration for o in outcomes])
        aggregated["slowest_run"] = max([o.run_duration for o in outcomes])
        
        return aggregated
    
    def _aggregate_diagnostics(self, diagnostics: List[DiagnosticMetrics]) -> Dict[str, Any]:
        """Aggregate diagnostic metrics across multiple runs"""
        if not diagnostics:
            return {}
            
        # Combine all diagnostic metrics from all runs
        all_gamestate = []
        all_move_executor = []
        all_position_evaluator = []
        all_search = []
        
        for diag in diagnostics:
            all_gamestate.append(diag.gamestate_metrics)
            all_move_executor.append(diag.move_executor_metrics)
            all_position_evaluator.append(diag.position_evaluator_metrics)
            all_search.append(diag.search_metrics)
        
        return {
            "gamestate": self._aggregate_metric_group(all_gamestate),
            "move_executor": self._aggregate_metric_group(all_move_executor),
            "position_evaluator": self._aggregate_metric_group(all_position_evaluator),
            "search": self._aggregate_metric_group(all_search)
        }
    
    def _aggregate_metric_group(self, metric_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate a group of metrics (e.g., all gamestate metrics)"""
        aggregated = {}
        
        # Get all unique metric names
        all_metric_names = set()
        for group in metric_groups:
            all_metric_names.update(group.keys())
        
        for metric_name in all_metric_names:
            all_values = []
            for group in metric_groups:
                if metric_name in group and group[metric_name]:
                    if isinstance(group[metric_name], list):
                        all_values.extend(group[metric_name])
                    else:
                        all_values.append(group[metric_name])
            
            if all_values:
                if len(all_values) == 1:
                    aggregated[metric_name] = {"value": all_values[0], "count": 1}
                else:
                    aggregated[metric_name] = {
                        "mean": statistics.mean(all_values),
                        "median": statistics.median(all_values),
                        "min": min(all_values),
                        "max": max(all_values),
                        "count": len(all_values)
                    }
                    
        return aggregated
    
    def _calculate_correlations(self, outcomes: List[GameOutcomeMetrics], 
                              diagnostics: List[DiagnosticMetrics]) -> List[CorrelationResult]:
        """Calculate correlations between diagnostic metrics and outcomes"""
        correlations = []
        
        if len(outcomes) < 2:
            return correlations
        
        # Extract outcome values for correlation
        win_status_values = [1 if o.win_status else 0 for o in outcomes]
        total_moves_values = [o.total_moves for o in outcomes]
        final_cards_values = [o.final_placed_cards_count for o in outcomes]
        
        # Extract key diagnostic metrics
        for i, diag in enumerate(diagnostics):
            # Position evaluator average score
            if diag.position_evaluator_metrics.get('score'):
                avg_scores = diag.position_evaluator_metrics['score']
                if avg_scores:
                    avg_score = statistics.mean(avg_scores)
                    corr = self._simple_correlation(final_cards_values, 
                                                  [avg_score if j == i else 0 for j in range(len(outcomes))])
                    if corr is not None:
                        correlations.append(CorrelationResult(
                            metric_name="avg_position_score",
                            correlation_coefficient=corr,
                            p_value=0.0,  # Simplified
                            significance=self._interpret_correlation(corr)
                        ))
        
        return correlations
    
    def _simple_correlation(self, x: List[float], y: List[float]) -> Optional[float]:
        """Calculate simple Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return None
            
        try:
            # Remove zero values from y (placeholder values)
            pairs = [(x[i], y[i]) for i in range(len(x)) if y[i] != 0]
            if len(pairs) < 2:
                return None
                
            x_vals = [p[0] for p in pairs]
            y_vals = [p[1] for p in pairs]
            
            return statistics.correlation(x_vals, y_vals)
        except (statistics.StatisticsError, ZeroDivisionError):
            return None
    
    def _interpret_correlation(self, corr: float) -> str:
        """Interpret correlation strength"""
        abs_corr = abs(corr)
        if abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.4:
            return "moderate"
        elif abs_corr >= 0.2:
            return "weak"
        else:
            return "none"
    
    def _generate_comparisons(self, runs: List[Tuple[GameOutcomeMetrics, DiagnosticMetrics]]) -> List[RunComparison]:
        """Generate pairwise comparisons between runs"""
        comparisons = []
        
        for i in range(len(runs)):
            for j in range(i + 1, len(runs)):
                outcome1, diag1 = runs[i]
                outcome2, diag2 = runs[j]
                
                comparison = self._compare_two_runs(f"run_{i+1}", f"run_{j+1}", 
                                                  outcome1, outcome2, diag1, diag2)
                comparisons.append(comparison)
        
        return comparisons
    
    def _compare_two_runs(self, run1_id: str, run2_id: str,
                         outcome1: GameOutcomeMetrics, outcome2: GameOutcomeMetrics,
                         diag1: DiagnosticMetrics, diag2: DiagnosticMetrics) -> RunComparison:
        """Compare two individual runs"""
        
        # Calculate outcome differences
        outcome_diff = {
            "total_moves": outcome2.total_moves - outcome1.total_moves,
            "redeals_used": outcome2.redeals_used - outcome1.redeals_used,
            "final_placed_cards": outcome2.final_placed_cards_count - outcome1.final_placed_cards_count,
            "run_duration": outcome2.run_duration - outcome1.run_duration,
            "win_status_change": 1 if outcome2.win_status and not outcome1.win_status else
                               -1 if outcome1.win_status and not outcome2.win_status else 0
        }
        
        # Calculate diagnostic differences (simplified)
        diagnostic_diff = {}
        
        # Identify significant changes (>10% difference)
        significant = []
        for metric, diff in outcome_diff.items():
            if metric == "win_status_change" and diff != 0:
                significant.append(f"Win status changed: {diff}")
            elif metric != "win_status_change" and abs(diff) > 0.1 * getattr(outcome1, metric.replace("final_placed_cards", "final_placed_cards_count")):
                significant.append(f"{metric}: {diff:+.2f}")
        
        return RunComparison(
            run1_id=run1_id,
            run2_id=run2_id,
            outcome_differences=outcome_diff,
            diagnostic_differences=diagnostic_diff,
            significant_changes=significant
        )
    
    def _generate_single_run_recommendations(self, outcome: GameOutcomeMetrics, 
                                           diagnostic: DiagnosticMetrics) -> List[str]:
        """Generate recommendations based on single run analysis"""
        recommendations = []
        
        if not outcome.win_status:
            if outcome.final_placed_cards_count < 40:
                recommendations.append("Consider increasing search depth to improve card placement")
            if outcome.run_duration > 10.0:
                recommendations.append("Run duration is high - consider optimizing search time limits")
        
        # Check diagnostic metrics for optimization opportunities
        if diagnostic.search_metrics.get('positions_per_second'):
            pos_per_sec = diagnostic.search_metrics['positions_per_second']
            if pos_per_sec and max(pos_per_sec) < 10000:
                recommendations.append("Low search speed detected - consider enabling optimizations")
        
        return recommendations
    
    def _generate_multi_run_recommendations(self, outcomes: List[GameOutcomeMetrics],
                                          diagnostics: List[DiagnosticMetrics],
                                          correlations: List[CorrelationResult]) -> List[str]:
        """Generate recommendations based on multi-run analysis"""
        recommendations = []
        
        # Check win rate
        win_rate = sum(1 for o in outcomes if o.win_status) / len(outcomes)
        if win_rate < 0.5:
            recommendations.append(f"Low win rate ({win_rate:.1%}) - consider adjusting search parameters")
        
        # Check consistency
        durations = [o.run_duration for o in outcomes]
        if len(durations) > 1 and statistics.stdev(durations) > statistics.mean(durations) * 0.5:
            recommendations.append("High variance in run duration - settings may need tuning")
        
        # Check for strong correlations
        strong_corr = [c for c in correlations if c.significance == "strong"]
        if strong_corr:
            recommendations.append("Strong correlations found - consider leveraging these for optimization")
        
        return recommendations