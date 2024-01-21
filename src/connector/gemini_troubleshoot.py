"""
At the command line, only need to run once to install the package via pip:

$ pip install google-generativeai
"""
import os
from pathlib import Path
import google.generativeai as genai
import dotenv

dotenv.load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Set up the model
generation_config = {
  "temperature": 0.4,
  "top_p": 1,
  "top_k": 32,
  "max_output_tokens": 4096,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  }
]

model = genai.GenerativeModel(model_name="gemini-pro-vision",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

# Validate that an image is present
img_loc = "./images/phoenix_taylor.png"
if not (img := Path(img_loc)).exists():
  raise FileNotFoundError(f"Could not find image: {img}")

image_parts = [
  {
    "mime_type": "image/png",
    "data": Path(img_loc).read_bytes()
  },
]

prompt_parts = [
  image_parts[0],
  "\nAnswer the following questions as best you can. You have access to the following tools:\n\nOverpass Turbo: Overpass Turbo(q: str) -> Any - Skims through the query string for a chunk of OSM Query, executes the query, and returns the resulting\n  lat long pairs. For example, a valid input would be:\n  '''\n  area[\"name\"~\".*Washington.*\"];\nway[\"name\"~\"Monroe.*St.*NW\"](area) -> .mainway;\n\n(\n nwr(around.mainway:500)[\"name\"~\"Korean.*Steak.*House\"];\n\n // Find nearby businesses with CA branding\n nwr(around.mainway:500)[\"name\"~\"^CA.*\"];\n\n // Look for a sign with the words \"Do not block\"\n node(around.mainway:500)[\"traffic_sign\"~\"Do not block\"];\n);\n\nout center;\n  '''\n  Do not include a codeblock in function call. Jus the raw query.\n  :param q: The overpass turbo query you are running. ALWAYS pass in a full overpass turbo query.\n  :return: list of tuples if valid, otherwise returns a string representing the next prompt\nOSM Wiki Search: OSM Wiki Search(query: str) -> str - Searches the OSM Wiki for a query. Use this if you are not sure about\n  specific features or tags that you would use for your later Overpass Turbo Query.\n  :param query:\n  :return:\nNomantim Geocoder: Nomantim Geocoder(query: str) -> str - Searches the OSM Wiki for a query. Use this if you are not sure about\n  what are the Open Streetmap names for a general location.\n  Priorize using this if you need an area name such as `United States` or `Washington`.\n  Prefer not to use this if you are looking up a specific string or name, for that use Overpass Turbo.\n  :param query: A single area or location you want to geocode for.\n  :return:\n\nUse the following format:\n\nQuestion1: The overall guideline to what you are going to do\nThought1: Think about what you should do\nAction1: the action to take, should be one of [Overpass Turbo, OSM Wiki Search, Nomantim Geocoder]\nAction Input1: the input to the action1\nObservation1 : the result of the action1\nAnalyze1: Analyze the results of action1\nThought2: Think about what you should do based on analyze1\nAction2: the action to take, should be one of [Overpass Turbo, OSM Wiki Search, Nomantim Geocoder]\nAction Input2: the input to the action2\nObservation2: the result of the action2\nAnalyze2: Analyze the results of action2\nThought3: So on...\n\nBegin!\n\nQuestion1: Where is this image located?\nThought1: ",
]

response = model.generate_content(prompt_parts)
print(response.text)