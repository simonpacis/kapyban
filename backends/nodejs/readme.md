
# Kapyban Node.js Backend

This Node.js server script provides backend support for the `kapyban` Python CLI kanban application. It handles upload, download, and viewing of the kapyban boards, ensuring secure file handling and access control.

## Features

- **Upload**: Securely upload kanban board JSON files with password protection.
- **Download**: Retrieve kanban board JSON files.
- **View**: Display the visual content of the kanban boards as HTML.

## Installation

### Prerequisites

- Node.js and npm (Node Package Manager)
- Python environment for `kapyban`

### Steps

1. **Clone the Repository**

   ```bash
   git clone [repository-url]
   cd [repository-name]
   ```

2. **Install Dependencies**

   Inside the repository directory, run:

   ```bash
   npm install
   ```

3. **Configuration**

   - Create a `passwords.yaml` file in the root directory with the following structure:

     ```yaml
     fallback_password: "your_default_password"
     passwords:
       board1.json: "password1"
       board2.json: "password2"
     ```

   - Modify the `fallback_password` and add filename-specific passwords as needed.

4. **File Directory**

   The script automatically creates a directory named `files` to store the JSON files. Ensure that the server has the necessary permissions to create and modify this directory.

## Usage

### Starting the Server

Run the server using:

```bash
node server.js
```

The server will start on `http://localhost:80`. You can change the port in the server script if needed.

### Integrating with Kapyban

Configure `kapyban` to interact with this server for uploading and downloading kanban board JSON files.

- **Upload**: Use the `/upload/:filename` endpoint to upload files.
- **Download**: Use the `/download/:filename` endpoint to download files.
- **View**: Access `/:filename` to view the visual body of the kanban board.

Ensure that the filenames used in `kapyban` match those specified in `passwords.yaml` for password-protected operations.

## Security

This script includes basic security features like password protection and input sanitization. For production use, it is recommended to enhance security measures according to your specific deployment environment.