"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";

interface Step1Data {
  assess_date: string;
  age_at_assess: number;
  height_cm: number;
  weight_kg: number;
  weight_3m_kg: number | null;
  weight_6m_kg: number | null;
  weight_3m_unknown: boolean;
  weight_6m_unknown: boolean;
  cc_cm: number | null;
}

interface Props {
  data: Step1Data;
  onChange: (data: Step1Data) => void;
}

export type { Step1Data };

export function Step1({ data, onChange }: Props) {
  const update = (patch: Partial<Step1Data>) => onChange({ ...data, ...patch });

  const bmi = data.weight_kg && data.height_cm
    ? (data.weight_kg / ((data.height_cm / 100) ** 2)).toFixed(1)
    : "—";

  const wlPct3m = data.weight_kg && data.weight_3m_kg
    ? (((data.weight_3m_kg - data.weight_kg) / data.weight_3m_kg) * 100).toFixed(1)
    : null;

  const wlPct6m = data.weight_kg && data.weight_6m_kg
    ? (((data.weight_6m_kg - data.weight_kg) / data.weight_6m_kg) * 100).toFixed(1)
    : null;

  return (
    <div className="space-y-4">
      <h3 className="font-bold text-[#1a56a4]">ステップ 1: 患者基本情報</h3>
      <div className="grid grid-cols-2 gap-4">
        <div><Label>評価日 *</Label><Input type="date" value={data.assess_date} onChange={(e) => update({ assess_date: e.target.value })} /></div>
        <div><Label>年齢 *</Label><Input type="number" value={data.age_at_assess || ""} onChange={(e) => update({ age_at_assess: Number(e.target.value) })} /></div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div><Label>身長 (cm) *</Label><Input type="number" step="0.1" value={data.height_cm || ""} onChange={(e) => update({ height_cm: Number(e.target.value) })} /></div>
        <div><Label>現在体重 (kg) *</Label><Input type="number" step="0.1" value={data.weight_kg || ""} onChange={(e) => update({ weight_kg: Number(e.target.value) })} /></div>
      </div>
      <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-sm">
        BMI: <strong>{bmi}</strong>
        {wlPct3m && <> | 3M体重減少率: <strong>{wlPct3m}%</strong></>}
        {wlPct6m && <> | 6M体重減少率: <strong>{wlPct6m}%</strong></>}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Label>3ヶ月前体重 (kg)</Label>
            <div className="flex items-center gap-1">
              <Checkbox checked={data.weight_3m_unknown} onCheckedChange={(v) => update({ weight_3m_unknown: !!v, weight_3m_kg: null })} />
              <span className="text-xs text-gray-500">不明</span>
            </div>
          </div>
          <Input type="number" step="0.1" disabled={data.weight_3m_unknown} value={data.weight_3m_kg ?? ""} onChange={(e) => update({ weight_3m_kg: e.target.value ? Number(e.target.value) : null })} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <Label>6ヶ月前体重 (kg)</Label>
            <div className="flex items-center gap-1">
              <Checkbox checked={data.weight_6m_unknown} onCheckedChange={(v) => update({ weight_6m_unknown: !!v, weight_6m_kg: null })} />
              <span className="text-xs text-gray-500">不明</span>
            </div>
          </div>
          <Input type="number" step="0.1" disabled={data.weight_6m_unknown} value={data.weight_6m_kg ?? ""} onChange={(e) => update({ weight_6m_kg: e.target.value ? Number(e.target.value) : null })} />
        </div>
      </div>
      <div>
        <Label>下腿周囲長 CC (cm)</Label>
        <Input type="number" step="0.1" value={data.cc_cm ?? ""} onChange={(e) => update({ cc_cm: e.target.value ? Number(e.target.value) : null })} />
        <p className="text-xs text-gray-500 mt-1">BMIが測定できない場合のMNA-SF問F代替</p>
      </div>
    </div>
  );
}
