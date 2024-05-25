import html
from auto_archiver.archivers.telegram_archiver import TelegramArchiver, Metadata
from auto_archiver.core import ArchivingContext
from bs4 import BeautifulSoup
from ..utils import image_to_prompt, Session, enforce_image, find_valid_loc, setup_session
from .vidutils import extract_frames_ffmpeg

def utl_is_telegram(url: str) -> bool:
    return "t.me" in url

def from_telegram(session: Session, url: str) -> str:
    ArchivingContext.set_tmp_dir(f"run/{session.id}")
    archiver = TelegramArchiver({})
    res = archiver.download(Metadata().set_url(url))
    webpage = html.unescape(str(res.get("content")))
    soup = BeautifulSoup(webpage, "html.parser")
    text = (soup.find("div", class_="tgme_widget_message_text")
            .get_text()
            .encode()
            .decode("unicode-escape")
            .encode("latin1")
            .decode("utf-8"))
    res_pmpt = f"Telegram Message: {text}"
    images = []
    for media in res.get_all_media():
        if media.is_image():
            im_loc = enforce_image(media.filename, session)
            res_pmpt += image_to_prompt(im_loc, session)
            images.append(str(im_loc))
        elif media.is_video():
            res_pmpt += f"Video: {media.filename}, extracted frames: "
            extracted = extract_frames_ffmpeg(media.filename, f"run/{session.id}")
            for frame in extracted:
                im_loc = enforce_image(frame, session)
                res_pmpt += image_to_prompt(im_loc, session)
                images.append(str(im_loc))
    session.update_info({
        "images": images,
        "content_type": "telegram",
        "telegram_id": "/".join(url.split("/")[-2:])
    })
    return res_pmpt

if __name__ == "__main__":
    ses = Session()
    setup_session(ses)
    print(from_telegram(ses, "https://t.me/truexanewsua/74039"))
