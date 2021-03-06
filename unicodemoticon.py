#!/usr/bin/env python3
# -*- coding: utf-8 -*-


# metadata
"""UnicodEmoticons."""
__package__ = "unicodemoticons"
__version__ = '1.0.1'
__license__ = ' GPLv3+ LGPLv3+ '
__author__ = ' Juan Carlos '
__email__ = ' juancarlospaco@gmail.com '
__url__ = 'https://github.com/juancarlospaco/unicodemoticon'
__source__ = ('https://raw.githubusercontent.com/juancarlospaco/'
              'unicodemoticon/master/unicodemoticon.py')


# imports
import logging as log
import os
import signal
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
from html import entities

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QCursor, QFont, QIcon
from PyQt5.QtNetwork import (QNetworkAccessManager, QNetworkProxyFactory,
                             QNetworkRequest)
from PyQt5.QtWidgets import (QApplication, QMenu, QMessageBox, QProgressDialog,
                             QStyle, QSystemTrayIcon)

try:
    import resource  # windows dont have resource
except ImportError:
    resource = None


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
Exec=chrt --idle 0 unicodemoticon.py
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
HTMLS = (
    "©®µ¶€℅№∗√∞≋≡≢⊕⊖⊗⊛☆★⏧⌖☎♀♂✓✗⦿⧉⩸*¢£¥×¤ж—†•π℗Ω≬⊹✠⩐∰§´»«@θ¯⋄"
    "¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞²³𝒜𝒞𝒟𝒢𝒥𝒦𝒩𝒪𝒫𝒬𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵𝔅𝔇𝔉𝔐ℵαβγδελμψ^@⋙⋘")
UNICODEMOTICONS = {
    "sex":
        "♀♂⚢⚣⚤⚥⚧☿👭👬👫",

    "cats":
        "😸😹😺😻😼😽😾😿🙀",

    "funny":
        "😀😁😂😃😅😆😇😈😉😊😋😌😍😎😏😗😘😙😚😛😜😝☺☻👿👀",

    "sad":
        "😐😒😓😔😕😖😤😞😟😠😡😢😣😥😦😧😨😩😪😫😭😮😯😰😱😲😳😴😵☹😷",

    "music":
        "♫♪♭♩🎶🎨🎬🎤🎧🎼🎵🎹🎻🎺🎷🎸",

    "arrows":
        "⇉⇇⇈⇊➺⇦⇨⇧⇩↔↕↖↗↘↙↯↰↱↲↳↴↵↶↷↺↻➭🔄⏪⏩⏫⏬",

    "numbers":
        "①②③④⑤⑥⑦⑧⑨⑩➊➋➌➍➎➏➐➑➒➓½¾⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑∞",

    "letters":
        "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓨⓩ",

    "simbols":
        "‼⁉…❓✔✗☑☒➖➗❌™®©Ω℮₤₧❎✅➿♿☠☯☮☘💲💯🚭🚮💤㋡🔞🚼🛀🚬🚭",

    "stars":
        "✵✪✬✫✻✴☆✨✶✩★✾❄❀✿🃏⚝⚹⚜🌟🌠💫💥",

    "hearts":
        "♥♡❤❦☙❣💌💘💞💖💓💗💟💝💑🌹💋💔💕",

    "hands":
        "✌☜☞☝☟✋✊✍👊👌👏🙌👍👎",

    "weather":
        "⛅⛈☀☁⚡☔☂❄☃☽☾🌞🌊🌋🌌🌁",

    "clothes":
        "🎩👑👒👟👞👡👠👢👕👔👚👗🎽👖👘👙💼👜👝👛👓🎀🌂💄",

    "plants":
        "💐🌸🌷🍀🌹🌻🌺🍁🍃🍂🌿🌾🍄🌵🌴🌲🌳🌰🌱🌼",

    "tech":
        "☎✉✎⌛⏳⏰⌚✂ℹ☢☣☤✇✆",

    "geometry":
        "■●▲▼▓▒░◑◐〇◈▣▨▧▩◎◊□◕☉",

    "zodiac":
        "♈♉♊♋♌♍♎♏♐♑♒♓",

    "chess":
        "♔♕♖♗♘♙♚♛♜♝♞♟",

    "recycle":
        "♲♻♳♴♵♶♷♸♹♺♼♽♾",

    "religion":
        "☦☧☨☩☪☫☬☭☯࿊࿕☥✟✠✡⛤",

    "animals faces":
        "🐭🐮🐵🐯🐰🐲🐳🐴🐶🐷🐸🐹🐺🐻🐼",

    "animals":
        "🐞🐝🐜🐛🐀🐁🐂🐃🐄🐅🐆🐇🐈🐉🐊🐋🐌🐍🐎🐏🐐🐑",

    "animals 2":
        "🐒🐓🐔🐕🐖🐗🐘🐪🐫🐩🐧🐨🐙🐬🐚🐟🐠🐡🐢🐣🐤🐥🐦",

    "faces":
        "👲👳👮👷💂👶👦👧👨👩👴👵👱👼👸👹👺🙈🙉🙊💀👽👯💇",

    "sports":
        "👾🎮🎴🀄🎲🎯🏈🏀⚽⚾🎾🎱🏉🎳⛳🚵🚴🏁🏇🏆🎿🏂🏊🏄⚾🎣",

    "fruits":
        "🍎🍏🍊🍋🍒🍇🍉🍓🍑🍈🍌🍐🍍🍠🍆🍅🌽",

    "food":
        "☕🍵🍶🍼🍺🍻🍸🍹🍷🍴🍕🍔🍟🍗🍖🍝🍛🍤🍱🍣🍥🍙🍜🍲🍢🍡🍳🍞🍩🍮🍦🍨🍧🎂🍰🍪🍫🍬🍭🍯",

    "buildings":
        "🏠🏡🏫🏢🏣🏥🏪🏩🏨💒⛪🏬🏤🌇🌆🏯🏰⛺🏭🗼🗻🌄🌅🌃🗽🌉🎠🎡⛲🎢🚢🗽",

    "objects":
        "🎍🎎🎒🎓🎏🎃👻🎅🎄🎁🎋🎉🎊🎈🎌🌎💩⚙⚖⚔⚒🔐🔗🔩",

    "tech":
        "🎥📷📹📼💿📀💽💾💻📱☎📞📟📠📡📺📻🔊🔉🔇🔔🔕📢⏰🔓🔒🔑💡🔌🔍🔧🔨📲⚛",

    "transport":
        "⛵🚤🚣⚓🚀✈💺🚁🚂🚊🚆🚈🚇🚋🚎🚌🚍🚙🚕🚖🚛🚚🚓🚔🚒🚑🚐🚲🚡🚟🚜",

    "papers":
        "📧✉📩📨📫📪📬📭📮📝📃📑📊📋📆📁📂✂📌📎📏📐📗📓📔📒📚📖🔖📛🔬🔭📰",

    "multi-character":
        ("d-( ʘ‿ʘ )_m", "ಠ_ಠ", "ಢ_ಢ", "┌П┐(⌣د̲⌣)┌П┐", "(￣(工)￣)", "⊙_ʘ",
         "ಡ_ಡ", "⊙﹏⊙", "⊙▃⊙", "¯\_(ツ)_/¯", "(づ｡◕‿‿◕｡)づ", "⊂(ʘ‿ʘ)つ",
         "ლ(ಠ_ಠ ლ)", "≖_≖", "⊂(`･ω･´)つ", "Ծ_Ծ", "¯＼(⊙_ʘ)/¯", "ʕ•ᴥ•ʔ",
         "͡° ͜ʖ﻿ ͡°", "ᕦ(ò_óˇ)ᕤ", "(¬▂¬)", "█▄▄ ███ █▄▄", "(⌐■_■)",
         "✌.|•͡˘‿•͡˘|.✌", "[̲̅$̲̅(̲̅ιοο̲̅)̲̅$̲̅]", "(｡◕‿‿◕｡)", "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧",
         "٩(｡͡•‿•｡)۶", "∩(︶▽︶)∩", "☜(ﾟヮﾟ☜)", "Ƹ̵̡Ӝ̵̨̄Ʒ", "┐(;´༎ຶД༎ຶ`)┌",
         "(✿つ°ヮ°)つ  └⋃┘", "(つ°ヮ°)つ  （。Y。）", "(✿ ◕‿◕) ᓄ✂╰⋃╯",
         "(つ°ヮ°)つ  (‿|‿)",  "▄︻̷̿┻̿═━一", "(｡♥‿‿♥｡)", "╭∩╮（︶︿︶）╭∩╮",
         "<('()))}><{", "┐(´～`；)┌")
}


###############################################################################


class Downloader(QProgressDialog):

    """Downloader Dialog with complete informations and progress bar."""

    def __init__(self, parent=None):
        """Init class."""
        super(Downloader, self).__init__(parent)
        self.setWindowTitle(__doc__)
        if not os.path.isfile(__file__) or not __source__:
            return
        if not os.access(__file__, os.W_OK):
            error_msg = ("Destination file permission denied (not Writable)! "
                         "Try again to Update but as root or administrator.")
            log.critical(error_msg)
            QMessageBox.warning(self, __doc__.title(), error_msg)
            return
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
        QMessageBox.warning(self, __doc__.title(), str(download_error))

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

    def __init__(self, icon, parent=None):
        """Tray icon main widget."""
        super(MainWindow, self).__init__(icon, parent)
        log.info("Iniciando {}.".format(__doc__))
        self.setIcon(icon)
        self.setToolTip(__doc__ + "\nPick 1 Emoticon, use CTRL+V to Paste it!")
        self.traymenu = QMenu("Emoticons")
        self.traymenu.addAction("Emoticons").setDisabled(True)
        self.traymenu.setIcon(icon)
        self.traymenu.setStyleSheet(QSS_STYLE.strip())
        self.traymenu.addSeparator()
        self.activated.connect(self.click_trap)
        # menus
        list_of_labels = sorted(UNICODEMOTICONS.keys())
        menu0 = self.traymenu.addMenu(list_of_labels[0].title())
        menu1 = self.traymenu.addMenu(list_of_labels[1].title())
        menu2 = self.traymenu.addMenu(list_of_labels[2].title())
        menu3 = self.traymenu.addMenu(list_of_labels[3].title())
        menu4 = self.traymenu.addMenu(list_of_labels[4].title())
        menu5 = self.traymenu.addMenu(list_of_labels[5].title())
        menu6 = self.traymenu.addMenu(list_of_labels[6].title())
        menu7 = self.traymenu.addMenu(list_of_labels[7].title())
        menu8 = self.traymenu.addMenu(list_of_labels[8].title())
        menu9 = self.traymenu.addMenu(list_of_labels[9].title())
        menu10 = self.traymenu.addMenu(list_of_labels[10].title())
        menu11 = self.traymenu.addMenu(list_of_labels[11].title())
        menu12 = self.traymenu.addMenu(list_of_labels[12].title())
        menu13 = self.traymenu.addMenu(list_of_labels[13].title())
        menu14 = self.traymenu.addMenu(list_of_labels[14].title())
        menu15 = self.traymenu.addMenu(list_of_labels[15].title())
        menu16 = self.traymenu.addMenu(list_of_labels[16].title())
        menu17 = self.traymenu.addMenu(list_of_labels[17].title())
        menu18 = self.traymenu.addMenu(list_of_labels[18].title())
        menu19 = self.traymenu.addMenu(list_of_labels[19].title())
        menu20 = self.traymenu.addMenu(list_of_labels[20].title())
        menu21 = self.traymenu.addMenu(list_of_labels[21].title())
        menu22 = self.traymenu.addMenu(list_of_labels[22].title())
        menu23 = self.traymenu.addMenu(list_of_labels[23].title())
        menu24 = self.traymenu.addMenu(list_of_labels[24].title())
        menu25 = self.traymenu.addMenu(list_of_labels[25].title())
        menu26 = self.traymenu.addMenu(list_of_labels[26].title())
        menu27 = self.traymenu.addMenu(list_of_labels[27].title())
        menu28 = self.traymenu.addMenu(list_of_labels[28].title())
        menu29 = self.traymenu.addMenu(list_of_labels[29].title())
        menu30 = self.traymenu.addMenu(list_of_labels[30].title())
        menu31 = self.traymenu.addMenu(list_of_labels[31].title())
        menu32 = self.traymenu.addMenu(list_of_labels[32].title())
        self.traymenu.addSeparator()
        menuhtml0 = self.traymenu.addMenu("HTML5 Code")
        for index, item in enumerate((
            menu0, menu1, menu2, menu3, menu4, menu5, menu6, menu7, menu8,
            menu9, menu10, menu11, menu12, menu13, menu14, menu15, menu16,
            menu17, menu18, menu19, menu20, menu21, menu22, menu23, menu24,
            menu25, menu26, menu27, menu28, menu29, menu30, menu31, menu32,
                )):
            item.setStyleSheet(("font-size:25px;padding:0;margin:0;border:0;"
                                "font-family:Oxygen;menu-scrollable:1;"))
            item.setFont(QFont('Oxygen', 25))
            self.build_submenu(UNICODEMOTICONS[list_of_labels[index]], item)
        # html entities
        added_html_entities = []
        menuhtml0.setStyleSheet("font-size:25px;padding:0;margin:0;border:0;")
        for html_char in tuple(sorted(entities.html5.items())):
            if html_char[1] in HTMLS:
                added_html_entities.append(
                    html_char[0].lower().replace(";", ""))
                if not html_char[0].lower() in added_html_entities:
                    action = menuhtml0.addAction(html_char[1])
                    action.triggered.connect(
                        lambda _, ch=html_char[0]:
                            QApplication.clipboard().setText(
                                "&{html_entity}".format(html_entity=ch)))
        self.traymenu.addSeparator()
        # help
        helpMenu = self.traymenu.addMenu("Help...")
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
        self.traymenu.addSeparator()
        self.traymenu.addAction("Quit", lambda: self.close())
        self.setContextMenu(self.traymenu)
        self.show()
        self.add_autostart()

    def build_submenu(self, char_list, submenu):
        """Take a list of characters and a submenu and build actions on it."""
        for _char in sorted(char_list):
            action = submenu.addAction(_char.strip())
            action.triggered.connect(
                lambda _, char=_char: QApplication.clipboard().setText(char))

    def click_trap(self, value):
        """Trap the mouse tight click."""
        if value == self.Trigger:  # left click
            self.traymenu.exec_(QCursor.pos())

    def add_autostart(self):
        """Add to autostart of the Desktop."""
        desktop_file = path.join(path.expanduser("~"),
                                 ".config/autostart/unicodemoticon.desktop")
        if (path.isdir(path.join(path.expanduser("~"), ".config/autostart"))
                and not path.isfile(desktop_file)):
            log.info("Writing AutoStart file: " + desktop_file)
            with open(desktop_file, "w", encoding="utf-8") as desktop_file:
                desktop_file.write(AUTOSTART_DESKTOP_FILE)

    def close(self):
        """Overload close method."""
        return sys.exit(0)


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
                    color = '\x1b[31;5;7m\n '  # blinking red with black
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
                    new_args[1].msg = color + str(new_args[1].msg) + ' \x1b[0m'
                except Exception as reason:
                    print(reason)  # Do not use log here.
                return fn(*new_args)
            return new
        # all non-Windows platforms support ANSI Colors so we use them
        log.StreamHandler.emit = add_color_emit_ansi(log.StreamHandler.emit)
    log.basicConfig(level=-1, format="%(levelname)s:%(asctime)s %(message)s")
    log.getLogger().addHandler(log.StreamHandler(sys.stderr))
    log.info(__doc__)
    try:
        os.nice(19)  # smooth cpu priority
        libc = cdll.LoadLibrary('libc.so.6')  # set process name
        buff = create_string_buffer(len(APPNAME) + 1)
        buff.value = bytes(APPNAME.encode("utf-8"))
        libc.prctl(15, byref(buff), 0, 0, 0)
    except Exception as reason:
        log.warning(reason)
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # CTRL+C work to quit app
    app = QApplication(sys.argv)
    app.setApplicationName(APPNAME)
    app.setOrganizationName(APPNAME)
    app.setOrganizationDomain(APPNAME)
    icon = QIcon(app.style().standardPixmap(QStyle.SP_FileIcon))
    app.setWindowIcon(icon)
    win = MainWindow(icon)
    win.show()
    log.info('Total Maximum RAM Memory used: ~{} MegaBytes.'.format(int(
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss *
        resource.getpagesize() / 1024 / 1024 if resource else 0)))
    sys.exit(app.exec_())


if __name__ in '__main__':
    main()
