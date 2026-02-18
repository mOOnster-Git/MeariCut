import sys
import os

# Debug logging removed

# 직접 실행 시 프로젝트 루트 경로 추가 (core 모듈 import 위해)
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 환경 변수 설정 (main.py와 동일하게)
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    os.environ["OMP_NUM_THREADS"] = "1"

# version.py import
try:
    import version
except ImportError:
    # 실행 경로 문제로 import 실패 시 path 추가 후 재시도
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import version

from pathlib import Path
from datetime import datetime

def resource_path(relative_path: str) -> str:
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal, QTimer, QEvent, QSize, QRect
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont, QPixmap, QMouseEvent
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QSlider,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QCheckBox,
    QRadioButton,
    QFrame,
    QFileDialog,
    QMessageBox,
    QGraphicsOpacityEffect,
    QStyle,
    QLineEdit,
    QApplication,
    QTextEdit,
    QPlainTextEdit,
    QSizePolicy,
    QDialog,
    QTabWidget,
)

class VideoControlsOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 반투명 배경 패널
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.5);
                border-radius: 20px;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
            }
        """)
        
        # Play Button
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.play_btn.setIconSize(QSize(24, 24))
        self.play_btn.setFixedSize(30, 30)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.setToolTip("재생")
        
        # Pause Button
        self.pause_btn = QPushButton()
        self.pause_btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        self.pause_btn.setIconSize(QSize(24, 24))
        self.pause_btn.setFixedSize(30, 30)
        self.pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pause_btn.setToolTip("일시정지")
        
        layout.addWidget(self.play_btn)
        layout.addWidget(self.pause_btn)
        
        self.hide()

class ClickableVideoWidget(QVideoWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.overlay = None

    def set_overlay(self, overlay):
        self.overlay = overlay
        if self.overlay:
            self.overlay.setParent(self)
            self.overlay.hide()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event):
        if self.overlay:
            self.overlay.show()
            self._update_overlay_pos()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.overlay:
            # 마우스가 오버레이 위로 이동했을 때도 leaveEvent가 발생할 수 있음
            # 오버레이가 자식 위젯이므로 괜찮을 수 있지만, 안전하게 처리
            self.overlay.hide()
        super().leaveEvent(event)

    def resizeEvent(self, event):
        if self.overlay:
            self._update_overlay_pos()
        super().resizeEvent(event)

    def _update_overlay_pos(self):
        if self.overlay:
            # 중앙 하단에 배치
            ow = self.overlay.sizeHint().width() + 20
            oh = 50
            self.overlay.resize(ow, oh)
            
            x = (self.width() - ow) // 2
            y = self.height() - oh - 30 # 하단에서 30px 위
            self.overlay.move(x, y)
            self.overlay.raise_()

import traceback
import math
import version

# 직접 실행 시 프로젝트 루트 경로 추가 (core 모듈 import 위해)
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # 환경 변수 설정 (main.py와 동일하게)
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    os.environ["OMP_NUM_THREADS"] = "1"

from core.processor import MeariProcessor

class LoadingOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.msg_label = QLabel("처리 중...", self)
        self.msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.msg_label)

        # 간단한 로딩 애니메이션을 위한 타이머
        self.angle = 0
        self.dot_count = 0
        self.base_msg = ""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        
    def show_message(self, msg: str) -> None:
        self.base_msg = msg
        # 초기 텍스트에도 줄바꿈 적용 (애니메이션 시작 전 텍스트 튐 방지)
        self.msg_label.setText(f"{msg}\n")
        self.angle = 0
        self.dot_count = 0
        self.timer.start(50)
        
        # 부모 위젯 크기에 맞춤
        if self.parent():
            self.resize(self.parent().size())
            
        self.show()
        self.raise_() # 최상단으로 올리기


    def hide_overlay(self) -> None:
        self.timer.stop()
        self.hide()

    def update_animation(self) -> None:
        self.angle = (self.angle + 10) % 360
        
        # 텍스트 애니메이션 (0.5초마다 점 개수 변경)
        if self.angle % 100 == 0:  # 50ms * 10 = 500ms
            self.dot_count = (self.dot_count + 1) % 4
            dots = "." * self.dot_count
            self.msg_label.setText(f"{self.base_msg}\n{dots}")
            
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 반투명 배경 (더 어둡게)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 180))
        
        # 스피너 그리기 (화면 높이의 20% 지름)
        radius = int(self.height() * 0.1)
        if radius < 30:
            radius = 30
            
        center_x = self.width() // 2
        # 텍스트와 겹치지 않도록 위로 올림
        center_y = self.height() // 2 - radius - 40 
        
        painter.translate(center_x, center_y)
        painter.rotate(self.angle)
        
        pen = QPen(QColor("#00C7AE"), 6) # 두께도 살짝 키움
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        painter.drawArc(-radius, -radius, radius*2, radius*2, 0, 270 * 16)


class RightPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.init_ui()

    def init_ui(self) -> None:
        # 우측 패널 전체 폰트 사이즈 축소 (12px -> 11px)
        self.setStyleSheet("font-size: 11px;")

        # 2. 단일 레이아웃: 전체 패널을 하나의 QVBoxLayout으로 관리
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. 상단 탭 (트리거, 화자, 볼륨)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #CCCCCC; border-radius: 4px; top: -1px; }
            QTabBar::tab { background: #f0f0f0; color: #666666; border: 1px solid #CCCCCC; padding: 6px 12px; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: white; color: #333333; border-bottom: 1px solid white; font-weight: bold; }
        """)
        
        self.tabs.addTab(self._create_trigger_tab(), "트리거 설정")
        self.tabs.addTab(self._create_speaker_tab(), "목소리 설정")
        self.tabs.addTab(self._create_volume_tab(), "볼륨 설정")
        
        layout.addWidget(self.tabs, 1) # [균형] 상단 탭에 Stretch 1 부여

        # 2. 중간 (탐지된 트리거)
        self.detected_label = self.create_section_label("탐지된 트리거 (0)", layout)
        
        self.detected_list = QListWidget()
        self.detected_list.setObjectName("detectedList")
        layout.addWidget(self.detected_list, 1) # [균형] 하단 리스트에 Stretch 1 부여 (1:1 비율)

        # 3. 하단 (매직 버튼 & 체크박스) - 우측 패널 하단으로 이동
        magic_container = QWidget()
        magic_layout = QVBoxLayout(magic_container)
        magic_layout.setContentsMargins(0, 10, 0, 0)
        magic_layout.setSpacing(8)
        magic_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Magic Button
        self.magic_button = QPushButton()
        self.magic_button.setObjectName("magicButton")
        self.magic_button.setToolTip("AI가 영상을 분석하여 선생님 목소리와 트리거 단어를 자동으로 찾아줍니다.")
        self.magic_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.magic_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.magic_button.setFixedSize(150, 60)
        
        # 내부 레이아웃으로 텍스트 크기 조절 (Magic 크게, mOOnster 작게)
        btn_layout = QVBoxLayout(self.magic_button)
        btn_layout.setContentsMargins(0, 8, 0, 8)
        btn_layout.setSpacing(0)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        lbl_magic = QLabel("Magic")
        lbl_magic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_magic.setStyleSheet("background: transparent; border: none; color: white; font-size: 18px; font-weight: 900; font-family: 'Segoe UI Black', sans-serif;")
        
        lbl_monster = QLabel("mOOnster")
        lbl_monster.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_monster.setStyleSheet("background: transparent; border: none; color: rgba(255,255,255,0.9); font-size: 10px; font-weight: bold; margin-top: -2px;")
        
        btn_layout.addWidget(lbl_magic)
        btn_layout.addWidget(lbl_monster)
        
        magic_layout.addWidget(self.magic_button, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(magic_container)



    def _create_trigger_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 라디오 버튼 (체크박스)
        chk_layout = QHBoxLayout()
        chk_layout.setSpacing(12)
        
        self.chk_start = QCheckBox("시작")
        self.chk_one_two_three = QCheckBox("하나둘셋")
        self.chk_two_three = QCheckBox("둘셋")
        
        self.chk_start.setChecked(True)
        self.chk_one_two_three.setChecked(True)
        self.chk_two_three.setChecked(True)

        chk_layout.addWidget(self.chk_start)
        chk_layout.addWidget(self.chk_one_two_three)
        chk_layout.addWidget(self.chk_two_three)
        layout.addLayout(chk_layout)

        # 입력창 + 추가 버튼
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.trigger_input = QLineEdit()
        self.trigger_input.setPlaceholderText("예: 생일축하해")
        self.trigger_input.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)
        self.trigger_input.focusInEvent = self._on_trigger_input_focus_in
        
        self.add_trigger_btn = QPushButton("추가")
        self.add_trigger_btn.setMinimumWidth(60)
        self.add_trigger_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        input_layout.addWidget(self.trigger_input)
        input_layout.addWidget(self.add_trigger_btn)
        layout.addLayout(input_layout)

        # 커스텀 트리거 목록
        self.custom_trigger_list = QListWidget()
        self.custom_trigger_list.setObjectName("customTriggerList")
        # 탭 내부이므로 높이 제한을 좀 더 유연하게 하거나 그대로 유지
        self.custom_trigger_list.setAlternatingRowColors(True)
        layout.addWidget(self.custom_trigger_list, 1) # 탭 내부에서 남은 공간 차지
        
        # Checkbox (기존 결과 유지) - 하단으로 이동
        self.chk_reanalyze = QCheckBox("기존 결과 유지")
        self.chk_reanalyze.setToolTip("기존에 찾은 결과를 지우지 않고, 새로운 결과를 추가합니다.")
        layout.addWidget(self.chk_reanalyze)

        return tab

    def _create_speaker_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        
        label = QLabel("선생님 목소리를 찾아 선택해주세요.")
        label.setStyleSheet("color: #666666; font-size: 12px; margin-bottom: 5px;")
        layout.addWidget(label)

        self.speaker_list = QListWidget()
        self.speaker_list.setObjectName("speakerList")
        self.speaker_list.setStyleSheet("""
            QListWidget { border: 1px solid #CCCCCC; border-radius: 4px; padding: 2px; }
            QListWidget::item { border-bottom: 1px solid #EEEEEE; padding: 4px; }
            QListWidget::item:hover { background-color: #f0f0f0; }
            QListWidget::item:selected { background-color: #E0F2F1; color: #009688; }
        """)
        layout.addWidget(self.speaker_list, 1)
        
        return tab

    def _create_volume_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        label = QLabel("기본 볼륨 설정")
        layout.addWidget(label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        layout.addWidget(self.volume_slider)

        # [추가] 인코딩 영향 설명
        desc_label = QLabel("이 설정은 저장되는 영상의 소리 크기에\n직접적인 영향을 줍니다.")
        desc_label.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: 5px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        return tab

    def _on_trigger_input_focus_in(self, event):
        """트리거 입력창 포커스 시 한글 입력 모드로 전환 (Windows 전용)"""
        # 기본 동작 수행
        QLineEdit.focusInEvent(self.trigger_input, event)
        
        # [Fix] winId() 호출로 인한 네이티브 위젯 변환이 비디오 재생(QVideoWidget)과 충돌하여
        # 화면이 검게 변하는 현상이 발생함. IME 자동 전환 기능을 비활성화하여 문제 해결.
        
        # try:
        #     import ctypes
        #     # Windows IMM32 API 사용
        #     imm32 = ctypes.windll.imm32
        #     hwnd = self.trigger_input.winId()
        #     hime = imm32.ImmGetContext(hwnd)
        #     
        #     if hime:
        #         # IME_CMODE_NATIVE (0x0001) | IME_CMODE_HANGUL (0x0001)
        #         # IME 활성화 (OpenStatus)
        #         imm32.ImmSetOpenStatus(hime, 1)
        #         # 한글 모드로 설정 (1)
        #         imm32.ImmSetConversionStatus(hime, 1, 0)
        #         imm32.ImmReleaseContext(hwnd, hime)
        # except Exception:
        #     pass # Windows가 아니거나 오류 발생 시 무시

    def create_section_label(self, text: str, layout: QVBoxLayout) -> QLabel:
        label = QLabel(text)
        # 3. 섹션 구분: '굵은 폰트(Bold)의 QLabel 제목'
        label.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #333333;
            margin-bottom: 4px;
            margin-top: 4px;
        """)
        layout.addWidget(label)
        return label


class TimelineWidget(QWidget):
    seek_requested = pyqtSignal(float)
    intervals_updated = pyqtSignal(list)
    trigger_clicked = pyqtSignal(int) # 트리거 클릭 시그널 (original_index 전달)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(100)
        self.setObjectName("timelineWidget")
        self.total_duration = 0.0
        self.cut_intervals: list[dict] = [] # 삭제할 구간 목록 (트리거 등)
        self.current_position = 0.0
        # 초기 상태(빈 타임라인)에서는 손 모양 커서
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 드래그 선택 상태 (삭제 구간 생성용)
        self.drag_start_x: int | None = None
        self.drag_current_x: int | None = None
        self.is_dragging = False

    def update_intervals(
        self,
        total_duration: float,
        intervals: list[dict],
    ) -> None:
        """
        타임라인 데이터를 업데이트합니다.
        :param total_duration: 전체 영상 길이 (초)
        :param intervals: 삭제할 구간(트리거) 목록. 각 항목은 dict 형태 ({'start': s, 'end': e, 'status': ...})
        """
        self.total_duration = total_duration
        self.cut_intervals = intervals
        
        # 파일 유무에 따라 커서 모양 변경
        if self.total_duration <= 0:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
        self.update()
        # 데이터가 변경되었으므로 보존 구간(Keep)을 계산하여 시그널 발생
        self._emit_keep_intervals()

    def update_triggers(self, triggers: list[dict]) -> None:
        """
        트리거 목록을 업데이트합니다.
        기존의 'manual' (수동 삭제) 구간은 유지하고, 트리거 구간만 교체합니다.
        """
        # 기존 수동 삭제 구간 유지
        manual_cuts = [c for c in self.cut_intervals if c.get("status") == "manual"]
        
        # 새 트리거와 병합
        new_intervals = manual_cuts + triggers
        
        self.update_intervals(self.total_duration, new_intervals)

    def set_position(self, position: float) -> None:
        self.current_position = position
        self.update()

    def _get_time_from_x(self, x: int) -> float:
        width = self.width()
        margin_x = 20
        bar_width = width - margin_x * 2
        if bar_width <= 0 or self.total_duration <= 0:
            return 0.0
        
        ratio = (x - margin_x) / bar_width
        ratio = max(0.0, min(1.0, ratio))
        return ratio * self.total_duration

    def _calculate_keep_intervals(self) -> list[tuple[float, float]]:
        """
        전체 구간에서 cut_intervals(삭제 구간)를 뺀 나머지(보존 구간)를 계산합니다.
        status가 'candidate'인 구간은 삭제하지 않고 보존합니다.
        """
        if self.total_duration <= 0:
            return []
            
        # 삭제할 구간만 필터링 (candidate 제외)
        real_cuts = [c for c in self.cut_intervals if c.get("status") != "candidate"]
            
        # 삭제 구간 정렬 및 병합
        cuts = sorted(real_cuts, key=lambda x: x.get("start", 0.0))
        merged_cuts = []
        if cuts:
            curr_start = float(cuts[0].get("start", 0.0))
            curr_end = float(cuts[0].get("end", 0.0))
            
            for i in range(1, len(cuts)):
                next_start = float(cuts[i].get("start", 0.0))
                next_end = float(cuts[i].get("end", 0.0))
                
                if next_start < curr_end: # 겹치거나 붙어있음
                    curr_end = max(curr_end, next_end)
                else:
                    merged_cuts.append((curr_start, curr_end))
                    curr_start = next_start
                    curr_end = next_end
            merged_cuts.append((curr_start, curr_end))
            
        # 보존 구간 계산 (전체 - 삭제)
        keep = []
        last_end = 0.0
        
        for start, end in merged_cuts:
            # 유효 범위 클램핑
            start = max(0.0, min(start, self.total_duration))
            end = max(0.0, min(end, self.total_duration))
            
            if start > last_end:
                keep.append((last_end, start))
            last_end = max(last_end, end)
            
        if last_end < self.total_duration:
            keep.append((last_end, self.total_duration))
            
        return keep

    def _emit_keep_intervals(self) -> None:
        keep = self._calculate_keep_intervals()
        self.intervals_updated.emit(keep)

    def mousePressEvent(self, event) -> None:
        if self.total_duration <= 0:
            # [추가] 파일이 없을 때 클릭하면 -> 파일 열기 실행
            main_window = self.window()
            if hasattr(main_window, 'open_file'):
                main_window.open_file()
            elif hasattr(main_window, '_on_open_clicked'):
                 main_window._on_open_clicked()
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Ctrl + 클릭: 드래그 모드 시작 (삭제 구간 생성)
                self.is_dragging = True
                self.drag_start_x = event.pos().x()
                self.drag_current_x = event.pos().x()
                self.update()
            else:
                # 일반 클릭: 탐색(Seek)
                target_time = self._get_time_from_x(event.pos().x())
                self.seek_requested.emit(target_time)
                
        elif event.button() == Qt.MouseButton.RightButton:
            # 우클릭: 구간 속성 토글 (삭제 <-> 보존)
            target_time = self._get_time_from_x(event.pos().x())
            self._toggle_interval_at(target_time)

    def mouseMoveEvent(self, event) -> None:
        if self.is_dragging:
            self.drag_current_x = event.pos().x()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self.is_dragging and event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
            start_x = self.drag_start_x
            end_x = event.pos().x()
            self.drag_start_x = None
            self.drag_current_x = None


            # 너무 짧은 드래그는 무시 (실수 방지)
            if abs(end_x - start_x) < 5:
                self.update()
                return
                
            start_time = self._get_time_from_x(min(start_x, end_x))
            end_time = self._get_time_from_x(max(start_x, end_x))
            
            # 선택된 구간을 '삭제' 처리 (cut_intervals에 추가)
            self._add_cut_range(start_time, end_time)
            self.update()

    def _add_cut_range(self, start: float, end: float) -> None:
        # 새로운 삭제 구간 추가 (수동)
        new_cut = {
            "start": start,
            "end": end,
            "status": "manual", # 수동 삭제
            "confidence": 1.0,
            "word": "Manual"
        }
        self.cut_intervals.append(new_cut)
        self._emit_keep_intervals()

    def _toggle_interval_at(self, time: float) -> None:
        # 클릭한 위치가 삭제 구간(cut_intervals) 내부인지 확인
        hit_index = -1
        hit_item = None
        
        # cut_intervals 순회
        for i, item in enumerate(self.cut_intervals):
            start = item.get("start", 0.0)
            end = item.get("end", 0.0)
            if start <= time <= end:
                hit_index = i
                hit_item = item
                break
        
        if hit_index != -1:
            # [수정] 트리거(original_index 보유)인 경우 -> 메인 윈도우에 토글 요청
            # (체크 상태 변경은 메인 윈도우가 처리하고, 다시 타임라인 업데이트)
            if "original_index" in hit_item:
                self.trigger_clicked.emit(hit_item["original_index"])
                return

            # [기존] 수동 삭제 구간(manual) -> 삭제
            del self.cut_intervals[hit_index]
        else:
            # 보존 구간(Green) 클릭 -> 삭제 (어떻게? 전체를 삭제? 아니면 작은 구간?)
            # 보통 이런 경우 '분할'하거나 그래야 하는데, 여기서는 
            # "이 지점을 포함하는 보존 구간을 삭제" 하기엔 너무 큼.
            # MeariCut의 UX상, 우클릭으로 삭제 구간을 만드는 건 애매함.
            # 하지만 기존 로직(_toggle_interval_at)은 갭을 채우거나 갭을 만드는 로직이었음.
            # 여기서는 간단히: 클릭 지점 주변 1초를 삭제 구간으로 설정? 
            # 아니면 사용자 혼란 방지를 위해 '삭제된 구간 복구'만 허용?
            
            # 기존 로직: "삭제 구간(Red/빈 공간) 클릭 -> 보존 (구간 추가 및 병합)"
            # 즉, Red를 클릭하면 Green이 됨. (삭제 취소)
            # Green을 클릭하면 Red가 됨. (삭제)
            
            # 여기서는 Green 위를 클릭했으므로, 해당 지점을 삭제해야 함.
            # 하지만 범위가 모호하므로, 드래그를 권장하거나 기본값(1초) 적용
            self._add_cut_range(time - 0.5, time + 0.5)
            
        self._emit_keep_intervals()
        self.update()

    def paintEvent(self, event) -> None:
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            width = self.width()
            height = self.height()
            margin_x = 20
            margin_y = 10
            timeline_height = 40
            
            # 배경 (타임라인 바)
            bar_rect_y = margin_y
            bar_rect_h = timeline_height
            
            painter.setBrush(QBrush(QColor("#F0F0F0"))) # 연한 회색 배경
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(margin_x, bar_rect_y, width - margin_x*2, bar_rect_h, 10, 10) # 둥근 모서리

            if self.total_duration <= 0:
                # [고대비 모드] 파일 없을 때 빈 타임라인 시각화
                rect = QRect(margin_x, bar_rect_y, width - margin_x*2, bar_rect_h)

                # 1. 배경 박스 (진하게)
                painter.setBrush(QBrush(QColor("#E0E0E0"))) # 진한 회색
                painter.setPen(QPen(QColor("#BDBDBD"), 2))  # 테두리
                painter.drawRoundedRect(rect, 8, 8)

                # 2. 안내 문구 (박스 정중앙)
                # 텍스트가 눈금과 겹치지 않도록 중앙 배치
                painter.setPen(QPen(QColor("#424242"))) # 진한 텍스트
                painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold)) 
                text = "파일을 열어 타임라인을 확인하세요"
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

                # 3. 눈금 (박스 하단에 붙여서)
                # 위로 솟아오르는 형태, 높이를 일정하게 하여 정돈된 느낌
                painter.setPen(QPen(QColor("#9E9E9E"), 2)) # 눈금 색상
                bar_width = width - margin_x * 2
                
                if bar_width > 0:
                    bottom_y = bar_rect_y + bar_rect_h
                    for i in range(1, 25): # 1부터 24까지 (양끝 제외)
                        x = int(margin_x + (bar_width * (i / 25.0)))
                        h = 6 # 일정한 높이
                        painter.drawLine(x, bottom_y, x, bottom_y - h)
                return

            # 구간 그리기
            bar_width = width - margin_x * 2
            if bar_width <= 0:
                return

            # 1. 기본 배경: 전체를 '보존(Green)'으로 칠함
            painter.setBrush(QBrush(QColor("#80CBC4"))) # 보존 (Pastel Green)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(margin_x, bar_rect_y, bar_width, bar_rect_h, 4, 4)

            # 2. 삭제 구간(Cut Intervals) 그리기 (Red/Yellow)
            # cut_intervals: [{'start':..., 'end':..., 'status':...}, ...]
            for item in self.cut_intervals:
                t_start = item.get("start", 0.0)
                t_end = item.get("end", 0.0)
                status = item.get("status", "confirmed")

                # 유효 범위 체크 및 클램핑
                t_start = max(0.0, min(t_start, self.total_duration))
                t_end = max(0.0, min(t_end, self.total_duration))

                if t_end <= t_start:
                    continue

                start_ratio = t_start / self.total_duration
                end_ratio = t_end / self.total_duration
                
                x = int(margin_x + bar_width * start_ratio)
                w = int(bar_width * (end_ratio - start_ratio))
                
                if w <= 0: continue
                
                # 색상 결정
                if status == "candidate":
                    color = QColor(255, 234, 0) # Yellow (Material Yellow A400)
                else:
                    # confirmed, manual 등은 Red
                    color = QColor(255, 82, 82) # Red (Material Red 400)
                
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.PenStyle.NoPen)
                
                # 삭제 구간 그리기
                painter.drawRoundedRect(x, bar_rect_y, w, bar_rect_h, 4, 4)

            # 드래그 선택 영역 그리기 (반투명 빨강)
            if self.is_dragging and self.drag_start_x is not None and self.drag_current_x is not None:
                dx = min(self.drag_start_x, self.drag_current_x)
                dw = abs(self.drag_current_x - self.drag_start_x)
                
                painter.setBrush(QBrush(QColor(255, 100, 100, 100))) # 반투명 파스텔 빨강
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(dx, bar_rect_y, dw, bar_rect_h, 4, 4)

            # 시간 눈금 그리기
            painter.setPen(QPen(QColor("#333333"), 2))
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            
            # 동적 눈금 간격 계산 (픽셀 단위 밀집도 방지)
            pixels_per_sec = bar_width / self.total_duration
            min_tick_spacing_px = 6  # 최소 눈금 간격 (픽셀)
            
            if pixels_per_sec > 0:
                min_time_step = min_tick_spacing_px / pixels_per_sec
            else:
                min_time_step = 1.0

            # 후보 스텝 (초 단위)
            candidates = [1, 5, 10, 30, 60, 300, 600, 1800, 3600]
            
            minor_step = candidates[-1]
            for step in candidates:
                if step >= min_time_step:
                    minor_step = step
                    break
            
            # 메이저 스텝 결정
            if minor_step == 1: major_step = 5.0
            elif minor_step == 5: major_step = 30.0
            elif minor_step == 10: major_step = 60.0
            elif minor_step == 30: major_step = 300.0 # 5분
            elif minor_step == 60: major_step = 300.0 # 5분
            elif minor_step == 300: major_step = 1800.0 # 30분
            elif minor_step == 600: major_step = 3600.0 # 1시간
            else: major_step = minor_step * 5.0

            # 눈금 그리기
            tick_y_start = bar_rect_y + bar_rect_h
            major_tick_y_end = tick_y_start + 8
            minor_tick_y_end = tick_y_start + 4
            text_y = major_tick_y_end + 12
            
            t = 0.0
            max_ticks = 5000 # 안전장치: 최대 눈금 개수 제한
            tick_count = 0
            
            while t <= self.total_duration + 0.1: # float 오차 보정
                tick_count += 1
                if tick_count > max_ticks:
                    break
                    
                ratio = t / self.total_duration
                if ratio > 1.0: break
                
                x = int(margin_x + bar_width * ratio)
                
                is_major = (abs(t % major_step) < 0.001) or (abs(t - self.total_duration) < 0.001)
                
                if is_major:
                    # 메이저 눈금
                    painter.setPen(QPen(QColor("#333333"), 2))
                    painter.drawLine(x, tick_y_start, x, major_tick_y_end)
                    
                    # 시간 텍스트
                    minutes = int(t // 60)
                    seconds = int(t % 60)
                    time_str = f"{minutes:02d}:{seconds:02d}"
                    
                    text_rect = painter.fontMetrics().boundingRect(time_str)
                    painter.drawText(x - text_rect.width() // 2, text_y, time_str)
                else:
                    # 마이너 눈금
                    painter.setPen(QPen(QColor("#999999"), 1))
                    painter.drawLine(x, tick_y_start, x, minor_tick_y_end)
                
                t += minor_step
            
            # 마지막 100% 눈금과 시간 표시 (강제)
            if self.total_duration > 0:
                x_end = margin_x + bar_width
                painter.setPen(QPen(QColor("#333333"), 2))
                painter.drawLine(x_end, tick_y_start, x_end, major_tick_y_end)
                
                end_minutes = int(self.total_duration // 60)
                end_seconds = int(self.total_duration % 60)
                end_time_str = f"{end_minutes:02d}:{end_seconds:02d}"
                
                end_text_rect = painter.fontMetrics().boundingRect(end_time_str)
                painter.drawText(x_end - end_text_rect.width() // 2, text_y, end_time_str)

            # 현재 재생 위치 (Playhead) 그리기
            current_ratio = self.current_position / self.total_duration
            playhead_x = int(margin_x + bar_width * current_ratio)
            
            # 빨간색 세로선
            painter.setPen(QPen(QColor("#FF0000"), 2))
            painter.drawLine(playhead_x, bar_rect_y - 5, playhead_x, bar_rect_y + bar_rect_h + 5)
            
            # 상단 원형 핸들
            painter.setBrush(QBrush(QColor("#FF0000")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(playhead_x - 4, bar_rect_y - 12, 8, 8)
            
        except Exception as e:
            # 드로잉 중 오류가 발생해도 프로그램이 죽지 않도록 처리
            print(f"PaintEvent Error: {e}")


class AnalyzeThread(QThread):
    finished = pyqtSignal(list, float, list, list, list)
    error = pyqtSignal(str)

    def __init__(
        self,
        video_path: Path,
        triggers: list[str],
        include_trigger: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.video_path = video_path
        self.triggers = triggers
        self.include_trigger = include_trigger

    def run(self) -> None:
        try:
            processor = MeariProcessor(triggers=self.triggers)
            intervals, total_duration, triggers, speakers, speaker_segments = processor.analyze_video(
                self.video_path,
                include_trigger=self.include_trigger
            )
            self.finished.emit(intervals, total_duration, triggers, speakers, speaker_segments)
        except Exception as e:
            traceback.print_exc()
            self.error.emit(str(e))


class SaveThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(
        self,
        processor: MeariProcessor,
        video_path: Path,
        output_path: Path,
        intervals: list[tuple[float, float]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.processor = processor
        self.video_path = video_path
        self.output_path = output_path
        self.intervals = intervals

    def run(self) -> None:
        try:
            result = self.processor.export_with_intervals(
                self.video_path,
                self.output_path,
                self.intervals,
            )
            if result:
                self.finished.emit(True, str(result))
            else:
                self.finished.emit(False, "저장된 파일이 없습니다.")
        except Exception as e:
            traceback.print_exc()
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        # 프로그램 버전 정보 (version.py 연동)
        self.program_version = f"v{version.VERSION}"
        
        self.setWindowTitle(f"MeariCut {self.program_version}")
        self.resize(880, 670)  # 초기 크기 설정 (880x670)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self.current_video_path: Path | None = None
        self.analyzed_intervals: list[tuple[float, float]] = []
        self.total_duration: float = 0.0
        self.analysis_thread: AnalyzeThread | None = None
        self.save_thread: SaveThread | None = None

        self._setup_ui()
        self._apply_styles()

        # 전역 이벤트 필터 설치 (스페이스바 처리용)
        QApplication.instance().installEventFilter(self)

        # 타임라인 및 비디오 플레이어 시그널 연결
        self.player.positionChanged.connect(self._on_video_position_changed)
        self.player.durationChanged.connect(self._on_video_duration_changed)
        self.timeline.seek_requested.connect(self._on_timeline_seek)
        self.timeline.intervals_updated.connect(self._on_intervals_updated)
        
        # 윈도우 활성화 및 최상단 이동 (실행 시 사용자에게 바로 보이도록)
        self.show()
        self.activateWindow()
        self.raise_()

    def resizeEvent(self, event) -> None:
        if hasattr(self, "loading_overlay") and self.loading_overlay:
            self.loading_overlay.resize(self.size())
            self.loading_overlay.raise_()
        super().resizeEvent(event)

    def _setup_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)

        center_layout = QHBoxLayout()
        center_layout.setSpacing(8)
        main_layout.addLayout(center_layout, 1)

        left_panel = self._create_left_panel()
        center_layout.addWidget(left_panel, 3)

        right_panel = self._create_right_panel()
        center_layout.addWidget(right_panel, 2)

        self.timeline = TimelineWidget(self)
        self.timeline.trigger_clicked.connect(self._on_timeline_trigger_clicked)
        main_layout.addWidget(self.timeline)

        # 타임라인 하단 영역
        bottom_info_layout = QHBoxLayout()
        bottom_info_layout.setContentsMargins(10, 0, 10, 0)
        
        # 가이드 텍스트 (좌측 하단 복구)
        guide_label = QLabel()
        guide_label.setTextFormat(Qt.TextFormat.RichText)
        guide_label.setStyleSheet("font-size: 11px; color: #555;")
        guide_text = """
        <span style='color:#FF5252;'>●</span> 삭제 
        <span style='color:#FFEA00;'>●</span> 후보 &nbsp;|&nbsp; 
        좌클릭:이동, Ctrl+드래그:구간설정 &nbsp;|&nbsp; 우클릭:선택/해제
        """
        guide_label.setText(guide_text)
        bottom_info_layout.addWidget(guide_label)

        bottom_info_layout.addStretch(1)

        # 2. 제작자 크레딧 및 후원 버튼 (우측 하단)
        right_info_container = QWidget()
        right_info_layout = QHBoxLayout(right_info_container) # [수정] 가로 배치로 변경
        right_info_layout.setContentsMargins(0, 0, 0, 0)
        right_info_layout.setSpacing(8)
        right_info_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        
        # 제작자 크레딧 (왼쪽 배치)
        credit_label = QLabel("제작자: mOOnster")
        credit_label.setStyleSheet("color: #999999; font-size: 11px; margin-right: 4px;")
        credit_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        right_info_layout.addWidget(credit_label)

        # 후원 버튼
        self.toss_btn = QPushButton("Toss 후원")
        self.toss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toss_btn.setFixedSize(72, 22) # [수정] 사이즈 조정 (80x24 -> 72x22)
        self.toss_btn.setStyleSheet("""
            QPushButton {
                background-color: #0064FF; color: white; border: none; border-radius: 4px;
                font-weight: bold; font-family: "Segoe UI", sans-serif; font-size: 10px; /* 폰트 축소 */
                padding: 0px;
            }
            QPushButton:hover { background-color: #0050CC; }
            QPushButton:pressed { background-color: #003C99; }
        """)
        self.toss_btn.clicked.connect(lambda: self._show_qr_popup("Toss 후원", resource_path("toss.png")))

        self.kakao_btn = QPushButton("Kakao 후원")
        self.kakao_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.kakao_btn.setFixedSize(72, 22) # [수정] 사이즈 조정 (80x24 -> 72x22)
        self.kakao_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEE500; color: #191919; border: none; border-radius: 4px;
                font-weight: bold; font-family: "Segoe UI", sans-serif; font-size: 10px; /* 폰트 축소 */
                padding: 0px;
            }
            QPushButton:hover { background-color: #E6CF00; }
            QPushButton:pressed { background-color: #CCB800; }
        """)
        self.kakao_btn.clicked.connect(lambda: self._show_qr_popup("Kakao 후원", resource_path("kakao.png")))
        
        right_info_layout.addWidget(self.toss_btn)
        right_info_layout.addWidget(self.kakao_btn)
        
        bottom_info_layout.addWidget(right_info_container)

        # main_layout의 spacing을 줄여서 타임라인과 하단 정보 사이 간격을 좁힘
        # 기본값 6 -> 2로 조정
        main_layout.addLayout(bottom_info_layout)
        main_layout.setSpacing(2)

        self.loading_overlay = LoadingOverlay(self)

        # 이벤트 필터 설치 (UI 생성 후)
        self.installEventFilter(self)
        if hasattr(self, 'video_widget'):
            self.video_widget.installEventFilter(self)

    def _create_top_bar(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("topBar")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)

        # [좌측] 제목 + 버전 + 설명 컨테이너
        # 1. 제목 + 버전 + 설명 (한 줄로 변경)
        title_container = QWidget(frame)
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # 제목
        self.logo_label = QLabel("메아리컷", title_container)
        self.logo_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50; font-family: 'Segoe UI', sans-serif;")
        
        # 버전 뱃지
        version_label = QLabel(self.program_version, title_container)
        version_label.setStyleSheet("""
            color: #009688;
            font-size: 11px;
            font-weight: bold;
            padding: 0px;
            margin-top: 8px; /* 타이틀 베이스라인과 맞추기 위해 */
        """)
        
        # 설명 (옆으로 이동, 폰트 사이즈 축소 13px -> 11px)
        desc_label = QLabel("선생님 목소리 구간은 덜어내고, 아이들의 영상만 모아 보여줍니다.", title_container)
        desc_label.setStyleSheet("font-size: 11px; color: #7f8c8d; font-family: 'Segoe UI', sans-serif; margin-left: 5px;")

        title_layout.addWidget(self.logo_label)
        title_layout.addWidget(version_label)
        title_layout.addWidget(desc_label)

        # (기존 top_row_widget 및 title_layout의 addWidget 부분은 제거됨)

        layout.addWidget(title_container)
        layout.addStretch(1)

        self.open_button = QPushButton("파일 열기", frame)
        self.open_button.setObjectName("openButton")
        self.open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.save_button = QPushButton("저장", frame)
        self.save_button.setObjectName("saveButton")
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout.addWidget(self.open_button)
        layout.addWidget(self.save_button)

        self.open_button.clicked.connect(self._on_open_clicked)
        self.save_button.clicked.connect(self._on_save_clicked)

        return frame

    def _create_left_panel(self) -> QWidget:
        frame = QFrame(self)
        frame.setObjectName("leftPanel")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        video_container = QFrame(frame)
        video_container.setObjectName("videoContainer")
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)

        self.video_widget = ClickableVideoWidget(video_container)
        self.video_widget.setObjectName("videoWidget")
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.video_widget.clicked.connect(self._toggle_play_pause)
        
        # [수정] 비디오 위젯 초기 크기 고정 및 최소 크기 설정 (레이아웃 흔들림 방지)
        # 16:9 비율 유지 (예: 640x360)
        self.video_widget.setMinimumSize(640, 360)
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # [수정] 비디오 위젯이 숨겨져도(setVisible(False)) 레이아웃 공간을 유지하도록 설정
        # 이렇게 하면 로딩 화면 표시를 위해 비디오를 숨겨도 우측 패널이 늘어나지 않음
        sp = self.video_widget.sizePolicy()
        sp.setRetainSizeWhenHidden(True)
        self.video_widget.setSizePolicy(sp)
        
        video_layout.addWidget(self.video_widget)

        # [수정] 비디오 컨테이너 높이 제한 제거 또는 조정 (고정 크기 확보를 위해)
        # video_container.setMaximumHeight(360) 

        self.player.setVideoOutput(self.video_widget)

        # [추가] 파일명 표시 라벨 (비디오 바로 아래)
        self.filename_label = QLabel("파일 이름", frame)
        self.filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.filename_label.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-top: 5px; margin-bottom: 5px;")
        
        # 비디오 컨테이너에 추가하지 않고, 메인 레이아웃에 추가 (비디오와 컨트롤 사이)
        layout.addWidget(video_container, 1)
        layout.addWidget(self.filename_label)

        # [수정] 컨트롤 패널 제거 및 오버레이 컨트롤 적용
        self.video_overlay = VideoControlsOverlay(self.video_widget)
        self.video_widget.set_overlay(self.video_overlay)
        
        # 오버레이 버튼 연결
        self.video_overlay.play_btn.clicked.connect(self.player.play)
        self.video_overlay.pause_btn.clicked.connect(self.player.pause)

        return frame

    def _create_right_panel(self) -> QWidget:
        # RightPanel 클래스 인스턴스 생성
        self.right_panel = RightPanel(self)
        self.right_panel.setObjectName("rightPanel")

        # --- [멤버 변수 매핑] ---
        # MainWindow의 기존 로직이 self.chk_start 등을 참조하므로,
        # RightPanel의 위젯들을 MainWindow의 멤버 변수로 연결합니다.
        
        # 1. 트리거 단어
        self.chk_start = self.right_panel.chk_start
        self.chk_one_two_three = self.right_panel.chk_one_two_three
        self.chk_two_three = self.right_panel.chk_two_three
        self.trigger_input = self.right_panel.trigger_input
        self.add_trigger_btn = self.right_panel.add_trigger_btn
        self.custom_trigger_list = self.right_panel.custom_trigger_list
        
        # 2. 볼륨
        self.volume_slider = self.right_panel.volume_slider
        
        # 3. 목소리 구분
        self.speaker_list = self.right_panel.speaker_list
        
        # 4. 탐지된 트리거
        self.detected_label = self.right_panel.detected_label
        self.detected_list = self.right_panel.detected_list
        
        # 5. 매직 버튼 및 체크박스 (RightPanel로 이동됨)
        self.magic_button = self.right_panel.magic_button
        self.chk_reanalyze = self.right_panel.chk_reanalyze
        
        # --- [시그널 연결] ---
        # 매직 버튼 연결
        self.magic_button.clicked.connect(self._on_magic_clicked)

        # 기존 _create_sidebar에 있던 연결 로직 복원
        
        # 사용자 정의 트리거 추가
        self.add_trigger_btn.clicked.connect(self._add_custom_trigger)
        self.trigger_input.returnPressed.connect(self._add_custom_trigger)
        
        # 리스트 아이템 더블 클릭 (삭제 등)
        self.custom_trigger_list.itemDoubleClicked.connect(self._on_custom_trigger_double_clicked)
        
        # 볼륨 슬라이더
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        # 초기 볼륨 설정 (70)
        self.audio_output.setVolume(0.7)
        
        return self.right_panel

    # _create_sidebar 메서드는 더 이상 사용하지 않으므로 제거하거나 주석 처리
    # (여기서는 코드가 깔끔해지도록 제거하고 _create_sidebar를 호출하던 부분을 위에서 수정했음)

    def _add_speaker_item(self, text: str, checked: bool, speaker_id: str) -> None:
        item = QListWidgetItem(self.speaker_list)
        item.setSizeHint(QSize(0, 40)) # 높이 조정 (40px)
        # 화자 ID 저장 (필터링용)
        item.setData(Qt.ItemDataRole.UserRole, speaker_id)
        
        container = QWidget()
        container.setObjectName("speakerItem")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)
        
        # 1. Checkbox
        chk = QCheckBox(container)
        chk.setChecked(checked)
        chk.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        chk.setObjectName("speakerCheckbox")
        
        # 2. Label
        lbl = QLabel(text, container)
        lbl.setStyleSheet("font-size: 12px; color: #333; font-weight: 500; border: none; background: transparent;")
        
        # 3. Preview Button
        btn = QPushButton(container)
        btn.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        btn.setFixedSize(20, 20) # 버튼 크기 축소 (20x20)
        btn.setToolTip("2초 미리듣기")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setObjectName("previewButton")
        # 실제 구현에서는 해당 화자의 첫 발화 구간으로 이동해야 함
        # lambda에 인자를 명시적으로 전달하여 클로저 문제 방지
        btn.clicked.connect(lambda checked=False, s_name=text, s_id=speaker_id: self._on_preview_clicked(s_name, s_id))
        
        layout.addWidget(chk)
        layout.addWidget(lbl, 1) # Stretch
        layout.addWidget(btn)
        
        self.speaker_list.setItemWidget(item, container)
        
        # 초기 스타일 설정
        self._update_speaker_style(container, checked)
        
        # 체크 상태 변경 시 스타일 업데이트
        chk.stateChanged.connect(lambda state: self._update_speaker_style(container, state == 2))
        # 체크 상태 변경 시 트리거 필터링 트리거
        chk.stateChanged.connect(self._on_speaker_selection_changed)

    def _update_speaker_style(self, container: QWidget, checked: bool) -> None:
        if checked:
            container.setStyleSheet("""
                #speakerItem {
                    background-color: #E0F2F1; /* Light Mint */
                    border: 1px solid #B2DFDB;
                    border-radius: 8px;
                }
            """)
        else:
            # 체크 해제 상태: 투명 배경 (QListWidget의 hover 효과가 보이도록)
            container.setStyleSheet("""
                #speakerItem {
                    background-color: transparent;
                    border: none;
                }
            """)

    def _on_preview_clicked(self, speaker_name: str, speaker_id: str) -> None:
        if not self.current_video_path:
            QMessageBox.information(self, "알림", "먼저 동영상 파일을 열어주세요.")
            return
            
        # 목소리 ID를 기반으로 해당 목소리의 첫 발화 구간 찾기
        target_time = 0.0
        found = False
        
        if hasattr(self, 'speaker_segments') and self.speaker_segments:
            # 1. 1초 이상인 구간 중 가장 빠른 구간 찾기
            candidates = [s for s in self.speaker_segments if s.get("speaker_id") == speaker_id]
            if candidates:
                # 시간순 정렬
                candidates.sort(key=lambda x: float(x.get("start", 0)))
                
                # 1초 이상인 첫 번째 구간 우선
                valid_seg = next((s for s in candidates if float(s.get("end", 0)) - float(s.get("start", 0)) >= 1.0), None)
                
                if valid_seg:
                    target_time = float(valid_seg.get("start", 0))
                    found = True
                else:
                    # 없으면 그냥 가장 긴 구간 사용
                    longest_seg = max(candidates, key=lambda x: float(x.get("end", 0)) - float(x.get("start", 0)))
                    target_time = float(longest_seg.get("start", 0))
                    found = True
        
        if not found:
            # 목소리 정보가 없으면 현재 위치에서 재생 (Fallback)
            if hasattr(self, "statusBar") and self.statusBar():
                self.statusBar().showMessage(f"'{speaker_name}'의 발화 구간을 찾을 수 없습니다.", 3000)
            return

        # 해당 위치로 이동 및 재생
        self.player.setPosition(int(target_time * 1000))
        self.player.play()
        
        # 이전 타이머가 있다면 취소 (중복 실행 방지)
        if hasattr(self, "_preview_timer") and self._preview_timer.isActive():
            self._preview_timer.stop()
            
        # 2초 후 일시정지 (QTimer 사용) - 사용자 요청: 2000ms
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self.player.pause)
        self._preview_timer.start(2000)
        
        # 상태바나 로그에 표시
        if hasattr(self, "statusBar") and self.statusBar():
            self.statusBar().showMessage(f"'{speaker_name}' 미리듣기 중... ({target_time:.1f}s)", 2000)

    def _show_qr_popup(self, title: str, image_path: str) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setFixedSize(400, 400)
        
        layout = QVBoxLayout(dialog)
        
        lbl = QLabel(dialog)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if Path(image_path).exists():
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                lbl.setPixmap(pixmap.scaled(350, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                 lbl.setText("이미지를 불러올 수 없습니다.")
        else:
            lbl.setText(f"{title} QR 코드를 찾을 수 없습니다.\n({image_path})")
            
        layout.addWidget(lbl)
        
        dialog.exec()

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            /* Global Reset & Font */
            * {
                outline: none;
                font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
            }
            
            QMainWindow {
                background-color: #F0F4F4; /* Light Mint/Off-white Background */
            }

            QMessageBox {
                background-color: #FFFFFF;
            }
            
            QMessageBox QLabel {
                color: #333333;
            }

            /* Card Style (Rounded Container) */
            #card, #topBar, #leftPanel, #rightPanel, #sideBar {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E0E0E0; /* Subtle border for card definition */
            }

            /* Video Area */
            #videoContainer {
                background-color: #000000;
                border-radius: 16px;
            }

            #videoWidget {
                border-radius: 16px;
            }

            /* Labels */
            QLabel {
                color: #333333;
            }

            #logoLabel {
                color: #37474F; /* Dark Blue Grey */
                font-size: 20px;
                font-weight: 700;
                padding-left: 8px;
            }

            #sectionLabel {
                font-size: 15px;
                font-weight: 700;
                color: #263238; /* Dark Charcoal */
                margin-bottom: 4px;
            }

            /* Buttons */
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #4DB6AC, stop:1 #009688);
                color: #FFFFFF;
                border-radius: 12px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 600;
                border: none;
            }

            QPushButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #80CBC4, stop:1 #26A69A);
            }

            QPushButton:pressed {
                background-color: #00796B;
                padding-top: 10px; /* Pressed effect */
            }

            /* Magic Button (Content Area - Matches Main Theme) */
            #magicButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #4DB6AC, stop:1 #009688); /* Mint/Teal */
                color: #FFFFFF;
                border-radius: 16px;
                padding: 4px 12px;
                border: 2px solid #26A69A;
                border-bottom: 6px solid #00695C; /* 3D Effect */
                margin-top: 0px;
            }

            #magicButton:hover {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #80CBC4, stop:1 #26A69A);
                border-color: #4DB6AC;
                border-bottom: 6px solid #00695C;
            }

            #magicButton:pressed {
                background-color: #00796B;
                border-bottom: 2px solid #00695C;
                margin-top: 4px;
                padding-top: 8px; /* Pressed effect compensation */
            }
            
            /* Custom Trigger Delete Button (Small x) */
            QPushButton[text="×"] {
                background-color: transparent;
                color: #999999;
                border: none;
                font-weight: bold;
                padding: 0;
                border-radius: 0;
            }
            QPushButton[text="×"]:hover {
                color: #FF4D4F;
                background-color: transparent;
            }

            /* Inputs */
            QLineEdit {
                background-color: #F5F5F5;
                border: 1px solid #E0E0E0;
                border-radius: 12px;
                padding: 8px;
                font-size: 14px;
                color: #333333;
            }

            QLineEdit:focus {
                border: 2px solid #80CBC4; /* Pastel Teal Focus */
                background-color: #FFFFFF;
            }

            /* Checkbox & List Item Indicator (Styled as Radio Button) */
            QCheckBox {
                font-size: 12px;
                color: #455A64;
                spacing: 8px;
            }
            
            QCheckBox::indicator, QListView::indicator {
                width: 10px;
                height: 10px;
                border-radius: 6px; /* Full Circle */
                border: 2px solid #B0BEC5;
                background-color: #FFFFFF;
            }

            QCheckBox::indicator:checked, QListView::indicator:checked {
                background-color: #616161; /* Grey 700 */
                border: 2px solid #00A896;
                /* Radio Button Dot Style: Solid Circle (Teal on Grey) */
                image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" fill="%2300A896"/></svg>');
            }
            
            QCheckBox::indicator:hover, QListView::indicator:hover {
                border-color: #00A896;
            }

            /* Slider */
            QSlider::groove:horizontal {
                border: none;
                height: 8px;
                background: #E0E0E0;
                border-radius: 4px;
            }

            QSlider::handle:horizontal {
                background: #00C7AE;
                border: 2px solid #FFFFFF;
                width: 24px;
                height: 24px;
                margin: -8px 0;
                border-radius: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            QSlider::sub-page:horizontal {
                background: #80CBC4;
                border-radius: 4px;
            }

            /* Lists */
            QListWidget {
                border: 1px solid #E0E0E0;
                background-color: #F9FAFB;
                border-radius: 12px;
                padding: 8px;
                outline: none;
            }

            #speakerList {
                background-color: transparent;
                border: none;
            }

            QListWidget::item {
                min-height: 32px;
                padding: 6px 10px;
                border-radius: 8px;
                margin-bottom: 2px;
                background-color: #FFFFFF;
                color: #333333;
                border: 1px solid #F0F0F0;
                border-bottom: none;
            }

            QListWidget::item:selected {
                background-color: #E0F2F1; /* Very Light Teal */
                color: #00796B; /* Dark Teal Text */
                border: 1px solid #B2DFDB;
                outline: none;
            }
            
            /* Custom Trigger List Specifics to remove artifacts */
            #customTriggerList::item {
                color: transparent; /* Hide underlying text */
                border: none; /* Remove border artifacts */
                background-color: transparent;
                padding: 0;
            }
            
            #customTriggerList::item:hover {
                background-color: transparent;
                border: none;
            }
            
            #customTriggerList::item:selected {
                background-color: transparent;
                border: none;
            }

            QListWidget::item:hover {
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
            }
            
            QListWidget::item:focus {
                outline: none;
                border: none;
            }

            /* Custom Trigger Item Widget (Transparent Container) */
            #customTriggerItemWidget {
                background-color: transparent;
                border: none;
            }
            
            #timelineWidget {
                background-color: transparent;
            }
            """
        )

    def show_loading(self, msg: str) -> None:
        # UI 비활성화 (모달 효과)
        if self.centralWidget():
            self.centralWidget().setEnabled(False)
            
        # [Fix] 비디오 재생 중지 및 비디오 출력 해제 (화면 겹침 및 리소스 문제 방지)
        if hasattr(self, "player"):
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.pause()
            self.player.setVideoOutput(None)

        # 비디오 위젯이 오버레이를 가리지 않도록 숨김 (Windows 등에서 필수)
        # retainSizeWhenHidden=True 설정으로 레이아웃은 유지됨
        if hasattr(self, "video_widget"):
            self.video_widget.setVisible(False)

        if hasattr(self, "loading_overlay"):
            self.loading_overlay.show_message(msg)

    def hide_loading(self) -> None:
        if hasattr(self, "loading_overlay"):
            self.loading_overlay.hide_overlay()
            
        # 비디오 위젯 복구
        if hasattr(self, "video_widget"):
            self.video_widget.setVisible(True)
            self.video_widget.repaint()
            self.video_widget.update()
            
            # [Fix] 비디오 출력 재설정 (show_loading에서 해제한 것 복구)
            if hasattr(self, "player"):
                self.player.setVideoOutput(self.video_widget)
                # 약간의 지연 후 갱신 (Qt 이벤트 루프 문제 방지)
                QTimer.singleShot(100, lambda: self.video_widget.update())

        # UI 활성화
        if self.centralWidget():
            self.centralWidget().setEnabled(True)

    def _on_open_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "비디오 파일 열기",
            "",
            "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*)"
        )

        if not file_path:
            return

        # 1. 이전 분석 데이터 완전 초기화 (Hard Reset)
        self.analyzed_intervals = []
        self.total_duration = 0.0
        self.raw_triggers = []
        self.speaker_segments = []
        
        # UI 초기화
        self.detected_list.clear()
        self.detected_label.setText("탐지된 트리거 (0)")
        self.speaker_list.clear()
        
        # 타임라인 초기화 (구간 제거)
        if hasattr(self, 'timeline'):
            self.timeline.update_intervals(0.0, [])
            self.timeline.update_triggers([])
            
        # 로그 또는 상태 표시 (Optional)
        if hasattr(self, "statusBar") and self.statusBar():
            self.statusBar().showMessage("새 파일이 열렸습니다. 분석을 시작해주세요.", 3000)

        # 2. 파일 로드
        self.current_video_path = Path(file_path)
        
        # [추가] 파일명 라벨 업데이트
        if hasattr(self, 'filename_label'):
            self.filename_label.setText(self.current_video_path.name)
            self.filename_label.setStyleSheet("color: #2c3e50; font-size: 13px; font-weight: bold; margin-top: 5px; margin-bottom: 5px;")
            
        self.player.setSource(QUrl.fromLocalFile(str(self.current_video_path)))
        
        # 3. 이전 분석 스레드가 있다면 정리
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.terminate()
            self.analysis_thread.wait()
            self.analysis_thread = None
            
        # 미리듣기 타이머 정리
        if hasattr(self, "_preview_timer") and self._preview_timer.isActive():
            self._preview_timer.stop()

    def _on_volume_changed(self, value: int) -> None:
        self.audio_output.setVolume(float(value) / 100.0)

    def _on_custom_trigger_double_clicked(self, item: QListWidgetItem) -> None:
        reply = QMessageBox.question(
            self, 
            "트리거 삭제", 
            f"'{item.text()}' 트리거를 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._remove_custom_trigger(item)

    def _add_custom_trigger(self) -> None:
        # 버튼 클릭 등으로 트리거 추가 시 메인 윈도우로 포커스 이동 (입력창 포커스 해제) -> 제거
        # self.setFocus()
        
        text = self.trigger_input.text().strip()
        if not text:
            self.trigger_input.setFocus() # 빈 입력일 때도 포커스 유지
            return
            
        # 중복 체크
        for i in range(self.custom_trigger_list.count()):
            if self.custom_trigger_list.item(i).text() == text:
                self.trigger_input.clear()
                self.trigger_input.setFocus() # 중복일 때도 포커스 유지
                return

        item = QListWidgetItem(self.custom_trigger_list)
        item.setText(text)
        
        widget = QWidget()
        widget.setObjectName("customTriggerItemWidget")
        widget.setStyleSheet("#customTriggerItemWidget { background-color: transparent; border: none; }")
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(10)
        
        label = QLabel(text)
        label.setStyleSheet("color: #555555; font-weight: 500; border: none; background: transparent;")
        
        # 라벨이 공간을 차지하도록 설정 (말줄임표 방지)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        
        delete_btn = QPushButton("×")
        delete_btn.setFixedSize(16, 16)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus) # 버튼 포커스 잔상 제거
        delete_btn.setStyleSheet("QPushButton { background-color: transparent; color: #999; border: none; font-weight: bold; } QPushButton:hover { color: #ff4d4f; }")
        
        # lambda 주의: item 참조를 위해
        delete_btn.clicked.connect(lambda checked=False, i=item: self._remove_custom_trigger(i))
        
        layout.addWidget(label, 1) # stretch factor 1
        layout.addWidget(delete_btn)
        
        item.setSizeHint(widget.sizeHint())
        self.custom_trigger_list.setItemWidget(item, widget)
        self.trigger_input.clear()
        self.trigger_input.setFocus() # 계속 입력할 수 있게 포커스 잡기

    def _remove_custom_trigger(self, item: QListWidgetItem) -> None:
        row = self.custom_trigger_list.row(item)
        self.custom_trigger_list.takeItem(row)

    def _on_magic_clicked(self) -> None:
        if not self.current_video_path:
            return
        if self.analysis_thread is not None and self.analysis_thread.isRunning():
            return

        triggers: list[str] = []
        if self.chk_start.isChecked():
            triggers.append("시작")
        if self.chk_one_two_three.isChecked():
            triggers.append("하나둘셋")
        if self.chk_two_three.isChecked():
            triggers.append("둘셋")

        # 커스텀 트리거 추가
        for i in range(self.custom_trigger_list.count()):
            text = self.custom_trigger_list.item(i).text().strip()
            if text:
                triggers.append(text)

        if not triggers:
            triggers = ["시작", "하나둘셋", "둘셋"]
            
        # 2. 분석 시작 시 안전장치 (Safety Clear)
        # 체크박스 상태 확인 ("기존 결과 유지")
        self.keep_existing = self.chk_reanalyze.isChecked()
        
        if not self.keep_existing:
            # 혹시 남아있을지 모르는 이전 결과 삭제 (기존 모드)
            self.analyzed_intervals = []
            self.raw_triggers = []
            self.speaker_segments = []
            self.detected_list.clear()
            self.speaker_list.clear()
            if hasattr(self, 'timeline'):
                self.timeline.update_intervals(self.total_duration, [])
                self.timeline.update_triggers([])
                self.timeline.update()
        else:
            # 유지 모드: 기존 결과 보존
            pass

        # 오버레이 표시 (UI 비활성화는 show_loading에서 처리됨)
        self.show_loading("분석 중")

        # include_trigger는 별도 설정이 없으므로 False (트리거 구간 삭제)
        # chk_reanalyze는 "결과 유지" 용도로 사용됨
        include_trigger = False 

        self.analysis_thread = AnalyzeThread(
            self.current_video_path,
            triggers,
            include_trigger,
            self
        )
        self.analysis_thread.finished.connect(self._on_analysis_finished)
        self.analysis_thread.error.connect(self._on_analysis_error)
        self.analysis_thread.start()

    def _on_analysis_finished(self, intervals, duration, triggers, speakers, speaker_segments) -> None:
        self.hide_loading()
        
        # [Merge Logic] 기존 결과 유지 모드일 경우 병합
        if hasattr(self, 'keep_existing') and self.keep_existing:
            # 1. 트리거 병합 (중복 제거)
            # 기존 트리거 + 새 트리거
            # 중복 판단 기준: start, end 시간이 거의 같으면 중복으로 처리
            existing_triggers = self.raw_triggers
            merged_triggers = existing_triggers.copy()
            
            for new_trig in triggers:
                is_duplicate = False
                new_start = float(new_trig.get("start", 0))
                new_end = float(new_trig.get("end", 0))
                
                for ex_trig in existing_triggers:
                    ex_start = float(ex_trig.get("start", 0))
                    ex_end = float(ex_trig.get("end", 0))
                    
                    # 겹침 허용 오차 0.5초
                    if abs(new_start - ex_start) < 0.5 and abs(new_end - ex_end) < 0.5:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    merged_triggers.append(new_trig)
            
            # 시간순 정렬
            merged_triggers.sort(key=lambda x: float(x.get("start", 0)))
            triggers = merged_triggers
            
            # 2. 화자 세그먼트 병합 (단순 추가)
            # 화자 식별은 매번 달라질 수 있으므로 주의 필요하지만, 여기서는 단순 추가
            self.speaker_segments.extend(speaker_segments)
            # speakers 요약 정보는 병합하기 어려우므로 새 분석 결과 위주로 사용하거나
            # 기존 speakers 리스트에 없는 ID만 추가
            
            # (여기서는 speakers 리스트는 새 결과만 사용 - 상위 3명 표시용)
            pass
            
        self.analyzed_intervals = intervals # 주의: intervals는 triggers 기반으로 재계산 필요할 수 있음
        self.total_duration = duration
        
        # [중요] 타임라인에 정확한 전체 길이 전달 (표시 오류 방지)
        # 기존 manual cut은 유지하면서 duration만 업데이트
        self.timeline.update_intervals(duration, self.timeline.cut_intervals)

        # 원본 트리거 데이터 저장 (재계산용)
        self.raw_triggers = triggers
        # speaker_segments는 위에서 병합됨 (keep_existing=True일 때)
        if not (hasattr(self, 'keep_existing') and self.keep_existing):
             self.speaker_segments = speaker_segments
        
        # 타임라인 업데이트
        # triggers(cut_intervals)만 전달하면 timeline이 알아서 keep_intervals 계산
        self.timeline.update_triggers(triggers)
        
        # 탐지된 트리거 목록 업데이트
        self.detected_list.clear()
        self.detected_label.setText(f"탐지된 트리거 ({len(triggers)})")
        
        # 시그널 차단 (아이템 추가 중 불필요한 이벤트 방지)
        self.detected_list.blockSignals(True)
        
        for i, trig in enumerate(triggers):
            text = trig.get("text", "").strip()
            start = float(trig.get("start", 0))
            end = float(trig.get("end", 0))
            
            # 리스트 넘버링 추가
            item = QListWidgetItem(f"{i+1}. [{start:.1f}s ~ {end:.1f}s] {text}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            # 아이템에 원본 데이터의 인덱스 저장
            item.setData(Qt.ItemDataRole.UserRole, i)
            
            self.detected_list.addItem(item)
            
        self.detected_list.blockSignals(False)
        
        # 목소리 목록 업데이트 (Speaker Sorting Logic)
        self.speaker_list.clear()
        
        # 상위 3명만 표시 (Top 3)
        top_speakers = speakers[:3]
        
        # 시그널 차단 (목소리 추가 중 불필요한 필터링 방지)
        # _add_speaker_item 내부에서 connect를 하므로, 여기서 blockSignals는 QListWidget 시그널만 막음.
        # 체크박스 시그널은 직접 연결되므로 blockSignals로 막히지 않음.
        # 따라서, 마지막에 한 번만 필터링 로직을 호출하도록 해야 함.
        # 하지만 _add_speaker_item에서 connect를 하므로, 추가할 때마다 호출될 수 있음.
        # 이를 방지하기 위해 _on_speaker_selection_changed 내부에서 초기화 중인지 체크하거나,
        # _add_speaker_item 호출 시에는 connect를 하지 않고 나중에 하거나...
        # 간단하게: 그냥 호출되게 두고, 마지막에 확실하게 한 번 더 호출.
        
        for i, spk in enumerate(top_speakers):
            spk_id = spk.get("id") # ID 필수
            name = spk.get("name", "Unknown")
            is_adult = spk.get("is_adult", False)
            
            # 1번 목소리(가장 상단) 자동 선택 (Auto-Select)
            # 조건: 성인 중 발화량이 가장 많은 1명만 선택 (Safety First)
            # 나머지 성인 목소리(외부인 등)는 체크 해제 상태로 두어 오작동 방지
            checked = (i == 0 and is_adult)
            self._add_speaker_item(name, checked, spk_id)
            
        # 나머지 목소리가 있다면 '더 보기' 아이템 추가
        if len(speakers) > 3:
            more_text = f"외 {len(speakers) - 3}명의 목소리..."
            more_item = QListWidgetItem(more_text)
            more_item.setFlags(Qt.ItemFlag.NoItemFlags) # 비활성화
            more_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            more_item.setForeground(QBrush(QColor("#999999")))
            self.speaker_list.addItem(more_item)
        
        # 아이템 변경 시그널 연결 (체크박스 변경 시 재계산)
        self.detected_list.itemChanged.connect(self._on_detected_item_changed)
        
        # 초기 목소리 필터링 적용 (자동 선택된 목소리 기준)
        self._on_speaker_selection_changed()
            
        QMessageBox.information(self, "완료", f"분석 완료! {len(triggers)}개의 트리거가 탐지되었고,\n{len(intervals)}개의 구간이 생성되었습니다.\n원하지 않는 트리거는 우측 목록에서 체크 해제하세요.")

    def _on_speaker_selection_changed(self) -> None:
        """목소리 선택 변경 시 트리거 목록 필터링 및 구간 재계산"""
        if not hasattr(self, 'raw_triggers') or not hasattr(self, 'speaker_segments'):
            return

        # 1. 선택된 목소리 ID 수집
        selected_speaker_ids = []
        for i in range(self.speaker_list.count()):
            item = self.speaker_list.item(i)
            # '더 보기' 아이템 등은 제외
            if item.flags() & Qt.ItemFlag.NoItemFlags:
                continue
                
            widget = self.speaker_list.itemWidget(item)
            if widget:
                chk = widget.findChild(QCheckBox, "speakerCheckbox")
                if chk and chk.isChecked():
                    spk_id = item.data(Qt.ItemDataRole.UserRole)
                    if spk_id:
                        selected_speaker_ids.append(spk_id)

        # 2. 프로세서를 통해 유효한 트리거 필터링 (Detect-Then-Filter)
        processor = MeariProcessor()
        valid_triggers = processor.filter_triggers_by_speaker(
            self.raw_triggers,
            self.speaker_segments,
            selected_speaker_ids,
            tolerance=1.0 # 1.0초 여유 (짧은 발화 손실 방지)
        )
        
        # valid_triggers에 포함된 트리거들의 인덱스(또는 start/end/text 매칭)를 찾아서
        # detected_list의 체크 상태 업데이트
        
        # raw_triggers와 detected_list의 순서는 동일하다고 가정 (인덱스 매칭)
        # valid_triggers는 raw_triggers의 부분집합이므로, 객체 비교가 가능할 수도 있지만
        # 딕셔너리이므로 값 비교가 안전. 하지만 raw_triggers의 객체 레퍼런스가 유지된다면 id 비교 가능.
        # 여기서는 filter_triggers_by_speaker가 raw_triggers의 요소를 그대로 반환한다고 가정.
        
        valid_indices = set()
        for trig in valid_triggers:
            # raw_triggers에서 해당 트리거의 인덱스 찾기
            # (주의: 동일한 내용/시간의 트리거가 있을 수 있으나, 여기서는 객체 아이덴티티나 인덱스로 접근하는게 좋음)
            # filter_triggers_by_speaker 구현상 원본 리스트의 요소를 그대로 반환하므로 id() 비교 가능
            # 하지만 안전하게 인덱스 매핑을 위해... 
            # processor.filter_triggers_by_speaker가 원본 객체를 반환한다고 확신.
            pass

        # 더 효율적인 방법:
        # raw_triggers의 각 요소에 대해 유효성 검사를 수행
        # 하지만 filter_triggers_by_speaker 로직을 재사용하려면 반환된 리스트를 이용해야 함.
        # 반환된 리스트의 요소들이 raw_triggers의 요소들과 동일 객체(reference)라면:
        valid_ids = {id(t) for t in valid_triggers}
        
        self.detected_list.blockSignals(True)
        for i in range(self.detected_list.count()):
            # UserRole에 저장된 인덱스 사용
            idx = self.detected_list.item(i).data(Qt.ItemDataRole.UserRole)
            trigger_obj = self.raw_triggers[idx]
            
            if id(trigger_obj) in valid_ids:
                self.detected_list.item(i).setCheckState(Qt.CheckState.Checked)
                # 시각적 강조 (선택됨)
                self.detected_list.item(i).setForeground(QBrush(QColor("#000000")))
            else:
                self.detected_list.item(i).setCheckState(Qt.CheckState.Unchecked)
                # 시각적 약화 (제외됨 - 회색 처리)
                self.detected_list.item(i).setForeground(QBrush(QColor("#AAAAAA")))
                
        self.detected_list.blockSignals(False)
        
        # 3. 변경된 트리거 선택 상태를 반영하여 구간 재계산
        # (detected_list의 itemChanged 시그널을 막았으므로 수동 호출 필요)
        # 하지만 _on_detected_item_changed는 단일 아이템 변경용이 아님?
        # 아니, _on_detected_item_changed는 item 인자를 받지만, 내부에서 전체 리스트를 순회함.
        # 따라서 아무 아이템이나 넘겨도 됨. 또는 로직 분리.
        
        # 로직 중복을 피하기 위해 _recalculate_intervals 메서드로 분리하는 것이 좋지만,
        # 여기서는 _on_detected_item_changed 로직을 그대로 사용하거나 복사.
        # _on_detected_item_changed 호출 (dummy item 전달)
        if self.detected_list.count() > 0:
            self._on_detected_item_changed(self.detected_list.item(0))
        else:
            # 트리거가 없는 경우
            pass

    def _on_timeline_trigger_clicked(self, index: int) -> None:
        # 타임라인에서 트리거 막대를 클릭했을 때 호출됨
        # 해당 인덱스의 아이템을 찾아 체크 상태를 토글
        if not hasattr(self, 'detected_list'):
            return
            
        for i in range(self.detected_list.count()):
            item = self.detected_list.item(i)
            # UserRole에 저장된 원본 인덱스와 비교
            if item.data(Qt.ItemDataRole.UserRole) == index:
                # 체크 상태 토글
                current_state = item.checkState()
                new_state = Qt.CheckState.Unchecked if current_state == Qt.CheckState.Checked else Qt.CheckState.Checked
                item.setCheckState(new_state)
                # itemChanged 시그널이 발생하여 _on_detected_item_changed가 호출됨
                break

    def _on_detected_item_changed(self, item: QListWidgetItem) -> None:
        # 리스트 아이템 변경 시 호출됨 (체크 상태 변경 등)
        # 체크 여부와 상관없이 '모든' 트리거를 타임라인에 전달하도록 변경
        
        if not hasattr(self, 'raw_triggers'):
            return
            
        final_triggers = []
        
        for i in range(self.detected_list.count()):
            list_item = self.detected_list.item(i)
            idx = list_item.data(Qt.ItemDataRole.UserRole)
            
            if idx < 0 or idx >= len(self.raw_triggers):
                continue
                
            # 원본 트리거 정보 복사
            trigger = self.raw_triggers[idx]
            t_copy = trigger.copy()
            t_copy['original_index'] = idx # 타임라인 클릭 처리를 위해 인덱스 저장
            
            # 체크 상태에 따라 status(색상) 결정
            if list_item.checkState() == Qt.CheckState.Checked:
                # 체크됨 -> 빨간색 (Confirmed / 삭제 대상)
                t_copy['status'] = 'confirmed'
            else:
                # 체크 해제됨 -> 노란색 (Candidate / 보존 대상)
                t_copy['status'] = 'candidate'
                
            final_triggers.append(t_copy)
            
        # 타임라인 업데이트 (수동 구간은 유지됨)
        self.timeline.update_triggers(final_triggers)

    def eventFilter(self, obj, event):
        # 스페이스바 재생/일시정지 핸들링
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Space:
            focused_widget = QApplication.focusWidget()
            # 입력창에 포커스가 있을 때는 띄어쓰기 허용 (이벤트 필터링 하지 않음)
            if isinstance(focused_widget, QLineEdit):
                return False
            
            # 그 외의 경우 재생/일시정지 토글
            self._toggle_play_pause()
            return True
            
        # 비디오 위젯 클릭 시 포커스 해제 (입력창 포커스 아웃)
        if obj == getattr(self, 'video_widget', None) and event.type() == QEvent.Type.MouseButtonPress:
            self.setFocus()
            # 클릭 이벤트는 그대로 전달하여 재생/일시정지 등 기본 동작 수행
            return False
            
        return super().eventFilter(obj, event)

    def _toggle_play_pause(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def _on_analysis_error(self, error_msg: str) -> None:
        self.hide_loading()
        QMessageBox.critical(self, "오류", f"분석 중 오류가 발생했습니다:\n{error_msg}")

    def _on_save_clicked(self) -> None:
        if not self.analyzed_intervals or not self.current_video_path:
            QMessageBox.warning(self, "경고", "분석된 구간이 없습니다.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"{self.current_video_path.stem}_{timestamp}_edited.mp4"
        default_path = str(self.current_video_path.with_name(default_filename))

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "저장할 파일 선택",
            default_path,
            "MP4 Files (*.mp4)"
        )

        if not output_path:
            return

        self.show_loading("영상을 저장 중입니다.\n(인코딩에 시간이 소요됩니다.)")

        # 저장 스레드
        # processor는 새로 생성해야 함 (스레드 안전)
        processor = MeariProcessor()
        
        self.save_thread = SaveThread(
            processor,
            self.current_video_path,
            Path(output_path),
            self.analyzed_intervals
        )
        self.save_thread.finished.connect(self._on_save_finished)
        self.save_thread.start()

    def _on_save_finished(self, success, msg) -> None:
        try:
            self.hide_loading()
            
            if success:
                QMessageBox.information(self, "완료", f"저장 완료!\n{msg}")
            else:
                QMessageBox.critical(self, "오류", f"저장 실패:\n{msg}")
        except Exception as e:
            traceback.print_exc()

    def _on_video_position_changed(self, position_ms: int) -> None:
        if self.total_duration > 0:
            self.timeline.set_position(position_ms / 1000.0)

    def _on_timeline_seek(self, position_s: float) -> None:
        self.player.setPosition(int(position_s * 1000))

    def _on_video_duration_changed(self, duration_ms: int) -> None:
        if duration_ms <= 0:
            return
            
        # 이미 분석된 결과가 있다면 덮어쓰지 않음
        if self.analyzed_intervals:
            return
            
        duration_s = duration_ms / 1000.0
        self.total_duration = duration_s
        
        # 분석 전에는 전체 구간을 보존(초록색)으로 표시
        # cut_intervals=[] (삭제 구간 없음)
        self.timeline.update_intervals(duration_s, [])

    def _on_intervals_updated(self, intervals: list[tuple[float, float]]) -> None:
        self.analyzed_intervals = intervals

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
