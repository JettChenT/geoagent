import useStore from "./store";
import JsonView from "react18-json-view";
import { URL } from "./socket";

export const proc_img_url = (url: string) => {
  if (url.startsWith("http")) {
    return url;
  }
  if (!url.startsWith("/")) {
    url = "/" + url;
  }
  return URL + url;
};

function InfoDisplay() {
  const { currentSession, sessionsInfo, globalInfo } = useStore();
  return (
    <>
      <div className="w-full mb-4 overflow-auto bg-slate-300 bg-opacity-20 rounded-xl p-2">
        <div className="text-lg font-bold mb-2">Session Info:</div>
        <JsonView
          src={
            currentSession === "all_sessions"
              ? sessionsInfo
              : sessionsInfo[currentSession]
          }
          collapsed={true}
        />
      </div>
      <div className="w-full mb-4 overflow-auto bg-slate-300 bg-opacity-20 rounded-xl p-2">
        <div className="text-lg font-bold my-2">Global Info:</div>
        <JsonView src={globalInfo} collapsed={true} />
      </div>
    </>
  );
}

export default InfoDisplay;
