#!/usr/bin/env python3
"""Main entry point for image analysis functionality."""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analysis import OpenRouterClient, ImageAnalyzer


def _parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze image differences using OpenRouter API with AI models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python src/analyze_images.py \\
      --inputs screenshots/run01 screenshots/run02 \\
      --output analysis_results

  # With difference directory
  python src/analyze_images.py \\
      --inputs screenshots/run01 screenshots/run02 \\
      --diff-dir screenshots/comparison01 \\
      --output analysis_results

  # Dry run (no API costs)
  python src/analyze_images.py \\
      --inputs screenshots/run01 screenshots/run02 \\
      --output analysis_results \\
      --dry-run

  # Custom model and prompt
  python src/analyze_images.py \\
      --api-key your_key_here \\
      --inputs screenshots/run01 screenshots/run02 \\
      --output analysis_results \\
      --model google/gemini-2.0-flash-thinking-exp:free \\
      --prompt "Describe only the color differences between these images"
        """
    )
    
    parser.add_argument("--api-key", type=str, help="OpenRouter API key (can also use OPENROUTER_API_KEY env variable)")
    parser.add_argument("--inputs", nargs=2, type=Path, required=True, metavar=("DIR_A", "DIR_B"), help="Two input directories containing matching image files")
    parser.add_argument("--diff-dir", type=Path, help="Optional directory containing difference images (with _diff suffix)")
    parser.add_argument("--output", type=Path, required=True, help="Output directory for analysis text files")
    parser.add_argument("--model", type=str, default="google/gemini-2.0-flash-thinking-exp:free", help="OpenRouter model to use (default: google/gemini-2.0-flash-thinking-exp:free)")
    parser.add_argument("--prompt", type=str, help="Custom prompt for image analysis (uses default if not provided)")
    parser.add_argument("--rate-limit", type=float, default=1.0, help="Delay between API requests in seconds (default: 1.0)")
    parser.add_argument("--dry-run", action="store_true", help="Save request details without sending to API (no costs incurred)")
    parser.add_argument("--dry-run-dir", type=Path, help="Directory to save dry run requests (default: output_dir/dry_runs)")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="Logging level (default: INFO)")
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = _parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Get API key from args, .env file, or environment
    api_key = args.api_key or os.environ.get("OPENROUTER_API_KEY")
    
    if not api_key and not args.dry_run:
        logging.error("API key not provided. Use --api-key or set OPENROUTER_API_KEY environment variable")
        sys.exit(1)
    
    logging.info("Initializing OpenRouter client")
    logging.info(f"Model: {args.model}")
    
    try:
        # Create client
        client = OpenRouterClient(api_key=api_key or "fake_key_for_dry_run", model=args.model)
        
        # Create analyzer
        analyzer = ImageAnalyzer(
            client=client,
            input_dirs=(args.inputs[0], args.inputs[1]),
            diff_dir=args.diff_dir,
            output_dir=args.output,
            rate_limit_delay=args.rate_limit,
            dry_run=args.dry_run,
            dry_run_dir=args.dry_run_dir
        )
        
        # Run analysis
        logging.info("Starting image analysis")
        results = analyzer.analyze_all(custom_prompt=args.prompt)
        
        # Report results
        successful = sum(1 for r in results.values() if not r.startswith("Error:"))
        failed = len(results) - successful
        
        logging.info(f"Analysis complete: {successful} successful, {failed} failed")
        logging.info(f"Results saved to: {args.output}")
        
        if failed > 0:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logging.info("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Analysis failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
