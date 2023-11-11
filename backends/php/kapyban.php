<?php

// KapybanFileManager class handles file upload, download, and view functionalities.
class KapybanFileManager {
	private $directory;       // Directory to store the JSON files.
	private $passwords;       // Array to store passwords loaded from YAML.
	private $fallback_password; // Fallback password for file access.

	// Constructor initializes the directory and loads passwords from YAML.
	public function __construct() {
		$this->directory = __DIR__ . '/'; // Sets the directory to the current script's directory.
		$this->loadPasswords();           // Calls the method to load passwords from YAML file.
	}

	// nanoYAML is a simple YAML parser for the specific structure of the passwords file.
	private function nanoYAML($file_path) {
		$lines = file($file_path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
		$result = [];
		$current_key = '';

		foreach ($lines as $line) {
			if (strpos($line, ':') !== false) {
				list($key, $value) = explode(':', $line, 2);
				$key = trim($key);
				$value = trim($value);

				// Handles nested structure in YAML.
				if ($value === '') {
					$current_key = $key;
					$result[$key] = [];
				} else {
					if ($current_key === '') {
						// For top-level keys.
						$result[$key] = trim($value, ' "');
					} else {
						// For nested keys under a top-level key.
						$result[$current_key][$key] = trim($value, ' "');
					}
				}
			}
		}

		return $result; // Returns the parsed YAML content as an array.
	}

	// Loads passwords from the YAML file.
	private function loadPasswords() {
		$yaml_content = $this->nanoYAML($this->directory . 'passwords.yaml');
		if (empty($yaml_content)) {
			throw new Exception("Unable to read or parse passwords file");
		}

		// Sets passwords and fallback password from the YAML content.
		$this->passwords = $yaml_content['passwords'] ?? [];
		$this->fallback_password = $yaml_content['fallback_password'] ?? null;
	}

	// Validates the password for a given filename.
	private function validatePassword($file_name, $password) {
		$expected_password = $this->passwords[$file_name] ?? $this->fallback_password;
		if ($expected_password !== $password) {
			throw new Exception("Invalid or missing password");
		}
	}

	// Handles file upload.
	public function uploadFile($file_name) {
		// Checks if the request method is POST.
		if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
			throw new Exception("Invalid request method");
		}

		// Validates the presence of a password.
		if (!isset($_POST['password'])) {
			throw new Exception("No password provided");
		}

		// Sanitizes and validates the password.
		$password = filter_var($_POST['password'], FILTER_SANITIZE_STRING);
		$this->validatePassword($file_name, $password);

		// Checks if a file was uploaded.
		if (!isset($_FILES['file'])) {
			throw new Exception("No file uploaded");
		}

		// Further validation for the uploaded file.
		$uploaded_file = $_FILES['file'];
		$file_type = mime_content_type($uploaded_file['tmp_name']);

		if ($file_type !== 'application/json') {
			throw new Exception("Invalid file type");
		}

		if ($uploaded_file['size'] > 2097152) {
			throw new Exception("File size exceeds limit");
		}

		// Moves the uploaded file to the specified directory.
		if (!move_uploaded_file($uploaded_file['tmp_name'], $this->directory . $file_name . '.json')) {
			throw new Exception("Failed to upload file");
		}

		return true;
	}

	// Handles file download.
	public function downloadFile($file_name) {
		$file_path = $this->directory . $file_name . '.json';

		// Checks if the file exists.
		if (!file_exists($file_path)) {
			throw new Exception("File not found");
		}

		// Sets headers to initiate a file download.
		header('Content-Type: application/json');
		header('Content-Disposition: attachment; filename="' . basename($file_path) . '"');
		readfile($file_path);
		return true;
	}

	// Handles viewing of the file content as an HTML document.
	public function viewFile($file_name) {
		$file_path = $this->directory . $file_name . '.json';

		// Checks if the file exists.
		if (!file_exists($file_path)) {
			throw new Exception("File not found");
		}

		// Reads and parses the JSON file.
		$json_content = json_decode(file_get_contents($file_path), true);

		// Checks if the 'visual_body' key exists in the JSON.
		if (!isset($json_content['visual_body'])) {
			throw new Exception("Invalid JSON structure");
		}

		// Outputs the HTML content stored in 'visual_body' within an HTML document.
		echo '<!DOCTYPE html>';
		echo '<html lang="en">';
		echo '<head>';
		echo '<meta charset="UTF-8">';
		echo '<meta name="viewport" content="width=device-width, initial-scale=1.0">';
		echo '<title>Kapyban Kanban Board</title>';
		echo '</head>';
		echo '<body>';
		echo htmlspecialchars($json_content['visual_body']);
		echo '</body>';
		echo '</html>';
		return true;
	}
}

// Routing logic
$file_manager = new KapybanFileManager();
$path = isset($_GET['path']) ? $_GET['path'] : '';
$segments = explode('/', filter_var($path, FILTER_SANITIZE_STRING));
$route = $segments[0] ?? '';
$file_name = basename($segments[1] ?? '');

// Executes the appropriate method based on the route.
try {
	switch ($route) {
	case 'upload':
		$file_manager->uploadFile($file_name);
		break;
	case 'download':
		$file_manager->downloadFile($file_name);
		break;
	case 'view':
		$file_manager->viewFile($file_name);
		break;
	default:
		// Sends a 404 response for invalid routes.
		header("HTTP/1.1 404 Not Found");
		exit('Invalid route');
	}
} catch (Exception $e) {
	// Handles exceptions and sends a 500 internal server error response.
	header("HTTP/1.1 500 Internal Server Error");
	exit('Error: ' . $e->getMessage());
}

