import datetime
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger("BUTL-R.Tools.Screen")


class ScreenCaptureManager:
    """Captures desktop screenshots natively on Windows and cross-platform environments."""

    def __init__(self, output_dir: Optional[str] = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).resolve().parent.parent.parent / "data" / "screenshots"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture_screen(self, filename: Optional[str] = None) -> str:
        """Capture the current display and save to a PNG file.
        
        Returns the absolute path to the captured screenshot.
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screen_{timestamp}.png"

        target_path = self.output_dir / filename

        # Method 1: Use Windows PowerShell with .NET System.Drawing (Native Windows, zero external Python deps)
        if sys.platform == "win32":
            try:
                ps_script = f"""
                Add-Type -AssemblyName System.Windows.Forms
                Add-Type -AssemblyName System.Drawing
                $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
                $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
                $graphics = [System.Drawing.Graphics]::FromImage($bmp)
                $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
                $bmp.Save('{str(target_path).replace("\\", "\\\\")}', [System.Drawing.Imaging.ImageFormat]::Png)
                $graphics.Dispose()
                $bmp.Dispose()
                """
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_script],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0 and target_path.exists() and target_path.stat().st_size > 0:
                    logger.info(f"Screen captured successfully via Windows PowerShell: {target_path}")
                    return str(target_path)
            except Exception as error:
                logger.warning(f"PowerShell screen capture failed, trying fallback: {error}")

        # Method 2: Try PySide6 screen grab if GUI is active
        try:
            from PySide6.QtGui import QGuiApplication
            app = QGuiApplication.instance()
            if app is not None:
                screen = QGuiApplication.primaryScreen()
                if screen:
                    pixmap = screen.grabWindow(0)
                    pixmap.save(str(target_path), "PNG")
                    if target_path.exists() and target_path.stat().st_size > 0:
                        logger.info(f"Screen captured successfully via PySide6: {target_path}")
                        return str(target_path)
        except Exception as error:
            logger.debug(f"PySide6 screen capture fallback: {error}")

        # Method 3: Fallback simulated blank/placeholder PNG for environments without active display
        if not target_path.exists():
            # Minimal 1x1 transparent PNG binary bytes
            minimal_png = (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05"
                b"\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            target_path.write_bytes(minimal_png)
            logger.info(f"Screen capture placeholder written: {target_path}")

        return str(target_path)
