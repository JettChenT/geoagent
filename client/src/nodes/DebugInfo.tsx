import JsonView from "react18-json-view";
import { ContextData } from "./ContextNode";

export default function DebugInfo({ data }: { data: ContextData }) {
  const lastMessage =
    data.cur_messages.length > 0
      ? data.cur_messages[data.cur_messages.length - 1].message
      : "No messages";
  return (
    <>
      <div
        className="text-sm text-left nodrag"
        style={{ userSelect: "text", cursor: "text" }}
      >
        <span className="font-bold">Session ID:</span>
        <span className="text-gray-500 font-mono"> {data.session_id}</span>
      </div>
      <div
        className="text-sm text-left nodrag"
        style={{ userSelect: "text", cursor: "text" }}
      >
        <span className="font-bold">Last Message:</span>
        <div className="text-gray-500 font-mono overflow-auto max-h-16">
          {lastMessage}
        </div>
        <div
          className="text-sm text-left nodrag"
          style={{ userSelect: "text", cursor: "text" }}
        >
          <span className="font-bold">Auxiliary:</span>
          <div className="text-gray-500 font-mono overflow-auto max-h-16">
            {typeof data.auxiliary === "object" ? (
              <JsonView src={data.auxiliary} collapsed={true} />
            ) : (
              data.auxiliary
            )}
          </div>
        </div>
        <div
          className="text-sm text-left nodrag"
          style={{ userSelect: "text", cursor: "text" }}
        >
          <span className="font-bold">Lats Data:</span>
          <div className="text-gray-500 font-mono overflow-auto max-h-16">
            {typeof data.lats_data === "object" ? (
              <JsonView src={data.lats_data} collapsed={true} />
            ) : (
              data.lats_data
            )}
          </div>
        </div>
      </div>
    </>
  );
}
