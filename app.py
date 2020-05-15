import os
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from pymongo import MongoClient
from datetime import datetime

chrome_options = ChromeOptions()
chrome_options.binary_location = os.environ.get('GOOGLE_CHROME_BIN')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--no-sandbox')

driver = Chrome(executable_path=os.environ.get('CHROMEDRIVER_PATH'), chrome_options=chrome_options)
wait = WebDriverWait(driver, 15)
client = MongoClient(os.environ.get('MONGODB_URI'))
db = client['hoax-detection']
collection = db['train-datasets']
datetime_format = "%B %d, %Y"


def get_article(url):
    driver.execute_script(f'window.open("{url}")')
    driver.switch_to.window(driver.window_handles[1])

    article = wait.until(lambda drv: drv.find_element_by_css_selector('article.post'))
    article_title_element = article.find_element_by_css_selector('h1.entry-title')
    article_date_element = article.find_element_by_css_selector('span.entry-meta-date a')
    article_author_element = article.find_element_by_css_selector('span.entry-meta-author a')
    article_content_element = article.find_element_by_css_selector('div.entry-content')

    article_title = article_title_element.text
    article_date_text = article_date_element.text
    article_datetime = datetime.strptime(article_date_text, datetime_format)
    article_date = f'{article_datetime.year}-' \
        f'{"0" + str(article_datetime.month) if article_datetime.month < 10 else article_datetime.month}-' \
        f'{"0" + str(article_datetime.day) if article_datetime.day < 10 else article_datetime.day}'
    article_author = article_author_element.text
    article_content = article_content_element.text

    if not collection.find_one({'url': url}):
        collection.insert_one({
            'url': url,
            'title': article_title,
            'date': article_date,
            'author': article_author,
            'content': article_content,
            'class': 'Hoax'
        })

    driver.close()
    driver.switch_to.window(driver.window_handles[0])


def get_all_articles(page):
    driver.get(f'https://turnbackhoax.id/page/{page}')

    try:
        articles = wait.until(lambda drv: drv.find_elements_by_css_selector('article.mh-loop-item'))

        for article in articles:
            article_url_element = article.find_element_by_css_selector('h3.mh-loop-title a')
            article_url = article_url_element.get_attribute('href')
            get_article(article_url)

        get_all_articles(page + 1)
    except TimeoutException:
        get_all_articles(1)


get_all_articles(1)