# 安装说明

[返回首页](../README.md)

本插件提供三种安装方式。

Window 系统仅提供一种官方安装方式，如果您因使用盗版 PS 导致方式一安装失败，可以尝试将此安装文档提供给 AI ，并且让 AI 根据文档给出类似方式三的安装步骤。您也可以请直接联系开发者。

macOS 系统提供官方安装方式与两种后备方式，您可以依次尝试。

---

## 方式一（官方安装方式）：使用 CCX 安装包

适用于已经安装 Adobe Creative Cloud 桌面应用的用户，操作最为简单。

1. 从 GitHub 仓库的 `installer/` 文件夹下载 `.ccx` 文件 `com.rax.lutpicker_PS.ccx`。在 GitHub 中打开文件后，点击 **Download raw**，或从 Release 下载附件；不要下载网页本身。
2. 打开 **Adobe Creative Cloud** 桌面应用，并保持登录状态。
3. 在 Finder 的“下载”文件夹中找到刚下载的 `.ccx` 文件，双击它。
4. 如果系统询问“使用哪个应用打开”，选择 **Adobe Creative Cloud**。
5. 按 Creative Cloud 的提示完成安装。安装期间不要删除 `.ccx` 文件，也不要退出 Creative Cloud。
6. 安装完成后启动或重启 Photoshop，在 **增效工具 / Plugins** 菜单中找到插件，并打开“颜色”面板。

---

## 方式二：macOS 使用 Python 脚本安装

适用于：没有可用的 Creative Cloud 安装流程，但使用 macOS，且可以运行 Python 3 的用户。

### 1. 下载完整源码

从 GitHub 下载整个项目（不要只下载 `index.js` 或某个子文件夹），解压后应看到这些内容位于同一个项目根目录：

```text
manifest.json
index.html
index.js
style.css
asset/
images/
sentence/
ins.py
```

**清您把解压后的文件夹改名为 `LUT-Color-Picker`，并放在“下载”文件夹中。**

### 2. 打开终端并进入项目文件夹

打开 macOS 自带的“终端”（按 `Command + 空格`，输入“终端”，按回车），逐行复制并执行：

```bash
cd ~/Downloads/LUT-Color-Picker
```

检查是否进入了正确目录：

```bash
ls
```

输出中应该能看到 `manifest.json`、`ins.py` 和 `asset`。如果提示 `No such file or directory`，说明文件夹名称或位置不对；可以在 Finder 中右键项目文件夹，选择“显示简介”确认名称，或把文件夹拖进终端，终端会自动填入它的路径。

### 3. 运行安装脚本

```bash
python3 ins.py install .
```

这里的 `.` 表示“当前文件夹”。脚本会显示源目录、目标目录、插件 ID 和版本。正常结束时应看到：

```text
[PASS] 插件文件夹与 manifest.json 就位
[PASS] PS.json 条目已写入
安装完成！请重启 Photoshop。
```

看到“安装完成”后，重启 Photoshop，在 **增效工具 / Plugins** 菜单中打开插件。

---

## 方式三：macOS 手动安装

这种方式将手动执行方式二中由代码执行的工作，适合愿意按步骤操作的用户。操作前您请关闭 Photoshop，**并严格按照步骤做好文件备份**。

### 第一步：准备完整插件文件夹

从 GitHub 下载完整源码并解压。确认插件根目录**直接**包含 `manifest.json`、`index.html`、`index.js`、`style.css`、`asset`、`images` 和 `sentence`。以下把这个根目录称为“插件源文件夹”。

### 第二步：打开 External 文件夹

在 Finder 中按 `Command + Shift + G`，粘贴下面的路径，按回车：

```text
~/Library/Application Support/Adobe/UXP/Plugins/External
```

如果文件夹不存在，可以在 Finder 中逐级打开 `~/Library/Application Support/Adobe/UXP/Plugins/`，手动新建名为 `External` 的文件夹。不要把插件直接放到 `Plugins` 这一层。

### 第三步：复制插件文件

在 `External` 文件夹中新建一个文件夹。名称为`com.rax.lutpicker_1.0.0`。打开你的“插件源文件夹”，选中其中的**全部内容**，复制到这个新建文件夹中。您的文件夹结构应该类似：

```text
External/
└── com.rax.lutpicker_1.0.0/
    ├── manifest.json
    ├── index.html
    ├── index.js
    ├── style.css
    ├── asset/
    ├── images/
    └── sentence/
```

### 第四步：备份 PS.json

在 Finder 中按 `Command + Shift + G`，打开：

```text
~/Library/Application Support/Adobe/UXP/PluginsInfo/v1
```

找到 `PS.json`，复制一份并命名为 `PS.json.bak`。如果已经存在同名备份，可命名为 `PS.json.bak.日期`，例如 `PS.json.bak.2026-09-20`。

如果找不到 `PS.json`，先启动一次 Photoshop，退出后再查找。**不要**自行新建 `PS.json`。

### 第五步：编辑 PS.json

用文本编辑器（例如 mac 自带的文本编辑）或代码编辑器（例如 VS code）打开 `PS.json`（不要使用 Word 或 WPS）。这是 JSON 文件，原有内容必须保留。

您的`PS.json`内容应该类似下面的文件（条目数量与长度可能不同，但结构应该类似）

```json
{
  "plugins": [
    {
      "hostMinVersion": "24.2",
      "name": "Alchemist",
      "path": "$localPlugins/External/2bcdb900_2.7.0",
      "pluginId": "2bcdb900",
      "status": "enabled",
      "type": "uxp",
      "versionString": "2.7.0"
    },
    {
      "hostMinVersion": "24.0.0",
      "name": "Sentence Display",
      "path": "$localPlugins/External/com.ld.sentencedisplay_1.0.0",
      "pluginId": "com.ld.sentencedisplay",
      "status": "enabled",
      "type": "uxp",
      "versionString": "1.0.0"
    },
    {
      "hostMinVersion": "22.0.0",
      "name": "TourBox",
      "path": "$localPlugins/External/a26bc524_1.0.0",
      "pluginId": "a26bc524",
      "status": "enabled",
      "type": "uxp",
      "versionString": "1.0.0"
    },
    {
      "hostMinVersion": "24.0.0",
      "name": "Head Frame",
      "path": "$localPlugins/External/com.yourname.headframe_1.0.0",
      "pluginId": "com.yourname.headframe",
      "status": "enabled",
      "type": "uxp",
      "versionString": "1.0.0"
    },
    {
      "hostMinVersion": "24.0.0",
      "name": "录制",
      "path": "$localPlugins/External/com.20260519.psrecorder.v2_1.0.0",
      "pluginId": "com.20260519.psrecorder.v2",
      "status": "enabled",
      "type": "uxp",
      "versionString": "1.0.0"
    }
  ]
}
```

找到顶层的：

```json
"plugins": [
```

在数组最后一个插件对象后添加逗号，再添加下面这段代码：

```json
{
  "hostMinVersion": "24.0.0",
  "name": "LUT Color Picker",
  "path": "$localPlugins/External/com.rax.lutpicker_1.0.0",
  "pluginId": "com.rax.lutpicker",
  "status": "enabled",
  "type": "uxp",
  "versionString": "1.0.0"
}
```

添加完成后您的文件应该类似下面的结构：

```json
{
  "plugins": [
    {
      "hostMinVersion": "24.2",
      "name": "Alchemist",
      "path": "$localPlugins/External/2bcdb900_2.7.0",
      "pluginId": "2bcdb900",
      "status": "enabled",
      "type": "uxp",
      "versionString": "2.7.0"
    },
    {
      "hostMinVersion": "24.0.0",
      "name": "Sentence Display",
      "path": "$localPlugins/External/com.ld.sentencedisplay_1.0.0",
      "pluginId": "com.ld.sentencedisplay",
      "status": "enabled",
      "type": "uxp",
      "versionString": "1.0.0"
    },
    {
      "hostMinVersion": "22.0.0",
      "name": "TourBox",
      "path": "$localPlugins/External/a26bc524_1.0.0",
      "pluginId": "a26bc524",
      "status": "enabled",
      "type": "uxp",
      "versionString": "1.0.0"
    },
    {
      "hostMinVersion": "24.0.0",
      "name": "Head Frame",
      "path": "$localPlugins/External/com.yourname.headframe_1.0.0",
      "pluginId": "com.yourname.headframe",
      "status": "enabled",
      "type": "uxp",
      "versionString": "1.0.0"
    },
    {
      "hostMinVersion": "24.0.0",
      "name": "录制",
      "path": "$localPlugins/External/com.20260519.psrecorder.v2_1.0.0",
      "pluginId": "com.20260519.psrecorder.v2",
      "status": "enabled",
      "type": "uxp",
      "versionString": "1.0.0"
    },
    {
      "hostMinVersion": "24.0.0",
      "name": "LUT Color Picker",
      "path": "$localPlugins/External/com.rax.lutpicker_1.0.0",
      "pluginId": "com.rax.lutpicker",
      "status": "enabled",
      "type": "uxp",
      "versionString": "1.0.0"
    }
  ]
}
```

请注意检查这些规则：

- 所有键和值使用**英文输入法**双引号。
- 对象之间用逗号分隔。
- 最后一个对象后面不要多余逗号。

### 第六步：启动 Photoshop

保存 `PS.json` 后，完全退出并重新启动 Photoshop。在 **增效工具 / Plugins** 菜单中查找插件，打开“颜色”面板。

如果 Photoshop 无法启动或插件消失，立即退出 Photoshop，把备份文件 `PS.json.bak` 改回 `PS.json`，然后重新启动。不要继续修改未验证的 JSON，并联系开发者。
