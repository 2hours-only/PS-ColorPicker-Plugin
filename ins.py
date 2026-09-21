#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Photoshop UXP 插件安装/卸载工具

安装:  python3 ps_plugin_manager.py install <插件项目文件夹路径>
卸载:  python3 ps_plugin_manager.py uninstall <插件名称>
列出:  python3 ps_plugin_manager.py list

说明:
  安装时会自动读取 <参数目录>/manifest.json 中的
    id / name / version / host.minVersion
  无需在脚本顶部手工配置。
"""

import json
import os
import shutil
import sys

# ===== 目标路径 =====
EXTERNAL_DIR = os.path.expanduser(
    "~/Library/Application Support/Adobe/UXP/Plugins/External"
)
PS_JSON_PATH = os.path.expanduser(
    "~/Library/Application Support/Adobe/UXP/PluginsInfo/v1/PS.json"
)


# ==================== 通用工具函数 ====================

def backup_file(file_path):
    """备份文件到 file_path.bak"""
    backup_path = file_path + ".bak"
    try:
        shutil.copy2(file_path, backup_path)
        print(f"  [OK] 已备份: {backup_path}")
        return True
    except Exception as e:
        print(f"  [ERROR] 备份失败: {e}")
        return False


def write_json_atomic(file_path, data):
    """原子写入 JSON：先写临时文件再 rename，防止中途崩溃导致文件损坏。"""
    tmp_path = file_path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        os.replace(tmp_path, file_path)
        return True
    except Exception as e:
        print(f"  [ERROR] 写入失败: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        bak = file_path + ".bak"
        if os.path.exists(bak):
            shutil.copy2(bak, file_path)
            print(f"  [INFO] 已从备份恢复: {bak}")
        return False


def read_ps_json():
    """读取 PS.json，返回 dict 或 None。"""
    if not os.path.isfile(PS_JSON_PATH):
        print(f"  [ERROR] PS.json 不存在: {PS_JSON_PATH}")
        print(f"          请确认 Photoshop 已至少启动过一次以生成此文件")
        return None
    try:
        with open(PS_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] 读取 PS.json 失败: {e}")
        return None
    if "plugins" not in data or not isinstance(data["plugins"], list):
        print("  [ERROR] PS.json 格式异常：缺少 plugins 数组")
        return None
    return data


def parse_manifest(manifest_path):
    """
    从 manifest.json 解析插件信息。

    UXP manifest 中:
      id          -> 插件 id
      name        -> 插件名称
      version     -> 版本号
      host        -> 对象 或 数组，取其 minVersion 字段
    """
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"  [ERROR] 读取 manifest.json 失败: {e}")
        return None

    plugin_id = manifest.get("id")
    plugin_name = manifest.get("name")
    plugin_version = manifest.get("version")

    # host 可以是对象，也可以是数组（PS 支持多 host）
    host = manifest.get("host", {})
    if isinstance(host, list):
        host = host[0] if host else {}
    elif not isinstance(host, dict):
        host = {}
    host_min_version = host.get("minVersion", "0.0.0")

    if not plugin_id:
        print("  [ERROR] manifest.json 缺少 'id' 字段")
        return None
    if not plugin_name:
        print("  [ERROR] manifest.json 缺少 'name' 字段")
        return None
    if not plugin_version:
        print("  [ERROR] manifest.json 缺少 'version' 字段")
        return None

    return {
        "id": plugin_id,
        "name": plugin_name,
        "version": plugin_version,
        "host_min_version": host_min_version,
    }


# ==================== 安装 ====================

def install(src_dir):
    print("=" * 55)
    print("  插件安装")
    print("=" * 55)

    src_dir = os.path.abspath(os.path.expanduser(src_dir))
    if not os.path.isdir(src_dir):
        print(f"\n[ERROR] 路径不存在或不是文件夹: {src_dir}")
        sys.exit(1)

    print(f"\n源目录:   {src_dir}")
    print(f"目标目录: {EXTERNAL_DIR}")
    print(f"PS.json:  {PS_JSON_PATH}")

    # --- 步骤 1: 解析 manifest.json ---
    print("\n--- 步骤 1/3: 解析 manifest.json ---")
    manifest_path = os.path.join(src_dir, "manifest.json")
    if not os.path.isfile(manifest_path):
        print(f"  [ERROR] 未在源目录根下找到 manifest.json: {manifest_path}")
        print("          请确保 manifest.json 直接位于插件项目根目录下（不要放在子文件夹内）")
        sys.exit(1)

    plugin_info = parse_manifest(manifest_path)
    if plugin_info is None:
        sys.exit(1)

    plugin_id          = plugin_info["id"]
    plugin_name        = plugin_info["name"]
    plugin_version     = plugin_info["version"]
    host_min_version   = plugin_info["host_min_version"]

    print(f"  [OK] manifest.json 解析成功")
    print(f"        id:          {plugin_id}")
    print(f"        name:        {plugin_name}")
    print(f"        version:     {plugin_version}")
    print(f"        host minVer: {host_min_version}")

    # --- 步骤 2: 复制项目文件 ---
    print("\n--- 步骤 2/3: 复制插件文件 ---")
    os.makedirs(EXTERNAL_DIR, exist_ok=True)
    print(f"  [OK] 确保目录存在: {EXTERNAL_DIR}")

    folder_name = f"{plugin_id}_{plugin_version}"
    dest_folder = os.path.join(EXTERNAL_DIR, folder_name)

    if os.path.exists(dest_folder):
        print(f"  [INFO] 目标文件夹已存在，先删除旧版: {dest_folder}")
        shutil.rmtree(dest_folder)

    try:
        shutil.copytree(src_dir, dest_folder)
    except Exception as e:
        print(f"  [ERROR] 复制失败: {e}")
        sys.exit(1)
    file_count = sum(len(files) for _, _, files in os.walk(dest_folder))
    print(f"  [OK] 已复制项目到: {dest_folder}")
    print(f"  [INFO] 共复制 {file_count} 个文件")

    # --- 步骤 3: 更新 PS.json ---
    print("\n--- 步骤 3/3: 更新 PS.json ---")
    ps_data = read_ps_json()
    if ps_data is None:
        sys.exit(1)

    backup_file(PS_JSON_PATH)

    # 移除同 ID 旧条目
    original = len(ps_data["plugins"])
    ps_data["plugins"] = [p for p in ps_data["plugins"] if p.get("pluginId") != plugin_id]
    removed = original - len(ps_data["plugins"])
    if removed > 0:
        print(f"  [INFO] 移除了 {removed} 条旧记录 (pluginId={plugin_id})")

    # 追加新条目
    new_entry = {
        "hostMinVersion": host_min_version,
        "name": plugin_name,
        "path": f"$localPlugins/External/{folder_name}",
        "pluginId": plugin_id,
        "status": "enabled",
        "type": "uxp",
        "versionString": plugin_version,
    }
    ps_data["plugins"].append(new_entry)
    print(f"  [OK] 已追加: {plugin_name} ({plugin_id})")

    if not write_json_atomic(PS_JSON_PATH, ps_data):
        print("\n[ABORT] 写入 PS.json 失败")
        sys.exit(1)
    print(f"  [OK] 已更新 PS.json")

    # --- 验证 ---
    print("\n========== 验证安装结果 ==========")
    if os.path.isdir(dest_folder) and os.path.isfile(os.path.join(dest_folder, "manifest.json")):
        print("  [PASS] 插件文件夹与 manifest.json 就位")
    else:
        print("  [FAIL] 文件验证失败")

    ps_data2 = read_ps_json()
    if ps_data2:
        found = any(p.get("pluginId") == plugin_id for p in ps_data2["plugins"])
        print(f"  {'[PASS]' if found else '[FAIL]'} PS.json 条目{'已写入' if found else '缺失'}")

    print("\n" + "=" * 55)
    print("  安装完成！请重启 Photoshop。")
    print(f"  在菜单 [增效工具/Plugins] 中找到 [{plugin_name}] 面板。")
    print("=" * 55)


# ==================== 卸载 ====================

def uninstall(plugin_name):
    print("=" * 55)
    print("  插件卸载")
    print("=" * 55)
    print(f"\n  目标插件名称: {plugin_name}")
    print(f"  PS.json:       {PS_JSON_PATH}")
    print(f"  External 目录: {EXTERNAL_DIR}")

    # --- 步骤 1: 读取 PS.json 并查找匹配条目 ---
    print("\n--- 步骤 1/3: 查找插件条目 ---")
    ps_data = read_ps_json()
    if ps_data is None:
        sys.exit(1)

    matched = [p for p in ps_data["plugins"] if p.get("name") == plugin_name]
    if not matched:
        print(f"  [ERROR] 在 PS.json 中未找到名为 '{plugin_name}' 的插件")
        print(f"\n  当前已安装的插件列表:")
        for p in ps_data["plugins"]:
            print(f"    - {p.get('name', '?')} (id={p.get('pluginId', '?')})")
        sys.exit(1)

    print(f"  [OK] 找到 {len(matched)} 条匹配记录:")
    for entry in matched:
        print(f"    - name: {entry.get('name')}")
        print(f"      id:   {entry.get('pluginId')}")
        print(f"      path: {entry.get('path')}")
        print(f"      ver:  {entry.get('versionString')}")

    # --- 收集要删除的文件夹 ---
    folders_to_remove = []
    for entry in matched:
        path_str = entry.get("path", "")
        if "$localPlugins/External/" in path_str:
            folder_name = path_str.split("$localPlugins/External/")[-1]
            if folder_name:
                folders_to_remove.append(folder_name)

    # --- 步骤 2: 备份并更新 PS.json ---
    print("\n--- 步骤 2/3: 从 PS.json 移除条目 ---")
    backup_file(PS_JSON_PATH)

    original = len(ps_data["plugins"])
    ps_data["plugins"] = [p for p in ps_data["plugins"] if p.get("name") != plugin_name]
    removed = original - len(ps_data["plugins"])
    print(f"  [INFO] 移除了 {removed} 条记录")

    if not write_json_atomic(PS_JSON_PATH, ps_data):
        print("\n[ABORT] 写入 PS.json 失败")
        sys.exit(1)
    print(f"  [OK] 已更新 PS.json")

    # --- 步骤 3: 删除插件文件夹 ---
    print("\n--- 步骤 3/3: 删除插件文件 ---")
    if not folders_to_remove:
        print("  [INFO] 未从 path 中提取到文件夹名，跳过文件删除")
    for folder_name in folders_to_remove:
        folder_path = os.path.join(EXTERNAL_DIR, folder_name)
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            print(f"  [OK] 已删除文件夹: {folder_path}")
        else:
            print(f"  [INFO] 文件夹不存在（可能已手动删除）: {folder_path}")

    # --- 验证 ---
    print("\n========== 验证卸载结果 ==========")
    ps_data2 = read_ps_json()
    if ps_data2:
        still = [p for p in ps_data2["plugins"] if p.get("name") == plugin_name]
        if not still:
            print(f"  [PASS] PS.json 中已无 '{plugin_name}' 条目")
        else:
            print(f"  [FAIL] PS.json 中仍有残留: {len(still)} 条")

        print(f"\n  剩余插件 ({len(ps_data2['plugins'])} 个):")
        for p in ps_data2["plugins"]:
            print(f"    - {p.get('name', '?')}")

    print("\n" + "=" * 55)
    print("  卸载完成！请重启 Photoshop。")
    print("=" * 55)


# ==================== 列出已安装插件 ====================

def list_plugins():
    print("=" * 55)
    print("  已安装 UXP 插件列表")
    print("=" * 55)
    print(f"\n  PS.json: {PS_JSON_PATH}\n")

    ps_data = read_ps_json()
    if ps_data is None:
        sys.exit(1)

    plugins = ps_data.get("plugins", [])
    if not plugins:
        print("  (无已安装插件)")
        return

    print(f"  共 {len(plugins)} 个插件:\n")
    print(f"  {'序号':<4} {'名称':<20} {'ID':<35} {'版本':<10} {'状态'}")
    print(f"  {'----':<4} {'--------------------':<20} {'-----------------------------------':<35} {'----------':<10} {'------'}")
    for i, p in enumerate(plugins, 1):
        name = p.get("name", "?")
        pid = p.get("pluginId", "?")
        ver = p.get("versionString", "?")
        status = p.get("status", "?")
        path = p.get("path", "")
        folder = path.split("$localPlugins/External/")[-1] if "$localPlugins/External/" in path else path
        folder_exists = "✓" if os.path.isdir(os.path.join(EXTERNAL_DIR, folder)) else "✗"
        print(f"  {i:<4} {name:<20} {pid:<35} {ver:<10} {status} (文件夹:{folder_exists})")


# ==================== 主入口 ====================

def print_usage():
    print("""
==================================================
  Photoshop UXP 插件管理工具
==================================================

用法:
  安装:  python3 ps_plugin_manager.py install  <插件项目文件夹路径>
  卸载:  python3 ps_plugin_manager.py uninstall <插件名称>
  列表:  python3 ps_plugin_manager.py list

示例:
  python3 ps_plugin_manager.py install  ~/Desktop/prj_v10_main
  python3 ps_plugin_manager.py uninstall 录制1
  python3 ps_plugin_manager.py list

注意:
  - 安装时会自动读取 <参数目录>/manifest.json 中的
    id / name / version / host.minVersion，无需手工配置。
  - manifest.json 必须直接位于插件项目根目录下（不要放在子文件夹内）。
  - 卸载时只需提供插件名称（PS.json 中 name 字段的值）。
  - 操作前会自动备份 PS.json 到 PS.json.bak
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "install":
        if len(sys.argv) < 3:
            print("[ERROR] 缺少参数: 请提供插件项目文件夹路径")
            print("  用法: python3 ps_plugin_manager.py install <路径>")
            sys.exit(1)
        install(sys.argv[2])

    elif command == "uninstall":
        if len(sys.argv) < 3:
            print("[ERROR] 缺少参数: 请提供要卸载的插件名称")
            print("  用法: python3 ps_plugin_manager.py uninstall <插件名称>")
            sys.exit(1)
        plugin_name = " ".join(sys.argv[2:])
        uninstall(plugin_name)

    elif command == "list":
        list_plugins()

    else:
        print(f"[ERROR] 未知命令: {command}")
        print_usage()
        sys.exit(1)
