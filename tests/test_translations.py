"""Localization catalog and live-widget contracts for all 20 supported locales."""
import ast,copy,json,os,re,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
os.environ['QT_QPA_PLATFORM']='offscreen'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QEvent
from core.i18n import I18nManager,LOCALES
from core.theme import ThemeManager
from ui.main_window import MainWindow
from ui.metadata_table import MetadataTableView
from ui.prompt_card import CopyIconButton
app=QApplication.instance()or QApplication([])

def flatten(d,p=''):
    result={}
    for k,v in d.items():
        key=(p+'.'+k).strip('.')
        if isinstance(v,dict):result.update(flatten(v,key))
        else:result[key]=v
    return result

def no_duplicates(pairs):
    d={}
    for k,v in pairs:
        if k in d:raise ValueError('Duplicate JSON key: '+k)
        d[k]=v
    return d

def markers(text,source):
    percentages=set(re.findall(r'(\d+)%',source))
    return sorted(x for x in re.findall(r'%\d+|\{[^{}\n]+\}',text)if not(x.startswith('%')and x[1:]in percentages))

class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();os.environ['GALIMVMINI_DATA_DIR']=self.temp.name
        I18nManager._instance=None;ThemeManager._instance=None
    def tearDown(self):
        if hasattr(self,'window'):
            self.window.close();self.window.deleteLater();app.sendPostedEvents(None,QEvent.Type.DeferredDelete);app.processEvents()
        I18nManager._instance=None;ThemeManager._instance=None;self.temp.cleanup()
    def test_available_catalogs_are_complete_and_preserve_parameters(self):
        for project in (ROOT,ROOT.parent/'galIMV'):
            if not (project/'locales').is_dir():continue
            folder=project/'locales';self.assertEqual({p.stem for p in folder.glob('*.json')},{code for code,_ in LOCALES})
            english=flatten(json.loads((folder/'en_US.json').read_text(encoding='utf-8'),object_pairs_hook=no_duplicates))
            for code,_ in LOCALES:
                native=flatten(json.loads((folder/f'{code}.json').read_text(encoding='utf-8'),object_pairs_hook=no_duplicates))
                self.assertEqual(set(native),set(english),(project.name,code))
                for key,value in native.items():
                    self.assertIsInstance(value,str);self.assertTrue(value.strip(),(code,key))
                    self.assertNotRegex(value,r'\ufffd|__KEEP|\[\[\d+\]\]')
                    self.assertFalse(any(0xE000<=ord(ch)<=0xF8FF for ch in value),(code,key))
                    self.assertEqual(markers(value,english[key]),markers(english[key],english[key]),(code,key))
    def test_selected_json_catalog_overrides_compatibility_fallback(self):
        manager=I18nManager.get_instance();manager._current_locale='ru_RU';manager._translations={'toolbar':{'open':'Catalog override'}}
        self.assertEqual(manager.tr('toolbar.open'),'Catalog override')
    def test_every_static_ui_key_has_an_english_catalog_entry(self):
        english=flatten(json.loads((ROOT/'locales/en_US.json').read_text(encoding='utf-8')))
        for path in (ROOT/'ui').glob('*.py'):
            for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
                if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and node.func.attr=='tr'and node.args and isinstance(node.args[0],ast.Constant)and isinstance(node.args[0].value,str):
                    self.assertIn(node.args[0].value,english,(path.name,node.args[0].value))
    def test_live_language_switches_translate_widgets_without_changing_metadata(self):
        self.window=window=MainWindow();window.show();window.load_image(str(ROOT/'tests/fixtures/anime_portrait_girl.png'));app.processEvents()
        meta=window._current_meta
        meta.categories['Camera Info']={'Make':'Test Camera','Model':'Camera V1','Exposuretime':'1/125','Isospeedratings':'100'}
        original=copy.deepcopy(meta.categories);manager=I18nManager.get_instance();table=window.findChild(MetadataTableView);table.set_metadata(meta)
        for code,_ in LOCALES:
            manager.set_locale(code);app.processEvents()
            self.assertEqual(window._inspector_heading.text(),manager.tr('ui.inspector'),code)
            self.assertEqual(window._tabs.tabText(2),manager.tr('tabs.raw'),code)
            self.assertEqual(table._table.horizontalHeaderItem(0).text(),manager.tr('common.property'),code)
            self.assertEqual(window._prompt_card._prompt_badge.text(),manager.tr('prompt.word_count').replace('{count}',str(len(meta.prompt.split()))),code)
            self.assertEqual(window._copy_prompt_btn.toolTip().count('Ctrl+C'),1,code)
            self.assertNotIn('(0) (0)',window._fit_btn.toolTip(),code)
            for button in window.findChildren(CopyIconButton):
                if hasattr(button,'_title_i18n_key'):self.assertTrue(button.toolTip().startswith(manager.tr('common.copy')),code)
            labels={table._table.item(row,0).text()for row in range(table._table.rowCount())if table._table.item(row,0)}
            self.assertIn(manager.tr('metadata.filename'),labels,code)
            self.assertIn(manager.tr('metadata.camera_model'),labels,code)
            self.assertEqual(meta.categories,original,code)
            with patch('ui.main_window.QFileDialog.getOpenFileName',return_value=('',''))as dialog:
                window.browse_file();file_filter=dialog.call_args.args[3]
                self.assertIn(manager.tr('dialog.images'),file_filter,code);self.assertIn('*.png',file_filter,code)

if __name__=='__main__':unittest.main(verbosity=2)
