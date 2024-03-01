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
  setGlobalInfoKey: (key: string, value: any) => void; // Added function type for setting a specific key in globalInfo
};

const useStore = create<EditorState>((set, get) => ({
  nodes: [],
  edges: [],
  globalInfo: {}, // Initialize globalInfo as an empty object
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
      if (!state.nodes.some((n) => n.id === node.id)) {
        return {
          nodes: [...state.nodes, node],
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
    // Implementation of the added function
    set((state) => ({
      globalInfo: { ...state.globalInfo, [key]: value },
    }));
  },
}));

export default useStore;
