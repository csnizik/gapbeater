import argparse
from src.game import GameManager
from src.config.settings_manager import SettingsManager

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Gaps Solitaire - Interactive card game")
    parser.add_argument("--verbose", action="store_true", 
                       help="Enable verbose diagnostic logging for all components")
    parser.add_argument("--quiet", action="store_true",
                       help="Disable all diagnostic logging (default)")
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add analyze-runs subcommand
    analyze_parser = subparsers.add_parser('analyze-runs', 
                                         help='Analyze diagnostic logs for performance metrics')
    analyze_parser.add_argument('game_id', 
                              help='Game ID to analyze (subdirectory name in debug/)')
    analyze_parser.add_argument('--debug-path', default='debug',
                              help='Path to debug directory (default: debug)')
    analyze_parser.add_argument('--output-format', choices=['text', 'json'], default='text',
                              help='Output format for analysis report')
    
    args = parser.parse_args()
    
    # Handle analyze-runs command
    if args.command == 'analyze-runs':
        from pathlib import Path
        from analysis.correlation_engine import CorrelationEngine
        import json
        
        debug_path = Path(args.debug_path)
        engine = CorrelationEngine()
        
        try:
            print(f"Analyzing runs for game ID: {args.game_id}")
            print(f"Debug path: {debug_path.absolute()}")
            
            report = engine.analyze_single_run(debug_path, args.game_id)
            
            if args.output_format == 'json':
                # Convert report to JSON
                report_dict = {
                    'game_id': report.game_id,
                    'run_count': report.run_count,
                    'outcome_summary': report.outcome_summary,
                    'diagnostic_summary': report.diagnostic_summary,
                    'correlations': [
                        {
                            'metric_name': c.metric_name,
                            'correlation_coefficient': c.correlation_coefficient,
                            'significance': c.significance
                        } for c in report.correlations
                    ],
                    'comparisons': [
                        {
                            'run1_id': comp.run1_id,
                            'run2_id': comp.run2_id,
                            'outcome_differences': comp.outcome_differences,
                            'significant_changes': comp.significant_changes
                        } for comp in report.comparisons
                    ],
                    'recommendations': report.recommendations
                }
                print(json.dumps(report_dict, indent=2))
            else:
                # Text format output
                print("\n" + "="*60)
                print(f"ANALYSIS REPORT FOR GAME ID: {report.game_id}")
                print("="*60)
                print(f"Number of runs analyzed: {report.run_count}")
                
                if report.outcome_summary:
                    print("\nOUTCOME METRICS:")
                    print("-" * 20)
                    for metric, value in report.outcome_summary.items():
                        if isinstance(value, float):
                            print(f"  {metric}: {value:.3f}")
                        else:
                            print(f"  {metric}: {value}")
                
                if report.diagnostic_summary:
                    print("\nDIAGNOSTIC SUMMARY:")
                    print("-" * 20)
                    for category, metrics in report.diagnostic_summary.items():
                        print(f"  {category.upper()}:")
                        for metric_name, metric_data in metrics.items():
                            if isinstance(metric_data, dict) and 'mean' in metric_data:
                                print(f"    {metric_name}: mean={metric_data['mean']:.4f}, count={metric_data['count']}")
                            elif isinstance(metric_data, dict) and 'value' in metric_data:
                                print(f"    {metric_name}: {metric_data['value']}")
                
                if report.correlations:
                    print("\nCORRELATIONS:")
                    print("-" * 20)
                    for corr in report.correlations:
                        print(f"  {corr.metric_name}: {corr.correlation_coefficient:.3f} ({corr.significance})")
                
                if report.comparisons:
                    print("\nRUN COMPARISONS:")
                    print("-" * 20)
                    for comp in report.comparisons:
                        print(f"  {comp.run1_id} vs {comp.run2_id}:")
                        if comp.significant_changes:
                            for change in comp.significant_changes:
                                print(f"    - {change}")
                        else:
                            print("    - No significant differences")
                
                if report.recommendations:
                    print("\nRECOMMENDATIONS:")
                    print("-" * 20)
                    for i, rec in enumerate(report.recommendations, 1):
                        print(f"  {i}. {rec}")
                
                print("\n" + "="*60)
            
        except Exception as e:
            print(f"Error during analysis: {e}")
            return 1
        
        return 0
    
    # Configure global logging based on command line arguments
    settings_manager = SettingsManager()
    if args.verbose:
        settings_manager.set_setting("logging_enabled", True)
        settings_manager.configure_global_logging(create_timestamped_run=True)
        print("Verbose diagnostic logging enabled with timestamped debug directory")
    elif args.quiet:
        settings_manager.set_setting("logging_enabled", False)
        settings_manager.configure_global_logging()
        print("Diagnostic logging disabled")
    
    print("Welcome to Gaps Solitaire")
    choice = input("Create a [N]ew game, [O]pen a saved game, or view [S]ettings? ").strip().lower()

    game_manager = GameManager()

    if choice == 'o':
        game_manager.open_saved_game()
    elif choice == 's':
        game_manager.display_settings()
    else:
        game_manager.create_new_game()

if __name__ == "__main__":
    main()
