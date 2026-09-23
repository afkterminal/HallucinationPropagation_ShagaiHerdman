"""
Propagation Visualizer - Generate diagrams and charts for hallucination propagation
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, List
import json
import os

class PropagationVisualizer:
    """Creates visualizations for hallucination propagation analysis"""
    
    def __init__(self, output_dir: str = "./outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.colors = {
            "persist": "#FF6B6B",
            "mutate": "#FFA500",
            "resolve": "#51CF66",
            "masked": "#FFD93D",
            "compound": "#8B0000",
        }
        self.type_colors = {
            "api": "#1f77b4",
            "dependency": "#ff7f0e",
            "logic": "#2ca02c",
            "security": "#d62728",
            "syntax": "#9467bd",
            "type": "#8c564b",
        }
    
    def plot_persistence_by_type(self, persistence_df: pd.DataFrame, save_path: str = None):
        """Bar chart: Persistence rates by hallucination type"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        df_filtered = persistence_df.copy()
        df_filtered = df_filtered.sort_values('persistence_rate', ascending=True)
        
        colors = [self.type_colors.get(t, '#1f77b4') for t in df_filtered['hallucination_type']]
        
        ax.barh(df_filtered['hallucination_type'], df_filtered['persistence_rate'], color=colors)
        ax.set_xlabel('Persistence Rate', fontsize=12, fontweight='bold')
        ax.set_ylabel('Hallucination Type', fontsize=12, fontweight='bold')
        ax.set_title('Hallucination Persistence Rates by Type', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 1)
        
        for i, (idx, row) in enumerate(df_filtered.iterrows()):
            ax.text(row['persistence_rate'] + 0.02, i, f"{row['persistence_rate']:.2%}", va='center')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        return fig, ax
    
    def plot_mutation_by_type(self, mutation_df: pd.DataFrame, save_path: str = None):
        """Bar chart: Mutation rates by hallucination type"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        df_filtered = mutation_df.copy()
        df_filtered = df_filtered.sort_values('mutation_rate', ascending=True)
        
        colors = [self.type_colors.get(t, '#1f77b4') for t in df_filtered['hallucination_type']]
        
        ax.barh(df_filtered['hallucination_type'], df_filtered['mutation_rate'], color=colors)
        ax.set_xlabel('Mutation Rate', fontsize=12, fontweight='bold')
        ax.set_ylabel('Hallucination Type', fontsize=12, fontweight='bold')
        ax.set_title('Mutation Rates Among Persistent Hallucinations', fontsize=14, fontweight='bold')
        ax.set_xlim(0, 1)
        
        for i, (idx, row) in enumerate(df_filtered.iterrows()):
            ax.text(row['mutation_rate'] + 0.02, i, f"{row['mutation_rate']:.2%}", va='center')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        return fig, ax
    
    def plot_persistence_by_severity(self, severity_df: pd.DataFrame, save_path: str = None):
        """Bar chart: Persistence rates grouped by severity"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        severity_order = ['critical', 'high', 'medium', 'low', 'info']
        df_filtered = severity_df.copy()
        
        severity_colors = {
            'critical': '#8B0000',
            'high': '#FF6B6B',
            'medium': '#FFA500',
            'low': '#FFD93D',
            'info': '#CCCCCC'
        }
        colors = [severity_colors.get(s, '#1f77b4') for s in df_filtered['severity']]
        
        ax.bar(range(len(df_filtered)), df_filtered['persistence_rate'], color=colors)
        ax.set_xticks(range(len(df_filtered)))
        ax.set_xticklabels(df_filtered['severity'])
        ax.set_ylabel('Persistence Rate', fontsize=12, fontweight='bold')
        ax.set_xlabel('Severity Level', fontsize=12, fontweight='bold')
        ax.set_title('Hallucination Persistence by Severity', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 1)
        
        for i, (idx, row) in enumerate(df_filtered.iterrows()):
            ax.text(i, row['persistence_rate'] + 0.02, f"{row['persistence_rate']:.2%}", ha='center')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        return fig, ax
    
    def plot_state_transition_matrix(self, transition_df: pd.DataFrame, save_path: str = None):
        """Heatmap: State transition matrix"""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # States with no outgoing transitions give 0/0 rows; show them as 0
        transition_norm = transition_df.div(transition_df.sum(axis=1), axis=0).fillna(0)
        
        im = ax.imshow(transition_norm.values, cmap='YlOrRd', aspect='auto')
        
        ax.set_xticks(np.arange(len(transition_norm.columns)))
        ax.set_yticks(np.arange(len(transition_norm.index)))
        ax.set_xticklabels(transition_norm.columns)
        ax.set_yticklabels(transition_norm.index)
        
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        
        for i in range(len(transition_norm.index)):
            for j in range(len(transition_norm.columns)):
                text = ax.text(j, i, f'{transition_norm.iloc[i, j]:.2f}',
                             ha="center", va="center", color="black", fontsize=10)
        
        ax.set_title('State Transition Matrix', fontsize=14, fontweight='bold')
        ax.set_xlabel('Next State', fontsize=12, fontweight='bold')
        ax.set_ylabel('Current State', fontsize=12, fontweight='bold')
        
        plt.colorbar(im, ax=ax, label='Probability')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        return fig, ax
    
    def create_summary_dashboard(self, summary_stats: Dict, save_path: str = None):
        """Summary dashboard with key statistics"""
        fig = plt.figure(figsize=(14, 8))
        gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3)
        
        fig.suptitle('Hallucination Propagation Analysis Summary', 
                    fontsize=16, fontweight='bold')
        
        # Plot 1: Hallucinations by type
        ax1 = fig.add_subplot(gs[0, 0])
        halluc_by_type = summary_stats.get('hallucinations_by_type', {})
        if halluc_by_type:
            types = list(halluc_by_type.keys())
            counts = list(halluc_by_type.values())
            colors = [self.type_colors.get(t, '#1f77b4') for t in types]
            ax1.pie(counts, labels=types, autopct='%1.1f%%', colors=colors)
            ax1.set_title('Distribution by Type')
        
        # Plot 2: Key metrics
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.axis('off')
        metrics_text = f"""
        KEY STATISTICS
        
        Total Hallucinations: {summary_stats.get('total_hallucinations', 0)}
        Total Tasks: {summary_stats.get('total_tasks', 0)}
        
        Persistence Rate: {summary_stats.get('overall_persistence_rate', 0):.2%}
        Mutation Rate: {summary_stats.get('overall_mutation_rate', 0):.2%}
        """
        ax2.text(0.1, 0.5, metrics_text, fontsize=11, family='monospace',
                verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Placeholders for remaining plots
        ax3 = fig.add_subplot(gs[1, :])
        ax3.axis('off')
        ax3.text(0.5, 0.5, 'Additional Analysis', ha='center', va='center', fontsize=12)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Saved: {save_path}")
        
        return fig