import useStore from "../store";
import { socket, URL } from "../socket";
import { FileUploader } from "react-drag-drop-files";
import { useState } from "react";

const fileTypes = ["JPG", "PNG", "GIF"];

function FileUpload() {
  const onUpdate = (file) => {
    console.log("on drop!");
    console.log(file);
    var reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = function () {
      socket.emit("start_session", {
        img_b64: reader.result,
      });
    };
  };
  return (
    <FileUploader handleChange={onUpdate} name="file" types={fileTypes}>
      <div className="w-full h-32 bg-slate-300 bg-opacity-20 rounded-md flex items-center justify-center hover:bg-slate-300 hover:bg-opacity-30 border-dashed border-2 border-slate-200 hover:cursor-pointer">
        <div className="text-lg font-bold">Import Image</div>
      </div>
    </FileUploader>
  );
}

export default FileUpload;
