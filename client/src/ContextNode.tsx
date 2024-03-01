import { useCallback, useState, useEffect } from "react";
import {
  Handle,
  NodeProps,
  Position,
  getIncomers,
  getRectOfNodes,
  getTransformForBounds,
} from "reactflow";
import useStore, { EditorState } from "./store";
import { toPng } from "html-to-image";
import { imageHeight, imageWidth } from "./utils";
import JsonView from "react18-json-view";

type Message = {
  message: string;
  role: null | "user" | "assistant" | "system";
};

type AgentAction = {
  type: "AgentAction";
  tool: string;
  tool_input: string;
};

type AgentFinish = {
  type: "AgentFinish";
  return_values: any;
};

export type ContextData = {
  cur_messages: Message[];
  observation: string | any;
  transition: AgentAction | AgentFinish | null;
  lats_data: any;
  auxiliary: any;
  state:
    | "normal"
    | "running"
    | "expanding"
    | "evaluating"
    | "rollout"
    | "success";
};

export const proc_incoming = (incoming: any): ContextData => {
  let transition = null;
  switch (incoming.transition.type) {
    case "AgentAction":
      transition = {
        type: "AgentAction",
        tool: incoming.transition.tool,
        tool_input: incoming.transition.tool_input,
      };
      break;
    case "AgentFinish":
      transition = {
        type: "AgentFinish",
        return_values: incoming.transition.return_values,
      };
      break;
  }
  return {
    cur_messages: incoming.cur_messages,
    observation: incoming.observation,
    transition: incoming.transition,
    auxiliary: incoming.auxiliary,
    state: incoming.state,
    lats_data: incoming.lats_data,
  };
};

export default function ContextNode({ id, data }: NodeProps<ContextData>) {
  const lastMessage =
    data.cur_messages.length > 0
      ? data.cur_messages[data.cur_messages.length - 1].message
      : "No messages";

  // Determine the background color and state text based on the state
  const [bgColor, setBgColor] = useState("bg-white");
  useEffect(() => {
    switch (data.state) {
      case "running":
        setBgColor("bg-blue-100 animate-pulse");
        break;
      case "evaluating":
        setBgColor("bg-yellow-100 animate-pulse");
        break;
      case "success":
        setBgColor("bg-green-100");
        break;
      default:
        setBgColor("bg-white");
    }
  }, [data.state]);

  const stext = (st) => {
    switch (st) {
      case "running":
        return "🔵 Running";
      case "expanding":
        return "🟢 Expanding";
      case "evaluating":
        return "🟡 Evaluating";
      case "rollout":
        return "🟣 Rollout";
      case "success":
        return "🟢 Success";
      default:
        return `⚪ ${st}`;
    }
  };

  return (
    <div
      className={`react-flow__node-default w-64 rounded shadow nowheel overflow-auto ${bgColor} select-text nodrag`}
    >
      <div className="p-2 space-y-1">
        <div className="text-lg font-bold text-left">Context</div>
        <div className="text-sm text-left" style={{ userSelect: "text" }}>
          <span className="font-bold">ID:</span>
          <span className="text-gray-500 font-mono"> {id}</span>
        </div>
        <div className="text-sm text-left" style={{ userSelect: "text" }}>
          <span className="font-bold">Last Message:</span>
          <div className="text-gray-500 font-mono overflow-auto max-h-16">
            {lastMessage}
          </div>
        </div>
        <div className="text-sm text-left" style={{ userSelect: "text" }}>
          <span className="font-bold">Observation:</span>
          <div className="text-gray-500 font-mono overflow-auto max-h-16">
            {data.observation}
          </div>
        </div>
        <div className="text-sm text-left" style={{ userSelect: "text" }}>
          <span className="font-bold">Transition: </span>
          {data.transition && "tool" in data.transition ? (
            <span>
              <span className="text-blue-500 font-mono">
                {data.transition.tool}
              </span>
              <span className="text-gray-500 font-mono">
                {" "}
                ({data.transition.tool_input})
              </span>
            </span>
          ) : (
            <span className="text-gray-500 font-mono">
              {" "}
              {data.transition["type"]}{" "}
            </span>
          )}
        </div>
        <div className="text-sm text-left" style={{ userSelect: "text" }}>
          <span className="font-bold">Auxiliary:</span>
          <div className="text-gray-500 font-mono overflow-auto max-h-16">
            {typeof data.auxiliary === "object" ? (
              <JsonView src={data.auxiliary} collapsed={true} />
            ) : (
              data.auxiliary
            )}
          </div>
        </div>
        <div className="text-sm text-left" style={{ userSelect: "text" }}>
          <span className="font-bold">Lats Data:</span>
          <div className="text-gray-500 font-mono overflow-auto max-h-16">
            {typeof data.lats_data === "object" ? (
              <JsonView src={data.lats_data} collapsed={true} />
            ) : (
              data.lats_data
            )}
          </div>
        </div>
        <div className="text-sm text-left" style={{ userSelect: "text" }}>
          <span className="font-bold">State:</span>
          <span className="font-mono"> {stext(data.state)}</span>
        </div>
      </div>
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </div>
  );
}
