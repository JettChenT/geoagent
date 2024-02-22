import { useCallback, useState } from "react";
import { Handle, NodeProps, Position, getIncomers } from "reactflow";
import useStore, { EditorState } from "./store";

type Message = {
  message: string;
  role: null | "user" | "assistant" | "system";
};

type AgentAction = {
  tool: string;
  tool_input: string;
};

type AgentFinish = {
  return_values: any;
};

export type ContextData = {
  cur_messages: Message[];
  observation: string | any;
  transition: AgentAction | AgentFinish | null;
  auxiliary: any;
};

export default function ContextNode({ id, data }: NodeProps<ContextData>) {
  const lastMessage =
    data.cur_messages.length > 0
      ? data.cur_messages[data.cur_messages.length - 1].message
      : "No messages";

  return (
    <div className="react-flow__node-default w-56 bg-white rounded shadow nowheel overflow-auto">
      <div className="p-2 space-y-1">
        <div className="text-lg font-bold text-left">Context</div>
        <div className="text-sm text-left">
          <span className="font-bold">ID:</span>
          <span className="text-gray-500 font-mono"> {id}</span>
        </div>
        <div className="text-sm text-left">
          <span className="font-bold">Last Message:</span>
          <div className="text-gray-500 font-mono overflow-auto max-h-16">
            {lastMessage}
          </div>
        </div>
        <div className="text-sm text-left">
          <span className="font-bold">Observation:</span>
          <span className="text-gray-500 font-mono"> {data.observation}</span>
        </div>
        <div className="text-sm text-left">
          <span className="font-bold">Transition:</span>
          {data.transition && "tool" in data.transition ? (
            <span className="text-gray-500 font-mono">
              {data.transition.tool}
            </span>
          ) : (
            <span className="text-gray-500 font-mono"> Finished</span>
          )}
        </div>
        <div className="text-sm text-left">
          <span className="font-bold">Auxiliary:</span>
          <div className="text-gray-500 font-mono overflow-auto max-h-16">
            {JSON.stringify(data.auxiliary)}
          </div>
        </div>
      </div>
      <Handle type="source" position={Position.Right} />
      <Handle type="target" position={Position.Left} />
    </div>
  );
}
