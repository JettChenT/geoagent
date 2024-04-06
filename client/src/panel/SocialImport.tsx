import useStore from "../store";
import { socket, URL } from "../socket";
import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { SiTwitter, SiTelegram } from "@icons-pack/react-simple-icons";
import { useToast } from "../components/ui/use-toast";

function ActionIcon({ url }: { url: string }) {
  if (url.search("twitter") !== -1) {
    return <SiTwitter size={18} className="ml-1 mt-0.5" />;
  }
  if (url.search("t.me") !== -1) {
    return <SiTelegram size={18} className="ml-1 mt-0.5" />;
  }
  return <ArrowRight size={18} />;
}

function SocialImport() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    socket.on("url_processed", (processed) => {
      console.log("processed", processed);
      setLoading(false);
      setUrl("");
      toast({
        title: "Imported",
        description: "Imported from social media",
      });
    });
  }, []);
  const onSubmit = () => {
    setLoading(true);
    socket.emit("from_social", { url });
  };
  return (
    <div className="w-full mb-4 overflow-auto bg-slate-300 bg-opacity-20 rounded-md p-2 font-mono">
      <span className="text-lg font-bold my-2 block">Import from Internet</span>
      <div className="flex w-full max-w-sm flex-col items-center space-y-2">
        <Input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              onSubmit();
            }
          }}
          placeholder="https://twitter.com/..."
          className="w-full"
        />
        <Button
          onClick={onSubmit}
          disabled={loading || url === ""}
          className="w-full"
        >
          Import
          <ActionIcon url={url} />
        </Button>
      </div>
    </div>
  );
}

export default SocialImport;
