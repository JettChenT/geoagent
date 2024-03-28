import dotenv
import os
from ... import config

SUBSCRIPTION_KEY = os.environ["BING_SEARCH_V7_SUBSCRIPTION_KEY"]
ENDPOINT = os.environ["BING_SEARCH_V7_ENDPOINT"]
HEADERS = {"Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY}
