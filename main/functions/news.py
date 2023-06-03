import datetime
from duckduckgo_search import ddg_news
from newsfetch.news import newspaper
from langchain.llms import Cohere
from langchain import PromptTemplate, LLMChain
import json
import random
import requests
from langchain.vectorstores import Chroma
from langchain.embeddings import CohereEmbeddings
from langdetect import detect
from translate import Translator
import time
from main.functions.create_pdf import create_pdf_function


def check_tweet_covered(tweet, category):
    # Randomly select an API key
    selected_key = json.load(open('apikeys.json', 'r'))['api_keys'][random.randint(
        0, len(json.load(open('apikeys.json', 'r'))['api_keys'])-1)]

    # Initialise model
    llm = Cohere(cohere_api_key=selected_key,
                 model='command-xlarge-nightly', temperature=0, max_tokens=300, stop=["\n"])

    persist_directory = "memory_news"
    selected_key = json.load(open('apikeys.json', 'r'))['api_keys'][random.randint(
        0, len(json.load(open('apikeys.json', 'r'))['api_keys'])-1)]
    embeddings = CohereEmbeddings(cohere_api_key=selected_key)

    vectordb = Chroma(persist_directory=persist_directory,
                      embedding_function=embeddings)

    docs = vectordb.similarity_search(tweet, k=3)

    similar_story_string = "\n".join(doc.page_content for doc in docs)
    print("Similar Story String")
    print(similar_story_string)

    template = """Instructions: Output 'Old' if the information in the Tweet or the exact same Tweet is already present in the Tweet List. If it is a new tweet then output 'New' . If the tweet is not related to {category} then output 'Irrelevant' \nTweet List:\n{similar_story_string}\nTweet:\n{tweet}\nOutput:"""

    prompt = PromptTemplate(template=template, input_variables=[
                            "tweet", "similar_story_string", "category"])

    # Create and run the llm chain
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    response = llm_chain.run(tweet=tweet, similar_story_string=similar_story_string,
                             category=category).replace("\n", "").replace(" ", "")
    print(response)

    if response == "New":
        print("adding text")
        print(tweet)
        vectordb.add_texts([tweet])
        vectordb.persist()
        print("DONE")

    return response


def news_function():
    list = ["Generative AI", "Artificial Intelligence", "Robotics"]

    summary_list = []
    title_list = []
    for i in range(len(list)):

        category = list[i]
        message = ""
        results = ddg_news(category, region='wt-wt',
                           safesearch='Off', time='d', max_results=10)

        print(f"Starting {category}")

        if results == None:
            break

        for result in results:

            link = result['url']
            try:
                response = requests.get(link, timeout=10)
                news = newspaper(link)
            except Exception as e:
                print(e)
                continue

            article = " ".join(
                [s for s in [news.description, news.article, news.summary] if s is not None])

            if article == "":
                continue

            # Randomly select an API key
            selected_key = json.load(open('apikeys.json', 'r'))['api_keys'][random.randint(
                0, len(json.load(open('apikeys.json', 'r'))['api_keys'])-1)]

            # Initialise model
            llm = Cohere(cohere_api_key=selected_key,
                         model='command-xlarge-nightly', temperature=0, max_tokens=300)

            template = "{article}\n\nInstructions: Summarize this text into 2-3 lines. Do not include any links in the summary."
            prompt = PromptTemplate(
                template=template, input_variables=["article"])

            # Create and run the llm chain
            llm_chain = LLMChain(prompt=prompt, llm=llm)
            info = llm_chain.run(article=article).replace("\n", "")

            covered_check = check_tweet_covered(info, category)
            if covered_check != "New":
                print(info)
                print("This link is " + covered_check)
                continue

            message = message + info + "\n" + link + "\n\n"

            # Load the JSON file
            with open('main/news.json', 'r') as file:
                data = json.load(file)

            # get current date
            now = datetime.datetime.now()

            # format date as YYYYMMDD without any symbols
            date_string = now.strftime('%Y%m%d')

            # Create a new item to add to the "news" array
            new_item = {
                "username": "",
                "id": "",
                "text": info,
                "link": link,
                "date": date_string
            }

            # Add the new item to the "news" array
            data['news'].append(new_item)

            # Write the updated JSON back to the file
            with open('main/news.json', 'w') as file:
                json.dump(data, file, indent=2)

        pre_message = f"{category} News\n\n"
        summary_list.append(message)
        title_list.append(pre_message)

    timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    create_pdf_function(summary_list, title_list, f'docs/{timestamp_str}.pdf')

    return ""
