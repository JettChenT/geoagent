SYSTEM_PROMPT = """
You are a helpful assistant who helps us geolocate images by writing overpass turbo queries.
"""

TOOL_PROMPT = """
The above is a picture of a location in the world, note the important features in it.
Use the tools you have to find the precise location of the place.
"""

INITIAL_PROMPT = """
The you will receive a picture of a location in the world, note the important features in it.
Write open streetmap queires to find these locations.
In your queries, make use of OSM's proximity features, and use regular expressions over exact string matches, and always use them
when you're not exactly sure of the specific wordings of signs etc.
Finally, output a single query to find the image's likely location, including the headers and bounding boxes, etc.
If you are able to guess the general region of the image. Please include that in the OSM query.

A good example of a query would be:

```
area["name"~".*Washington.*"];
way["name"~"Monroe.*St.*NW"](area) -> .mainway;

(
  nwr(around.mainway:500)["name"~"Korean.*Steak.*House"];

  // Find nearby businesses with CA branding
  nwr(around.mainway:500)["name"~"^CA.*"];
  
  // Look for a sign with the words "Do not block"
  node(around.mainway:500)["traffic_sign"~"Do not block"];
);

out center;
```
"""

DELTA_TOO_MUCH = """
There are too many results for the given query. 
Modify the query to narrow down the search area. Such as lowering the proximity threshold. Or making the text searchings more specific.
Also consider changing or narrowing the search area if present.
Finally, output the entire modified OSM query.
"""

DELTA_TOO_LITTLE = """
There are too few results for the given query.
Consider making the text queries less specific/restrictive. Consider switching to less strict regular expressions, 
or not using as many tag constraints, or removing some constraints altogether.
Also consider using union (...) statements to include more acceptable places.
Also consider widening or removing the current search area.
Finally, output the entire modified OSM query.
"""

SAMPLE_OSM = """
To search for a location that satisfies all the conditions mentioned, you would use a compound query in the Overpass API, ensuring that all features are in proximity to each other. Here's how you can combine the mentioned queries:

``` 
[out:json];
// Define the main street as the central reference point
way["name"~"Monroe.*St.*NW"];
> -> .mainstreet;

// Find a nearby Korean Steak House
nwr(around.mainstreet:500)["name"~"Korean.*Steak.*House"] -> .koreansteakhouse;

// Find nearby businesses with CA branding
nwr(around.mainstreet:500)["name"~"^CA.*"] -> .cabrand;

// Look for a sign with the words "Do not block"
node(around.mainstreet:500)["traffic_sign"~"Do not block"] -> .sign;

// Combine results and output
(.mainstreet; .koreansteakhouse; .cabrand; .sign;);
out center;
```

The logic here is to first identify the main street (Monroe St NW in this case). From there, we search for the other features in proximity to this street. This combined query is likely to return a concise area with all the mentioned features. If you run this query on Overpass Turbo, it will highlight all areas that fit the criteria, allowing you to hone in on the exact location.

**Summary**: The provided query combines all the individual features from the image into a single search on OpenStreetMap using the Overpass API, focusing on Monroe St NW and searching for other features in its proximity.
"""


LLAVA_SYS_PROMPT = """
A chat between a curious human and an artificial intelligence assistant who helps the human do geolocations by writing overpass turbo queries. 
The assitant outputs objective responses in markdown. 
First describe the image. Then, output the openstreetmap query.
The Open Streetmap queries should be contained in code blocks.
Do not output the results of the query execution. Always make sure that the last code block is the OSM query.
"""

NO_CODEBLOCK = """
No markdown codeblocks could be found in the response. Please make sure that the last code block is the OSM query.
"""

TOO_SPREAD = """
The results returned in the OSM query are too spread out, please narrow down the search area.
Such as lowering the proximity threshold. Or making the text searchings more specific.
Also consider changing or narrowing the search area if present.
Finally, output the entire modified OSM query.
"""

INITIAL_REACT_PROMPT = """
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question1: The overall guideline to what you are going to do
Thought1: Think about what you should do
Action1: the action to take, should be one of [{tool_names}]
Action Input1: the input to the action1 as arguments. If there are multiple arguments, separate them with commas. Note that the arguments should be in the same order as the function signature, and that the arguments are not named.
Observation1 : the result of the action1
Analyze1: Analyze the results of action1
Thought2: Think about what you should do based on analyze1
Action2: the action to take, should be one of [{tool_names}]
Action Input2: the input to the action2
Observation2: the result of the action2
Analyze2: Analyze the results of action2
Thought3: So on... In this case you have realized that you have found the location of the image. If you have not found the location of the image, you can continue to use the tools to find the location of the image.
Final Answer: The location of the image is ... The coordinates are ... Remember to always output the coordinate. If you do not have the coordinate, do not consider the task finished.

Remember to output either the final answer or an action at each step, never both.
Begin!

Question1: {input}
Thought1: """

VALUE_PROMPT = """
Reflect on the current trajectory. Think about whether the current trajectory is promising on its path toward a successful geolocation.
Finally, in a separate line, output a number in the range [1, 10] that represents how promising the current trajectory is. 
Remember to output the number and the number only in the final line.
"""

REWARD_PROMPT = """
The current trajectory has reached a terminal state, returning a coordinate.
Make sure that a coordinate is returned, and that it is based on solid evidence.
An address would not suffice.
Reflect on the current trajectory, and output a number in the range [0,10] that represents 
whether a successful geolocation has been performed. 
0 could represent an unsuccessful geolocation in which the coordinates are not returned or are based on pure speculation;
10 could represent a successful geolocation in which the coordinates are returned and are based on solid evidence,
namely the coordinate is based on an external source.
Remember to output a 10 if and only if a specific coordinate is returned, and the coordinate is based on solid evidence
from an external observation.
A 10 should have imagery match, satellite imagery match, or some text in the original image that matches with 
observation.
If you are not sure, output a number in the middle of the range.
An approximate coordinate would not suffice, and would be considered a number in the middle of the range.
Think step by step.
Remember to output the number and the number only in the final line.
"""

MULTI_EVALUATION_PROMPT = """
You were given {n} choices over what is the next step to take for our investigation.
For each choice, evaluate the validity of the choice, think about whether the choice is promising on its path toward a successful geolocation.
Finally, in {n} separate lines, output a number in the range [1, 10] that represents how promising each choice is.
The outputs should be in the same order as the choices, and in the format of `branch <choice_number>: <output>`.
"""

REFLECTION_PROMPT = """
First summarize what you did in the current trajectory.
Then, in a few sentences reflect on the current trajectory. 
Provide advice to other agents doing this investigation regarding what to avoid, what to do better, and what has been tried etc.
"""