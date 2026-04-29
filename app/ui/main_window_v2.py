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
    QTabWidget,
)

from app.capture.worker import CaptureConfig, CaptureWorker
from app.config import get_config, set_config, AppConfig
from app.translate.base import TranslatorType
from app.translate.factory import TranslatorFactory
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
        self.setWindowTitle("FFXIV 实时翻译（改进版）")
        
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

        # ===== 翻译设置（选项卡） =====
        gb_translate = QGroupBox("翻译服务（可选）", left)
        translate_layout = QVBoxLayout(gb_translate)
        
        # 翻译类型选择
        type_row = QWidget(gb_translate)
        type_row_l = QHBoxLayout(type_row)
        type_row_l.setContentsMargins(0, 0, 0, 0)
        type_row_l.addWidget(QLabel("翻译类型："))
        self.cmb_translator_type = QComboBox(type_row)
        self.cmb_translator_type.addItems(["离线（不翻译）", "Ollama（本地）", "DeepSeek API", "百度翻译"])
        self.cmb_translator_type.setCurrentText(self._translate_type_to_label(self._config.translator_type))
        self.cmb_translator_type.currentTextChanged.connect(self._on_translator_type_changed)
        type_row_l.addWidget(self.cmb_translator_type)
        type_row_l.addStretch(1)
        translate_layout.addWidget(type_row)
        
        # 创建选项卡用于不同翻译器的设置
        self.tabs_translator = QTabWidget(gb_translate)
        
        # Ollama 选项卡
        tab_ollama = QWidget(self.tabs_translator)
        fl_ollama = QFormLayout(tab_ollama)
        self.txt_ollama_url = QLineEdit(tab_ollama)
        self.txt_ollama_url.setText(self._config.ollama.base_url)
        self.txt_ollama_model = QLineEdit(tab_ollama)
        self.txt_ollama_model.setText(self._config.ollama.model)
        fl_ollama.addRow("Ollama 地址：", self.txt_ollama_url)
        fl_ollama.addRow("模型名：", self.txt_ollama_model)
        self.btn_check_ollama = QPushButton("检查连接", tab_ollama)
        self.btn_check_ollama.clicked.connect(self._check_ollama_connection)
        fl_ollama.addRow(self.btn_check_ollama)
        self.tabs_translator.addTab(tab_ollama, "Ollama")
        
        # DeepSeek 选项卡
        tab_deepseek = QWidget(self.tabs_translator)
        fl_deepseek = QFormLayout(tab_deepseek)
        self.txt_deepseek_key = QLineEdit(tab_deepseek)
        self.txt_deepseek_key.setText(self._config.deepseek.api_key)
        self.txt_deepseek_key.setEchoMode(QLineEdit.Password)
        self.txt_deepseek_url = QLineEdit(tab_deepseek)
        self.txt_deepseek_url.setText(self._config.deepseek.base_url)
        fl_deepseek.addRow("API 密钥：", self.txt_deepseek_key)
        fl_deepseek.addRow("API 地址：", self.txt_deepseek_url)
        lbl_deepseek_hint = QLabel(
            "💡 获取免费 API 密钥：<a href=\"https://api.deepseek.com\">https://api.deepseek.com</a>",
            tab_deepseek
        )
        lbl_deepseek_hint.setOpenExternalLinks(True)
        lbl_deepseek_hint.setWordWrap(True)
        fl_deepseek.addRow(lbl_deepseek_hint)
        self.tabs_translator.addTab(tab_deepseek, "DeepSeek")
        
        # 百度翻译选项卡
        tab_baidu = QWidget(self.tabs_translator)
        fl_baidu = QFormLayout(tab_baidu)
        self.txt_baidu_app_id = QLineEdit(tab_baidu)
        self.txt_baidu_app_id.setText(self._config.baidu.app_id)
        self.txt_baidu_secret = QLineEdit(tab_baidu)
        self.txt_baidu_secret.setText(self._config.baidu.secret_key)
        self.txt_baidu_secret.setEchoMode(QLineEdit.Password)
        fl_baidu.addRow("APP ID：", self.txt_baidu_app_id)
        fl_baidu.addRow("密钥：", self.txt_baidu_secret)
        lbl_baidu_hint = QLabel(
            "💡 申请免费账号：<a href=\"https://api.fanyi.baidu.com\">https://api.fanyi.baidu.com</a><br>"
            "免费额度：每月 2M 字符",
            tab_baidu
        )
        lbl_baidu_hint.setOpenExternalLinks(True)
        lbl_baidu_hint.setWordWrap(True)
        fl_baidu.addRow(lbl_baidu_hint)
        self.tabs_translator.addTab(tab_baidu, "百度翻译")
        
        translate_layout.addWidget(self.tabs_translator)
        
        self.lbl_tr_status = QLabel("翻译：离线模式（仅显示原文）", gb_translate)
        self.lbl_tr_status.setWordWrap(True)
        translate_layout.addWidget(self.lbl_tr_status)

        # ===== 控制按钮 =====
        gb_ctrl = QGroupBox("控制", left)
        ctrl_l = QVBoxLayout(gb_ctrl)
        self.btn_start = QPushButton("开始", gb_ctrl)
        self.btn_pause = QPushButton("暂停", gb_ctrl)
        self.btn_pause.setEnabled(False)
        self.btn_clear = QPushButton("清空记录", gb_ctrl)
        self.btn_save_config = QPushButton("保存配置", gb_ctrl)
        ctrl_l.addWidget(self.btn_start)
        ctrl_l.addWidget(self.btn_pause)
        ctrl_l.addWidget(self.btn_clear)
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
        self.txt_log.setPlaceholderText("这里会持续追加识别/翻译出来的台词记录…")
        right_layout.addWidget(self.txt_log, 1)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout(root)
        layout.addWidget(splitter, 1)

        # ===== 菜单 =====
        act_about = QAction("关于", self)
        act_about.triggered.connect(self._about)
        act_docs = QAction("快速开始", self)
        act_docs.triggered.connect(self._show_quick_start)
        self.menuBar().addAction(act_about)
        self.menuBar().addAction(act_docs)

        # ===== 信号连接 =====
        self.btn_refresh_windows.clicked.connect(self._refresh_windows)
        self.btn_bind_window.clicked.connect(self._bind_selected_window)
        self.btn_set_roi.clicked.connect(self._choose_roi)
        self.btn_start.clicked.connect(self._start)
        self.btn_pause.clicked.connect(self._pause)
        self.btn_clear.clicked.connect(self.txt_log.clear)
        self.btn_save_config.clicked.connect(self._save_config)

        self._refresh_windows()
        self._update_translator_status()

    @staticmethod
    def _translate_type_to_label(type_str: str) -> str:
        """将翻译类型转换为标签"""
        mapping = {
            "offline": "离线（不翻译）",
            "ollama": "Ollama（本地）",
            "deepseek": "DeepSeek API",
            "baidu": "百度翻译",
        }
        return mapping.get(type_str, "离线（不翻译）")

    @staticmethod
    def _label_to_translate_type(label: str) -> str:
        """将标签转换为翻译类型"""
        mapping = {
            "离线（不翻译）": "offline",
            "Ollama（本地）": "ollama",
            "DeepSeek API": "deepseek",
            "百度翻译": "baidu",
        }
        return mapping.get(label, "offline")

    @Slot(str)
    def _on_translator_type_changed(self, label: str) -> None:
        """翻译器类型改变时"""
        translator_type = self._label_to_translate_type(label)
        # 更新 Tab 页选中
        if translator_type == "ollama":
            self.tabs_translator.setCurrentIndex(0)
        elif translator_type == "deepseek":
            self.tabs_translator.setCurrentIndex(1)
        elif translator_type == "baidu":
            self.tabs_translator.setCurrentIndex(2)
        self._update_translator_status()

    @Slot()
    def _check_ollama_connection(self) -> None:
        """检查 Ollama 连接"""
        from app.translate.base import OllamaConfig
        from app.translate.ollama import OllamaTranslator
        
        try:
            cfg = OllamaConfig(
                base_url=self.txt_ollama_url.text().strip(),
                model=self.txt_ollama_model.text().strip(),
            )
            translator = OllamaTranslator(cfg)
            if translator.health_check():
                QMessageBox.information(self, "成功", "✅ Ollama 连接正常，模型已加载")
            else:
                QMessageBox.warning(self, "失败", "❌ 无法连接 Ollama 或无可用模型")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"❌ 检查失败：{e}")

    def _update_translator_status(self) -> None:
        """更新翻译状态标签"""
        translator_type = self._label_to_translate_type(self.cmb_translator_type.currentText())
        if translator_type == "offline":
            self.lbl_tr_status.setText("翻译：离线模式（仅显示原文）")
        elif translator_type == "ollama":
            url = self.txt_ollama_url.text().strip()
            model = self.txt_ollama_model.text().strip()
            self.lbl_tr_status.setText(f"翻译：Ollama\n地址：{url}\n模型：{model}")
        elif translator_type == "deepseek":
            key_preview = self.txt_deepseek_key.text()
            if key_preview:
                key_preview = key_preview[:8] + "***"
            self.lbl_tr_status.setText(f"翻译：DeepSeek API\nAPI 密钥：{key_preview or '未设置'}")
        elif translator_type == "baidu":
            app_id = self.txt_baidu_app_id.text().strip()
            self.lbl_tr_status.setText(f"翻译：百度翻译\nAPP ID：{app_id or '未设置'}")

    @Slot()
    def _about(self) -> None:
        QMessageBox.information(
            self,
            "关于 FFXIV 实时翻译",
            "版本：2.0（改进版）\n\n"
            "功能：\n"
            "• ROI 屏幕截图\n"
            "• Windows OCR 英文识别\n"
            "• 支持多种翻译后端（Ollama/DeepSeek/百度/离线）\n"
            "• 术语保护（人名/地名不翻译）\n"
            "• 自动去重\n\n"
            "使用流程：\n"
            "1. 刷新窗口 → 绑定 FFXIV\n"
            "2. 框选对白框 ROI\n"
            "3. 配置翻译服务（可选）\n"
            "4. 点击开始\n\n"
            "GitHub：https://github.com/yourusername/ffxiv-translator",
        )

    @Slot()
    def _show_quick_start(self) -> None:
        QMessageBox.information(
            self,
            "快速开始",
            "📖 快速开始指南\n\n"
            "【无翻译模式】\n"
            "1. 选择 \"离线（不翻译）\"\n"
            "2. 框选 ROI → 开始\n"
            "3. 只显示识别的英文\n\n"
            "【本地翻译（推荐）】\n"
            "前提：安装 Ollama\n"
            "1. ollama pull qwen2.5:7b-instruct-q4_K_M\n"
            "2. ollama serve\n"
            "3. 程序中选择 \"Ollama（本地）\"\n"
            "4. 点击 \"检查连接\" 验证\n"
            "5. 框选 ROI → 开始\n\n"
            "【DeepSeek API（快速）】\n"
            "1. 访问 https://api.deepseek.com\n"
            "2. 获取免费 API 密钥\n"
            "3. 程序中选择 \"DeepSeek API\"\n"
            "4. 粘贴 API 密钥\n"
            "5. 框选 ROI → 开始\n\n"
            "【百度翻译】\n"
            "1. 访问 https://api.fanyi.baidu.com\n"
            "2. 申请账号并获取 APP ID & 密钥\n"
            "3. 程序中选择 \"百度翻译\"\n"
            "4. 填入凭证\n"
            "5. 框选 ROI → 开始",
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

        # 构建翻译器配置
        translator_type = self._label_to_translate_type(self.cmb_translator_type.currentText())
        translator_config = None
        
        if translator_type == "ollama":
            translator_config = {
                "base_url": self.txt_ollama_url.text().strip(),
                "model": self.txt_ollama_model.text().strip(),
            }
        elif translator_type == "deepseek":
            if not self.txt_deepseek_key.text().strip():
                QMessageBox.warning(self, "配置不完整", "DeepSeek 模式需要填写 API 密钥")
                return
            translator_config = {
                "api_key": self.txt_deepseek_key.text().strip(),
                "base_url": self.txt_deepseek_url.text().strip(),
            }
        elif translator_type == "baidu":
            if not self.txt_baidu_app_id.text().strip() or not self.txt_baidu_secret.text().strip():
                QMessageBox.warning(self, "配置不完整", "百度翻译模式需要填写 APP ID 和密钥")
                return
            translator_config = {
                "app_id": self.txt_baidu_app_id.text().strip(),
                "secret_key": self.txt_baidu_secret.text().strip(),
            }

        cfg = CaptureConfig(
            hwnd=self._hwnd,
            roi_screen=(self._roi_screen.left, self._roi_screen.top, self._roi_screen.width, self._roi_screen.height),
            fps=int(self.spn_fps.value()),
            ocr_interval_ms=int(self.spn_ocr_ms.value()),
            translator_type=translator_type,
            translator_config=translator_config,
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

    @Slot()
    def _save_config(self) -> None:
        """保存配置到文件"""
        try:
            # 更新配置对象
            self._config.translator_type = self._label_to_translate_type(self.cmb_translator_type.currentText())
            self._config.default_fps = int(self.spn_fps.value())
            self._config.default_ocr_interval_ms = int(self.spn_ocr_ms.value())
            self._config.window_width = self.width()
            self._config.window_height = self.height()
            
            # 更新翻译器配置
            self._config.ollama.base_url = self.txt_ollama_url.text().strip()
            self._config.ollama.model = self.txt_ollama_model.text().strip()
            self._config.deepseek.api_key = self.txt_deepseek_key.text().strip()
            self._config.deepseek.base_url = self.txt_deepseek_url.text().strip()
            self._config.baidu.app_id = self.txt_baidu_app_id.text().strip()
            self._config.baidu.secret_key = self.txt_baidu_secret.text().strip()
            
            # 保存
            self._config.save_to_file()
            QMessageBox.information(self, "成功", "✅ 配置已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"❌ 保存配置失败：{e}")

    def closeEvent(self, event) -> None:  # noqa: N802
        try:
            self._worker.stop_capture()
        finally:
            super().closeEvent(event)
