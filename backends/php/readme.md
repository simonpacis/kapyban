# README - Kapyban Backend Script

This PHP script is designed to integrate with kapyban, a Python CLI kanban application. It facilitates the uploading, downloading, and HTML-based viewing of kanban boards, with password protection for each file derived from a YAML configuration.

## Features

- **Upload Route (`/upload/$filename`)**: Securely uploads JSON files with unique passwords.
- **Download Route (`/download/$filename`)**: Enables the downloading of specified JSON files.
- **View Route (`/$filename`)**: Displays the HTML content of `visual_body` from JSON files within a full HTML document.

## Setup

### Prerequisites

- Apache Web Server with mod_rewrite enabled.
- PHP 7.x or higher.

### Installation Steps

1. **Clone or Download the Repository**
   - Obtain the script files from the provided repository URL.

2. **Deploy the Script**
   - Place `kapyban.php` and `.htaccess` in the desired directory on your Apache server.

3. **Configure Apache**
   - Make sure that the `.htaccess` overrides are allowed in your server configuration.

4. **Set Directory Permissions**
   - The directory containing the script should be writable by the server:
     ```bash
     chmod 755 /path/to/directory
     ```

5. **Create the Passwords File**
   - Name the file `passwords.yaml` and place it in the same directory as the script.
   - Define passwords for individual files and a fallback password.

     ```yaml
     fallback_password: "your_default_password"
     passwords:
       board1.json: "password1"
       board2.json: "password2"
     ```


### File Structure

- `kapyban.php`: The main script handling the routes and functionalities.
- `.htaccess`: Apache configuration file for URL rewriting.
- `passwords.yaml`: YAML file containing the password configurations.


## Security and Limitations

- The script sanitizes inputs to mitigate common web vulnerabilities.
- Passwords are managed securely via the `passwords.yaml` file.
- The included YAML parser (nanoYAML) is designed for simple YAML structures and does not support most YAML features.

## Contributions

Feel free to contribute to this project by submitting pull requests or issues. Please adhere to the existing coding style and functionality.
