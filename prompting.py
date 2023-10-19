INITIAL_PROMPT = """
The above is a picture of a location in the world, note the important features in it.
Write open streetmap queires to find these locations.
In your queries, make use of OSM's proximity features, and use regular expressions over exact string matches.
Finally, output a single query to find the image's likely location, including the headers and bounding boxes, etc.

A good example of a query would be:

```
[out:json];
// Define the main street as the central reference point
way["name"~"Monroe.*St.*NW"]({{bbox}});
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