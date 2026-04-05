"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { patientsApi, type Patient } from "@/lib/api";

interface Props {
  patient?: Patient;
  onSaved: () => void;
}

export function PatientForm({ patient, onSaved }: Props) {
  const [code, setCode] = useState(patient?.patient_code || "");
  const [name, setName] = useState(patient?.name || "");
  const [gender, setGender] = useState(patient?.gender || "male");
  const [birthDate, setBirthDate] = useState(patient?.birth_date || "");
  const [notes, setNotes] = useState(patient?.notes || "");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) { setError("患者IDは必須です"); return; }
    setSubmitting(true);
    setError("");
    try {
      const data = { patient_code: code, name, gender, birth_date: birthDate || undefined, notes };
      if (patient) {
        await patientsApi.update(patient.id, data);
      } else {
        await patientsApi.create(data);
      }
      onSaved();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "保存に失敗しました");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <div>
        <Label>患者ID *</Label>
        <Input value={code} onChange={(e) => setCode(e.target.value)} placeholder="PT-0001" />
      </div>
      <div>
        <Label>氏名</Label>
        <Input value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div>
        <Label>性別 *</Label>
        <Select value={gender} onValueChange={(v) => v && setGender(v)}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="male">男性</SelectItem>
            <SelectItem value="female">女性</SelectItem>
            <SelectItem value="other">その他</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div>
        <Label>生年月日</Label>
        <Input type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} />
      </div>
      <div>
        <Label>備考</Label>
        <Input value={notes} onChange={(e) => setNotes(e.target.value)} />
      </div>
      <Button type="submit" disabled={submitting} className="w-full bg-[#1a56a4]">
        {submitting ? "保存中..." : patient ? "更新" : "登録"}
      </Button>
    </form>
  );
}
