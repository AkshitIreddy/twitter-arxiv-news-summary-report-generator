import json
import re
import time
from translate import Translator
from twitter_scraper_selenium import scrape_profile
from langchain.llms import Cohere
from langchain import PromptTemplate, LLMChain
import random
from duckduckgo_search import ddg
from newsfetch.news import newspaper
import datetime
import requests
from main.functions.create_pdf import create_pdf_function


def summarize(information):
    time.sleep(10)
    # Randomly select an API key
    selected_key = json.load(open('apikeys.json', 'r'))['api_keys'][random.randint(
        0, len(json.load(open('apikeys.json', 'r'))['api_keys'])-1)]

    # Initialise model
    llm = Cohere(cohere_api_key=selected_key,
                 model='command-xlarge-nightly', temperature=0, max_tokens=300)

    template = "{information}\nSummarize these tweets in a clear and concise way. Do not remove any information. Make it easy to understand. \nSummary:"

    prompt = PromptTemplate(template=template, input_variables=["information"])

    # Create and run the llm chain
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    response = llm_chain.run(information).replace("\n", "")
    return response


def twitter_function():
    print("Starting...")
    # Load the JSON data from the file
    with open('main/twitter_usernames.json') as f:
        data = json.load(f)

    title_list = []
    summary_list = []

    # Iterate through the usernames array
    for username in data['usernames']:
        print("Sleeping for 2 minutes...")
        time.sleep(120)
        print("Sleep over...")
        print("Scraping Profile")
        try:
            response = scrape_profile(
                twitter_username=username, output_format="json", browser="chrome", tweets_count=10)
        except Exception as e:
            continue
        print("Scraping done")
        response = json.loads(response)
        response = dict(
            sorted(response.items(), key=lambda x: x[1]['posted_time']))
        print("Tweet Data")
        print(response)

        tweets_full_info = ""
        all_links = []
        # Iterate through the JSON response
        for tweet_id, tweet_data in response.items():
            # Load the JSON file
            with open('main/news.json', 'r') as file:
                data = json.load(file)

            print(f"\n\nAnalysing Tweet {tweet_id}")
            posted_time = datetime.datetime.strptime(
                tweet_data['posted_time'], '%Y-%m-%dT%H:%M:%S+00:00')

            # get current time
            current_time = datetime.datetime.utcnow()

            # calculate the time difference between posted_time and current_time
            time_diff = current_time - posted_time

            # check if the time difference is more than 24 hours
            if time_diff > datetime.timedelta(hours=24):
                print(
                    "Tweet " + tweet_data['content'] + " from " + tweet_data['username'] + " is old.")
                continue

            print("Tweet is not old")

            # Check if the tweet id is in the news_data if yes skip
            if tweet_id in [user['id'] for user in data['news']]:
                print("Tweet " + tweet_data['content'] + " from " +
                      tweet_data['username'] + " is already covered as id found.")
                continue

            print("Tweet id is not covered")

            # get current date
            now = datetime.datetime.now()

            # format date as YYYYMMDD without any symbols
            date_string = now.strftime('%Y%m%d')

            # Create a new item to add to the "news" array
            new_item = {
                "username": tweet_data['username'],
                "id": tweet_id,
                "text": "NOTPOSTED",
                "link": "NOTPOSTED",
                "date": date_string
            }

            tweet = tweet_data['content']
            tweet_link = ""
            tweet_link_info = ""
            print("Creating tweet link info")
            if tweet_data['link'] != "":
                print(tweet_data['link'])
                try:
                    tweet_link = requests.head(
                        tweet_data['link'], allow_redirects=True).url
                    response = requests.get(tweet_link, timeout=10)
                    news = newspaper(tweet_link)
                    tweet_link_info = " ".join(
                        [s for s in [news.description, news.article, news.summary] if s is not None])
                    if tweet_link != "":
                        all_links.append(tweet_link)
                except Exception as e:
                    print(e)

            tweet_link_info = tweet_link_info[:2000]
            print(
                f"Tweet is {tweet} and tweet link info is {tweet_link_info}")

            # define the regular expression to match links
            link_regex = r"(?P<url>https?://[^\s]+)"

            # use the findall method to extract all links from the text
            links = re.findall(link_regex, tweet)
            print("Extracted Links")
            print(links)

            links_info = ""
            # print out the links that were found
            for link in links:
                link = link.replace("…", "")
                try:
                    print("Scraping Link")
                    response = requests.get(link, timeout=10)
                    news = newspaper(link)
                except Exception as e:
                    print("Error ocurred while scraping")
                    print(e)
                    continue
                article = " ".join(
                    [s for s in [news.description, news.article, news.summary] if s is not None])
                print(f"Article is {article}")
                links_info = links_info + article
                all_links.append(link)

            if links_info != "":
                links_info = links_info[:2000]

                print(f"Links info is {links_info}")

            tweet_full_info = '\n'.join([tweet, tweet_link_info, links_info])

            print(f"tweet full info is {tweet_full_info}")

            tweet_full_info = "Tweet: " + tweet_full_info

            # update tweets_full_info
            tweets_full_info = tweets_full_info + tweet_full_info + "\n"

            # Add the new item to the "news" array
            new_item['text'] = tweet_full_info
            new_item['link'] = tweet_link
            data['news'].append(new_item)
            # Write the updated JSON back to the file
            with open('main/news.json', 'w') as file:
                json.dump(data, file, indent=2)

        if tweets_full_info == "":
            continue

        tweets_full_info = summarize(tweets_full_info)
        print(f"Summarized tweet_full_info {tweets_full_info}")

        links_string = ""
        info = f"{tweets_full_info}"

        link = ""
        if len(all_links) > 0:
            link = all_links[0]
            links_string = "\n".join(i for i in all_links)

        print("Information is " + info)
        print("Link is " + link)

        post = info + "\n" + links_string

        summary_list.append(post)
        title_list.append(tweet_data['username'])

    timestamp_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    create_pdf_function(summary_list, title_list, f'docs/{timestamp_str}.pdf')

    return ""
