import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from collections import defaultdict
import time
import threading
from queue import Queue
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import argparse
import os


# Define logo
logo = """
 __          __  _ __          __           _ _    _             _            
 \ \        / / | |\ \        / /          | | |  | |           | |           
  \ \  /\  / /__| |_\ \  /\  / /__  _ __ __| | |__| |_   _ _ __ | |_ ___ _ __ 
   \ \/  \/ / _ \ '_ \ \/  \/ / _ \| '__/ _` |  __  | | | | '_ \| __/ _ \ '__|
    \  /\  /  __/ |_) \  /\  / (_) | | | (_| | |  | | |_| | | | | ||  __/ |   
     \/  \/ \___|_.__/ \/  \/ \___/|_|  \__,_|_|  |_|\__,_|_| |_|\__\___|_|   
"""

# Print the logo when the script starts
print(logo)


class WWH:
    def __init__(self, url, depth=2, min_word_length=5, max_words=None, verbose=False, threads=1):
        self.url = url
        self.depth = depth
        self.min_word_length = min_word_length
        self.max_words = max_words
        self.verbose = verbose
        self.threads = threads
        self.visited = set()
        self.word_count = defaultdict(int)
        self.stop_words = self.load_stop_words()
        self.domain = urlparse(self.url).netloc
        self.queue = Queue()

    def load_stop_words(self):
        """Load a list of common stop words to exclude."""
        stop_words = set()
        try:
            with open("blacklist.txt", "r") as f:
                stop_words = set(line.strip() for line in f)
        except FileNotFoundError:
            print("\033[1;31mStop words file not found. Using default stop words.\033[1;m")
            stop_words = set(["the", "and", "or", "is", "it", "in", "to", "of", "for", "on", "with", "as", "at", "by"])
        return stop_words

    def fetch_page(self, url):
        """Fetch the content of a webpage with retries and error handling."""
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            if self.verbose:
                print(f"\033[1;33mError fetching {url}: {e}\033[1;m")
        return None

    def extract_words(self, text):
        """Extract relevant words from text using regex and exclude stop words."""
        words = re.findall(r'\b\w{%d,}\b' % self.min_word_length, text.lower())
        words = [word for word in words if word not in self.stop_words]
        return words

    def process_url(self):
        """Worker function to process URLs from the queue."""
        while not self.queue.empty():
            url, current_depth = self.queue.get()
            if url in self.visited or current_depth > self.depth:
                self.queue.task_done()
                continue

            self.visited.add(url)
            if self.verbose:
                print(f"\033[1;34mSpidering: {url} (Depth: {current_depth})\033[1;m")

            html = self.fetch_page(url)
            if not html:
                self.queue.task_done()
                continue

            try:
                soup = BeautifulSoup(html, 'html.parser')
            except Exception as e:
                if self.verbose:
                    print(f"\033[1;33mError parsing HTML for {url}: {e}\033[1;m")
                self.queue.task_done()
                continue

            # Extract words from the page
            text = soup.get_text()
            words = self.extract_words(text)
            for word in words:
                self.word_count[word] += 1

            # Add new links to the queue
            for link in soup.find_all('a', href=True):
                next_url = urljoin(url, link['href'])
                parsed_url = urlparse(next_url)
                if parsed_url.netloc == self.domain and next_url not in self.visited:
                    self.queue.put((next_url, current_depth + 1))

            self.queue.task_done()

    def spider(self):
        """Start the spidering process using threads."""
        self.queue.put((self.url, 1))

        threads = []
        for _ in range(self.threads):
            thread = threading.Thread(target=self.process_url)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    def generate_wordlist(self):
        """Generate and return the wordlist."""
        self.spider()
        sorted_words = sorted(self.word_count.items(), key=lambda x: x[1], reverse=True)
        if self.max_words:
            sorted_words = sorted_words[:self.max_words]
        return [word for word, count in sorted_words]

    def save_wordlist(self, filename):
        """Save the wordlist to a file."""
        wordlist = self.generate_wordlist()
        with open(filename, 'w') as f:
            for word in wordlist:
                f.write(f"{word}\n")
        print(
            f"[+] Saving Wordlist to \033[1;32m{filename}\033[1;m, "
            f"counting \033[1;32m{len(wordlist)} words.\033[1;m"
        )


def format_url(url):
    """Ensure the URL is properly formatted."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"http://{url}"
    if not url.endswith("/"):
        url += "/"
    return url


# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WWH - Custom Word List Generator")
    parser.add_argument("url", nargs="?", help="Target URL (e.g., http://example.com)")
    parser.add_argument("-d", "--depth", type=int, default=2, help="Spidering depth (default is 2)")
    parser.add_argument("-m", "--min-word-length", type=int, default=5, help="Minimum word length (default is 5)")
    parser.add_argument("-M", "--max-words", type=int, help="Maximum number of words to include")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
    parser.add_argument("-t", "--threads", type=int, default=1, help="Number of threads to use (default is 1)")
    parser.add_argument("-o", "--output", type=str, default="wordlist.txt", help="Output filename (default is wordlist.txt)")
    parser.add_argument("-i", "--interactive", action="store_true", help="Enable interactive mode")

    args = parser.parse_args()

    # Interactive mode
    if args.interactive or not args.url:
        print("\033[1;36m=== WWH - Interactive Mode ===\033[1;m")
        args.url = input("\033[1;33mEnter the target URL (e.g., testphp.vulnweb.com): \033[1;m").strip()
        args.url = format_url(args.url)
        args.depth = int(input("\033[1;33mEnter the spidering depth (default is 2): \033[1;m") or 2)
        args.min_word_length = int(input("\033[1;33mEnter the minimum word length (default is 5): \033[1;m") or 5)
        max_words = input("\033[1;33mEnter the maximum number of words to include (leave blank for no limit): \033[1;m").strip()
        args.max_words = int(max_words) if max_words else None
        args.threads = int(input("\033[1;33mEnter the number of threads to use (default is 1): \033[1;m") or 1)
        args.verbose = input("\033[1;33mEnable verbose mode? (y/n): \033[1;m").strip().lower() == "y"
        args.output = input("\033[1;33mEnter the output filename (default is wordlist.txt): \033[1;m").strip() or "wordlist.txt"

    # Ensure the URL is formatted properly
    if args.url:
        args.url = format_url(args.url)

    WWH = WWH(
        url=args.url,
        depth=args.depth,
        min_word_length=args.min_word_length,
        max_words=args.max_words,
        verbose=args.verbose,
        threads=args.threads
    )
    
    WWH.save_wordlist(args.output)
