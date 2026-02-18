import sys
import os
import datetime

# [Fix] pythonw.exe 실행 시 크래시 원인을 파악하기 위해 로그 파일로 리다이렉트
# 프로그램이 "사라지는" 현상(크래시) 발생 시 crash_debug.log를 확인해야 함
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_debug.log")

class Logger(object):
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")

    def write(self, message):
        # 터미널이 있으면 출력 (python.exe 실행 시)
        if self.terminal and hasattr(self.terminal, "write"):
            try:
                self.terminal.write(message)
            except:
                pass
        # 파일에 기록
        try:
            self.log.write(message)
            self.log.flush()
        except:
            pass

    def flush(self):
        if self.terminal and hasattr(self.terminal, "flush"):
            try:
                self.terminal.flush()
            except:
                pass
        try:
            self.log.flush()
        except:
            pass

# stdout/stderr를 파일로 리다이렉트
sys.stdout = Logger(log_file_path)
sys.stderr = sys.stdout

print(f"DEBUG: Starting main.py at {datetime.datetime.now()}", flush=True)

# 전역 예외 처리기 (Uncaught Exceptions)
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    print("Uncaught exception:", flush=True)
    import traceback
    traceback.print_exception(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

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
except Exception as e:
    print(f"DEBUG: Error importing torch/whisper: {e}", flush=True)
    torch = None
    whisper = None

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
