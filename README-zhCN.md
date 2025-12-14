# LudusEngine

[English Documentation](README.md)

LudusEngine 是一个通用的游戏引擎，专为创作和游玩桌游及卡牌游戏而设计。它包含了一个用于生成游戏资源的自定义领域特定语言 (DSL)、一个强大的 Python 游戏服务器以及一个现代化的 Web 前端。

## 特性

- **LuduScript (DSL)**: 专为定义和生成游戏卡牌及资源（如扑克牌、狼人杀卡牌）设计的脚本语言（C++）。
- **实时游戏服务器**: 基于 Python、Flask 和 Socket.IO 构建，高效处理游戏逻辑和玩家连接。
- **跨平台客户端**: 基于 Vue 3 + TypeScript 的前端，可流畅运行于 Web 浏览器中，或作为独立桌面应用（使用 `pywebview`）运行。
- **灵活的游戏定义**: 使用 Python 脚本和 JSON 配置轻松定义新游戏和规则。
- **多种运行模式**: 支持桌面 (Desktop)、浏览器 (Browser) 和浏览器应用 (App) 模式。

## 项目结构

- **`res/dsl/`**: **LuduScript** 的源代码，用于生成游戏资源的 C++ DSL。
- **`res/app/`**: 基于 **Vue 3**、**Vite** 和 **TypeScript** 构建的前端应用。
- **`src/`**: 后端源代码，包括游戏服务器、玩家管理和核心逻辑。
- **`.games/`**: 包含游戏定义和资源的目录（例如：Spyfall, Werewolf）。
- **`app.py`**: 应用程序的主要入口点。

## 环境要求

- **Python 3.8+**
- **Node.js & npm** (用于构建前端)
- **CMake & C++ 编译器** (用于构建 DSL，如果提供预编译二进制文件则为可选)

## 安装与设置

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/LudusEngine.git
cd LudusEngine
```

### 2. 构建前端

进入前端目录并安装依赖：

```bash
cd res/app
npm install
```

构建前端资源：

```bash
npm run build
```

这将在 `res/app/static` 中生成静态文件，由 Python 后端提供服务。

### 3. 安装后端依赖

返回根目录并安装所需的 Python 包：

```bash
cd ../..
pip install -r requirements.txt
```

### 4. 构建 DSL (可选)

如果您需要使用 LuduScript 修改或重新生成游戏资源：

```bash
cd res/dsl
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

## 使用方法

使用 `app.py` 启动应用程序。引擎通过环境变量支持不同的运行模式。

### 默认 (浏览器模式)

```bash
python app.py
```

### 桌面模式

作为独立桌面应用程序运行（需要 `pywebview`）：

```bash
# Windows
set MODE=desktop
python app.py

# Linux/macOS
export MODE=desktop
python app.py
```

### 调试模式

启用调试日志和功能：

```bash
# Windows
set DEBUG_APP=1
python app.py
```

## 创建游戏

游戏位于 `.games/` 目录下。每个游戏通常包含：

- `config.json`: 游戏配置。
- `game.py`: 定义游戏逻辑的 Python 脚本。
- `prompt.json`: AI 提示词（如果适用）。

使用 `res/dsl/` 中的 **LuduScript** 为您的游戏生成复杂的卡牌集或资源。

## 许可证

本项目采用 Apache 2.0 许可证。详情请参阅 [LICENSE](LICENSE) 文件。
