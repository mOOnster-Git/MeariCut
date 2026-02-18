import os
import sys
import shutil
import whisper
import torch
import random
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from moviepy.editor import VideoFileClip, concatenate_videoclips
import imageio_ffmpeg

# [환경 설정] WinError 1114 및 FFmpeg 경로 설정
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["OMP_NUM_THREADS"] = "1"

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_exe)
os.environ["PATH"] += os.pathsep + ffmpeg_dir

# Windows ffmpeg 바이너리 복사 (안전장치)
if sys.platform == "win32" and shutil.which("ffmpeg") is None:
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bin_dir = os.path.join(project_root, "bin")
        os.makedirs(bin_dir, exist_ok=True)
        target_ffmpeg = os.path.join(bin_dir, "ffmpeg.exe")
        if not os.path.exists(target_ffmpeg) or os.path.getsize(target_ffmpeg) != os.path.getsize(ffmpeg_exe):
            shutil.copy2(ffmpeg_exe, target_ffmpeg)
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]
    except Exception as e:
        print(f"Warning: Failed to setup local ffmpeg: {e}")

class MeariProcessor:
    _model_cache = {}

    def __init__(
        self,
        model_name: str = "tiny",
        device: Optional[str] = None,
        triggers: Optional[List[str]] = None,
    ) -> None:
        self.model_name = model_name
        
        # [Device Auto-Detection]
        if device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
                print(f"🚀 CUDA GPU Detected: {torch.cuda.get_device_name(0)}")
            else:
                self.device = "cpu"
                print("⚠️ No GPU detected, using CPU (slower)")
        else:
            self.device = device
            
        self.triggers = triggers or ["시작", "하나둘셋", "둘셋"]
        self.model = None

    def _ensure_model(self) -> None:
        if self.model is None:
            # 캐시된 모델이 있으면 재사용
            cache_key = (self.model_name, self.device)
            if cache_key in MeariProcessor._model_cache:
                print(f"Loading Whisper model '{self.model_name}' from cache...")
                self.model = MeariProcessor._model_cache[cache_key]
            else:
                print(f"Loading Whisper model '{self.model_name}' on {self.device}...")
                self.model = whisper.load_model(self.model_name, device=self.device)
                MeariProcessor._model_cache[cache_key] = self.model

    def transcribe(
        self,
        video_path: str | Path,
        language: str = "ko",
    ) -> dict:
        self._ensure_model()
        
        # [Whisper Prompt Engineering]
        # 모델에게 이런 단어가 나올 거라고 미리 '귀띔'을 해줌
        # 잡음이 많거나 발화가 짧은 경우에도 놓치지 않도록 유도
        # "졸업", "학교" 등 아이들 관련 키워드 추가
        initial_prompt = "선생님 목소리. 유치원 수업. 시작. 하나둘셋. 둘셋. 집중하세요. 자. 네. 졸업. 학교. 입학. 안녕."
        
        # [Optimization Settings]
        use_fp16 = (self.device == "cuda")
        beam_size = 1 if self.device == "cpu" else 5 # CPU는 속도 우선(Greedy), GPU는 정확도 우선(Beam)
        
        try:
            result = self.model.transcribe(
                str(video_path),
                language=language,
                verbose=False,
                initial_prompt=initial_prompt,    # 핵심: 힌트 제공
                word_timestamps=True,             # 핵심: 단어 단위 시간 활성화 (정밀도 향상)
                condition_on_previous_text=False, # 환각 방지
                fp16=use_fp16,                    # GPU 가속 (CPU는 False)
                beam_size=beam_size,              # 탐색 폭 조절
                
                # [Hallucination Prevention]
                # 잡음을 무의미한 텍스트로 인식하는 것을 방지하기 위한 파라미터
                compression_ratio_threshold=2.4,  # 반복되는 텍스트(나나나...) 무시
                logprob_threshold=-1.0,           # 확신이 낮은 구간 무시
                no_speech_threshold=0.6           # 말소리가 없는 구간 무시
            )
        except Exception as e:
            print(f"Transcription failed with default settings: {e}")
            print("Retrying with fallback settings (fp16=False, beam_size=1)...")
            try:
                result = self.model.transcribe(
                    str(video_path),
                    language=language,
                    verbose=False,
                    fp16=False,
                    beam_size=1, # Retry는 무조건 Greedy Search
                    initial_prompt=initial_prompt,
                    word_timestamps=True,
                    condition_on_previous_text=False,
                    
                    # [Hallucination Prevention] - Retry에도 동일 적용
                    compression_ratio_threshold=2.4,
                    logprob_threshold=-1.0,
                    no_speech_threshold=0.6
                )
            except Exception as e2:
                print(f"Transcription failed again: {e2}")
                raise e2
                
        return result

    def find_trigger_segments(self, segments: List[dict], triggers: Optional[List[str]] = None) -> List[dict]:
        """
        단어(Word) 단위로 정밀하게 트리거를 찾아냅니다.
        시간상으로 멀리 떨어진 트리거 단어들은 별개의 구간으로 분리(Clustering)합니다.
        """
        use_triggers = triggers or self.triggers
        found = []
        num_map = {"1": "하나", "2": "둘", "3": "셋"} # 숫자 변환 맵

        for seg in segments:
            # 1. 정밀 모드: Whisper가 '단어 정보(words)'를 줬을 때
            if "words" in seg:
                trigger_words = []
                # 1차 필터링: 세그먼트 내의 모든 트리거 단어 수집
                for word_info in seg["words"]:
                    word_text = word_info.get("word", "").strip()
                    # 특수문자 제거 및 숫자 변환
                    clean_text = "".join(c for c in word_text if c.isalnum())
                    clean_text = num_map.get(clean_text, clean_text)
                    
                    # 트리거 단어인지 확인
                    for trigger in use_triggers:
                        if trigger in clean_text or clean_text in trigger:
                            trigger_words.append(word_info)
                            break
                
                # 2차 클러스터링: 시간차 기반으로 그룹 분리
                if trigger_words:
                    groups = []
                    current_group = []
                    cluster_threshold = 0.8  # 트리거 단어 간 분리 임계값 (0.8초로 상향 조정)
                    
                    for word in trigger_words:
                        if not current_group:
                            current_group.append(word)
                        else:
                            last_word = current_group[-1]
                            # 현재 단어 시작 - 이전 단어 끝 시간 차이가 임계값 미만이면 같은 그룹
                            if float(word["start"]) - float(last_word["end"]) < cluster_threshold:
                                current_group.append(word)
                            else:
                                # 임계값 이상 차이나면 기존 그룹 저장하고 새 그룹 시작
                                groups.append(current_group)
                                current_group = [word]
                    
                    # 마지막 그룹 저장
                    if current_group:
                        groups.append(current_group)
                    
                    # 각 그룹별로 결과 생성
                    for group in groups:
                        start_time = float(group[0]["start"])
                        end_time = float(group[-1]["end"])
                        detected_text = " ".join([w["word"] for w in group])
                        
                        # [Dynamic Padding] 트리거 단어별 맞춤 패딩
                        # 기본값은 짧게(0.1), 길게 끄는 단어("다시")는 길게(0.8)
                        current_end_padding = 0.1
                        
                        if "다시" in detected_text:
                            current_end_padding = 0.8
                        elif "자" in detected_text: # "자~" 같은 경우
                            current_end_padding = 0.5
                            
                        # 신뢰도 및 상태 결정
                        confidence = 1.0
                        status = "confirmed" if confidence >= 0.9 else "candidate"

                        found.append({
                            "text": detected_text,
                            "word": detected_text, # Alias for UI compatibility
                            "start": max(0, start_time - 0.2), # 시작 패딩은 0.2로 고정
                            "end": end_time + current_end_padding, # 끝 패딩 가변 적용
                            "confidence": confidence,
                            "status": status
                        })
            
            # 2. 일반 모드: 단어 정보가 없을 때 (예비용)
            else:
                text = seg.get("text", "")
                clean_text = "".join(c for c in text if c.isalnum())
                for trigger in use_triggers:
                    if trigger in clean_text:
                        # 문장이 너무 길면(3초 이상) 트리거일 확률이 낮으므로 앞부분 1초만 사용
                        start = float(seg.get("start", 0))
                        end = float(seg.get("end", 0))
                        if end - start > 3.0:
                            end = start + 1.0
                            
                        # 신뢰도 및 상태 결정 (일반 모드는 신뢰도 낮음)
                        confidence = 0.8
                        status = "confirmed" if confidence >= 0.9 else "candidate"

                        found.append({
                            "text": text,
                            "word": text,
                            "start": start,
                            "end": end,
                            "confidence": confidence,
                            "status": status
                        })
                        break
        return found

    def calculate_intervals(
        self,
        trigger_segments: List[dict],
        total_duration: float,
        include_trigger: bool = False,
    ) -> List[Tuple[float, float]]:
        # 트리거 구간을 '삭제(Red)'하고 나머지를 '보존(Green)'하는 로직
        valid_clips = []
        if not trigger_segments:
             return [(0.0, total_duration)]

        sorted_triggers = sorted(trigger_segments, key=lambda x: float(x.get("start", 0)))
        last_end = 0.0
        
        for seg in sorted_triggers:
            start = float(seg.get("start", 0))
            end = float(seg.get("end", 0))
            
            if start > last_end:
                valid_clips.append((last_end, start))
            
            if include_trigger:
                last_end = start # 트리거 포함 (삭제 안 함)
            else:
                last_end = end   # 트리거 삭제
                
        if last_end < total_duration:
            valid_clips.append((last_end, total_duration))
            
        return valid_clips

    def _detect_speakers(self, total_duration: float) -> Tuple[List[dict], List[dict]]:
        # 시뮬레이션 데이터 (실제 분석 아님 - 속도 영향 없음)
        random.seed(42)
        speaker_defs = [
            {"id": "spk_01", "name": "선생님 목소리 (후보)", "is_adult": True, "weight": 0.45},
            {"id": "spk_02", "name": "아이들 목소리", "is_adult": False, "weight": 0.35},
            {"id": "spk_03", "name": "목소리 2 (성인)", "is_adult": True, "weight": 0.15},
        ]
        speaker_segments = []
        current_time = 0.0
        
        while current_time < total_duration:
            seg_duration = random.uniform(2.0, 10.0)
            if current_time + seg_duration > total_duration:
                seg_duration = total_duration - current_time
            
            chosen = random.choices(speaker_defs, weights=[s["weight"] for s in speaker_defs])[0]
            speaker_segments.append({
                "start": current_time,
                "end": current_time + seg_duration,
                "speaker_id": chosen["id"]
            })
            current_time += seg_duration
            
        return speaker_defs, speaker_segments

    def filter_triggers_by_speaker(self, triggers, speaker_segments, selected_ids, tolerance=1.0):
        # [관대함 모드] 애매하면 살려두는 로직
        if not selected_ids: return triggers
        valid = []
        for trig in triggers:
            trig_start = float(trig.get("start", 0))
            trig_end = float(trig.get("end", 0))
            check_start = max(0, trig_start - tolerance)
            check_end = trig_end + tolerance
            
            overlapping = set()
            for seg in speaker_segments:
                if max(check_start, seg["start"]) < min(check_end, seg["end"]):
                    overlapping.add(seg["speaker_id"])
            
            # 목소리 정보가 없거나, 선택된 목소리가 포함되어 있으면 유지
            if not overlapping or any(sid in selected_ids for sid in overlapping):
                valid.append(trig)
            # 확실히 다른 목소리(아이들)만 있을 때만 제거
        return valid

    def analyze_video(
        self,
        video_path: str | Path,
        language: str = "ko",
        triggers: Optional[List[str]] = None,
        include_trigger: bool = False,
    ) -> Tuple[List[Tuple[float, float]], float, List[dict], List[dict], List[dict]]:
        
        path_str = str(video_path)
        
        # [속도 최적화] 영상 길이만 빠르게 가져오고 즉시 해제 (인코딩 방지)
        try:
            with VideoFileClip(path_str) as clip:
                total_duration = float(clip.duration)
        except Exception as e:
            print(f"Error reading video duration: {e}")
            total_duration = 0.0

        # [Whisper 실행] 비디오 인코딩 없이 오디오만 내부 추출하여 빠르게 분석
        # write_videofile이나 오디오 변환 과정 없음
        result = self.transcribe(path_str, language=language)
        segments = result.get("segments", [])

        # 3. 트리거 찾기 (텍스트 분석)
        all_trigger_segments = self.find_trigger_segments(segments, triggers=triggers)
        
        # 4. 목소리 분석 (시뮬레이션)
        speakers_summary, speaker_segments = self._detect_speakers(total_duration)
        
        # 5. 구간 계산
        valid_clips = self.calculate_intervals(all_trigger_segments, total_duration, include_trigger)
                
        return valid_clips, total_duration, all_trigger_segments, speakers_summary, speaker_segments

    def export_with_intervals(
        self,
        video_path: str | Path,
        output_path: str | Path,
        intervals: List[Tuple[float, float]],
        crossfade: float = 0.2,
        min_segment_duration: float = 0.5,
        fps: Optional[int] = None,
        codec: str = "libx264", # 기본값은 유지하되 내부에서 무시하거나 재설정
        audio_codec: str = "aac",
    ) -> Optional[Path]:
        if not intervals: return None
        path_str = str(video_path)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        try:
            # [Smart Rendering Logic]
            # 만약 crossfade가 0이고, 코덱 변환이 필요 없다면 스트림 복사(Copy Stream) 시도
            # 이는 인코딩을 아예 하지 않으므로 속도가 수십 배 빠름
            # 단, 키프레임 문제로 정확한 컷이 안 될 수 있어 제한적으로 사용
            use_smart_rendering = (crossfade <= 0)
            
            if use_smart_rendering:
                print("⚡ 스마트 렌더링(Stream Copy) 시도 중... (초고속 모드)")
                try:
                    import subprocess
                    
                    # ffmpeg filter_complex를 사용하여 스트림 복사 시도
                    # concat demuxer 사용을 위해 임시 파일 목록 생성
                    temp_list_path = output.with_suffix('.txt')
                    with open(temp_list_path, 'w', encoding='utf-8') as f:
                        for start, end in intervals:
                            if end - start < min_segment_duration: continue
                            # inpoint/outpoint 사용
                            f.write(f"file '{path_str.replace(os.sep, '/')}'\n")
                            f.write(f"inpoint {start}\n")
                            f.write(f"outpoint {end}\n")
                    
                    # ffmpeg concat 실행
                    cmd = [
                        imageio_ffmpeg.get_ffmpeg_exe(),
                        "-f", "concat",
                        "-safe", "0",
                        "-i", str(temp_list_path),
                        "-c", "copy",  # 핵심: 인코딩 없이 복사
                        "-y",
                        str(output)
                    ]
                    
                    subprocess.run(cmd, check=True, capture_output=True)
                    os.remove(temp_list_path)
                    print("✅ 스마트 렌더링 성공!")
                    return output
                    
                except Exception as e:
                    print(f"⚠️ 스마트 렌더링 실패 (재인코딩으로 전환): {e}")
                    if 'temp_list_path' in locals() and os.path.exists(temp_list_path):
                        os.remove(temp_list_path)

            # [Standard Rendering with Hardware Acceleration]
            with VideoFileClip(path_str) as clip:
                child_clips = []
                for start, end in intervals:
                    duration = end - start
                    if duration < min_segment_duration: continue
                    
                    subclip = clip.subclip(start, end)
                    if crossfade > 0:
                        subclip = subclip.audio_fadein(crossfade).audio_fadeout(crossfade)
                    child_clips.append(subclip)

                if not child_clips: return None

                final_clip = concatenate_videoclips(child_clips, method="compose", padding=-crossfade)
                
                # [1단계] GPU 가속 시도 (NVIDIA NVENC)
                print("🚀 GPU 가속 인코딩 시도 중... (h264_nvenc)")
                try:
                    final_clip.write_videofile(
                        str(output),
                        codec="h264_nvenc",     # GPU 코덱
                        audio_codec=audio_codec,
                        fps=fps or 24,
                        preset="p1",            # 가장 빠름
                        threads=8,
                        ffmpeg_params=["-rc", "constqp", "-qp", "23"],
                        logger="bar"
                    )
                except Exception as e1:
                    print(f"⚠️ NVENC 인코딩 실패: {e1}")
                    
                    # [2단계] Intel QuickSync (QSV) 시도
                    print("🚀 Intel QSV 가속 인코딩 시도 중... (h264_qsv)")
                    try:
                        final_clip.write_videofile(
                            str(output),
                            codec="h264_qsv",
                            audio_codec=audio_codec,
                            fps=fps or 24,
                            preset="veryfast",
                            threads=8,
                            ffmpeg_params=["-global_quality", "23"],
                            logger="bar"
                        )
                    except Exception as e2:
                        print(f"⚠️ QSV 인코딩 실패: {e2}")
                        
                        # [3단계] AMD AMF 시도
                        print("🚀 AMD AMF 가속 인코딩 시도 중... (h264_amf)")
                        try:
                            final_clip.write_videofile(
                                str(output),
                                codec="h264_amf",
                                audio_codec=audio_codec,
                                fps=fps or 24,
                                preset="speed",
                                threads=8,
                                logger="bar"
                            )
                        except Exception as e3:
                            print(f"⚠️ AMF 인코딩 실패: {e3}")
                            
                            # [4단계] CPU 초고속 모드 (Fallback)
                            print("🐢 CPU 인코딩으로 전환합니다. (libx264 ultrafast)")
                            final_clip.write_videofile(
                                str(output),
                                codec="libx264",
                                audio_codec=audio_codec,
                                fps=fps or 24,
                                preset="ultrafast",     # CPU 최고 속도
                                threads=os.cpu_count() or 4, # 가용 스레드 최대 활용
                                ffmpeg_params=["-crf", "28", "-tune", "zerolatency"], # crf 28로 속도 우선
                                logger="bar"
                            )
                    
                final_clip.close()
                
            return output
            
        except Exception as e:
            print(f"Export failed: {e}")
            return None
