import sys
import os
import json
import ctypes
from ctypes import wintypes
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QSizePolicy, QFileDialog)
from PySide6.QtCore import Qt

# ==========================================
# Windows 原生 API 定义区
# ==========================================

def move_files_native(src_list, dst_folder):
    """调用 Windows 原生移动对话框"""
    FO_MOVE = 0x0001
    src_str = '\0'.join(src_list) + '\0\0'
    dst_str = os.path.abspath(dst_folder) + '\0\0'

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [
            ("hwnd", wintypes.HWND),
            ("wFunc", wintypes.UINT),
            ("pFrom", wintypes.LPCWSTR),
            ("pTo", wintypes.LPCWSTR),
            ("fFlags", wintypes.WORD),
            ("fAnyOperationsAborted", wintypes.BOOL),
            ("hNameMappings", ctypes.c_void_p),
            ("lpszProgressTitle", wintypes.LPCWSTR)
        ]

    shop = SHFILEOPSTRUCTW()
    shop.hwnd = None
    shop.wFunc = FO_MOVE
    shop.pFrom = src_str
    shop.pTo = dst_str
    # 0x0200 = FOF_NOCONFIRMMKDIR (目标文件夹不存在时直接创建)
    shop.fFlags = 0x0200 

    return ctypes.windll.shell32.SHFileOperationW(ctypes.byref(shop))

# --- 桌面停靠栏 (AppBar) API ---
ABM_NEW = 0x00000000
ABM_REMOVE = 0x00000001
ABM_SETPOS = 0x00000003
ABE_LEFT = 0

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

class APPBARDATA(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD),
                ("hWnd", wintypes.HWND),
                ("uCallbackMessage", wintypes.UINT),
                ("uEdge", wintypes.UINT),
                ("rc", RECT),
                ("lParam", wintypes.LPARAM)]


# ==========================================
# UI 组件与业务逻辑区
# ==========================================

class DropZoneLabel(QLabel):
    """自定义的可拖拽分类方块"""
    def __init__(self, name, target_path, hover_color):
        super().__init__(name)
        self.target_path = target_path
        self.hover_color = hover_color
        
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setWordWrap(True)
        
        self.base_style = """
            background-color: #2D2D30;
            color: #999999;
            font-size: 15px;
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            border-radius: 8px;
            border: 2px dashed #444444;
        """
        self.setStyleSheet(self.base_style)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.setStyleSheet(f"""
                background-color: #3E3E42;
                border: 2px solid {self.hover_color};
                color: #FFFFFF;
                font-weight: bold;
                font-size: 15px;
                border-radius: 8px;
            """)
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.base_style)
        event.accept()

    def dropEvent(self, event):
        self.setStyleSheet(self.base_style)
        urls = event.mimeData().urls()
        if not urls:
            return
        
        file_paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if file_paths:
            if not os.path.exists(self.target_path):
                try:
                    os.makedirs(self.target_path, exist_ok=True)
                except Exception as e:
                    print(f"创建目录失败: {e}")
            
            move_files_native(file_paths, self.target_path)


class DropToolWindow(QWidget):
    """主程序窗口"""
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.abd = APPBARDATA()
        self.abd.cbSize = ctypes.sizeof(APPBARDATA)
        self.abd.hWnd = int(self.winId()) 

        # 构建界面结构
        self.setup_custom_title_bar()
        
        # 准备存放方块的容器
        self.zone_container = QWidget()
        self.zone_layout = QVBoxLayout(self.zone_container)
        self.zone_layout.setContentsMargins(15, 15, 15, 15)
        self.zone_layout.setSpacing(15)
        self.main_layout.addWidget(self.zone_container)

        self.setup_geometry()
        self.apply_modern_stylesheet()
        
        # 初始加载默认配置
        self.load_config_data('config.json')

    def showEvent(self, event):
        super().showEvent(event)
        ctypes.windll.shell32.SHAppBarMessage(ABM_NEW, ctypes.byref(self.abd))
        
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.1)
        
        self.abd.uEdge = ABE_LEFT
        self.abd.rc.left = 0
        self.abd.rc.top = 0
        self.abd.rc.right = width
        self.abd.rc.bottom = screen.height()
        
        ctypes.windll.shell32.SHAppBarMessage(ABM_SETPOS, ctypes.byref(self.abd))

    def closeEvent(self, event):
        ctypes.windll.shell32.SHAppBarMessage(ABM_REMOVE, ctypes.byref(self.abd))
        super().closeEvent(event)

    def setup_geometry(self):
        screen = QApplication.primaryScreen().availableGeometry()
        width = int(screen.width() * 0.1)
        self.setGeometry(0, 0, width, screen.height())

    def setup_custom_title_bar(self):
        title_bar = QWidget()
        title_bar.setObjectName("TitleBar")
        title_bar.setFixedHeight(40)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 10, 0)
        
        title_label = QLabel("收集面板")
        title_label.setObjectName("TitleLabel")
        
        # 新增：切换配置按钮
        switch_btn = QPushButton("📁")
        switch_btn.setObjectName("IconBtn")
        switch_btn.setFixedSize(30, 30)
        switch_btn.setToolTip("选择配置文件")
        switch_btn.clicked.connect(self.switch_config)
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setObjectName("CloseBtn")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(switch_btn)
        title_layout.addWidget(close_btn)
        
        self.main_layout.addWidget(title_bar)

    def switch_config(self):
        """弹出文件选择器，加载新的 JSON"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择配置文件", 
            "", 
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.load_config_data(file_path)

    def load_config_data(self, config_file):
        """清空旧方块，读取新配置并渲染"""
        # 1. 清理现有的所有方块
        while self.zone_layout.count():
            item = self.zone_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # 2. 读取新配置
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                categories = config_data.get('categories', {})
                for name, info in categories.items():
                    path = info.get('path', '')
                    color = info.get('color', '#007ACC')
                    
                    zone = DropZoneLabel(name, path, color)
                    zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                    self.zone_layout.addWidget(zone)
                    
            except json.JSONDecodeError as e:
                self.show_error_zone(f"JSON 格式错误\n{str(e)}")
            except Exception as e:
                self.show_error_zone(f"读取配置失败\n{str(e)}")
        else:
            self.show_error_zone("未找到配置\n点击上方 📁 重新选择")

    def show_error_zone(self, message):
        error_zone = QLabel(message)
        error_zone.setAlignment(Qt.AlignCenter)
        error_zone.setStyleSheet("""
            background-color: #2D2D30;
            color: #E81123; 
            font-size: 14px;
            font-weight: bold;
            border-radius: 8px;
            border: 2px dashed #E81123;
        """)
        error_zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.zone_layout.addWidget(error_zone)

    def apply_modern_stylesheet(self):
        self.setStyleSheet("""
            QWidget#MainWindow {
                background-color: #1E1E1E;
                border-right: 1px solid #333333;
            }
            QWidget#TitleBar {
                background-color: #252526;
                border-bottom: 1px solid #333333;
            }
            QLabel#TitleLabel {
                color: #CCCCCC;
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
            QPushButton#CloseBtn, QPushButton#IconBtn {
                background-color: transparent;
                color: #888888;
                font-size: 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton#CloseBtn:hover {
                background-color: #E81123;
                color: white;
            }
            QPushButton#IconBtn:hover {
                background-color: #3E3E42;
                color: white;
            }
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DropToolWindow()
    window.show()
    sys.exit(app.exec())