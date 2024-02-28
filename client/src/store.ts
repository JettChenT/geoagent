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
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  updateContextData: (nodeId: string, data: ContextData) => void;
  getNodeById: (nodeId: string) => Node<ContextData> | undefined;
  createNode: (node: Node<ContextData>) => void;
  createChildNode: (node: Node<ContextData>, parentId: string) => void;
  setNodes: (nodes: Node<ContextData>[]) => void;
  setEdges: (edges: Edge[]) => void;
  clearAll: () => void; // Added function type for clearing all nodes and edges
};

const useStore = create<EditorState>((set, get) => ({
  nodes: [],
  edges: [],
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
    set({ nodes: [], edges: [] }); // Implementation for clearing all nodes and edges
  },
}));

export default useStore;
