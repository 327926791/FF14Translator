from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget, QRubberBand


class RoiSelectDialog(QDialog):
    """
    全屏框选 ROI（屏幕坐标）。

    MVP 只提供简单框选：鼠标拖拽生成矩形，松开即确认；Esc 取消。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("框选对白框区域（ROI）")
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setWindowModality(Qt.ApplicationModal)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        screen = QGuiApplication.primaryScreen()
        geo = screen.geometry() if screen else QRect(0, 0, 1280, 720)
        self.setGeometry(geo)

        self._origin: Optional[QPoint] = None
        self._rubber = QRubberBand(QRubberBand.Rectangle, self)
        self._rect: Optional[QRect] = None

        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(18, 18, 18, 18)
        msg = QLabel(
            "拖拽框选对白框区域（ROI）。\n"
            "松开鼠标确认，按 Esc 取消。",
            root,
        )
        msg.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(msg, 0, Qt.AlignLeft | Qt.AlignTop)
        root.setGeometry(self.rect())

    def selected_rect(self) -> Optional[QRect]:
        return self._rect

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.LeftButton:
            return
        self._origin = event.position().toPoint()
        self._rubber.setGeometry(QRect(self._origin, self._origin))
        self._rubber.show()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._origin is None:
            return
        current = event.position().toPoint()
        self._rubber.setGeometry(QRect(self._origin, current).normalized())

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.LeftButton or self._origin is None:
            return
        current = event.position().toPoint()
        self._rect = QRect(self._origin, current).normalized()
        self._rubber.hide()
        if self._rect.width() < 30 or self._rect.height() < 20:
            self._rect = None
            self.reject()
            return
        self.accept()

    def paintEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet("background-color: rgba(0, 0, 0, 90);")
        super().paintEvent(event)

