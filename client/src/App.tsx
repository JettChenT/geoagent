import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
  useMemo,
} from "react";
import ReactFlow, {
  Background,
  Controls,
  Panel,
  ReactFlowProvider,
  getNodesBounds,
  getRectOfNodes,
  getTransformForBounds,
  getViewportForBounds,
  useUpdateNodeInternals,
  useReactFlow,
  MiniMap,
} from "reactflow";
import Dagre from "@dagrejs/dagre";
import { shallow } from "zustand/shallow";

import "reactflow/dist/style.css";
import "react18-json-view/src/style.css";

import useStore, { EditorState } from "./store";
import ContextNode, { proc_incoming } from "./nodes/ContextNode";
import { socket } from "./socket";
import { useDebouncedCallback } from "use-debounce";
import { downloadImage, imageHeight, imageWidth } from "./utils";
import { toPng } from "html-to-image";
import InfoDisplay from "./panel/InfoDisplay";
import FileUpload from "./panel/FileUpload";
import SocialImport from "./panel/SocialImport";
import { Button } from "./components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChevronDownSquareIcon, Image } from "lucide-react";
import ConfigPanel from "./panel/ConfigPanel";

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

      return {
        ...node,
        position: { x: x - node.width / 2, y: y - node.height / 2 },
      };
    }),
    edges,
  };
};
function App() {
  const {
    nodes,
    edges,
    globalInfo,
    sessionsInfo,
    debug,
    onNodesChange,
    onEdgesChange,
    onConnect,
    createNode,
    createChildNode,
    updateContextData,
    getNodeById,
    setEdges,
    setNodes,
    clearAll,
    setGlobalInfo,
    setGlobalInfoKey,
    setSessionId,
    currentSession,
    setCurrentSession,
    setSessionsInfoKey,
    setSessionInfo,
  } = useStore();
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);
  const [isConnected, setIsConnected] = useState(socket.connected);
  const { fitView } = useReactFlow();
  const updateNodeInternals = useUpdateNodeInternals();

  const onLayout = useDebouncedCallback(() => {
    let { edges, nodes } = useStore.getState();
    for (const node of nodes) {
      updateNodeInternals(node.id);
    }
    setTimeout(() => {
      let new_nodes = useStore.getState().nodes;
      const layouted = getLayoutedElements(new_nodes, edges, {
        direction: "LR",
      });

      setNodes([...layouted.nodes]);
      setEdges([...layouted.edges]);
    }, 100);
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
        data: proc_incoming(dat),
      });
      fitView();
      onLayout();
    });

    socket.on("add_node", (par_id, node_id, dat) => {
      console.log("add_node", par_id, node_id, dat);
      createChildNode(
        {
          id: node_id,
          type: "contextNode",
          position: {
            x: 100,
            y: 100,
          },
          data: proc_incoming(dat),
        },
        par_id
      );
      onLayout();
    });

    socket.on("update_node", (node_id, dat) => {
      console.log("update_node", node_id, dat);
      updateContextData(node_id, proc_incoming(dat));
      onLayout();
    });

    socket.on("global_info", (info) => {
      setGlobalInfo(info);
    });

    socket.on("global_info_set", (key, value) => {
      setGlobalInfoKey(key, value);
    });

    socket.on("set_session_id", (node_id, session_id) => {
      console.log("set_session_id", node_id, session_id);
      setSessionId(node_id, session_id);
    });

    socket.on("set_session_info_key", (session_id, key, value) => {
      console.log("set_session_info_key", session_id, key, value);
      setSessionsInfoKey(session_id, key, value);
    });

    socket.on("set_current_session", (session_id) => {
      setCurrentSession(session_id);
      onLayout();
    });

    socket.on("set_session_info", (session_id, info) => {
      setSessionInfo(session_id, info);
    });
  }, []);

  const down_image = () => {
    onLayout();
    const nodesBounds = getNodesBounds(useStore.getState().nodes);
    const transform = getTransformForBounds(
      nodesBounds,
      imageWidth,
      imageHeight,
      0.5,
      2
    );

    toPng(document.querySelector(".react-flow__viewport") as HTMLElement, {
      backgroundColor: "#1a365d",
      width: imageWidth,
      height: imageHeight,
      style: {
        width: `${imageWidth}px`,
        height: `${imageHeight}px`,
        transform: `translate(${transform[0]}px, ${transform[1]}px) scale(${transform[2]})`,
      },
    }).then(downloadImage);
  };

  const handleSessionChange = (value: string) => {
    setCurrentSession(value);
    setTimeout(() => {
      fitView();
    }, 10);
  };

  return (
    <div
      style={{ width: "100%", height: "100vh" }}
      className="reactflow-wrapper"
      ref={reactFlowWrapper}
    >
      <ReactFlow
        nodes={nodes.filter(
          (node) =>
            ((currentSession === null || currentSession === "all_sessions") &&
              (sessionsInfo[node.data.session_id]
                ? sessionsInfo[node.data.session_id]["completed"] !== true
                : true)) ||
            node.data.session_id === currentSession
        )}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onInit={setReactFlowInstance}
        nodeTypes={nodeTypes}
        minZoom={0.01}
        fitView
      >
        <Panel
          position="top-right"
          className="flex flex-col space-y-4 w-72 overflow-auto overflow-x-hidden p-2 font-mono"
        >
          <h1 className="text-2xl">
            <span className="text-blue-700 font-bold">GeoAgent</span> Console
          </h1>
          <div className="font-bold">
            {isConnected ? (
              <div className="text-green-500 flex items-center">
                🟢 Connected to Server
              </div>
            ) : (
              <div className="flex items-center text-red-500">
                🔴 Not Connected
              </div>
            )}
          </div>

          <Select value={currentSession} onValueChange={handleSessionChange}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select Session" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all_sessions">All Sessions</SelectItem>
              {Object.keys(sessionsInfo).map((sessionId) => (
                <SelectItem key={sessionId} value={sessionId}>
                  Session: {sessionId}
                </SelectItem>
              ))}
            </SelectContent>
            <ConfigPanel onLayout={onLayout} />
          </Select>
          {debug && <InfoDisplay />}
          <SocialImport />
          <FileUpload />
          <div className="mb-4">
            <Button onClick={down_image} className="w-full">
              Export Screenshot <Image className="ml-2 mt-0.5" size={20} />
            </Button>
          </div>
        </Panel>
        <Background />
        <MiniMap position="top-left" />
        <Controls />
      </ReactFlow>
    </div>
  );
}
export default App;
