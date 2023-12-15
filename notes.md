# Potential Strategies for Geolocation

- Cluster of OSM feats and their positions
- Triangulation: https://github.com/Xetnus/osm-finder
- Features in proximity to each other https://github.com/bellingcat/osm-search
- OSM querying techniques: 


## Some Sub-Problems
- OSM Feature Extraction
- Converting Feature Extraction to OSM Query
- Spacial ordering & reasoning
  - Does simple proximity work?
- Integration with OSM database & the internet
- Improving Overpass turbo querying itself to be more probabilistic

## Possible Pipelines
- End-To-End: We provide a bunch of examples, VLLM is smart enough to generate a valid OSM query
- Fully-Agent based: Not only do we provide OSM interpreter, we provide Nomantim, Google reverse image search, overpass documentation via function calling, etc
- Fine-Tuning: We finetune VLLM to be able to better craft OSM queries
- Feature Extraction: We use VLLM to extract features, then use a different model to generate OSM queries

## Useful Resources
https://osm-queries.ldodds.com/

### Tools
- [ x ] Nomantim
- [ x ] Overpass Turbo
- [ ] Bing: text & image search
- [ ] Open Streetmap Wiki

### Features
- When creating the chain, also use images for feedback loop