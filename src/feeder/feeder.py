from ..utils import Session, image_to_prompt
from .twitter import from_twitter, url_is_twitter

def process_url(session: Session, url: str) -> str:
    if url_is_twitter(url):
        return from_twitter(session, url)
    raise NotImplementedError(f"URL {url} not supported")

if __name__ == "__main__":
    print(process_url(Session(), "https://twitter.com/Jaaneek/status/1775316981794656471"))

