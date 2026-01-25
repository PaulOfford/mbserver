import re
import os
import urllib.request
import urllib.error
import urllib.parse
import logging

from typing import Optional


logger = logging.getLogger(__name__)


class UpstreamStore:
    posts_url_root = ""
    posts_url = ""
    posts_dir_root = ""
    posts_dir = ""
    blog = ""
    init_rc = -1  # default to bad

    def __init__(self, url_root, dir_root, blog):
        self.blog = blog

        self.posts_url_root = url_root
        self.posts_url = f"{self.posts_url_root}{self.blog}"

        self.posts_dir_root = dir_root
        self.posts_dir = f"{self.posts_dir_root}{self.blog}"
        self.posts_dir = dir_root  # remove this line if/when we support multiple blogs on one station

        if not os.path.isdir(self.posts_dir_root):
            logger.info(f"Creating posts directory {self.posts_dir}/")
            os.mkdir(f"{self.posts_dir}/")
            if os.path.isdir(f"{self.posts_dir_root}/"):
                self.init_rc = 0
            else:
                logger.error(f"Terminating - can't create posts directory {self.posts_dir}/")
                exit(-1)
        else:
            self.init_rc = 0

        # The following code is for future use if we enable running multiple blogs on a single station
        #
        # if os.path.isdir(self.posts_dir_root):
        #     if os.path.isdir(f"{self.posts_dir}/"):
        #         self.init_rc = 0
        #     else:
        #         os.mkdir(f"{self.posts_dir/")

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
        post_lst = self.get_web_data(f'{self.posts_url_root}{self.blog}/post.lst')
        if post_lst:
            entries = re.findall(r"(\d+) - ([ .A-Za-z0-9\-]+)\r\n", post_lst)
            # print(entries)

            for i, entry in enumerate(entries):
                if i < starting_at:
                    continue
                else:
                    file_name = f"{entry[0]} - {entry[1]}"
                    enc_fn = urllib.parse.quote(file_name)
                    file_url = f"{self.posts_url_root}{self.blog}/{enc_fn}"
                    post_text = self.get_web_data(file_url)
                    if post_text:
                        post_text = post_text.replace("\r\n", "\n")
                        logger.info(f"Adding new post to the blog store - {file_name}")
                        f = open(f"{self.posts_dir}/{file_name}", "wt")
                        f.write(post_text)
                        f.close()
