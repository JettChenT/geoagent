# geolocation

Project structure:

```
src/ - python codebase on the agent system
client/ - react+vite frontend
geoeval/ - WIP evaluation dataset
```

## Setup

Note: requirements.txt is likely not up to date.

```
pip install -r requirements.txt
```

Then, set `.env` file as according to `.env.example`.

## Running the Agent

Against an image:

`just agent <image_path>`

Running the server:

`just server`

## Running the Client

Note: the server should be running in background.

```
cd client
bun i
bun dev
```
