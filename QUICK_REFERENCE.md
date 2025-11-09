# Quick Reference: Image Analysis with OpenRouter

## Setup (One Time)
```bash
# Get API key from https://openrouter.ai/
export OPENROUTER_API_KEY='your_key_here'

# Install dependencies
pip install requests pillow
```

## Basic Commands

### Analyze Image Pairs
```bash
python image_analysis_openrouter.py \
    --inputs screenshots/run01 screenshots/run02 \
    --output analysis_results
```

### Include Difference Images
```bash
python image_analysis_openrouter.py \
    --inputs screenshots/run01 screenshots/run02 \
    --diff-dir screenshots/comparison01 \
    --output analysis_results
```

### Complete Automated Workflow
```bash
./analyze_differences.sh \
    -a screenshots/run01 \
    -b screenshots/run02 \
    -o analysis_results
```

## Common Options

| Option | Description | Example |
|--------|-------------|---------|
| `--inputs DIR1 DIR2` | Two directories to compare (required) | `--inputs run01 run02` |
| `--output DIR` | Output directory (required) | `--output results` |
| `--diff-dir DIR` | Directory with diff images | `--diff-dir comparison01` |
| `--api-key KEY` | API key (or use env var) | `--api-key sk-...` |
| `--model NAME` | Model to use | `--model google/gemini-2.0-flash-thinking-exp:free` |
| `--prompt TEXT` | Custom prompt | `--prompt "Describe colors only"` |
| `--rate-limit SEC` | Delay between calls | `--rate-limit 2.0` |
| `--log-level LVL` | Logging detail | `--log-level DEBUG` |

## Output Files

- `*_analysis.txt` - Individual analysis for each image pair
- `_summary.txt` - Overview of all analyses

## Typical Workflow

```bash
# 1. Generate screenshots (two runs)
./run_automation.sh --mode script --script events.txt \
    --exe ./GreenTriangle --output screenshots/run01

./run_automation.sh --mode script --script events.txt \
    --exe ./GreenTriangle --output screenshots/run02

# 2. Generate differences
./run_automation.sh --mode comparison \
    --inputs screenshots/run01 screenshots/run02 \
    --output screenshots/comparison01

# 3. AI Analysis
python image_analysis_openrouter.py \
    --inputs screenshots/run01 screenshots/run02 \
    --diff-dir screenshots/comparison01 \
    --output analysis_results

# 4. View results
cat analysis_results/_summary.txt
cat analysis_results/000_0000_after_launch_analysis.txt
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "API key not provided" | `export OPENROUTER_API_KEY='your_key'` |
| "No matching files" | Check both dirs have same PNG filenames |
| "Rate limit exceeded" | Add `--rate-limit 2.0` or higher |
| Connection errors | Check internet and OpenRouter status |

## Environment Variables

```bash
# Set API key
export OPENROUTER_API_KEY='sk-or-v1-...'

# Verify it's set
echo $OPENROUTER_API_KEY
```

## Available Models

Common OpenRouter models for vision tasks:
- `google/gemini-2.0-flash-thinking-exp:free` (free, recommended)
- `anthropic/claude-3-opus` (paid, high quality)
- `openai/gpt-4-vision-preview` (paid)

Check https://openrouter.ai/models for current list and pricing.

## Tips

✅ **DO:**
- Use consistent image naming across directories
- Start with `--rate-limit 2.0` for free tier
- Check `_summary.txt` first for overview
- Use custom prompts for specific analysis needs

❌ **DON'T:**
- Mix different image formats in same directory
- Forget to set OPENROUTER_API_KEY
- Use very short rate limits on free tier
- Process extremely large batches without monitoring

## Quick Examples

### Color Analysis Only
```bash
python image_analysis_openrouter.py \
    --inputs run01 run02 --output color_analysis \
    --prompt "Describe only color differences. Use plain text."
```

### Geometry Focus
```bash
python image_analysis_openrouter.py \
    --inputs run01 run02 --output geometry_analysis \
    --prompt "Focus on shapes, positions, rotations. Provide measurements."
```

### Slow and Steady (Free Tier)
```bash
python image_analysis_openrouter.py \
    --inputs run01 run02 --output results \
    --rate-limit 3.0 --log-level INFO
```

## Help Commands

```bash
# Full help
python image_analysis_openrouter.py --help

# Script help
./analyze_differences.sh --help

# Check version/info
python image_analysis_openrouter.py --version
```
