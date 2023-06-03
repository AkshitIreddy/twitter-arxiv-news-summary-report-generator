from functions.arxiv import arxiv_function
from functions.twitter import twitter_function
from functions.news import news_function
import datetime
import time


def main_function(timezone):
    next_call_time = ""
    while True:
        # Get the current time in the specified timezone
        now = datetime.datetime.now(timezone)

        # Convert the timezone to a string for logging purposes
        timezone_name = now.strftime('%Z')

        # Check if it's 9:00 AM IST and call functions arxiv_function and twitter_function
        if now.hour == 9 and now.minute == 0:
            try:
                arxiv_function()
                twitter_function()
            except Exception as e:
                print(e)
            # Set the next function call time to 11:00 AM IST
            next_call_time = now.replace(
                hour=11, minute=0, second=0, microsecond=0)
        # Check if it's 11:00 AM or 5:00 PM IST and call function news_function
        elif now.hour in [11, 17] and now.minute == 0:
            try:
                news_function()
            except Exception as e:
                print(e)
            # Set the next function call time to the next hour
            next_call_time = now.replace(
                minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
        # Check if it's been 3 hours since the last time twitter_function was called and call twitter_function
        elif now.hour % 3 == 0 and now.minute == 0:
            try:
                twitter_function()
            except Exception as e:
                print(e)
            # Calculate the time for the next function call
            next_call_time = now.replace(
                hour=(now.hour + 3) % 24, minute=0, second=0, microsecond=0)
            if now.hour < 18 and now.hour >= 15:
                next_call_time = now.replace(
                    hour=17, minute=0, second=0, microsecond=0)
        else:
            time.sleep(10)
            print(now)

        if next_call_time == "":
            continue

        # Calculate the time remaining until the next function call
        time_remaining = (next_call_time - now).total_seconds()

        # If the next function call is less than 5 minutes away, don't sleep
        if time_remaining <= 300:
            continue

        # Otherwise, sleep until 5 minutes before the next function call
        print(
            f"Next function call at {next_call_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ({timezone_name}). Sleeping for {time_remaining - 300} seconds...")
        time.sleep(time_remaining - 300)


main_function(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
