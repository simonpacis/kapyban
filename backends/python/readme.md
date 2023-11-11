# Kapyban Python Backend

## Overview

This script serves as a server-side component for kapyban, a Python CLI kanban application. It handles HTTP requests to upload, download, and viewing of the kapyban boards.

## Features

- **File Upload**: Securely upload JSON files representing kanban boards.
- **File Download**: Download existing kanban board files.
- **File Viewing**: View the contents of a kanban board in a web browser.

## Prerequisites

- Python 3.x
- Flask
- PyYAML

## Installation

1. **Clone/Download the Repository**

   Clone this repository or download the script and YAML file to your local machine.

2. **Install Dependencies**

   Open a terminal and run the following command to install required Python packages:

   ```bash
   pip install flask pyyaml
   ```

## Configuration

1. **YAML File**

   Create a `passwords.yaml` file in the same directory as the script with the following structure:

   ```yaml
   fallback_password: [your_fallback_password]
   file_passwords:
     [filename1.json]: [password1]
     [filename2.json]: [password2]
   ```

   Replace `[your_fallback_password]`, `[filename1.json]`, `[password1]`, etc., with your actual passwords and filenames.

2. **Script Settings**

   You can configure the upload directory and other settings directly in the script.

## Running the Script

Run the script using Python:

```bash
python kapyban_server.py
```

The server will start, and you can interact with it using HTTP requests on the configured port.

## Usage

### Uploading a File

Send a POST request to `/upload/[filename]` with the JSON file and password as form-data.

### Downloading a File

Send a GET request to `/download/[filename]` to download the specified file.

### Viewing a File

Send a GET request to `/[filename]` to view the contents of the file in a web browser.

## Security Notes

This script includes basic password authentication. For production use, consider enhancing security measures.

## Contributing

Contributions to this script are welcome. Please fork the repository and submit a pull request with your changes.