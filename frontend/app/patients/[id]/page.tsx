"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { patientsApi, assessmentsApi, exportApi, type Patient, type Assessment } from "@/lib/api";
import { PatientForm } from "@/components/patient-form";
import { AssessmentChart } from "@/components/assessment-chart";

const GENDER_LABELS: Record<string, string> = { male: "男性", female: "女性", other: "その他" };

export default function PatientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const patientId = Number(params.id);

  const [patient, setPatient] = useState<Patient | null>(null);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [editOpen, setEditOpen] = useState(false);

  const load = useCallback(async () => {
    const [p, a] = await Promise.all([
      patientsApi.get(patientId),
      assessmentsApi.listForPatient(patientId),
    ]);
    setPatient(p);
    setAssessments(a);
  }, [patientId]);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async () => {
    if (!confirm("この患者を削除しますか？関連する評価も全て削除されます。")) return;
    await patientsApi.delete(patientId);
    router.push("/patients");
  };

  if (!patient) return <div className="text-center py-8 text-gray-400">読み込み中...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/patients" className="text-sm text-gray-500 hover:underline">← 患者一覧</Link>
          <h2 className="text-xl font-bold mt-1">{patient.patient_code} — {patient.name || "氏名未登録"}</h2>
        </div>
        <div className="flex gap-2">
          <Dialog open={editOpen} onOpenChange={setEditOpen}>
            <DialogTrigger render={<Button variant="outline" />}>
              編集
            </DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>患者情報の編集</DialogTitle></DialogHeader>
              <PatientForm patient={patient} onSaved={() => { setEditOpen(false); load(); }} />
            </DialogContent>
          </Dialog>
          <Button variant="outline" className="text-red-500 border-red-200 hover:bg-red-50" onClick={handleDelete}>削除</Button>
        </div>
      </div>

      <Card>
        <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4 py-4">
          <div><span className="text-gray-500 text-sm">性別</span><p className="font-medium">{GENDER_LABELS[patient.gender]}</p></div>
          <div><span className="text-gray-500 text-sm">生年月日</span><p className="font-medium">{patient.birth_date || "—"}</p></div>
          <div><span className="text-gray-500 text-sm">備考</span><p className="font-medium">{patient.notes || "—"}</p></div>
          <div><span className="text-gray-500 text-sm">評価回数</span><p className="font-medium">{assessments.length}回</p></div>
        </CardContent>
      </Card>

      <AssessmentChart patientId={patientId} />

      <div className="flex items-center justify-between">
        <h3 className="font-bold">評価履歴</h3>
        <div className="flex gap-2">
          <a href={exportApi.csvUrl(patientId)} download><Button variant="outline" size="sm">CSV</Button></a>
          <a href={exportApi.excelUrl(patientId)} download><Button variant="outline" size="sm">Excel</Button></a>
          <Link href={`/assess/new?patient=${patientId}`}><Button className="bg-[#1a56a4] text-white">新規評価</Button></Link>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>評価日</TableHead>
                <TableHead>年齢</TableHead>
                <TableHead>BMI</TableHead>
                <TableHead>MNA-SF</TableHead>
                <TableHead>GLIM</TableHead>
                <TableHead>重症度</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {assessments.map((a) => (
                <TableRow key={a.id} className="cursor-pointer hover:bg-blue-50">
                  <TableCell>
                    <Link href={`/assess/${a.id}`} className="text-[#1a56a4] hover:underline">{a.assess_date}</Link>
                  </TableCell>
                  <TableCell>{a.age_at_assess}歳</TableCell>
                  <TableCell>{a.bmi?.toFixed(1) || "—"}</TableCell>
                  <TableCell>
                    <Badge variant={a.mna_category === "normal" ? "default" : a.mna_category === "risk" ? "secondary" : "destructive"}>
                      {a.mna_total ?? "—"} / 14
                    </Badge>
                  </TableCell>
                  <TableCell>{a.glim_diagnosed ? "低栄養" : "—"}</TableCell>
                  <TableCell>{a.glim_severity === "stage2" ? "Stage 2" : a.glim_severity === "stage1" ? "Stage 1" : "—"}</TableCell>
                </TableRow>
              ))}
              {assessments.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-gray-400 py-8">評価履歴がありません</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
