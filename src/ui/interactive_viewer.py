"""Interactive image viewer for comparing multiple image sets.

This module provides a GUI for viewing and comparing image sets with
different display modes (side-by-side, overlay, split, diff).
"""

import logging
from pathlib import Path
from typing import List, Optional

try:
    import tkinter as tk
    from PIL import Image, ImageTk, ImageChops
except ImportError as exc:
    raise ImportError(
        "Interactive viewer requires tkinter and Pillow. Install with 'pip install pillow'. Original error: %s" % exc
    )


class InteractiveViewer:
    """Interactive image viewer for comparing image sets."""
    
    def __init__(self, inputs: List[Path]) -> None:
        """Initialize the viewer with input directories.
        
        Args:
            inputs: List of 2-3 input directories (A, B, [diff])
        """
        if len(inputs) < 2:
            raise ValueError("Interactive viewer requires at least two input directories")
        
        self.dir_a, self.dir_b = inputs[0], inputs[1]
        self.dir_diff = inputs[2] if len(inputs) >= 3 else None
        
        # Validate directories
        for directory in (self.dir_a, self.dir_b):
            if not directory.exists() or not directory.is_dir():
                raise FileNotFoundError(f"Input directory not found: {directory}")
        
        if self.dir_diff and not self.dir_diff.exists():
            logging.warning(f"Diff directory not found: {self.dir_diff}")
            self.dir_diff = None
        
        # Load file mappings
        self._load_files()
        
        # Initialize viewer
        self._setup_viewer()
    
    def _load_files(self) -> None:
        """Load and match image files across directories."""
        self.files_a = {p.name: p for p in self.dir_a.glob("*.png")}
        self.files_b = {p.name: p for p in self.dir_b.glob("*.png")}
        self.names = sorted(self.files_a.keys() & self.files_b.keys())
        
        if not self.names:
            raise SystemExit("No matching PNG filenames across the first two inputs")
        
        self.files_diff = {}
        if self.dir_diff:
            self.files_diff = {p.name: p for p in self.dir_diff.glob("*.png")}
    
    def _setup_viewer(self) -> None:
        """Set up the tkinter viewer interface."""
        self.root = tk.Tk()
        self.root.title("Interactive Viewer")
        self.mode = 0  # 0 side, 1 overlay, 2 split, 3 diff
        self.modes = ["side-by-side", "overlay", "split", "diff"]
        self.index = 0
        self.alpha = 0.5
        self.split = 0.5
        self.fit = True
        self.help_on = True
        
        # Setup canvas
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.canvas = tk.Canvas(
            self.root, 
            width=min(1600, sw-100), 
            height=min(900, sh-100), 
            bg="#222"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind events
        self._bind_events()
        
        # Initial render
        self.photo = None
        self.render()
    
    def _bind_events(self) -> None:
        """Bind keyboard and mouse events."""
        # Window events
        self.canvas.bind("<Configure>", lambda e: self.render())
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        
        # Keyboard shortcuts
        self.root.bind("<Left>", lambda e: self.prev())
        self.root.bind("<Right>", lambda e: self.next())
        self.root.bind("1", lambda e: self.set_mode(0))
        self.root.bind("2", lambda e: self.set_mode(1))
        self.root.bind("3", lambda e: self.set_mode(2))
        self.root.bind("4", lambda e: self.set_mode(3))
        self.root.bind("[", lambda e: self._set_alpha(self.alpha - 0.05))
        self.root.bind("]", lambda e: self._set_alpha(self.alpha + 0.05))
        self.root.bind(",", lambda e: self._set_split(self.split - 0.05))
        self.root.bind(".", lambda e: self._set_split(self.split + 0.05))
        self.root.bind("f", lambda e: self._toggle_fit())
        self.root.bind("F", lambda e: self._toggle_fit())
        self.root.bind("h", lambda e: self._toggle_help())
        self.root.bind("?", lambda e: self._toggle_help())
    
    def _toggle_fit(self) -> None:
        """Toggle fit-to-window mode."""
        self.fit = not self.fit
        self.render()
    
    def _toggle_help(self) -> None:
        """Toggle help overlay."""
        self.help_on = not self.help_on
        self.render()
    
    def set_mode(self, m: int) -> None:
        """Set display mode.
        
        Args:
            m: Mode index (0=side-by-side, 1=overlay, 2=split, 3=diff)
        """
        self.mode = m
        
        # Change cursor for split mode
        if self.mode == 2:
            try:
                self.canvas.config(cursor="sb_h_double_arrow")
            except Exception:
                self.canvas.config(cursor="")
        else:
            self.canvas.config(cursor="")
        
        self.render()
    
    def _set_alpha(self, a: float) -> None:
        """Set overlay alpha value.
        
        Args:
            a: Alpha value between 0.0 and 1.0
        """
        self.alpha = max(0.0, min(1.0, a))
        if self.mode == 1:  # Only re-render in overlay mode
            self.render()
    
    def _set_split(self, s: float) -> None:
        """Set split position.
        
        Args:
            s: Split position between 0.0 and 1.0
        """
        self.split = max(0.0, min(1.0, s))
        if self.mode == 2:  # Only re-render in split mode
            self.render()
    
    def prev(self) -> None:
        """Show previous image pair."""
        self.index = (self.index - 1) % len(self.names)
        self.render()
    
    def next(self) -> None:
        """Show next image pair."""
        self.index = (self.index + 1) % len(self.names)
        self.render()
    
    def _load_pair(self) -> tuple:
        """Load current image pair for display.
        
        Returns:
            Tuple of (name, image_a, image_b, diff_image)
        """
        name = self.names[self.index]
        a = Image.open(self.files_a[name]).convert("RGB")
        b = Image.open(self.files_b[name]).convert("RGB")
        
        # Resize if needed
        if a.size != b.size:
            b = b.resize(a.size, Image.LANCZOS)
        
        # Load diff image if available
        d = None
        if name in self.files_diff:
            try:
                d = Image.open(self.files_diff[name]).convert("RGB")
                if d.size != a.size:
                    d = d.resize(a.size, Image.LANCZOS)
            except Exception:
                d = None
        
        return name, a, b, d
    
    def _compose(self, a: Image.Image, b: Image.Image, d: Optional[Image.Image]) -> Image.Image:
        """Compose images based on current display mode.
        
        Args:
            a: First image
            b: Second image
            d: Optional difference image
            
        Returns:
            Composed image for display
        """
        if self.mode == 0:  # side-by-side
            w, h = a.size
            out = Image.new("RGB", (w*2, h), (0, 0, 0))
            out.paste(a, (0, 0))
            out.paste(b, (w, 0))
            return out
            
        elif self.mode == 1:  # overlay
            return Image.blend(a, b, self.alpha)
            
        elif self.mode == 2:  # split
            w, h = a.size
            x = int(self.split * w)
            out = Image.new("RGB", (w, h), (0, 0, 0))
            out.paste(a.crop((0, 0, x, h)), (0, 0))
            out.paste(b.crop((x, 0, w, h)), (x, 0))
            return out
            
        else:  # diff mode
            if d is not None:
                return d
            return ImageChops.difference(a, b)
    
    def _fit_image(self, img: Image.Image) -> Image.Image:
        """Scale image to fit window if needed.
        
        Args:
            img: Input image
            
        Returns:
            Scaled image
        """
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        
        if cw <= 1 or ch <= 1:
            return img
        
        if not self.fit:
            return img
        
        iw, ih = img.size
        scale = min(cw / iw, ch / ih)
        
        if scale < 1.0:
            nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
            return img.resize((nw, nh), Image.LANCZOS)
        
        return img
    
    def render(self) -> None:
        """Render the current image pair."""
        name, a, b, d = self._load_pair()
        composed = self._compose(a, b, d)
        disp = self._fit_image(composed)
        
        self.photo = ImageTk.PhotoImage(disp)
        self.canvas.delete("all")
        
        # Calculate center position
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        x = max(0, (cw - disp.size[0]) // 2)
        y = max(0, (ch - disp.size[1]) // 2)
        
        # Store drawn image geometry for hit testing
        self._draw_x, self._draw_y = x, y
        self._draw_w, self._draw_h = disp.size
        
        # Draw image
        self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
        
        # Draw splitter in split mode
        if self.mode == 2:
            sx = x + int(self.split * self._draw_w)
            self.canvas.create_line(sx, y, sx, y + self._draw_h, fill="#FFD54F", width=2)
        
        # Update window title
        self.root.title(f"{self.names[self.index]}  |  {self.modes[self.mode]}  |  {self.dir_a.name} vs {self.dir_b.name}")
        
        # Draw help text
        if self.help_on:
            help_text = (
                "←/→ prev/next   1 side  2 overlay  3 split  4 diff   "
                "[/] alpha   ,/. split   F fit   H help"
            )
            self.canvas.create_text(10, 10, anchor=tk.NW, text=help_text, fill="#fff", font=("Segoe UI", 10))
    
    def _on_click(self, event) -> None:
        """Handle mouse click events."""
        if self.mode == 2 and self.canvas.winfo_width() > 0:
            self._update_split_from_x(event.x)
    
    def _on_drag(self, event) -> None:
        """Handle mouse drag events."""
        if self.mode == 2 and self.canvas.winfo_width() > 0:
            self._update_split_from_x(event.x)
    
    def _update_split_from_x(self, x: int) -> None:
        """Update split position from mouse position.
        
        Args:
            x: Mouse x coordinate
        """
        # Map canvas x to image-local x if image is centered
        draw_x = getattr(self, "_draw_x", 0)
        draw_w = max(1, getattr(self, "_draw_w", self.canvas.winfo_width()))
        rel = (x - draw_x) / draw_w
        self._set_split(rel)
    
    def run(self) -> None:
        """Start the interactive viewer."""
        self.root.mainloop()
