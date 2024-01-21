import dotenv
import os

dotenv.load_dotenv()

SUBSCRIPTION_KEY = os.environ["BING_SEARCH_V7_SUBSCRIPTION_KEY"]
ENDPOINT = os.environ["BING_SEARCH_V7_ENDPOINT"]
HEADERS = {"Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY}
