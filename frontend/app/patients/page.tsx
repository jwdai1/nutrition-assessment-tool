"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { patientsApi, type Patient } from "@/lib/api";
import { PatientForm } from "@/components/patient-form";

const GENDER_LABELS: Record<string, string> = {
  male: "男性", female: "女性", other: "その他",
};

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);

  const load = useCallback(async () => {
    const data = await patientsApi.list(search || undefined);
    setPatients(data);
  }, [search]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">患者一覧</h2>
        <span className="text-sm text-gray-500">{patients.length}名</span>
      </div>
      <div className="flex items-center justify-between gap-4">
        <Input
          placeholder="患者ID または 氏名で検索..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger render={<Button className="bg-[#1a56a4] hover:bg-[#1648b0] text-white" />}>
            ＋ 患者追加
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>患者登録</DialogTitle>
            </DialogHeader>
            <PatientForm onSaved={() => { setDialogOpen(false); load(); }} />
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>患者ID</TableHead>
                <TableHead>氏名</TableHead>
                <TableHead>性別</TableHead>
                <TableHead>生年月日</TableHead>
                <TableHead>更新日</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {patients.map((p) => (
                <TableRow key={p.id} className="cursor-pointer hover:bg-blue-50">
                  <TableCell>
                    <Link href={`/patients/${p.id}`} className="text-[#1a56a4] font-semibold hover:underline">
                      {p.patient_code}
                    </Link>
                  </TableCell>
                  <TableCell>{p.name || "—"}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{GENDER_LABELS[p.gender] || p.gender}</Badge>
                  </TableCell>
                  <TableCell>{p.birth_date || "—"}</TableCell>
                  <TableCell className="text-gray-500 text-sm">
                    {p.updated_at ? new Date(p.updated_at).toLocaleDateString("ja-JP") : "—"}
                  </TableCell>
                </TableRow>
              ))}
              {patients.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-16">
                    <div className="text-gray-400 space-y-2">
                      <p className="text-lg">患者が登録されていません</p>
                      <p className="text-sm">「＋ 患者追加」ボタンから最初の患者を登録してください</p>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
