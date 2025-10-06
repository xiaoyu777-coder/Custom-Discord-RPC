import sys
import os
import json
import time
from datetime import datetime

try:
	from PyQt5.QtWidgets import (
		QApplication,
		QWidget,
		QLabel,
		QLineEdit,
		QTextEdit,
		QPushButton,
		QVBoxLayout,
		QHBoxLayout,
		QGroupBox,
		QCheckBox,
		QFileDialog,
		QMessageBox,
	)
	from PyQt5.QtGui import QPixmap, QColor, QPainter, QFont
	from PyQt5.QtCore import Qt
except Exception as e:
	print("需要安装 PyQt5: pip install PyQt5")
	raise

# pypresence 为必须依赖，用于向本地 Discord 客户端设置 Rich Presence
try:
	from pypresence import Presence
except Exception:
	print("需要安装 pypresence: pip install pypresence")
	sys.exit(1)


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "presence_config.json")


DEFAULT_LARGE_IMAGE = "large_image_key"
DEFAULT_SMALL_IMAGE = "small_image_key"


class RPCSimulator(QWidget):
	"""Main GUI for managing Discord Rich Presence using a provided Client ID."""
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Custom Discord RPC")
		self.resize(760, 480)

		# Inputs
		self.details_input = QLineEdit()
		self.details_input.setPlaceholderText("Playing some cool stuff")
		self.state_input = QLineEdit()
		self.state_input.setPlaceholderText("In a match")
		self.large_text_input = QLineEdit()
		self.large_text_input.setPlaceholderText("Large image text")
		self.small_text_input = QLineEdit()
		self.small_text_input.setPlaceholderText("Small image text")
		self.start_timestamp_chk = QCheckBox("显示开始时间（现在）")

		# Developer Portal button
		self.open_dev_btn = QPushButton("打开 Discord Developer Portal")
		self.open_dev_btn.clicked.connect(self.open_developer_portal)
		# Theme toggle (暗/浅)
		self.theme_toggle_btn = QPushButton("主题：暗（点击切换）")
		self.theme_toggle_btn.setCheckable(False)
		self.theme_toggle_btn.clicked.connect(self.toggle_theme)

		# Client ID and image keys
		self.client_id_input = QLineEdit()
		self.client_id_input.setPlaceholderText("在此输入 Application Client ID（必需用于真实发布）")
		# large/small image 使用占位符（隐性文字），如果用户未输入则发布时使用占位符的值
		self.large_image_input = QLineEdit()
		self.large_image_input.setPlaceholderText(DEFAULT_LARGE_IMAGE)
		self.small_image_input = QLineEdit()
		self.small_image_input.setPlaceholderText(DEFAULT_SMALL_IMAGE)

		# Status summary + log
		# 现在用更简洁的状态摘要替代之前的 HTML 预览区域
		self.status_label = QLabel("状态：未连接")
		self.log_area = QTextEdit()
		self.log_area.setReadOnly(True)
		self.log_area.setMaximumHeight(140)
		self.clear_log_btn = QPushButton("清除日志")

		# Buttons
		self.save_btn = QPushButton("保存配置")
		self.load_btn = QPushButton("加载配置")
		self.start_real_btn = QPushButton("连接并发布")
		self.stop_real_btn = QPushButton("断开并清除")
		self.start_real_btn.setEnabled(False)
		self.stop_real_btn.setEnabled(False)

		# Layout
		left_layout = QVBoxLayout()
		# top actions: developer portal + theme toggle
		top_actions = QHBoxLayout()
		top_actions.addWidget(self.open_dev_btn)
		top_actions.addWidget(self.theme_toggle_btn)
		left_layout.addLayout(top_actions)
		left_layout.addWidget(QLabel("主要信息"))
		left_layout.addWidget(self.details_input)
		left_layout.addWidget(QLabel("次级信息"))
		left_layout.addWidget(self.state_input)
		left_layout.addWidget(QLabel("大图片标题"))
		left_layout.addWidget(self.large_text_input)
		left_layout.addWidget(QLabel("小图片标题"))
		left_layout.addWidget(self.small_text_input)

		left_layout.addWidget(QLabel("Client ID (必需)"))
		left_layout.addWidget(self.client_id_input)

		left_layout.addWidget(QLabel("大图片key"))
		left_layout.addWidget(self.large_image_input)
		left_layout.addWidget(QLabel("小图片key"))
		left_layout.addWidget(self.small_image_input)

		left_layout.addWidget(self.start_timestamp_chk)
		left_layout.addStretch()
		left_layout.addWidget(self.save_btn)
		left_layout.addWidget(self.load_btn)

		right_layout = QVBoxLayout()
		# 预览区域已移除，改为在状态栏显示简洁摘要
		btns = QHBoxLayout()
		btns.addWidget(self.start_real_btn)
		btns.addWidget(self.stop_real_btn)
		right_layout.addLayout(btns)
		right_layout.addWidget(self.status_label)
		right_layout.addWidget(QLabel("日志"))
		right_layout.addWidget(self.log_area)
		# Clear log button
		right_layout.addWidget(self.clear_log_btn)

		main_layout = QHBoxLayout()
		main_layout.addLayout(left_layout, 1)
		main_layout.addLayout(right_layout, 2)
		self.setLayout(main_layout)

		# Connections
		self.client_id_input.textChanged.connect(self.check_real_rpc_availability)
		# 字段变化时更新状态摘要
		self.details_input.textChanged.connect(self.update_preview)
		self.state_input.textChanged.connect(self.update_preview)
		self.large_text_input.textChanged.connect(self.update_preview)
		self.small_text_input.textChanged.connect(self.update_preview)
		self.start_timestamp_chk.stateChanged.connect(self.update_preview)
		self.large_image_input.textChanged.connect(self.update_preview)
		self.small_image_input.textChanged.connect(self.update_preview)

		self.save_btn.clicked.connect(self.save_config)
		self.load_btn.clicked.connect(self.load_config)

		self.start_real_btn.clicked.connect(self.start_real_presence)
		self.stop_real_btn.clicked.connect(self.stop_real_presence)
		self.clear_log_btn.clicked.connect(self.clear_log)

		# internal
		self.rpc_client = None
		self.rpc_start_time = None

		# 主题：默认暗色
		self.dark_theme = True
		self.apply_theme()

		# 初始化显示摘要
		self.update_preview()
		self.check_real_rpc_availability()

	# -------------------- UI helpers --------------------
	def append_log(self, *parts):
		msg = " ".join(str(p) for p in parts)
		ts = datetime.now().strftime("%H:%M:%S")
		self.log_area.append(f"[{ts}] {msg}")

	def clear_log(self):
		self.log_area.clear()
		self.append_log("Log cleared")

	# -------------------- developer portal --------------------
	def open_developer_portal(self):
		import webbrowser
		webbrowser.open("https://discord.com/developers/applications")

	def toggle_theme(self):
		# 切换主题并应用
		self.dark_theme = not getattr(self, 'dark_theme', True)
		self.apply_theme()

	def apply_theme(self):
		# 两套基本样式：暗色与浅色
		if getattr(self, 'dark_theme', True):
			# Dark
			self.theme_toggle_btn.setText("主题：暗（点击切换）")
			sheet = r"""
			QWidget { background: #0f1720; color: #e6eef6; font-family: Segoe UI, Microsoft YaHei, Arial; }
			QLineEdit, QTextEdit { background: #0b1220; border: 1px solid #1f2937; padding:6px; border-radius:6px; color:#e6eef6 }
			QPushButton { background: #2563eb; color:white; padding:8px; border:none; border-radius:8px; }
			QPushButton:hover { background: #1e40af; }
			QPushButton:disabled { background: #1e2935; color: #9aa8bf; border: 1px dashed #334155 }
			QLabel { color: #dbeafe; }
			QTextEdit { background: #071027; color:#cfe8ff }
			"""
		else:
			# Light
			self.theme_toggle_btn.setText("主题：浅（点击切换）")
			sheet = r"""
			QWidget { background: #f3f4f6; color: #0f1720; font-family: Segoe UI, Microsoft YaHei, Arial; }
			QLineEdit, QTextEdit { background: #ffffff; border: 1px solid #d1d5db; padding:6px; border-radius:6px; color:#0f1720 }
			QPushButton { background: #2563eb; color:white; padding:8px; border:none; border-radius:8px; }
			QPushButton:hover { background: #1e40af; }
			QPushButton:disabled { background: #e6eef6; color: #9aa8bf; border: 1px dashed #cbd5e1 }
			QLabel { color: #0f1720; }
			QTextEdit { background: #ffffff; color:#0f1720 }
			"""
		self.setStyleSheet(sheet)

	# -------------------- config / client id --------------------
	# (client_id file load/save removed) client id is expected to be entered in the input field

	def check_real_rpc_availability(self):
		has_client_id = bool(self.client_id_input.text().strip())
		# pypresence 为必需，程序在导入失败时已退出。这里只检测是否存在 client_id 输入
		self.start_real_btn.setEnabled(bool(has_client_id))
	
	# activity UI 已移除


	# -------------------- preview --------------------
	def update_preview(self):
		# 简洁的状态摘要，替代之前的 HTML 预览
		details = self.details_input.text() or "(无详情)"
		state = self.state_input.text() or "(无状态)"
		show_ts = self.start_timestamp_chk.isChecked()

		timestamp_str = ""
		if show_ts and self.rpc_start_time:
			ts = int(self.rpc_start_time)
			timestamp_str = f" • Started: {datetime.fromtimestamp(ts).strftime('%H:%M:%S')}"
		elif show_ts:
			timestamp_str = f" • Started: {datetime.now().strftime('%H:%M:%S')}"

		summary = f"{details} — {state}{timestamp_str}"
		self.status_label.setText("状态：" + summary)

	# -------------------- config --------------------
	def save_config(self):
		# 强制要求 client id 才能保存配置
		has_cid = bool(self.client_id_input.text().strip())
		if not has_cid:
			QMessageBox.warning(self, "缺少 Client ID", "必须提供 Client ID 才能保存配置。请在输入框中输入。")
			return

		data = {
			"details": self.details_input.text(),
			"state": self.state_input.text(),
			"large_text": self.large_text_input.text(),
			"small_text": self.small_text_input.text(),
			"large_image": self.large_image_input.text(),
			"small_image": self.small_image_input.text(),
			"client_id": self.client_id_input.text(),
			"start_ts": self.start_timestamp_chk.isChecked(),
		}
		# 让用户选择保存路径（支持任意位置）
		path, _ = QFileDialog.getSaveFileName(self, "保存配置为", CONFIG_FILE, "JSON 文件 (*.json);;All Files (*)")
		if not path:
			return
		try:
			with open(path, "w", encoding="utf-8") as f:
				json.dump(data, f, ensure_ascii=False, indent=2)
			self.append_log("Saved config to", path)
			QMessageBox.information(self, "保存成功", f"配置已保存到 {path}")
		except Exception as e:
			QMessageBox.warning(self, "保存失败", f"保存配置失败：{e}")

	def load_config(self):
		# 允许用户从任意路径加载配置
		path, _ = QFileDialog.getOpenFileName(self, "加载配置", os.path.dirname(CONFIG_FILE), "JSON 文件 (*.json);;All Files (*)")
		if not path:
			return
		try:
			with open(path, "r", encoding="utf-8") as f:
				data = json.load(f)
			self.details_input.setText(data.get("details", ""))
			self.state_input.setText(data.get("state", ""))
			self.large_text_input.setText(data.get("large_text", ""))
			self.small_text_input.setText(data.get("small_text", ""))
			self.large_image_input.setText(data.get("large_image", DEFAULT_LARGE_IMAGE))
			self.small_image_input.setText(data.get("small_image", DEFAULT_SMALL_IMAGE))
			self.client_id_input.setText(data.get("client_id", ""))
			# ...existing code...
			self.start_timestamp_chk.setChecked(data.get("start_ts", False))
			self.update_preview()
			self.append_log("Loaded config from", path)
			QMessageBox.information(self, "加载完成", f"配置已从 {path} 加载")
		except Exception as e:
			QMessageBox.warning(self, "加载失败", f"加载配置失败：{e}")

	# -------------------- RPC actions --------------------
	def get_client_id(self):
		# 只从输入框读取 client_id，取消文件读取逻辑
		cid = self.client_id_input.text().strip()
		return cid or None

	def start_real_presence(self):
		client_id = self.get_client_id()
		if not client_id:
			QMessageBox.warning(self, "缺少 client_id", "请在输入框中输入 Client ID。")
			return

		try:
			self.append_log("Connecting to Discord RPC with client_id", client_id)
			self.rpc_client = Presence(client_id)
			self.rpc_client.connect()
			self.append_log("Connected to Discord RPC")
		except Exception as e:
			QMessageBox.critical(self, "连接失败", f"连接到 Discord IPC 失败：{e}")
			self.append_log("Connection failed:", e)
			self.rpc_client = None
			return

		payload = self._build_payload()
		try:
			self.rpc_client.update(**payload)
			self.rpc_start_time = time.time() if self.start_timestamp_chk.isChecked() else None
			self.update_preview()
			self.start_real_btn.setEnabled(False)
			self.stop_real_btn.setEnabled(True)
			self.status_label.setText("状态：已连接并发布")
			self.append_log("Presence updated")
			QMessageBox.information(self, "已发布", "已将 Rich Presence 发布到本地 Discord 客户端。")
		except Exception as e:
			QMessageBox.critical(self, "更新失败", f"更新 Rich Presence 失败：{e}")
			self.append_log("Update failed:", e)

	def stop_real_presence(self):
		if self.rpc_client:
			try:
				self.rpc_client.clear()
				self.rpc_client.close()
			except Exception:
				pass
		self.rpc_client = None
		self.rpc_start_time = None
		self.start_real_btn.setEnabled(True)
		self.stop_real_btn.setEnabled(False)
		self.status_label.setText("状态：已断开")
		self.append_log("Disconnected and cleared presence")
		QMessageBox.information(self, "已停止", "真实 Rich Presence 已停止（如果之前已发布）。")

	def _build_payload(self):
		# 当 image key 输入为空时，使用 placeholder（默认）值
		large_key = self.large_image_input.text().strip() or self.large_image_input.placeholderText() or DEFAULT_LARGE_IMAGE
		small_key = self.small_image_input.text().strip() or self.small_image_input.placeholderText() or DEFAULT_SMALL_IMAGE

		# 构造 details，前置 activity 类型
		type_text = self.activity_type.currentText()
		if type_text == "不显示":
			prefix = ""
		elif type_text == "自定义...":
			prefix = self.activity_custom.text().strip()
		else:
			prefix = type_text

		details_val = self.details_input.text() or None
		if details_val and prefix:
			details_val = f"{prefix} {details_val}"

		payload = {
			"details": details_val,
			"state": self.state_input.text() or None,
			"large_image": large_key,
			"small_image": small_key,
			"large_text": self.large_text_input.text() or None,
			"small_text": self.small_text_input.text() or None,
		}
		if self.start_timestamp_chk.isChecked():
			payload["start"] = int(time.time())
		return payload


def main():
	if sys.platform.startswith("win"):
		import ctypes
		whnd = ctypes.windll.kernel32.GetConsoleWindow()
		if whnd != 0:
			ctypes.windll.user32.ShowWindow(whnd, 0)
			
	app = QApplication(sys.argv)
	win = RPCSimulator()
	win.show()
	return app.exec_()


if __name__ == "__main__":
	main()