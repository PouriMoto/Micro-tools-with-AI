# Project Aggregator for LLM

A **Gradio‑based desktop tool** that scans your project folder, filters text/code files, and combines them into a single (or chunked) output file – ready to paste directly into Claude, ChatGPT, or any other LLM.

It automatically:
- Builds a **project summary** (total files, languages, token estimate)
- Generates a **directory tree**
- Creates a **file index** (numbered list)
- Inlines the **content of every text file** (with syntax highlighting in Markdown, or as XML with CDATA)
- Splits the output into **multiple parts** if it exceeds a token limit you set

---

## ✨ Features

- **Smart filtering** – ignores binary files, common cache/version‑control directories, and hidden files.
- **Language detection** – labels each file with its language (Python, JavaScript, etc.) and groups them in the summary.
- **Token estimation** – uses a simple heuristic (≈4 chars per token) to help you stay within LLM context windows.
- **Chunking** – automatically splits output into multiple files when the estimated token count exceeds your chosen limit.
- **Two output formats**:
  - **Markdown** – files are wrapped in code blocks with language tags.
  - **XML** – files are placed inside `<FILE>` tags with CDATA sections (safe for any content).
- **Optional SHA‑256 hash** – include a short hash per file for version tracking.
- **Customisable** – choose which file extensions to include (by category or custom list), ignore extra directories, and set per‑file size limits.
- **Graphical interface** – built with Gradio, no command‑line fiddling.

---

## 📦 Installation

1. **Clone or download** this repository.
2. **Install the required dependency**:

```bash
pip install gradio
```

> The script uses only the standard library aside from Gradio. No additional packages are needed.

---

## 🚀 Usage

Run the script from the terminal:

```bash
python app.py
```

A browser window will open with the Gradio interface.

### Interface walkthrough

- **Project folder path** – enter the absolute path to your project, or click the *Browse* button to pick a folder graphically.
- **Only include these categories** – check one or more file type groups (e.g., *Python*, *JS / TypeScript*, *Web*). Leave empty to include all supported text files.
- **Additional custom extensions** – add extra file extensions (e.g., `.vue`, `.dart`) in case your language isn’t in the predefined categories.
- **Directories to ignore** – a comma‑separated list of directory names (default excludes `.git`, `node_modules`, etc.). These are ignored wherever they appear.
- **Output format** – choose *Markdown* or *XML*.
- **Max tokens per part** – if set to a positive number, the tool will split the output into multiple files, each staying under that token count. `0` (default) means no splitting.
- **Max file size (MB)** – files larger than this will be skipped (default 2 MB).
- **Include sha256 per file** – adds a short hash in the file meta‑tag.
- **Preview project tree** – shows you the directory structure that will be included, based on the current filters.
- **Build output** – generates the output file(s). They will appear in the *Output files* box as downloadable links. The status bar shows how many files were aggregated and the total estimated token count.

After building, you can download the generated `.md` or `.xml` file(s) and paste the content into your favourite LLM chat.

---

## 🧠 How it works (under the hood)

1. **Scan** – recursively walks the project directory, ignoring:
   - Directories from the ignore list (e.g., `.git`, `__pycache__`).
   - Hidden directories (starting with a dot).
   - Binary files (detected by presence of null bytes) and files with binary extensions (`.exe`, `.png`, etc.).
   - Files larger than the specified size limit.
   - Files with extensions not in the allowed set (if a filter is active).

2. **Read** – each file is read as UTF‑8; fallback to Latin‑1 if UTF‑8 decoding fails.

3. **Build entries** – for each readable file, we store its relative path, extension, content, approximate token count, line count, and (optionally) a SHA‑256 hash.

4. **Generate output** – a header (summary + tree + index) is constructed, then each file is serialised as a block (code block in Markdown, `<FILE>` tag in XML). If chunking is enabled, blocks are accumulated until adding the next block would exceed the token limit; then a new output file is started.

5. **Save** – files are written to a temporary directory and offered for download.

---

## ⚙️ Configuration (modifying defaults)

You can tweak the constants at the top of `app.py`:

- `IGNORE_DIRS_DEFAULT` – change the default comma‑separated list of ignored directories.
- `IGNORE_EXTENSIONS` – add more binary/irrelevant extensions.
- `LANGUAGE_MAP` – map file extensions to display names.
- `EXTENSION_CATEGORIES` – regroup extensions into different categories.
- `CHARS_PER_TOKEN` – adjust the heuristic (default 4 characters per token) to better match your LLM’s tokenisation.

---

## 📄 Output format details

### Markdown

Each file is placed inside a Markdown code block with the language set to the file extension. The file is wrapped between `<FILE path="..." tokens="..." lines="..." [sha256="..."]>` and `</FILE>` comments for easier parsing (though they are just HTML‑style comments in Markdown).

### XML

The entire output is wrapped in `<PROJECT>` and `<SUMMARY>` with CDATA, followed by `<FILES>` containing one `<FILE>` element per file. File content is safely placed inside `<![CDATA[ ... ]]>` to avoid escaping issues.

---

## 🤝 Contributing

Feel free to open issues or pull requests for improvements, additional language mappings, or new features. The code is kept simple and beginner‑friendly.

---

## 📜 License

MIT – use it for any purpose, personal or commercial.

---

Happy aggregating! 🚀
