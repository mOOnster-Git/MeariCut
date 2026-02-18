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
cmd = [
    "pyinstaller",
    "--noconfirm",
    "--onefile",
    "--windowed",
    "--name", exe_name,
    "--add-data", "kakao.png;.",
    "--add-data", "toss.png;.",
    "--hidden-import", "scipy.special.cython_special",
    "--hidden-import", "torch",
    "--collect-all", "whisper",
    "--exclude-module", "torchaudio",
    "--exclude-module", "torchvision",
    "--clean",
    "main.py"
]

if torch_path:
            # Explicitly add ALL DLLs from torch/lib
            torch_lib = os.path.join(torch_path, 'lib')
            if os.path.exists(torch_lib):
                dlls = [f for f in os.listdir(torch_lib) if f.endswith('.dll')]
                for dll in dlls:
                    dll_path = os.path.join(torch_lib, dll)
                    # Insert before main.py (last argument)
                    cmd.insert(-1, "--add-binary")
                    cmd.insert(-1, f"{dll_path};torch/lib")
                    
                    # Also add libiomp5md.dll to the root
                    if "libiomp5md.dll" in dll:
                        cmd.insert(-1, "--add-binary")
                        cmd.insert(-1, f"{dll_path};.")
                        print(f"Added binary to root: {dll}")

                    print(f"Added binary: {dll}")
            else:
                print(f"Warning: {torch_lib} not found")

print(f"Command: {cmd}", flush=True)

try:
    # Run PyInstaller
    subprocess.run(cmd, check=True)
    print(f"Build complete! File is located in 'dist/{exe_name}.exe'", flush=True)
except subprocess.CalledProcessError as e:
    print(f"Build failed: {e}", flush=True)
except Exception as e:
    print(f"Execution failed: {e}", flush=True)



