"""
Visualization and analysis of anomaly detection results
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class AnomalyAnalyzer:
    """Analyze and visualize anomaly detection results"""
    
    def __init__(self, df: pd.DataFrame, training_results: dict):
        """Initialize analyzer"""
        self.df = df
        self.predictions = training_results['predictions']
        self.anomaly_scores = training_results['anomaly_scores']
        
    def display_anomalies(self):
        """Display detected anomalies"""
        print(f"\n🚨 ANOMALY DETECTION RESULTS")
        print(f"{'='*70}")
        
        anomaly_mask = self.predictions == 1
        normal_mask = self.predictions == 0
        
        anomalies_df = self.df[anomaly_mask].copy()
        anomalies_df['anomaly_score'] = self.anomaly_scores[anomaly_mask]
        
        if len(anomalies_df) > 0:
            print(f"\n🔴 ANOMALIES DETECTED: {len(anomalies_df)}")
            print(f"{'─'*70}")
            
            for idx, (_, row) in enumerate(anomalies_df.iterrows(), 1):
                print(f"\n{idx}. Chunk: {row['chunk_id']}")
                print(f"   Timestamp: {row['timestamp']}")
                print(f"   Anomaly Score: {row['anomaly_score']:.4f} (lower = more anomalous)")
                print(f"   Metrics:")
                print(f"      • Avg Latency: {row['avg_latency']:.0f}ms")
                print(f"      • Max Latency: {row['max_latency']:.0f}ms")
                print(f"      • CPU Usage: {row['avg_cpu_usage']:.1f}%")
                print(f"      • Memory Usage: {row['avg_memory_usage']:.1f}%")
                print(f"      • Queue Depth: {row['avg_queue_depth']:.0f}")
                print(f"      • Timeout Events: {int(row['timeout_events'])}")
                print(f"   Categories: HEALTH={int(row['health_count'])}, " +
                      f"ANOMALY={int(row['anomaly_count'])}, " +
                      f"SERVICE={int(row['service_count'])}, " +
                      f"SECURITY={int(row['security_count'])}")
        
        print(f"\n🟢 NORMAL SAMPLES: {np.sum(normal_mask)}")
        print(f"{'─'*70}")
        
    def generate_visualizations(self, output_dir: str = "./ml_results"):
        """Generate visualization plots"""
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n📈 Generating visualizations...")
        print(f"{'='*70}")
        
        # 1. Anomaly Score Distribution
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Kubernetes Log Anomaly Detection Analysis', fontsize=16, fontweight='bold')
        
        # Score distribution
        ax = axes[0, 0]
        ax.hist(self.anomaly_scores, bins=20, edgecolor='black', alpha=0.7, color='skyblue')
        ax.axvline(np.mean(self.anomaly_scores), color='red', linestyle='--', label='Mean')
        ax.set_xlabel('Anomaly Score')
        ax.set_ylabel('Frequency')
        ax.set_title('Anomaly Score Distribution')
        ax.legend()
        ax.grid(alpha=0.3)
        
        # 2. Predictions pie chart
        ax = axes[0, 1]
        anomaly_count = np.sum(self.predictions == 1)
        normal_count = np.sum(self.predictions == 0)
        colors = ['#ff6b6b', '#51cf66']
        ax.pie([normal_count, anomaly_count], labels=['Normal', 'Anomaly'], 
               autopct='%1.1f%%', colors=colors, startangle=90)
        ax.set_title('Anomaly Detection Results')
        
        # 3. Latency vs CPU Usage (colored by anomaly)
        ax = axes[1, 0]
        colors_map = ['green' if pred == 0 else 'red' for pred in self.predictions]
        ax.scatter(self.df['avg_latency'], self.df['avg_cpu_usage'], 
                  c=colors_map, s=100, alpha=0.6, edgecolors='black')
        ax.set_xlabel('Average Latency (ms)')
        ax.set_ylabel('Average CPU Usage (%)')
        ax.set_title('Latency vs CPU Usage')
        ax.grid(alpha=0.3)
        
        # 4. Queue Depth vs Memory Usage
        ax = axes[1, 1]
        ax.scatter(self.df['avg_queue_depth'], self.df['avg_memory_usage'], 
                  c=colors_map, s=100, alpha=0.6, edgecolors='black')
        ax.set_xlabel('Average Queue Depth')
        ax.set_ylabel('Average Memory Usage (%)')
        ax.set_title('Queue Depth vs Memory Usage')
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        plot_path = os.path.join(output_dir, 'anomaly_analysis.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {plot_path}")
        plt.close()
        
        # 5. Feature importance-like visualization
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Calculate average feature values for anomalies vs normal
        normal_data = self.df[self.predictions == 0]
        anomaly_data = self.df[self.predictions == 1]
        
        if len(anomaly_data) > 0:
            features_to_plot = ['avg_latency', 'avg_cpu_usage', 'avg_memory_usage', 
                              'avg_queue_depth', 'timeout_events']
            
            normal_means = [normal_data[f].mean() for f in features_to_plot]
            anomaly_means = [anomaly_data[f].mean() for f in features_to_plot]
            
            x = np.arange(len(features_to_plot))
            width = 0.35
            
            ax.bar(x - width/2, normal_means, width, label='Normal', alpha=0.8, color='green')
            ax.bar(x + width/2, anomaly_means, width, label='Anomaly', alpha=0.8, color='red')
            
            ax.set_xlabel('Features')
            ax.set_ylabel('Average Value')
            ax.set_title('Feature Comparison: Normal vs Anomaly')
            ax.set_xticks(x)
            ax.set_xticklabels([f.replace('avg_', '').replace('_', ' ').title() 
                               for f in features_to_plot], rotation=45)
            ax.legend()
            ax.grid(alpha=0.3, axis='y')
        
        plt.tight_layout()
        plot_path = os.path.join(output_dir, 'feature_comparison.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {plot_path}")
        plt.close()
        
        # 6. Timeseries anomaly scores
        fig, ax = plt.subplots(figsize=(14, 6))
        
        x_axis = range(len(self.df))
        colors_scatter = ['red' if pred == 1 else 'green' for pred in self.predictions]
        
        ax.plot(x_axis, self.anomaly_scores, 'b-', alpha=0.5, label='Anomaly Score')
        ax.scatter(x_axis, self.anomaly_scores, c=colors_scatter, s=100, 
                  alpha=0.7, edgecolors='black', label='Samples')
        
        ax.axhline(y=0, color='orange', linestyle='--', linewidth=2, label='Normal Threshold')
        ax.set_xlabel('Sample Index (Chunk Order)')
        ax.set_ylabel('Anomaly Score')
        ax.set_title('Anomaly Scores Over Time (Chunk Sequence)')
        ax.legend()
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        plot_path = os.path.join(output_dir, 'timeseries_anomalies.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        print(f"✅ Saved: {plot_path}")
        plt.close()
        
        print(f"\n✅ All visualizations saved to: {output_dir}/")
