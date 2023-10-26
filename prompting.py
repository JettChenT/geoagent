INITIAL_PROMPT = """
The above is a picture of a location in the world, note the important features in it.
Write open streetmap queires to find these locations.
In your queries, make use of OSM's proximity features, and use regular expressions over exact string matches, and always use them
when you're not exactly sure of the specific wordings of signs etc.
Finally, output a single query to find the image's likely location, including the headers and bounding boxes, etc.
If you are able to guess the general region of the image. Please include that in the OSM query.

A good example of a query would be:

```
area["name"~"United States"];
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