# Document Converter Web App

This Flask-based web application allows users to upload PDF files, convert them to DOCX format, and manage their files efficiently. The conversion process is handled asynchronously using Flask-SocketIO for real-time updates.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Folder Structure](#folder-structure)
- [Dependencies](#dependencies)
- [License](#license)

## Features

- Upload PDF files to the server.
- Convert PDF files to DOCX format.
- Real-time flash messages using Flask-SocketIO.
- Download converted files.
- Delete unwanted files.

## Installation

Follow these steps to set up the Document Converter Web App:

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/document-converter.git
    ```

2. Navigate to the project directory:

    ```bash
    cd document-converter
    ```

3. Create a virtual environment:

    ```bash
    python -m venv venv
    ```

4. Activate the virtual environment:

    - On Windows:

        ```bash
        venv\Scripts\activate
        ```

    - On macOS and Linux:

        ```bash
        source venv/bin/activate
        ```

5. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

6. Set up your Flask application:

    - On Windows:

        ```bash
        set FLASK_APP=app.py
        ```

    - On macOS and Linux:

        ```bash
        export FLASK_APP=app.py
        ```

    Optionally, set the Flask environment to development:

    ```bash
    set FLASK_ENV=development  # Windows
    export FLASK_ENV=development  # macOS/Linux
    ```

7. Initialize the Flask application:

    ```bash
    flask run
    ```

8. Open your web browser and go to [http://127.0.0.1:5000/](http://127.0.0.1:5000/) to access the Document Converter Web App.

## Usage

- **Upload Files:**
  1. Click on the "Choose file" button to select a PDF file.
  2. Click "Add File" to upload the selected file.

- **Convert Files:**
  1. Select the desired output format (e.g., DOCX) from the dropdown menu.
  2. Click "Convert" to initiate the conversion process.

- **Download Converted Files:**
  1. Once a file is converted, a list of converted files will be available.
  2. Click "Download" next to the desired converted file.

- **Delete Files:**
  1. Delete uploaded or converted files by clicking the "Delete" button.

## Folder Structure

```plaintext
document-converter/
│
├── files/
│   ├── uploads/
│   └── outputs/
│
├── static/
│   └── (static files, e.g., CSS, JavaScript)
│
├── templates/
│   ├── about.html
│   └── index.html
│
├── venv/  (virtual environment)
│
├── app.py  (Flask application)
├── requirements.txt
└── README.md
```

## Dependencies

- Flask
- Flask-SocketIO
- pdf2docx
- gevent
- python-dotenv
- Werkzeug

Install the dependencies using the following command:

```bash
pip install -r requirements.txt
```

## License

This project is licensed under the [MIT License](LICENSE).

Feel free to contribute and make the Document Converter Web App even better!