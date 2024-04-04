import { Checkbox } from "@/components/ui/checkbox";
import useStore from "@/store";

export default function ConfigPanel({ onLayout }: { onLayout: () => void }) {
  const { debug, setDebug } = useStore();
  return (
    <div className="w-full mb-4 overflow-auto bg-slate-300 bg-opacity-20 rounded-md p-2 pb-4 font-mono">
      <span className="text-lg font-bold my-2 block">Configuration</span>
      <div className="flex items-center space-x-2">
        <Checkbox
          checked={debug}
          onCheckedChange={() => {
            setDebug(!debug);
            onLayout();
          }}
          id="debugcheck"
        />
        <label className="text-sm font-bold leading-none" htmlFor="debugcheck">
          Debug Mode
        </label>
      </div>
    </div>
  );
}
