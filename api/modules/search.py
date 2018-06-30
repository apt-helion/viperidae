#!/usr/bin/python3.6
import asyncio
import requests
import re

from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

class Spider():
    """
    Spider class used for crawl a website based of a provided seed uri.
    Used when website is not in db.

    Example usage:
    >>> uri = 'https://blog.justinduch.com'
    >>> spider  = Spider(uri)
    >>> results = spider.crawl()
    >>> results
    [...]
    """

    cache = {}

    def __init__(self, uri):
        self.uri      = uri
        self.hostname = urlparse(self.uri).netloc

        self.loop = asyncio.get_event_loop()

        # initalise pages with seed link
        self.pages = [{
            'uri'     : self.uri,
            'links'   : self.get_links(self.uri),
            'content' : self.get_content(self.uri)
        }]

        self.crawled  = [self.uri] # uris that have been crawled

    def cache_html(fn):
        def inner(uri):
            cache_key = hash(uri)
            if Spider.cache.get(cache_key): return Spider.cache[cache_key]

            Spider.cache[cache_key] = fn(uri)
            return Spider.cache[cache_key]

        return inner

    @staticmethod
    @cache_html
    def request_page(uri):
        """Gets the html for a page"""
        page  = requests.get(uri)
        html  = BeautifulSoup(page.text, "html.parser")

        return html

    def check_url(self, uri):
        """Checks if the uri is a file or a webpage"""
        url   = urljoin(self.uri, uri) # join in case it's a relative link
        _file = False

        file_extentions = (
            '.jpg', '.png', '.gif', '.pdf', '.docx',
            '.odt', '.doc', '.pptx', '.csv', '.xlsx'
        )

        if '?' in url or '#' in url: return None
        if url.lower().endswith(file_extentions): _file = True
        if url.endswith('/'): url = url[:-1] # strip any trailing backslashes

        return { 'uri': url, 'file': _file }

    def get_content(self, uri):
        """Gets important text from a webpage"""
        html = self.request_page(uri)

        return {
            'title' : html.title.string,
            'text'  : html.get_text()
        }

    def get_links(self, uri):
        """Gets every link in a page"""
        html = self.request_page(uri)

        links = [self.check_url(a['href']) for a in html.find_all('a', href=True) if self.check_url(a['href'])]

        return links

    async def async_get_links(self, uri):
        """Gets every link in a page but asyncronously"""
        html = await self.loop.run_in_executor(ThreadPoolExecutor(), self.request_page, uri)

        links = [self.check_url(a['href']) for a in html.find_all('a', href=True) if self.check_url(a['href'])]

        return links

    async def handle_task(self, task_id, work_queue):
        """Handles the async work for crawling"""
        while not work_queue.empty():
            link = await work_queue.get()
            uri  = link['uri']

            if uri not in self.crawled:
                self.crawled.append(uri)
                if self.hostname == urlparse(uri).netloc:

                    links = await self.async_get_links(uri)
                    for link in links:
                        if not link['file']: work_queue.put_nowait(link)

                    self.pages.append({
                        'uri'     : uri,
                        'links'   : links,
                        'content' : self.get_content(uri)
                    })
                    print(uri)

    async def crawl(self):
        """Sets the async queue, tasks, etc..."""
        queue = asyncio.Queue()

        [queue.put_nowait(link) for link in self.get_links(self.uri)]

        tasks = [self.handle_task(task_id, queue) for task_id in range(10)]

        await asyncio.wait(tasks)

        return self.pages

class Query():
    """
    Query ranks pages it is given according to a query term

    Example usage:
    >>> uri = 'https://blog.justinduch.com'
    >>> spider = Spider(uri)
    >>> pages  = spider.crawl()
    >>> Query(pages, 'test').search()
    [...]
    """

    def __init__(self, pages, query):
        self.pages = pages
        self.query = query.lower()
        self.words = re.split(" ", self.query)

        self.ranked_pages = []

    def link_rank(self, page):
        """Adds to the rank of every page it points to"""
        for link in page['links']:
            uri = link['uri']
            for r_page in self.ranked_pages:
                if uri == r_page['uri']: r_page['l_rank'] += page['c_rank']

    def content_rank(self, page):
        """Gets a page and returns it with a rank based on content"""
        rank = 0

        for word in self.words:
            rank += len(re.findall(word, page['content']['title'].lower())) * 2
            rank += len(re.findall(word, page['content']['text'].lower()))

        page['c_rank'] = rank
        page['l_rank'] = 0 # initalise link rank

        return page

    def search(self):
        for page in self.pages:
            # Copy pages in to ranked_pages with ranks
            self.ranked_pages.append(self.content_rank(page))

        for page in self.ranked_pages:
            self.link_rank(page) # rank pages from links

        # Final pass to add ranks together
        for page in self.ranked_pages:
            page['rank'] = ((page['c_rank']*page['l_rank']) + page['l_rank']) / 2

        return sorted(self.ranked_pages, key=lambda k: k['rank'], reverse=True)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
