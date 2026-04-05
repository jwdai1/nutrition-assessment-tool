"use client";

import { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Step1, type Step1Data } from "@/components/wizard/step-1";
import { Step2MNA, type MNAData } from "@/components/wizard/step-2-mna";
import { Step3GLIM, type GLIMData } from "@/components/wizard/step-3-glim";
import { assessmentsApi } from "@/lib/api";

function WizardContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const patientId = Number(searchParams.get("patient"));
  const [step, setStep] = useState(1);
  const today = new Date().toISOString().slice(0, 10);

  const [step1, setStep1] = useState<Step1Data>({
    assess_date: today, age_at_assess: 0, height_cm: 0, weight_kg: 0,
    weight_3m_kg: null, weight_6m_kg: null, weight_3m_unknown: false, weight_6m_unknown: false, cc_cm: null,
  });

  const [mna, setMna] = useState<MNAData>({ q_a: null, q_b: null, q_c: null, q_d: null, q_e: null, q_f: null });
  const [glim, setGlim] = useState<GLIMData>({ weight_loss: 0, low_bmi: 0, muscle: "none", intake: 0, inflam: 0, chronic: 0 });

  const bmi = step1.weight_kg && step1.height_cm ? step1.weight_kg / ((step1.height_cm / 100) ** 2) : null;

  const autoQB = (() => {
    if (!step1.weight_kg || !step1.weight_3m_kg) return null;
    const loss = step1.weight_3m_kg - step1.weight_kg;
    if (loss >= 3) return 0; if (loss > 0) return 2; return 3;
  })();

  const autoQF = (() => {
    if (bmi !== null) { if (bmi < 19) return 0; if (bmi < 21) return 1; if (bmi < 23) return 2; return 3; }
    if (step1.cc_cm !== null) return step1.cc_cm >= 31 ? 3 : 0;
    return null;
  })();

  const autoWeightLoss = (() => {
    if (step1.weight_3m_kg && step1.weight_kg) { if (((step1.weight_3m_kg - step1.weight_kg) / step1.weight_3m_kg) * 100 > 5) return true; }
    if (step1.weight_6m_kg && step1.weight_kg) { if (((step1.weight_6m_kg - step1.weight_kg) / step1.weight_6m_kg) * 100 > 10) return true; }
    return false;
  })();

  const autoLowBmi = bmi !== null ? (step1.age_at_assess >= 70 ? bmi < 22 : bmi < 20) : false;

  const mnaValues = [mna.q_a, mna.q_b, mna.q_c, mna.q_d, mna.q_e, mna.q_f];
  const mnaTotal = mnaValues.every((v) => v !== null) ? mnaValues.reduce((s, v) => s! + v!, 0) : null;
  const skipGlim = mnaTotal !== null && mnaTotal >= 12;
  const totalSteps = skipGlim ? 2 : 3;

  const handleSubmit = async () => {
    const payload = {
      patient_id: patientId, assess_date: step1.assess_date, age_at_assess: step1.age_at_assess,
      height_cm: step1.height_cm, weight_kg: step1.weight_kg, weight_3m_kg: step1.weight_3m_kg,
      weight_6m_kg: step1.weight_6m_kg, cc_cm: step1.cc_cm, mna,
      glim: skipGlim ? { weight_loss: 0, low_bmi: 0, muscle: "none", intake: 0, inflam: 0, chronic: 0 } : glim,
    };
    const result = await assessmentsApi.create(payload);
    router.push(`/assess/${result.id}`);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="flex items-center justify-center gap-2 text-sm">
        {Array.from({ length: totalSteps }, (_, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${step >= i + 1 ? "bg-[#1a56a4] text-white" : "bg-gray-200 text-gray-500"}`}>{i + 1}</div>
            {i < totalSteps - 1 && <div className="w-8 h-px bg-gray-300" />}
          </div>
        ))}
      </div>
      <Card><CardContent className="pt-6">
        {step === 1 && <Step1 data={step1} onChange={setStep1} />}
        {step === 2 && <Step2MNA data={mna} autoEstimates={{ q_b: autoQB, q_f: autoQF }} onChange={setMna} />}
        {step === 3 && !skipGlim && <Step3GLIM data={glim} autoEstimates={{ weight_loss: autoWeightLoss, low_bmi: autoLowBmi }} onChange={setGlim} />}
      </CardContent></Card>
      <div className="flex justify-between">
        <Button variant="outline" onClick={() => step > 1 ? setStep(step - 1) : router.back()}>
          {step > 1 ? "← 前へ" : "← キャンセル"}
        </Button>
        {step < totalSteps ? (
          <Button className="bg-[#1a56a4] text-white" onClick={() => setStep(step + 1)}>次へ →</Button>
        ) : (
          <Button className="bg-[#1a7a4a] hover:bg-[#156b3e] text-white" onClick={handleSubmit}>評価を保存</Button>
        )}
      </div>
    </div>
  );
}

export default function NewAssessmentPage() {
  return (
    <Suspense fallback={<div className="text-center py-8 text-gray-400">読み込み中...</div>}>
      <WizardContent />
    </Suspense>
  );
}
