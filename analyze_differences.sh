#!/bin/bash
# Complete workflow script for analyzing image differences with AI
# This script runs the comparison and then uses OpenRouter API to analyze differences

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored message
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if API key is set
check_api_key() {
    if [ -z "$OPENROUTER_API_KEY" ]; then
        print_error "OPENROUTER_API_KEY environment variable is not set"
        echo "Please set it with: export OPENROUTER_API_KEY=your_key_here"
        exit 1
    fi
    print_info "API key found in environment"
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Analyze image differences between two screenshot directories using AI.

Options:
    -a, --dir-a DIR         First screenshot directory (required)
    -b, --dir-b DIR         Second screenshot directory (required)
    -d, --diff-dir DIR      Difference images directory (optional, will be created if not exists)
    -o, --output DIR        Output directory for analysis results (default: analysis_results)
    -m, --model MODEL       OpenRouter model to use (default: google/gemini-2.0-flash-thinking-exp:free)
    -p, --prompt TEXT       Custom analysis prompt (optional)
    --skip-diff             Skip generating difference images if they already exist
    --rate-limit SECONDS    Delay between API calls (default: 1.0)
    -h, --help              Show this help message

Environment Variables:
    OPENROUTER_API_KEY      Your OpenRouter API key (required)

Examples:
    # Basic analysis
    export OPENROUTER_API_KEY=your_key_here
    $0 -a screenshots/run01 -b screenshots/run02

    # With existing difference directory
    $0 -a screenshots/run01 -b screenshots/run02 -d screenshots/comparison01

    # Custom output and model
    $0 -a screenshots/run01 -b screenshots/run02 -o detailed_analysis \\
        -m google/gemini-2.0-flash-thinking-exp:free

EOF
}

# Parse command line arguments
DIR_A=""
DIR_B=""
DIFF_DIR=""
OUTPUT_DIR="analysis_results"
MODEL="google/gemini-2.0-flash-thinking-exp:free"
CUSTOM_PROMPT=""
SKIP_DIFF=false
RATE_LIMIT="1.0"

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--dir-a)
            DIR_A="$2"
            shift 2
            ;;
        -b|--dir-b)
            DIR_B="$2"
            shift 2
            ;;
        -d|--diff-dir)
            DIFF_DIR="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -p|--prompt)
            CUSTOM_PROMPT="$2"
            shift 2
            ;;
        --skip-diff)
            SKIP_DIFF=true
            shift
            ;;
        --rate-limit)
            RATE_LIMIT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$DIR_A" ] || [ -z "$DIR_B" ]; then
    print_error "Both --dir-a and --dir-b are required"
    usage
    exit 1
fi

# Check if directories exist
if [ ! -d "$DIR_A" ]; then
    print_error "Directory does not exist: $DIR_A"
    exit 1
fi

if [ ! -d "$DIR_B" ]; then
    print_error "Directory does not exist: $DIR_B"
    exit 1
fi

# Check API key
check_api_key

print_info "Starting image difference analysis"
print_info "  Directory A: $DIR_A"
print_info "  Directory B: $DIR_B"
print_info "  Output: $OUTPUT_DIR"
print_info "  Model: $MODEL"

# Generate difference images if needed
if [ -n "$DIFF_DIR" ]; then
    if [ "$SKIP_DIFF" = true ] && [ -d "$DIFF_DIR" ]; then
        print_info "Skipping difference generation (--skip-diff specified)"
    else
        print_info "Generating difference images..."
        python automation_framework.py \
            --mode comparison \
            --inputs "$DIR_A" "$DIR_B" \
            --output "$DIFF_DIR"
        
        if [ $? -eq 0 ]; then
            print_info "Difference images generated successfully"
        else
            print_error "Failed to generate difference images"
            exit 1
        fi
    fi
fi

# Build analysis command
CMD="python image_analysis_openrouter.py"
CMD="$CMD --inputs \"$DIR_A\" \"$DIR_B\""
CMD="$CMD --output \"$OUTPUT_DIR\""
CMD="$CMD --model \"$MODEL\""
CMD="$CMD --rate-limit $RATE_LIMIT"

if [ -n "$DIFF_DIR" ]; then
    CMD="$CMD --diff-dir \"$DIFF_DIR\""
fi

if [ -n "$CUSTOM_PROMPT" ]; then
    CMD="$CMD --prompt \"$CUSTOM_PROMPT\""
fi

# Run analysis
print_info "Running AI analysis..."
eval $CMD

if [ $? -eq 0 ]; then
    print_info "Analysis completed successfully!"
    print_info "Results saved to: $OUTPUT_DIR"
    print_info ""
    print_info "Quick summary:"
    if [ -f "$OUTPUT_DIR/_summary.txt" ]; then
        head -n 20 "$OUTPUT_DIR/_summary.txt"
    fi
else
    print_error "Analysis failed"
    exit 1
fi
