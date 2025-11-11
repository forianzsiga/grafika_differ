# Grafika Differ - Project Documentation

## Overview

Grafika Differ is a cross-platform automation framework for image difference analysis and UI automation. The project provides tools for replaying recorded UI interactions, automated image capture and comparison, AI-powered image analysis, and cross-platform automation support for both Windows and Linux X11 environments.

## Project Structure

```
grafika_differ/
├── src/                          # Main source code directory
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # Main entry point
│   ├── analyze_images.py        # Image analysis functionality
│   ├── analysis/                # Image analysis and comparison
│   │   ├── __init__.py
│   │   ├── comparison.py        # Pixel-wise image comparison
│   │   └── image_analyzer.py    # AI-powered image analysis
│   ├── core/                    # Core automation framework
│   │   ├── __init__.py
│   │   ├── automation_runner.py # Main automation coordinator
│   │   ├── event_parser.py      # Script transcript parser
│   │   └── event_types.py       # Event definitions
│   ├── platform/                # Platform-specific implementations
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract platform interfaces
│   │   └── x11_automation.py    # Linux X11 automation
│   ├── ui/                      # User interface components
│   │   ├── __init__.py
│   │   └── interactive_viewer.py # Interactive image viewer
│   └── utils/                   # Utility functions
│       └── __init__.py
├── test/                        # Test files and examples
├── tests/                       # Unit tests
├── image_analysis_openrouter.py # OpenRouter AI integration (legacy, use src/analyze_images.py)
├── requirements.txt             # Python dependencies
├── README.md                    # Usage documentation
└── DOCUMENTATION.md            # This file
```

## Architecture Overview

### Core Components

#### 1. **Core Framework** (`src/core/`)
The heart of the automation system containing:

- **`event_types.py`**: Defines the `Event` dataclass that represents recorded UI interactions (mouse presses, releases, keyboard events)
- **`event_parser.py`**: Parses textual transcripts into structured `Event` objects with proper timing
- **`automation_runner.py`**: Coordinates process execution, input replay, and screenshot capture across platforms

#### 2. **Platform Abstraction** (`src/platform/`)
Provides cross-platform support through abstract interfaces and implementations:

- **`base.py`**: Defines abstract interfaces (`WindowManager`, `InputHandler`, `ScreenshotHandler`, `ProcessManager`)
- **`x11_automation.py`**: Linux X11 implementation using `python-xlib` and `xdotool`
- Windows implementation using `pywinauto` (integrated directly in automation_runner.py)

#### 3. **Image Analysis** (`src/analysis/`)
Advanced image processing and AI-powered analysis:

- **`comparison.py`**: Generates pixel-wise absolute differences between matching frames using PIL
- **`image_analyzer.py`**: OpenRouter API integration for AI-powered image difference analysis using multimodal models

#### 4. **User Interface** (`src/ui/`)
Interactive tools for viewing and analyzing results:

- **`interactive_viewer.py`**: Tkinter-based GUI for viewing image comparisons with multiple display modes (side-by-side, overlay, split, diff)

### Entry Points

#### 1. **`src/main.py`**
Modern modular entry point that provides a clean command-line interface for all framework modes:
- **Script Mode**: Replays recorded events from transcript files
- **Comparison Mode**: Generates pixel-wise differences between two image directories
- **Interactive Mode**: Launches the image viewer GUI
- **Stealth Mode**: Captures frames at fixed intervals without event replay

#### 2. **`image_analysis_openrouter.py`**
Legacy script for AI-powered image analysis. **Deprecated**: Use `src/analyze_images.py` instead for better integration and error handling.

#### 3. **`image_analysis_openrouter.py`**
Dedicated script for AI-powered image analysis using OpenRouter's API with support for multiple multimodal models.

## Key Features

### 1. **Cross-Platform Automation**
- **Windows**: Uses `pywinauto` for window management and `pyautogui` for input simulation
- **Linux/X11**: Uses `python-xlib` for X11 interaction and `xdotool` for enhanced reliability

### 2. **Multiple Execution Modes**

#### Script Mode
Replays recorded UI interactions from text transcripts:
```
[ +0.370s ] onMousePressed L: window(100,100) -> world(-16.666666,16.666666)
[ +0.370s ] onMouseReleased L: window(100,100) -> world(-16.666666,16.666666)
```

#### Comparison Mode
Generates pixel-wise absolute differences between two runs:
- Uses PIL's `ImageChops.difference` for accurate pixel comparison
- Handles size mismatches and different image modes gracefully
- Outputs `_diff.png` files for each matched frame

#### Interactive Mode
GUI viewer with multiple display modes:
- **Side-by-side**: Two images displayed next to each other
- **Overlay**: Alpha-blended combination of both images
- **Split**: Draggable division between the two images
- **Diff**: Shows pre-computed or real-time difference images

#### Stealth Mode
Capture frames at fixed intervals without code injection:
- Useful for applications where modifying source code isn't possible
- Configurable capture interval and total duration
- Generates timestamped frame sequences

### 3. **AI-Powered Analysis**
Integration with OpenRouter API for intelligent image difference analysis:
- Supports multiple multimodal models (GPT-4o-mini, Gemini, Claude)
- Dry-run mode for testing without API costs
- Detailed textual descriptions of visual differences
- Rate limiting and error handling

### 4. **Robust Error Handling**
- Graceful fallbacks for screenshot capture (window → full screen)
- Platform-specific window detection strategies
- Process monitoring and cleanup
- Comprehensive logging with configurable levels

## Dependencies

### Core Dependencies (`requirements.txt`)
- `pyautogui`: Cross-platform input simulation
- `pywinauto`: Windows UI automation
- `pillow`: Image processing capabilities
- `python-xlib`: X11 client library for Linux
- `psutil`: Process and system utilities
- `requests`: HTTP library for API calls
- `python-dotenv`: Environment variable management

### Platform-Specific Dependencies

#### Windows
- `pywinauto`: Native Windows UI automation
- Windows UI Automation APIs

#### Linux
- `python-xlib`: Direct X11 communication
- `xdotool`: Command-line X11 automation tool (recommended)
- `scrot`, `imagemagick`, or `xwd`: Screenshot utilities
- X11 server (standard on most Linux desktop environments)

## Usage Patterns

### Basic Workflow
1. **Record Events**: Generate transcript files from application runs
2. **Replay Script**: Use script mode to replay events and capture screenshots
3. **Generate Differences**: Use comparison mode to create pixel-wise diffs
4. **Analyze Results**: Use interactive mode to view results or AI analysis for automated insights

### Advanced Features
- **Stealth Mode**: No code modification required
- **AI Analysis**: Automated description of visual differences
- **Cross-Platform**: Same scripts work on Windows and Linux
- **Batch Processing**: Automated workflows via shell scripts

## Design Principles

### 1. **Modularity**
- Clear separation of concerns between platform, analysis, and UI components
- Abstract interfaces enable easy testing and extension
- Clean package structure with logical groupings

### 2. **Cross-Platform Compatibility**
- Platform detection and conditional imports
- Abstract base classes for platform-specific implementations
- Consistent APIs across different operating systems

### 3. **Error Resilience**
- Multiple fallback strategies for critical operations
- Graceful degradation when features aren't available
- Comprehensive logging for troubleshooting

### 4. **Extensibility**
- Plugin-like architecture for new analysis methods
- Configurable AI models and analysis prompts
- Easy integration with external tools and APIs

## Testing Structure

### Test Organization
- **`test/`**: Integration tests and examples
- **`tests/`**: Unit tests organized by module
- **Test executables**: Sample applications for testing automation

### Test Categories
- **Platform-specific tests**: Validated on both Windows and Linux
- **Image processing tests**: Verify comparison and analysis accuracy
- **Integration tests**: End-to-end workflow validation

## Development Guidelines

### Code Organization
- Use abstract base classes for platform-specific implementations
- Implement proper error handling and logging throughout
- Maintain consistent naming conventions and documentation

### Platform Considerations
- Windows: Focus on pywinauto integration and process management
- Linux: Emphasize X11 robustness and display handling
- Cross-platform: Ensure consistent behavior across operating systems

### Performance Optimization
- Efficient image processing using PIL
- Rate limiting for API calls
- Optimized screenshot capture strategies

## Future Enhancements

### Potential Improvements
1. **Additional Platforms**: macOS automation support
2. **Advanced AI Models**: Integration with more AI providers
3. **Performance Monitoring**: Automated performance regression detection
4. **Cloud Integration**: Remote execution and result storage
5. **Visual Regression Testing**: Automated testing frameworks

This documentation provides a comprehensive overview of the Grafika Differ project's architecture, components, and capabilities. The modular design enables easy maintenance, testing, and extension of the framework.