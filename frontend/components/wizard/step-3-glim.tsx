"use client";

import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface GLIMData {
  weight_loss: number;
  low_bmi: number;
  muscle: string;
  intake: number;
  inflam: number;
  chronic: number;
}

interface Props {
  data: GLIMData;
  autoEstimates: { weight_loss: boolean; low_bmi: boolean };
  onChange: (data: GLIMData) => void;
}

export type { GLIMData };

export function Step3GLIM({ data, autoEstimates, onChange }: Props) {
  const update = (patch: Partial<GLIMData>) => onChange({ ...data, ...patch });
  const phenotypicMet = data.weight_loss || data.low_bmi || data.muscle !== "none";
  const etiologicMet = data.intake || data.inflam || data.chronic;

  return (
    <div className="space-y-4">
      <h3 className="font-bold text-[#1a56a4]">ステップ 3: GLIM 評価</h3>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">
            表現型基準（1項目以上で充足）
            {phenotypicMet ? <span className="ml-2 text-green-600">✓ 充足</span> : <span className="ml-2 text-gray-400">未充足</span>}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <Checkbox checked={!!data.weight_loss} onCheckedChange={(v) => update({ weight_loss: v ? 1 : 0 })} />
            <Label className="font-normal">意図しない体重減少{autoEstimates.weight_loss && <span className="text-blue-500 text-xs ml-1">(自動判定: 該当)</span>}</Label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox checked={!!data.low_bmi} onCheckedChange={(v) => update({ low_bmi: v ? 1 : 0 })} />
            <Label className="font-normal">低BMI（アジア人基準）{autoEstimates.low_bmi && <span className="text-blue-500 text-xs ml-1">(自動判定: 該当)</span>}</Label>
          </div>
          <div>
            <Label>筋肉量・筋量の低下</Label>
            <Select value={data.muscle} onValueChange={(v) => v && update({ muscle: v })}>
              <SelectTrigger className="mt-1"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">なし</SelectItem>
                <SelectItem value="mild">軽〜中等度</SelectItem>
                <SelectItem value="severe">高度</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">
            病因基準（1項目以上で充足）
            {etiologicMet ? <span className="ml-2 text-green-600">✓ 充足</span> : <span className="ml-2 text-gray-400">未充足</span>}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2">
            <Checkbox checked={!!data.intake} onCheckedChange={(v) => update({ intake: v ? 1 : 0 })} />
            <Label className="font-normal">食事摂取量の低下 / 消化吸収障害</Label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox checked={!!data.inflam} onCheckedChange={(v) => update({ inflam: v ? 1 : 0 })} />
            <Label className="font-normal">急性疾患 / 外傷による炎症</Label>
          </div>
          <div className="flex items-center gap-2">
            <Checkbox checked={!!data.chronic} onCheckedChange={(v) => update({ chronic: v ? 1 : 0 })} />
            <Label className="font-normal">慢性疾患による炎症（中等度）</Label>
          </div>
        </CardContent>
      </Card>
      {phenotypicMet && etiologicMet && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-800">
          表現型基準・病因基準ともに充足 → <strong>低栄養と診断されます</strong>
        </div>
      )}
    </div>
  );
}
