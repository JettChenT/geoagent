import { Card, CardContent } from "@/components/ui/card";
import { ContextData } from "../ContextNode";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
import { proc_img_url } from "@/utils";

export default function DisplayImages({ data }: { data: ContextData }) {
  if (!data.auxiliary.images) {
    return null;
  }
  const images = data.auxiliary.images;
  return (
    <div className="px-5">
      <Carousel
        opts={{
          watchDrag: false,
        }}
      >
        <CarouselContent>
          {images.map((image, index) => (
            <CarouselItem key={index}>
              <img
                src={proc_img_url(image)}
                className="w-full h-full rounded-sm"
                loading="lazy"
              />
            </CarouselItem>
          ))}
        </CarouselContent>
        <CarouselPrevious className="ml-7 size-7" />
        <CarouselNext className="mr-7 size-7" />
      </Carousel>
    </div>
  );
}
