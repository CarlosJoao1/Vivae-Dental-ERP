import json, os
from flask import g, request, current_app

LANGS = ["pt","en","es","fr","zh"]
TRANSL = {}

def load_translations():
    base = os.path.join(os.path.dirname(__file__), "..", "i18n")
    data = {}
    for lang in LANGS:
        p = os.path.join(base, f"{lang}.json")
        try:
            with open(p, "r", encoding="utf-8") as f:
                data[lang] = json.load(f)
        except FileNotFoundError:
            data[lang] = {}
    return data

def t(lang, key, **kw):
    text = TRANSL.get(lang, {}).get(key) or TRANSL.get("pt", {}).get(key) or key
    try:
        return text.format(**kw) if kw else text
    except Exception:
        return text

def init_i18n(app):
    global TRANSL
    TRANSL = load_translations()

    @app.before_request
    def _set_lang():
        q = request.args.get("lang")
        if q in LANGS:
            g.lang = q
        else:
            al = request.headers.get("Accept-Language", "")
            code = (al.split(",")[0].strip()[:2] if al else current_app.config.get("DEFAULT_LANG","pt"))
            g.lang = code if code in LANGS else "pt"

    @app.context_processor
    def inject_i18n():
        return {"_": lambda k, **kw: t(getattr(g, "lang", "pt"), k, **kw)}
