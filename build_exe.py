import os
import subprocess
import sys
import site

# Set environment variables for torch
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

print("Script started...", flush=True)

# 프로젝트 루트 경로 추가 (version.py import 위해)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from version import VERSION
except ImportError:
    VERSION = "1.0.0"

# Avoid importing torch directly as it causes crashes in this env
print("Locating torch without import...", flush=True)
torch_path = ""
for site_pkg in site.getsitepackages():
    candidate = os.path.join(site_pkg, "torch")
    if os.path.exists(candidate):
        torch_path = candidate
        print(f"Torch found at: {torch_path}")
        break

if not torch_path:
    # Fallback for user specific site-packages
    user_site = site.getusersitepackages()
    candidate = os.path.join(user_site, "torch")
    if os.path.exists(candidate):
        torch_path = candidate
        print(f"Torch found at user site: {torch_path}")

# 실행 파일 이름 설정 (MeariCut_v1.0.22.exe)
exe_name = f"MeariCut_v{VERSION}"

print(f"Building {exe_name}...", flush=True)

# PyInstaller 명령어 구성
# [중요] torch와 같은 대형 DLL을 포함할 때는 --onefile 보다
# --onedir 모드가 DLL 초기화 오류(WinError 1114)가 훨씬 적습니다.
cmd = [
    "pyinstaller",
    "--noconfirm",
    "--onedir",  # 폴더 형태로 배포 (안정성 우선)
    "--windowed",
    "--name", exe_name,
    "--add-data", "kakao.png;.",
    "--add-data", "toss.png;.",
    "--hidden-import", "scipy.special.cython_special",
    "--collect-all", "whisper",
    "--collect-all", "imageio",
    "--collect-all", "imageio_ffmpeg",
    "--exclude-module", "torchaudio",
    "--exclude-module", "torchvision",
    "--clean",
    "main.py",
]

# torch DLL은 PyInstaller의 hook이 자동으로 수집합니다.
# 이전에는 torch/lib에서 DLL을 직접 추가했지만,
# 이는 DLL 중복/충돌로 WinError 1114를 유발할 수 있어 제거합니다.

print(f"Command: {cmd}", flush=True)

try:
    # Run PyInstaller
    subprocess.run(cmd, check=True)
    print(f"Build complete! File is located in 'dist/{exe_name}.exe'", flush=True)
except subprocess.CalledProcessError as e:
    print(f"Build failed: {e}", flush=True)
except Exception as e:
    print(f"Execution failed: {e}", flush=True)
