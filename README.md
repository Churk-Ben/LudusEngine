# LudusEngine

[中文文档](README-zhCN.md)

LudusEngine is a versatile game engine designed for creating and playing board games and card games. It features a custom Domain Specific Language (DSL) for game asset generation, a robust Python-based game server, and a modern web-based frontend.

## Features

- **LuduScript (DSL)**: A specialized scripting language (C++) for defining and generating game cards and assets (e.g., Poker decks, Werewolf cards).
- **Real-time Game Server**: Built with Python, Flask, and Socket.IO to handle game logic and player connections efficiently.
- **Cross-Platform Client**: A Vue 3 + TypeScript frontend that runs seamlessly in a web browser or as a standalone desktop application (using `pywebview`).
- **Flexible Game Definitions**: Easily define new games and rules using Python scripts and JSON configurations.
- **Multiple Running Modes**: Support for Desktop, Browser, and Browser App modes.

## Project Structure

- **`res/dsl/`**: Source code for **LuduScript**, the C++ based DSL for generating game assets.
- **`res/app/`**: The frontend application built with **Vue 3**, **Vite**, and **TypeScript**.
- **`src/`**: The backend source code, including the game server, player management, and core logic.
- **`.games/`**: Directory containing game definitions and assets (e.g., Spyfall, Werewolf).
- **`app.py`**: The main entry point for the application.

## Prerequisites

- **Python 3.8+**
- **Node.js & npm** (for building the frontend)
- **CMake & C++ Compiler** (for building the DSL, optional if binaries are provided)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/LudusEngine.git
cd LudusEngine
```

### 2. Build the Frontend

Navigate to the frontend directory and install dependencies:

```bash
cd res/app
npm install
```

Build the frontend assets:

```bash
npm run build
```

This will generate static files in `res/app/static`, which are served by the Python backend.

### 3. Install Backend Dependencies

Return to the root directory and install the required Python packages:

```bash
cd ../..
pip install -r requirements.txt
```

### 4. Build the DSL (Optional)

If you need to modify or regenerate game assets using LuduScript:

```bash
cd res/dsl
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release
```

## Usage

Start the application using `app.py`. The engine supports different modes via environment variables.

### Default (Browser Mode)

```bash
python app.py
```

### Desktop Mode

To run as a standalone desktop application (requires `pywebview`):

```bash
# On Windows
set MODE=desktop
python app.py

# On Linux/macOS
export MODE=desktop
python app.py
```

### Debug Mode

To enable debug logging and features:

```bash
# On Windows
set DEBUG_APP=1
python app.py
```

## Creating Games

Games are located in the `.games/` directory. Each game typically consists of:

- `config.json`: Game configuration.
- `game.py`: Python script defining game logic.
- `prompt.json`: AI prompts (if applicable).

Use **LuduScript** in `res/dsl/` to generate complex card sets or assets for your games.

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.
