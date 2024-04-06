import html
from auto_archiver.archivers.telegram_archiver import TelegramArchiver, Metadata
from auto_archiver.core import ArchivingContext
from bs4 import BeautifulSoup
from ..utils import image_to_prompt, Session, enforce_image, find_valid_loc, setup_session
import subprocess
import os

def utl_is_telegram(url: str) -> bool:
    return "t.me" in url

def extract_frames_ffmpeg(input_video_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    command = [
        'ffmpeg',
        '-i', input_video_path,
        '-vf', 'fps=1',
        os.path.join(output_dir, 'frame_%03d.png')
    ]
    
    try:
        subprocess.run(command, check=True)
        print(f"Frames extracted and saved to {output_dir} at one frame per second")
        # Assuming the duration of the video is not known, 
        # and thus the exact number of frames to be extracted is not known beforehand.
        # Listing the directory content to return the paths of extracted frames.
        extracted_frames = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if str(f).startswith('frame_')]
        return extracted_frames
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        return []

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
