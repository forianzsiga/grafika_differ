# Image Analysis with OpenRouter - Examples and Documentation

## Overview

This tool uses OpenRouter's API to send image pairs to Gemini 2.5 Pro for detailed visual analysis. The goal is to generate comprehensive textual descriptions of differences that can be analyzed by non-multimodal LLMs.

## Task Summary

The image analysis workflow:

1. **Input**: Takes two directories containing matching screenshot pairs from different test runs
2. **Optional Input**: Can include a third directory with pixel-wise difference images
3. **Processing**: Sends each image pair (and optional diff) to Gemini 2.5 Pro via OpenRouter API
4. **Output**: Generates detailed plain-text descriptions for each pair, saved as individual `.txt` files
5. **Summary**: Creates a master summary file listing all analyzed pairs

## Key Features

- **Automatic Pair Matching**: Finds matching image files across directories by filename
- **Base64 Encoding**: Converts images to base64 data URIs for API transmission
- **Smart Prompting**: Default prompt designed to elicit detailed, parseable descriptions
- **Rate Limiting**: Configurable delay between API calls to avoid rate limits
- **Error Handling**: Robust error handling with detailed logging
- **Plain Text Output**: No markdown formatting - pure text for easy parsing by text-only models

## Setup Instructions

### 1. Get OpenRouter API Key

1. Visit https://openrouter.ai/
2. Create an account or sign in
3. Navigate to "Keys" section
4. Generate a new API key
5. Copy the key

### 2. Set Environment Variable

**Linux/macOS:**
```bash
export OPENROUTER_API_KEY='your_api_key_here'

# To make it permanent, add to ~/.bashrc or ~/.zshrc:
echo 'export OPENROUTER_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
$env:OPENROUTER_API_KEY = "your_api_key_here"

# To make it permanent:
[Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "your_api_key_here", "User")
```

### 3. Install Dependencies

```bash
pip install requests pillow
# or use the requirements.txt
pip install -r requirements.txt
```

## Usage Examples

### Example 1: Basic Analysis

Analyze two screenshot directories without difference images:

```bash
python image_analysis_openrouter.py \
    --inputs screenshots/run01 screenshots/run02 \
    --output analysis_results
```

### Example 2: Complete Workflow with Differences

```bash
# Step 1: Generate difference images
python automation_framework.py \
    --mode comparison \
    --inputs screenshots/run01 screenshots/run02 \
    --output screenshots/comparison01

# Step 2: Analyze with AI
python image_analysis_openrouter.py \
    --inputs screenshots/run01 screenshots/run02 \
    --diff-dir screenshots/comparison01 \
    --output analysis_results
```

### Example 3: Using the Automated Script

The `analyze_differences.sh` script automates the entire process:

```bash
export OPENROUTER_API_KEY='your_api_key_here'

./analyze_differences.sh \
    --dir-a screenshots/run01 \
    --dir-b screenshots/run02 \
    --diff-dir screenshots/comparison01 \
    --output analysis_results
```

### Example 4: Custom Prompt for Specific Analysis

Focus on specific aspects with a custom prompt:

```bash
python image_analysis_openrouter.py \
    --inputs screenshots/run01 screenshots/run02 \
    --output color_analysis \
    --prompt "Analyze only the color differences between these images. 
             Provide exact RGB values if possible and describe any color 
             shifts or changes in saturation, brightness, or hue. 
             Use plain text without formatting."
```

### Example 5: Different Model

Use a different OpenRouter model:

```bash
python image_analysis_openrouter.py \
    --inputs screenshots/run01 screenshots/run02 \
    --output analysis_results \
    --model google/gemini-2.0-flash-thinking-exp:free
```

## Output Format

### Individual Analysis Files

Each image pair generates a file like `000_0000_after_launch_analysis.txt`:

```
Image Pair Analysis
================================================================================

Image A: screenshots/run01/000_0000_after_launch.png
Image B: screenshots/run02/000_0000_after_launch.png
Diff Image: screenshots/comparison01/000_0000_after_launch_diff.png

================================================================================

ANALYSIS:

The two images show a graphics rendering of a green triangle on a dark background. 
In the first image, the triangle is positioned slightly to the left with its apex 
pointing upward at approximately 45 degrees...

[Detailed analysis continues...]
```

### Summary File

The `_summary.txt` file provides an overview:

```
IMAGE ANALYSIS SUMMARY
================================================================================

Total image pairs analyzed: 15
Input directories:
  - A: screenshots/run01
  - B: screenshots/run02
  - Diff: screenshots/comparison01
Output directory: analysis_results

================================================================================

ANALYZED FILES:

  1. 000_0000_after_launch.png                      [Success]
  2. 001_000_0370_000_mouse_press_left.png          [Success]
  3. 002_000_0370_001_mouse_release_left.png        [Success]
...
```

## Default Prompt Behavior

The default prompt asks Gemini to provide:

1. **Visual Differences**:
   - Position changes
   - Color/appearance changes
   - New/disappeared elements
   - Size/scale changes
   - Rotation/transformation changes

2. **Semantic Meaning**:
   - What the changes represent
   - Animation or transformation context
   - User interaction effects
   - Rendering differences
   - State changes

3. **Quantitative Observations**:
   - Approximate positions and movements
   - Color values
   - Size measurements

4. **Difference Image Analysis** (if provided):
   - Exact regions that changed
   - Magnitude of changes
   - Subtle vs significant differences

The prompt explicitly requests **plain text output** without markdown or special formatting.

## Rate Limiting

OpenRouter has rate limits that vary by model. The script includes:

- Default 1-second delay between requests
- Configurable via `--rate-limit` parameter
- Automatic error handling for rate limit responses

Recommended delays:
- Free tier: 2-3 seconds
- Paid tier: 0.5-1 second

## Troubleshooting

### API Key Issues

**Problem**: "API key not provided" error

**Solution**: 
```bash
# Verify environment variable
echo $OPENROUTER_API_KEY

# Set it if empty
export OPENROUTER_API_KEY='your_key_here'

# Or provide via command line
python image_analysis_openrouter.py --api-key your_key_here ...
```

### Rate Limit Errors

**Problem**: "Rate limit exceeded" errors

**Solution**:
```bash
# Increase delay between requests
python image_analysis_openrouter.py \
    --inputs screenshots/run01 screenshots/run02 \
    --output analysis_results \
    --rate-limit 3.0
```

### No Matching Files

**Problem**: "No matching PNG filenames across the first two inputs"

**Solution**: Ensure both directories contain PNG files with identical names:
```bash
# Check files in both directories
ls screenshots/run01/*.png | wc -l
ls screenshots/run02/*.png | wc -l

# Find common files
comm -12 <(ls screenshots/run01/*.png | xargs -n1 basename | sort) \
         <(ls screenshots/run02/*.png | xargs -n1 basename | sort)
```

### API Request Failures

**Problem**: "API request failed" errors

**Solution**:
- Check internet connection
- Verify API key is valid
- Check OpenRouter service status
- Review error message in logs with `--log-level DEBUG`

## Cost Considerations

OpenRouter charges vary by model:

- **google/gemini-2.0-flash-thinking-exp:free**: Free tier with rate limits
- Check current pricing at: https://openrouter.ai/models

Estimate costs:
- Each image pair = 1 API call
- Image size affects token usage
- Typical cost per 1000 screenshots: varies by model

## Advanced Usage

### Batch Processing Multiple Runs

```bash
#!/bin/bash
export OPENROUTER_API_KEY='your_key_here'

for run in run01 run02 run03; do
    echo "Analyzing $run vs baseline..."
    python image_analysis_openrouter.py \
        --inputs screenshots/baseline screenshots/$run \
        --output analysis_$run \
        --rate-limit 2.0
done
```

### Custom Analysis Pipeline

```python
from image_analysis_openrouter import OpenRouterClient, ImageAnalyzer
from pathlib import Path

# Create custom client
client = OpenRouterClient(
    api_key="your_key_here",
    model="google/gemini-2.0-flash-thinking-exp:free"
)

# Custom prompt
custom_prompt = """
Focus only on geometric transformations in these images.
Describe rotation angles, scaling factors, and translation vectors.
Provide numerical values where possible.
Use plain text format.
"""

# Run analysis
analyzer = ImageAnalyzer(
    client=client,
    input_dirs=(Path("screenshots/run01"), Path("screenshots/run02")),
    diff_dir=None,
    output_dir=Path("geometric_analysis"),
    rate_limit_delay=1.5
)

results = analyzer.analyze_all(custom_prompt=custom_prompt)
```

## Integration with Further Analysis

The plain-text output is designed for processing by non-multimodal LLMs:

```bash
# Concatenate all analyses
cat analysis_results/*_analysis.txt > all_analyses.txt

# Use with another LLM for summarization
cat all_analyses.txt | llm "Summarize the main rendering issues found"

# Or use programmatically
import openai
with open('all_analyses.txt', 'r') as f:
    analyses = f.read()
    
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are analyzing visual test results."},
        {"role": "user", "content": f"Summarize these visual differences:\n\n{analyses}"}
    ]
)
```

## Best Practices

1. **Image Quality**: Use high-quality PNG screenshots for best results
2. **Consistent Naming**: Ensure matching filenames across directories
3. **Rate Limiting**: Start with conservative rate limits and adjust
4. **Prompt Engineering**: Customize prompts for your specific analysis needs
5. **Error Handling**: Check logs and handle failed analyses
6. **Cost Management**: Monitor API usage for paid models
7. **Batch Processing**: Process large sets overnight with appropriate delays

## Future Enhancements

Potential improvements to consider:

- Support for other image formats (JPG, WebP)
- Parallel processing with rate limiting
- Resume capability for interrupted runs
- JSON output format option
- Integration with CI/CD pipelines
- Automatic diff generation if missing
- Confidence scores for detected differences
- Filtering by difference magnitude
