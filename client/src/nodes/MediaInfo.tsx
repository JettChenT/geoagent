import { Tweet } from "react-tweet";
import { ContextData } from "./ContextNode";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import DisplayResults from "./views/DisplayResults";
import { proc_img_url } from "@/utils";
import DisplayGeojson from "./views/DisplayGeojson";
import DisplayImages from "./views/DisplayImages";
import { useMemo } from "react";

export default function MediaInfo({
  data,
  sessionsInfo,
}: {
  data: ContextData;
  sessionsInfo: any;
}) {
  const sessionInfo = sessionsInfo[data.session_id];
  const tabs = useMemo(() => {
    let tempTabs = [];
    if (
      data.transition &&
      data.transition.type === "AgentAction" &&
      data.transition.tool === "Propose Coordinates"
    ) {
      tempTabs.push({
        label: "Results",
        content: <DisplayResults data={data} />,
      });
    }
    if (data.is_root && sessionInfo) {
      if (sessionInfo.content_type === "tweet") {
        tempTabs.push({
          label: "Tweet",
          content: <Tweet id={sessionInfo.tweet_id} />,
        });
      }
      if (sessionInfo.content_type === "telegram") {
        tempTabs.push({
          label: "Telegram",
          content: (
            <iframe
              src={`https://t.me/${sessionInfo.telegram_id}?embed=1`}
              width="100%"
              height="400"
            ></iframe>
          ),
        });
      }
      if (sessionInfo.images) {
        tempTabs.push({
          label: "Images",
          content: <DisplayImages images={sessionInfo.images} />,
        });
      }
      if (sessionInfo.image_loc) {
        tempTabs.push({
          label: "Image",
          content: (
            <img
              src={proc_img_url(sessionInfo.image_loc)}
              alt="session_image"
              className="w-full mb-2"
            />
          ),
        });
      }
    }
    if (data.auxiliary.geojson) {
      tempTabs.push({
        label: "Map",
        content: <DisplayGeojson data={data} />,
      });
    }
    if (data.auxiliary.images) {
      tempTabs.push({
        label: "Images",
        content: <DisplayImages images={data.auxiliary.images} />,
      });
    }
    if (data.auxiliary.text) {
      tempTabs.push({
        label: "Text",
        content: (
          <div className="text-sm font-mono text-left nodrag max-h-24 overflow-auto border-2 border-solid">
            <pre className="whitespace-pre-wrap">{data.auxiliary.text}</pre>
          </div>
        ),
      });
    }
    return tempTabs;
  }, [data, sessionInfo]);

  if (tabs.length === 0) {
    return null;
  }
  return (
    <Tabs defaultValue="0">
      <TabsList className="flex w-full">
        {tabs.map((tab, index) => (
          <TabsTrigger
            key={index}
            value={index.toString()}
            className="flex-auto"
          >
            {tab.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {tabs.map((tab, index) => (
        <TabsContent key={index} value={index.toString()}>
          {tab.content}
        </TabsContent>
      ))}
    </Tabs>
  );
}
