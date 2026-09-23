"""
Statistical Tests - Validate hypotheses H1 and H2
"""

from scipy import stats
import numpy as np
import pandas as pd
from typing import Dict, List

class StatisticalAnalyzer:
    """Conducts statistical tests for hallucination propagation hypotheses"""
    
    @staticmethod
    def chi_square_test_h1(
        with_fix_data: Dict,
        without_fix_data: Dict
    ) -> Dict:
        """
        Test H1: Explicit fix prompts reduce persistence
        
        Chi-square test comparing persistence rates
        """
        
        persist_with_fix = with_fix_data.get('persisting_count', 0)
        total_with_fix = with_fix_data.get('count', 1)
        resolve_with_fix = total_with_fix - persist_with_fix
        
        persist_without_fix = without_fix_data.get('persisting_count', 0)
        total_without_fix = without_fix_data.get('count', 1)
        resolve_without_fix = total_without_fix - persist_without_fix
        
        contingency_table = np.array([
            [persist_with_fix, resolve_with_fix],
            [persist_without_fix, resolve_without_fix]
        ])
        
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
        
        n = contingency_table.sum()
        min_dim = min(contingency_table.shape) - 1
        cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
        
        return {
            "hypothesis": "H1: Explicit fix prompts reduce persistence",
            "test": "Chi-square test",
            "chi_square_statistic": float(chi2),
            "p_value": float(p_value),
            "degrees_of_freedom": int(dof),
            "significance_level": 0.05,
            "result": "REJECT null hypothesis" if p_value < 0.05 else "FAIL TO REJECT",
            "interpretation": (
                "Explicit fix prompts significantly reduce persistence"
                if p_value < 0.05
                else "No significant difference"
            ),
            "effect_size_cramers_v": float(cramers_v),
            "persistence_rate_with_fix": persist_with_fix / total_with_fix if total_with_fix > 0 else 0,
            "persistence_rate_without_fix": persist_without_fix / total_without_fix if total_without_fix > 0 else 0,
        }
    
    @staticmethod
    def chi_square_test_h2(
        security_data: Dict,
        syntax_data: Dict
    ) -> Dict:
        """
        Test H2: Security hallucinations persist more than syntax
        
        Chi-square test comparing persistence rates
        """
        
        security_persist = security_data.get('persisting', 0)
        security_total = security_data.get('count', 1)
        security_resolve = security_total - security_persist
        
        syntax_persist = syntax_data.get('persisting', 0)
        syntax_total = syntax_data.get('count', 1)
        syntax_resolve = syntax_total - syntax_persist
        
        contingency_table = np.array([
            [security_persist, security_resolve],
            [syntax_persist, syntax_resolve]
        ])
        
        chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
        
        n = contingency_table.sum()
        min_dim = min(contingency_table.shape) - 1
        cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0
        
        security_rate = security_persist / security_total if security_total > 0 else 0
        syntax_rate = syntax_persist / syntax_total if syntax_total > 0 else 0
        
        return {
            "hypothesis": "H2: Security hallucinations persist more than syntax",
            "test": "Chi-square test",
            "chi_square_statistic": float(chi2),
            "p_value": float(p_value),
            "degrees_of_freedom": int(dof),
            "significance_level": 0.05,
            "result": "REJECT null hypothesis" if p_value < 0.05 else "FAIL TO REJECT",
            "interpretation": (
                "Security hallucinations have higher persistence"
                if p_value < 0.05 and security_rate > syntax_rate
                else "No significant difference"
            ),
            "effect_size_cramers_v": float(cramers_v),
            "security_persistence_rate": float(security_rate),
            "syntax_persistence_rate": float(syntax_rate),
            "persistence_rate_difference": float(security_rate - syntax_rate),
        }
    
    @staticmethod
    def t_test_mutation_rates(
        hallucination_type_1: str,
        mutation_rates_1: List[float],
        hallucination_type_2: str,
        mutation_rates_2: List[float],
        test_type: str = "independent"
    ) -> Dict:
        """T-test comparing mutation rates between two hallucination types"""
        
        if len(mutation_rates_1) < 2 or len(mutation_rates_2) < 2:
            return {
                "error": "Insufficient sample size",
                "group_1_n": len(mutation_rates_1),
                "group_2_n": len(mutation_rates_2),
            }
        
        rates_1 = np.array(mutation_rates_1)
        rates_2 = np.array(mutation_rates_2)
        
        if test_type == "independent":
            t_stat, p_value = stats.ttest_ind(rates_1, rates_2)
        else:
            t_stat, p_value = stats.ttest_rel(rates_1, rates_2)
        
        pooled_std = np.sqrt((np.std(rates_1, ddof=1)**2 + np.std(rates_2, ddof=1)**2) / 2)
        cohens_d = (np.mean(rates_1) - np.mean(rates_2)) / pooled_std if pooled_std > 0 else 0
        
        return {
            "test": f"{test_type} t-test",
            "group_1_type": hallucination_type_1,
            "group_1_mean": float(np.mean(rates_1)),
            "group_1_std": float(np.std(rates_1, ddof=1)),
            "group_1_n": len(rates_1),
            "group_2_type": hallucination_type_2,
            "group_2_mean": float(np.mean(rates_2)),
            "group_2_std": float(np.std(rates_2, ddof=1)),
            "group_2_n": len(rates_2),
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significance_level": 0.05,
            "result": "REJECT null hypothesis" if p_value < 0.05 else "FAIL TO REJECT",
            "cohens_d": float(cohens_d),
        }
    
    @staticmethod
    def persistence_duration_analysis(
        persistence_durations: List[int],
        hallucination_types: List[str] = None
    ) -> Dict:
        """Analyze how long hallucinations persist (duration in iterations)"""
        durations = np.array(persistence_durations)
        
        result = {
            "metric": "Persistence Duration (iterations)",
            "sample_size": len(durations),
            "mean_duration": float(np.mean(durations)),
            "median_duration": float(np.median(durations)),
            "std_deviation": float(np.std(durations, ddof=1)) if len(durations) > 1 else 0.0,
            "min_duration": int(np.min(durations)) if len(durations) > 0 else 0,
            "max_duration": int(np.max(durations)) if len(durations) > 0 else 0,
        }
        
        if hallucination_types:
            by_type = {}
            unique_types = set(hallucination_types)
            
            for h_type in unique_types:
                type_durations = [d for d, t in zip(persistence_durations, hallucination_types) if t == h_type]
                if type_durations:
                    by_type[h_type] = {
                        "mean": float(np.mean(type_durations)),
                        "median": float(np.median(type_durations)),
                        "std": float(np.std(type_durations, ddof=1)) if len(type_durations) > 1 else 0.0,
                        "count": len(type_durations),
                    }
            
            result["by_type"] = by_type
        
        return result
    
    @staticmethod
    def generate_statistical_report(h1_result: Dict, h2_result: Dict) -> Dict:
        """Generate comprehensive statistical report"""
        return {
            "title": "Statistical Analysis Report - Hallucination Propagation",
            "hypothesis_tests": {
                "H1_explicit_fix_prompts": h1_result,
                "H2_security_vs_syntax": h2_result,
            },
            "summary": {
                "h1_supported": h1_result.get('result') == "REJECT null hypothesis",
                "h2_supported": h2_result.get('result') == "REJECT null hypothesis",
            }
        }