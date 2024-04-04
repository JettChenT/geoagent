import { create } from "zustand";
import {
  Edge,
  EdgeChange,
  Node,
  NodeChange,
  addEdge,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
  applyNodeChanges,
  applyEdgeChanges,
} from "reactflow";
import { ContextData } from "./nodes/ContextNode";

export type EditorState = {
  nodes: Node<ContextData>[];
  edges: Edge[];
  globalInfo: any;
  sessionsInfo: any;
  currentSession: string | null;
  debug: boolean;
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  updateContextData: (nodeId: string, data: ContextData) => void;
  getNodeById: (nodeId: string) => Node<ContextData> | undefined;
  createNode: (node: Node<ContextData>) => void;
  createChildNode: (node: Node<ContextData>, parentId: string) => void;
  setNodes: (nodes: Node<ContextData>[]) => void;
  setEdges: (edges: Edge[]) => void;
  clearAll: () => void;
  setGlobalInfo: (info: any) => void;
  setGlobalInfoKey: (key: string, value: any) => void;
  setSessionId: (nodeId: string, sessionId: string | null) => void;
  setCurrentSession: (sessionId: string | null) => void;
  setSessionsInfoKey: (sessionId: string, key: string, value: any) => void;
  setSessionInfo: (sessionId: string, info: any) => void; // Added setSessionInfo function type
  setDebug: (debug: boolean) => void;
};

const sampleNodes: Node<ContextData>[] = [
  {
    id: "1",
    type: "contextNode",
    position: { x: 100, y: 100 },
    data: {
      cur_messages: [],
      observation: "Hello, World!",
      transition: {
        type: "AgentAction",
        tool: "Propose Coordinates",
        tool_input: "37.7749,-122.4194",
      },
      lats_data: {},
      auxiliary: {},
      session_id: "1",
      is_root: false,
      state: "normal",
    },
  },
  {
    id: "2",
    type: "contextNode",
    position: { x: 100, y: 100 },
    data: {
      cur_messages: [],
      observation: "Hello, World!",
      transition: {
        type: "AgentAction",
        tool: "Google Lens",
        tool_input: "foo bar",
      },
      lats_data: {},
      auxiliary: {},
      session_id: "1",
      is_root: false,
      state: "normal",
    },
  },
];

const useStore = create<EditorState>((set, get) => ({
  nodes: [],
  edges: [],
  globalInfo: {},
  sessionsInfo: {},
  currentSession: "all_sessions",
  debug: true,
  onNodesChange: (changes: NodeChange[]) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
  },
  onEdgesChange: (changes: EdgeChange[]) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
  },
  onConnect: (params) => {
    set({
      edges: addEdge(params, get().edges),
    });
  },
  updateContextData: (nodeId, data) => {
    set((state) => {
      console.log("updateContextData", nodeId, data);
      const nodes = state.nodes.map((node) => {
        if (node.id === nodeId) {
          const updatedData = { ...node.data };
          Object.keys(data).forEach((key) => {
            if (data[key] !== null) {
              updatedData[key] = data[key];
            }
          });
          return { ...node, data: updatedData };
        }
        return node;
      });
      console.log("new nodes", nodes);
      return { nodes };
    });
  },
  getNodeById: (nodeId) => {
    return get().nodes.find((n) => n.id === nodeId);
  },
  createNode: (node) => {
    if (!get().nodes.some((n) => n.id === node.id)) {
      node.data = { ...node.data, is_root: true };
      set({
        nodes: [...get().nodes, node],
      });
    }
  },
  createChildNode: (node, parentId) => {
    set((state) => {
      const parentNode = state.nodes.find((n) => n.id === parentId);
      if (!state.nodes.some((n) => n.id === node.id) && parentNode) {
        const updatedNode = {
          ...node,
          data: { ...node.data, session_id: parentNode.data.session_id },
        };
        return {
          nodes: [...state.nodes, updatedNode],
          edges: [
            ...state.edges,
            {
              id: `e${parentId}-${node.id}`,
              source: parentId,
              target: node.id,
            },
          ],
        };
      }
      return state;
    });
  },
  setNodes: (nodes) => {
    set({ nodes });
  },
  setEdges: (edges) => {
    set({ edges });
  },
  clearAll: () => {
    set({ nodes: [], edges: [] });
  },
  setGlobalInfo: (info) => {
    set({ globalInfo: info });
  },
  setGlobalInfoKey: (key, value) => {
    set((state) => ({
      globalInfo: { ...state.globalInfo, [key]: value },
    }));
  },
  setSessionId: (nodeId, sessionId) => {
    set((state) => {
      const nodes = state.nodes.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, session_id: sessionId } }
          : node
      );
      console.log("setSessionId", nodeId, sessionId, nodes);
      return { nodes };
    });
  },
  setCurrentSession: (sessionId) => {
    set({ currentSession: sessionId });
  },
  setSessionsInfoKey: (sessionId, key, value) => {
    set((state) => ({
      sessionsInfo: {
        ...state.sessionsInfo,
        [sessionId]: { ...state.sessionsInfo[sessionId], [key]: value },
      },
    }));
  },
  setSessionInfo: (sessionId, info) => {
    // Implementation of setSessionInfo
    set((state) => ({
      sessionsInfo: {
        ...state.sessionsInfo,
        [sessionId]: { ...state.sessionsInfo[sessionId], ...info },
      },
    }));
  },
  setDebug: (debug) => {
    set({ debug });
  },
}));

export default useStore;
