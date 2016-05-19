from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep, time
from re import compile, match, search
from sys import argv
from random import choice
import os
import json

def scrollPage(browser):
    print 'Starting to scroll'
    oldSource = browser.page_source
    while True:
        sleep(3)
        print 'Executing scroll script'
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        newSource = browser.page_source
        if newSource == oldSource:
            break
        oldSource = newSource
    print 'Done scrolling'

def getTopics():
    fr = open('topic_urls.txt', mode='r')
    lines = fr.read().split('\n')
    topic_urls = []
    for line in lines:
        x = line.split('\t')
        topic_urls.append(x[len(x)-1])
    return topic_urls


def getHTMLSrc(browser, topic):
    url = topic + '?share=1' #'https://www.quora.com' + topic + '?share=1'
    try:
        browser.get(url)
    except:
        return "<html></html>"
    scrollPage(browser)
    sleep(3)
    html_source = browser.page_source
    return html_source

def extractQuestionLinks(html_source, useCached=False):
    if useCached:
        fr = open('index.html' , mode='r')
        html_source = fr.read()
    soup = BeautifulSoup(html_source)
    links = []
    for i in soup.find_all('a', { "class" : "question_link" }):
        #anchors = i.find_all('a', href=True)
        if len(i) >0 :
            link = i['href']
            try:
                links.append(link)
            except UnicodeEncodeError:
                pass
    return links

def getQuestionText(soup):
    try:
        a = soup.find('div', { "class" : "question_text_edit" }).getText()
        return a
    except:
        return None

def getTopics(soup):
    topics = soup.find_all('div', { "class" : "QuestionTopicListItem TopicListItem topic_pill" })
    return ', '.join(topic.getText() for topic in topics)

def getAnswerText(answer):
    answer_text = answer.find('div', { "class" : "ExpandedQText ExpandedAnswer" }) # _all
    result = answer_text.getText()
    if result:
        return result


def question(browser, question_url):
    if not match('/', question_url):
        print 'Local urls should start with /:', question_url
        return
    url = 'http://www.quora.com' + question_url + '?share=1'
    browser.get(url)
    scrollPage(browser)
    sleep(3)
    html_source = browser.page_source.encode('utf-8')

    
    soup = BeautifulSoup(html_source)
    question_id = question_url
    question_text = getQuestionText(soup)
    if question_text == None:
        return 0
    #current_topic = getCurrentTopic(soup)
    topics = getTopics(soup)
    collapsed_answer_pattern = compile('\d+ Answers? Collapsed')
    answers = soup.find_all('div', { "class" : "Answer AnswerBase" })  #class="Answer AnswerBase
    i = 1
    answer_text = ""
    for answer in answers:
        result = collapsed_answer_pattern.match(answer.getText())
        if result or 'add_answer_wrapper' in answer['class']:
            print("skipped ***")
            continue # skip collapsed answers and answer text box
        answer= getAnswerText(answer)
        answer_text = answer_text + answer
    try:
        #First line is answer_id
        dict= {'topics': topics, 'question': question_text, 'answers':answer_text}
        # out_string =  '{{{' + topics + '}}}' + ', ' \
        #               + '{{{' + question_text + '}}}' + ', ' \
        #               + '{{{' + answer_text + '}}}' + '\n'

    except UnicodeDecodeError:
        print 'Unicode decode error'
        return 0
    a = []
    if not os.path.isfile('/Users/ana/Desktop/All data/UCLA/Q3rd/cho/project/crawler/answers.csv'):
        a.append(dict)
        with open ('/Users/ana/Desktop/All data/UCLA/Q3rd/cho/project/crawler/answers.csv', 'w')as f:
            f.write(json.dumps(a,indent=2))
    else:
        with open ('/Users/ana/Desktop/All data/UCLA/Q3rd/cho/project/crawler/answers.csv') as file:
            feeds = json.load(file)
        feeds.append(dict)
        with open('/Users/ana/Desktop/All data/UCLA/Q3rd/cho/project/crawler/answers.csv', mode= 'w') as f:
            f.write(json.dumps(feeds,indent=2))


def main(argv):
    chromedriver = "/anaconda/bin/chromedriver"
    os.environ["webdriver.chrome.driver"] = chromedriver
    start = time()
    option = argv
    if option == 'getquestionlinks':
        browser = webdriver.Chrome(chromedriver)
        topic_urls = getTopics()
        print topic_urls
        for topic_url in topic_urls:
            html_source = getHTMLSrc(browser, topic_url)
            links = extractQuestionLinks(html_source, False)
            print len(links)
            with open('questions.txt', mode='a') as file:
                file.write('\n'.join(links).encode('utf-8'))
            with open('questions_' + str(topic_url), mode='a'):
                file.write('\n'.join(links).encode('utf-8'))
    elif option == 'downloadquestions':
        browser = webdriver.Chrome(chromedriver)
        links = []
        done = []
        with open('questions.txt', mode='r') as file:
            links = file.read().split('\n')
        try:
            with open('questions-done.txt', mode='r') as file:
                done = file.read().split('\n')
        except IOError:
            done = []
        links_set = set(links)
        done_set = set(done)
        
        links_not_done_unique = list(links_set.difference(done_set))
        print len(links_not_done_unique), 'remaining'
        for link in links_not_done_unique:
            print link
            res = question(browser, link)
            if res != 0:
                with open('questions-done.txt', mode='a') as file:
                    try:
                        file.write((link + '\n').encode('utf-8'))
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        print 'Character encodings suck and fail'
    end = time()
    print 'Script runtime: ', end - start

if __name__ == "__main__":
    main(argv="downloadquestions")


        # answer_id = question_id + '-' + user_id
        #date = getDate(answer)
        #number_of_upvotes = getNumberOfUpvotes(answer)
        #upvoters = getUpvoters(answer)