import React, { useCallback, useEffect, useRef, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  Panel,
  ReactFlowProvider,
  useReactFlow,
} from "reactflow";
import Dagre from "@dagrejs/dagre";
import { shallow } from "zustand/shallow";

import "reactflow/dist/style.css";

import useStore, { EditorState } from "./store";
import ContextNode from "./ContextNode";
import { socket } from "./socket";
import { useDebouncedCallback } from "use-debounce";
import { getOutgoers } from "reactflow";

const nodeTypes = {
  contextNode: ContextNode,
};

const g = new Dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes, edges, options) => {
  g.setGraph({ rankdir: options.direction });

  edges.forEach((edge) => g.setEdge(edge.source, edge.target));
  nodes.forEach((node) => g.setNode(node.id, node));

  Dagre.layout(g);

  return {
    nodes: nodes.map((node) => {
      const { x, y } = g.node(node.id);

      return { ...node, position: { x, y } };
    }),
    edges,
  };
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
    setEdges,
    setNodes,
  } = useStore();
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [isConnected, setIsConnected] = useState(socket.connected);
  const { fitView } = useReactFlow();

  const onLayout = useDebouncedCallback((direction) => {
    let { edges, nodes } = useStore.getState();
    const layouted = getLayoutedElements(nodes, edges, { direction });

    setNodes([...layouted.nodes]);
    setEdges([...layouted.edges]);

    window.requestAnimationFrame(() => {
      fitView();
    });
  }, 100);

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
            x: 100,
            y: 100,
          },
          data: dat,
        },
        par_id
      );
      onLayout("LR");
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
