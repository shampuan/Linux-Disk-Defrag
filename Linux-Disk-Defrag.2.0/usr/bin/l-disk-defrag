#!/usr/bin/env python3

import sys
import subprocess
import os
import json
import re
import random 

# PySide6 kütüphanesine geçiş yapıldı
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QMessageBox,
    QProgressBar, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QIcon, QPixmap

# GÜNCELLENMİŞ Renk kodları sözlüğü
COLOR_SCHEME = {
    "empty": QColor(Qt.white),            # Empty Space (White)
    "metadata": QColor(128, 0, 128),      # Purple - Metadata
    "non_fragmented": QColor(0, 170, 0),  # Bright Green - Non-fragmented files
    "fragmented": QColor("#a60909"),      # Dark Red/Maroon - Fragmented files
    "unmovable": QColor("#353535"),       # Dark Gray - Unmovable areas
    "unknown": QColor(192, 192, 192)      # Light Gray - Unknown/Busy status
}

# Disk Haritası Çizimi için Özel Widget
# Disk Haritası Çizimi için Özel Widget (l.py dosyasında)
class DiskMapWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setMinimumSize(400, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

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
        offset_x = self.lineWidth()
        offset_y = self.lineWidth()

        if not self.disk_map_data:
            painter.drawText(self.rect(), Qt.AlignCenter, "Disk Map Data Not Available / Loading...") 
            return

        for r in range(self.rows):
            for c in range(self.cols):
                color = self.disk_map_data[r][c]
                painter.setBrush(QColor(color))
                painter.setPen(QPen(QColor("#000000"), 0.5))

                x = offset_x + c * self.block_size + 0.5
                y = offset_y + r * self.block_size + 0.5
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

    def __init__(self, device_path, map_widget):
        super().__init__()
        self.device_path = device_path
        self.map_widget = map_widget
        self.is_running = True

    def run(self):
        try:
            self.progress.emit(10)
            if self.map_widget.fragmentation_score < 56: 
                self.map_widget.set_fragmentation_data(90)

            self.msleep(500)

            command = ["pkexec", "/usr/sbin/e4defrag", self.device_path]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            for i in range(10):
                if not self.is_running: return
                self.progress.emit(10 + i * 8)
                self.msleep(500)

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.progress.emit(100)
                # English translation
                self.finished.emit(f"Disk defragmentation successfully completed: {self.device_path}\n\n{stdout}") 
            else:
                # English translation
                self.error.emit(f"An error occurred during disk defragmentation:\n\n{stderr}") 

        except Exception as e:
            # English translation
            self.error.emit(f"An unexpected error occurred: {e}") 
        finally:
            if self.isFinished() or (hasattr(process, 'returncode') and process.returncode == 0):
                self.map_widget.set_fragmentation_data(0, 0.0)
            else:
                self.map_widget.set_fragmentation_data(self.map_widget.fragmentation_score, self.map_widget.actual_fragmented_ratio) 
            self.is_running = False


    def terminate(self):
        self.is_running = False
        super().terminate()


# Worker for e4defrag check (Analyze button)
class CheckDefragWorker(QThread):
    finished_with_map_data = Signal(dict, str) 
    error = Signal(str)

    def __init__(self, device_path):
        super().__init__()
        self.device_path = device_path

    def run(self):
        try:
            command = ["pkexec", "/usr/sbin/e4defrag", "-c", self.device_path]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                score = -1
                total_files = 0
                fragmented_files_count = 0
                
                lines = stdout.splitlines()
                
                for line in lines:
                    if "Fragmentation score" in line:
                        match = re.search(r'Fragmentation score\s*(\d+)', line)
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
                # English translation
                self.error.emit(f"An error occurred during disk fragmentation check:\n{stderr}") 

        except FileNotFoundError:
            # English translation
            self.error.emit("Error: '/usr/sbin/e4defrag' command not found. Please ensure that the 'e2fsprogs' package is installed.")
        except Exception as e:
            # English translation
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
        icon_analyze = QIcon(os.path.join(current_dir, 'analiz.png'))
        icon_defrag = QIcon(os.path.join(current_dir, 'def.png'))
        icon_info = QIcon(os.path.join(current_dir, 'info.png'))
        icon_size = QSize(32, 32) # Set fixed icon size

        icon_path = os.path.join(current_dir, 'defrag.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setGeometry(300, 300, 800, 600)
        main_layout = QVBoxLayout()

        disk_selection_layout = QHBoxLayout()
        # English translation
        disk_label = QLabel('Select Disk:')
        self.disk_combobox = QComboBox()
        self.disk_combobox.setStyleSheet("padding-top: 5px; padding-bottom: 5px;")
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

        # ABOUT BUTTON
        self.about_button = QPushButton(icon_info, 'About')
        self.about_button.setStyleSheet(button_style)
        self.about_button.clicked.connect(self.show_about)
        self.about_button.setIconSize(icon_size) 
        button_layout.addWidget(self.about_button)
        
        main_layout.addLayout(button_layout) 

        # English translation
        self.info_label = QLabel("Information about the selected disk will appear here.")
        self.info_label.setWordWrap(True)

        self.defrag_result_label = QLabel("")
        self.defrag_result_label.setWordWrap(True)
        self.defrag_result_label.setStyleSheet("font-weight: bold; color: green;")

        # Image (Logo) Area
        self.image_display_label = QLabel()
        self.image_display_label.setAlignment(Qt.AlignCenter)
        self.image_display_label.setScaledContents(True)
        self.image_display_label.setFixedSize(QSize(100, 100)) 
        self.image_display_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.load_initial_image() 

        info_vertical_layout = QVBoxLayout()
        info_vertical_layout.addSpacing(15) 
        info_vertical_layout.addWidget(self.info_label)
        info_vertical_layout.addWidget(self.defrag_result_label)

        info_and_image_container_layout = QHBoxLayout()
        info_and_image_container_layout.addLayout(info_vertical_layout)
        info_and_image_container_layout.addWidget(self.image_display_label, alignment=Qt.AlignRight | Qt.AlignTop) 
        main_layout.addLayout(info_and_image_container_layout) 
        main_layout.addSpacing(10) 

        # Busy Progress Bar
        self.busy_progress_bar = QProgressBar()
        self.busy_progress_bar.setRange(0, 100)
        self.busy_progress_bar.setValue(0)
        self.busy_progress_bar.setVisible(False) 
        main_layout.addWidget(self.busy_progress_bar)

        # Disk Map Section
        disk_map_group_box = QVBoxLayout()
        # English translation
        disk_map_label = QLabel("<b>Disk Map (Hypothetical)</b>")
        disk_map_label.setAlignment(Qt.AlignCenter)
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
            # English translation
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
        # Full English About text
        about_text = (
            "Linux Disk Defrag\n"
            "\n"
            "Version: 2.0.0\n"
            "License: GPLv3\n"
            "Programming Language: Python3\n"
            "Interface: PySide6\n"
            "Developer: A. Serhat KILIÇOĞLU\n"
            "Github: www.github.com/shampuan\n"
            "\n"
            "This program is an HDD defragmentation software developed for Debian-based systems. "
            "It increases performance on systems using HDDs (including servers) by defragmenting fragmented files "
            "without the need to shut down the system.\n"
            "\n"
            "This program comes with absolutely no warranty.\n"
            "\n"
            "Copyright © 2025 - A. Serhat KILIÇOĞLU"
        )
        # English translation
        QMessageBox.information(self, "About Linux Disk Defrag", about_text)

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
                # English translation
                self.disk_combobox.addItem("No disk found or insufficient privileges.")
                self.analyze_button.setEnabled(False)
                self.defrag_button.setEnabled(False)
                self.info_label.setText("No defragmentable EXT4 disk found on the system or insufficient privileges.")
            else:
                self.analyze_button.setEnabled(True)
                self.defrag_button.setEnabled(False)
                self.on_disk_selection_changed()

        except FileNotFoundError:
            # English translation
            QMessageBox.critical(self, "Error", "'lsblk' command not found. Please ensure that the 'util-linux' package is installed.")
            self.analyze_button.setEnabled(False)
            self.defrag_button.setEnabled(False)
        except Exception as e:
            # English translation
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
            
            # SSD check fix: Check if rota is explicitly "0" or False (non-rotational)
            # If rota is "1" or None/missing, assume HDD (rotational)
            is_ssd = (rotational == "0") or (rotational is False) 
            
            if is_ssd:
                display_name += f" [SSD]"
            else:
                display_name += f" [HDD/Rotational]" # English translation

            self.disks.append({
                "path": path,
                "fstype": fstype,
                "mountpoint": mountpoint if mountpoint else "None", # English translation
                "is_ssd": is_ssd # New key
            })
            self.disk_combobox.addItem(display_name)

    def on_disk_selection_changed(self):
        selected_index = self.disk_combobox.currentIndex()
        self.defrag_result_label.clear()
        self.disk_map_widget.set_fragmentation_data(-1)
        self.busy_progress_bar.setVisible(False)

        if selected_index == -1 or not self.disks or selected_index >= len(self.disks):
            # English translation
            self.info_label.setText("Please select a valid disk.")
            self.analyze_button.setEnabled(False)
            self.defrag_button.setEnabled(False)
            return

        selected_disk_info = self.disks[selected_index]
        fstype = selected_disk_info["fstype"]
        path = selected_disk_info["path"]
        mountpoint = selected_disk_info["mountpoint"]
        is_ssd = selected_disk_info["is_ssd"]

        # English translation
        disk_type_info = "Solid State Drive (SSD)" if is_ssd else "Hard Disk Drive (HDD/Rotational)"
        
        if fstype == "ext4":
            self.info_label.setText(
                f"Selected Disk: <b>{path}</b><br>"
                f"File System: <b>{fstype}</b><br>"
                f"Disk Type: <b>{disk_type_info}</b><br>"
                f"Mount Point: <b>{mountpoint}</b><br><br>"
                # English translation
                f"<b>This disk is defragmentable.</b> Click 'Analyze' button to check fragmentation." 
            )
            self.analyze_button.setEnabled(True)
            self.defrag_button.setEnabled(False)
        else:
            self.info_label.setText(
                f"Selected Disk: <b>{path}</b><br>"
                f"File System: <b>{fstype}</b><br>"
                f"Disk Type: <b>{disk_type_info}</b><br>"
                f"Mount Point: <b>{mountpoint}</b><br><br>"
                # English translation
                f"<span style='color:red;'><b>Warning:</b> Defragmentation cannot be performed directly on this disk in Linux environment because it is not an Ext filesystem.</span>"
            )
            self.analyze_button.setEnabled(False)
            self.defrag_button.setEnabled(False)

    def start_analysis(self):
        selected_index = self.disk_combobox.currentIndex()
        if selected_index == -1 or not self.disks or selected_index >= len(self.disks):
            # English translation
            QMessageBox.warning(self, "Warning", "Please select a disk.")
            return

        selected_disk_info = self.disks[selected_index]
        fstype = selected_disk_info["fstype"]
        path = selected_disk_info["path"]
        is_ssd = selected_disk_info["is_ssd"]

        if fstype != "ext4":
            # English translation
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
            "Defragmenting an SSD can even unnecessarily shorten its lifespan."
        )
        self.defrag_result_label.setText(result_text)
        self.defrag_result_label.setStyleSheet("font-weight: bold;")
        
        # English translation
        QMessageBox.information(self, "Analysis Result: SSD Detected", 
                                "This is an SSD. Defragmentation is unnecessary and may shorten the SSD's lifespan. "
                                "Your drive will continue to run at peak performance without defragmentation. "
                                "You don't have to do anything now.")

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
            f"Disk Type: <b>Hard Disk Drive (HDD/Rotational)</b><br>" # English translation
            f"Mount Point: <b>{mountpoint}</b><br><br>"
            f"<b>This disk is defragmentable.</b>" # English translation
        )
        self.info_label.setText(current_info_text)

        result_text = ""
        if score == 0:
            # English translation
            result_text = "Fragmentation Score: <b>0</b>. Disk is not fragmented. No defragmentation needed."
            self.defrag_result_label.setStyleSheet("font-weight: bold; color: green;")
        elif 1 <= score <= 30:
            # English translation
            result_text = f"Fragmentation Score: <b>{score}</b>. Very little fragmentation. Defragmentation is usually not required."
            self.defrag_result_label.setStyleSheet("font-weight: bold; color: blue;")
        elif 31 <= score <= 55:
            # English translation
            result_text = f"Fragmentation Score: <b>{score}</b>. Moderately fragmented. Defragmentation is recommended."
            self.defrag_result_label.setStyleSheet("font-weight: bold; color: orange;")
        elif score >= 56:
            # English translation
            result_text = f"Fragmentation Score: <b>{score}</b>. Highly fragmented! Disk needs defragmentation."
            self.defrag_result_label.setStyleSheet("font-weight: bold; color: red;")
        else:
            # English translation
            result_text = "Fragmentation Score could not be determined or an unknown situation occurred."
            self.defrag_result_label.setStyleSheet("font-weight: bold; color: gray;")
            self.defrag_button.setEnabled(False)

        self.defrag_result_label.setText(result_text)
        # English translation
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
            # English translation
            f"<span style='color:red;'><b>An error occurred during fragmentation check: {message}</b></span>"
        )
        self.analyze_button.setEnabled(True)
        self.defrag_button.setEnabled(False)
        self.disk_combobox.setEnabled(True)
        self.busy_progress_bar.setVisible(False)
        # English translation
        QMessageBox.critical(self, "Error", f"An error occurred during fragmentation check: {message}")
        self.defrag_result_label.clear()
        self.disk_map_widget.set_fragmentation_data(-1)

    def start_defrag(self):
        selected_index = self.disk_combobox.currentIndex()
        if selected_index == -1 or not self.disks or selected_index >= len(self.disks):
            # English translation
            QMessageBox.warning(self, "Warning", "Please select a disk.")
            return

        selected_disk_info = self.disks[selected_index]
        device_path = selected_disk_info["path"]
        fstype = selected_disk_info["fstype"]
        is_ssd = selected_disk_info["is_ssd"]
        
        if fstype != "ext4":
            # English translation
            QMessageBox.warning(self, "Error", f"Selected disk ({device_path}) is not in EXT4 format. Only EXT4 disks can be defragmented.")
            return
            
        if is_ssd:
             # English translation
             QMessageBox.warning(self, "Warning", f"The selected disk is an SSD. Defragmentation is not recommended. Please click the 'Analyze' button again and read the resulting warning.")
             self.defrag_button.setEnabled(False)
             return

        # Warning message (English translation)
        warning_message = ("This operation may take a long time. It is recommended not to use your computer, perform downloads, updates, "
                           "or other disk operations until the process is complete. Please let your computer rest until the operation is finished.")
        # English translation
        reply = QMessageBox.question(self, 'Confirmation and Warning', warning_message,
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.defrag_button.setEnabled(False)
            self.analyze_button.setEnabled(False)
            self.disk_combobox.setEnabled(False)

            # Set busy bar to % mode
            self.busy_progress_bar.setRange(0, 100)
            self.busy_progress_bar.setVisible(True)
            self.busy_progress_bar.setValue(0)
            
            # Show map as highly fragmented
            self.disk_map_widget.set_fragmentation_data(90)
            # English translation
            QMessageBox.information(self, "Defragmentation Starting", f"Disk defragmentation process is starting: <b>{device_path}</b>\n (May ask for password)")
            
            self.worker = DefragWorker(device_path, self.disk_map_widget)
            self.worker.finished.connect(self.defrag_finished)
            self.worker.error.connect(self.defrag_error)
            self.worker.progress.connect(self.busy_progress_bar.setValue)
            
            self.worker.start()

    def defrag_finished(self, message):
        # English translation
        QMessageBox.information(self, "Success", "Disk defragmentation complete.")
        self.busy_progress_bar.setVisible(False)
        self.reset_ui()

    def defrag_error(self, message):
        # English translation
        QMessageBox.critical(self, "Error", "An error occurred during disk defragmentation.")
        self.busy_progress_bar.setVisible(False)
        self.reset_ui()

    def closeEvent(self, event):
        is_worker_running = self.worker and self.worker.isRunning()
        is_check_worker_running = self.check_worker and self.check_worker.isRunning()

        if is_worker_running or is_check_worker_running:
            # English translation
            reply = QMessageBox.question(self, 'Warning',
                                         "An operation is currently running (analysis or defragmentation). Closing the application now may cause data loss or interrupt the process. Do you still want to close?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
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

    def reset_ui(self: QWidget) -> None:
        self.defrag_button.setEnabled(False)
        self.analyze_button.setEnabled(True)
        self.disk_combobox.setEnabled(True)
        self.worker = None
        self.check_worker = None
        self.on_disk_selection_changed()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DiskDefragmenterApp()
    ex.show()
    sys.exit(app.exec())
