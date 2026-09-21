#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
project_packer.py — 项目打包 / 解包工具

用法:
  交互模式            python project_packer.py
  命令行打包          python project_packer.py pack ["项目描述"]
  命令行解包          python project_packer.py unpack <txt文件路径>
  保留注释打包        python project_packer.py pack --keep-comments ["项目描述"]
  包含二进制文件内容  python project_packer.py pack --include-binary ["项目描述"]
  跳过指定后缀        python project_packer.py pack --skip-ext .log .tmp .bak ["项目描述"]
"""

import os
import sys
import re
import base64
from pathlib import Path

# ========================== 可修改配置 ==========================

OUTPUT_FILENAME = "prj.txt"

EXCLUDE_DIRS = {
    ".git", ".svn", "node_modules", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".next", ".cache",
    "venv", ".venv", "target", "out", "coverage", ".tox",
}

EXCLUDE_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}

# ========================== 内部常量 ==========================

TREE_MARKER  = "===== 目录结构 ====="
CODE_MARKER  = "===== 项目代码 ====="
FILE_SEP_L   = "---=== "
FILE_SEP_R   = " ===---"

FILE_HEADER_RE = re.compile(
    r"^" + re.escape(FILE_SEP_L) + r"(.+?)" + re.escape(FILE_SEP_R) + r"\s*$",
    re.MULTILINE,
)

TEXT_EXTENSIONS = {
    ".html", ".htm", ".xhtml", ".css", ".scss", ".less", ".sass",
    ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
    ".py", ".pyw", ".rb", ".pl", ".pm", ".php",
    ".java", ".scala", ".kt",
    ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hh", ".hxx",
    ".cs", ".go", ".rs", ".swift",
    ".json", ".json5", ".xml", ".xsl", ".xslt",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".md", ".markdown", ".rst", ".txt", ".log",
    ".sh", ".bash", ".zsh", ".fish", ".bat", ".cmd", ".ps1",
    ".sql", ".vue", ".svelte",
    ".glsl", ".hlsl", ".wgsl", ".vert", ".frag",
    ".cmake", ".mk", ".csv", ".lua", ".dart",
}

TEXT_FILENAMES = {
    "Makefile", "Dockerfile", "Rakefile", "Gemfile",
    "Vagrantfile", "Jenkinsfile",
    ".gitignore", ".gitattributes", ".editorconfig",
    ".babelrc", ".eslintrc", ".prettierrc",
    ".npmrc", ".nvmrc", ".env", ".env.local", ".env.production",
    ".python-version", "README", "LICENSE", "COPYING", "AUTHORS",
}

BINARY_EXTENSIONS = {
    ".bin", ".dat", ".exe", ".dll", ".so", ".dylib", ".o", ".obj",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".tiff",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".rar", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp3", ".mp4", ".wav", ".ogg", ".flac", ".avi", ".mov", ".mkv",
    ".pyc", ".class", ".jar", ".war", ".wasm", ".sqlite", ".db",
    ".pkl", ".pickle", ".npy", ".npz", ".parquet",
}

# ========================== ANSI 颜色 / 样式 ==========================

class C:
    """终端颜色与样式"""
    RST   = "\033[0m"
    BOLD  = "\033[1m"
    DIM   = "\033[2m"
    ITAL  = "\033[3m"

    BLK   = "\033[30m"
    RED   = "\033[31m"
    GRN   = "\033[32m"
    YEL   = "\033[33m"
    BLU   = "\033[34m"
    MAG   = "\033[35m"
    CYN   = "\033[36m"
    WHT   = "\033[37m"

    B_RED = "\033[1;31m"
    B_GRN = "\033[1;32m"
    B_YEL = "\033[1;33m"
    B_BLU = "\033[1;34m"
    B_MAG = "\033[1;35m"
    B_CYN = "\033[1;36m"
    B_WHT = "\033[1;37m"

    BG_BLU   = "\033[44m"
    BG_GRN   = "\033[42m"
    BG_RED   = "\033[41m"
    BG_YEL   = "\033[43m"
    BG_CYN   = "\033[46m"
    BG_WHT   = "\033[47m"

    @staticmethod
    def supports_color():
        """检测终端是否支持颜色"""
        if os.getenv("NO_COLOR"):
            return False
        if not hasattr(sys.stdout, "isatty"):
            return False
        if not sys.stdout.isatty():
            return False
        if os.getenv("TERM") == "dumb":
            return False
        return True

# 如果终端不支持颜色，将所有颜色代码置空
if not C.supports_color():
    for attr in dir(C):
        if attr.startswith("_"):
            continue
        val = getattr(C, attr)
        if isinstance(val, str) and val.startswith("\033["):
            setattr(C, attr, "")


def s_ok(msg):    return f"{C.B_GRN}+{C.RST} {msg}"
def s_fail(msg):  return f"{C.B_RED}x{C.RST} {C.B_RED}{msg}{C.RST}"
def s_warn(msg):  return f"{C.B_YEL}!{C.RST} {C.YEL}{msg}{C.RST}"
def s_info(msg):  return f"{C.B_BLU}>{C.RST} {msg}"
def s_tip(msg):   return f"{C.B_CYN}*{C.RST} {C.CYN}{msg}{C.RST}"
def s_skip(msg):  return f"{C.DIM}>{C.RST} {C.DIM}{msg}{C.RST}"

CAT_ART = [" /\\_/\\", "( -.- )", " > ^ <"]


def banner(title, width=56):
    """猫猫 banner: 左右两只猫夹标题，用 ─ 连接"""
    cat = CAT_ART
    inner_w = width - len(cat[1]) * 2 - 2
    raw_title = f" {title} "
    dash_total = max(0, inner_w - len(raw_title))
    left_d = dash_total // 2
    right_d = dash_total - left_d

    lines = []
    gap0 = width - len(cat[0]) * 2
    lines.append(f"{C.CYN}{cat[0]}{C.RST}{' ' * gap0}{C.CYN}{cat[0]}{C.RST}")
    lines.append(
        f"{C.CYN}{cat[1]}{C.RST} {C.DIM}{C.CYN}{'─' * left_d}{C.RST} "
        f"{C.BOLD}{C.CYN}{raw_title}{C.RST}{C.DIM}{C.CYN}{'─' * right_d}{C.RST}"
        f" {C.CYN}{cat[1]}{C.RST}"
    )
    gap2 = width - len(cat[2]) * 2
    lines.append(f"{C.CYN}{cat[2]}{C.RST}{' ' * gap2}{C.CYN}{cat[2]}{C.RST}")
    return "\n".join(lines)


def divider():
    return f"{C.DIM}{'─' * 52}{C.RST}"


def path_highlight(p):
    """路径高亮"""
    parts = p.rsplit("/", 1) if "/" in p else ("", p)
    if len(parts) == 2:
        return f"{C.DIM}{parts[0]}/{C.RST}{C.WHT}{parts[1]}{C.RST}"
    return f"{C.WHT}{p}{C.RST}"


def norm_ext(ext: str) -> str:
    """规范化后缀: 确保以 . 开头，转小写"""
    ext = ext.strip().lower()
    if ext and not ext.startswith("."):
        ext = "." + ext
    return ext


def parse_skip_ext_input(raw: str) -> set:
    """从用户输入中解析后缀列表，支持空格/逗号/分号分隔"""
    raw = raw.strip()
    if not raw:
        return set()
    raw = raw.replace(",", " ").replace(";", " ")
    result = set()
    for part in raw.split():
        e = norm_ext(part)
        if e:
            result.add(e)
    return result


# ========================== 工具函数 ==========================

def is_text_file(filepath: str) -> bool:
    ext  = Path(filepath).suffix.lower()
    name = os.path.basename(filepath)
    if ext in TEXT_EXTENSIONS or name in TEXT_FILENAMES:
        return True
    if ext in BINARY_EXTENSIONS:
        return False
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            f.read(8192)
        return True
    except (UnicodeDecodeError, PermissionError, OSError):
        return False


def get_file_size_str(filepath: str) -> str:
    try:
        size = os.path.getsize(filepath)
        return format_size(size)
    except OSError:
        return "unknown"


def format_size(n: int) -> str:
    """字节数格式化"""
    if n >= 1048576:
        return f"{n / 1048576:.1f} MB"
    elif n >= 1024:
        return f"{n / 1024:.1f} KB"
    else:
        return f"{n} bytes"


def remove_comments(text: str, filepath: str) -> str:
    ext = Path(filepath).suffix.lower()

    if ext in (".json", ".json5"):
        return text
    if ext in (".html", ".htm", ".xhtml", ".xml", ".xsl", ".xslt"):
        return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    if ext in (".css", ".scss", ".less", ".sass"):
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
        return text
    if ext in (
        ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs",
        ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hh", ".hxx",
        ".java", ".scala", ".kt", ".cs", ".go", ".rs", ".swift",
        ".glsl", ".hlsl", ".wgsl", ".vert", ".frag", ".vue", ".svelte",
    ):
        text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        return text
    if ext in (
        ".py", ".pyw", ".rb", ".pl", ".pm",
        ".sh", ".bash", ".zsh", ".fish",
        ".yaml", ".yml", ".toml", ".lua", ".dart",
    ):
        text = re.sub(r"#.*?$", "", text, flags=re.MULTILINE)
        return text
    if ext == ".sql":
        text = re.sub(r"--.*?$", "", text, flags=re.MULTILINE)
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        return text
    if ext in (".bat", ".cmd"):
        text = re.sub(r"^\s*REM\b.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
        text = re.sub(r"^\s*::.*$", "", text, flags=re.MULTILINE)
        return text
    return text


def clean_empty_lines(text: str) -> str:
    lines = text.split("\n")
    result, empty = [], 0
    for line in lines:
        if line.strip() == "":
            empty += 1
            if empty <= 1:
                result.append("")
        else:
            empty = 0
            result.append(line)
    while result and result[0].strip()  == "": result.pop(0)
    while result and result[-1].strip() == "": result.pop()
    return "\n".join(result)


def generate_tree(root_dir: str, skip_exts: set = None) -> str:
    """生成目录树（写入输出文件的纯文本版）"""
    if skip_exts is None:
        skip_exts = set()
    root_name = os.path.basename(root_dir) or os.path.basename(os.getcwd())
    self_name = os.path.basename(__file__)
    lines = [f"{root_name}/"]

    def walk(dir_path: str, prefix: str):
        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            return

        filtered = []
        for e in entries:
            full = os.path.join(dir_path, e)
            if os.path.isdir(full):
                if e in EXCLUDE_DIRS:
                    continue
                filtered.append(e)
            else:
                if e in EXCLUDE_FILES or e == OUTPUT_FILENAME or e == self_name:
                    continue
                if skip_exts and Path(full).suffix.lower() in skip_exts:
                    continue
                filtered.append(e)

        dirs  = sorted(e for e in filtered if os.path.isdir(os.path.join(dir_path, e)))
        files = sorted(e for e in filtered if not os.path.isdir(os.path.join(dir_path, e)))
        all_entries = dirs + files

        for i, entry in enumerate(all_entries):
            full     = os.path.join(dir_path, entry)
            is_last  = i == len(all_entries) - 1
            conn     = "└── " if is_last else "├── "
            ext_pre  = "    " if is_last else "│   "

            if os.path.isdir(full):
                lines.append(f"{prefix}{conn}{entry}/")
                walk(full, prefix + ext_pre)
            else:
                lines.append(f"{prefix}{conn}{entry}")

    walk(root_dir, "")
    return "\n".join(lines)


def generate_display_tree(root_dir: str, skip_exts: set = None,
                          include_binary: bool = False) -> str:
    """生成带大小和标记的终端显示用目录树"""
    if skip_exts is None:
        skip_exts = set()
    root_name = os.path.basename(root_dir) or os.path.basename(os.getcwd())
    self_name = os.path.basename(__file__)
    lines = []

    def walk(dir_path: str, prefix: str):
        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            return

        filtered = []
        for e in entries:
            full = os.path.join(dir_path, e)
            if os.path.isdir(full):
                if e in EXCLUDE_DIRS:
                    continue
                filtered.append(e)
            else:
                if e in EXCLUDE_FILES or e == OUTPUT_FILENAME or e == self_name:
                    continue
                filtered.append(e)

        dirs  = sorted(e for e in filtered if os.path.isdir(os.path.join(dir_path, e)))
        files = sorted(e for e in filtered if not os.path.isdir(os.path.join(dir_path, e)))
        all_entries = dirs + files

        for i, entry in enumerate(all_entries):
            full    = os.path.join(dir_path, entry)
            is_last = i == len(all_entries) - 1
            conn    = "└── " if is_last else "├── "
            ext_pre = "    " if is_last else "│   "

            if os.path.isdir(full):
                lines.append(
                    f"{C.DIM}{prefix}{conn}{C.RST}{C.B_CYN}{entry}/{C.RST}"
                )
                walk(full, prefix + ext_pre)
            else:
                file_ext = Path(full).suffix.lower()
                size_str = get_file_size_str(full)
                size_col = f"{C.DIM}({size_str}){C.RST}"

                if file_ext in skip_exts:
                    name   = f"{C.DIM}{entry}{C.RST}"
                    marker = f"  {C.YEL}[skip: {file_ext}]{C.RST}"
                elif not is_text_file(full):
                    if include_binary:
                        name   = f"{C.MAG}{entry}{C.RST}"
                        marker = f"  {C.MAG}[binary]{C.RST}"
                    else:
                        name   = f"{C.DIM}{entry}{C.RST}"
                        marker = f"  {C.DIM}[binary, skip]{C.RST}"
                else:
                    name   = f"{C.WHT}{entry}{C.RST}"
                    marker = ""

                lines.append(
                    f"{C.DIM}{prefix}{conn}{C.RST}{name}  {size_col}{marker}"
                )

    lines.append(f"  {C.B_WHT}{root_name}/{C.RST}")
    walk(root_dir, "  ")
    return "\n".join(lines)


# ========================== 模式 1 : 打包 ==========================

def pack(description: str, keep_comments: bool = False,
         include_binary: bool = False, skip_exts: set = None):
    root_dir  = os.getcwd()
    self_name = os.path.basename(__file__)

    if skip_exts is None:
        skip_exts = set()

    # ---- 静默扫描 ----
    tree_str = generate_tree(root_dir, skip_exts=skip_exts)

    file_entries      = []
    skipped_binaries  = []
    skipped_by_ext    = 0
    errors            = 0

    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS)

        for filename in sorted(filenames):
            if filename in EXCLUDE_FILES or filename == OUTPUT_FILENAME or filename == self_name:
                continue

            filepath = os.path.join(dirpath, filename)
            relpath  = os.path.relpath(filepath, root_dir).replace("\\", "/")
            file_ext = Path(filepath).suffix.lower()

            if file_ext in skip_exts:
                skipped_by_ext += 1
                continue

            if is_text_file(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    if not keep_comments:
                        content = remove_comments(content, filepath)
                        content = clean_empty_lines(content)
                    file_entries.append((relpath, content, False))
                except Exception:
                    errors += 1
            else:
                if include_binary:
                    try:
                        with open(filepath, "rb") as f:
                            data = f.read()
                        content = base64.b64encode(data).decode("ascii")
                        file_entries.append((relpath, content, True))
                    except Exception:
                        errors += 1
                else:
                    size_str = get_file_size_str(filepath)
                    placeholder = f"[binary file omitted -- {size_str}]"
                    file_entries.append((relpath, placeholder, False))
                    skipped_binaries.append((relpath, size_str))

    # ---- 写入输出文件 ----
    parts = [description, "", TREE_MARKER, "", tree_str, "", CODE_MARKER]
    for relpath, content, is_binary in file_entries:
        parts.append("")
        tag = f"{FILE_SEP_L}{relpath}{' [binary]' if is_binary else ''}{FILE_SEP_R}"
        parts.append(tag)
        parts.append(content)

    output = "\n".join(parts)
    output_path = os.path.join(root_dir, OUTPUT_FILENAME)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

    # ---- 显示结果 ----
    output_size = os.path.getsize(output_path)
    output_s    = format_size(output_size)

    print(banner("PROJECT PACKER"))
    print()
    if skip_exts:
        ext_list = ", ".join(sorted(skip_exts))
        print(s_info(f"Skip extensions: {C.YEL}{ext_list}{C.RST}"))
        print()
    print(generate_display_tree(
        root_dir, skip_exts=skip_exts, include_binary=include_binary
    ))
    print()
    print(divider())
    print(s_ok(f"Pack complete, Size {C.BOLD}{output_s}{C.RST}"))
    if skipped_binaries:
        print(s_tip("Use --include-binary to pack binary file content"))
    if errors:
        print(s_warn(f"{errors} file(s) failed to read"))


# ========================== 模式 2 : 解包 ==========================

def unpack(txt_filepath: str):
    if not os.path.exists(txt_filepath):
        print(s_fail(f"File not found: {txt_filepath}"))
        return

    print(banner("PROJECT UNPACKER"))
    print()

    with open(txt_filepath, "r", encoding="utf-8") as f:
        text = f.read()

    code_idx = text.find(CODE_MARKER)
    if code_idx == -1:
        print(s_fail("Format error: code marker not found"))
        return
    code_section = text[code_idx + len(CODE_MARKER):]

    matches = list(FILE_HEADER_RE.finditer(code_section))
    if not matches:
        print(s_fail("Format error: no file entries found"))
        return

    files = []
    placeholders = []

    for i, m in enumerate(matches):
        raw       = m.group(1)
        is_binary = "[binary]" in raw
        relpath   = raw.replace(" [binary]", "").strip()

        start = m.end()
        if start < len(code_section) and code_section[start] == "\n":
            start += 1
        end     = matches[i + 1].start() if i + 1 < len(matches) else len(code_section)
        content = code_section[start:end].rstrip("\n")
        files.append((relpath, content, is_binary))

        if content.strip().startswith("[binary file omitted"):
            placeholders.append(relpath)

    print(s_info(f"Found {C.BOLD}{len(files)}{C.RST} file(s)"))
    print()

    for relpath, content, is_binary in files:
        if content.strip().startswith("[binary file omitted"):
            print(f"    {C.DIM}{relpath}  (placeholder){C.RST}")
        elif is_binary:
            print(f"    {C.MAG}{relpath}  (binary){C.RST}")
        else:
            print(f"    {C.WHT}{relpath}{C.RST}")

    if placeholders:
        print()
        print(s_warn(f"{len(placeholders)} file(s) are placeholders, cannot be restored:"))
        for p in placeholders:
            print(f"      {C.DIM}-- {p}{C.RST}")

    print()
    print(divider())
    try:
        confirm = input(f"  {C.BOLD}Continue?{C.RST} [y/N] ").strip().lower()
    except EOFError:
        confirm = "n"
    if confirm != "y":
        print(s_skip("Cancelled."))
        return

    print()
    root_dir = os.getcwd()
    count = 0
    for relpath, content, is_binary in files:
        if content.strip().startswith("[binary file omitted"):
            print(s_skip(f"Skip placeholder: {path_highlight(relpath)}"))
            continue

        filepath = os.path.join(root_dir, relpath)
        dirpath  = os.path.dirname(filepath)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        try:
            if is_binary:
                with open(filepath, "wb") as f:
                    f.write(base64.b64decode(content))
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
            print(s_ok(f"Created {path_highlight(relpath)}"))
            count += 1
        except Exception as e:
            print(s_fail(f"{relpath}: {e}"))

    print()
    print(divider())
    print(s_ok(f"Unpack complete, {C.BOLD}{count}{C.RST} file(s) created"))
    if placeholders:
        print(s_warn(f"{len(placeholders)} binary file(s) not restored"))


# ========================== 主入口 ==========================

def main():
    print(banner("PROJECT PACKER"))
    print()
    print(f"  {C.BOLD}1{C.RST}  {C.WHT}Pack{C.RST}   -- scan directory, generate description file")
    print(f"  {C.BOLD}2{C.RST}  {C.WHT}Unpack{C.RST} -- restore project from description file")
    print()

    try:
        choice = input(f"  {C.B_CYN}>{C.RST} Select mode [1/2]: ").strip()
    except EOFError:
        choice = ""

    if choice == "1":
        try:
            desc = input(f"  {C.B_CYN}>{C.RST} Project description: ").strip() or "Project"
        except EOFError:
            desc = "Project"
        try:
            keep = input(f"  {C.B_CYN}>{C.RST} Keep comments? [y/N]: ").strip().lower() == "y"
        except EOFError:
            keep = False
        try:
            ibin = input(f"  {C.B_CYN}>{C.RST} Include binary content? [y/N]: ").strip().lower() == "y"
        except EOFError:
            ibin = False
        try:
            skip_raw = input(f"  {C.B_CYN}>{C.RST} Skip extensions (e.g. .log .tmp): ").strip()
        except EOFError:
            skip_raw = ""
        skip_exts = parse_skip_ext_input(skip_raw)
        print()
        pack(desc, keep_comments=keep, include_binary=ibin, skip_exts=skip_exts)

    elif choice == "2":
        try:
            path = input(f"  {C.B_CYN}>{C.RST} Description file path: ").strip().strip('"').strip("'")
        except EOFError:
            path = ""
        print()
        if path:
            unpack(path)
        else:
            print(s_fail("No file path provided."))

    else:
        print(s_skip("Invalid choice."))


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        mode = sys.argv[1].lower()
        if mode in ("pack", "1"):
            args = sys.argv[2:]
            keep_comments  = False
            include_binary = False
            skip_exts      = set()
            desc_parts     = []
            collecting_skip = False

            for a in args:
                if a in ("--keep-comments", "--keep", "-k"):
                    keep_comments = True
                elif a in ("--include-binary", "--binary", "-b"):
                    include_binary = True
                elif a in ("--skip-ext", "--skip", "-s"):
                    collecting_skip = True
                elif a.startswith("-"):
                    pass
                elif collecting_skip:
                    ext = norm_ext(a)
                    if ext:
                        skip_exts.add(ext)
                else:
                    desc_parts.append(a)

            desc = " ".join(desc_parts) or "Project"
            pack(desc, keep_comments=keep_comments, include_binary=include_binary,
                 skip_exts=skip_exts)

        elif mode in ("unpack", "2"):
            if len(sys.argv) < 3:
                print(s_fail("Usage: python project_packer.py unpack <txt_file_path>"))
                sys.exit(1)
            unpack(sys.argv[2])

        elif mode in ("help", "-h", "--help"):
            print(__doc__)
        else:
            print(s_fail(f"Unknown argument: {mode}"))
            print(__doc__)
            sys.exit(1)
    else:
        main()
