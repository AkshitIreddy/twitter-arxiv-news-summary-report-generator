import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from langchain.llms import Cohere
from langchain import PromptTemplate, LLMChain
import random
import json
from main.functions.create_pdf import create_pdf_function


def arxiv_function():

    list = ["Generative AI" , "Language Models"]

    summary_list = []
    title_list = []
    for topic in list:
        time.sleep(60)
        print(f"Starting {topic}")

        papers = get_paper_info(topic)

        print(f"Found {len(papers)} for {topic}")

        if len(papers) == 0:
            print(f"No Papers for {topic}")
            continue

        summary_with_link = ""
        print(f"Starting {topic}")
        count = 0
        for paper in papers:
            if count > 5:
                time.sleep(20)
                count = 0
            count += 1
            title = paper['title']
            print(f"Analyzing Paper {title} ")
            # Randomly select an API key
            selected_key = json.load(open('apikeys.json', 'r'))['api_keys'][random.randint(
                0, len(json.load(open('apikeys.json', 'r'))['api_keys'])-1)]

            # Initialise model
            llm = Cohere(cohere_api_key=selected_key,
                         model='command-xlarge-nightly', temperature=0, max_tokens=300)

            # Create the prompt
            text = f'Title: {paper["title"]}\nAuthors: {", ".join(paper["authors"])}\nAbstract: {paper["abstract"]}'
            template = """{text}\nSummarise this research paper in a concise and clear way, do not exceed more than 5 lines."""
            prompt = PromptTemplate(
                template=template, input_variables=["text"])

            # Create and run the llm chain
            llm_chain = LLMChain(prompt=prompt, llm=llm)
            response = llm_chain.run(text).replace("\n", "")

            # add to the string
            summary_with_link = summary_with_link + \
                f'Title: {paper["title"]}\n{response}\nLink: {paper["url"]}\n\n'

        pre_message = f"{topic} research papers summaries\n\n"
        message = summary_with_link

        summary_list.append(message)
        title_list.append(pre_message)

    timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    create_pdf_function(summary_list, title_list, f'docs/{timestamp_str}.pdf')

    return ""


def get_paper_info(topic):
    result = []

    try:
        url = f'https://arxiv.org/search/?query={topic}&searchtype=all&abstracts=show&order=-announced_date_first&size=25'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        papers = soup.find_all('li', class_='arxiv-result')

        for paper in papers:
            paper_dict = {}

            # Extract the date of submission from the HTML
            date_string = paper.find('p', class_='is-size-7').text.strip()
            date_string = date_string.split(
                ';')[0].replace('Submitted ', '').strip()
            date_format = '%d %B, %Y'
            date = datetime.strptime(date_string, date_format)

            # Check if the date is within the last 48 hours
            if datetime.now() - date < timedelta(hours=48):
                title = paper.find(
                    'p', class_='title is-5 mathjax').text.strip()
                paper_dict['title'] = title

                authors = paper.find('p', class_='authors').find_all('a')
                authors = [author.text.strip() for author in authors]
                paper_dict['authors'] = authors

                abstract = paper.find(
                    'p', class_='abstract mathjax').text.strip()
                # Remove unnecessary text from the abstract
                abstract = abstract.split('▽ More\n\n\n')[1].split(
                    '\n        △ Less')[0].strip()
                paper_dict['abstract'] = abstract

                paper_url = paper.find(
                    'p', class_='list-title is-inline-block').find('a')['href']
                paper_dict['url'] = paper_url

                result.append(paper_dict)
    except Exception as e:
        print(e)

    return result
