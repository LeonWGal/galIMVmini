"""UI behavior and shared-design contract checks; run with Python directly."""
import os,sys,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
os.environ['QT_QPA_PLATFORM']='offscreen'
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt,QEvent
from PyQt6.QtTest import QTest,QSignalSpy
from PyQt6.QtGui import QPalette
from core.design import DESIGN,contrast
from core.icons import get_tabler_icon
from core.theme import ThemeManager,LOBE_ACCENTS
from core.i18n import I18nManager
from ui.main_window import MainWindow
from ui.prompt_card import ParamBadge

app=QApplication.instance() or QApplication([])
class UnifiedInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        os.environ['GALIMVMINI_DATA_DIR']=self.temp.name
        ThemeManager._instance=None;I18nManager._instance=None
        self.window=MainWindow();self.window.show();app.processEvents()
    def tearDown(self):
        self.window.close();self.window.deleteLater();app.sendPostedEvents(None,QEvent.Type.DeferredDelete);app.processEvents()
        ThemeManager._instance=None;I18nManager._instance=None
        self.temp.cleanup()
    def load(self):
        self.window.load_image(str(ROOT/'tests/fixtures/anime_portrait_girl.png'));app.processEvents()
    def test_svg_catalog_and_optional_sibling_qml_use_identical_tokens(self):
        other=ROOT.parent/'galIMV/resources/ui/design.json'
        if other.exists():
            self.assertEqual(DESIGN,json.loads(other.read_text(encoding='utf-8')))
            js=(ROOT.parent/'galIMV/qml/DesignSystem.js').read_text(encoding='utf-8')
            self.assertEqual(DESIGN,json.loads(js.split('var design = ',1)[1].split(';\nfunction rgb',1)[0]))
        for name in DESIGN['icons']:
            self.assertFalse(get_tabler_icon(name).pixmap(18,18).isNull(),name)
    def test_gestart_lobe_palette_matches_both_theme_variants(self):
        source=json.loads((ROOT/'tests/fixtures/lobe-colors.json').read_text(encoding='utf-8'))
        imported=[a for a in DESIGN['accents'] if a.get('group')=='lobe']
        self.assertEqual(len(imported),12)
        self.assertEqual(len(DESIGN['accents']),12)
        self.assertEqual(set(self.window._palette_actions),{a['name'] for a in imported})
        self.assertTrue(all(a['name']=='Lobe '+original['label'] for original,a in zip(source,imported)))
        theme=ThemeManager.get_instance()
        for original,accent in zip(source,imported):
            self.assertEqual(accent['hex'],original['color'])
            for dark in (True,False):
                theme.set_theme(dark,accent['name'])
                self.assertEqual(theme.get_colors().accent,original['black' if dark else 'white'])
                self.assertTrue(self.window._palette_actions[accent['name']].isChecked())
        theme.set_accent('Lobe Gold')
        self.assertEqual(ThemeManager().accent_name,'Lobe Gold')

    def test_saved_accent_names_migrate_to_current_palette(self):
        settings=ThemeManager.get_instance()._settings
        for saved,expected in (("GestArt Gold","Lobe Gold"),("Lobe Cyan","Lobe Cyan"),("Monochrome Zinc","Lobe Blue")):
            settings.setValue("theme_accent",saved);settings.sync()
            theme=ThemeManager()
            self.assertEqual(theme.accent_name,expected)
            self.assertEqual(settings.value("theme_accent"),expected)

    def test_every_accent_has_a_distinct_application_icon(self):
        hashes=set();theme=ThemeManager.get_instance()
        for accent in LOBE_ACCENTS:
            theme.set_accent(accent)
            image=self.window.windowIcon().pixmap(48,48).toImage()
            self.assertFalse(image.isNull())
            hashes.add(bytes(image.constBits().asstring(image.sizeInBytes())))
        self.assertEqual(len(hashes),12)

    def test_all_accent_foregrounds_and_labels_have_contrast(self):
        theme=ThemeManager.get_instance()
        for dark in (True,False):
            for accent in LOBE_ACCENTS:
                theme.set_theme(dark,accent);c=theme.get_colors()
                self.assertGreaterEqual(contrast(c.accent,c.accent_ink),4.5,accent)
                self.assertGreaterEqual(contrast(c.accent_text,c.bg_card),4.5,accent)
                self.assertGreaterEqual(contrast(c.text_muted,c.bg_card),4.5)
                self.assertFalse(c.bg_card.startswith('rgba'))
    def test_empty_inspector_and_disabled_actions_become_available_after_open(self):
        w=self.window
        self.assertEqual(w._inspector_stack.currentWidget(),w._inspector_empty)
        self.assertFalse(w._export_btn.isEnabled());self.assertFalse(w._zoom_in_btn.isEnabled())
        self.assertTrue(w._canvas._browse_button.accessibleName())
        self.load()
        self.assertEqual(w._inspector_stack.currentWidget(),w._tabs)
        self.assertTrue(w._export_btn.isEnabled());self.assertTrue(w._copy_prompt_btn.isEnabled())
    def test_empty_canvas_open_button_has_contrast_and_keyboard_action(self):
        button=self.window._canvas._browse_button
        button.ensurePolished();palette=button.palette()
        self.assertGreaterEqual(contrast(palette.color(QPalette.ColorRole.ButtonText),palette.color(QPalette.ColorRole.Button)),4.5)
        self.window._canvas.open_requested.disconnect(self.window.browse_file)
        spy=QSignalSpy(self.window._canvas.open_requested)
        button.setFocus();QTest.keyClick(button,Qt.Key.Key_Space)
        self.assertEqual(len(spy),1)
    def test_failed_open_keeps_previous_image_and_metadata(self):
        self.load();w=self.window;previous=(w._current_path,w._current_meta)
        broken=Path(self.temp.name)/'broken.png';broken.write_bytes(b'not an image')
        w.load_image(str(broken))
        self.assertEqual(previous,(w._current_path,w._current_meta))
        self.assertFalse(w._status_timer.isActive())
    def test_new_status_is_not_cleared_by_previous_timer(self):
        self.load();w=self.window
        w.show_status('first',30);QTest.qWait(10);w.show_status('second',100)
        QTest.qWait(45);self.assertEqual(w._status_msg.text(),'second')
        QTest.qWait(80);self.assertIn(w._current_meta.file_name,w._status_msg.text())
    def test_copyable_parameter_supports_enter(self):
        badge=ParamBadge('Seed','12345',True,self.window);badge.show();badge.setFocus()
        with patch('ui.prompt_card.pyperclip.copy') as clipboard:
            QTest.keyClick(badge,Qt.Key.Key_Return);clipboard.assert_called_once_with('12345')
    def test_toolbar_controls_have_names_and_adequate_targets(self):
        for button in (self.window._open_btn,self.window._fit_btn,self.window._inspector_btn,self.window._theme_btn):
            self.assertGreaterEqual(button.height(),32)
            self.assertTrue(button.accessibleName())
            self.assertEqual(button.focusPolicy(),Qt.FocusPolicy.StrongFocus)
    def test_narrow_inspector_reflows_generation_parameters(self):
        self.load();w=self.window;w.resize(900,700);w._splitter.setSizes([530,330]);app.processEvents()
        grid=w._prompt_card._params_grid
        self.assertLess(w._prompt_card.width(),460)
        for i in range(grid.count()):self.assertEqual(grid.getItemPosition(i)[1],0)
    def test_tab_colors_update_and_inspector_width_is_remembered(self):
        self.load();w=self.window;w._tabs.setCurrentIndex(1);app.processEvents()
        w._splitter.setSizes([650,450]);before=w._splitter.sizes()
        w._inspector_btn.setChecked(False);w._inspector_btn.setChecked(True);app.processEvents()
        self.assertLess(abs(w._splitter.sizes()[1]-before[1]),12)

if __name__=='__main__':unittest.main(verbosity=2)
