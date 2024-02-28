import { io } from "socket.io-client";

const URL = import.meta.env.PROD ? undefined : "http://localhost:3141";

export const socket = io(URL, {
  transports: ["websocket", "polling", "flashsocket"],
});
