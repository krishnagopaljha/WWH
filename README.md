# WWH - Web Word Hunter

WWH is a customizable web crawler and wordlist generator that extracts words from a target website. It crawls a website at a specified depth, scrapes the content, and generates a list of words based on your requirements. It's ideal for generating wordlists for penetration testing, security assessments, or any use where you need a list of words from a website.

## Features

- Customizable spidering depth
- Extracts words with a minimum length
- Ability to limit the number of words in the generated list
- Support for multiple threads to speed up the process
- Includes a blacklist of common stop words that can be customized
- Saves the generated wordlist to a file
- Verbose output for debugging and progress tracking
- Interactive mode for easy configuration

## Requirements

- Python 3.x
- Required Python libraries:
  - `requests`
  - `beautifulsoup4`
  - `argparse`

You can install the necessary libraries using `pip`:

```bash
pip install -r requirements.txt
