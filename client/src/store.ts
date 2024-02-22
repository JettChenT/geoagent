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
    const node = get().nodes.find((n) => n.id === nodeId);
    if (node) {
      node.data = data;
      set({
        nodes: get().nodes,
      });
    }
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
    set((state) => ({
      nodes: [...state.nodes, node],
      edges: [
        ...state.edges,
        { id: `e${parentId}-${node.id}`, source: parentId, target: node.id },
      ],
    }));
  },
}));

export default useStore;
