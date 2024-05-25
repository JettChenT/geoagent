from yt_dlp import YoutubeDL
from yt_dlp.extractor.twitter import TwitterIE
import requests
import re
from ..utils import image_to_prompt, Session, enforce_image, find_valid_loc
from .vidutils import extract_frames_ffmpeg

def twitter_best_quality_url(url: str) -> str:
    """
    some twitter image URLs point to a less-than best quality
    this returns the URL pointing to the highest (original) quality
    source: bellingcat auto-archiver
    """
    return re.sub(r"name=(\w+)", "name=orig", url, 1)

def url_is_twitter(url: str) -> bool:
    return "twitter.com" in url or "x.com" in url

def choose_variant(variants):
    variant, width, height = None, 0, 0
    for var in variants:
        if var.get("content_type", "") == "video/mp4":
            width_height = re.search(r"\/(\d+)x(\d+)\/", var["url"])
            if width_height:
                w, h = int(width_height[1]), int(width_height[2])
                if w > width or h > height:
                    width, height = w, h
                    variant = var
        else:
            variant = var if not variant else variant
    return variant

def from_twitter(session: Session, url: str) -> str:
    downloader = YoutubeDL()
    tie = TwitterIE(downloader)
    twid = tie._match_valid_url(url).group("id")
    tweet = tie._extract_status(twid)
    pmpt = f"Tweet Content: {tweet['full_text']}"
    if not tweet.get("entities", {}).get("media", []):
        return pmpt
    for media in tweet["entities"]["media"]:
        if media["type"] == "photo":
            im_loc = enforce_image(media["media_url_https"], session)
            pmpt += image_to_prompt(im_loc, session)
            session.update_info({"image_loc": str(im_loc)})
        elif media["type"] == "video":
            variant = choose_variant(media["video_info"]["variants"])
            tar_url = variant["url"]
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36'
            }
            r = requests.get(tar_url, headers=headers)
            to_filename = find_valid_loc(session, "vid_", ".mp4")
            with open(to_filename, "wb") as f:
                f.write(r.content)
            frame_loc = find_valid_loc(session, "frame_", ".png")
            frames = extract_frames_ffmpeg(to_filename, frame_loc)
            for frame in frames:
                im_loc = enforce_image(frame, session)
                pmpt += image_to_prompt(im_loc, session)
    session.update_info({
        "content_type": "tweet",
        "tweet_id": twid,
    })
    return pmpt

if __name__ == "__main__":
    from ..utils import setup_session
    ses = Session()
    setup_session(ses)
    print(from_twitter(ses, "https://twitter.com/OSINTNic/status/1744307938074722320"))

