import React, { useEffect, useRef, useState } from "react";
import ReactFlow, { Background, Controls, Panel } from "reactflow";
import { shallow } from "zustand/shallow";

import "reactflow/dist/style.css";

import useStore, { EditorState } from "./store";
import ContextNode from "./ContextNode";
import { socket } from "./socket";
import { getOutgoers } from "reactflow";

const nodeTypes = {
  contextNode: ContextNode,
};

function App() {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    createNode,
    createChildNode,
    updateContextData,
    getNodeById,
  } = useStore();
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [isConnected, setIsConnected] = useState(socket.connected);

  useEffect(() => {
    socket.on("connect", () => {
      setIsConnected(true);
    });
    socket.on("disconnect", () => {
      setIsConnected(false);
    });
    socket.on("root_node", (node_id, dat) => {
      console.log("root_node", node_id, dat);
      createNode({
        id: node_id,
        type: "contextNode",
        position: { x: 100, y: 100 },
        data: dat,
      });
    });
    socket.on("add_node", (par_id, node_id, dat) => {
      console.log("add_node", par_id, node_id, dat);
      let par_node = getNodeById(par_id);
      createChildNode(
        {
          id: node_id,
          type: "contextNode",
          position: {
            x: par_node.position.x + 100,
            y:
              par_node.position.y +
              100 * getOutgoers(par_node, nodes, edges).length,
          },
          data: dat,
        },
        par_id
      );
    });
    socket.on("update_node", (node_id, dat) => {
      updateContextData(node_id, dat);
    });
  }, []);

  return (
    <div
      style={{ width: "100%", height: "100vh" }}
      className="reactflow-wrapper"
      ref={reactFlowWrapper}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onInit={setReactFlowInstance}
        nodeTypes={nodeTypes}
        fitView
      >
        <Panel position="top-right" className="space-x-4">
          <div>
            {isConnected ? (
              <div className="text-green-500">🟢 Connected</div>
            ) : (
              <div className="text-red-500">🔴 Not Connected</div>
            )}
          </div>
        </Panel>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}

export default App;
