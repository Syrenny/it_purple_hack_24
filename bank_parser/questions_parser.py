import requests
import csv
import os

from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

parsed_links = []
fields = ['answer_filename', 'answer_link']
saved_cnt = 0
questions_number = 0

def parse_questions(parser, url, questions_folder):
    global saved_cnt, data_file, questions_number
    question_class_list = parser.find_all('div', class_='dropdown question')
    for question_container in question_class_list:
        questions_number += 1
        try:
            text_path = os.path.join(questions_folder, f'text{saved_cnt}.txt')
            text_file = open(text_path, 'wb')
            question_phrase_tag = question_container.find('div', class_='question_title').find('h3 h2')
            check_paragraph_tag = question_phrase_tag.find('p')
            if check_paragraph_tag != None:
                question_phrase_tag = check_paragraph_tag
            question_phrase = question_phrase_tag.text
            text_block = question_container.find('div', class_='additional-text-block')
            data_tags = text_block.find_all('p ul li ol')
            text_data = question_phrase + '\n'
            if len(data_tags) == 0:
                text_data += text_block.text
            else:
                for data_tag in data_tags:
                    text_data += data_tag.text
            text_data = text_data.encode('utf-16')
            text_file.write(text_data)
            data_file.writerows([{
                fields[0]: f'text{saved_cnt}.txt', 
                fields[1]: url
            }])
            saved_cnt += 1
        except Exception as e:
            print(e)
            pass
        text_file.close()


def parse_dropdown_containers(parser, url, questions_folder):
    global saved_cnt, data_file, questions_number
    dropdown_containers = parser.find_all('div', class_='dropdown dropdown_container')
    if len(dropdown_containers) != 0:
        print('have containers')
        for dropdown_container in dropdown_containers:
            if len(dropdown_container.find_all('div', class_='dropdown_title-link')) == 0:
                parse_questions(dropdown_container, url, questions_folder)
            else:
                anchor = dropdown_container.find('a')
                new_url = urljoin(url, anchor['href'])
                if urlparse(new_url).netloc == 'www.cbr.ru':
                    link_page = requests.get(new_url)
                    link_parser = BeautifulSoup(link_page.content, 'html.parser')
                    parse_dropdown_containers(link_parser, new_url)
    else:
        print('no containers')
        parse_questions(parser, url, questions_folder)


def get_all_questions(url, questions_folder):
    global data_file
    main_page = requests.get(url)
    main_page_parser = BeautifulSoup(main_page.text, 'html.parser')
    parsed_links.append(url)

    if not os.path.exists(questions_folder):
        os.makedirs(questions_folder)

    # получаем каждую рубрику
    rubrics = main_page_parser.find_all("div", class_="rubric")
    rubric_links = []
    rubric_names = []
    for rubric in rubrics:
        rubric_links.append(urljoin(url, rubric.a['href']))
        rubric_names.append(urljoin(url, rubric.a.text))

    # обрабатываем каждую рубрику
    for rubric_link, rubric_name in zip(rubric_links, rubric_names):
        print(rubric_name)
        rubric_page = requests.get(rubric_link)
        rubric_parser = BeautifulSoup(rubric_page.text, 'html.parser')
        parse_dropdown_containers(rubric_parser, rubric_link, questions_folder)
        

if __name__ == "__main__":

    csv_file = open("text_files_name_link.csv", 'w')
    data_file = csv.DictWriter(csv_file, fieldnames=fields)
    data_file.writeheader()
    get_all_questions("https://cbr.ru/faq/", "text_files")
    print(saved_cnt, questions_number)
