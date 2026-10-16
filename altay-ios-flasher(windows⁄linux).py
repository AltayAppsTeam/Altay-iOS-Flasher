#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adios Engine (Altay Down iOS) - GUI Edition v2.6
Geliştirici: Kıvanç
Açıklama: Cihaz tarama butonu ve hata durumunda sıfırlama özellikli sürüm.
"""

import os
import sys
import subprocess
import time
import shutil
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

class AdiosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Adios (Altay Down iOS) v2.6")
        self.root.geometry("540x360")
        self.root.resizable(False, False)

        self.temp_dir = tempfile.mkdtemp(prefix="adios_fix_")
        self.selected_ipsw = None

        # Renk Paleti (Şık Koyu Tema)
        self.bg_color = "#1e1e1e"
        self.fg_color = "#d4d4d4"
        self.success_color = "#4ec9b0"
        self.warning_color = "#ce9178"

        self.root.configure(bg=self.bg_color)

        self.create_widgets()
        self.check_dependencies_on_startup()

    def create_widgets(self):
        title_label = tk.Label(
            self.root,
            text="ADIOS (Altay Down iOS) v2.6",
            font=("Helvetica", 14, "bold"),
            bg=self.bg_color,
            fg="#569cd6"
        )
        title_label.pack(pady=15)

        # 1. Adım: IPSW Seçme ve Cihaz Tarama Alanı
        frame_ipsw = tk.Frame(self.root, bg=self.bg_color)
        frame_ipsw.pack(fill=tk.X, padx=25, pady=5)

        self.btn_select = tk.Button(
            frame_ipsw,
            text="IPSW Seç",
            command=self.select_ipsw,
            bg="#333333", fg=self.fg_color, relief=tk.FLAT, width=11, font=("Helvetica", 9, "bold")
        )
        self.btn_select.pack(side=tk.LEFT)

        self.btn_scan = tk.Button(
            frame_ipsw,
            text="Cihazı Tara",
            command=self.thread_scan_device,
            bg="#333333", fg=self.fg_color, relief=tk.FLAT, width=11, font=("Helvetica", 9, "bold")
        )
        self.btn_scan.pack(side=tk.LEFT, padx=5)

        self.lbl_ipsw = tk.Label(
            frame_ipsw,
            text="IPSW Seçilmedi",
            bg=self.bg_color,
            fg=self.warning_color,
            anchor="w",
            font=("Helvetica", 8)
        )
        self.lbl_ipsw.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # 2. Adım: Başlat Butonu
        self.btn_flash = tk.Button(
            self.root,
            text="Otomatik DFU & Yüklemeyi Başlat",
            command=self.thread_start_auto_flash,
            bg="#264f78", fg="#ffffff", relief=tk.FLAT, font=("Helvetica", 11, "bold"), height=2
        )
        self.btn_flash.pack(fill=tk.X, padx=25, pady=15)

        # İlerleme ve Durum Gösterge Paneli
        frame_progress = tk.Frame(self.root, bg=self.bg_color)
        frame_progress.pack(fill=tk.X, padx=25, pady=5)

        self.lbl_status = tk.Label(
            frame_progress,
            text="Durum: Bekleniyor...",
            bg=self.bg_color,
            fg=self.fg_color,
            anchor="w",
            font=("Helvetica", 10, "bold")
        )
        self.lbl_status.pack(fill=tk.X, pady=2)

        self.lbl_percent = tk.Label(
            frame_progress,
            text="%0",
            bg=self.bg_color,
            fg=self.success_color,
            anchor="e",
            font=("Helvetica", 10, "bold")
        )
        self.lbl_percent.pack(anchor="e", pady=2)

        self.progress = ttk.Progressbar(
            frame_progress,
            orient="horizontal",
            length=490,
            mode="determinate"
        )
        self.progress.pack(fill=tk.X, pady=5)

    def check_dependencies_on_startup(self):
        for tool in ["idevicerestore", "irecovery", "ideviceinfo", "idevice_id"]:
            if not shutil.which(tool):
                messagebox.showerror("Eksik Araç", f"'{tool}' sisteminizde bulunamadı!")
                sys.exit(1)

    def select_ipsw(self):
        ipsw_path = filedialog.askopenfilename(
            title="Adios - Hedef IPSW Dosyasını Seçin",
            filetypes=[("IPSW Dosyaları", "*.ipsw"), ("Tüm Dosyalar", "*.*")]
        )
        if ipsw_path:
            self.selected_ipsw = ipsw_path
            filename = os.path.basename(ipsw_path)
            display_name = (filename[:25] + '..') if len(filename) > 25 else filename
            self.lbl_ipsw.config(text=display_name, fg=self.success_color)

    def update_ui_progress(self, status_text, percent_val):
        self.lbl_status.config(text=f"Durum: {status_text}")
        self.lbl_percent.config(text=f"%{percent_val}")
        self.progress['value'] = percent_val
        self.root.update_idletasks()

    def get_device_udid(self):
        try:
            res = subprocess.run(["idevice_id", "-l"], capture_output=True, text=True, timeout=3)
            udids = res.stdout.strip().splitlines()
            if udids:
                return udids[0].strip()
        except Exception:
            pass
        return None

    def thread_scan_device(self):
        threading.Thread(target=self.scan_device_process, daemon=True).start()

    def scan_device_process(self):
        self.update_ui_progress("Cihaz taranıyor...", 20)
        time.sleep(0.5)

        device_status = "Bulunamadı"

        # 1. Normal Mod Kontrolü
        try:
            res = subprocess.run(["ideviceinfo"], capture_output=True, text=True, timeout=3)
            if res.returncode == 0 and "ProductVersion" in res.stdout:
                device_status = "Normal Modda Bağlı"
        except Exception:
            pass

        # 2. Recovery / DFU Mod Kontrolü
        if device_status == "Bulunamadı":
            try:
                res = subprocess.run(["irecovery", "-q"], capture_output=True, text=True, timeout=3)
                output = res.stdout.lower()
                if "recovery" in output:
                    device_status = "Recovery Modda Bağlı"
                elif "dfu" in output:
                    device_status = "DFU Modda Bağlı"
                elif output.strip():
                    device_status = "Bootloader Modunda"
            except Exception:
                pass

        udid = self.get_device_udid()
        if udid and device_status == "Bulunamadı":
            device_status = "Cihaz Algılandı (UDID Var)"

        if "Bağlı" in device_status or "Algılandı" in device_status or "Modunda" in device_status:
            self.update_ui_progress(f"Başarılı: {device_status}", 100)
            messagebox.showinfo("Cihaz Durumu", f"Cihaz algılandı!\nDurum: {device_status}")
        else:
            self.update_ui_progress("Bekleniyor...", 0)
            messagebox.showwarning("Cihaz Durumu", "Hiçbir cihaz algılanamadı! Kabloyu veya bağlantıyı kontrol edin.")

    def thread_start_auto_flash(self):
        if not self.selected_ipsw:
            messagebox.showwarning("Uyarı", "Lütfen önce yüklemek istediğiniz IPSW dosyasını seçin!")
            return

        onay = messagebox.askyesno(
            "Yükleme Onayı",
            "Cihaz otomatik olarak DFU moduna alınıp yükleme başlatılacak. Onaylıyor musunuz?"
        )
        if not onay:
            return

        self.btn_select.config(state=tk.DISABLED)
        self.btn_scan.config(state=tk.DISABLED)
        self.btn_flash.config(state=tk.DISABLED, bg="#444444")

        threading.Thread(target=self.run_auto_flash_process, daemon=True).start()

    def run_auto_flash_process(self):
        try:
            self.update_ui_progress("Cihaz UDID taranıyor...", 10)
            udid = self.get_device_udid()

            device_state = "UNKNOWN"

            try:
                res = subprocess.run(["ideviceinfo"], capture_output=True, text=True, timeout=3)
                if res.returncode == 0 and "ProductVersion" in res.stdout:
                    device_state = "NORMAL"
            except Exception:
                pass

            if device_state == "UNKNOWN":
                try:
                    res = subprocess.run(["irecovery", "-q"], capture_output=True, text=True, timeout=3)
                    output = res.stdout.lower()
                    if "recovery" in output or "product" in output:
                        device_state = "RECOVERY"
                    elif "dfu" in output:
                        device_state = "DFU"
                except Exception:
                    pass

            if device_state == "NORMAL":
                self.update_ui_progress("Recovery moda alınıyor...", 20)
                try:
                    if udid:
                        subprocess.run(["ideviceenterrecovery", udid], check=True)
                    else:
                        subprocess.run(["ideviceenterrecovery"], check=True)
                    time.sleep(5)
                    device_state = "RECOVERY"
                except Exception:
                    pass

            if device_state == "RECOVERY":
                self.update_ui_progress("DFU moduna zorlanıyor...", 30)
                try:
                    subprocess.run(["irecovery", "-c", "setenv auto-boot true"], capture_output=True)
                    subprocess.run(["irecovery", "-c", "dfu"], capture_output=True)
                    time.sleep(3)
                except Exception:
                    pass

            self.update_ui_progress("Dosyalar Ayıklanıyor & Yükleniyor...", 40)
            cmd = ["idevicerestore", "-d", self.selected_ipsw]

            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )

            current_progress = 40
            for byte_line in process.stdout:
                try:
                    line = byte_line.decode('utf-8', errors='ignore').lower().strip()
                except Exception:
                    continue

                if not line:
                    continue

                if "extracting" in line:
                    current_progress = min(current_progress + 1, 65)
                    self.update_ui_progress("Extracting (Arşivden Çıkarılıyor)", current_progress)
                elif "sending" in line or "upload" in line:
                    current_progress = min(current_progress + 1, 85)
                    self.update_ui_progress("Sending to Device (Cihaza Gönderiliyor)", current_progress)
                elif "flashing" in line or "restoring" in line:
                    current_progress = min(current_progress + 1, 95)
                    self.update_ui_progress("Flashing OS (Yükleniyor)", current_progress)

            process.wait()

            if process.returncode == 0:
                self.update_ui_progress("İşlem Tamamlandı!", 100)
                messagebox.showinfo("Başarılı", "Yükleme başarıyla tamamlandı!")
            else:
                # Hata durumunda durum ve yüzdelik göstergeyi sıfırla
                self.update_ui_progress("Bekleniyor...", 0)
                messagebox.showerror("Hata", "Yükleme tamamlanamadı! (Cihaz bağlantısını kontrol edin)")

        except Exception as e:
            # Kritik hata durumunda durum ve yüzdelik göstergeyi sıfırla
            self.update_ui_progress("Bekleniyor...", 0)
            messagebox.showerror("Hata", f"Bir hata oluştu: {str(e)}")
        finally:
            self.btn_select.config(state=tk.NORMAL)
            self.btn_scan.config(state=tk.NORMAL)
            self.btn_flash.config(state=tk.NORMAL, bg="#264f78")

    def cleanup(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

if __name__ == "__main__":
    root = tk.Tk()
    app = AdiosApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.cleanup(), root.destroy()))
    root.mainloop()
