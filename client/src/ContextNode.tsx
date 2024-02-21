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
  id: string;
  cur_messages: Message[];
  observation: string | any;
  transition: AgentAction | AgentFinish | null;
  auxiliary: any;
};

export default function ContextNode({ id, data }: NodeProps<ContextData>) {
  return (
    <div className="react-flow__node-default w-56 min-h-48 bg-white rounded shadow nowheel">
      <div className="p-2">
        <div className="text-lg font-bold">Context</div>
        <div className="text-sm text-gray-500">{id}</div>
        <div className="text-sm text-gray-500">
          Messages: {data.cur_messages.length}
        </div>
        <div className="text-sm text-gray-500">
          Observation: {data.observation}
        </div>
        {data.transition && "tool" in data.transition ? (
          <div className="text-sm text-gray-500">
            Transition: {data.transition.tool}
          </div>
        ) : (
          <div className="text-sm text-gray-500">Transition Finished</div>
        )}
        <div className="text-sm text-gray-500">Auxiliary: {data.auxiliary}</div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
