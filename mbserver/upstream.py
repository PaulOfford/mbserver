import re
import os
import urllib.request
import urllib.error
import urllib.parse
import logging

from typing import Optional

from .config import SETTINGS

logger = logging.getLogger(__name__)


class UpstreamStore:
    posts_url_root = ""
    posts_dir = ""
    init_rc = -1  # default to bad

    def __init__(self):
        self.posts_url_root = SETTINGS.posts_url_root
        self.posts_dir = SETTINGS.posts_dir

        if not os.path.isdir(self.posts_dir):
            logger.info(f"Creating posts directory {self.posts_dir}/")
            os.mkdir(f"{self.posts_dir}/")
            if os.path.isdir(f"{self.posts_dir}/"):
                self.init_rc = 0
            else:
                logger.error(f"Terminating - can't create posts directory {self.posts_dir}/")
                exit(-1)
        else:
            self.init_rc = 0

    @staticmethod
    def get_web_data(url) -> Optional[str]:
        try:
            page = urllib.request.urlopen(url)
            page_bytes = page.read()
            return page_bytes.decode("utf-8")
        except (urllib.error.HTTPError, urllib.error.URLError):
            logger.error(f"Unable to get {url}")
            return None

    def get_new_content(self, starting_at: int):
        post_lst = self.get_web_data(f'{self.posts_url_root}/post.lst')
        if post_lst:
            entries = re.findall(r"(\d+) - ([ .A-Za-z0-9\-]+)\r\n", post_lst)
            # print(entries)

            for i, entry in enumerate(entries):
                if i < starting_at:
                    continue
                else:
                    file_name = f"{entry[0]} - {entry[1]}"
                    enc_fn = urllib.parse.quote(file_name)
                    file_url = f"{self.posts_url_root}/{enc_fn}"
                    post_text = self.get_web_data(file_url)
                    if post_text:
                        post_text = post_text.replace("\r\n", "\n")
                        post_text = post_text.strip()
                        logger.info(f"Adding new post to the blog store - {file_name}")
                        f = open(f"{self.posts_dir}/{file_name}", "wt")
                        f.write(post_text)
                        f.close()
