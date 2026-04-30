from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
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
from app.config import get_config, set_config, AppConfig
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
        self.setWindowTitle("FFXIV 实时翻译")

        self._config = get_config()
        self.resize(self._config.window_width, self._config.window_height)

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

        # ===== 目标窗口 =====
        gb_window = QGroupBox("目标窗口", left)
        fl_window = QFormLayout(gb_window)
        from PySide6.QtWidgets import QComboBox
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

        # ===== ROI 设置 =====
        gb_roi = QGroupBox("对白框区域（ROI）", left)
        fl_roi = QFormLayout(gb_roi)
        self.btn_set_roi = QPushButton("框选 ROI", gb_roi)
        self.lbl_roi = QLabel("未设置（建议先框选对白框）", gb_roi)
        self.lbl_roi.setWordWrap(True)
        self.spn_fps = QSpinBox(gb_roi)
        self.spn_fps.setRange(1, 10)
        self.spn_fps.setValue(self._config.default_fps)
        self.spn_ocr_ms = QSpinBox(gb_roi)
        self.spn_ocr_ms.setRange(250, 5000)
        self.spn_ocr_ms.setSingleStep(250)
        self.spn_ocr_ms.setValue(self._config.default_ocr_interval_ms)
        fl_roi.addRow(self.btn_set_roi)
        fl_roi.addRow("ROI：", self.lbl_roi)
        fl_roi.addRow("捕获 FPS：", self.spn_fps)
        fl_roi.addRow("OCR 间隔(ms)：", self.spn_ocr_ms)

        # ===== 千问 MT 翻译配置 =====
        gb_translate = QGroupBox("翻译服务（千问 MT）", left)
        fl_tr = QFormLayout(gb_translate)

        self.txt_qwen_mt_key = QLineEdit(gb_translate)
        self.txt_qwen_mt_key.setEchoMode(QLineEdit.Password)
        self.txt_qwen_mt_key.setPlaceholderText("sk-xxxx…")
        self.txt_qwen_mt_key.setText(self._config.qwen_mt.api_key)

        self.txt_qwen_mt_model = QLineEdit(gb_translate)
        self.txt_qwen_mt_model.setPlaceholderText("qwen-mt-flash")
        self.txt_qwen_mt_model.setText(self._config.qwen_mt.model)

        self.txt_qwen_mt_url = QLineEdit(gb_translate)
        self.txt_qwen_mt_url.setText(self._config.qwen_mt.base_url)

        fl_tr.addRow("API Key：", self.txt_qwen_mt_key)
        fl_tr.addRow("模型：", self.txt_qwen_mt_model)
        fl_tr.addRow("API 地址：", self.txt_qwen_mt_url)

        lbl_hint = QLabel(
            "• <b>qwen-mt-flash</b>（快速低成本）　• <b>qwen-mt-plus</b>（最高质量）<br>"
            "新加坡区：<tt>https://dashscope-intl.aliyuncs.com/compatible-mode/v1</tt><br>"
            "国内区：<tt>https://dashscope.aliyuncs.com/compatible-mode/v1</tt>",
            gb_translate,
        )
        lbl_hint.setOpenExternalLinks(True)
        lbl_hint.setWordWrap(True)
        fl_tr.addRow(lbl_hint)

        self.btn_check_qwen_mt = QPushButton("检查连接", gb_translate)
        self.btn_check_qwen_mt.clicked.connect(self._check_qwen_mt_connection)
        fl_tr.addRow(self.btn_check_qwen_mt)

        # ===== 控制按钮 =====
        gb_ctrl = QGroupBox("控制", left)
        ctrl_l = QVBoxLayout(gb_ctrl)
        self.btn_start = QPushButton("开始", gb_ctrl)
        self.btn_pause = QPushButton("暂停", gb_ctrl)
        self.btn_pause.setEnabled(False)
        self.btn_clear = QPushButton("清空记录", gb_ctrl)
        self.btn_export = QPushButton("导出日志…", gb_ctrl)
        self.btn_save_config = QPushButton("保存配置", gb_ctrl)
        ctrl_l.addWidget(self.btn_start)
        ctrl_l.addWidget(self.btn_pause)
        ctrl_l.addWidget(self.btn_clear)
        ctrl_l.addWidget(self.btn_export)
        ctrl_l.addWidget(self.btn_save_config)
        ctrl_l.addStretch(1)

        left_layout.addWidget(gb_window)
        left_layout.addWidget(gb_roi)
        left_layout.addWidget(gb_translate)
        left_layout.addWidget(gb_ctrl)
        left_layout.addStretch(1)

        # ===== 右侧日志 =====
        right = QWidget(splitter)
        right_layout = QVBoxLayout(right)
        self.txt_log = QPlainTextEdit(right)
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("识别 / 翻译的台词将持续追加在这里…")
        right_layout.addWidget(self.txt_log, 1)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout(root)
        layout.addWidget(splitter, 1)

        # ===== 菜单 =====
        act_about = QAction("关于", self)
        act_about.triggered.connect(self._about)
        self.menuBar().addAction(act_about)

        # ===== 信号连接 =====
        self.btn_refresh_windows.clicked.connect(self._refresh_windows)
        self.btn_bind_window.clicked.connect(self._bind_selected_window)
        self.btn_set_roi.clicked.connect(self._choose_roi)
        self.btn_start.clicked.connect(self._start)
        self.btn_pause.clicked.connect(self._pause)
        self.btn_clear.clicked.connect(self.txt_log.clear)
        self.btn_export.clicked.connect(self._export_log)
        self.btn_save_config.clicked.connect(self._save_config)

        self._refresh_windows()

    # ------------------------------------------------------------------
    # 千问 MT 连接检查
    # ------------------------------------------------------------------

    @Slot()
    def _check_qwen_mt_connection(self) -> None:
        from app.translate.qwen_mt import QwenMtTranslator
        from app.translate.base import QwenMtConfig
        try:
            cfg = QwenMtConfig(
                api_key=self.txt_qwen_mt_key.text().strip(),
                model=self.txt_qwen_mt_model.text().strip() or "qwen-mt-flash",
                base_url=self.txt_qwen_mt_url.text().strip(),
            )
            translator = QwenMtTranslator(cfg)
            translator.health_check()
            QMessageBox.information(self, "成功", "✅ 千问 MT API 连接正常")
        except Exception as e:
            QMessageBox.critical(self, "连接失败", f"❌ {e}")

    # ------------------------------------------------------------------
    # 窗口 / ROI
    # ------------------------------------------------------------------

    @Slot()
    def _refresh_windows(self) -> None:
        self.cmb_windows.clear()
        wins = find_ffxiv_windows()
        for w in wins:
            self.cmb_windows.addItem(f"[{w.hwnd}] {w.title}", userData=w.hwnd)
        if not wins:
            self.cmb_windows.addItem("未找到 FFXIV 窗口（先开游戏，或用窗口化/无边框）", userData=None)

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
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        r = dlg.selected_rect()
        if r is None:
            return
        self._roi_screen = RoiRect(r.x(), r.y(), r.width(), r.height())
        self.lbl_roi.setText(f"({r.x()}, {r.y()})  {r.width()} × {r.height()} px")

    # ------------------------------------------------------------------
    # 开始 / 暂停
    # ------------------------------------------------------------------

    @Slot()
    def _start(self) -> None:
        if self._roi_screen is None:
            QMessageBox.warning(self, "需要 ROI", "请先框选对白框 ROI。")
            return

        api_key = self.txt_qwen_mt_key.text().strip()
        if not api_key:
            QMessageBox.warning(self, "配置不完整", "请先填写千问 MT 的 API Key。")
            return

        cfg = CaptureConfig(
            hwnd=self._hwnd,
            roi_screen=(
                self._roi_screen.left,
                self._roi_screen.top,
                self._roi_screen.width,
                self._roi_screen.height,
            ),
            fps=int(self.spn_fps.value()),
            ocr_interval_ms=int(self.spn_ocr_ms.value()),
            translator_type="qwen_mt",
            translator_config={
                "api_key": api_key,
                "model": self.txt_qwen_mt_model.text().strip() or "qwen-mt-flash",
                "base_url": self.txt_qwen_mt_url.text().strip(),
            },
        )
        self._worker.start_capture(cfg)
        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)

    @Slot()
    def _pause(self) -> None:
        self._worker.stop_capture()
        self.btn_start.setEnabled(True)
        self.btn_pause.setEnabled(False)

    # ------------------------------------------------------------------
    # 日志
    # ------------------------------------------------------------------

    @Slot(str)
    def _on_new_line(self, line: str) -> None:
        self.txt_log.appendPlainText(line)
        self.txt_log.verticalScrollBar().setValue(self.txt_log.verticalScrollBar().maximum())

    @Slot(str)
    def _on_status(self, status: str) -> None:
        self.statusBar().showMessage(status, 5000)

    @Slot()
    def _export_log(self) -> None:
        content = self.txt_log.toPlainText()
        if not content.strip():
            QMessageBox.information(self, "日志为空", "当前没有可导出的记录。")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出翻译日志",
            "ffxiv_translation_log.txt",
            "文本文件 (*.txt);;所有文件 (*)",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "成功", f"✅ 日志已导出到：\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"❌ 导出失败：{e}")

    # ------------------------------------------------------------------
    # 配置持久化
    # ------------------------------------------------------------------

    def _collect_config(self) -> None:
        self._config.translator_type = "qwen_mt"
        self._config.default_fps = int(self.spn_fps.value())
        self._config.default_ocr_interval_ms = int(self.spn_ocr_ms.value())
        self._config.window_width = self.width()
        self._config.window_height = self.height()
        self._config.qwen_mt.api_key = self.txt_qwen_mt_key.text().strip()
        self._config.qwen_mt.model = self.txt_qwen_mt_model.text().strip()
        self._config.qwen_mt.base_url = self.txt_qwen_mt_url.text().strip()

    @Slot()
    def _save_config(self) -> None:
        try:
            self._collect_config()
            self._config.save_to_file()
            QMessageBox.information(self, "成功", "✅ 配置已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"❌ 保存配置失败：{e}")

    def closeEvent(self, event) -> None:  # noqa: N802
        try:
            self._worker.stop_capture()
            try:
                self._collect_config()
                self._config.save_to_file()
            except Exception:
                pass
        finally:
            super().closeEvent(event)

    # ------------------------------------------------------------------
    # 关于
    # ------------------------------------------------------------------

    @Slot()
    def _about(self) -> None:
        QMessageBox.information(
            self,
            "关于 FFXIV 实时翻译",
            "版本：2.1\n\n"
            "使用流程：\n"
            "1. 刷新窗口 → 绑定 FFXIV\n"
            "2. 框选对白框 ROI\n"
            "3. 填写千问 MT API Key\n"
            "4. 点击开始\n\n"
            "翻译引擎：Qwen-MT（阿里云千问专用翻译模型）",
        )
