const express = require('express');
const fileUpload = require('express-fileupload');
const fs = require('fs');
const path = require('path');
const sanitizeHtml = require('sanitize-html');
const yaml = require('js-yaml');

const app = express();
const port = 80;

// Directory to store files
const filesDir = './boards';

// Ensure filesDir exists
if (!fs.existsSync(filesDir)) {
    fs.mkdirSync(filesDir, { recursive: true });
}

// Middleware
app.use(fileUpload());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Function to load passwords from YAML
function loadPasswords() {
    try {
        let fileContents = fs.readFileSync('./passwords.yaml', 'utf8');
        return yaml.load(fileContents);
    } catch (e) {
        console.error("Error loading passwords:", e);
        return null;
    }
}

// Upload endpoint
app.post('/upload/:filename', (req, res) => {
		const passwordsConfig = loadPasswords();

    if (!passwordsConfig || typeof passwordsConfig.file_passwords !== 'object') {
        return res.status(500).send('Internal server error: Unable to load passwords configuration');
    }

    const filename = req.params.filename;
    const providedPassword = req.body.password;
    const fileSpecificPassword = passwordsConfig.file_passwords.hasOwnProperty(filename) ? passwordsConfig.passwords[filename] : null;
    const fallbackPassword = passwordsConfig.fallback_password;

    if (providedPassword !== fileSpecificPassword && providedPassword !== fallbackPassword) {
        return res.status(403).send('Access denied');
    }

    if (!req.files || !req.files.file) {
        return res.status(400).send('No file uploaded');
    }

    req.files.file.mv(path.join(filesDir, `${filename}.json`), err => {
        if (err) return res.status(500).send(err);
        res.send('File uploaded successfully');
    });
});

// Download endpoint
app.get('/download/:filename', (req, res) => {
    let filename = req.params.filename;
    res.download(path.join(filesDir, `${filename}.json`), `${filename}.json`);
});

// View endpoint
app.get('/:filename', (req, res) => {
    let filename = req.params.filename;
    fs.readFile(path.join(filesDir, `${filename}.json`), 'utf8', (err, data) => {
        if (err) return res.status(500).send(err);

        try {
            let jsonData = JSON.parse(data);
            let visualBody = jsonData.board_visual;

            if (!visualBody) {
                return res.status(404).send('Visual body not found');
            }

            let cleanVisualBody = sanitizeHtml(visualBody, {
                allowedTags: ['br', 'h1', 'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td'],
                allowedAttributes: {
										'table': ['border'],
                    'tr': ['rowspan', 'colspan'],
                    'th': ['rowspan', 'colspan', 'scope'],
                    'td': ['rowspan', 'colspan']
                },
                selfClosing: ['br', 'hr'],
                allowedStyles: {}
            });

            res.writeHead(200, { 'Content-Type': 'text/html' });
            res.write(`<html><body>${cleanVisualBody}</body></html>`);
            res.end();
        } catch (error) {
            res.status(500).send('Error parsing JSON');
        }
    });
});

// Start server
app.listen(port, () => {
    console.log(`Server running on http://localhost:${port}`);
});

