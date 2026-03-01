import json
import os

class Translator:
    def __init__(self, lang="fr"):
        self.lang = lang
        self.translations = {}
        self.load_translations()

    def load_translations(self):
        try:
            path = os.path.join(os.path.dirname(__file__), "../assets/i18n.json")
            with open(path, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        except Exception as e:
            print(f"Error loading translations: {e}")

    def get(self, key, default_value=None):
        return self.translations.get(self.lang, {}).get(key, default_value if default_value is not None else key)

    def set_lang(self, lang):
        self.lang = lang

    def is_rtl(self):
        return self.lang == "ar"
