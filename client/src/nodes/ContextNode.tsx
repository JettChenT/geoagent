import { useCallback, useState, useEffect } from "react";
import {
  Handle,
  NodeProps,
  Position,
  getIncomers,
  getRectOfNodes,
  getTransformForBounds,
} from "reactflow";
import useStore, { EditorState } from "../store";
import DebugInfo from "./DebugInfo";
import MediaInfo from "./MediaInfo";
import TransitionInfo from "./TransitionInfo";

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
  session_id: string | null;
  is_root?: boolean;
  state:
    | "normal"
    | "running"
    | "expanding"
    | "evaluating"
    | "rollout"
    | "success"
    | "reflecting";
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
    session_id: null,
  };
};

const stext = (st) => {
  switch (st) {
    case "running":
      return "🏃 Running";
    case "expanding":
      return "📈 Expanding";
    case "evaluating":
      return "🔍 Evaluating";
    case "rollout":
      return "🚀 Rollout";
    case "success":
      return "✅ Success";
    case "reflecting":
      return "🤔 Reflecting";
    default:
      return `⚪ ${st}`;
  }
};

export default function ContextNode({ id, data }: NodeProps<ContextData>) {
  // Determine the background color and state text based on the state
  const { sessionsInfo, debug } = useStore();
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
      case "reflecting":
        setBgColor("bg-yellow-100");
        break;
      case "expanding":
        setBgColor("bg-orange-100 animate-pulse");
        break;
      default:
        setBgColor("bg-white");
    }
  }, [data.state]);

  return (
    <div
      className={`react-flow__node-default ${
        data.is_root ? "w-96" : "w-64"
      } rounded-md shadow nowheel overflow-auto ${bgColor} select-text`}
    >
      <div className="p-2 space-y-1">
        <div className="text-lg font-bold text-left">
          Context{" "}
          <span className="text-gray-500 font-mono">{data.session_id}</span>
        </div>
        <MediaInfo data={data} sessionsInfo={sessionsInfo} />
        <TransitionInfo transition={data.transition} />
        {debug && <DebugInfo data={data} />}
        <div
          className="text-sm text-left nodrag"
          style={{ userSelect: "text", cursor: "text" }}
        >
          <span className="font-bold">State:</span>
          <span className="font-mono"> {stext(data.state)}</span>
        </div>
      </div>
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </div>
  );
}
