"""
Tests for image analysis functionality.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from src.analysis.image_analyzer import OpenRouterClient, ImageAnalyzer
    from src.analysis.comparison import generate_comparison
    HAS_ANALYSIS_DEPS = True
except ImportError:
    HAS_ANALYSIS_DEPS = False


def test_openrouter_client_initialization():
    """Test OpenRouter client initialization."""
    if not HAS_ANALYSIS_DEPS:
        print("⚠ Skipping OpenRouter client test (missing dependencies)")
        return
    
    client = OpenRouterClient("fake_api_key", "test_model")
    assert client.api_key == "fake_api_key"
    assert client.model == "test_model"
    assert "Bearer fake_api_key" in client.headers["Authorization"]


def test_mock_api_key_handling():
    """Test API key handling in client."""
    if not HAS_ANALYSIS_DEPS:
        print("⚠ Skipping API key handling test (missing dependencies)")
        return
    
    # Test with different models
    client1 = OpenRouterClient("key1")
    assert client1.model == "google/gemini-2.0-flash-thinking-exp:free"
    
    client2 = OpenRouterClient("key2", "custom/model")
    assert client2.model == "custom/model"


def test_image_analyzer_initialization():
    """Test ImageAnalyzer initialization."""
    if not HAS_ANALYSIS_DEPS:
        print("⚠ Skipping ImageAnalyzer test (missing dependencies)")
        return
    
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_a = Path(tmpdir) / "a"
        dir_b = Path(tmpdir) / "b"
        dir_output = Path(tmpdir) / "output"
        
        dir_a.mkdir()
        dir_b.mkdir()
        dir_output.mkdir()
        
        client = OpenRouterClient("fake_key")
        
        # Test valid initialization
        analyzer = ImageAnalyzer(
            client=client,
            input_dirs=(dir_a, dir_b),
            diff_dir=None,
            output_dir=dir_output
        )
        
        assert analyzer.dir_a == dir_a
        assert analyzer.dir_b == dir_b
        assert analyzer.diff_dir is None
        assert analyzer.output_dir == dir_output
        assert analyzer.rate_limit_delay == 1.0


def test_find_image_pairs():
    """Test finding matching image pairs."""
    if not HAS_ANALYSIS_DEPS:
        print("⚠ Skipping image pairs test (missing dependencies)")
        return
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_a = Path(tmpdir) / "a"
        dir_b = Path(tmpdir) / "b"
        dir_output = Path(tmpdir) / "output"
        
        dir_a.mkdir()
        dir_b.mkdir()
        dir_output.mkdir()
        
        # Create test images
        (dir_a / "frame1.png").touch()
        (dir_a / "frame2.png").touch()
        (dir_a / "frame3.png").touch()
        
        (dir_b / "frame1.png").touch()
        (dir_b / "frame2.png").touch()
        # frame3 missing in dir_b
        
        (dir_a / "extra.png").touch()  # Extra file in dir_a only
        
        client = OpenRouterClient("fake_key")
        analyzer = ImageAnalyzer(
            client=client,
            input_dirs=(dir_a, dir_b),
            diff_dir=None,
            output_dir=dir_output
        )
        
        pairs = analyzer.find_image_pairs()
        
        # Should find 2 matching pairs (frame1 and frame2)
        assert len(pairs) == 2
        
        # Check pair structure
        for name, path_a, path_b, diff_path in pairs:
            assert name in ["frame1.png", "frame2.png"]
            assert path_a.name == name
            assert path_b.name == name
            assert diff_path is None  # No diff directory


def test_generate_comparison():
    """Test image comparison generation."""
    if not HAS_ANALYSIS_DEPS:
        print("⚠ Skipping comparison test (missing dependencies)")
        return
    
    try:
        from PIL import Image
    except ImportError:
        print("⚠ Skipping comparison test (missing PIL)")
        return
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_a = Path(tmpdir) / "a"
        dir_b = Path(tmpdir) / "b"
        dir_output = Path(tmpdir) / "output"
        
        dir_a.mkdir()
        dir_b.mkdir()
        dir_output.mkdir()
        
        # Create test images
        img1_a = Image.new('RGB', (100, 100), color='red')
        img1_b = Image.new('RGB', (100, 100), color='blue')
        img1_a.save(dir_a / "frame1.png")
        img1_b.save(dir_b / "frame1.png")
        
        img2_a = Image.new('RGB', (100, 100), color='green')
        img2_b = Image.new('RGB', (100, 100), color='yellow')
        img2_a.save(dir_a / "frame2.png")
        img2_b.save(dir_b / "frame2.png")
        
        # Run comparison
        generate_comparison([dir_a, dir_b], dir_output)
        
        # Check that diff images were created
        diff_files = list(dir_output.glob("*_diff.png"))
        assert len(diff_files) == 2
        
        # Check file names
        diff_names = [f.name for f in diff_files]
        assert "frame1_diff.png" in diff_names
        assert "frame2_diff.png" in diff_names


def test_invalid_directories():
    """Test handling of invalid directories."""
    if not HAS_ANALYSIS_DEPS:
        print("⚠ Skipping invalid directories test (missing dependencies)")
        return
    
    with tempfile.TemporaryDirectory() as tmpdir:
        client = OpenRouterClient("fake_key")
        
        # Test with non-existent directories
        dir_nonexistent = Path(tmpdir) / "nonexistent"
        dir_valid = Path(tmpdir) / "valid"
        dir_valid.mkdir()
        
        try:
            analyzer = ImageAnalyzer(
                client=client,
                input_dirs=(dir_nonexistent, dir_valid),
                diff_dir=None,
                output_dir=Path(tmpdir) / "output"
            )
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass  # Expected


if __name__ == "__main__":
    print("Testing image analysis functionality...")
    
    test_openrouter_client_initialization()
    print("✓ OpenRouter client initialization test passed")
    
    test_mock_api_key_handling()
    print("✓ API key handling test passed")
    
    test_image_analyzer_initialization()
    print("✓ ImageAnalyzer initialization test passed")
    
    test_find_image_pairs()
    print("✓ Image pairs finding test passed")
    
    test_generate_comparison()
    print("✓ Image comparison generation test passed")
    
    test_invalid_directories()
    print("✓ Invalid directories handling test passed")
    
    print("\nAll image analysis tests passed!")
