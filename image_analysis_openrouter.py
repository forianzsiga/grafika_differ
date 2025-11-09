"""Image difference analysis using OpenRouter API with Gemini 2.5 Pro.

This script analyzes image pairs and their differences using a multimodal LLM
to provide detailed textual descriptions for further analysis by non-multimodal models.

The script:
1. Reads image pairs from two comparison directories
2. Optionally includes difference images from a comparison output directory
3. Sends images to Gemini 2.5 Pro via OpenRouter API
4. Generates detailed textual descriptions of differences
5. Saves analysis results as text files for each image pair

Environment Variables:
    OPENROUTER_API_KEY: Your OpenRouter API key (optional if provided via CLI)

Example usage:
    # Using environment variable for API key
    export OPENROUTER_API_KEY=your_key_here
    python image_analysis_openrouter.py \\
        --inputs screenshots/run01 screenshots/run02 \\
        --diff-dir screenshots/comparison01 \\
        --output analysis_results

    # Providing API key via command line
    python image_analysis_openrouter.py \\
        --api-key your_key_here \\
        --inputs screenshots/run01 screenshots/run02 \\
        --output analysis_results

Required packages:
    - requests
    - pillow

Install with: pip install requests pillow
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import requests
    from PIL import Image
except ImportError as exc:
    raise SystemExit(
        "Missing required dependencies. Install with 'pip install requests pillow'. Original error: %s" % exc
    )


class OpenRouterClient:
    """Client for interacting with OpenRouter API."""
    
    def __init__(self, api_key: str, model: str = "google/gemini-2.0-flash-thinking-exp:free"):
        """Initialize OpenRouter client.
        
        Args:
            api_key: OpenRouter API key
            model: Model to use (default: google/gemini-2.0-flash-thinking-exp:free)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/grafika_differ",
            "X-Title": "Grafika Differ Image Analysis"
        }
    
    def encode_image_to_base64(self, image_path: Path) -> str:
        """Encode an image file to base64 data URI.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64-encoded data URI string
        """
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Detect image format from file extension
        ext = image_path.suffix.lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(ext, 'image/png')
        
        return f"data:{mime_type};base64,{base64_image}"
    
    def analyze_images(
        self,
        image_a_path: Path,
        image_b_path: Path,
        diff_path: Optional[Path] = None,
        prompt: Optional[str] = None
    ) -> str:
        """Analyze image pair with optional difference image.
        
        Args:
            image_a_path: Path to first image
            image_b_path: Path to second image
            diff_path: Optional path to difference image
            prompt: Optional custom prompt (uses default if not provided)
            
        Returns:
            Analysis text from the model
        """
        if prompt is None:
            prompt = self._get_default_prompt(has_diff=diff_path is not None)
        
        # Prepare message content
        content = [
            {
                "type": "text",
                "text": prompt
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": self.encode_image_to_base64(image_a_path)
                }
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": self.encode_image_to_base64(image_b_path)
                }
            }
        ]
        
        # Add difference image if provided
        if diff_path and diff_path.exists():
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": self.encode_image_to_base64(diff_path)
                }
            })
        
        # Prepare request payload
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ]
        }
        
        # Make API request
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract response text
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                logging.error(f"Unexpected response format: {result}")
                return "Error: Unexpected response format from API"
                
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            return f"Error: API request failed - {str(e)}"
    
    def _get_default_prompt(self, has_diff: bool = False) -> str:
        """Get default analysis prompt.
        
        Args:
            has_diff: Whether a difference image is included
            
        Returns:
            Default prompt string
        """
        base_prompt = """You are analyzing two images from a graphics application test run. These images represent consecutive frames or states of a graphical application.

Your task is to provide a detailed textual description of the differences between these two images. This description will be used by non-multimodal language models for further analysis, so it must be thorough and precise.

Please analyze and describe:
1. Visual differences: What has changed between the two images? Include details about:
   - Position changes of objects or elements
   - Color or appearance changes
   - New elements that appeared or elements that disappeared
   - Size or scale changes
   - Rotation or transformation changes

2. Semantic meaning: What do these changes likely represent in the context of a graphics application?
   - Animation or transformation in progress
   - User interaction effects
   - Rendering differences
   - State changes

3. Quantitative observations where possible:
   - Approximate position coordinates or movements (e.g., "moved 50 pixels to the right")
   - Color values or changes if notable
   - Size measurements if relevant

"""
        
        if has_diff:
            base_prompt += """4. Difference image analysis: A third image showing the pixel-wise difference is provided. Use this to:
   - Identify the exact regions that changed
   - Quantify the magnitude of changes
   - Distinguish between subtle and significant differences

"""
        
        base_prompt += """IMPORTANT: Provide your analysis in plain text without any formatting markup (no markdown, no asterisks, no special characters for formatting). Write in clear, descriptive paragraphs that can be easily parsed and analyzed by text-only models. Be thorough but concise, focusing on observable facts rather than speculation."""
        
        return base_prompt


class ImageAnalyzer:
    """Orchestrates image analysis workflow."""
    
    def __init__(
        self,
        client: OpenRouterClient,
        input_dirs: Tuple[Path, Path],
        diff_dir: Optional[Path],
        output_dir: Path,
        rate_limit_delay: float = 1.0
    ):
        """Initialize image analyzer.
        
        Args:
            client: OpenRouter client instance
            input_dirs: Tuple of two input directories containing image pairs
            diff_dir: Optional directory containing difference images
            output_dir: Directory to save analysis results
            rate_limit_delay: Delay between API requests in seconds
        """
        self.client = client
        self.dir_a, self.dir_b = input_dirs
        self.diff_dir = diff_dir
        self.output_dir = output_dir
        self.rate_limit_delay = rate_limit_delay
        
        # Validate directories
        for directory in [self.dir_a, self.dir_b]:
            if not directory.exists() or not directory.is_dir():
                raise FileNotFoundError(f"Input directory not found: {directory}")
        
        if self.diff_dir and not self.diff_dir.exists():
            logging.warning(f"Diff directory not found: {self.diff_dir}")
            self.diff_dir = None
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def find_image_pairs(self) -> List[Tuple[str, Path, Path, Optional[Path]]]:
        """Find matching image pairs across input directories.
        
        Returns:
            List of tuples (name, path_a, path_b, diff_path)
        """
        files_a = {p.name: p for p in self.dir_a.glob("*.png")}
        files_b = {p.name: p for p in self.dir_b.glob("*.png")}
        files_diff = {}
        
        if self.diff_dir:
            # Diff files have _diff suffix
            for p in self.diff_dir.glob("*_diff.png"):
                # Remove _diff suffix to match original names
                original_name = p.name.replace("_diff.png", ".png")
                files_diff[original_name] = p
        
        # Find matching names
        shared_names = sorted(files_a.keys() & files_b.keys())
        
        if not shared_names:
            logging.warning("No matching image pairs found")
            return []
        
        # Build result list
        pairs = []
        for name in shared_names:
            diff_path = files_diff.get(name)
            pairs.append((name, files_a[name], files_b[name], diff_path))
        
        logging.info(f"Found {len(pairs)} image pairs to analyze")
        return pairs
    
    def analyze_all(self, custom_prompt: Optional[str] = None) -> Dict[str, str]:
        """Analyze all image pairs.
        
        Args:
            custom_prompt: Optional custom prompt to use for all analyses
            
        Returns:
            Dictionary mapping image names to analysis results
        """
        pairs = self.find_image_pairs()
        
        if not pairs:
            logging.error("No image pairs to analyze")
            return {}
        
        results = {}
        
        for idx, (name, path_a, path_b, diff_path) in enumerate(pairs, 1):
            logging.info(f"Analyzing {idx}/{len(pairs)}: {name}")
            
            try:
                # Analyze the image pair
                analysis = self.client.analyze_images(
                    path_a,
                    path_b,
                    diff_path,
                    prompt=custom_prompt
                )
                
                # Save result
                output_name = Path(name).stem + "_analysis.txt"
                output_path = self.output_dir / output_name
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    # Write metadata header
                    f.write(f"Image Pair Analysis\n")
                    f.write(f"=" * 80 + "\n\n")
                    f.write(f"Image A: {path_a}\n")
                    f.write(f"Image B: {path_b}\n")
                    if diff_path:
                        f.write(f"Diff Image: {diff_path}\n")
                    f.write(f"\n" + "=" * 80 + "\n\n")
                    f.write("ANALYSIS:\n\n")
                    f.write(analysis)
                    f.write("\n")
                
                logging.info(f"Saved analysis to {output_path}")
                results[name] = analysis
                
                # Rate limiting
                if idx < len(pairs):
                    time.sleep(self.rate_limit_delay)
                    
            except Exception as e:
                logging.error(f"Failed to analyze {name}: {e}")
                results[name] = f"Error: {str(e)}"
        
        # Generate summary
        self._generate_summary(results)
        
        return results
    
    def _generate_summary(self, results: Dict[str, str]) -> None:
        """Generate summary file of all analyses.
        
        Args:
            results: Dictionary of analysis results
        """
        summary_path = self.output_dir / "_summary.txt"
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("IMAGE ANALYSIS SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Total image pairs analyzed: {len(results)}\n")
            f.write(f"Input directories:\n")
            f.write(f"  - A: {self.dir_a}\n")
            f.write(f"  - B: {self.dir_b}\n")
            if self.diff_dir:
                f.write(f"  - Diff: {self.diff_dir}\n")
            f.write(f"Output directory: {self.output_dir}\n")
            f.write(f"\n" + "=" * 80 + "\n\n")
            
            # List all analyzed files
            f.write("ANALYZED FILES:\n\n")
            for idx, name in enumerate(sorted(results.keys()), 1):
                status = "Success" if not results[name].startswith("Error:") else "Failed"
                f.write(f"{idx:3d}. {name:<50s} [{status}]\n")
            
            f.write(f"\n" + "=" * 80 + "\n")
            f.write("\nIndividual analysis files saved as: *_analysis.txt\n")
        
        logging.info(f"Summary saved to {summary_path}")


def _parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze image differences using OpenRouter API with Gemini 2.5 Pro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variable for API key
  export OPENROUTER_API_KEY=your_key_here
  python image_analysis_openrouter.py \\
      --inputs screenshots/run01 screenshots/run02 \\
      --output analysis_results

  # With difference images
  python image_analysis_openrouter.py \\
      --api-key your_key_here \\
      --inputs screenshots/run01 screenshots/run02 \\
      --diff-dir screenshots/comparison01 \\
      --output analysis_results

  # Custom model and prompt
  python image_analysis_openrouter.py \\
      --api-key your_key_here \\
      --inputs screenshots/run01 screenshots/run02 \\
      --output analysis_results \\
      --model google/gemini-2.0-flash-thinking-exp:free \\
      --prompt "Describe only the color differences between these images"
        """
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenRouter API key (can also use OPENROUTER_API_KEY env variable)"
    )
    
    parser.add_argument(
        "--inputs",
        nargs=2,
        type=Path,
        required=True,
        metavar=("DIR_A", "DIR_B"),
        help="Two input directories containing matching image files"
    )
    
    parser.add_argument(
        "--diff-dir",
        type=Path,
        help="Optional directory containing difference images (with _diff suffix)"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory for analysis text files"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        default="google/gemini-2.0-flash-thinking-exp:free",
        help="OpenRouter model to use (default: google/gemini-2.0-flash-thinking-exp:free)"
    )
    
    parser.add_argument(
        "--prompt",
        type=str,
        help="Custom prompt for image analysis (uses default if not provided)"
    )
    
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Delay between API requests in seconds (default: 1.0)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = _parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Get API key from args or environment
    api_key = args.api_key or os.environ.get("OPENROUTER_API_KEY")
    
    if not api_key:
        logging.error("API key not provided. Use --api-key or set OPENROUTER_API_KEY environment variable")
        sys.exit(1)
    
    logging.info("Initializing OpenRouter client")
    logging.info(f"Model: {args.model}")
    
    try:
        # Create client
        client = OpenRouterClient(api_key=api_key, model=args.model)
        
        # Create analyzer
        analyzer = ImageAnalyzer(
            client=client,
            input_dirs=(args.inputs[0], args.inputs[1]),
            diff_dir=args.diff_dir,
            output_dir=args.output,
            rate_limit_delay=args.rate_limit
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
