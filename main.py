import sys
import os

print("DEBUG: Starting main.py", flush=True)

# [WinError 1114] Fix: Set environment variables and import torch/whisper BEFORE PyQt6
# This avoids DLL conflicts (e.g., with Intel OpenMP / MKL)
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_THREADING_LAYER"] = "GNU"

try:
    print("DEBUG: Importing numpy...", flush=True)
    import numpy
    print(f"DEBUG: Numpy imported: {numpy.__version__}", flush=True)

    print("DEBUG: Importing torch and whisper...", flush=True)
    import torch
    import whisper
    print("DEBUG: Torch and whisper imported successfully.", flush=True)
except ImportError as e:
    print(f"DEBUG: ImportError for torch/whisper: {e}", flush=True)
    pass  # Allow program to continue if not installed, errors will be caught later

print("DEBUG: Importing QApplication...", flush=True)
from PyQt6.QtWidgets import QApplication

print("DEBUG: Importing MainWindow...", flush=True)
from ui.main_window import MainWindow


def main() -> None:
    print("DEBUG: Creating QApplication...", flush=True)
    app = QApplication(sys.argv)
    print("DEBUG: Creating MainWindow...", flush=True)
    try:
        window = MainWindow()
        print("DEBUG: Showing MainWindow...", flush=True)
        window.show()
        print("DEBUG: Entering event loop...", flush=True)
        sys.exit(app.exec())
    except Exception as e:
        print(f"DEBUG: Error in main execution: {e}", flush=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 개발 환경에서 실행 시, 코드가 변경되었다면 자동으로 패치 버전을 올림
    try:
        print("DEBUG: Checking version...", flush=True)
        from utils.version_manager import auto_bump_if_modified
        # 현재 파일(main.py)이 있는 디렉토리를 기준으로 변경 사항 체크
        auto_bump_if_modified(os.path.dirname(os.path.abspath(__file__)))
        print("DEBUG: Version check complete.", flush=True)
    except Exception as e:
        print(f"DEBUG: Auto version check failed: {e}", flush=True)

    main()
