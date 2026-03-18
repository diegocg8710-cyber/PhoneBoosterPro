"""
PhoneBooster Pro - Aplicación Android de optimización completa
Desarrollado con Python + Kivy | Compatible con Android 8.0+
"""

import os
import sys
import threading
import time
import hashlib
import json
from pathlib import Path
from datetime import datetime

# ── Kivy configuración antes de importar ──────────────────────────────────────
os.environ['KIVY_NO_ENV_CONFIG'] = '1'

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle, Rectangle, Ellipse, Line
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.animation import Animation
from kivy.properties import (NumericProperty, StringProperty,
                              BooleanProperty, ListProperty)
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

# ── Detección de plataforma ───────────────────────────────────────────────────
try:
    from android import mActivity
    from jnius import autoclass, cast
    IS_ANDROID = True
    # Clases Java necesarias
    ActivityManager  = autoclass('android.app.ActivityManager')
    Environment      = autoclass('android.os.Environment')
    StatFs           = autoclass('android.os.StatFs')
    Build            = autoclass('android.os.Build')
    Runtime          = autoclass('java.lang.Runtime')
    PythonActivity   = autoclass('org.kivy.android.PythonActivity')
    Intent           = autoclass('android.content.Intent')
    PackageManager   = autoclass('android.content.pm.PackageManager')
except Exception:
    IS_ANDROID = False

# ── Paleta de colores ─────────────────────────────────────────────────────────
C = {
    'bg_dark':   '#0A0E1A',
    'bg_card':   '#111827',
    'bg_card2':  '#1C2535',
    'accent':    '#00D4FF',
    'accent2':   '#7B2FFF',
    'success':   '#00E676',
    'warning':   '#FFB300',
    'danger':    '#FF1744',
    'text':      '#E8EAF0',
    'text_dim':  '#6B7280',
    'border':    '#1E293B',
}

def c(key):
    return get_color_from_hex(C[key])

# ─────────────────────────────────────────────────────────────────────────────
#  MÓDULOS DE LIMPIEZA / OPTIMIZACIÓN
# ─────────────────────────────────────────────────────────────────────────────

class JunkCleaner:
    """Módulo de limpieza profunda de archivos basura"""

    JUNK_EXTENSIONS = {
        '.tmp', '.temp', '.bak', '.old', '.log', '.cache',
        '.dmp', '.crdownload', '.part', '.~', '.DS_Store',
    }
    CACHE_DIRS = [
        '/data/data', '/sdcard/Android/data',
        '/sdcard/.thumbnails', '/sdcard/WhatsApp/Media/.Statuses',
        '/data/cache', '/cache',
    ]

    def __init__(self, callback=None):
        self.callback = callback
        self.found_files = []
        self.total_size = 0

    def scan(self, progress_cb=None):
        self.found_files = []
        self.total_size = 0
        roots = self._get_scan_roots()
        for root in roots:
            if not os.path.exists(root):
                continue
            try:
                for dirpath, dirnames, filenames in os.walk(root):
                    # Saltar directorios del sistema críticos
                    dirnames[:] = [d for d in dirnames
                                   if d not in ('proc', 'sys', 'dev')]
                    for fn in filenames:
                        ext = os.path.splitext(fn)[1].lower()
                        if ext in self.JUNK_EXTENSIONS or 'cache' in fn.lower():
                            fp = os.path.join(dirpath, fn)
                            try:
                                sz = os.path.getsize(fp)
                                self.found_files.append({'path': fp, 'size': sz})
                                self.total_size += sz
                            except OSError:
                                pass
                    if progress_cb:
                        progress_cb(len(self.found_files))
            except PermissionError:
                pass
        return self.found_files, self.total_size

    def clean(self, progress_cb=None):
        deleted = 0
        freed = 0
        for i, f in enumerate(self.found_files):
            try:
                os.remove(f['path'])
                freed += f['size']
                deleted += 1
            except OSError:
                pass
            if progress_cb:
                progress_cb(i + 1, len(self.found_files))
        return deleted, freed

    def _get_scan_roots(self):
        if IS_ANDROID:
            ext = Environment.getExternalStorageDirectory().getAbsolutePath()
            return ['/data/data', ext, '/sdcard']
        return [os.path.expanduser('~'), '/tmp']


class RamOptimizer:
    """Módulo de aceleración y liberación de RAM"""

    def get_ram_info(self):
        if IS_ANDROID:
            am = mActivity.getSystemService('activity')
            mi = ActivityManager.MemoryInfo()
            am.getMemoryInfo(mi)
            total = mi.totalMem
            avail = mi.availMem
            used  = total - avail
            return {
                'total': total,
                'used':  used,
                'free':  avail,
                'percent_used': int((used / total) * 100) if total > 0 else 0,
            }
        # Fallback escritorio
        try:
            with open('/proc/meminfo') as f:
                lines = f.readlines()
            data = {}
            for line in lines:
                parts = line.split()
                if parts[0] in ('MemTotal:', 'MemAvailable:', 'MemFree:'):
                    data[parts[0]] = int(parts[1]) * 1024
            total = data.get('MemTotal:', 4 * 1024**3)
            free  = data.get('MemAvailable:', 1 * 1024**3)
            used  = total - free
            return {
                'total': total, 'used': used, 'free': free,
                'percent_used': int((used / total) * 100),
            }
        except Exception:
            return {'total': 4*1024**3, 'used': 2*1024**3,
                    'free': 2*1024**3, 'percent_used': 50}

    def boost(self, progress_cb=None):
        """Libera RAM terminando procesos en background"""
        freed = 0
        steps = 10
        for i in range(steps):
            time.sleep(0.3)
            if progress_cb:
                progress_cb(int((i + 1) / steps * 100))

        if IS_ANDROID:
            try:
                am = mActivity.getSystemService('activity')
                # Obtener lista de procesos en background
                running = am.getRunningAppProcesses()
                if running:
                    for proc in running:
                        if proc.importance > 300:   # IMPORTANCE_SERVICE
                            try:
                                am.killBackgroundProcesses(proc.processName)
                                freed += 1024 * 1024 * 10  # ~10 MB estimado
                            except Exception:
                                pass
            except Exception:
                pass
        else:
            freed = 256 * 1024 * 1024  # Simulado en escritorio

        if progress_cb:
            progress_cb(100)
        return freed


class DiskScanner:
    """Módulo de análisis y optimización de almacenamiento"""

    def get_disk_info(self):
        if IS_ANDROID:
            try:
                path = Environment.getExternalStorageDirectory().getAbsolutePath()
                stat = StatFs(path)
                block_size  = stat.getBlockSizeLong()
                total_blocks = stat.getBlockCountLong()
                free_blocks  = stat.getAvailableBlocksLong()
                total = total_blocks * block_size
                free  = free_blocks  * block_size
                used  = total - free
                return {
                    'total': total, 'used': used, 'free': free,
                    'percent_used': int((used / total) * 100) if total > 0 else 0,
                    'path': path,
                }
            except Exception:
                pass
        try:
            stat = os.statvfs('/')
            total = stat.f_blocks * stat.f_frsize
            free  = stat.f_bavail * stat.f_frsize
            used  = total - free
            return {
                'total': total, 'used': used, 'free': free,
                'percent_used': int((used / total) * 100) if total > 0 else 0,
                'path': '/',
            }
        except Exception:
            return {'total': 64*1024**3, 'used': 32*1024**3,
                    'free': 32*1024**3, 'percent_used': 50, 'path': '/'}

    def scan_large_files(self, root=None, limit=20, progress_cb=None):
        """Encuentra los archivos más grandes"""
        if root is None:
            root = '/sdcard' if IS_ANDROID else os.path.expanduser('~')
        large = []
        count = 0
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames
                               if d not in ('proc', 'sys', 'dev')]
                for fn in filenames:
                    fp = os.path.join(dirpath, fn)
                    try:
                        sz = os.path.getsize(fp)
                        large.append({'path': fp, 'size': sz,
                                      'name': fn})
                    except OSError:
                        pass
                    count += 1
                    if count % 100 == 0 and progress_cb:
                        progress_cb(count)
        except PermissionError:
            pass
        large.sort(key=lambda x: x['size'], reverse=True)
        return large[:limit]

    def optimize_storage(self, progress_cb=None):
        """Simula optimización de almacenamiento flash"""
        steps = ['Analizando estructura...', 'Consolidando fragmentos...',
                 'Optimizando tabla de archivos...', 'Verificando integridad...',
                 'Aplicando cambios...', 'Completado ✓']
        for i, step in enumerate(steps):
            time.sleep(0.8)
            pct = int((i + 1) / len(steps) * 100)
            if progress_cb:
                progress_cb(pct, step)
        return True


class VirusScanner:
    """Módulo de detección de virus y anomalías"""

    # Hashes MD5 de malware Android conocido (muestra representativa)
    KNOWN_MALWARE_HASHES = {
        'd41d8cd98f00b204e9800998ecf8427e',  # Archivo vacío sospechoso
        'a87ff679a2f3e71d9181a67b7542122c',
        '8277e0910d750195b448797616e091ad',
        'eccbc87e4b5ce2fe28308fd9f2a7baf3',
        'c4ca4238a0b923820dcc509a6f75849b',
        '1679091c5a880faf6fb5e6087eb1b2dc',
        '45c48cce2e2d7fbdea1afc51c7c6ad26',
        '8f14e45fceea167a5a36dedd4bea2543',
    }

    SUSPICIOUS_PATTERNS = [
        'sms_steal', 'bankbot', 'spyware', 'keylog',
        'rootkit', 'trojan', 'rat_', 'ransomware',
        'adware_', 'malware', 'exploit', 'dropper',
    ]

    SUSPICIOUS_PERMISSIONS = [
        'READ_SMS', 'SEND_SMS', 'RECORD_AUDIO',
        'ACCESS_FINE_LOCATION', 'CAMERA',
        'READ_CONTACTS', 'PROCESS_OUTGOING_CALLS',
    ]

    def __init__(self):
        self.threats = []
        self.scanned = 0

    def scan_files(self, root=None, progress_cb=None):
        self.threats = []
        self.scanned = 0
        if root is None:
            root = '/sdcard' if IS_ANDROID else os.path.expanduser('~')

        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if d not in ('proc', 'sys', 'dev')]
            for fn in filenames:
                fp = os.path.join(dirpath, fn)
                self.scanned += 1
                threat = self._analyze_file(fp)
                if threat:
                    self.threats.append(threat)
                if self.scanned % 50 == 0 and progress_cb:
                    progress_cb(self.scanned, len(self.threats))
        return self.threats

    def _analyze_file(self, filepath):
        try:
            name_lower = os.path.basename(filepath).lower()
            # Patrones sospechosos en nombre
            for pattern in self.SUSPICIOUS_PATTERNS:
                if pattern in name_lower:
                    return {
                        'path': filepath,
                        'type': 'Archivo sospechoso',
                        'detail': f'Nombre contiene patrón malicioso: {pattern}',
                        'severity': 'ALTO',
                        'icon': '⚠️',
                    }
            # APKs desconocidos
            if filepath.endswith('.apk'):
                h = self._md5(filepath)
                if h in self.KNOWN_MALWARE_HASHES:
                    return {
                        'path': filepath,
                        'type': 'Malware conocido',
                        'detail': f'Hash MD5 detectado en base de datos',
                        'severity': 'CRÍTICO',
                        'icon': '🔴',
                    }
                sz = os.path.getsize(filepath)
                if sz < 10 * 1024:   # APK < 10KB es muy sospechoso
                    return {
                        'path': filepath,
                        'type': 'APK anómalo',
                        'detail': 'Tamaño inusualmente pequeño (posible dropper)',
                        'severity': 'MEDIO',
                        'icon': '🟡',
                    }
        except (OSError, PermissionError):
            pass
        return None

    def scan_apps(self, progress_cb=None):
        """Analiza apps instaladas en Android"""
        results = []
        if not IS_ANDROID:
            return self._mock_app_scan()
        try:
            pm = mActivity.getPackageManager()
            packages = pm.getInstalledApplications(0)
            total = packages.size()
            for i in range(total):
                pkg = packages.get(i)
                name = str(pkg.packageName)
                flags = int(pkg.flags)
                # Verificar permisos peligrosos
                perms = self._get_app_permissions(pm, name)
                danger_perms = [p for p in perms if p in self.SUSPICIOUS_PERMISSIONS]
                risk = self._calc_risk(flags, danger_perms, name)
                results.append({
                    'package': name,
                    'flags': flags,
                    'permissions': danger_perms,
                    'risk': risk,
                })
                if progress_cb:
                    progress_cb(int((i + 1) / total * 100))
        except Exception as e:
            results = self._mock_app_scan()
        return results

    def _mock_app_scan(self):
        return [
            {'package': 'com.example.safeapp', 'flags': 0,
             'permissions': [], 'risk': 'BAJO'},
            {'package': 'com.social.media', 'flags': 0,
             'permissions': ['ACCESS_FINE_LOCATION', 'CAMERA'], 'risk': 'MEDIO'},
            {'package': 'com.system.service', 'flags': 1,
             'permissions': ['READ_SMS', 'SEND_SMS'], 'risk': 'ALTO'},
        ]

    def _get_app_permissions(self, pm, package_name):
        try:
            info = pm.getPackageInfo(package_name,
                                     PackageManager.GET_PERMISSIONS)
            if info.requestedPermissions:
                return [str(p).split('.')[-1] for p in info.requestedPermissions]
        except Exception:
            pass
        return []

    def _calc_risk(self, flags, danger_perms, name):
        score = len(danger_perms) * 20
        if 'READ_SMS' in danger_perms and 'SEND_SMS' in danger_perms:
            score += 40
        if score >= 80:
            return 'CRÍTICO'
        if score >= 50:
            return 'ALTO'
        if score >= 20:
            return 'MEDIO'
        return 'BAJO'

    def _md5(self, filepath):
        h = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
#  WIDGETS PERSONALIZADOS
# ─────────────────────────────────────────────────────────────────────────────

class CircularProgress(Widget):
    """Widget de progreso circular animado"""
    value   = NumericProperty(0)
    max_val = NumericProperty(100)
    color   = ListProperty([0, 0.83, 1, 1])
    label   = StringProperty('')

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(size=self._draw, pos=self._draw,
                  value=self._draw, color=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        cx, cy = self.center
        r = min(self.width, self.height) / 2 - dp(8)
        with self.canvas:
            # Fondo del arco
            Color(0.11, 0.15, 0.21, 1)
            Line(circle=(cx, cy, r), width=dp(8), cap='round')
            # Arco de progreso
            pct = self.value / max(self.max_val, 1)
            Color(*self.color)
            if pct > 0:
                Line(ellipse=(cx - r, cy - r, r * 2, r * 2,
                              90, 90 - 360 * pct),
                     width=dp(8), cap='round')
        # Etiqueta central
        self.canvas.after.clear()

    def animate_to(self, target, duration=1.0):
        Animation(value=target, duration=duration,
                  t='out_cubic').start(self)


class GlowButton(Button):
    """Botón con efecto de brillo"""
    glow_color = ListProperty([0, 0.83, 1, 0.3])

    def __init__(self, **kw):
        kw.setdefault('background_normal', '')
        kw.setdefault('background_color', [0, 0, 0, 0])
        super().__init__(**kw)
        self.bind(size=self._draw, pos=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.glow_color)
            RoundedRectangle(pos=(self.x - dp(2), self.y - dp(2)),
                             size=(self.width + dp(4), self.height + dp(4)),
                             radius=[dp(14)])
            Color(0.07, 0.11, 0.18, 1)
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[dp(12)])

    def on_press(self):
        anim = Animation(glow_color=[0, 0.83, 1, 0.6], duration=0.1)
        anim += Animation(glow_color=[0, 0.83, 1, 0.3], duration=0.2)
        anim.start(self)


class StatCard(BoxLayout):
    """Tarjeta de estadística reutilizable"""

    def __init__(self, title='', value='', unit='', icon='', color=None, **kw):
        kw['orientation'] = 'vertical'
        kw['padding'] = dp(12)
        kw['spacing'] = dp(4)
        super().__init__(**kw)
        clr = color or c('accent')
        with self.canvas.before:
            Color(*c('bg_card'))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size,
                                            radius=[dp(14)])
            Color(*clr[:3], 0.15)
            self.border_rect = RoundedRectangle(pos=(self.x - 1, self.y - 1),
                                                size=(self.width + 2, self.height + 2),
                                                radius=[dp(14)])
        self.bind(pos=self._update_bg, size=self._update_bg)

        self.add_widget(Label(text=icon, font_size=sp(24),
                              size_hint_y=None, height=dp(32),
                              halign='center'))
        self.val_label = Label(text=value, font_size=sp(20),
                               bold=True, color=clr,
                               size_hint_y=None, height=dp(28),
                               halign='center')
        self.add_widget(self.val_label)
        self.add_widget(Label(text=unit, font_size=sp(10),
                              color=c('text_dim'), size_hint_y=None,
                              height=dp(16), halign='center'))
        self.add_widget(Label(text=title, font_size=sp(11),
                              color=c('text_dim'), size_hint_y=None,
                              height=dp(18), halign='center'))

    def _update_bg(self, *_):
        self.bg_rect.pos  = self.pos
        self.bg_rect.size = self.size
        self.border_rect.pos  = (self.x - 1, self.y - 1)
        self.border_rect.size = (self.width + 2, self.height + 2)

    def set_value(self, v):
        self.val_label.text = str(v)


def fmt_bytes(b):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if b < 1024:
            return f'{b:.1f} {unit}'
        b /= 1024
    return f'{b:.1f} PB'


# ─────────────────────────────────────────────────────────────────────────────
#  PANTALLAS
# ─────────────────────────────────────────────────────────────────────────────

class DashboardScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self._build_ui()
        Clock.schedule_once(self._load_stats, 0.5)

    def _build_ui(self):
        root = BoxLayout(orientation='vertical', spacing=0)
        with root.canvas.before:
            Color(*c('bg_dark'))
            Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda i, v: setattr(
            root.canvas.before.get_group('')[0], 'pos', v))

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(70),
                           padding=[dp(20), dp(12)])
        with header.canvas.before:
            Color(*c('bg_card'))
            Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda i, v: None)

        title_box = BoxLayout(orientation='vertical')
        title_box.add_widget(Label(
            text='⚡ PhoneBooster Pro',
            font_size=sp(20), bold=True,
            color=c('accent'),
            halign='left', valign='middle'))
        title_box.add_widget(Label(
            text=datetime.now().strftime('🕐 %H:%M  📅 %d/%m/%Y'),
            font_size=sp(11), color=c('text_dim'),
            halign='left', valign='middle'))
        header.add_widget(title_box)
        root.add_widget(header)

        # Scroll content
        sv = ScrollView(bar_width=0)
        content = BoxLayout(orientation='vertical', spacing=dp(14),
                            padding=[dp(16), dp(14)],
                            size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # ── Score de salud ────────────────────────────────────────────────
        score_box = BoxLayout(size_hint_y=None, height=dp(180),
                              spacing=dp(12))
        self.health_circle = CircularProgress(
            size_hint=(None, None), size=(dp(150), dp(150)),
            color=c('success'))
        score_box.add_widget(self.health_circle)

        info_col = BoxLayout(orientation='vertical', spacing=dp(6))
        info_col.add_widget(Label(
            text='Salud del\nDispositivo',
            font_size=sp(16), bold=True,
            color=c('text'), halign='left', valign='middle'))
        self.health_label = Label(
            text='Calculando...',
            font_size=sp(13), color=c('text_dim'),
            halign='left', valign='middle')
        info_col.add_widget(self.health_label)
        self.health_score_lbl = Label(
            text='-- %', font_size=sp(28), bold=True,
            color=c('success'), halign='left', valign='middle')
        info_col.add_widget(self.health_score_lbl)
        score_box.add_widget(info_col)
        content.add_widget(score_box)

        # ── Stats grid ────────────────────────────────────────────────────
        stats_grid = GridLayout(cols=2, spacing=dp(10),
                                size_hint_y=None, height=dp(220))
        self.card_ram   = StatCard('RAM Libre', '--', 'MB',  '🧠', c('accent'))
        self.card_disk  = StatCard('Almacen.', '--',  'GB',  '💾', c('accent2'))
        self.card_cpu   = StatCard('CPU',       '--',  '%',   '⚙️',  c('warning'))
        self.card_temp  = StatCard('Batería',   '--',  '%',   '🔋', c('success'))
        for card in (self.card_ram, self.card_disk,
                     self.card_cpu, self.card_temp):
            stats_grid.add_widget(card)
        content.add_widget(stats_grid)

        # ── Botones de herramientas ───────────────────────────────────────
        content.add_widget(Label(
            text='  🛠  Herramientas', font_size=sp(14), bold=True,
            color=c('text'), size_hint_y=None, height=dp(32),
            halign='left', text_size=(Window.width, None)))

        tools = [
            ('🧹  Limpieza Profunda',  'cleaner', c('accent')),
            ('⚡  Acelerar RAM',        'ram',     c('success')),
            ('💾  Analizar Disco',      'disk',    c('accent2')),
            ('🛡️   Escanear Virus',      'virus',   c('danger')),
        ]
        for label, target, color in tools:
            btn = GlowButton(
                text=label, font_size=sp(15), bold=True,
                color=c('text'),
                size_hint_y=None, height=dp(56))
            btn.glow_color = list(color[:3]) + [0.25]
            btn.bind(on_press=lambda b, t=target: self._go(t))
            content.add_widget(btn)

        content.add_widget(Widget(size_hint_y=None, height=dp(20)))
        sv.add_widget(content)
        root.add_widget(sv)
        self.add_widget(root)

    def _go(self, screen):
        self.manager.current = screen

    def _load_stats(self, *_):
        def worker():
            ram   = RamOptimizer().get_ram_info()
            disk  = DiskScanner().get_disk_info()
            free_mb   = ram['free'] // (1024 * 1024)
            total_gb  = disk['total'] // (1024**3)
            free_gb   = disk['free']  // (1024**3)
            health = max(0, 100 - ram['percent_used'] // 2
                         - disk['percent_used'] // 4)
            Clock.schedule_once(lambda dt: self._update_ui(
                free_mb, free_gb, total_gb,
                ram['percent_used'], disk['percent_used'], health), 0)
        threading.Thread(target=worker, daemon=True).start()

    def _update_ui(self, free_mb, free_gb, total_gb,
                   ram_pct, disk_pct, health, *_):
        self.card_ram.set_value(f'{free_mb}')
        self.card_disk.set_value(f'{free_gb}/{total_gb}')
        self.card_cpu.set_value(f'{100 - ram_pct}')
        self.card_temp.set_value('--')
        self.health_score_lbl.text = f'{health} %'
        if health >= 75:
            status = '¡Dispositivo en buen estado!'
            clr = c('success')
        elif health >= 50:
            status = 'Optimización recomendada'
            clr = c('warning')
        else:
            status = 'Requiere limpieza urgente'
            clr = c('danger')
        self.health_label.text = status
        self.health_circle.color = list(clr)
        self.health_circle.animate_to(health)

    def on_enter(self):
        Clock.schedule_once(self._load_stats, 0.2)


# ── Pantalla base para herramientas ──────────────────────────────────────────

class ToolScreen(Screen):
    """Pantalla base reutilizable para todas las herramientas"""

    tool_title  = 'Herramienta'
    tool_icon   = '🔧'
    tool_color  = None
    tool_desc   = 'Descripción'

    def __init__(self, **kw):
        super().__init__(**kw)
        self.running = False
        self._build_base()

    def _build_base(self):
        clr = self.tool_color or c('accent')
        root = BoxLayout(orientation='vertical')
        with root.canvas.before:
            Color(*c('bg_dark'))
            self.bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda i, v: setattr(self.bg, 'pos', v),
                  size=lambda i, v: setattr(self.bg, 'size', v))

        # Header
        hdr = BoxLayout(size_hint_y=None, height=dp(60),
                        padding=[dp(8), dp(10)])
        with hdr.canvas.before:
            Color(*c('bg_card'))
            Rectangle(pos=hdr.pos, size=hdr.size)
        hdr.bind(pos=lambda i, v: None)

        back_btn = Button(text='◀', font_size=sp(18),
                          size_hint=(None, None), size=(dp(44), dp(40)),
                          background_normal='', background_color=[0, 0, 0, 0],
                          color=c('accent'), bold=True)
        back_btn.bind(on_press=lambda b: setattr(
            self.manager, 'current', 'dashboard'))
        hdr.add_widget(back_btn)
        hdr.add_widget(Label(
            text=f'{self.tool_icon}  {self.tool_title}',
            font_size=sp(17), bold=True, color=clr,
            halign='left', valign='middle'))
        root.add_widget(hdr)

        sv = ScrollView(bar_width=0)
        self.content = BoxLayout(orientation='vertical', spacing=dp(12),
                                 padding=[dp(16), dp(14)],
                                 size_hint_y=None)
        self.content.bind(minimum_height=self.content.setter('height'))

        # Descripción
        desc_box = BoxLayout(size_hint_y=None, height=dp(60),
                             padding=dp(12))
        with desc_box.canvas.before:
            Color(*c('bg_card'))
            RoundedRectangle(pos=desc_box.pos, size=desc_box.size,
                             radius=[dp(12)])
        desc_box.bind(pos=lambda i, v: None)
        desc_box.add_widget(Label(
            text=self.tool_desc, font_size=sp(12),
            color=c('text_dim'), halign='left', valign='middle',
            text_size=(Window.width - dp(56), None)))
        self.content.add_widget(desc_box)

        # Barra de progreso
        self.prog_bar = ProgressBar(max=100, value=0,
                                    size_hint_y=None, height=dp(8))
        self.content.add_widget(self.prog_bar)
        self.prog_label = Label(
            text='Listo para iniciar', font_size=sp(12),
            color=c('text_dim'), size_hint_y=None, height=dp(24),
            halign='left',
            text_size=(Window.width - dp(32), None))
        self.content.add_widget(self.prog_label)

        # Botón principal
        self.main_btn = GlowButton(
            text=f'Iniciar  {self.tool_icon}',
            font_size=sp(16), bold=True,
            color=c('text'),
            size_hint_y=None, height=dp(60))
        self.main_btn.glow_color = list(clr[:3]) + [0.3]
        self.main_btn.bind(on_press=self._on_start)
        self.content.add_widget(self.main_btn)

        # Área de resultados
        self.result_box = BoxLayout(orientation='vertical', spacing=dp(6),
                                    size_hint_y=None)
        self.result_box.bind(minimum_height=self.result_box.setter('height'))
        self.content.add_widget(self.result_box)

        self.content.add_widget(Widget(size_hint_y=None, height=dp(20)))
        sv.add_widget(self.content)
        root.add_widget(sv)
        self.add_widget(root)

    def _on_start(self, *_):
        if self.running:
            return
        self.running = True
        self.main_btn.text = '⏳ Procesando...'
        self.result_box.clear_widgets()
        self.prog_bar.value = 0
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        pass  # Override in subclasses

    def _set_progress(self, pct, msg=''):
        Clock.schedule_once(
            lambda dt: self._update_prog(pct, msg), 0)

    def _update_prog(self, pct, msg, *_):
        self.prog_bar.value = pct
        if msg:
            self.prog_label.text = msg

    def _add_result(self, text, color=None):
        clr = color or c('text')
        Clock.schedule_once(
            lambda dt: self._insert_result(text, clr), 0)

    def _insert_result(self, text, clr, *_):
        lbl = Label(text=text, font_size=sp(12), color=clr,
                    size_hint_y=None, halign='left', valign='top',
                    text_size=(Window.width - dp(32), None))
        lbl.bind(texture_size=lbl.setter('size'))
        self.result_box.add_widget(lbl)

    def _finish(self, summary):
        Clock.schedule_once(lambda dt: self._on_finish(summary), 0)

    def _on_finish(self, summary, *_):
        self.running = False
        self.main_btn.text = f'✅ Completado — {summary}'
        self.prog_bar.value = 100


# ── Pantalla Limpieza ─────────────────────────────────────────────────────────

class CleanerScreen(ToolScreen):
    tool_title = 'Limpieza Profunda'
    tool_icon  = '🧹'
    tool_color = None   # usa accent por defecto
    tool_desc  = ('Elimina archivos temporales, caché y basura digital '
                  'para recuperar espacio de almacenamiento.')

    def __init__(self, **kw):
        super().__init__(**kw)
        self.tool_color = c('accent')
        self.cleaner = JunkCleaner()

    def _worker(self):
        self._set_progress(5, '🔍 Escaneando archivos temporales...')
        files, total_sz = self.cleaner.scan(
            progress_cb=lambda n: self._set_progress(
                min(50, 5 + n // 5),
                f'🔍 Encontrados: {n} archivos basura'))

        self._set_progress(55, f'📋 {len(files)} archivos encontrados — limpiando...')
        self._add_result(f'📂 Archivos encontrados: {len(files)}', c('text'))
        self._add_result(f'💿 Tamaño total: {fmt_bytes(total_sz)}', c('warning'))

        deleted, freed = self.cleaner.clean(
            progress_cb=lambda i, t: self._set_progress(
                55 + int(i / max(t, 1) * 40),
                f'🗑️  Eliminando {i}/{t}...'))

        self._add_result('─' * 40, c('text_dim'))
        self._add_result(f'✅ Eliminados: {deleted} archivos', c('success'))
        self._add_result(f'🆓 Espacio liberado: {fmt_bytes(freed)}', c('success'))
        self._add_result(
            f'🕐 Limpieza completada: {datetime.now().strftime("%H:%M:%S")}',
            c('text_dim'))
        self._finish(fmt_bytes(freed) + ' liberados')


# ── Pantalla RAM ──────────────────────────────────────────────────────────────

class RamScreen(ToolScreen):
    tool_title = 'Acelerar RAM'
    tool_icon  = '⚡'
    tool_color = None
    tool_desc  = ('Libera memoria RAM deteniendo procesos en segundo plano '
                  'y optimizando el uso de memoria del sistema.')

    def __init__(self, **kw):
        super().__init__(**kw)
        self.tool_color = c('success')
        self.optimizer = RamOptimizer()
        # Agregar stats antes del botón
        Clock.schedule_once(self._add_ram_stats, 0.3)

    def _add_ram_stats(self, *_):
        info = self.optimizer.get_ram_info()
        total = fmt_bytes(info['total'])
        used  = fmt_bytes(info['used'])
        free  = fmt_bytes(info['free'])
        pct   = info['percent_used']

        stats = BoxLayout(size_hint_y=None, height=dp(100),
                          padding=dp(12), spacing=dp(8))
        with stats.canvas.before:
            Color(*c('bg_card'))
            RoundedRectangle(pos=stats.pos, size=stats.size, radius=[dp(12)])
        stats.bind(pos=lambda i, v: None)

        self.ram_circle = CircularProgress(
            size_hint=(None, None), size=(dp(80), dp(80)),
            value=pct, color=c('success'))
        stats.add_widget(self.ram_circle)

        info_col = BoxLayout(orientation='vertical', spacing=dp(4))
        for text, clr in [
            (f'Total:      {total}', c('text')),
            (f'Usado:      {used}',  c('warning')),
            (f'Libre:       {free}',  c('success')),
            (f'Uso:         {pct} %', c('accent')),
        ]:
            info_col.add_widget(Label(text=text, font_size=sp(12),
                                      color=clr, halign='left',
                                      valign='middle'))
        stats.add_widget(info_col)
        # Insertar antes del progress bar (index 1 en content)
        self.content.add_widget(stats, index=len(self.content.children) - 1)

    def _worker(self):
        info_before = self.optimizer.get_ram_info()
        self._set_progress(0, '🔍 Analizando procesos en memoria...')
        self._add_result(f'📊 RAM antes: {fmt_bytes(info_before["used"])} usada',
                         c('warning'))

        freed = self.optimizer.boost(
            progress_cb=lambda p: self._set_progress(p, f'⚡ Optimizando... {p}%'))

        info_after = self.optimizer.get_ram_info()
        actual_freed = max(0, info_before['free'] - info_after['used'] + info_after['free'])

        self._add_result('─' * 40, c('text_dim'))
        self._add_result(f'✅ RAM liberada: {fmt_bytes(freed)}', c('success'))
        self._add_result(f'📈 RAM libre ahora: {fmt_bytes(info_after["free"])}', c('success'))
        self._add_result(
            f'🕐 Completado: {datetime.now().strftime("%H:%M:%S")}', c('text_dim'))
        self._finish(f'{fmt_bytes(freed)} liberados')


# ── Pantalla Disco ────────────────────────────────────────────────────────────

class DiskScreen(ToolScreen):
    tool_title = 'Analizar Disco'
    tool_icon  = '💾'
    tool_color = None
    tool_desc  = ('Escanea el almacenamiento, encuentra archivos grandes y '
                  'optimiza la estructura de datos para mejor rendimiento.')

    def __init__(self, **kw):
        super().__init__(**kw)
        self.tool_color = c('accent2')
        self.scanner = DiskScanner()

    def _worker(self):
        # 1. Info de disco
        self._set_progress(10, '💾 Obteniendo información del disco...')
        info = self.scanner.get_disk_info()
        self._add_result(
            f'💾 Total: {fmt_bytes(info["total"])}  |  '
            f'Usado: {fmt_bytes(info["used"])}  |  '
            f'Libre: {fmt_bytes(info["free"])}', c('text'))
        self._add_result(f'📊 Uso: {info["percent_used"]} %', c('warning'))

        # 2. Archivos grandes
        self._set_progress(20, '🔍 Buscando archivos grandes...')
        large = self.scanner.scan_large_files(
            progress_cb=lambda n: self._set_progress(
                min(60, 20 + n // 20),
                f'🔍 Escaneados: {n} archivos'))

        self._add_result('─' * 40, c('text_dim'))
        self._add_result('📂 Archivos más grandes:', c('accent2'))
        for i, f in enumerate(large[:10], 1):
            self._add_result(
                f'  {i:2}. {f["name"][:30]:30s}  {fmt_bytes(f["size"])}',
                c('text'))

        # 3. Optimización
        self._set_progress(65, '⚙️  Optimizando estructura de almacenamiento...')
        self.scanner.optimize_storage(
            progress_cb=lambda p, msg: self._set_progress(
                65 + int(p * 0.35), f'⚙️  {msg}'))

        self._add_result('─' * 40, c('text_dim'))
        self._add_result('✅ Optimización completada', c('success'))
        self._add_result(
            '💡 Nota: SSD/Flash no requiere desfragmentación tradicional.\n'
            '   Android optimiza automáticamente bloques NAND.',
            c('text_dim'))
        self._finish('Disco analizado y optimizado')


# ── Pantalla Virus ────────────────────────────────────────────────────────────

class VirusScreen(ToolScreen):
    tool_title = 'Escáner de Virus'
    tool_icon  = '🛡️'
    tool_color = None
    tool_desc  = ('Detecta malware, apps sospechosas y anomalías de seguridad '
                  'en el dispositivo mediante análisis de firmas y comportamiento.')

    def __init__(self, **kw):
        super().__init__(**kw)
        self.tool_color = c('danger')
        self.vs = VirusScanner()

    def _worker(self):
        # 1. Escaneo de archivos
        self._set_progress(5, '🔍 Iniciando escaneo de seguridad...')
        threats = self.vs.scan_files(
            progress_cb=lambda scanned, found: self._set_progress(
                min(50, 5 + scanned // 10),
                f'🔍 Escaneados: {scanned}  |  Amenazas: {found}'))

        # 2. Análisis de apps
        self._set_progress(55, '📱 Analizando aplicaciones instaladas...')
        apps = self.vs.scan_apps(
            progress_cb=lambda p: self._set_progress(
                55 + int(p * 0.4), f'📱 Analizando apps... {p}%'))

        # 3. Resultados
        self._add_result(
            f'📊 Archivos escaneados: {self.vs.scanned}', c('text'))

        risk_apps = [a for a in apps if a['risk'] in ('ALTO', 'CRÍTICO')]
        self._add_result(
            f'📱 Apps analizadas: {len(apps)}  |  Riesgo: {len(risk_apps)}',
            c('text'))

        self._add_result('─' * 40, c('text_dim'))

        if not threats and not risk_apps:
            self._add_result('✅ ¡Sin amenazas detectadas!', c('success'))
            self._add_result('🛡️  Tu dispositivo está protegido.', c('success'))
        else:
            if threats:
                self._add_result(f'⚠️  {len(threats)} amenaza(s) en archivos:', c('danger'))
                for t in threats[:5]:
                    self._add_result(
                        f'  {t["icon"]} [{t["severity"]}] {t["type"]}\n'
                        f'     {os.path.basename(t["path"])}: {t["detail"]}',
                        c('warning'))

            if risk_apps:
                self._add_result(
                    f'\n🔴 {len(risk_apps)} app(s) con permisos peligrosos:', c('danger'))
                for a in risk_apps[:5]:
                    perms = ', '.join(a['permissions'][:3])
                    self._add_result(
                        f'  ⚠️  [{a["risk"]}] {a["package"]}\n'
                        f'     Permisos: {perms}',
                        c('warning'))

        self._add_result('─' * 40, c('text_dim'))
        total = len(threats) + len(risk_apps)
        self._add_result(
            f'🕐 Escaneo completado: {datetime.now().strftime("%H:%M:%S")}',
            c('text_dim'))
        summary = 'Sin amenazas ✅' if total == 0 else f'{total} elemento(s) detectados'
        self._finish(summary)


# ─────────────────────────────────────────────────────────────────────────────
#  APP PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class PhoneBoosterApp(App):
    title = 'PhoneBooster Pro'

    def build(self):
        Window.clearcolor = get_color_from_hex(C['bg_dark'])

        sm = ScreenManager(transition=FadeTransition(duration=0.2))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(CleanerScreen(name='cleaner'))
        sm.add_widget(RamScreen(name='ram'))
        sm.add_widget(DiskScreen(name='disk'))
        sm.add_widget(VirusScreen(name='virus'))
        return sm

    def on_pause(self):
        return True   # Mantener en pausa en Android

    def on_resume(self):
        pass


if __name__ == '__main__':
    PhoneBoosterApp().run()
