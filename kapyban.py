import os
import json
import sys
from datetime import datetime
import dateparser
from prettytable import PrettyTable
import textwrap
import random
import string
from fuzzywuzzy import fuzz, process
from dateutil import parser
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from rich.panel import Panel
from rich.prompt import Prompt
import aiohttp
import asyncio

class KanbanBoard:
    def __init__(self, filename="kanban.json"):
        self.columns = {}
        self.filename = filename  # Store the filename
        self.output = []
        self.console = Console()  # Rich console instance
        self.remote = False
        self.api_endpoint = ''
        self.api_password = ''

    def reset_output(self, params):
        self.output = []

    def add_to_output(self, output, newline=1, bold = False):
        if bold:
            output = ('\n' * newline) + '[bold]' + output + '[/bold]'
        else:
            output = ('\n' * newline) + '-- ' + output
        self.output.append(output)

    def print_output(self, latest=True, last_n_entries=10):
        print_string = ''
        if latest and self.output:
            print_string += "-- " + self.output[-1]
        elif last_n_entries is not None and last_n_entries > 0:
            # Ensure we don't exceed the length of the output list
            start_index = max(0, len(self.output) - last_n_entries)
            for entry in self.output[start_index:]:
                print_string += entry
        else:
            for entry in self.output:
                print_string += "\n-- " + entry
        print_string = print_string + '\n'
        rprint(Panel(print_string, title='History'))

    def create_column(self, column_name):
        # Add a new column to the board
        column_name = ' '.join(column_name)
        if column_name not in self.columns:
            self.columns[column_name] = []
            self.add_to_output(f"Column '{column_name}' added.")
        else:
            self.add_to_output(f"Column '{column_name}' already exists.")

    def destroy_column(self, params):
        if not params:
            self.add_to_output("No column name provided.")
            return

        column_name = ' '.join(params)
        column_name = self.find_column_case_insensitive(column_name)

        if column_name is None:
            self.add_to_output(f"Column '{column_name}' does not exist.")
            return

        del self.columns[column_name]
        self.add_to_output(f"Column '{column_name}' removed.")

    def edit_task(self, params):
        if len(params) < 3:
            self.add_to_output("Insufficient parameters. Usage: edit [task_id] [property] [new_value]")
            return

        task_id, property_to_edit, new_value = params[0], params[1], ' '.join(params[2:])
        column_name, task = self.find_task_by_id(task_id)

        if task is None:
            self.add_to_output(f"Task with ID {task_id} not found.")
            return

        if property_to_edit not in ['description', 'deadline', 'due']:
            self.add_to_output(f"Cannot edit '{property_to_edit}'. Editable properties: description, deadline.")
            return

        if property_to_edit == 'deadline' or property_to_edit == 'due':
            self.set_task_deadline([task_id] + params[2:])
        else:
            task[property_to_edit] = new_value
            self.add_to_output(f"Task {task_id} updated: {property_to_edit} set to {new_value}.")

    def set_task_deadline(self, params):
        if len(params) < 2:
            self.add_to_output("Insufficient parameters. Usage: deadline [task_id] [deadline]")
            return

        task_id, new_deadline = params[0], ' '.join(params[1:])
        column_name, task = self.find_task_by_id(task_id)

        if task is None:
            self.add_to_output(f"Task with ID {task_id} not found.")
            return

        try:
            parsed_deadline = dateparser.parse(new_deadline)
            task['deadline'] = parsed_deadline.strftime("%Y-%m-%d %H:%M:%S")
            self.add_to_output(f"Deadline for task {task_id} set to {task['deadline']}.")
        except ValueError:
            self.add_to_output("Invalid deadline format. Please provide a valid date.")


    def generate_unique_id(self):
        id_length = 1
        while True:
            for _ in range(26 ** id_length):  # Iterate through all possible combinations for the current length
                id = ''.join(random.choices(string.ascii_lowercase, k=id_length))
                if not self.is_id_used(id):
                    return id
            id_length += 1  # Increase the length of the ID by 1

    def is_id_used(self, id):
        for column in self.columns.values():
            for task in column:
                if task['id'] == id:
                    return True
        return False



    def find_column_name(self, params):
        """
        Finds the best matching column name from the command parameters.
        Returns a tuple (best_match_column, best_match_index).
        If no match is found, returns (None, -1).
        """
        best_match_column = None
        best_match_index = -1
        for i, word in enumerate(params):
            if word.lower() == "to":
                potential_column_name = ' '.join(params[i+1:])
                best_match = self.find_best_match(potential_column_name, self.columns.keys())
                if best_match:
                    best_match_column = best_match
                    best_match_index = i
                    break

        if best_match_column is None:
            self.add_to_output("Column name not found or invalid.")
            return None, -1

        return best_match_column, best_match_index

    def add_task(self, params):
        if not params:
            self.add_to_output("No task description provided.")
            return

        # Use find_column_name to get the best match column and its index
        best_match_column, best_match_index = self.find_column_name(params)
        best_match_column = self.find_column_case_insensitive(best_match_column)

        if best_match_column is None:
            self.add_to_output("Column name not found or invalid.")
            return

        # Extract the task description from the parameters
        task_description = ' '.join(params[:best_match_index])
        if task_description:
            self.add_task_to_column(task_description, best_match_column)
        else:
            self.add_to_output("No task description provided.")

    def find_column_case_insensitive(self, column_name):
        column_name_lower = column_name.lower()
        matched_column = None

        # Find the matching column in a case-insensitive manner
        for col in self.columns.keys():
            if col.lower() == column_name_lower:
                return col

        if matched_column is None:
            self.add_to_output(f"Column '{column_name}' does not exist.")
            return

    def swap_columns(self, params):
        if len(params) < 2:
            self.add_to_output("Insufficient parameters. Usage: swap <column1> <column2>")
            return

        column1, column2 = None, None

        # Find the best matching first column name
        for i in range(1, len(params)):
            column1_try = ' '.join(params[:i])
            column1 = self.find_column_case_insensitive(column1_try)
            if column1 is not None:
                # Find the best matching second column name from the remaining parameters
                for j in range(i + 1, len(params) + 1):
                    column2_try = ' '.join(params[i:j])
                    column2 = self.find_column_case_insensitive(column2_try)
                    if column2 is not None:
                        break
                break

        # Swapping columns
        self.columns[column1], self.columns[column2] = self.columns[column2], self.columns[column1]
        self.add_to_output(f"Columns '{column1}' and '{column2}' have been swapped.")

    def rename_column(self, params):
        if len(params) < 2:
            self.add_to_output("Insufficient parameters. Usage: rename <old column name> <new column name>")
            return

        # Find the best matching old column name
        for i in range(1, len(params)):
            old_name_try = ' '.join(params[:i])
            old_name = self.find_column_case_insensitive(old_name_try)
            if old_name is not None:
                new_name = ' '.join(params[i:])
                break
        else:
            self.add_to_output("Old column name not found.")
            return

        if new_name in self.columns:
            self.add_to_output(f"A column with the name '{new_name}' already exists.")
            return

        self.columns[new_name] = self.columns.pop(old_name)
        self.add_to_output(f"Column '{old_name}' renamed to '{new_name}'.")

    def add_task_to_column(self, task_description, column_name):
        """
        Adds a task with the given description to the specified column.
        The column name comparison is case-insensitive.
        """
        # Convert column_name to lower case for case-insensitive comparison
        matched_column = self.find_column_case_insensitive(column_name)
        # Generate a unique ID for the new task
        task_id = self.generate_unique_id()
        # Get the current timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Create the task object
        task = {
                "id": task_id,
                "description": task_description,
                "timestamp": current_time,
                "priority": "low"  # Default priority
                }
        # Add the task to the matched column
        self.columns[matched_column].append(task)
        self.add_to_output(f"Task added to column '{matched_column}'.")

    def prioritize_task(self, params):
        if len(params) < 2:
            self.add_to_output("Insufficient parameters. Usage: prioritize <task_id> <priority level>")
            return

        task_id, priority_level = params[0], params[1].lower()
        if priority_level not in ["high", "medium", "low"]:
            self.add_to_output("Invalid priority level. Choose from high, medium, low.")
            return

        column_name, task = self.find_task_by_id(task_id)
        if task is None:
            self.add_to_output(f"Task with ID {task_id} not found.")
            return

        task['priority'] = priority_level
        self.add_to_output(f"Priority of task {task_id} set to {priority_level}.")

    def find_task_by_id(self, task_id):
        """
        Find a task by its ID and return the column name and the task.
        Returns (None, None) if the task is not found.
        """
        for column_name, tasks in self.columns.items():
            for task in tasks:
                if task['id'] == task_id:
                    return column_name, task
        return None, None 

    def move_task_by_id(self, params):
        if len(params) < 2:
            self.add_to_output("Insufficient parameters for moving a task.")
            return

        task_id = params[0]
        current_column, task_to_move = self.find_task_by_id(task_id)
        if not task_to_move:
            self.add_to_output(f"Task with ID {task_id} not found.")
            return

        # Join the remaining parameters to form the potential column name
        potential_column_name = ' '.join(params[1:])
        best_match_column = self.find_best_match(potential_column_name, self.columns.keys())

        # Check if best_match_column is None
        if best_match_column is None:
            self.add_to_output(f"Target column not found or invalid: {potential_column_name}")
            return

        best_match_column = self.find_column_case_insensitive(best_match_column)

        # Move the task to the best match column
        self.columns[current_column].remove(task_to_move)
        self.columns[best_match_column].append(task_to_move)
        self.add_to_output(f"Task {task_id} moved to {best_match_column}.")

    def remove_task_by_id(self, params):
        if not params:
            self.add_to_output("No task ID provided.")
            return

        task_id = params[0]
        current_column, task_to_remove = self.find_task_by_id(task_id)

        if not task_to_remove:
            self.add_to_output(f"Task with ID {task_id} not found.")
            return

        self.columns[current_column].remove(task_to_remove)
        self.add_to_output(f"Task {task_id} removed from {current_column}.")

    def find_best_match(self, target, potential_matches, threshold=90):
        """
        Find the best fuzzy match for a target string from a list of potential matches.
        Returns the best match if the similarity is above the threshold, otherwise None.
        This comparison is case-insensitive.
        """
        target = target.lower()
        potential_matches = [match.lower() for match in potential_matches]
        best_match, highest_similarity = process.extractOne(target, potential_matches, scorer=fuzz.ratio)

        return best_match if highest_similarity >= threshold else None

    def remove_task(self, column_index):
        # Display tasks in the selected column and remove a chosen task
        column_names = list(self.columns.keys())
        if 0 <= column_index < len(column_names):
            column_name = column_names[column_index]
            tasks = self.columns[column_name]

            if tasks:
                self.add_to_output(f"Tasks in '{column_name}':")
                for i, task in enumerate(tasks, start=1):
                    self.add_to_output(f"{i}. {task['description']} (Added: {task['timestamp']})")

                task_index = int(input("Enter the task number to remove: ")) - 1
                if 0 <= task_index < len(tasks):
                    del tasks[task_index]
                    self.add_to_output(f"Task removed from '{column_name}'.")
                else:
                    self.add_to_output("Invalid task index.")
            else:
                self.add_to_output(f"No tasks in '{column_name}'.")
        else:
            self.add_to_output("Invalid column index.")

    def remove_column(self, column_index):
        # Remove a column from the board
        column_names = list(self.columns.keys())
        if 0 <= column_index < len(column_names):
            column_name = column_names[column_index]
            del self.columns[column_name]
            self.add_to_output(f"Column '{column_name}' destroyed.")
        else:
            self.add_to_output("Invalid column index.")

    def format_time_difference(self, deadline):
        now = datetime.now()
        deadline = datetime.strptime(deadline, "%Y-%m-%d %H:%M:%S")
        diff = deadline - now

        days, seconds = diff.days, diff.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        if days < 0 or (days == 0 and hours <= 0 and minutes <= 0):
            return "[red]Past due[/red]"
        elif 0 <= days < 3:  # Less than 3 days
            if days < 1:  # Less than 24 hours
                return f"Due in [red]{hours} hours, {minutes} minutes[/red]"
            else:
                return f"Due in [yellow]{days} days, {hours} hours[/yellow]"
        else:
            return f"Due in {days} days, {hours} hours"

    def show_board(self, should_print=True):
        table = Table(show_header=True, header_style="bold magenta", expand=True)
        for col_name in self.columns.keys():
            table.add_column(col_name, justify="left", style="dim")

        # Sort tasks first by priority and then by timestamp
        sorted_columns = {
            col: sorted(tasks, key=lambda x: (x.get('priority', 'low'), x['timestamp']))
            for col, tasks in self.columns.items()
        }

        max_tasks = max((len(tasks) for tasks in sorted_columns.values()), default=0)

        for i in range(max_tasks):
            row = []
            for tasks in sorted_columns.values():
                if i < len(tasks):
                    task = tasks[i]
                    # Apply color formatting based on priority
                    priority = task.get('priority', 'low')
                    if priority == 'high':
                        priority_formatted = "[red]high[/red]"
                    elif priority == 'medium':
                        priority_formatted = "[yellow]medium[/yellow]"
                    else:
                        priority_formatted = "low"

                    # Check if task has a deadline and format it
                    deadline_str = task.get('deadline')
                    if deadline_str:
                        formatted_deadline = '\n      ' + self.format_time_difference(deadline_str)
                    else:
                        formatted_deadline = ""

                    task_info = f"[dim]\[{task['id']}][/dim] [bold]{task['description']}[/bold]{formatted_deadline}\n      Priority: {priority_formatted}"

                    row.append(task_info)

                else:
                    row.append("")
            table.add_row(*row)

        if should_print:
            self.console.print(table)
        else:
            return table

    def generate_html_table(self):
        # Prepare data for the HTML table
        headers = list(self.columns.keys())
        max_tasks = max((len(tasks) for tasks in self.columns.values()), default=0)
        
        html_table = "<h1>" + self.filename + "</h1>"
        # Start the HTML table
        html_table += "<table border='1'><tr>"

        # Add table headers
        for header in headers:
            html_table += f"<th>{header}</th>"
        html_table += "</tr>"

        # Add table rows
        for i in range(max_tasks):
            html_table += "<tr>"
            for column in headers:
                tasks = self.columns[column]
                if i < len(tasks):
                    task = tasks[i]
                    # Format each task and replace newlines with <br>
                    task_str = "<br>".join([f"{key}: {self.nl2br(value)}" for key, value in task.items()])
                    html_table += f"<td>{task_str}</td>"
                else:
                    html_table += "<td></td>"
            html_table += "</tr>"

        # Close the HTML table
        html_table += "</table>"

        return html_table

    def nl2br(self, value):
        if isinstance(value, str):
            return value.replace('\n', '<br>')
        return self.decode_unicode_escapes(str(value))

    def decode_unicode_escapes(self, s):
        return s.encode('latin1').decode('unicode_escape')

    async def save_to_json(self, params='', add_output=True):
        # Save the current state of the Kanban board to the specified JSON file
        board_data = {
                "data": self.columns,
                "remote": self.remote,
                "board_visual": self.generate_html_table()
                }

        filename = self.filename
        if not filename.lower().endswith('.json'):
            filename += '.json'

        # Convert board_data to a JSON string
        json_string = self.decode_unicode_escapes(json.dumps(board_data, indent=4))

        # Write the JSON string to a file
        with open(filename, 'w') as file:
            file.write(json_string)

        if self.api_endpoint:
            url = f"{self.api_endpoint}/upload/{filename}"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data={'password': self.api_password}, files={'file': open(filename, 'rb')}) as response:
                    if response.status == 200:
                        self.add_to_output("File successfully uploaded")
                    else:
                        self.add_to_output(f"Failed to upload file: {await response.text()}")


    def load_from_json(self, filename="kanban.json"):
        # Load the Kanban board from a JSON file
        if not filename.lower().endswith('.json'):
            filename += '.json'
        try:
            with open(filename, 'r') as file:
                loaded_data = json.load(file)
                self.columns = loaded_data.get("data", {})  # Default to empty dict if "data" key is not found
                self.add_to_output(f"Kanban board loaded from {filename}.")
        except FileNotFoundError:
            self.add_to_output(f"No existing {filename} found. Starting with a new board.")


    def show_help(self, params = ''):
        help_message = """
        Kanban Board Command List:
        ==========================

        General:
        - help: Displays this help message.
        - save: Saves the current state of the board to .json.
        - exit: Exits the application.

        Board Management:
        - create <column name>: Creates a new column.
        - destroy <column name>: Deletes a specified column.
        - rename <old column name> <new column name>: Renames a column.
        - swap <old column> <new column>: Swaps the contents of two columns.

        Task Management:
        - add <task description> to <column name>: Adds a new task.
        - move <task id> <column name>: Moves a task to a different column.
        - remove <task id>: Removes a specified task.
        - edit <task id> <property> <new value>: Edits a task's property.
        - deadline <task id> <deadline>: Sets a deadline for a task. You can use natural language such as "deadline z tomorrow at 7pm".
        - priority <task id> <priority level>: Sets a task's priority. Priority levels are "low," "medium," "high," with "low" being default.
        
        Output:
        - clear: Clears the output history.
        """
        self.add_to_output(help_message)

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

async def parse_and_execute_command(kanban, command_str):
    commands = {
            "create": kanban.create_column,
            "c": kanban.create_column,
            "destroy": kanban.destroy_column,
            "deadline": kanban.set_task_deadline,
            "due": kanban.set_task_deadline,
            "add": kanban.add_task,
            "move": kanban.move_task_by_id,
            "mv": kanban.move_task_by_id,
            "remove": kanban.remove_task_by_id,
            "rm": kanban.remove_task_by_id,
            "priority": kanban.prioritize_task,
            "pr": kanban.prioritize_task,
            "rename": kanban.rename_column,
            "clear": kanban.reset_output,
            "cl": kanban.reset_output,
            "save": kanban.save_to_json,
            "exit": sys.exit,
            "help": kanban.show_help,
            "swap": kanban.swap_columns,
            "edit": kanban.edit_task
            }

    words = command_str.split()
    if words:
        cmd = kanban.find_best_match(words[0], commands.keys())
        if cmd:
            params = words[1:]
            kanban.add_to_output(f"{command_str}", 1, True)
            commands[cmd](params)  # Return the output of the command
            await kanban.save_to_json('', True)
        else:
            return f"Command not recognized: {words[0]}"
    else:
        return "No command entered."

async def main():
    kanban = KanbanBoard()
    clear_screen()  # Clear the screen after command execution

    # Check if a filename is provided as a command-line argument
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        kanban.load_from_json(filename)
        kanban.filename = filename
        kanban.show_board()
        kanban.print_output(False, 2)  # Print the output of the command

    else:
        # Prompt the user to enter a filename if not provided
        filename_input = Prompt.ask("Enter a name for your new Kanban board: ", default="Kanban")
        filename = filename_input if filename_input.lower().endswith('.json') else filename_input + '.json'

        if os.path.isfile(filename):
            kanban.load_from_json(filename)
            kanban.show_board()  # Show the board
        else:
            kanban.filename = filename

    while True:
        command_str = Prompt.ask("\nEnter command")
        await parse_and_execute_command(kanban, command_str)
        clear_screen()  # Clear the screen after command execution
        kanban.show_board()  # Show the board
        kanban.print_output(False, 10)  # Print the output of the command

if __name__ == "__main__":
    asyncio.run(main())
