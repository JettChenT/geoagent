import { URL } from "./socket";
export function downloadImage(dataUrl) {
  const a = document.createElement("a");

  a.setAttribute("download", "reactflow.png");
  a.setAttribute("href", dataUrl);
  a.click();
}

export const proc_img_url = (url: string) => {
  if (url.startsWith("http")) {
    return url;
  }
  if (!url.startsWith("/")) {
    url = "/" + url;
  }
  return URL + url;
};

export const imageWidth = 2048;
export const imageHeight = 2048;
