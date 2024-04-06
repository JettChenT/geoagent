import { ContextData } from "./nodes/ContextNode";
import { Node } from "reactflow";

export const sampleNodes: Node<ContextData>[] = [
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
    position: { x: 100, y: 200 },
    data: {
      cur_messages: [],
      observation: "Hello, World!",
      transition: {
        type: "AgentAction",
        tool: "Google Lens",
        tool_input: "Nobody Expects the Spanish Inquisition",
      },
      lats_data: {},
      auxiliary: {
        images: [
          "https://upload.wikimedia.org/wikipedia/commons/4/47/Monty_Python_Live_02-07-14_12_46_43_%2814415411808%29.jpg",
          "https://upload.wikimedia.org/wikipedia/commons/a/a3/Monty_Python_Live_02-07-14_12_56_41_%2814415567757%29.jpg",
        ],
        geojson: {
          type: "FeatureCollection",
          features: [
            {
              type: "Feature",
              geometry: { type: "Point", coordinates: [51.505, 13.11] },
              properties: {},
            },
          ],
          properties: {
            bounds: [
              [50.505, -29.09],
              [52.505, 29.09],
            ],
          },
        },
      },
      session_id: "1",
      is_root: false,
      state: "normal",
    },
  },
  {
    id: "3",
    type: "contextNode",
    position: { x: 300, y: 100 },
    data: {
      cur_messages: [],
      observation: "Hello, World!",
      transition: null,
      lats_data: {},
      auxiliary: {},
      session_id: "1",
      is_root: true,
      state: "normal",
    },
  },
];

export const sampleSessionInfo = {
  1: {
    content_type: "telegram",
    telegram_id: "truexanewsua/74039",
  },
};
