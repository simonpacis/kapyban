# Kapyban: An AI-Generated Python-Based Kanban Board

Disclaimer: This project has been 95% coded by AI. Including this readme.

## Description

Kapyban is a Python application designed to manage tasks using a Kanban board approach. It provides a simple, text-based interface to create, edit, move, and prioritize tasks organized in columns, mimicking a traditional Kanban board. This tool is ideal for personal task management or small team projects.

## Features

- **Task Management:** Add, edit, remove, and move tasks across different columns.
- **Column Operations:** Create, rename, and destroy columns to customize your board.
- **Prioritization:** Set priorities for tasks (high, medium, low).
- **Deadlines:** Assign deadlines to tasks using natural language.
- **Data Persistence:** Save and load the board state as a JSON file.
- **Command-line Interface:** Easy-to-use commands for managing tasks and columns. No menus in the shape of numbered lists.

## Installation

To use Kapyban, ensure you have Python installed on your system. Then, install the required dependencies:

```bash
pip3 install dateparser prettytable fuzzywuzzy python-dateutil tabulate rich
```

## Usage

1. **Starting Kapyban:** Run the script to start the application. Optionally, pass a `.json` filename as an argument to load an existing board.

   ```bash
   python3 kapyban.py [filename.json]
   ```

2. **Command List:**
   - General Commands: `help`, `save`, `exit`
   - Board Management: `create <column name>`, `destroy <column name>`, `rename <old column name> <new column name>`
   - Task Management: `add <task description> to <column name>`, `move <task id> <column name>`, `remove <task id>`, `edit <task id> <property> <new value>`, `deadline <task id> <deadline>`, `priority <task id> <priority level>`
   - Output Control: `clear`

3. **Interacting with Kapyban:**
   - Enter commands at the prompt to manage tasks and columns.
   - Use `help` for guidance on command usage.

## Contribution

Contributions to Kapyban are welcome! If you have suggestions or improvements, feel free to fork the repository and submit a pull request.

## License

Kapyban is released under [MIT License](https://opensource.org/licenses/MIT). 
