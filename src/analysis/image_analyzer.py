"""Image analysis using OpenRouter API with AI models.

This module provides functionality to analyze image differences using
multimodal AI models via the OpenRouter API.
"""

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
    raise ImportError(
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
        prompt: Optional[str] = None,
        dry_run_output_dir: Optional[Path] = None
    ) -> str:
        """Analyze image pair with optional difference image.
        
        Args:
            image_a_path: Path to first image
            image_b_path: Path to second image
            diff_path: Optional path to difference image
            prompt: Optional custom prompt (uses default if not provided)
            dry_run_output_dir: Optional directory to save request details without sending
            
        Returns:
            Analysis text from the model, or "Dry run completed" message
        """
        if prompt is None:
            prompt = self._get_default_prompt(has_diff=diff_path is not None)
        
        if dry_run_output_dir and dry_run_output_dir.exists():
            return self._save_dry_run_request(
                image_a_path, image_b_path, diff_path, prompt, dry_run_output_dir
            )

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
    
    def _save_dry_run_request(
        self,
        image_a_path: Path,
        image_b_path: Path,
        diff_path: Optional[Path],
        prompt: str,
        output_dir: Path
    ) -> str:
        """Save dry run request details to files without sending to API.
        
        Args:
            image_a_path: Path to first image
            image_b_path: Path to second image
            diff_path: Optional path to difference image
            prompt: The prompt text
            output_dir: Directory to save request details
            
        Returns:
            Success message
        """
        # Create readable request content
        request_content = []
        request_content.append("DRY RUN REQUEST - API CALL NOT MADE")
        request_content.append("=" * 80)
        request_content.append(f"Model: {self.model}")
        request_content.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        request_content.append("")
        
        # Add prompt
        request_content.append("PROMPT:")
        request_content.append("-" * 40)
        request_content.append(prompt)
        request_content.append("")
        
        # Add image references (not base64 data)
        request_content.append("IMAGE REFERENCES:")
        request_content.append("-" * 40)
        request_content.append(f"Image A: {image_a_path.absolute()}")
        request_content.append(f"Image B: {image_b_path.absolute()}")
        if diff_path:
            request_content.append(f"Difference Image: {diff_path.absolute()}")
        request_content.append("")
        
        # Generate filename
        timestamp = int(time.time())
        stem_a = image_a_path.stem
        
        # Save request details
        request_filename = f"dry_run_request_{stem_a}_{timestamp}.txt"
        request_path = output_dir / request_filename
        with open(request_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(request_content))
        
        # Create mock JSON response
        mock_response = self._create_mock_response(image_a_path, image_b_path, diff_path, prompt)
        
        # Save mock response
        response_filename = f"mock_response_{stem_a}_{timestamp}.json"
        response_path = output_dir / response_filename
        with open(response_path, 'w', encoding='utf-8') as f:
            json.dump(mock_response, f, indent=2)
        
        logging.info(f"Dry run request saved to {request_path}")
        logging.info(f"Mock response saved to {response_path}")
        return f"Dry run completed - request: {request_path}, response: {response_path}"
    
    def _create_mock_response(
        self,
        image_a_path: Path,
        image_b_path: Path,
        diff_path: Optional[Path],
        prompt: str
    ) -> dict:
        """Create a mock API response that mimics OpenRouter's response format."""
        # Generate a mock analysis text based on image names and prompt
        stem_a = image_a_path.stem
        stem_b = image_b_path.stem
        
        mock_analysis = f"""Based on the analysis of the two images, here are the key differences identified:

**Visual Differences:**
The images show different visual states, with variations in color, position, or appearance of graphical elements. The first image shows the application state at {stem_a} while the second image captures the state at {stem_b}.

**Quantitative Observations:**
- Image files analyzed: {image_a_path.absolute()} vs {image_b_path.absolute()}
- File sizes: {image_a_path.stat().st_size} bytes vs {image_b_path.stat().st_size} bytes
"""
        
        if diff_path:
            mock_analysis += f"- Difference image provided: {diff_path.absolute()}\n"
        
        mock_analysis += f"""
**Analysis Method:**
This analysis was generated in dry run mode to demonstrate the request structure and mock response format without incurring API costs. The actual analysis would be performed by the OpenRouter API using the {self.model} model.

**Data Sources:**
- Image A: {image_a_path.absolute()}
- Image B: {image_b_path.absolute()}
- Difference Image: {diff_path.absolute() if diff_path else "Not provided"}
"""
        
        mock_analysis += f"""
**Technical Details:**
- Model used: {self.model}
- Prompt type: {'Custom' if prompt != self._get_default_prompt(diff_path is not None) else 'Default'}
- Analysis timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
- Processing mode: DRY RUN (no actual API call made)

**Note:** This is a mock response generated for testing and development purposes. The actual OpenRouter API would provide a real multimodal analysis of the image differences."""
        
        # Create mock OpenRouter API response
        mock_response = {
            "id": f"mock-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": mock_analysis
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": len(mock_analysis.split()),
                "total_tokens": len(mock_analysis.split())
            },
            "dry_run": {
                "enabled": True,
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
                "image_a_path": str(image_a_path.absolute()),
                "image_b_path": str(image_b_path.absolute()),
                "diff_path": str(diff_path.absolute()) if diff_path else None,
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                "request_saved": True,
                "note": "This is a mock response. No actual API call was made to OpenRouter."
            }
        }
        
        return mock_response
    
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
        rate_limit_delay: float = 1.0,
        dry_run: bool = False,
        dry_run_dir: Optional[Path] = None
    ):
        """Initialize image analyzer.
        
        Args:
            client: OpenRouter client instance
            input_dirs: Tuple of two input directories containing image pairs
            diff_dir: Optional directory containing difference images
            output_dir: Directory to save analysis results
            rate_limit_delay: Delay between API requests in seconds
            dry_run: If True, save request details without sending to API
            dry_run_dir: Directory to save dry run requests (default: output_dir/dry_runs)
        """
        self.client = client
        self.dir_a, self.dir_b = input_dirs
        self.diff_dir = diff_dir
        self.output_dir = output_dir
        self.rate_limit_delay = rate_limit_delay
        self.dry_run = dry_run
        self.dry_run_dir = dry_run_dir or (output_dir / "dry_runs")
        
        # Validate directories
        for directory in [self.dir_a, self.dir_b]:
            if not directory.exists() or not directory.is_dir():
                raise FileNotFoundError(f"Input directory not found: {directory}")
        
        if self.diff_dir and not self.diff_dir.exists():
            logging.warning(f"Diff directory not found: {self.diff_dir}")
            self.diff_dir = None
        
        # Create output and dry run directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.dry_run:
            self.dry_run_dir.mkdir(parents=True, exist_ok=True)
    
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
                    prompt=custom_prompt,
                    dry_run_output_dir=self.dry_run_dir if self.dry_run else None
                )
                
                # Save result
                output_name = Path(name).stem + ("_analysis_dry_run.txt" if self.dry_run else "_analysis.txt")
                output_path = self.output_dir / output_name
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    # Write metadata header
                    f.write(f"Image Pair Analysis{' - DRY RUN' if self.dry_run else ''}\n")
                    f.write(f"=" * 80 + "\n\n")
                    f.write(f"Image A: {path_a}\n")
                    f.write(f"Image B: {path_b}\n")
                    if diff_path:
                        f.write(f"Diff Image: {diff_path}\n")
                    if self.dry_run:
                        f.write(f"Dry Run Output: {self.dry_run_dir}\n")
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
        """Generate summary file of all analyses."""
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
            if self.dry_run:
                f.write(f"Dry run mode: enabled\n")
                f.write(f"Dry run directory: {self.dry_run_dir}\n")
                f.write(f"Mock JSON responses: {self.dry_run_dir}/*.json\n")
            f.write(f"\n" + "=" * 80 + "\n\n")
            
            # List all analyzed files
            f.write("ANALYZED FILES:\n\n")
            for idx, name in enumerate(sorted(results.keys()), 1):
                status = "Success" if not results[name].startswith("Error:") else "Failed"
                f.write(f"{idx:3d}. {name:<50s} [{status}]\n")
            
            f.write(f"\n" + "=" * 80 + "\n")
            if self.dry_run:
                f.write("\nDry run also saves mock JSON responses in the same directory.\n")
            f.write("\nIndividual analysis files saved as: *_analysis.txt\n")
        
        logging.info(f"Summary saved to {summary_path}")
