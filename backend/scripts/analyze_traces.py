#!/usr/bin/env python3
"""
CLI script to analyze traces and generate insights.
Usage: python -m scripts.analyze_traces [--output OUTPUT] [--csv] [--report]
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from observability import TraceAnalyzer


def main():
    parser = argparse.ArgumentParser(description="Analyze agent traces and generate insights")
    parser.add_argument(
        "--traces-dir",
        type=str,
        help="Directory containing trace JSON files (default: backend/traces/)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for JSON insights (default: insights.json)",
        default="insights.json",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Also export CSV files for dashboard integration",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print human-readable report to console",
    )
    
    args = parser.parse_args()
    
    # Initialize analyzer
    traces_dir = Path(args.traces_dir) if args.traces_dir else None
    analyzer = TraceAnalyzer(traces_dir)
    
    print("🔍 Analyzing traces...")
    insights = analyzer.analyze_all_traces()
    
    # Save JSON
    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(insights, f, indent=2, default=str)
    print(f"✅ Insights saved to {output_path}")
    
    # Export CSV if requested
    if args.csv:
        csv_output = output_path.parent / output_path.stem
        analyzer.export_to_csv(insights, csv_output)
    
    # Print report if requested
    if args.report:
        print("\n" + "=" * 80)
        print("BEHAVIORAL INSIGHTS REPORT")
        print("=" * 80 + "\n")
        report = analyzer.generate_report(insights)
        print(report)
    
    # Print summary
    summary = insights.get("summary", {})
    print(f"\n📊 Summary:")
    print(f"   Total Traces: {summary.get('total_traces', 0)}")
    print(f"   Overall Success Rate: {summary.get('overall_success_rate', 0):.1%}")
    print(f"   Shortcut Rate: {summary.get('shortcut_rate', 0):.1%}")
    print(f"   Total Errors: {summary.get('total_errors', 0)}")


if __name__ == "__main__":
    main()

