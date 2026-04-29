from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.capture.worker import CaptureConfig, CaptureWorker
from app.ui.roi_select import RoiSelectDialog
from app.win.window_finder import find_ffxiv_windows


@dataclass(frozen=True)
class RoiRect:
    left: int
    top: int
    width: int
    height: int


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FFXIV 实时翻译（MVP）")
        self.resize(1100, 700)

        self._hwnd: Optional[int] = None
        self._roi_screen: Optional[RoiRect] = None

        self._worker = CaptureWorker()
        self._worker.new_line.connect(self._on_new_line)
        self._worker.status.connect(self._on_status)

        root = QWidget(self)
        self.setCentralWidget(root)

        splitter = QSplitter(Qt.Horizontal, root)

        left = QWidget(splitter)
        left_layout = QVBoxLayout(left)

        gb_window = QGroupBox("目标窗口", left)
        fl_window = QFormLayout(gb_window)
        self.cmb_windows = QComboBox(gb_window)
        self.btn_refresh_windows = QPushButton("刷新", gb_window)
        self.btn_bind_window = QPushButton("绑定", gb_window)
        self.lbl_bound = QLabel("未绑定", gb_window)
        self.lbl_bound.setWordWrap(True)

        row = QWidget(gb_window)
        row_l = QHBoxLayout(row)
        row_l.setContentsMargins(0, 0, 0, 0)
        row_l.addWidget(self.cmb_windows, 1)
        row_l.addWidget(self.btn_refresh_windows)
        row_l.addWidget(self.btn_bind_window)

        fl_window.addRow(row)
        fl_window.addRow("状态：", self.lbl_bound)

        gb_roi = QGroupBox("对白框区域（ROI）", left)
        fl_roi = QFormLayout(gb_roi)
        self.btn_set_roi = QPushButton("框选 ROI", gb_roi)
        self.lbl_roi = QLabel("未设置（建议先框选对白框）", gb_roi)
        self.lbl_roi.setWordWrap(True)
        self.spn_fps = QSpinBox(gb_roi)
        self.spn_fps.setRange(1, 10)
        self.spn_fps.setValue(3)
        self.spn_ocr_ms = QSpinBox(gb_roi)
        self.spn_ocr_ms.setRange(250, 5000)
        self.spn_ocr_ms.setSingleStep(250)
        self.spn_ocr_ms.setValue(750)
        fl_roi.addRow(self.btn_set_roi)
        fl_roi.addRow("ROI：", self.lbl_roi)
        fl_roi.addRow("捕获 FPS：", self.spn_fps)
        fl_roi.addRow("OCR 间隔(ms)：", self.spn_ocr_ms)

        gb_translate = QGroupBox("翻译（可选）", left)
        fl_tr = QFormLayout(gb_translate)
        self.txt_ollama_url = QLineEdit(gb_translate)
        self.txt_ollama_url.setText("http://localhost:11434")
        self.txt_model = QLineEdit(gb_translate)
        self.txt_model.setText("qwen2.5:7b-instruct-q4_K_M")
        fl_tr.addRow("Ollama 地址：", self.txt_ollama_url)
        fl_tr.addRow("模型名：", self.txt_model)
        self.lbl_tr_status = QLabel("翻译：未启用（可直接先跑 OCR）", gb_translate)
        self.lbl_tr_status.setWordWrap(True)
        fl_tr.addRow(self.lbl_tr_status)

        gb_ctrl = QGroupBox("控制", left)
        ctrl_l = QVBoxLayout(gb_ctrl)
        self.btn_start = QPushButton("开始", gb_ctrl)
        self.btn_pause = QPushButton("暂停", gb_ctrl)
        self.btn_pause.setEnabled(False)
        self.btn_clear = QPushButton("清空记录", gb_ctrl)
        ctrl_l.addWidget(self.btn_start)
        ctrl_l.addWidget(self.btn_pause)
        ctrl_l.addWidget(self.btn_clear)
        ctrl_l.addStretch(1)

        left_layout.addWidget(gb_window)
        left_layout.addWidget(gb_roi)
        left_layout.addWidget(gb_translate)
        left_layout.addWidget(gb_ctrl)
        left_layout.addStretch(1)

        right = QWidget(splitter)
        right_layout = QVBoxLayout(right)
        self.txt_log = QPlainTextEdit(right)
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("这里会持续追加识别/翻译出来的台词记录…")
        right_layout.addWidget(self.txt_log, 1)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout(root)
        layout.addWidget(splitter, 1)

        # menu
        act_about = QAction("关于", self)
        act_about.triggered.connect(self._about)
        self.menuBar().addAction(act_about)

        # signals
        self.btn_refresh_windows.clicked.connect(self._refresh_windows)
        self.btn_bind_window.clicked.connect(self._bind_selected_window)
        self.btn_set_roi.clicked.connect(self._choose_roi)
        self.btn_start.clicked.connect(self._start)
        self.btn_pause.clicked.connect(self._pause)
        self.btn_clear.clicked.connect(self.txt_log.clear)

        self._refresh_windows()

    @Slot()
    def _about(self) -> None:
        QMessageBox.information(
            self,
            "关于",
            "这是一个 MVP：ROI 截图 + Windows OCR + 可选本地 Ollama 翻译。\n"
            "建议先：刷新窗口→绑定FFXIV→框选对白框ROI→开始。",
        )

    @Slot()
    def _refresh_windows(self) -> None:
        self.cmb_windows.clear()
        wins = find_ffxiv_windows()
        for w in wins:
            self.cmb_windows.addItem(f"[{w.hwnd}] {w.title}", userData=w.hwnd)
        if not wins:
            self.cmb_windows.addItem("未找到 FFXIV 窗口（你可以先开游戏，或用窗口化/无边框）", userData=None)

    @Slot()
    def _bind_selected_window(self) -> None:
        hwnd = self.cmb_windows.currentData()
        if not hwnd:
            self._hwnd = None
            self.lbl_bound.setText("未绑定")
            return
        self._hwnd = int(hwnd)
        self.lbl_bound.setText(f"已绑定 hwnd={self._hwnd}")

    @Slot()
    def _choose_roi(self) -> None:
        dlg = RoiSelectDialog(self)
        if dlg.exec() != dlg.Accepted:
            return
        r = dlg.selected_rect()
        if r is None:
            return
        self._roi_screen = RoiRect(r.x(), r.y(), r.width(), r.height())
        self.lbl_roi.setText(f"screen: ({r.x()},{r.y()}) {r.width()}x{r.height()}")

    @Slot()
    def _start(self) -> None:
        if self._roi_screen is None:
            QMessageBox.warning(self, "需要 ROI", "请先框选对白框 ROI。")
            return
        cfg = CaptureConfig(
            hwnd=self._hwnd,
            roi_screen=(self._roi_screen.left, self._roi_screen.top, self._roi_screen.width, self._roi_screen.height),
            fps=int(self.spn_fps.value()),
            ocr_interval_ms=int(self.spn_ocr_ms.value()),
            ollama_base_url=self.txt_ollama_url.text().strip() or None,
            ollama_model=self.txt_model.text().strip() or None,
        )
        self._worker.start_capture(cfg)
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)

    @Slot()
    def _pause(self) -> None:
        self._worker.stop_capture()
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)

    @Slot(str)
    def _on_new_line(self, line: str) -> None:
        self.txt_log.appendPlainText(line)
        self.txt_log.verticalScrollBar().setValue(self.txt_log.verticalScrollBar().maximum())

    @Slot(str)
    def _on_status(self, status: str) -> None:
        self.statusBar().showMessage(status, 5000)

    def closeEvent(self, event) -> None:  # noqa: N802
        try:
            self._worker.stop_capture()
        finally:
            super().closeEvent(event)

