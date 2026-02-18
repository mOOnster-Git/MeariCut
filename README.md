# MeariCut (메아리컷)

**MeariCut**은 유치원/어린이집 선생님들이 아이들의 활동 영상을 손쉽게 편집할 수 있도록 도와주는 **AI 기반 자동 컷 편집 도구**입니다.

OpenAI의 **Whisper** 모델을 활용하여 음성을 인식하고, 특정 키워드(트리거)나 화자(선생님/아이들)를 기준으로 영상을 자동으로 분석하고 컷 편집해줍니다.

## ✨ 주요 기능

*   **🎙️ AI 음성 인식 (Whisper)**: 영상 속 음성을 텍스트로 변환하여 분석합니다.
*   **✂️ 자동 컷 편집**: "시작", "하나둘셋" 등 설정한 트리거 단어를 기준으로 영상을 자동으로 자릅니다.
*   **🗣️ 화자 분리 (Speaker Diarization)**: 선생님 목소리와 아이들 목소리를 구분하여 원하는 목소리만 남길 수 있습니다.
*   **🚀 초고속 렌더링 (Smart Rendering)**: 재인코딩 없이 영상을 자르는 '스마트 렌더링' 기술로 매우 빠른 저장 속도를 지원합니다.
*   **GPU 가속 지원**: NVIDIA, Intel, AMD 그래픽 카드를 활용한 하드웨어 가속을 지원합니다.

## 🛠️ 설치 방법 (Installation)

### 1. 필수 프로그램 설치
*   [Python 3.10 이상](https://www.python.org/downloads/)을 설치해주세요.
*   `ffmpeg`가 필요할 수 있습니다. (기본적으로 내장되어 있으나, 시스템에 설치 권장)

### 2. 프로젝트 클론 및 패키지 설치

```bash
# 1. 저장소 클론
git clone https://github.com/YOUR_USERNAME/MeariCut.git
cd MeariCut

# 2. 가상환경 생성 (권장)
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# 3. 필수 라이브러리 설치
pip install -r requirements.txt
```

### 3. PyTorch 설치 (GPU 가속용)
GPU 가속을 사용하려면 본인의 CUDA 버전에 맞는 PyTorch를 설치해야 합니다.
[PyTorch 공식 홈페이지](https://pytorch.org/get-started/locally/)를 참고하세요.

```bash
# 예시 (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## ▶️ 실행 방법 (Usage)

```bash
python main.py
```

1.  **영상 열기**: 편집할 동영상 파일을 불러옵니다.
2.  **분석 설정**: 트리거 단어(예: "시작")를 설정하고 분석을 시작합니다.
3.  **결과 확인**: 타임라인에서 잘라질 구간을 확인하고 미세 조정합니다.
4.  **저장**: '저장' 버튼을 눌러 편집된 영상을 내보냅니다.

## 🤝 기여하기 (Contributing)
버그 리포트, 기능 제안, 풀 리퀘스트는 언제나 환영합니다!

## 📄 라이선스 (License)
이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참고하세요.
