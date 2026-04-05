"use client";

import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Badge } from "@/components/ui/badge";

interface MNAData {
  q_a: number | null;
  q_b: number | null;
  q_c: number | null;
  q_d: number | null;
  q_e: number | null;
  q_f: number | null;
}

interface Props {
  data: MNAData;
  autoEstimates: { q_b: number | null; q_f: number | null };
  onChange: (data: MNAData) => void;
}

export type { MNAData };

const QUESTIONS = [
  { key: "q_a" as const, label: "問A: 食事量の変化（過去3ヶ月）", options: [
    { value: 0, label: "著しい食事量の減少" }, { value: 1, label: "中程度の食事量の減少" }, { value: 2, label: "食事量の減少なし" },
  ]},
  { key: "q_b" as const, label: "問B: 体重減少（過去3ヶ月）", options: [
    { value: 0, label: "3kg以上の減少" }, { value: 1, label: "わからない" }, { value: 2, label: "1〜3kgの減少" }, { value: 3, label: "体重減少なし" },
  ]},
  { key: "q_c" as const, label: "問C: 移動能力", options: [
    { value: 0, label: "寝たきりまたは車椅子" }, { value: 1, label: "ベッド・車椅子から離れられるが外出不可" }, { value: 2, label: "自由に外出できる" },
  ]},
  { key: "q_d" as const, label: "問D: 過去3ヶ月間の精神的ストレス・急性疾患", options: [
    { value: 0, label: "はい" }, { value: 2, label: "いいえ" },
  ]},
  { key: "q_e" as const, label: "問E: 神経・精神的問題", options: [
    { value: 0, label: "強度の認知症またはうつ状態" }, { value: 1, label: "軽度の認知症" }, { value: 2, label: "精神的問題なし" },
  ]},
  { key: "q_f" as const, label: "問F: BMI（またはCC）", options: [
    { value: 0, label: "BMI 19未満 / CC 31cm未満" }, { value: 1, label: "BMI 19以上 21未満" }, { value: 2, label: "BMI 21以上 23未満" }, { value: 3, label: "BMI 23以上 / CC 31cm以上" },
  ]},
];

export function Step2MNA({ data, autoEstimates, onChange }: Props) {
  const values = [data.q_a, data.q_b, data.q_c, data.q_d, data.q_e, data.q_f];
  const total = values.every((v) => v !== null) ? values.reduce((s, v) => s! + v!, 0) : null;
  const maxScore = 14;

  const getScoreColor = () => {
    if (total === null) return "bg-gray-200";
    if (total >= 12) return "bg-[#1a7a4a]";
    if (total >= 8) return "bg-[#b45309]";
    return "bg-[#c0392b]";
  };

  const getLabel = () => {
    if (total === null) return "未入力";
    if (total >= 12) return "栄養良好";
    if (total >= 8) return "低栄養のリスクあり";
    return "低栄養の可能性";
  };

  return (
    <div className="space-y-4">
      <h3 className="font-bold text-[#1a56a4]">ステップ 2: MNA-SF スクリーニング</h3>
      <div className="bg-gray-100 rounded-lg p-3">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium">MNA-SF スコア</span>
          <Badge className={`${getScoreColor()} text-white`}>{total ?? "—"} / {maxScore} — {getLabel()}</Badge>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div className={`h-3 rounded-full transition-all ${getScoreColor()}`} style={{ width: `${total !== null ? (total / maxScore) * 100 : 0}%` }} />
        </div>
      </div>
      {QUESTIONS.map((q) => {
        const autoValue = q.key === "q_b" ? autoEstimates.q_b : q.key === "q_f" ? autoEstimates.q_f : null;
        return (
          <div key={q.key} className="border rounded-lg p-4 bg-white">
            <Label className="text-sm font-semibold">
              {q.label}
              {autoValue !== null && data[q.key] === null && (
                <span className="ml-2 text-blue-500 text-xs cursor-pointer" onClick={() => onChange({ ...data, [q.key]: autoValue })}>
                  [自動推定値: {autoValue}点 — クリックで適用]
                </span>
              )}
              {autoValue !== null && data[q.key] !== null && data[q.key] === autoValue && (
                <span className="ml-2 text-green-600 text-xs">✓ 自動推定値を使用中</span>
              )}
            </Label>
            <RadioGroup value={data[q.key]?.toString() ?? ""} onValueChange={(v: string) => onChange({ ...data, [q.key]: Number(v) })} className="mt-2 space-y-1">
              {q.options.map((opt) => (
                <div key={opt.value} className="flex items-center space-x-2">
                  <RadioGroupItem value={opt.value.toString()} id={`${q.key}-${opt.value}`} />
                  <Label htmlFor={`${q.key}-${opt.value}`} className="font-normal cursor-pointer">
                    {opt.label} <span className="text-gray-400">({opt.value}点)</span>
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>
        );
      })}
    </div>
  );
}
