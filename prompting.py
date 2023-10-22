INITIAL_PROMPT = """
The above is a picture of a location in the world, note the important features in it.
Write open streetmap queires to find these locations.
In your queries, make use of OSM's proximity features, and use regular expressions over exact string matches.
Finally, output a single query to find the image's likely location, including the headers and bounding boxes, etc.

A good example of a query would be:

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
"""

DELTA_TOO_MUCH = """
There are too many results for the given query. 
Modify the query to narrow down the search area. Such as lowering the proximity threshold.
Finally, output the entire modified OSM query.
"""

DELTA_TOO_LITTLE = """
There are too few results for the given query.
Modify the query to expand the search area. Such as increasing the proximity threshold.
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