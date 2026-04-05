"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { assessmentsApi, exportApi, type Assessment } from "@/lib/api";
import { IsocalBanner } from "@/components/isocal-banner";

const BANNER_STYLES = {
  normal: { bg: "bg-green-50", border: "border-green-500", text: "text-green-700", label: "栄養良好（MNA-SF ≥12）" },
  risk: { bg: "bg-yellow-50", border: "border-yellow-500", text: "text-yellow-700", label: "低栄養のリスクあり" },
  severe: { bg: "bg-red-50", border: "border-red-500", text: "text-red-700", label: "低栄養の可能性" },
};

export default function AssessmentResultPage() {
  const params = useParams();
  const assessmentId = Number(params.id);
  const [assessment, setAssessment] = useState<Assessment | null>(null);

  useEffect(() => { assessmentsApi.get(assessmentId).then(setAssessment); }, [assessmentId]);

  if (!assessment) return <div className="text-center py-8 text-gray-400">読み込み中...</div>;

  const a = assessment;
  const category = a.mna_category || "risk";
  const banner = BANNER_STYLES[category as keyof typeof BANNER_STYLES] || BANNER_STYLES.risk;

  const glimLabel = a.glim_diagnosed
    ? a.glim_severity === "stage2" ? "低栄養（Stage 2: 高度）" : "低栄養（Stage 1: 中等度）"
    : a.mna_category === "normal" ? null : "低栄養非該当（要観察）";

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <Link href={`/patients/${a.patient_id}`} className="text-sm text-gray-500 hover:underline">← 患者詳細に戻る</Link>
      <h2 className="text-xl font-bold">評価結果 — {a.assess_date}</h2>

      {/* Diagnosis banner */}
      <div className={`${banner.bg} border-2 ${banner.border} rounded-lg p-4`}>
        <p className={`text-lg font-bold ${banner.text}`}>{banner.label}</p>
        {glimLabel && <p className={`text-sm mt-1 ${banner.text}`}>{glimLabel}</p>}
      </div>

      {/* Score summary */}
      <Card>
        <CardHeader><CardTitle className="text-sm">スコアサマリ</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div><span className="text-gray-500 text-xs">MNA-SF</span><p className="text-lg font-bold">{a.mna_total ?? "—"} / 14</p></div>
          <div><span className="text-gray-500 text-xs">BMI</span><p className="text-lg font-bold">{a.bmi?.toFixed(1) ?? "—"}</p></div>
          <div><span className="text-gray-500 text-xs">体重減少率(3M)</span><p className="text-lg font-bold">{a.wl_pct_3m ? `${a.wl_pct_3m.toFixed(1)}%` : "—"}</p></div>
          <div><span className="text-gray-500 text-xs">体重減少率(6M)</span><p className="text-lg font-bold">{a.wl_pct_6m ? `${a.wl_pct_6m.toFixed(1)}%` : "—"}</p></div>
        </CardContent>
      </Card>

      {/* GLIM breakdown */}
      {a.glim_diagnosed !== null && a.reasons.length > 0 && (
        <Card>
          <CardHeader><CardTitle className="text-sm">GLIM 評価内訳</CardTitle></CardHeader>
          <CardContent>
            <ul className="space-y-1">{a.reasons.map((r, i) => (
              <li key={i} className="text-sm flex items-start gap-2"><span className="text-red-500 mt-0.5">●</span>{r}</li>
            ))}</ul>
          </CardContent>
        </Card>
      )}

      {/* Recommendations */}
      <Card>
        <CardHeader><CardTitle className="text-sm">推奨アクション</CardTitle></CardHeader>
        <CardContent className="space-y-2">{a.recommendations.map((rec, i) => (
          <div key={i} className={`p-3 rounded-md text-sm ${a.glim_severity === "stage2" ? "bg-red-50 border border-red-200" : "bg-yellow-50 border border-yellow-200"}`}>{rec}</div>
        ))}</CardContent>
      </Card>

      {/* Isocal 100 recommendation */}
      <IsocalBanner recommendation={a.isocal_recommendation} />

      {/* Actions */}
      <div className="flex gap-3">
        <a href={exportApi.pdfUrl(a.id)} download><Button variant="outline">PDF出力</Button></a>
        <Link href={`/patients/${a.patient_id}`}><Button variant="outline">患者詳細に戻る</Button></Link>
      </div>
    </div>
  );
}
