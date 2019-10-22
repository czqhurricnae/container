# -*- coding:utf-8 -*-
from bs4 import BeautifulSoup
from splinter import Browser
browser = Browser()
import time
import re
from collections import namedtuple


class Scrapper:
    def __init__(self):
        self.project_tools = []
        self.urls = []

    def get_title(self):
        content = open(r'C:\Users\czq\OneDrive\exercise\scrapper\tool.txt',
                       'r',
                       encoding='utf-8').read()
        bs_obj = BeautifulSoup(content, 'html.parser')
        raw_title_list = bs_obj.find_all(
            'h4', {'class': "list-group-item-heading ng-binding"})
        title_list = [x.get_text() for x in raw_title_list]
        # raw_model_list = bs_obj.find_all('b',{'class':'ng-binding'})
        # model_list = [x.get_text() for x in raw_model_list[::2]]
        # raw_list = [x+y for x, y in zip(model_list, title_list)]
        result_list = []
        with open(r'C:\Users\czq\OneDrive\exercise\scrapper\title.txt',
                  'w+',
                  encoding='utf-8') as wf:
            for t in title_list:
                try:
                    temp = t.split(' ')[-1]
                    result = temp.replace('·', '')
                except Exception as e:
                    print(e)
                result_list.append(result)
                wf.write(result)
                wf.write('\n')
        return result_list

    def get_url(self, title_list):
        browser.visit('http://fzxiamenaircom.h250.000pc.net/PC/index.html')
        url_list = []
        url_txt = open(r'C:\Users\czq\OneDrive\exercise\scrapper\url.txt',
                       'w+',
                       encoding='utf-8')
        for title in title_list:
            try:
                browser.find_by_tag('input').fill(title)
                browser.find_by_text('搜索').click()
                time.sleep(1)
                browser.find_by_tag('h4').click()
                time.sleep(1)
                url = browser.url
            except Exception as e:
                print e
            url_list.append(url)
        url_set = {item for item in url_list}
        for item in url_set:
            url_txt.write(item)
            url_txt.write('\n')
        print(len(url_list), len(title_list))
        return list(url_set)

    def get_tool(self, urls):
        urls = list(urls)
        Project_tools = namedtuple(
            'Project_tools', 'title model chapter last_modified tool_list')
        i = 0
        for url in urls:
            i += 1
            browser.visit(url)
            time.sleep(1)
            bs_obj = BeautifulSoup(browser.html)
            meta = bs_obj.find('p', {'class': 'ng-binding'})
            chapter_rexp = re.compile(r'\b\d{2,2}\b')
            last_modified_rexp = re.compile(r'(\d{4,4}-\d{2,2}-\d{2,3})')
            try:
                title = bs_obj.find('b', {
                    'style': 'padding-left:15px;'
                }).text.replace('· ', '')
                for c in {
                        '737NG ',
                        '737NG',
                        '737-700/800 ',
                        '737-700 ',
                        '737-700',
                        '737-800 ',
                        '737-800'
                        '737-700/800',
                        '757',
                        '757 ',
                        '757-200',
                        '757-200 ',
                        '787',
                        '787 ',
                }:
                    if c in title:
                        title = title.lstrip(c)
                model = meta.find('b', {
                    'class': 'ng-binding'
                }).text.lstrip('B')
                chapter = chapter_rexp.search(meta.text).group(0)
                last_modified = last_modified_rexp.search(meta.text).group(0)
                print(i, title)
            except Exception as e:
                print('Pattern search go wrong,{0}:{1}'.format(
                    type(e).__name__, e))
                print(url)
            raw_str = bs_obj.findAll('tr', {'class': 'ng-scope'})
            tool_list = [item.text.split('\n')[1:-1] for item in raw_str]
            projec_tools = Project_tools(model + title, model, chapter,
                                         last_modified, tool_list)
            self.project_tools.append(projec_tools)

    def read_url(self):
        self.urls = list(open('/home/c/scrapper/url.txt', 'r').readlines())
        return self.urls
