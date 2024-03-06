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
import { ContextData } from "./ContextNode";

export type EditorState = {
  nodes: Node<ContextData>[];
  edges: Edge[];
  globalInfo: any;
  currentSession: string | null; // Added current session identifier
  sessionsInfo: { [sessionId: string]: any }; // Added session-specific information dictionary
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
  setCurrentSession: (sessionId: string | null) => void; // Function to set the current session
  setSessionInfo: (sessionId: string, info: any) => void; // Function to set session-specific information
};

const useStore = create<EditorState>((set, get) => ({
  nodes: [],
  edges: [],
  globalInfo: {},
  currentSession: null, // Initialize currentSession as null
  sessionsInfo: {}, // Initialize sessionsInfo as an empty object
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
      const nodes = state.nodes.map((node) =>
        node.id === nodeId ? { ...node, data: { ...node.data, ...data } } : node
      );
      console.log("new nodes", nodes);
      return { nodes };
    });
  },
  getNodeById: (nodeId) => {
    return get().nodes.find((n) => n.id === nodeId);
  },
  createNode: (node) => {
    set({
      nodes: [...get().nodes, node],
    });
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
    set({ nodes: [], edges: [], currentSession: null, sessionsInfo: {} });
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
      return { nodes };
    });
  },
  setCurrentSession: (sessionId) => {
    set({ currentSession: sessionId });
  },
  setSessionInfo: (sessionId, info) => {
    set((state) => ({
      sessionsInfo: {
        ...state.sessionsInfo,
        [sessionId]: { ...state.sessionsInfo[sessionId], ...info },
      },
    }));
  },
}));

export default useStore;
