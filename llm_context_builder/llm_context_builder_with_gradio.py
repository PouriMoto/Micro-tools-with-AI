#!/usr/bin/env python3
"""
app.py — یکپارچه‌ساز فایل‌های پروژه برای ورودی LLM (با رابط Gradio)

اجرا:
    pip install gradio
    python app.py

منطق اصلی (اسکن/فیلتر/توکن/chunk) عیناً از context_builder.py گرفته شده،
فقط یک لایه‌ی نازک Gradio روش اضافه شده. کدهای دسته‌بندی/کپی فایل به
پوشه‌های جدا (که در نسخه قبلی‌ت بود) حذف شده، چون هدف نهایی «یک متن واحد
برای دادن به LLM» است، نه سازمان‌دهی فایل‌ها روی دیسک.
"""

import hashlib
import tempfile
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import gradio as gr

# ---------------------------------------------------------------------------
# تنظیمات ثابت
# ---------------------------------------------------------------------------

IGNORE_DIRS_DEFAULT = (
    ".git,.idea,.vscode,__pycache__,.pytest_cache,node_modules,venv,.venv,"
    "env,build,dist,.next,.cache,site-packages,.mypy_cache,target,.gradle,bin,obj"
)

IGNORE_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".png", ".jpg", ".jpeg", ".gif", ".ico",
    ".svg", ".webp", ".zip", ".rar", ".7z", ".tar", ".gz", ".pdf", ".mp4",
    ".mp3", ".wav", ".mov", ".woff", ".woff2", ".ttf", ".eot", ".pyc",
    ".class", ".jar", ".db", ".sqlite3", ".lock", ".bin", ".dat",
}

LANGUAGE_MAP = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript (JSX)",
    ".ts": "TypeScript", ".tsx": "TypeScript (TSX)", ".html": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".json": "JSON", ".yaml": "YAML",
    ".yml": "YAML", ".toml": "TOML", ".xml": "XML", ".md": "Markdown",
    ".sql": "SQL", ".java": "Java", ".go": "Go", ".rb": "Ruby",
    ".php": "PHP", ".c": "C", ".cpp": "C++", ".cs": "C#", ".swift": "Swift",
    ".kt": "Kotlin", ".sh": "Shell", ".txt": "Text", ".env": "Env",
    ".ini": "INI", ".cfg": "Config", ".rst": "reStructuredText",
}

EXTENSION_CATEGORIES = {
    "Python": {".py"},
    "JS / TypeScript": {".js", ".jsx", ".ts", ".tsx"},
    "وب (HTML/CSS)": {".html", ".css", ".scss"},
    "تنظیمات / داده (JSON, YAML, ...)": {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml", ".env"},
    "مستندات (Markdown/Text)": {".md", ".txt", ".rst"},
    "سایر زبان‌ها (Java, Go, C++, ...)": {".java", ".go", ".rb", ".php", ".c", ".cpp", ".cs", ".swift", ".kt", ".sql", ".sh"},
}

CHARS_PER_TOKEN = 4.0


# ---------------------------------------------------------------------------
# منطق فیلتر کردن — همه‌جا فقط اینجا تعریف می‌شود
# ---------------------------------------------------------------------------

def should_ignore_dir(dir_name: str, extra_ignore_dirs: set) -> bool:
    return dir_name in extra_ignore_dirs or dir_name.startswith(".")


def should_ignore_file(path: Path, allowed_ext) -> bool:
    if path.name.startswith("."):
        return True
    if path.suffix.lower() in IGNORE_EXTENSIONS:
        return True
    if allowed_ext and path.suffix.lower() not in allowed_ext:
        return True
    return False


def is_probably_binary(path: Path, blocksize: int = 2048) -> bool:
    try:
        with open(path, "rb") as f:
            chunk = f.read(blocksize)
        return b"\x00" in chunk
    except Exception:
        return True


# ---------------------------------------------------------------------------
# اسکن و خواندن
# ---------------------------------------------------------------------------

def scan_files(root: Path, extra_ignore_dirs: set, max_size_mb: float, allowed_ext):
    files = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        rel_parts = path.relative_to(root).parts[:-1]
        if any(should_ignore_dir(part, extra_ignore_dirs) for part in rel_parts):
            continue
        if should_ignore_file(path, allowed_ext):
            continue
        try:
            if path.stat().st_size > max_size_mb * 1024 * 1024:
                continue
        except OSError:
            continue
        if is_probably_binary(path):
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def read_file_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            return ""
    except Exception:
        return ""


def build_tree_text(root: Path, files) -> str:
    lines = []
    for f in files:
        rel = f.relative_to(root)
        depth = len(rel.parts) - 1
        indent = "    " * depth
        lines.append(f"{indent}├── {rel.name}")
    return "\n".join(lines) if lines else "(فایلی پیدا نشد)"


def estimate_tokens(text: str) -> int:
    return max(1, int(len(text) / CHARS_PER_TOKEN))


def short_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:12]


def xml_safe(text: str) -> str:
    # جلوگیری از شکستن CDATA اگر خود محتوا شامل "]]>" باشد
    return text.replace("]]>", "]]]]><![CDATA[>")


# ---------------------------------------------------------------------------
# ساخت خروجی (Markdown یا XML) + تقسیم بر اساس توکن
# ---------------------------------------------------------------------------

def build_entries(root: Path, extra_ignore_dirs: set, max_size_mb: float,
                   allowed_ext, include_hash: bool):
    files = scan_files(root, extra_ignore_dirs, max_size_mb, allowed_ext)

    with ThreadPoolExecutor(max_workers=16) as ex:
        contents = list(ex.map(read_file_safe, files))

    entries = []
    for path, content in zip(files, contents):
        if not content.strip():
            continue
        entries.append({
            "path": path.relative_to(root).as_posix(),
            "ext": path.suffix.lower(),
            "content": content,
            "tokens": estimate_tokens(content),
            "lines": content.count("\n") + 1,
            "sha": short_sha256(content) if include_hash else None,
        })
    return entries


def build_header(root: Path, entries, tree_text: str) -> str:
    total_tokens = sum(e["tokens"] for e in entries)
    languages = sorted({LANGUAGE_MAP.get(e["ext"], e["ext"] or "بدون‌پسوند") for e in entries})

    lines = [
        "# PROJECT SUMMARY", "",
        f"Project: {root.resolve().name}",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Total files: {len(entries)}",
        f"Approx Tokens: {total_tokens}",
        "",
        "Languages:",
    ]
    lines += [f"- {lang}" for lang in languages] if languages else ["- (none)"]
    lines += ["", "---", "", "# DIRECTORY TREE", "", tree_text, "",
              "---", "", "# FILE INDEX", ""]
    lines += [f"{i + 1:03d}. {e['path']}" for i, e in enumerate(entries)]
    lines += ["", "---", "", "# FILES", ""]
    return "\n".join(lines)


def build_file_block_md(e: dict) -> str:
    lang = e["ext"].lstrip(".") or "text"
    meta = f'path="{e["path"]}" tokens="{e["tokens"]}" lines="{e["lines"]}"'
    if e["sha"]:
        meta += f' sha256="{e["sha"]}"'
    return f"\n---\n\n<FILE {meta}>\n\n```{lang}\n{e['content']}\n```\n\n</FILE>\n"


def build_file_block_xml(e: dict) -> str:
    meta = f'path="{e["path"]}" tokens="{e["tokens"]}" lines="{e["lines"]}"'
    if e["sha"]:
        meta += f' sha256="{e["sha"]}"'
    return f"\n<FILE {meta}><![CDATA[\n{xml_safe(e['content'])}\n]]></FILE>\n"


def build_output_parts(root: Path, extra_ignore_dirs: set, max_size_mb: float,
                        allowed_ext, include_hash: bool, output_format: str,
                        max_tokens: int):
    entries = build_entries(root, extra_ignore_dirs, max_size_mb, allowed_ext, include_hash)
    tree_text = build_tree_text(root, [root / e["path"] for e in entries])
    header = build_header(root, entries, tree_text)

    is_xml = output_format == "XML"
    block_fn = build_file_block_xml if is_xml else build_file_block_md
    blocks = [block_fn(e) for e in entries]

    if is_xml:
        wrap_open, wrap_close = "<PROJECT>\n<SUMMARY><![CDATA[\n", "\n]]></SUMMARY>\n<FILES>"
        tail = "\n</FILES>\n</PROJECT>\n"
    else:
        wrap_open, wrap_close, tail = "", "", ""

    if not max_tokens or max_tokens <= 0:
        if is_xml:
            body = wrap_open + xml_safe(header) + wrap_close + "".join(blocks) + tail
        else:
            body = header + "".join(blocks)
        return [body], entries, tree_text

    parts = []
    current_blocks = []
    current_tokens = estimate_tokens(header)

    def flush():
        if is_xml:
            return wrap_open + xml_safe(header) + wrap_close + "".join(current_blocks) + tail
        return header + "".join(current_blocks)

    for block in blocks:
        bt = estimate_tokens(block)
        if current_tokens + bt > max_tokens and current_blocks:
            parts.append(flush())
            current_blocks = []
            current_tokens = estimate_tokens(header)
        current_blocks.append(block)
        current_tokens += bt

    if current_blocks:
        parts.append(flush())

    return parts, entries, tree_text


# ---------------------------------------------------------------------------
# توابع مربوط به رابط Gradio
# ---------------------------------------------------------------------------

def select_folder():
    """تلاش برای باز کردن دیالوگ انتخاب پوشه (فقط وقتی برنامه لوکال اجرا می‌شود)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        folder = filedialog.askdirectory()
        root.destroy()
        return folder if folder else ""
    except Exception:
        return "⚠️ دیالوگ گرافیکی در دسترس نیست — مسیر را دستی وارد کنید."


def preview_tree(project_path, extra_ignore_dirs_text, max_size_mb):
    if not project_path or not Path(project_path).exists():
        return "مسیر معتبر نیست."
    root = Path(project_path).resolve()
    extra_ignore = {d.strip() for d in extra_ignore_dirs_text.split(",") if d.strip()}
    files = scan_files(root, extra_ignore, max_size_mb, allowed_ext=None)
    return build_tree_text(root, files) or "(فایلی پیدا نشد)"


def run_build(project_path, categories, custom_ext_text, extra_ignore_dirs_text,
              output_format, max_tokens, max_size_mb, include_hash):
    if not project_path or not Path(project_path).exists():
        return "❌ مسیر پروژه معتبر نیست.", "", "", []

    root = Path(project_path).resolve()
    extra_ignore = {d.strip() for d in extra_ignore_dirs_text.split(",") if d.strip()}

    allowed_ext = set()
    for cat in categories or []:
        allowed_ext |= EXTENSION_CATEGORIES.get(cat, set())
    for e in (custom_ext_text or "").split(","):
        e = e.strip()
        if e:
            allowed_ext.add(e if e.startswith(".") else f".{e}")
    allowed_ext = allowed_ext or None  # خالی = بدون فیلتر (همه فایل‌های متنی)

    parts, entries, tree_text = build_output_parts(
        root=root,
        extra_ignore_dirs=extra_ignore,
        max_size_mb=max_size_mb,
        allowed_ext=allowed_ext,
        include_hash=include_hash,
        output_format=output_format,
        max_tokens=int(max_tokens) if max_tokens else 0,
    )

    out_dir = Path(tempfile.mkdtemp(prefix="llm_context_"))
    ext = "xml" if output_format == "XML" else "md"
    out_files = []
    for i, part in enumerate(parts, start=1):
        name = f"context.{ext}" if len(parts) == 1 else f"context_part{i}.{ext}"
        p = out_dir / name
        p.write_text(part, encoding="utf-8")
        out_files.append(str(p))

    total_tokens = sum(e["tokens"] for e in entries)
    status = (
        f"✅ {len(entries)} فایل یکپارچه شد در {len(parts)} فایل خروجی "
        f"(~{total_tokens} توکن تقریبی)."
    )
    preview = parts[0][:3000] + ("\n\n... (ادامه در فایل خروجی) ..." if len(parts[0]) > 3000 else "")
    return status, tree_text, preview, out_files


# ---------------------------------------------------------------------------
# رابط Gradio
# ---------------------------------------------------------------------------

with gr.Blocks(title="یکپارچه‌ساز پروژه برای LLM") as demo:
    gr.Markdown(
        "## 🗂️ یکپارچه‌ساز فایل‌های پروژه برای LLM\n"
        "فایل‌های متنی/کد پروژه را اسکن، فیلتر و در یک یا چند فایل خروجی "
        "(به همراه خلاصه، درخت پروژه و شماره‌گذاری) آماده می‌کند تا مستقیم "
        "به Claude / ChatGPT بدهی."
    )

    with gr.Row():
        project_path = gr.Textbox(label="مسیر پوشه پروژه", scale=4,
                                   placeholder="/home/user/my-project")
        browse_btn = gr.Button("انتخاب پوشه...", scale=1)

    with gr.Row():
        categories = gr.CheckboxGroup(
            choices=list(EXTENSION_CATEGORIES.keys()),
            label="فقط این دسته‌ها را شامل کن (خالی = همه فایل‌های متنی)",
        )
    with gr.Row():
        custom_ext = gr.Textbox(
            label="پسوندهای دلخواه اضافه (با کاما جدا کن)",
            placeholder=".vue, .dart, .r"
        )
        extra_ignore_dirs = gr.Textbox(
            label="پوشه‌های نادیده گرفته‌شده",
            value=IGNORE_DIRS_DEFAULT,
        )

    with gr.Row():
        output_format = gr.Radio(choices=["Markdown", "XML"], value="Markdown", label="فرمت خروجی")
        max_tokens = gr.Number(value=0, label="حداکثر توکن هر بخش (۰ = بدون تقسیم)", precision=0)
        max_size_mb = gr.Number(value=2.0, label="حداکثر حجم هر فایل (MB)")
        include_hash = gr.Checkbox(value=False, label="افزودن sha256 به هر فایل")

    with gr.Row():
        preview_btn = gr.Button("👁️ پیش‌نمایش درخت پروژه")
        run_btn = gr.Button("🚀 ساخت خروجی", variant="primary")

    status_out = gr.Textbox(label="وضعیت", lines=2)
    tree_out = gr.Textbox(label="🌳 درخت پروژه", lines=14)
    preview_out = gr.Textbox(label="پیش‌نمایش خروجی (بخش اول)", lines=16)
    files_out = gr.File(label="فایل‌های خروجی", file_count="multiple")

    browse_btn.click(fn=select_folder, outputs=project_path)
    preview_btn.click(
        fn=preview_tree,
        inputs=[project_path, extra_ignore_dirs, max_size_mb],
        outputs=tree_out,
    )
    run_btn.click(
        fn=run_build,
        inputs=[project_path, categories, custom_ext, extra_ignore_dirs,
                output_format, max_tokens, max_size_mb, include_hash],
        outputs=[status_out, tree_out, preview_out, files_out],
    )

if __name__ == "__main__":
    demo.launch(inbrowser=True)
