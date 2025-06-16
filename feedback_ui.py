# Interactive Feedback MCP UI
# Developed by Fábio Ferreira (https://x.com/fabiomlferreira)
# Inspired by/related to dotcursorrules.com (https://dotcursorrules.com/)
# Enhanced by Pau Oliva (https://x.com/pof) with ideas from https://github.com/ttommyth/interactive-mcp
import os
import sys
import json
import argparse
import uuid
from datetime import datetime
from typing import Optional, TypedDict, List

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QTextEdit, QGroupBox,
    QFrame, QToolButton, QFileDialog, QMessageBox, QGridLayout,
    QScrollArea
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer, QSettings, QBuffer, QByteArray, QMimeData
from PySide6.QtGui import QTextCursor, QIcon, QKeyEvent, QPalette, QColor, QPixmap, QImage, QClipboard, QPainter

class FeedbackResult(TypedDict):
    interactive_feedback: str
    image_paths: List[str]

def get_dark_mode_palette(app: QApplication):
    darkPalette = app.palette()
    darkPalette.setColor(QPalette.Window, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.WindowText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Base, QColor(42, 42, 42))
    darkPalette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    darkPalette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ToolTipText, Qt.white)
    darkPalette.setColor(QPalette.Text, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.Dark, QColor(35, 35, 35))
    darkPalette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    darkPalette.setColor(QPalette.Button, QColor(53, 53, 53))
    darkPalette.setColor(QPalette.ButtonText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.BrightText, Qt.red)
    darkPalette.setColor(QPalette.Link, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
    darkPalette.setColor(QPalette.HighlightedText, Qt.white)
    darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
    darkPalette.setColor(QPalette.PlaceholderText, QColor(127, 127, 127))
    return darkPalette

def get_light_mode_palette(app: QApplication):
    # Visual Studio风格的浅色主题
    lightPalette = app.palette()
    lightPalette.setColor(QPalette.Window, QColor(240, 240, 240))
    lightPalette.setColor(QPalette.WindowText, QColor(30, 30, 30))
    lightPalette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(180, 180, 180))
    lightPalette.setColor(QPalette.Base, QColor(255, 255, 255))
    lightPalette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    lightPalette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    lightPalette.setColor(QPalette.ToolTipText, QColor(30, 30, 30))
    lightPalette.setColor(QPalette.Text, QColor(30, 30, 30))
    lightPalette.setColor(QPalette.Disabled, QPalette.Text, QColor(180, 180, 180))
    lightPalette.setColor(QPalette.Dark, QColor(220, 220, 220))
    lightPalette.setColor(QPalette.Shadow, QColor(200, 200, 200))
    lightPalette.setColor(QPalette.Button, QColor(240, 240, 240))
    lightPalette.setColor(QPalette.ButtonText, QColor(30, 30, 30))
    lightPalette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(180, 180, 180))
    lightPalette.setColor(QPalette.BrightText, QColor(200, 0, 0))
    lightPalette.setColor(QPalette.Link, QColor(0, 120, 215))
    lightPalette.setColor(QPalette.Highlight, QColor(0, 120, 215))
    lightPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(200, 200, 200))
    lightPalette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    lightPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(180, 180, 180))
    lightPalette.setColor(QPalette.PlaceholderText, QColor(180, 180, 180))
    return lightPalette

class ImageLabel(QLabel):
    """可以显示图片的标签，支持删除功能"""
    deleted = Signal(str)  # 发送图片路径信号
    
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setToolTip("点击删除图片")
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("border: 1px solid gray; margin: 2px;")
        
        # 加载图片并调整大小
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(200, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(pixmap)
            self.setFixedSize(pixmap.width() + 4, pixmap.height() + 4)
        else:
            self.setText("图片加载失败")
            self.setFixedSize(200, 150)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            reply = QMessageBox.question(self, "确认删除", 
                                       "确定要删除这张图片吗？", 
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.deleted.emit(self.image_path)
                self.deleteLater()
        super().mousePressEvent(event)

class FeedbackTextEdit(QTextEdit):
    """支持粘贴图片的文本编辑器"""
    image_pasted = Signal(QImage)
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            # 查找父FeedbackUI实例并调用提交
            parent = self.parent()
            while parent and not isinstance(parent, FeedbackUI):
                parent = parent.parent()
            if parent:
                parent._submit_feedback()
        else:
            super().keyPressEvent(event)
    
    def canInsertFromMimeData(self, source):
        return source.hasImage() or super().canInsertFromMimeData(source)
    
    def insertFromMimeData(self, source):
        if source.hasImage():
            image = source.imageData()
            if not image.isNull():
                self.image_pasted.emit(image)
                return
        super().insertFromMimeData(source)

class FeedbackUI(QMainWindow):
    def __init__(self, prompt: str, predefined_options: Optional[List[str]] = None):
        super().__init__()
        self.prompt = prompt
        self.predefined_options = predefined_options or []
        self.uploaded_images = []  # 存储上传图片的路径

        self.feedback_result = None
        
        self.setWindowTitle("交互式反馈")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 尝试多个可能的图标位置
        icon_paths = [
            os.path.join(script_dir, "icon.ico"),
            os.path.join(script_dir, "images", "feedback.png")
        ]
        
        for icon_path in icon_paths:
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                break
                
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 确保images目录存在
        self.images_dir = os.path.join(script_dir, "images")
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
        
        self.settings = QSettings("InteractiveFeedbackMCP", "InteractiveFeedbackMCP")
        
        # 加载主窗口的一般UI设置（几何形状、状态）
        self.settings.beginGroup("MainWindow_General")
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(800, 600)
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - 800) // 2
            y = (screen.height() - 600) // 2
            self.move(x, y)
        state = self.settings.value("windowState")
        if state:
            self.restoreState(state)
            
        # 加载主题设置
        self.is_dark_mode = self.settings.value("isDarkMode", "true") == "true"
        self.settings.endGroup() # 结束 "MainWindow_General" 组

        # 创建主题图标
        self._create_theme_icons()
        self._create_ui()
        self._apply_theme()

    def _create_theme_icons(self):
        """创建主题切换图标（日/月）"""
        # 创建月亮图标（深色主题）
        self.moon_icon = QPixmap(32, 32)
        self.moon_icon.fill(Qt.transparent)
        
        # 创建太阳图标（浅色主题）
        self.sun_icon = QPixmap(32, 32)
        self.sun_icon.fill(Qt.transparent)
        
        # 使用文本作为临时图标
        self.moon_text = "🌙"
        self.sun_text = "☀️"

    def _create_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 反馈部分
        self.feedback_group = QGroupBox("")
        feedback_layout = QVBoxLayout(self.feedback_group)

        # 在反馈框内添加标题栏，包含描述和主题切换按钮
        title_bar = QHBoxLayout()
        
        # 描述标签
        self.description_label = QLabel(self.prompt)
        self.description_label.setWordWrap(True)
        title_bar.addWidget(self.description_label, 1)  # 1表示可伸展比例
        
        # 创建主题切换图标按钮
        self.theme_button = QToolButton()
        self.theme_button.setToolTip("切换" + ("浅色" if self.is_dark_mode else "深色") + "主题")
        self.theme_button.setText(self.sun_text if self.is_dark_mode else self.moon_text)
        self.theme_button.setFixedSize(32, 32)
        self.theme_button.clicked.connect(self._toggle_theme)
        title_bar.addWidget(self.theme_button)
        
        feedback_layout.addLayout(title_bar)

        # 添加预定义选项（如果有）
        self.option_checkboxes = []
        if self.predefined_options and len(self.predefined_options) > 0:
            # 创建滚动区域
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.NoFrame)
            
            # 创建容器小部件
            options_container = QWidget()
            
            # 使用网格布局
            grid_layout = QGridLayout(options_container)
            grid_layout.setContentsMargins(0, 10, 0, 10)
            grid_layout.setSpacing(10)
            
            # 计算合适的列数
            num_options = len(self.predefined_options)
            cols = min(3, num_options)  # 最多3列
            
            # 添加选项到网格
            for i, option in enumerate(self.predefined_options):
                row = i // cols
                col = i % cols
                
                checkbox = QCheckBox(option)
                self.option_checkboxes.append(checkbox)
                grid_layout.addWidget(checkbox, row, col)
            
            # 设置滚动区域的内容
            scroll_area.setWidget(options_container)
            
            # 设置最大高度，超过此高度将显示滚动条
            max_height = 200  # 最大高度200像素
            scroll_area.setMaximumHeight(max_height)
            
            feedback_layout.addWidget(scroll_area)
            
            # 添加分隔符
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            feedback_layout.addWidget(separator)

        # 自由格式文本反馈
        self.feedback_text = FeedbackTextEdit()
        self.feedback_text.image_pasted.connect(self._handle_pasted_image)
        font_metrics = self.feedback_text.fontMetrics()
        row_height = font_metrics.height()
        # 计算5行文本的高度 + 一些边距填充
        padding = self.feedback_text.contentsMargins().top() + self.feedback_text.contentsMargins().bottom() + 5 # 5是额外的垂直填充
        self.feedback_text.setMinimumHeight(5 * row_height + padding)

        self.feedback_text.setPlaceholderText("在此处输入您的反馈（按Ctrl+Enter提交）\n您可以直接粘贴截图(Ctrl+V)添加图片")
        
        # 图片预览区域
        self.images_container = QWidget()
        self.images_layout = QHBoxLayout(self.images_container)
        self.images_layout.setAlignment(Qt.AlignLeft)
        self.images_container.setVisible(False)  # 初始隐藏
        
        # 提交按钮
        submit_button = QPushButton("发送反馈")
        submit_button.clicked.connect(self._submit_feedback)

        feedback_layout.addWidget(self.feedback_text)
        feedback_layout.addWidget(self.images_container)
        feedback_layout.addWidget(submit_button)

        # 设置feedback_group的最小高度
        self.feedback_group.setMinimumHeight(self.description_label.sizeHint().height() + self.feedback_text.minimumHeight() + submit_button.sizeHint().height() + feedback_layout.spacing() * 2 + feedback_layout.contentsMargins().top() + feedback_layout.contentsMargins().bottom() + 10)

        # 添加部件
        layout.addWidget(self.feedback_group)

    def _handle_pasted_image(self, image):
        """处理粘贴的图片"""
        if image.isNull():
            return
            
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"pasted_image_{timestamp}_{unique_id}.png"
        filepath = os.path.join(self.images_dir, filename)
        
        # 保存图片
        if image.save(filepath):
            self._add_image_to_preview(filepath)
            self.uploaded_images.append(filepath)
            QMessageBox.information(self, "图片已添加", "截图已成功添加到反馈中")
        else:
            QMessageBox.warning(self, "错误", "无法保存图片")

    def _add_image_to_preview(self, image_path):
        """将图片添加到预览区域"""
        image_label = ImageLabel(image_path)
        image_label.deleted.connect(self._remove_image)
        self.images_layout.addWidget(image_label)
        
        # 显示图片容器
        if not self.images_container.isVisible():
            self.images_container.setVisible(True)

    def _remove_image(self, image_path):
        """从上传列表中移除图片"""
        if image_path in self.uploaded_images:
            self.uploaded_images.remove(image_path)
            
            # 如果没有图片了，隐藏容器
            if not self.uploaded_images:
                self.images_container.setVisible(False)

    def _toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self._apply_theme()
        self.theme_button.setToolTip("切换到" + ("浅色" if self.is_dark_mode else "深色") + "主题")
        self.theme_button.setText(self.sun_text if self.is_dark_mode else self.moon_text)
        
        # 保存主题设置
        self.settings.beginGroup("MainWindow_General")
        self.settings.setValue("isDarkMode", str(self.is_dark_mode).lower())
        self.settings.endGroup()
        
    def _apply_theme(self):
        app = QApplication.instance()
        if self.is_dark_mode:
            app.setPalette(get_dark_mode_palette(app))
        else:
            app.setPalette(get_light_mode_palette(app))

    def _submit_feedback(self):
        feedback_text = self.feedback_text.toPlainText().strip()
        selected_options = []
        
        # 获取选中的预定义选项（如果有）
        if self.option_checkboxes:
            for i, checkbox in enumerate(self.option_checkboxes):
                if checkbox.isChecked():
                    selected_options.append(self.predefined_options[i])
        
        # 合并选中的选项和反馈文本
        final_feedback_parts = []
        
        # 添加选中的选项
        if selected_options:
            final_feedback_parts.append("; ".join(selected_options))
        
        # 添加用户的文本反馈
        if feedback_text:
            final_feedback_parts.append(feedback_text)
            
        # 如果两部分都存在，则用换行符连接
        final_feedback = "\n\n".join(final_feedback_parts)
            
        self.feedback_result = FeedbackResult(
            interactive_feedback=final_feedback,
            image_paths=self.uploaded_images.copy()
        )
        self.close()

    def closeEvent(self, event):
        # 保存主窗口的一般UI设置（几何形状、状态）
        self.settings.beginGroup("MainWindow_General")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.endGroup()

        super().closeEvent(event)

    def run(self) -> FeedbackResult:
        self.show()
        QApplication.instance().exec()

        if not self.feedback_result:
            return FeedbackResult(
                interactive_feedback="",
                image_paths=[]
            )

        return self.feedback_result

def feedback_ui(prompt: str, predefined_options: Optional[List[str]] = None, output_file: Optional[str] = None) -> Optional[FeedbackResult]:
    app = QApplication.instance() or QApplication()
    
    # 主题将在FeedbackUI构造函数中应用
    app.setStyle("Fusion")
    
    ui = FeedbackUI(prompt, predefined_options)
    result = ui.run()

    if output_file and result:
        # 确保目录存在
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)
        # 将结果保存到输出文件
        with open(output_file, "w") as f:
            json.dump(result, f)
        return None

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行反馈UI")
    parser.add_argument("--prompt", default="我已实现您请求的更改。", help="向用户显示的提示")
    parser.add_argument("--predefined-options", default="", help="预定义选项的管道分隔列表(|||)")
    parser.add_argument("--output-file", help="保存反馈结果为JSON的路径")
    args = parser.parse_args()

    predefined_options = [opt for opt in args.predefined_options.split("|||") if opt] if args.predefined_options else None
    
    result = feedback_ui(args.prompt, predefined_options, args.output_file)
    if result:
        print(f"\n收到反馈：\n{result['interactive_feedback']}")
        if result['image_paths']:
            print(f"\n附带图片：\n{', '.join(result['image_paths'])}")
    sys.exit(0)
