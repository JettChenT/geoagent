import useStore from "../store";
import JsonView from "react18-json-view";

function InfoDisplay() {
  const { currentSession, sessionsInfo, globalInfo } = useStore();
  return (
    <>
      <div className="w-full mb-4 overflow-auto bg-slate-300 bg-opacity-20 rounded-md p-2">
        <div className="text-lg font-bold mb-1">Session Info</div>
        <JsonView
          src={
            currentSession === "all_sessions"
              ? sessionsInfo
              : sessionsInfo[currentSession]
          }
          collapsed={true}
        />
      </div>
      <div className="w-full mb-4 overflow-auto bg-slate-300 bg-opacity-20 rounded-md p-2">
        <div className="text-lg font-bold mb-1">Global Info</div>
        <JsonView src={globalInfo} collapsed={true} />
      </div>
    </>
  );
}

export default InfoDisplay;
