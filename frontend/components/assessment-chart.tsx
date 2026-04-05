"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { assessmentsApi, type ChartDataPoint } from "@/lib/api";

interface Props {
  patientId: number;
}

export function AssessmentChart({ patientId }: Props) {
  const [data, setData] = useState<ChartDataPoint[]>([]);

  useEffect(() => {
    assessmentsApi.chartData(patientId).then((res) => setData(res.data));
  }, [patientId]);

  if (data.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-gray-400">
          評価データがありません
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">経時変化グラフ</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="assess_date" fontSize={11} />
            <YAxis yAxisId="left" fontSize={11} />
            <YAxis yAxisId="right" orientation="right" fontSize={11} />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="weight_kg" stroke="#1a56a4" name="体重(kg)" strokeWidth={2} />
            <Line yAxisId="left" type="monotone" dataKey="bmi" stroke="#b45309" name="BMI" strokeWidth={2} />
            <Line yAxisId="right" type="monotone" dataKey="mna_total" stroke="#1a7a4a" name="MNA-SF" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
