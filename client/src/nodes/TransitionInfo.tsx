export default function TransitionInfo({ transition }) {
  return (
    <div
      className="text-sm text-left nodrag"
      style={{ userSelect: "text", cursor: "text" }}
    >
      <span className="font-bold">Transition: </span>
      {transition && "tool" in transition ? (
        <span>
          <span className="text-blue-500 font-mono">{transition.tool}</span>
          <span className="text-gray-500 font-mono">
            {" "}
            ({transition.tool_input})
          </span>
        </span>
      ) : (
        <span className="text-gray-500 font-mono">
          {" "}
          {transition ? transition["type"] : "None"}{" "}
        </span>
      )}
    </div>
  );
}
