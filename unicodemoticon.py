#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# PEP8:OK, LINT:OK, PY3:OK, PEP257:OK


# metadata
"""UnicodEmoticons."""
__package__ = "unicodemoticons"
__version__ = '0.0.1'
__license__ = ' GPLv3 LGPLv3 '
__author__ = ' Juan Carlos '
__email__ = ' juancarlospaco@gmail.com '
__url__ = 'https://github.com/juancarlospaco/unicodemoticon'
__source__ = ('https://raw.githubusercontent.com/juancarlospaco/'
              'unicodemoticon/master/unicodemoticon.py')


# imports
import logging as log
import os
import sys
import time
from copy import copy
from ctypes import byref, cdll, create_string_buffer
from datetime import datetime
from getopt import getopt
from os import path
from subprocess import call
from tempfile import gettempdir
from urllib import request
from webbrowser import open_new_tab

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtNetwork import (QNetworkAccessManager, QNetworkProxyFactory,
                             QNetworkRequest)
from PyQt5.QtWidgets import (QApplication, QMenu, QMessageBox, QProgressDialog,
                             QSystemTrayIcon)


QSS_STYLE = """
QWidget { background-color: #302F2F; border-radius: 9px; font-family: Oxygen }
QWidget:item:selected { background-color: skyblue }
QMenu { border: 1px solid gray; color: silver; font-weight: light }
QMenu::item { padding: 1px 1em 1px 1em; margin: 0; border: 0 }
QMenu::item:selected { color: black }
QWidget:disabled { color: #404040 }"""
AUTOSTART_DESKTOP_FILE = """
[Desktop Entry]
Comment=Trayicon with Unicode Emoticons.
Exec=chrt --idle 0 /usr/bin/unicodemoticon
GenericName=Trayicon with Unicode Emoticons.
Icon=system-run
Name=UnicodEmoticon
StartupNotify=false
Terminal=false
Type=Application
X-DBUS-ServiceName=unicodemoticon
X-DBUS-StartupType=none
X-KDE-StartupNotify=false
X-KDE-SubstituteUID=false
"""


###############################################################################


class Downloader(QProgressDialog):

    """Downloader Dialog with complete informations and progress bar."""

    def __init__(self, parent=None):
        """Init class."""
        super(Downloader, self).__init__(parent)
        self.setWindowTitle(__doc__)
        if not os.path.isfile(__file__) or not __source__:
            self.close()
        if not os.access(__file__, os.W_OK):
            error_msg = ("Destination file permission denied (not Writable)! "
                         "Try again to Update but as root or administrator.")
            log.critical(error_msg)
            QMessageBox.error(self, __doc__.title(), error_msg)
            self.close()
        self._time, self._date = time.time(), datetime.now().isoformat()[:-7]
        self._url, self._dst = __source__, __file__
        log.debug("Downloading from {} to {}.".format(self._url, self._dst))
        if not self._url.lower().startswith("https:"):
            log.warning("Unsecure Download over plain text without SSL.")
        self.template = """<h3>Downloading</h3><hr><table>
        <tr><td><b>From:</b></td>      <td>{}</td>
        <tr><td><b>To:  </b></td>      <td>{}</td> <tr>
        <tr><td><b>Started:</b></td>   <td>{}</td>
        <tr><td><b>Actual:</b></td>    <td>{}</td> <tr>
        <tr><td><b>Elapsed:</b></td>   <td>{}</td>
        <tr><td><b>Remaining:</b></td> <td>{}</td> <tr>
        <tr><td><b>Received:</b></td>  <td>{} MegaBytes</td>
        <tr><td><b>Total:</b></td>     <td>{} MegaBytes</td> <tr>
        <tr><td><b>Speed:</b></td>     <td>{}</td>
        <tr><td><b>Percent:</b></td>     <td>{}%</td></table><hr>"""
        self.manager = QNetworkAccessManager(self)
        self.manager.finished.connect(self.save_downloaded_data)
        self.manager.sslErrors.connect(self.download_failed)
        self.progreso = self.manager.get(QNetworkRequest(QUrl(self._url)))
        self.progreso.downloadProgress.connect(self.update_download_progress)
        self.show()
        self.exec_()

    def save_downloaded_data(self, data):
        """Save all downloaded data to the disk and quit."""
        log.debug("Download done. Update Done.")
        with open(os.path.join(self._dst), "wb") as output_file:
            output_file.write(data.readAll())
        data.close()
        QMessageBox.information(self, __doc__.title(),
                                "<b>You got the latest version of this App!")
        del self.manager, data
        return self.close()

    def download_failed(self, download_error):
        """Handle a download error, probable SSL errors."""
        log.error(download_error)
        QMessageBox.error(self, __doc__.title(), str(download_error))

    def seconds_time_to_human_string(self, time_on_seconds=0):
        """Calculate time, with precision from seconds to days."""
        minutes, seconds = divmod(int(time_on_seconds), 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        human_time_string = ""
        if days:
            human_time_string += "%02d Days " % days
        if hours:
            human_time_string += "%02d Hours " % hours
        if minutes:
            human_time_string += "%02d Minutes " % minutes
        human_time_string += "%02d Seconds" % seconds
        return human_time_string

    def update_download_progress(self, bytesReceived, bytesTotal):
        """Calculate statistics and update the UI with them."""
        downloaded_MB = round(((bytesReceived / 1024) / 1024), 2)
        total_data_MB = round(((bytesTotal / 1024) / 1024), 2)
        downloaded_KB, total_data_KB = bytesReceived / 1024, bytesTotal / 1024
        # Calculate download speed values, with precision from Kb/s to Gb/s
        elapsed = time.clock()
        if elapsed > 0:
            speed = round((downloaded_KB / elapsed), 2)
            if speed > 1024000:  # Gigabyte speeds
                download_speed = "{} GigaByte/Second".format(speed // 1024000)
            if speed > 1024:  # MegaByte speeds
                download_speed = "{} MegaBytes/Second".format(speed // 1024)
            else:  # KiloByte speeds
                download_speed = "{} KiloBytes/Second".format(int(speed))
        if speed > 0:
            missing = abs((total_data_KB - downloaded_KB) // speed)
        percentage = int(100.0 * bytesReceived // bytesTotal)
        self.setLabelText(self.template.format(
            self._url.lower()[:99], self._dst.lower()[:99],
            self._date, datetime.now().isoformat()[:-7],
            self.seconds_time_to_human_string(time.time() - self._time),
            self.seconds_time_to_human_string(missing),
            downloaded_MB, total_data_MB, download_speed, percentage))
        self.setValue(percentage)


###############################################################################


class MainWindow(QSystemTrayIcon):

    """Main widget for UnicodEmoticons,not really a window since not needed."""

    def __init__(self):
        """Tray icon main widget."""
        super(MainWindow, self).__init__()
        self.setIcon(QIcon.fromTheme("edit-paste"))
        self.setToolTip(__doc__ + "\nPick 1 Emoticon, use CTRL+V to Paste it!")
        traymenu = QMenu("Emoticons")
        self.setIcon(QIcon("edit-paste"))
        traymenu.addAction("Emoticons").setDisabled(True)
        traymenu.setStyleSheet(QSS_STYLE.strip())
        traymenu.addSeparator()
        # NOTE: I try to do this with JSON and Dict, but the QActions Fail,
        #       pointing all actions to the lastest action assigned :(
        # menus
        menu0 = traymenu.addMenu("Sex")
        menu1 = traymenu.addMenu("Cats")
        menu2 = traymenu.addMenu("Funny")
        menu3 = traymenu.addMenu("Sad")
        menu4 = traymenu.addMenu("Music")
        menu5 = traymenu.addMenu("Arrows")
        menu6 = traymenu.addMenu("Numbers")
        menu7 = traymenu.addMenu("Letters")
        menu8 = traymenu.addMenu("Stars")
        menu9 = traymenu.addMenu("Hearts")
        menu10 = traymenu.addMenu("Hands")
        menu11 = traymenu.addMenu("Weather")
        menu12 = traymenu.addMenu("Symbols")
        menu13 = traymenu.addMenu("Tech")
        menu14 = traymenu.addMenu("Geometry")
        menu15 = traymenu.addMenu("Zodiac")
        menu16 = traymenu.addMenu("Chess")
        menu17 = traymenu.addMenu("Recycle")
        menu18 = traymenu.addMenu("Religion")
        menu19 = traymenu.addMenu("Animals face")
        menu20 = traymenu.addMenu("Animals")
        for item in (menu0, menu1, menu2, menu3, menu4, menu5, menu6, menu7,
                     menu8, menu9, menu10, menu11, menu12, menu13, menu14,
                     menu15, menu16, menu17, menu18, menu19, menu20):
            item.setStyleSheet(
                "font-size:25px;padding:0;margin:0;font-family:Oxygen")
            item.setFont(QFont('Oxygen', 25))
        # sex
        menu0.addAction("all", lambda:
                        QApplication.clipboard().setText("☿⚢⚣⚤⚥♀⚧♂"))
        menu0.addAction("♀", lambda: QApplication.clipboard().setText(" ♀ "))
        menu0.addAction("♂", lambda: QApplication.clipboard().setText(" ♂ "))
        menu0.addAction("⚢", lambda: QApplication.clipboard().setText(" ⚢ "))
        menu0.addAction("⚣", lambda: QApplication.clipboard().setText(" ⚣ "))
        menu0.addAction("⚤", lambda: QApplication.clipboard().setText(" ⚤ "))
        menu0.addAction("⚥", lambda: QApplication.clipboard().setText(" ⚥ "))
        menu0.addAction("⚧", lambda: QApplication.clipboard().setText(" ⚧ "))
        menu0.addAction("☿", lambda: QApplication.clipboard().setText(" ☿ "))
        menu0.addAction("👭", lambda: QApplication.clipboard().setText(" 👭 "))
        menu0.addAction("👬", lambda: QApplication.clipboard().setText(" 👬 "))
        menu0.addAction("👫", lambda: QApplication.clipboard().setText(" 👫 "))
        # animals
        menu1.addAction("all", lambda:
                        QApplication.clipboard().setText("😸😹😺😻😼😽😾😿🐭🐵"))
        menu1.addAction("😸", lambda: QApplication.clipboard().setText(" 😸 "))
        menu1.addAction("😹", lambda: QApplication.clipboard().setText(" 😹 "))
        menu1.addAction("😺", lambda: QApplication.clipboard().setText(" 😺 "))
        menu1.addAction("😻", lambda: QApplication.clipboard().setText(" 😻 "))
        menu1.addAction("😼", lambda: QApplication.clipboard().setText(" 😼 "))
        menu1.addAction("😽", lambda: QApplication.clipboard().setText(" 😽 "))
        menu1.addAction("😾", lambda: QApplication.clipboard().setText(" 😾 "))
        menu1.addAction("😿", lambda: QApplication.clipboard().setText(" 😿 "))
        menu1.addAction("🙀", lambda: QApplication.clipboard().setText(" 🙀 "))
        # funny
        menu2.addAction("😀", lambda: QApplication.clipboard().setText(" 😀 "))
        menu2.addAction("😁", lambda: QApplication.clipboard().setText(" 😁 "))
        menu2.addAction("😂", lambda: QApplication.clipboard().setText(" 😂 "))
        menu2.addAction("😃", lambda: QApplication.clipboard().setText(" 😃 "))
        menu2.addAction("😅", lambda: QApplication.clipboard().setText(" 😅 "))
        menu2.addAction("😆", lambda: QApplication.clipboard().setText(" 😆 "))
        menu2.addAction("😇", lambda: QApplication.clipboard().setText(" 😇 "))
        menu2.addAction("😈", lambda: QApplication.clipboard().setText(" 😈 "))
        menu2.addAction("😉", lambda: QApplication.clipboard().setText(" 😉 "))
        menu2.addAction("😊", lambda: QApplication.clipboard().setText(" 😊 "))
        menu2.addAction("😋", lambda: QApplication.clipboard().setText(" 😋 "))
        menu2.addAction("😌", lambda: QApplication.clipboard().setText(" 😌 "))
        menu2.addAction("😍", lambda: QApplication.clipboard().setText(" 😍 "))
        menu2.addAction("😎", lambda: QApplication.clipboard().setText(" 😎 "))
        menu2.addAction("😏", lambda: QApplication.clipboard().setText(" 😏 "))
        menu2.addAction("😗", lambda: QApplication.clipboard().setText(" 😗 "))
        menu2.addAction("😘", lambda: QApplication.clipboard().setText(" 😘 "))
        menu2.addAction("😙", lambda: QApplication.clipboard().setText(" 😙 "))
        menu2.addAction("😚", lambda: QApplication.clipboard().setText(" 😚 "))
        menu2.addAction("😛", lambda: QApplication.clipboard().setText(" 😛 "))
        menu2.addAction("😜", lambda: QApplication.clipboard().setText(" 😜 "))
        menu2.addAction("😝", lambda: QApplication.clipboard().setText(" 😝 "))
        menu2.addAction("☺", lambda: QApplication.clipboard().setText(" ☺ "))
        menu2.addAction("☻", lambda: QApplication.clipboard().setText(" ☻ "))
        menu2.addAction("", lambda: QApplication.clipboard().setText("  "))
        menu2.addAction("👿", lambda: QApplication.clipboard().setText(" 👿 "))
        menu2.addAction("👸", lambda: QApplication.clipboard().setText(" 👸 "))
        # sad
        menu3.addAction("😐", lambda: QApplication.clipboard().setText(" 😐 "))
        menu3.addAction("😑", lambda: QApplication.clipboard().setText(" 😑 "))
        menu3.addAction("😒", lambda: QApplication.clipboard().setText(" 😒 "))
        menu3.addAction("😓", lambda: QApplication.clipboard().setText(" 😓 "))
        menu3.addAction("😔", lambda: QApplication.clipboard().setText(" 😔 "))
        menu3.addAction("😕", lambda: QApplication.clipboard().setText(" 😕 "))
        menu3.addAction("😖", lambda: QApplication.clipboard().setText(" 😖 "))
        menu3.addAction("😞", lambda: QApplication.clipboard().setText(" 😞 "))
        menu3.addAction("😟", lambda: QApplication.clipboard().setText(" 😟 "))
        menu3.addAction("😠", lambda: QApplication.clipboard().setText(" 😠 "))
        menu3.addAction("😡", lambda: QApplication.clipboard().setText(" 😡 "))
        menu3.addAction("😢", lambda: QApplication.clipboard().setText(" 😢 "))
        menu3.addAction("😣", lambda: QApplication.clipboard().setText(" 😣 "))
        menu3.addAction("😥", lambda: QApplication.clipboard().setText(" 😥 "))
        menu3.addAction("😦", lambda: QApplication.clipboard().setText(" 😦 "))
        menu3.addAction("😧", lambda: QApplication.clipboard().setText(" 😧 "))
        menu3.addAction("😨", lambda: QApplication.clipboard().setText(" 😨 "))
        menu3.addAction("😩", lambda: QApplication.clipboard().setText(" 😩 "))
        menu3.addAction("😪", lambda: QApplication.clipboard().setText(" 😪 "))
        menu3.addAction("😫", lambda: QApplication.clipboard().setText(" 😫 "))
        menu3.addAction("😭", lambda: QApplication.clipboard().setText(" 😭 "))
        menu3.addAction("😮", lambda: QApplication.clipboard().setText(" 😮 "))
        menu3.addAction("😯", lambda: QApplication.clipboard().setText(" 😯 "))
        menu3.addAction("😰", lambda: QApplication.clipboard().setText(" 😰 "))
        menu3.addAction("😱", lambda: QApplication.clipboard().setText(" 😱 "))
        menu3.addAction("😲", lambda: QApplication.clipboard().setText(" 😲 "))
        menu3.addAction("😳", lambda: QApplication.clipboard().setText(" 😳 "))
        menu3.addAction("😴", lambda: QApplication.clipboard().setText(" 😴 "))
        menu3.addAction("😵", lambda: QApplication.clipboard().setText(" 😵 "))
        menu3.addAction("☹", lambda: QApplication.clipboard().setText(" ☹ "))
        menu3.addAction("😷", lambda: QApplication.clipboard().setText(" 😷 "))
        # music
        menu4.addAction("all", lambda:
                        QApplication.clipboard().setText(" ♩ ♫ ♬ ♪ ♪ ♭ 🎶 "))
        menu4.addAction("♬", lambda: QApplication.clipboard().setText(" ♬ "))
        menu4.addAction("♫", lambda: QApplication.clipboard().setText(" ♫ "))
        menu4.addAction("♪", lambda: QApplication.clipboard().setText(" ♪ "))
        menu4.addAction("♭", lambda: QApplication.clipboard().setText(" ♭ "))
        menu4.addAction("♩", lambda: QApplication.clipboard().setText(" ♩ "))
        menu4.addAction("🎶", lambda: QApplication.clipboard().setText(" 🎶 "))
        # arrows
        menu5.addAction("⇉", lambda: QApplication.clipboard().setText(" ⇉ "))
        menu5.addAction("⇇", lambda: QApplication.clipboard().setText(" ⇇ "))
        menu5.addAction("⇈", lambda: QApplication.clipboard().setText(" ⇈ "))
        menu5.addAction("⇊", lambda: QApplication.clipboard().setText(" ⇊ "))
        menu5.addAction("➺", lambda: QApplication.clipboard().setText(" ➺ "))
        menu5.addAction("➽", lambda: QApplication.clipboard().setText(" ➽ "))
        menu5.addAction("⇦", lambda: QApplication.clipboard().setText(" ⇦ "))
        menu5.addAction("⇨", lambda: QApplication.clipboard().setText(" ⇨ "))
        menu5.addAction("⇧", lambda: QApplication.clipboard().setText(" ⇧ "))
        menu5.addAction("⇩", lambda: QApplication.clipboard().setText(" ⇩ "))
        menu5.addAction("↔", lambda: QApplication.clipboard().setText(" ↔ "))
        menu5.addAction("↕", lambda: QApplication.clipboard().setText(" ↕ "))
        menu5.addAction("↖", lambda: QApplication.clipboard().setText(" ↖ "))
        menu5.addAction("↗", lambda: QApplication.clipboard().setText(" ↗ "))
        menu5.addAction("↘", lambda: QApplication.clipboard().setText(" ↘ "))
        menu5.addAction("↙", lambda: QApplication.clipboard().setText(" ↙ "))
        menu5.addAction("↯", lambda: QApplication.clipboard().setText(" ↯ "))
        menu5.addAction("↰", lambda: QApplication.clipboard().setText(" ↰ "))
        menu5.addAction("↱", lambda: QApplication.clipboard().setText(" ↱ "))
        menu5.addAction("↲", lambda: QApplication.clipboard().setText(" ↲ "))
        menu5.addAction("↳", lambda: QApplication.clipboard().setText(" ↳ "))
        menu5.addAction("↴", lambda: QApplication.clipboard().setText(" ↴ "))
        menu5.addAction("↵", lambda: QApplication.clipboard().setText(" ↵ "))
        menu5.addAction("↶", lambda: QApplication.clipboard().setText(" ↶ "))
        menu5.addAction("↷", lambda: QApplication.clipboard().setText(" ↷ "))
        menu5.addAction("↺", lambda: QApplication.clipboard().setText(" ↺ "))
        menu5.addAction("↻", lambda: QApplication.clipboard().setText(" ↻ "))
        menu5.addAction("➩", lambda: QApplication.clipboard().setText(" ➩ "))
        menu5.addAction("➪", lambda: QApplication.clipboard().setText(" ➪ "))
        menu5.addAction("➫", lambda: QApplication.clipboard().setText(" ➫ "))
        menu5.addAction("➬", lambda: QApplication.clipboard().setText(" ➬ "))
        menu5.addAction("➭", lambda: QApplication.clipboard().setText(" ➭ "))
        menu5.addAction("➮", lambda: QApplication.clipboard().setText(" ➮ "))
        menu5.addAction("➯", lambda: QApplication.clipboard().setText(" ➯ "))
        # numbers
        menu6.addAction("all", lambda:
                        QApplication.clipboard().setText("①②③④⑤⑥⑦⑧⑨⑩∞"))
        menu6.addAction("①", lambda: QApplication.clipboard().setText(" ① "))
        menu6.addAction("②", lambda: QApplication.clipboard().setText(" ② "))
        menu6.addAction("③", lambda: QApplication.clipboard().setText(" ③ "))
        menu6.addAction("④", lambda: QApplication.clipboard().setText(" ④ "))
        menu6.addAction("⑤", lambda: QApplication.clipboard().setText(" ⑤ "))
        menu6.addAction("⑥", lambda: QApplication.clipboard().setText(" ⑥ "))
        menu6.addAction("⑦", lambda: QApplication.clipboard().setText(" ⑦ "))
        menu6.addAction("⑧", lambda: QApplication.clipboard().setText(" ⑧ "))
        menu6.addAction("⑨", lambda: QApplication.clipboard().setText(" ⑨ "))
        menu6.addAction("⑩", lambda: QApplication.clipboard().setText(" ⑩ "))
        menu6.addAction("➊", lambda: QApplication.clipboard().setText(" ➊ "))
        menu6.addAction("➋", lambda: QApplication.clipboard().setText(" ➋ "))
        menu6.addAction("➌", lambda: QApplication.clipboard().setText(" ➌ "))
        menu6.addAction("➍", lambda: QApplication.clipboard().setText(" ➍ "))
        menu6.addAction("➎", lambda: QApplication.clipboard().setText(" ➎ "))
        menu6.addAction("➏", lambda: QApplication.clipboard().setText(" ➏ "))
        menu6.addAction("➐", lambda: QApplication.clipboard().setText(" ➐ "))
        menu6.addAction("➑", lambda: QApplication.clipboard().setText(" ➑ "))
        menu6.addAction("➒", lambda: QApplication.clipboard().setText(" ➒ "))
        menu6.addAction("➓", lambda: QApplication.clipboard().setText(" ➓ "))
        menu6.addAction("½", lambda: QApplication.clipboard().setText(" ½ "))
        menu6.addAction("¾", lambda: QApplication.clipboard().setText(" ¾ "))
        menu6.addAction("⒈", lambda: QApplication.clipboard().setText(" ⒈ "))
        menu6.addAction("⒉", lambda: QApplication.clipboard().setText(" ⒉ "))
        menu6.addAction("⒊", lambda: QApplication.clipboard().setText(" ⒊ "))
        menu6.addAction("⒋", lambda: QApplication.clipboard().setText(" ⒋ "))
        menu6.addAction("⒌", lambda: QApplication.clipboard().setText(" ⒌ "))
        menu6.addAction("⒍", lambda: QApplication.clipboard().setText(" ⒍ "))
        menu6.addAction("⒎", lambda: QApplication.clipboard().setText(" ⒎ "))
        menu6.addAction("⒏", lambda: QApplication.clipboard().setText(" ⒏ "))
        menu6.addAction("⒐", lambda: QApplication.clipboard().setText(" ⒐ "))
        menu6.addAction("⒑", lambda: QApplication.clipboard().setText(" ⒑ "))
        menu6.addAction("∞", lambda: QApplication.clipboard().setText(" ∞ "))
        # letters
        menu7.addAction("all", lambda: QApplication.clipboard().setText(
            "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ"))
        menu7.addAction("ⓐ", lambda: QApplication.clipboard().setText(" ⓐ "))
        menu7.addAction("ⓑ", lambda: QApplication.clipboard().setText(" ⓑ "))
        menu7.addAction("ⓒ", lambda: QApplication.clipboard().setText(" ⓒ "))
        menu7.addAction("ⓓ", lambda: QApplication.clipboard().setText(" ⓓ "))
        menu7.addAction("ⓔ", lambda: QApplication.clipboard().setText(" ⓔ "))
        menu7.addAction("ⓕ", lambda: QApplication.clipboard().setText(" ⓕ "))
        menu7.addAction("ⓖ", lambda: QApplication.clipboard().setText(" ⓖ "))
        menu7.addAction("ⓗ", lambda: QApplication.clipboard().setText(" ⓗ "))
        menu7.addAction("ⓘ", lambda: QApplication.clipboard().setText(" ⓘ "))
        menu7.addAction("ⓙ", lambda: QApplication.clipboard().setText(" ⓙ "))
        menu7.addAction("ⓚ", lambda: QApplication.clipboard().setText(" ⓚ "))
        menu7.addAction("ⓛ", lambda: QApplication.clipboard().setText(" ⓛ "))
        menu7.addAction("ⓜ", lambda: QApplication.clipboard().setText(" ⓜ "))
        menu7.addAction("ⓝ", lambda: QApplication.clipboard().setText(" ⓝ "))
        menu7.addAction("ⓞ", lambda: QApplication.clipboard().setText(" ⓞ "))
        menu7.addAction("ⓟ", lambda: QApplication.clipboard().setText(" ⓟ "))
        menu7.addAction("ⓠ", lambda: QApplication.clipboard().setText(" ⓠ "))
        menu7.addAction("ⓡ", lambda: QApplication.clipboard().setText(" ⓡ "))
        menu7.addAction("ⓢ", lambda: QApplication.clipboard().setText(" ⓢ "))
        menu7.addAction("ⓣ", lambda: QApplication.clipboard().setText(" ⓣ "))
        menu7.addAction("ⓤ", lambda: QApplication.clipboard().setText(" ⓤ "))
        menu7.addAction("ⓥ", lambda: QApplication.clipboard().setText(" ⓥ "))
        menu7.addAction("ⓦ", lambda: QApplication.clipboard().setText(" ⓦ "))
        menu7.addAction("ⓧ", lambda: QApplication.clipboard().setText(" ⓨ "))
        menu7.addAction("ⓩ", lambda: QApplication.clipboard().setText(" ⓩ "))
        # stars
        menu8.addAction("all", lambda: QApplication.clipboard().setText(
            "✵✡✪✬✫✻✴☆✨✶✩★✾❄❀✿🃏"))
        menu8.addAction("✵", lambda: QApplication.clipboard().setText(" ✵ "))
        menu8.addAction("✪", lambda: QApplication.clipboard().setText(" ✪ "))
        menu8.addAction("✬", lambda: QApplication.clipboard().setText(" ✬ "))
        menu8.addAction("✫", lambda: QApplication.clipboard().setText(" ✫ "))
        menu8.addAction("✻", lambda: QApplication.clipboard().setText(" ✻ "))
        menu8.addAction("✴", lambda: QApplication.clipboard().setText(" ✴ "))
        menu8.addAction("☆", lambda: QApplication.clipboard().setText(" ☆ "))
        menu8.addAction("✨", lambda: QApplication.clipboard().setText(" ✨ "))
        menu8.addAction("✶", lambda: QApplication.clipboard().setText(" ✶ "))
        menu8.addAction("✩", lambda: QApplication.clipboard().setText(" ✩ "))
        menu8.addAction("★", lambda: QApplication.clipboard().setText(" ★ "))
        menu8.addAction("✾", lambda: QApplication.clipboard().setText(" ✾ "))
        menu8.addAction("❄", lambda: QApplication.clipboard().setText(" ❄ "))
        menu8.addAction("❀", lambda: QApplication.clipboard().setText(" ❀ "))
        menu8.addAction("✿", lambda: QApplication.clipboard().setText(" ✿ "))
        menu8.addAction("🃏", lambda: QApplication.clipboard().setText(" 🃏 "))
        menu8.addAction("⚝", lambda: QApplication.clipboard().setText(" ⚝ "))
        menu8.addAction("⚹", lambda: QApplication.clipboard().setText(" ⚹ "))
        menu8.addAction("⚜", lambda: QApplication.clipboard().setText(" ⚜ "))
        menu8.addAction("🌟", lambda: QApplication.clipboard().setText(" 🌟 "))
        menu8.addAction("🌠", lambda: QApplication.clipboard().setText(" 🌠 "))
        menu8.addAction("💫", lambda: QApplication.clipboard().setText(" 💫 "))
        menu8.addAction("💥", lambda: QApplication.clipboard().setText(" 💥 "))
        # hearts
        menu9.addAction("all", lambda:
                        QApplication.clipboard().setText("♥♡❤❦"))
        menu9.addAction("♥", lambda: QApplication.clipboard().setText(" ♥ "))
        menu9.addAction("♡", lambda: QApplication.clipboard().setText(" ♡ "))
        menu9.addAction("❤", lambda: QApplication.clipboard().setText(" ❤ "))
        menu9.addAction("❦", lambda: QApplication.clipboard().setText(" ❦ "))
        menu9.addAction("☙", lambda: QApplication.clipboard().setText(" ☙ "))
        menu9.addAction("❣", lambda: QApplication.clipboard().setText(" ❣ "))
        menu9.addAction("💌", lambda: QApplication.clipboard().setText(" 💌 "))
        menu9.addAction("💘", lambda: QApplication.clipboard().setText(" 💘 "))
        menu9.addAction("💞", lambda: QApplication.clipboard().setText(" 💞 "))
        menu9.addAction("💖", lambda: QApplication.clipboard().setText(" 💖 "))
        menu9.addAction("💓", lambda: QApplication.clipboard().setText(" 💓 "))
        menu9.addAction("💗", lambda: QApplication.clipboard().setText(" 💗 "))
        menu9.addAction("💟", lambda: QApplication.clipboard().setText(" 💟 "))
        menu9.addAction("💝", lambda: QApplication.clipboard().setText(" 💝 "))
        menu9.addAction("💑", lambda: QApplication.clipboard().setText(" 💑 "))
        menu9.addAction("🌹", lambda: QApplication.clipboard().setText(" 🌹 "))
        menu9.addAction("💋", lambda: QApplication.clipboard().setText(" 💋 "))
        menu9.addAction("💔", lambda: QApplication.clipboard().setText(" 💔 "))
        menu9.addAction("💕", lambda: QApplication.clipboard().setText(" 💕 "))
        # hands
        menu10.addAction("all", lambda:
                         QApplication.clipboard().setText("✌☜☞✋✊"))
        menu10.addAction("✌", lambda: QApplication.clipboard().setText(" ✌ "))
        menu10.addAction("☜", lambda: QApplication.clipboard().setText(" ☜ "))
        menu10.addAction("☞", lambda: QApplication.clipboard().setText(" ☞ "))
        menu10.addAction("☝", lambda: QApplication.clipboard().setText(" ☝ "))
        menu10.addAction("☟", lambda: QApplication.clipboard().setText(" ☟ "))
        menu10.addAction("✋", lambda: QApplication.clipboard().setText(" ✋ "))
        menu10.addAction("✊", lambda: QApplication.clipboard().setText(" ✊ "))
        menu10.addAction("✍", lambda: QApplication.clipboard().setText(" ✍ "))
        menu10.addAction("👊", lambda: QApplication.clipboard().setText(" 👊 "))
        menu10.addAction("👌", lambda: QApplication.clipboard().setText(" 👌 "))
        menu10.addAction("👏", lambda: QApplication.clipboard().setText(" 👏 "))
        menu10.addAction("👀", lambda: QApplication.clipboard().setText(" 👀 "))
        menu10.addAction("🙌", lambda: QApplication.clipboard().setText(" 🙌 "))
        menu10.addAction("👍", lambda: QApplication.clipboard().setText(" 👍 "))
        menu10.addAction("👎", lambda: QApplication.clipboard().setText(" 👎 "))
        # weather
        menu11.addAction("all", lambda:
                         QApplication.clipboard().setText("☀☁⚡☔❄☃☽☾"))
        menu11.addAction("☀", lambda: QApplication.clipboard().setText(" ☀ "))
        menu11.addAction("☁", lambda: QApplication.clipboard().setText(" ☁ "))
        menu11.addAction("⚡", lambda: QApplication.clipboard().setText(" ⚡ "))
        menu11.addAction("☔", lambda: QApplication.clipboard().setText(" ☔ "))
        menu11.addAction("☂", lambda: QApplication.clipboard().setText(" ☂ "))

        menu11.addAction("❄", lambda: QApplication.clipboard().setText(" ❄ "))
        menu11.addAction("☃", lambda: QApplication.clipboard().setText(" ☃ "))
        menu11.addAction("☽", lambda: QApplication.clipboard().setText(" ☽ "))
        menu11.addAction("☾", lambda: QApplication.clipboard().setText(" ☾ "))
        menu11.addAction("🌞", lambda: QApplication.clipboard().setText(" 🌞 "))
        # symbols
        menu12.addAction("‼", lambda: QApplication.clipboard().setText(" ‼ "))
        menu12.addAction("⁉", lambda: QApplication.clipboard().setText(" ⁉ "))
        menu12.addAction("…", lambda: QApplication.clipboard().setText(" … "))
        menu12.addAction("❓", lambda: QApplication.clipboard().setText(" ❓ "))
        menu12.addAction("✔", lambda: QApplication.clipboard().setText(" ✔ "))
        menu12.addAction("✗", lambda: QApplication.clipboard().setText(" ✗ "))
        menu12.addAction("☑", lambda: QApplication.clipboard().setText(" ☑ "))
        menu12.addAction("☒", lambda: QApplication.clipboard().setText(" ☒ "))
        menu12.addAction("➕", lambda: QApplication.clipboard().setText(" ➕ "))
        menu12.addAction("➖", lambda: QApplication.clipboard().setText(" ➖ "))
        menu12.addAction("➗", lambda: QApplication.clipboard().setText(" ➗ "))
        menu12.addAction("❌", lambda: QApplication.clipboard().setText(" ❌ "))
        menu12.addAction("™", lambda: QApplication.clipboard().setText(" ™ "))
        menu12.addAction("®", lambda: QApplication.clipboard().setText(" ® "))
        menu12.addAction("©", lambda: QApplication.clipboard().setText(" © "))
        menu12.addAction("Ω", lambda: QApplication.clipboard().setText(" Ω "))
        menu12.addAction("℮", lambda: QApplication.clipboard().setText(" ℮ "))
        menu12.addAction("₤", lambda: QApplication.clipboard().setText(" ₤ "))
        menu12.addAction("₧", lambda: QApplication.clipboard().setText(" ₧ "))
        menu12.addAction("", lambda: QApplication.clipboard().setText("  "))
        menu12.addAction("❎", lambda: QApplication.clipboard().setText(" ❎ "))
        menu12.addAction("✅", lambda: QApplication.clipboard().setText(" ✅ "))
        menu12.addAction("➿", lambda: QApplication.clipboard().setText(" ➿ "))
        menu12.addAction("♿", lambda: QApplication.clipboard().setText(" ♿ "))
        menu12.addAction("⚓ ", lambda: QApplication.clipboard().setText(" ⚓ "))
        menu12.addAction("✈", lambda: QApplication.clipboard().setText(" ✈ "))
        menu12.addAction("⚠", lambda: QApplication.clipboard().setText(" ⚠ "))
        menu12.addAction("☕", lambda: QApplication.clipboard().setText(" ☕ "))
        menu12.addAction("♛", lambda: QApplication.clipboard().setText(" ♛ "))
        menu12.addAction("☠", lambda: QApplication.clipboard().setText(" ☠ "))
        menu12.addAction("", lambda: QApplication.clipboard().setText("  "))
        menu12.addAction("☮", lambda: QApplication.clipboard().setText(" ☮ "))
        menu12.addAction("☯", lambda: QApplication.clipboard().setText(" ☯ "))
        menu12.addAction("☘", lambda: QApplication.clipboard().setText(" ☘ "))
        menu12.addAction("⚐", lambda: QApplication.clipboard().setText(" ⚐ "))
        menu12.addAction("⚑", lambda: QApplication.clipboard().setText(" ⚑ "))
        menu12.addAction("⚒", lambda: QApplication.clipboard().setText(" ⚒ "))
        menu12.addAction("⚔", lambda: QApplication.clipboard().setText(" ⚔ "))
        menu12.addAction("⚖", lambda: QApplication.clipboard().setText(" ⚖ "))
        menu12.addAction("⚙", lambda: QApplication.clipboard().setText(" ⚙ "))
        menu12.addAction("⚛", lambda: QApplication.clipboard().setText(" ⚛ "))
        menu12.addAction("⚕", lambda: QApplication.clipboard().setText(" ⚕ "))
        menu12.addAction("", lambda: QApplication.clipboard().setText("  "))
        menu12.addAction("", lambda: QApplication.clipboard().setText("  "))
        menu12.addAction("💩", lambda: QApplication.clipboard().setText(" 💩 "))
        menu12.addAction("🍹", lambda: QApplication.clipboard().setText(" 🍹 "))
        menu12.addAction("👙", lambda: QApplication.clipboard().setText(" 👙 "))
        menu12.addAction("👡", lambda: QApplication.clipboard().setText(" 👡 "))
        menu12.addAction("👕", lambda: QApplication.clipboard().setText(" 👕 "))
        menu12.addAction("🌴", lambda: QApplication.clipboard().setText(" 🌴 "))
        menu12.addAction("💪", lambda: QApplication.clipboard().setText(" 💪 "))
        menu12.addAction("👯", lambda: QApplication.clipboard().setText(" 👯 "))
        menu12.addAction("🍴", lambda: QApplication.clipboard().setText(" 🍴 "))
        menu12.addAction("👪", lambda: QApplication.clipboard().setText(" 👪 "))
        menu12.addAction("🎁", lambda: QApplication.clipboard().setText(" 🎁 "))
        menu12.addAction("🍰", lambda: QApplication.clipboard().setText(" 🍰 "))
        menu12.addAction("🎂", lambda: QApplication.clipboard().setText(" 🎂 "))
        menu12.addAction("🎈", lambda: QApplication.clipboard().setText(" 🎈 "))
        menu12.addAction("🔥", lambda: QApplication.clipboard().setText(" 🔥 "))
        menu12.addAction("💣", lambda: QApplication.clipboard().setText(" 💣 "))
        menu12.addAction("🔫", lambda: QApplication.clipboard().setText(" 🔫 "))
        menu12.addAction("🍻", lambda: QApplication.clipboard().setText(" 🍻 "))
        menu12.addAction("🍸", lambda: QApplication.clipboard().setText(" 🍸 "))
        menu12.addAction("🍷", lambda: QApplication.clipboard().setText(" 🍷 "))
        menu12.addAction("🌍", lambda: QApplication.clipboard().setText(" 🌍 "))
        menu12.addAction("🌎", lambda: QApplication.clipboard().setText(" 🌎 "))
        menu12.addAction("🌏", lambda: QApplication.clipboard().setText(" 🌏 "))
        menu12.addAction("👽", lambda: QApplication.clipboard().setText(" 👽 "))
        menu12.addAction("💀", lambda: QApplication.clipboard().setText(" 💀 "))
        menu12.addAction("🍬", lambda: QApplication.clipboard().setText(" 🍬 "))
        menu12.addAction("👾", lambda: QApplication.clipboard().setText(" 👾 "))
        menu12.addAction("🚀", lambda: QApplication.clipboard().setText(" 🚀 "))
        menu12.addAction("📹", lambda: QApplication.clipboard().setText(" 📹 "))
        menu12.addAction("📷", lambda: QApplication.clipboard().setText(" 📷 "))
        menu12.addAction("💻", lambda: QApplication.clipboard().setText(" 💻 "))
        menu12.addAction("📱", lambda: QApplication.clipboard().setText(" 📱 "))
        menu12.addAction("📡", lambda: QApplication.clipboard().setText(" 📡 "))
        menu12.addAction("📺", lambda: QApplication.clipboard().setText(" 📺 "))
        # tech
        menu13.addAction("all", lambda:
                         QApplication.clipboard().setText("☎✉✎⌛⌚✂ℹ"))
        menu13.addAction("☎", lambda: QApplication.clipboard().setText(" ☎ "))
        menu13.addAction("✉", lambda: QApplication.clipboard().setText(" ✉ "))
        menu13.addAction("✎", lambda: QApplication.clipboard().setText(" ✎ "))
        menu13.addAction("⌛", lambda: QApplication.clipboard().setText(" ⌛ "))
        menu13.addAction("⏳", lambda: QApplication.clipboard().setText(" ⏳ "))
        menu13.addAction("⏰", lambda: QApplication.clipboard().setText(" ⏰ "))
        menu13.addAction("⌚", lambda: QApplication.clipboard().setText(" ⌚ "))
        menu13.addAction("✂", lambda: QApplication.clipboard().setText(" ✂ "))
        menu13.addAction("ℹ", lambda: QApplication.clipboard().setText(" ℹ "))
        menu13.addAction("☢", lambda: QApplication.clipboard().setText(" ☢ "))
        menu13.addAction("☣", lambda: QApplication.clipboard().setText(" ☣ "))
        menu13.addAction("☤", lambda: QApplication.clipboard().setText(" ☤ "))
        menu13.addAction("✇", lambda: QApplication.clipboard().setText(" ✇ "))
        menu13.addAction("✆", lambda: QApplication.clipboard().setText(" ✆ "))
        # geometric
        menu14.addAction("all", lambda: QApplication.clipboard().setText(
            "■●▲▼▓▒░◑◐〇◈▣▨▧▩◎◊□◕"))
        menu14.addAction("■", lambda: QApplication.clipboard().setText(" ■ "))
        menu14.addAction("●", lambda: QApplication.clipboard().setText(" ● "))
        menu14.addAction("▲", lambda: QApplication.clipboard().setText(" ▲ "))
        menu14.addAction("▼", lambda: QApplication.clipboard().setText(" ▼ "))
        menu14.addAction("▓", lambda: QApplication.clipboard().setText(" ▓ "))
        menu14.addAction("▒", lambda: QApplication.clipboard().setText(" ▒ "))
        menu14.addAction("░", lambda: QApplication.clipboard().setText(" ░ "))
        menu14.addAction("◑", lambda: QApplication.clipboard().setText(" ◑ "))
        menu14.addAction("◐", lambda: QApplication.clipboard().setText(" ◐ "))
        menu14.addAction("〇", lambda: QApplication.clipboard().setText(" 〇 "))
        menu14.addAction("◈", lambda: QApplication.clipboard().setText(" ◈ "))
        menu14.addAction("▣", lambda: QApplication.clipboard().setText(" ▣ "))
        menu14.addAction("▨", lambda: QApplication.clipboard().setText(" ▨ "))
        menu14.addAction("▧", lambda: QApplication.clipboard().setText(" ▧ "))
        menu14.addAction("▩", lambda: QApplication.clipboard().setText(" ▩ "))
        menu14.addAction("◎", lambda: QApplication.clipboard().setText(" ◎ "))
        menu14.addAction("◊", lambda: QApplication.clipboard().setText(" ◊ "))
        menu14.addAction("□", lambda: QApplication.clipboard().setText(" □ "))
        menu14.addAction("◕", lambda: QApplication.clipboard().setText(" ◕ "))
        menu14.addAction("☉", lambda: QApplication.clipboard().setText(" ☉ "))
        # zodiac
        menu15.addAction("♈", lambda: QApplication.clipboard().setText(" ♈ "))
        menu15.addAction("♉", lambda: QApplication.clipboard().setText(" ♉ "))
        menu15.addAction("♊", lambda: QApplication.clipboard().setText(" ♊ "))
        menu15.addAction("♋", lambda: QApplication.clipboard().setText(" ♋ "))
        menu15.addAction("♌", lambda: QApplication.clipboard().setText(" ♌ "))
        menu15.addAction("♍", lambda: QApplication.clipboard().setText(" ♍ "))
        menu15.addAction("♎", lambda: QApplication.clipboard().setText(" ♎ "))
        menu15.addAction("♏", lambda: QApplication.clipboard().setText(" ♏ "))
        menu15.addAction("♐", lambda: QApplication.clipboard().setText(" ♐ "))
        menu15.addAction("♑", lambda: QApplication.clipboard().setText(" ♑ "))
        menu15.addAction("♒", lambda: QApplication.clipboard().setText(" ♒ "))
        menu15.addAction("♓", lambda: QApplication.clipboard().setText(" ♓ "))
        # chess
        menu16.addAction("♔", lambda: QApplication.clipboard().setText(" ♔ "))
        menu16.addAction("♕", lambda: QApplication.clipboard().setText(" ♕ "))
        menu16.addAction("♖", lambda: QApplication.clipboard().setText(" ♖ "))
        menu16.addAction("♗", lambda: QApplication.clipboard().setText(" ♗ "))
        menu16.addAction("♘", lambda: QApplication.clipboard().setText(" ♘ "))
        menu16.addAction("♙", lambda: QApplication.clipboard().setText(" ♙ "))
        menu16.addAction("♚", lambda: QApplication.clipboard().setText(" ♚ "))
        menu16.addAction("♛", lambda: QApplication.clipboard().setText(" ♛ "))
        menu16.addAction("♜", lambda: QApplication.clipboard().setText(" ♜ "))
        menu16.addAction("♝", lambda: QApplication.clipboard().setText(" ♝ "))
        menu16.addAction("♞", lambda: QApplication.clipboard().setText(" ♞ "))
        menu16.addAction("♟", lambda: QApplication.clipboard().setText(" ♟ "))
        # recycle
        menu17.addAction("♲", lambda: QApplication.clipboard().setText(" ♲ "))
        menu17.addAction("♻", lambda: QApplication.clipboard().setText(" ♻ "))
        menu17.addAction("♳", lambda: QApplication.clipboard().setText(" ♳ "))
        menu17.addAction("♴", lambda: QApplication.clipboard().setText(" ♴ "))
        menu17.addAction("♵", lambda: QApplication.clipboard().setText(" ♵ "))
        menu17.addAction("♶", lambda: QApplication.clipboard().setText(" ♶ "))
        menu17.addAction("♷", lambda: QApplication.clipboard().setText(" ♷ "))
        menu17.addAction("♸", lambda: QApplication.clipboard().setText(" ♸ "))
        menu17.addAction("♹", lambda: QApplication.clipboard().setText(" ♹ "))
        menu17.addAction("♺", lambda: QApplication.clipboard().setText(" ♺ "))
        menu17.addAction("♼", lambda: QApplication.clipboard().setText(" ♼ "))
        menu17.addAction("♽", lambda: QApplication.clipboard().setText(" ♽ "))
        menu17.addAction("♾", lambda: QApplication.clipboard().setText(" ♾ "))
        # religion
        menu18.addAction("☦", lambda: QApplication.clipboard().setText(" ☦ "))
        menu18.addAction("☧", lambda: QApplication.clipboard().setText(" ☧ "))
        menu18.addAction("☨", lambda: QApplication.clipboard().setText(" ☨ "))
        menu18.addAction("☩", lambda: QApplication.clipboard().setText(" ☩ "))
        menu18.addAction("☪", lambda: QApplication.clipboard().setText(" ☪ "))
        menu18.addAction("☫", lambda: QApplication.clipboard().setText(" ☫ "))
        menu18.addAction("☬", lambda: QApplication.clipboard().setText(" ☬ "))
        menu18.addAction("☭", lambda: QApplication.clipboard().setText(" ☭ "))
        menu18.addAction("☯", lambda: QApplication.clipboard().setText(" ☯ "))
        menu18.addAction("࿊", lambda: QApplication.clipboard().setText(" ࿊ "))
        menu18.addAction("࿕", lambda: QApplication.clipboard().setText(" ࿕ "))
        menu18.addAction("☥", lambda: QApplication.clipboard().setText(" ☥ "))
        menu18.addAction("✟", lambda: QApplication.clipboard().setText(" ✟ "))
        menu18.addAction("✠", lambda: QApplication.clipboard().setText(" ✠ "))
        menu18.addAction("✡", lambda: QApplication.clipboard().setText(" ✡ "))
        # animals face
        menu19.addAction("🐭", lambda: QApplication.clipboard().setText(" 🐭 "))
        menu19.addAction("🐮", lambda: QApplication.clipboard().setText(" 🐮 "))
        menu19.addAction("🐵", lambda: QApplication.clipboard().setText(" 🐵 "))
        menu19.addAction("🐯", lambda: QApplication.clipboard().setText(" 🐯 "))
        menu19.addAction("🐰", lambda: QApplication.clipboard().setText(" 🐰 "))
        menu19.addAction("🐲", lambda: QApplication.clipboard().setText(" 🐲 "))
        menu19.addAction("🐳", lambda: QApplication.clipboard().setText(" 🐳 "))
        menu19.addAction("🐴", lambda: QApplication.clipboard().setText(" 🐴 "))
        menu19.addAction("🐶", lambda: QApplication.clipboard().setText(" 🐶 "))
        menu19.addAction("🐷", lambda: QApplication.clipboard().setText(" 🐷 "))
        menu19.addAction("🐸", lambda: QApplication.clipboard().setText(" 🐸 "))
        menu19.addAction("🐹", lambda: QApplication.clipboard().setText(" 🐹 "))
        menu19.addAction("🐺", lambda: QApplication.clipboard().setText(" 🐺 "))
        menu19.addAction("🐻", lambda: QApplication.clipboard().setText(" 🐻 "))
        menu19.addAction("🐼", lambda: QApplication.clipboard().setText(" 🐼 "))
        # animals
        menu20.addAction("🐞", lambda: QApplication.clipboard().setText(" 🐞 "))
        menu20.addAction("🐝", lambda: QApplication.clipboard().setText(" 🐝 "))
        menu20.addAction("🐜", lambda: QApplication.clipboard().setText(" 🐜 "))
        menu20.addAction("🐛", lambda: QApplication.clipboard().setText(" 🐛 "))
        menu20.addAction("🐀", lambda: QApplication.clipboard().setText(" 🐀 "))
        menu20.addAction("🐁", lambda: QApplication.clipboard().setText(" 🐁 "))
        menu20.addAction("🐂", lambda: QApplication.clipboard().setText(" 🐂 "))
        menu20.addAction("🐃", lambda: QApplication.clipboard().setText(" 🐃 "))
        menu20.addAction("🐄", lambda: QApplication.clipboard().setText(" 🐄 "))
        menu20.addAction("🐅", lambda: QApplication.clipboard().setText(" 🐅 "))
        menu20.addAction("🐆", lambda: QApplication.clipboard().setText(" 🐆 "))
        menu20.addAction("🐇", lambda: QApplication.clipboard().setText(" 🐇 "))
        menu20.addAction("🐈", lambda: QApplication.clipboard().setText(" 🐈 "))
        menu20.addAction("🐉", lambda: QApplication.clipboard().setText(" 🐉 "))
        menu20.addAction("🐊", lambda: QApplication.clipboard().setText(" 🐊 "))
        menu20.addAction("🐋", lambda: QApplication.clipboard().setText(" 🐋 "))
        menu20.addAction("🐌", lambda: QApplication.clipboard().setText(" 🐌 "))
        menu20.addAction("🐍", lambda: QApplication.clipboard().setText(" 🐍 "))
        menu20.addAction("🐎", lambda: QApplication.clipboard().setText(" 🐎 "))
        menu20.addAction("🐏", lambda: QApplication.clipboard().setText(" 🐏 "))
        menu20.addAction("🐐", lambda: QApplication.clipboard().setText(" 🐐 "))
        menu20.addAction("🐑", lambda: QApplication.clipboard().setText(" 🐑 "))
        menu20.addAction("🐒", lambda: QApplication.clipboard().setText(" 🐒 "))
        menu20.addAction("🐓", lambda: QApplication.clipboard().setText(" 🐓 "))
        menu20.addAction("🐔", lambda: QApplication.clipboard().setText(" 🐔 "))
        menu20.addAction("🐕", lambda: QApplication.clipboard().setText(" 🐕 "))
        menu20.addAction("🐖", lambda: QApplication.clipboard().setText(" 🐖 "))
        menu20.addAction("🐗", lambda: QApplication.clipboard().setText(" 🐗 "))
        menu20.addAction("🐘", lambda: QApplication.clipboard().setText(" 🐘 "))
        menu20.addAction("🐪", lambda: QApplication.clipboard().setText(" 🐪 "))
        menu20.addAction("🐫", lambda: QApplication.clipboard().setText(" 🐫 "))
        menu20.addAction("🐩", lambda: QApplication.clipboard().setText(" 🐩 "))
        menu20.addAction("🐧", lambda: QApplication.clipboard().setText(" 🐧 "))
        menu20.addAction("🐨", lambda: QApplication.clipboard().setText(" 🐨 "))
        menu20.addAction("🐙", lambda: QApplication.clipboard().setText(" 🐙 "))
        menu20.addAction("🐬", lambda: QApplication.clipboard().setText(" 🐬 "))
        menu20.addAction("🐚", lambda: QApplication.clipboard().setText(" 🐚 "))
        menu20.addAction("🐟", lambda: QApplication.clipboard().setText(" 🐟 "))
        menu20.addAction("🐠", lambda: QApplication.clipboard().setText(" 🐠 "))
        menu20.addAction("🐡", lambda: QApplication.clipboard().setText(" 🐡 "))
        menu20.addAction("🐢", lambda: QApplication.clipboard().setText(" 🐢 "))
        menu20.addAction("🐣", lambda: QApplication.clipboard().setText(" 🐣 "))
        menu20.addAction("🐤", lambda: QApplication.clipboard().setText(" 🐤 "))
        menu20.addAction("🐥", lambda: QApplication.clipboard().setText(" 🐥 "))
        menu20.addAction("🐦", lambda: QApplication.clipboard().setText(" 🐦 "))
        #
        traymenu.addSeparator()
        # help
        helpMenu = traymenu.addMenu("Help...")
        helpMenu.addAction("About Python 3",
                           lambda: open_new_tab('https://www.python.org'))
        helpMenu.addAction("About " + __doc__, lambda: open_new_tab(__url__))
        helpMenu.addSeparator()
        if not sys.platform.startswith("win"):
            helpMenu.addAction("View Source Code", lambda: call(
                ('xdg-open ' if sys.platform.startswith("linux") else 'open ')
                + __file__, shell=True))
        helpMenu.addSeparator()
        helpMenu.addAction("Report Bugs", lambda:
                           open_new_tab(__url__ + '/issues?state=open'))
        helpMenu.addAction("Check for updates", lambda: Downloader())
        traymenu.addSeparator()
        traymenu.addAction("Quit", lambda: self.close())
        self.setContextMenu(traymenu)
        self.show()
        self.add_autostart()

    def add_autostart(self):
        """Add to autostart of the Desktop."""
        desktop_file = path.join(path.expanduser("~"),
                                 ".config/autostart/unicodemoticon.desktop")
        if (path.isdir(path.join(path.expanduser("~"), ".config/autostart"))
                and not path.isfile(desktop_file)):
            log.info("Writing AutoStart file: " + desktop_file)
            with open(desktop_file, "w") as desktop_file_to_write:
                desktop_file_to_write.write(AUTOSTART_DESKTOP_FILE)

    def close(self):
        """Overload close method."""
        return sys.exit(0)

    def __hash__(self):
        """Return a valid answer."""
        return 42


###############################################################################


def main():
    """Main Loop."""
    APPNAME = str(__package__ or __doc__)[:99].lower().strip().replace(" ", "")
    if not sys.platform.startswith("win") and sys.stderr.isatty():
        def add_color_emit_ansi(fn):
            """Add methods we need to the class."""
            def new(*args):
                """Method overload."""
                if len(args) == 2:
                    new_args = (args[0], copy(args[1]))
                else:
                    new_args = (args[0], copy(args[1]), args[2:])
                if hasattr(args[0], 'baseFilename'):
                    return fn(*args)
                levelno = new_args[1].levelno
                if levelno >= 50:
                    color = '\x1b[31m'  # red
                elif levelno >= 40:
                    color = '\x1b[31m'  # red
                elif levelno >= 30:
                    color = '\x1b[33m'  # yellow
                elif levelno >= 20:
                    color = '\x1b[32m'  # green
                elif levelno >= 10:
                    color = '\x1b[35m'  # pink
                else:
                    color = '\x1b[0m'  # normal
                try:
                    new_args[1].msg = color + str(new_args[1].msg) + '\x1b[0m'
                except Exception as reason:
                    print(reason)  # Do not use log here.
                return fn(*new_args)
            return new
        # all non-Windows platforms support ANSI Colors so we use them
        log.StreamHandler.emit = add_color_emit_ansi(log.StreamHandler.emit)
    log.basicConfig(level=-1, format="%(levelname)s:%(asctime)s %(message)s")
    log.getLogger().addHandler(log.StreamHandler(sys.stderr))
    try:
        os.nice(19)  # smooth cpu priority
        libc = cdll.LoadLibrary('libc.so.6')  # set process name
        buff = create_string_buffer(len(APPNAME) + 1)
        buff.value = bytes(APPNAME.encode("utf-8"))
        libc.prctl(15, byref(buff), 0, 0, 0)
    except Exception as reason:
        log.warning(reason)
    app = QApplication(sys.argv)
    app.setApplicationName(APPNAME)
    app.setOrganizationName(APPNAME)
    app.setOrganizationDomain(APPNAME)
    app.setWindowIcon(QIcon.fromTheme("edit-paste"))
    win = MainWindow()
    win.show()
    try:
        opts, args = getopt(sys.argv[1:], 'hv', ('version', 'help'))
    except:
        pass
    for o, v in opts:
        if o in ('-h', '--help'):
            print(APPNAME + ''' Usage:
                  -h, --help        Show help informations and exit.
                  -v, --version     Show version information and exit.''')
            return sys.exit(0)
        elif o in ('-v', '--version'):
            log.info(__version__)
            return sys.exit(0)
    sys.exit(app.exec_())


if __name__ in '__main__':
    main()
