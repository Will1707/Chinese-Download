import requests
import lxml.html
import random
import time
import os
import json
import urllib.parse
from bs4 import BeautifulSoup
from bs4.dammit import EncodingDetector
from datetime import datetime

WEBSITE_NAME = 'WEBSITE_NAME'
SIGN_IN_PAGE = 'SIGN_IN_PAGE'
LESSON_PAGE = 'LESSON_PAGE'
WEBSITE = 'WEBSITE'

lesson_url = []
login_details = {
        'email': 'EMAIL',
        'password': 'PASSWORD'
        }

download_urls = []
downloads = ['HQ_audio', 'LQ_audio', 'Dialogue', 'Vocab_Review', 'Lesson', 'Lesson_Plan', 'Expansion', 'Grammar']
failed_count = 0

def login(info):
    s = requests.session()
    login = s.get(SIGN_IN_PAGE)
    login_html = lxml.html.fromstring(login.text)
    hidden_inputs = login_html.xpath(r'//form//input[@type="hidden"]')
    form = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs}
    form['email'] = info['email']
    form['password'] = info['password']
    s.post(SIGN_IN_PAGE, data=form)
    print("logged in")
    return s

def request(url, s):
    failed_count = 0
    while True:
        try:
            response = s.get(url)
            if type(response.content) is None:
                0/0
            failed_count = 0
            break
        except:
            print("failed")
            time.sleep(3)
            if failed_count ==3:
                break
            failed_count +=1
    http_encoding = response.encoding if 'charset' in response.headers.get('content-type', '').lower() else None
    html_encoding = EncodingDetector.find_declared_encoding(response.content, is_html=True)
    encoding = html_encoding or http_encoding
    soup = BeautifulSoup(response.content, from_encoding=encoding)
    return soup

def get_lesson_urls(s):
    for page_num in range(3,4):
        intermediate_url = LESSON_PAGE + str(page_num)
        soup = request(intermediate_url, s)
        for links in soup.find_all('a', href=True):
            if links['href'][0:9] == '/lessons/':
                lesson_url.append(urllib.parse.unquote(WEBSITE + links['href']))
        time.sleep(random.uniform(1, 10.0))
        print("got lesson urls")
        return lesson_url

def get_download_urls(s, lesson_url):
    lesson_download_info = {}
    for i in range(len(lesson_url)):
        soup = request(lesson_url[i], s)
        date = soup.find(itemprop = 'datePublished').get_text()
        date = datetime.strptime(date, '%B %d, %Y').strftime('%Y-%m-%d')
        lesson_downloads = lesson_logic(soup)
        title = get_title(lesson_url[i])
        lesson = str(date) + '_Lesson'

        lesson_download_info[lesson] = {
                'HQ_audio': {
                        'url': lesson_downloads['HQ_audio'],
                        'extension': '.mp3'
                        },
                'LQ_audio': {
                        'url': lesson_downloads['LQ_audio'],
                        'extension': '.mp3'
                        },
                'Dialogue': {
                        'url': lesson_downloads['Dialogue'],
                        'extension': '.mp3'
                        },
                'Vocab_Review': {
                        'url': lesson_downloads['Vocab_Review'],
                        'extension': '.mp3'
                        },
                'Lesson': {
                        'url': lesson_downloads['Lesson'],
                        'extension': '.pdf'
                        },
                'Lesson_Plan': {
                        'url': lesson_downloads['Lesson_Plan'],
                        'extension': '.html'
                        },
                'Expansion': {
                        'url': lesson_downloads['Expansion'],
                        'extension': '.html'
                        },
                'Grammar': {
                        'url': lesson_downloads['Grammar'],
                        'extension': '.html'
                        },
                'title': title,
                'date': date,
                }
        time.sleep(random.uniform(1, 5.0))
    print("download urls")
    return lesson_download_info

def lesson_logic(soup):
    lesson_downloads = {
        'HQ_audio': None,
        'LQ_audio': None,
        'Dialogue': None,
        'Vocab_Review': None,
        'Lesson': None,
        'Lesson_Plan': None,
        'Expansion': None,
        'Grammar': None
    }
    download_lesson = soup.find(id = 'panelLessonReviewDownloads').findAll('a')
    for i in range(len(download_lesson)):
        text = download_lesson[i].get_text().strip()
        if text == 'Lesson':
             lesson_downloads['HQ_audio'] = WEBSITE + download_lesson[i]['href']
        elif 'LQ' in text:
            lesson_downloads['LQ_audio'] = WEBSITE + download_lesson[i]['href']
        elif 'Dialogue' in text:
            lesson_downloads['Dialogue'] = WEBSITE + download_lesson[i]['href']
        elif 'Vocab Review' in text:
            lesson_downloads['Vocab_Review'] = WEBSITE + download_lesson[i]['href']
        elif 'Lesson PDF' in text:
            lesson_downloads['Lesson'] = WEBSITE + download_lesson[i]['href']
        elif 'Text Version' in text:
            lesson_downloads['Lesson_Plan'] = WEBSITE + download_lesson[i]['href']
        elif 'Expansion' in text:
            lesson_downloads['Expansion'] = WEBSITE + download_lesson[i]['href']
        elif 'Grammar' in text:
            lesson_downloads['Grammar'] = WEBSITE + download_lesson[i]['href']
    return lesson_downloads

def get_title(lesson_link):
    title = lesson_link[31:].split("-")
    if len(title) > 4:
        title = "_".join(title[:5])
    else:
        title = "_".join(title)
    return title

def write_file(s, lesson, download, lesson_download_info):
    failed_count = 0
    print("Downloading; " + str(lesson_download_info[lesson]['title']))
    file = str(str(download)  + '-' + str(lesson_download_info[lesson]['title']) + str(lesson_download_info[lesson][download]['extension']))
    folder = str(lesson_download_info[lesson]['date'])  + ' - ' + str(" ".join(lesson_download_info[lesson]['title'].split("_")).title())
    DIR_PATH  = os.path.dirname(os.path.realpath(__file__))
    if not os.path.exists(os.path.join(DIR_PATH, WEBSITE_NAME, folder)):
        os.mkdir(os.path.join(DIR_PATH, WEBSITE_NAME, folder))
    file_path = os.path.join(DIR_PATH, WEBSITE_NAME, folder, file)
    if not os.path.exists(os.path.join(DIR_PATH, WEBSITE_NAME, folder, file)):
        while True:
            try:
                if lesson_download_info[lesson][download]['url'] is None:
                    break
                print("Downloading")
                failed_count += 1
                if failed_count == 3:
                    break
                response = s.get(lesson_download_info[lesson][download]['url'])
                if response.status_code == 200:
                    with open(file_path, 'wb') as file:
                        file.write(response.content)
                    print("Downloaded")
                    break
            except:
                print("Failed")
                time.sleep(3)
        print("finished write file")

def main():
    s = login(login_details)
    lesson_url = get_lesson_urls(s)
    lesson_download_info = get_download_urls(s, lesson_url)
    for lesson in lesson_download_info.keys():
        for download in downloads:
            write_file(s, lesson, download, lesson_download_info)

if __name__== "__main__":
    main()
