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
        content: <DisplayImages data={data} />,
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
