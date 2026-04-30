from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QPainter, QGuiApplication
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget, QRubberBand


class RoiSelectDialog(QDialog):
    """
    全屏框选 ROI（屏幕坐标）。
    鼠标左键拖拽生成矩形，松开确认；Esc 取消。
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("框选对白框区域（ROI）")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool  # 避免在任务栏出现，也更容易捕获鼠标
        )
        self.setWindowModality(Qt.ApplicationModal)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        # 捕获全部鼠标事件，避免点击穿透
        self.setMouseTracking(True)

        screen = QGuiApplication.primaryScreen()
        geo = screen.geometry() if screen else QRect(0, 0, 1920, 1080)
        self.setGeometry(geo)

        self._origin: Optional[QPoint] = None
        self._rubber = QRubberBand(QRubberBand.Rectangle, self)
        self._rect: Optional[QRect] = None

        root = QWidget(self)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(20, 20, 20, 20)
        msg = QLabel(
            "拖拽鼠标框选对白框区域（ROI）\n"
            "松开鼠标确认，Esc 取消",
            root,
        )
        msg.setStyleSheet(
            "color: white; font-size: 16px; font-weight: bold;"
            "background: rgba(0,0,0,120); padding: 6px 10px; border-radius: 4px;"
        )
        layout.addWidget(msg, 0, Qt.AlignLeft | Qt.AlignTop)
        root.setGeometry(self.rect())
        root.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def selected_rect(self) -> Optional[QRect]:
        return self._rect

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
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
        # 最小 10x10，避免 DPI 缩放导致误拒
        if self._rect.width() < 10 or self._rect.height() < 10:
            self._rect = None
            self.reject()
            return
        self.accept()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
        painter.end()
