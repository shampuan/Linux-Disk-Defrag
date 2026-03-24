#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import os
import json
import re
import random 

# PyQt6 kütüphanesine geçiş yapıldı
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QMessageBox,
    QProgressBar, QFrame, QSizePolicy, QDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal as Signal, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QIcon, QPixmap

# Linux/Debian tabanlı sistemler için X11 zorlaması
os.environ['QT_QPA_PLATFORM'] = 'xcb'

# GÜNCELLENMİŞ Renk kodları sözlüğü
COLOR_SCHEME = {
    "empty": QColor(Qt.GlobalColor.white),  # Empty Space (White)
    "metadata": QColor(128, 0, 128),      # Purple - Metadata
    "non_fragmented": QColor(0, 170, 0),  # Bright Green - Non-fragmented files
    "fragmented": QColor("#a60909"),      # Dark Red/Maroon - Fragmented files
    "unmovable": QColor("#353535"),       # Dark Gray - Unmovable areas
    "unknown": QColor(192, 192, 192)      # Light Gray - Unknown/Busy status
}

# Disk Haritası Çizimi için Özel Widget (l.py dosyasında)
class DiskMapWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setMinimumSize(400, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.block_size = 10 
        self.disk_map_data = [] 
        self.cols = 0
        self.rows = 0

        self.fragmentation_score = -1 
        self.actual_fragmented_ratio = None 
        self.generate_dummy_map_data() 
        self.update()

    def set_fragmentation_data(self, score, actual_fragmented_ratio=None):
        """Sets the score and ratio based on real analysis. -1 score triggers busy/gray map."""
        self.fragmentation_score = score
        self.actual_fragmented_ratio = actual_fragmented_ratio 
        self.generate_dummy_map_data() 
        self.update() 

    def generate_dummy_map_data(self):
        widget_width = self.width() - self.lineWidth() * 2
        widget_height = self.height() - self.lineWidth() * 2

        if widget_width <= 0 or widget_height <= 0:
            self.cols = 0
            self.rows = 0
            self.disk_map_data = []
            return

        self.cols = widget_width // self.block_size
        self.rows = widget_height // self.block_size
        total_blocks = self.cols * self.rows

        if total_blocks == 0:
            self.disk_map_data = []
            return

        # Map is Busy/Unknown, fill entirely with Gray
        if self.fragmentation_score == -1:
            self.disk_map_data = [[COLOR_SCHEME["unknown"]] * self.cols for _ in range(self.rows)]
            return

        # 1. Determine Color Ratios
        if self.actual_fragmented_ratio is not None:
            fragmented_ratio = self.actual_fragmented_ratio
        else:
            fragmented_ratio = 0.0
            if self.fragmentation_score == 0: 
                fragmented_ratio = 0.0
            elif 1 <= self.fragmentation_score <= 30: 
                fragmented_ratio = 0.1
            elif 31 <= self.fragmentation_score <= 55: 
                fragmented_ratio = 0.35
            elif self.fragmentation_score >= 56: 
                fragmented_ratio = 0.55
        
        empty_ratio = 0.15 
        metadata_ratio = 0.03 
        unmovable_ratio = 0.07 
        
        num_fragmented = int(total_blocks * fragmented_ratio)
        num_empty = int(total_blocks * empty_ratio)
        num_metadata = int(total_blocks * metadata_ratio)
        num_unmovable = int(total_blocks * unmovable_ratio)

        remaining = total_blocks - (num_fragmented + num_empty + num_metadata + num_unmovable)
        num_non_fragmented = max(0, remaining)
        
        current_total = num_fragmented + num_non_fragmented + num_empty + num_metadata + num_unmovable
        if current_total > total_blocks:
            num_non_fragmented -= (current_total - total_blocks)
            num_non_fragmented = max(0, num_non_fragmented)

        
        # 2. Add Block Types to a Logically Ordered List
        
        block_types = []
        
        # Tüm disklerde Metadata en başta yer alsın.
        block_types.extend([COLOR_SCHEME["metadata"]] * num_metadata)

        # FIX: Fragmentation score 0 ise rastgeleliği kaldır, sabit bir düzen ver.
        if self.fragmentation_score == 0:
            
            # SSD/Mükemmel durum: Blokları düzenli olarak arka arkaya yerleştir
            block_types.extend([COLOR_SCHEME["unmovable"]] * num_unmovable)
            block_types.extend([COLOR_SCHEME["non_fragmented"]] * num_non_fragmented)
            block_types.extend([COLOR_SCHEME["empty"]] * num_empty)
            
        else:
            # Fragmented Disks (HDD): Rastgeleliği koru

            non_fragmented_list = []
            i = 0
            while i < num_non_fragmented:
                # Use smaller, random chunks for HDD visualization
                block_count = random.randint(3, 5) 
                actual_count = min(block_count, num_non_fragmented - i)
                non_fragmented_list.extend([COLOR_SCHEME["non_fragmented"]] * actual_count)
                i += actual_count
            
            fragmented_list = [COLOR_SCHEME["fragmented"]] * num_fragmented
            unmovable_blocks = [COLOR_SCHEME["unmovable"]] * num_unmovable
            
            main_content_list = non_fragmented_list + fragmented_list
            random.shuffle(main_content_list) # Keep shuffling for fragmentation visualization

            for block in unmovable_blocks:
                insert_index = random.randint(0, len(main_content_list))
                main_content_list.insert(insert_index, block)

            block_types.extend(main_content_list)
            block_types.extend([COLOR_SCHEME["empty"]] * num_empty)
        
        # 3. Convert List to 2D Map (remains the same)
        current_length = len(block_types)
        if current_length < total_blocks:
            block_types.extend([COLOR_SCHEME["unknown"]] * (total_blocks - current_length))
        elif current_length > total_blocks:
            block_types = block_types[:total_blocks]
            
        # 4. Fill the 2D map
        self.disk_map_data = []
        for i in range(self.rows):
            row_data = []
            for j in range(self.cols):
                index = i * self.cols + j
                if index < len(block_types):
                    row_data.append(block_types[index])
                else:
                    row_data.append(COLOR_SCHEME["unknown"])
            self.disk_map_data.append(row_data)

    def paintEvent(self, event):
        painter = QPainter(self)
        # painter.setRenderHint(QPainter.RenderHint.Antialiasing) <-- ızgarayı çirkinleştiriyordu.
        offset_x = self.lineWidth()
        offset_y = self.lineWidth()

        if not self.disk_map_data:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Disk Map Data Not Available / Loading...") 
            return

        for r in range(self.rows):
            for c in range(self.cols):
                color = self.disk_map_data[r][c]
                painter.setBrush(QColor(color))
                painter.setPen(QPen(QColor("#000000"), 1, Qt.PenStyle.SolidLine))

                x = int(offset_x + c * self.block_size)
                y = int(offset_y + r * self.block_size)
                painter.drawRect(x, y, self.block_size, self.block_size)

        painter.end()

    def resizeEvent(self, event):
        self.generate_dummy_map_data()
        self.update()


# Disk defragmentation worker thread
class DefragWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int)
    map_data_update = Signal(int, object)  # score ve ratio için yeni sinyal

    def __init__(self, device_path, map_widget):
        super().__init__()
        self.device_path = device_path
        self.map_widget = map_widget
        self.is_running = True

    def run(self):
        try:
            self.progress.emit(10)
            if self.map_widget.fragmentation_score < 56: 
                self.map_data_update.emit(90, None)

            self.msleep(500)

            # Önce kullanıcı tarafından doğrulanan yolu, yoksa sistemdeki yolu kullan
            cmd_path = "/usr/sbin/e4defrag" if os.path.exists("/usr/sbin/e4defrag") else "e4defrag"
            command = ["pkexec", cmd_path, self.device_path]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            for i in range(10):
                if not self.is_running: return
                self.progress.emit(10 + i * 8)
                self.msleep(500)

            stdout, stderr = process.communicate()

            if not stdout.strip():
                self.error.emit("Analysis output could not be retrieved. The process may have been canceled or permission was not granted.")
                return

            if process.returncode != 0:
                self.error.emit(f"An error occurred during disk analysis:\n\n{stderr}")
                return

            # Analiz başarılıysa buradan sonra score yakalama döngüsü (lines = stdout.splitlines() vb.) başlar. 

        except Exception as e:
            
            self.error.emit(f"An unexpected error occurred: {e}") 
        finally:
            success = False
            try:
                if 'process' in locals() and process.returncode == 0:
                    success = True
            except:
                pass
            
            if success:
                self.map_data_update.emit(0, 0.0)
            else:
                self.map_data_update.emit(-1, None)
            self.is_running = False


    def terminate(self):
        self.is_running = False
        super().terminate()

# SSD Optimization (TRIM) worker thread
class OptimizeWorker(QThread):
    finished = Signal(str)
    error = Signal(str)
    progress = Signal(int)

    def __init__(self, device_path, mountpoint):
        super().__init__()
        self.device_path = device_path
        self.mountpoint = mountpoint

    def run(self):
        try:
            
            # Eğer mountpoint yoksa (None), kök dizine fallback yapıyoruz
            target = self.mountpoint
            cmd_path = "/usr/sbin/fstrim" if os.path.exists("/usr/sbin/fstrim") else "fstrim"
            command = ["pkexec", cmd_path, "-v", target]
            
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                
                trim_output = stdout.strip()
                # Örneğin: /: 1.2 GiB (123456789 bytes) trimmed demesi için.
                match = re.search(r"\((.*?) bytes\)", trim_output)
                if match:
                    bytes_val = int(match.group(1))
                    if bytes_val == 0:
                        final_msg = "0 B (Drive is already optimized.)"
                    else:
                        final_msg = trim_output
                else:
                    final_msg = trim_output
                
                self.finished.emit(final_msg)
            else:
                self.error.emit(f"{stderr}")

        except Exception as e:
            self.error.emit(f"An unexpected error occurred: {e}")

# Worker for e4defrag check (Analyze button)
class CheckDefragWorker(QThread):
    finished_with_map_data = Signal(dict, str) 
    error = Signal(str)

    def __init__(self, device_path):
        super().__init__()
        self.device_path = device_path

    def run(self):
        try:
            cmd_path = "/usr/sbin/e4defrag" if os.path.exists("/usr/sbin/e4defrag") else "e4defrag"
            command = ["pkexec", cmd_path, "-c", self.device_path]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                score = -1
                total_files = 0
                fragmented_files_count = 0
                
                lines = stdout.splitlines()
                
                for line in lines:
                    if "Fragmentation score" in line:
                        match = re.search(r'Fragmentation score[:\s]+(\d+)', line)
                        if match:
                            score = int(match.group(1))
                    
                    elif "Total files" in line:
                        match = re.search(r'Total files:\s*(\d+)', line)
                        if match:
                            total_files = int(match.group(1))

                    elif "Fragmented files" in line:
                        match = re.search(r'Fragmented files:\s*(\d+)', line)
                        if match:
                            fragmented_files_count = int(match.group(1))
                            
                    elif "No fragmentation found" in line and score == -1:
                        score = 0
                
                fragmented_ratio = 0.0
                if score == 0:
                    fragmented_ratio = 0.0
                elif total_files > 0 and score != -1:
                    fragment_rate_by_files = fragmented_files_count / total_files
                    fragmented_ratio = (score / 100.0) * (fragment_rate_by_files * 0.5 + 0.5) 
                    fragmented_ratio = min(max(0.0, fragmented_ratio), 0.55) 

                elif score != -1:
                    fragmented_ratio = min(score / 100.0, 0.55)
                    
                
                map_data = {
                    "score": score,
                    "fragmented_ratio": fragmented_ratio,
                    "full_output": stdout
                }
                
                self.finished_with_map_data.emit(map_data, stdout)
                
            else:
                 
                self.error.emit(f"An error occurred during disk fragmentation check:\n{stderr}") 

        except FileNotFoundError:
             
            self.error.emit("Error: '/usr/sbin/e4defrag' command not found. Please ensure that the 'e2fsprogs' package is installed.")
        except Exception as e:
             
            self.error.emit(f"An unexpected error occurred during fragmentation check: {e}")

class DiskDefragmenterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.check_worker = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Linux Disk Defrag')
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Button styles and icon definitions
        button_style = "min-height: 30px; min-width: 100px; padding: 5px;" 
        icon_analyze = QIcon(str(os.path.join(current_dir, 'analiz.png')))
        icon_defrag = QIcon(str(os.path.join(current_dir, 'def.png')))
        icon_info = QIcon(str(os.path.join(current_dir, 'info.png')))
        icon_optimize = QIcon(str(os.path.join(current_dir, 'optimize-SSD.png')))
        icon_size = QSize(32, 32)

        icon_path = os.path.join(current_dir, 'defrag.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setGeometry(300, 300, 800, 600)
        main_layout = QVBoxLayout()

        disk_selection_layout = QHBoxLayout()
         
        disk_label = QLabel('Select Disk:')
        self.disk_combobox = QComboBox()
        disk_selection_layout.addStretch(1)
        self.disk_combobox.setMaximumWidth(450)
        # self.disk_combobox.setStyleSheet("padding: 5px 15px 5px 15px;")
        self.disk_combobox.setStyleSheet("QComboBox { padding-left: 10px; padding-right: 10px; min-height: 30px; }")
        disk_selection_layout.addWidget(disk_label)
        disk_selection_layout.addWidget(self.disk_combobox)
        main_layout.addLayout(disk_selection_layout)

        button_layout = QHBoxLayout()
        
        # ANALYZE BUTTON
        self.analyze_button = QPushButton(icon_analyze, 'Analyze')
        self.analyze_button.setStyleSheet(button_style)
        self.analyze_button.clicked.connect(self.start_analysis)
        self.analyze_button.setIconSize(icon_size) 
        button_layout.addWidget(self.analyze_button)

        # DEFRAGMENT BUTTON
        self.defrag_button = QPushButton(icon_defrag, 'Defragment')
        self.defrag_button.setStyleSheet(button_style)
        self.defrag_button.clicked.connect(self.start_defrag)
        self.defrag_button.setEnabled(False)
        self.defrag_button.setIconSize(icon_size) 
        button_layout.addWidget(self.defrag_button)
        
        # OPTIMIZE (SSD) BUTTON
        self.optimize_button = QPushButton(icon_optimize, 'Optimize SSD')
        self.optimize_button.setStyleSheet(button_style)
        self.optimize_button.clicked.connect(self.start_optimization)
        self.optimize_button.setEnabled(False)
        self.optimize_button.setIconSize(icon_size) 
        button_layout.addWidget(self.optimize_button)

        # ABOUT BUTTON
        self.about_button = QPushButton(icon_info, 'About')
        self.about_button.setStyleSheet(button_style)
        self.about_button.clicked.connect(self.show_about)
        self.about_button.setIconSize(icon_size) 
        button_layout.addWidget(self.about_button)
        
        main_layout.addLayout(button_layout) 

        
        self.info_label = QLabel("Information about the selected disk will appear here.")
        self.info_label.setWordWrap(True)

        self.defrag_result_label = QLabel("")
        self.defrag_result_label.setWordWrap(True)
        self.defrag_result_label.setStyleSheet("font-weight: bold; color: green;")

        # Image (Logo) Area
        self.image_display_label = QLabel()
        self.image_display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_display_label.setScaledContents(True)
        self.image_display_label.setFixedSize(100, 100) 
        self.image_display_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.load_initial_image() 

        info_vertical_layout = QVBoxLayout()
        info_vertical_layout.addSpacing(15) 
        info_vertical_layout.addWidget(self.info_label)
        info_vertical_layout.addWidget(self.defrag_result_label)

        info_and_image_container_layout = QHBoxLayout()
        info_and_image_container_layout.addLayout(info_vertical_layout)
        info_and_image_container_layout.addWidget(self.image_display_label, alignment=(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)) 
        main_layout.addLayout(info_and_image_container_layout) 
        main_layout.addSpacing(10) 

        # Busy Progress Bar
        self.busy_progress_bar = QProgressBar()
        self.busy_progress_bar.setTextVisible(False)
        self.busy_progress_bar.setRange(0, 0)
        self.busy_progress_bar.setValue(0)
        self.busy_progress_bar.setVisible(False) 
        main_layout.addWidget(self.busy_progress_bar)

        # Disk Map Section
        disk_map_group_box = QVBoxLayout()
        
        disk_map_label = QLabel("<b>Disk Map (Hypothetical)</b>")
        disk_map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disk_map_group_box.addWidget(disk_map_label)
        
        self.disk_map_widget = DiskMapWidget(self)
        disk_map_group_box.addWidget(self.disk_map_widget)
        main_layout.addLayout(disk_map_group_box) 

        # Legend (English translation) 
        legend_layout = QHBoxLayout()
        self.add_legend_item(legend_layout, "Empty Space", "Available empty space on the disk", COLOR_SCHEME["empty"])
        self.add_legend_item(legend_layout, "Metadata", "File system structures and indexes", COLOR_SCHEME["metadata"])
        self.add_legend_item(legend_layout, "Non-fragmented", "Properly placed file blocks", COLOR_SCHEME["non_fragmented"])
        self.add_legend_item(legend_layout, "Fragmented", "Scattered file blocks, requires defragmentation", COLOR_SCHEME["fragmented"])
        self.add_legend_item(legend_layout, "Unmovable", "Areas locked by the system or user", COLOR_SCHEME["unmovable"])
        main_layout.addLayout(legend_layout) 

        self.populate_disks()
        self.disk_combobox.currentIndexChanged.connect(self.on_disk_selection_changed)
        self.on_disk_selection_changed()

        self.setLayout(main_layout)



    def load_initial_image(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, 'defrag.png')

        self.image_display_label.clear() 

        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            self.image_display_label.setPixmap(pixmap)
        else:
             
            self.image_display_label.setText("Logo (defrag.png) not found.")

    def add_legend_item(self, layout, text, tooltip, color):
        color_label = QLabel()
        color_label.setFixedSize(20, 15)
        color_label.setStyleSheet(f"background-color: {color.name()}; border: 1px solid gray;")
        
        text_label = QLabel(text)
        text_label.setToolTip(tooltip)
        
        item_layout = QHBoxLayout()
        item_layout.addWidget(color_label)
        item_layout.addWidget(text_label)
        item_layout.addStretch(1)
        layout.addLayout(item_layout)

    def show_about(self):
        
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About Linux Disk Defrag")
        
        layout = QHBoxLayout(about_dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20) 

        # Logo Alanı
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, 'defrag.png')
        logo_label = QLabel()
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        
        info_label = QLabel(
            "<h2>Linux Disk Defrag</h2>"
            "<b>Version: 3.1.0</b><br>"
            "License: GPLv3<br>"
            "Developer: A. Serhat KILIÇOĞLU<br>"
            "<a href='https://www.github.com/shampuan'>www.github.com/shampuan</a>"
            "<br><br>"
            "This software is a comprehensive disk maintenance tool designed for Debian-based systems. "
            "It provides high-performance defragmentation for HDDs and safe TRIM optimization for SSD and NVMe drives."
            "<br><br>"
            "<b>Disclaimer:</b> This program is distributed in the hope that it will be useful, "
            "but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY "
            "or FITNESS FOR A PARTICULAR PURPOSE."
            "<br><br>"
            "Copyright © 2026 - A. Serhat KILIÇOĞLU"
        )
        info_label.setWordWrap(True)
        info_label.setOpenExternalLinks(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setMaximumWidth(450)
        
        text_layout.addWidget(info_label)
        
        # Kapatma Butonu
        ok_button = QPushButton("OK")
        ok_button.setFixedWidth(80)
        ok_button.clicked.connect(about_dialog.accept)
        text_layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addLayout(text_layout)
        
        # Pencere boyutunu içeriğe göre daralt
        about_dialog.setFixedSize(about_dialog.sizeHint())
        about_dialog.exec()

    def populate_disks(self):
        try:
            # ROTA (Rotational) column added
            command = ["lsblk", "-o", "NAME,FSTYPE,MOUNTPOINT,PATH,ROTA", "--json"]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            disk_info = json.loads(result.stdout)

            self.disks = []
            self.disk_combobox.clear()

            for device in disk_info.get("blockdevices", []):
                if "children" in device:
                    for child_device in device["children"]:
                        self._add_disk_item(child_device)
                else:
                    self._add_disk_item(device)

            if not self.disks:
                 
                self.disk_combobox.addItem("No disk found or insufficient privileges.")
                self.analyze_button.setEnabled(False)
                self.defrag_button.setEnabled(False)
                self.optimize_button.setEnabled(is_ssd and fstype == "ext4")
                self.info_label.setText("No defragmentable EXT4 disk found on the system or insufficient privileges.")
            else:
                self.analyze_button.setEnabled(True)
                self.defrag_button.setEnabled(False)
                self.on_disk_selection_changed()

        except FileNotFoundError:
             
            QMessageBox.critical(self, "Error", "'lsblk' command not found. Please ensure that the 'util-linux' package is installed.")
            self.analyze_button.setEnabled(False)
            self.defrag_button.setEnabled(False)
        except Exception as e:
             
            QMessageBox.critical(self, "Error", f"An unexpected error occurred while listing disks: {e}")
            self.analyze_button.setEnabled(False)
            self.defrag_button.setEnabled(False)

    def _add_disk_item(self, device):
        fstype = device.get("fstype")
        mountpoint = device.get("mountpoint")
        path = device.get("path")
        rotational = device.get("rota") # Get ROTA information

        if fstype and path and path.startswith("/dev/"):
            display_name = f"{path} ({fstype})"
            if mountpoint:
                display_name += f" - {mountpoint}"
            
            # NVMe ve ROTA kontrolü ile hibrit SSD tespiti
            is_nvme = "nvme" in path.lower()
            is_ssd = is_nvme or (str(rotational) == "0" or rotational is False) 
            
            if is_ssd:
                display_name += f" [SSD]"
            else:
                display_name += f" [HDD/Rotational]"  

            self.disks.append({
                "path": path,
                "fstype": fstype,
                "mountpoint": mountpoint if mountpoint else "None",  
                "is_ssd": is_ssd 
            })
            self.disk_combobox.addItem(display_name)

    def on_disk_selection_changed(self):
        selected_index = self.disk_combobox.currentIndex()
        self.defrag_result_label.clear()
        self.disk_map_widget.set_fragmentation_data(-1)
        self.busy_progress_bar.setVisible(False)

        if selected_index == -1 or not self.disks or selected_index >= len(self.disks):
            
            self.info_label.setText("Please select a valid disk.")
            self.analyze_button.setEnabled(False)
            self.defrag_button.setEnabled(False)
            return

        selected_disk_info = self.disks[selected_index]
        fstype = selected_disk_info["fstype"]
        path = selected_disk_info["path"]
        mountpoint = selected_disk_info["mountpoint"]
        is_ssd = selected_disk_info["is_ssd"]

        
        disk_type_info = "Solid State Drive (SSD)" if is_ssd else "Hard Disk Drive (HDD/Rotational)"
        
        if fstype == "ext4":
            self.info_label.setText(
                f"Selected Disk: <b>{path}</b><br>"
                f"File System: <b>{fstype}</b><br>"
                f"Disk Type: <b>{disk_type_info}</b><br>"
                f"Mount Point: <b>{mountpoint}</b><br><br>"
                
                f"<b>This disk is defragmentable.</b> Click 'Analyze' button to check fragmentation." 
            )
            self.analyze_button.setEnabled(True)
            self.defrag_button.setEnabled(False)
            self.optimize_button.setEnabled(is_ssd)
        else:
            self.info_label.setText(
                f"Selected Disk: <b>{path}</b><br>"
                f"File System: <b>{fstype}</b><br>"
                f"Disk Type: <b>{disk_type_info}</b><br>"
                f"Mount Point: <b>{mountpoint}</b><br><br>"
                
                f"<span style='color:red;'><b>Warning:</b> Defragmentation cannot be performed directly on this disk in Linux environment because it is not an Ext filesystem.</span>"
            )
            self.analyze_button.setEnabled(False)
            self.defrag_button.setEnabled(False)
            self.optimize_button.setEnabled(False)

    def start_analysis(self):
        selected_index = self.disk_combobox.currentIndex()
        if selected_index == -1 or not self.disks or selected_index >= len(self.disks):
            
            QMessageBox.warning(self, "Warning", "Please select a disk.")
            return

        selected_disk_info = self.disks[selected_index]
        fstype = selected_disk_info["fstype"]
        path = selected_disk_info["path"]
        is_ssd = selected_disk_info["is_ssd"]

        if fstype != "ext4":
            
            QMessageBox.warning(self, "Error", f"Selected disk ({path}) is not in EXT4 format. Only EXT4 disks can be defragmented.")
            return
            
        # SSD Check: If SSD, display the "Good News" message.
        if is_ssd:
            self.display_ssd_info(path, fstype, selected_disk_info["mountpoint"])
            return

        # Normal HDD/Rotational disk analysis process
        self.analyze_button.setEnabled(False)
        self.defrag_button.setEnabled(False)
        self.disk_combobox.setEnabled(False)
        self.defrag_result_label.clear()
        
        # Set busy bar for analysis
        self.busy_progress_bar.setRange(0, 0)
        self.busy_progress_bar.setVisible(True)
        self.disk_map_widget.set_fragmentation_data(-1) # Set map to busy (gray)

        self.check_worker = CheckDefragWorker(path)
        self.check_worker.finished_with_map_data.connect( 
            lambda map_data, full_output: self.display_defrag_score(path, fstype, selected_disk_info["mountpoint"], map_data)
        )
        self.check_worker.error.connect(self.display_defrag_check_error)
        self.check_worker.start()
        
    def display_ssd_info(self, path, fstype, mountpoint):
        """Displays the 'Good News' message when an SSD is detected."""
        
        # Reset UI elements
        self.analyze_button.setEnabled(True)
        self.defrag_button.setEnabled(False)
        self.disk_combobox.setEnabled(True)
        self.busy_progress_bar.setVisible(False)
        
        # Show map as non-fragmented (SSD's ideal state)
        self.disk_map_widget.set_fragmentation_data(0, 0.0) 

        current_info_text = (
            f"Selected Disk: <b>{path}</b><br>"
            f"File System: <b>{fstype}</b><br>"
            f"Disk Type: <b>Solid State Drive (SSD)</b><br>"
            f"Mount Point: <b>{mountpoint}</b><br><br>"
            f"<b>This disk is defragmentable.</b>"
        )
        self.info_label.setText(current_info_text)

        # Good News Message (English translation) 
        result_text = (
            "<span style='color:green;'><b>GOOD NEWS! This is an SSD (Solid State Drive).</b></span><br>"
            "SSDs manage fragmentation automatically and **do not require** defragmentation. "
            "However, to maintain peak performance, you should use the **Optimize SSD (TRIM)** feature. "
            "This operation helps the drive manage unused data blocks efficiently without the risks of defragmentation."
        )
        self.defrag_result_label.setText(result_text)
        self.defrag_result_label.setStyleSheet("font-weight: bold;")
        self.optimize_button.setEnabled(True)
        
         
        QMessageBox.information(self, "Analysis Result: SSD Detected", 
                                "This is an SSD. Defragmentation is unnecessary and harmful for SSDs. "
                                "Instead, please use the 'Optimize SSD' button to perform a TRIM operation. "
                                "This will keep your drive healthy and fast.")

    def display_defrag_score(self, path, fstype, mountpoint, map_data):
        score = map_data["score"]
        fragmented_ratio = map_data["fragmented_ratio"]
        
        self.analyze_button.setEnabled(True)
        self.disk_combobox.setEnabled(True)
        self.defrag_button.setEnabled(True)
        
        self.busy_progress_bar.setVisible(False)

        current_info_text = (
            f"Selected Disk: <b>{path}</b><br>"
            f"File System: <b>{fstype}</b><br>"
            f"Disk Type: <b>Hard Disk Drive (HDD/Rotational)</b><br>"  
            f"Mount Point: <b>{mountpoint}</b><br><br>"
            f"<b>This disk is defragmentable.</b>"  
        )
        self.info_label.setText(current_info_text)

        result_text = ""
        if score == 0:
             
            result_text = "Fragmentation Score: <b>0</b>. Disk is not fragmented. No defragmentation needed."
            self.defrag_result_label.setStyleSheet("font-weight: bold; color: green;")
        elif 1 <= score <= 30:
             
            result_text = f"Fragmentation Score: <b>{score}</b>. Very little fragmentation. Defragmentation is usually not required."
            self.defrag_result_label.setStyleSheet("font-weight: bold; color: blue;")
        elif 31 <= score <= 55:
            
            result_text = f"Fragmentation Score: <b>{score}</b>. Moderately fragmented. Defragmentation is recommended."
            self.defrag_result_label.setStyleSheet("font-weight: bold; color: orange;")
        elif score >= 56:
            
            result_text = f"Fragmentation Score: <b>{score}</b>. Highly fragmented! Disk needs defragmentation."
            self.defrag_result_label.setStyleSheet("font-weight: bold; color: red;")
        else:
            
            result_text = "Fragmentation Score could not be determined or an unknown situation occurred."
            self.defrag_result_label.setStyleSheet("font-weight: bold; color: gray;")
            self.defrag_button.setEnabled(False)

        self.defrag_result_label.setText(result_text)
        
        QMessageBox.information(self, "Analysis Result", "Disk analysis complete.")
        self.disk_map_widget.set_fragmentation_data(score, fragmented_ratio)

    def display_defrag_check_error(self, message):
        selected_index = self.disk_combobox.currentIndex()
        selected_disk_info = self.disks[selected_index]
        path = selected_disk_info["path"]
        fstype = selected_disk_info["fstype"]
        mountpoint = selected_disk_info["mountpoint"]
        is_ssd = selected_disk_info["is_ssd"]
        disk_type_info = "Solid State Drive (SSD)" if is_ssd else "Hard Disk Drive (HDD/Rotational)"

        self.info_label.setText(
            f"Selected Disk: <b>{path}</b><br>"
            f"File System: <b>{fstype}</b><br>"
            f"Disk Type: <b>{disk_type_info}</b><br>"
            f"Mount Point: <b>{mountpoint}</b><br><br>"
            
            f"<span style='color:red;'><b>An error occurred during fragmentation check: {message}</b></span>"
        )
        self.analyze_button.setEnabled(True)
        self.defrag_button.setEnabled(False)
        self.disk_combobox.setEnabled(True)
        self.busy_progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Error", f"An error occurred during fragmentation check: {message}")
        self.defrag_result_label.clear()
        self.disk_map_widget.set_fragmentation_data(-1)

    def start_defrag(self):
        selected_index = self.disk_combobox.currentIndex()
        if selected_index == -1 or not self.disks or selected_index >= len(self.disks):
            
            QMessageBox.warning(self, "Warning", "Please select a disk.")
            return

        selected_disk_info = self.disks[selected_index]
        device_path = selected_disk_info["path"]
        fstype = selected_disk_info["fstype"]
        is_ssd = selected_disk_info["is_ssd"]
        
        if fstype != "ext4":
            
            QMessageBox.warning(self, "Error", f"Selected disk ({device_path}) is not in EXT4 format. Only EXT4 disks can be defragmented.")
            return
            
        if is_ssd:
             
             QMessageBox.warning(self, "Warning", f"The selected disk is an SSD. Defragmentation is not recommended. Please click the 'Analyze' button again and read the resulting warning.")
             self.defrag_button.setEnabled(False)
             return

        # Warning message (English translation)
        warning_message = ("This operation may take a long time. It is recommended not to use your computer, perform downloads, updates, "
                           "or other disk operations until the process is complete. Please let your computer rest until the operation is finished.")
        
        reply = QMessageBox.question(self, 'Confirmation and Warning', warning_message,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.optimize_button.setEnabled(False)
            self.defrag_button.setEnabled(False) 
            self.analyze_button.setEnabled(False)
            self.disk_combobox.setEnabled(False)

            # Set busy bar to % mode
            self.busy_progress_bar.setRange(0, 0)
            self.busy_progress_bar.setVisible(True)
            
            # Show map as highly fragmented
            self.disk_map_widget.set_fragmentation_data(90)
            
            QMessageBox.information(self, "Defragmentation Starting", f"Disk defragmentation process is starting: <b>{device_path}</b>\n (May ask for password)")
            
            self.worker = DefragWorker(device_path, self.disk_map_widget)
            self.worker.finished.connect(self.defrag_finished)
            self.worker.error.connect(self.defrag_error)
            self.worker.map_data_update.connect(self.disk_map_widget.set_fragmentation_data)
            
            self.worker.start()

    def defrag_finished(self, message):
        if isinstance(self.sender(), OptimizeWorker):
            # Clarifying why the user might see 0B or specific values
            info_note = (
    f"{message}\n\n"
    "This process may show different values or reset to zero after a few repetitions, which is completely normal. "
    "The ext4 file system cannot always release all empty blocks in a single pass. "
    "The system skips blocks that are temporarily locked or busy and handles them in subsequent attempts. "
    "The high values you see are not new data, but previously inaccessible areas now being reached. "
    "A decreasing value proves the cleaning is working thoroughly and reaching peak efficiency."
)
            QMessageBox.information(self, "SSD Optimization Complete", info_note)
        else:
            QMessageBox.information(self, "Success", f"Defragmentation complete.\n\n{message}")
            
        self.busy_progress_bar.setVisible(False)
        self.reset_ui()

    def defrag_error(self, message):
        # İşlem tipine göre hata başlığını belirle
        op_name = "SSD optimization (TRIM)" if isinstance(self.sender(), OptimizeWorker) else "disk defragmentation"
        QMessageBox.critical(self, "Error", f"An error occurred during {op_name}.\n\n{message}")
        self.busy_progress_bar.setVisible(False)
        self.reset_ui()

    def closeEvent(self, event):
        is_worker_running = self.worker and self.worker.isRunning()
        is_check_worker_running = self.check_worker and self.check_worker.isRunning()

        if is_worker_running or is_check_worker_running:
            
            reply = QMessageBox.question(self, 'Warning',
                                         "An operation is currently running (analysis or defragmentation). Closing the application now may cause data loss or interrupt the process. Do you still want to close?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if is_worker_running:
                    self.worker.terminate()
                    self.worker.wait(5000)
                if is_check_worker_running:
                    self.check_worker.terminate()
                    self.check_worker.wait(5000)
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def reset_ui(self):
        self.defrag_button.setEnabled(False)
        self.analyze_button.setEnabled(True)
        self.disk_combobox.setEnabled(True)
        self.worker = None
        self.check_worker = None
        self.on_disk_selection_changed()

    def start_optimization(self):
        selected_index = self.disk_combobox.currentIndex()
        selected_disk_info = self.disks[selected_index]
        mountpoint = selected_disk_info["mountpoint"]

        if mountpoint == "None":
            QMessageBox.warning(self, "Warning", "Cannot optimize a disk that is not mounted.")
            return

        reply = QMessageBox.question(self, 'Confirmation', 
                                     f"Are you sure you want to run TRIM optimization on {mountpoint}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.optimize_button.setEnabled(False)
            self.analyze_button.setEnabled(False)
            self.disk_combobox.setEnabled(False)
            
            self.busy_progress_bar.setVisible(True)
            self.busy_progress_bar.setRange(0, 0)

            self.worker = OptimizeWorker(selected_disk_info["path"], mountpoint)
            self.worker.finished.connect(self.defrag_finished) # Mevcut bitiş metodunu kullanabiliriz
            self.worker.error.connect(self.defrag_error)      # Mevcut hata metodunu kullanabiliriz
            
            self.worker.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = DiskDefragmenterApp()
    ex.show()
    sys.exit(app.exec())
