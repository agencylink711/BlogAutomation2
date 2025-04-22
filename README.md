# BlogAutomation2

Automated blog writing tool that uses Claude.ai and Playwright to generate real estate content.

## Project Overview

This project automates the process of:

1. Taking keywords from a list
2. Accessing Claude.ai through Playwright
3. Submitting a prompt template with the keyword
4. Waiting for Claude to generate a response
5. Saving the generated content as Markdown files

## Setup

### Prerequisites

- Python 3.8+
- pip
- Chrome browser (recommended for best compatibility)

### Installation

1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
4. Install Playwright browsers:
   ```
   playwright install chromium
   ```

## Usage

1. Ensure you have keywords in the `content/keywords/keywords.txt` file (one per line)
2. Run the script:
   ```
   python src/main.py
   ```
3. When the browser opens, you'll need to complete Google login manually the first time
4. The script will automatically:
   - Handle cookie acceptance
   - Submit your prompt with the keyword
   - Wait for Claude to respond
   - Save the response as markdown files
   - Track processed keywords to avoid duplicates

## Project Structure

```
BlogAutomation2/
├── content/
│   ├── completed/        # Generated blog posts stored here
│   ├── keywords/         # Keywords to process
│   │   ├── keywords.txt  # List of keywords, one per line
│   │   └── processed_keywords.txt  # Tracks completed keywords
│   └── prompts/          # Prompt templates
│       └── prompt_template.txt
├── src/
│   ├── claude_client.py  # Claude.ai Playwright automation
│   ├── file_manager.py   # File operations
│   ├── keyword_manager.py # Keyword handling
│   └── main.py           # Main script to run
├── tests/                # Test scripts
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Notes

- The automation uses a persistent browser context to maintain login state
- First-time use requires manual Google login
- Claude.ai web interface may change over time, requiring updates to the selectors in `claude_client.py`
- To reprocess all keywords, delete the `processed_keywords.txt` file
- Generated content is saved in markdown format with proper formatting

## Future Enhancements

- PDF file generation support (planned)
- Additional output formats
- Enhanced error recovery
- Progress tracking and reporting
