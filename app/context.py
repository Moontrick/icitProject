import os
from dotenv import load_dotenv

load_dotenv()

class Context:
    visitedPages = set()
    startUrl = "https://www.flaticon.com/ru/icon-fonts-most-downloaded"
    directory = 'images'
    databaseUrl = os.getenv("URL_DATABASE")
    visitedPageData = "visitedUrl.txt"
    def init_visited_pages(self):
        if os.path.exists(self.visitedPageData):
            with open(self.visitedPageData, "r") as f:
                self.visitedPages = set(f.read().splitlines())
    def make_directory(self):
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)


ctx = Context()