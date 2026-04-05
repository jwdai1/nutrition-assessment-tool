"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { IsocalRecommendation } from "@/lib/api";

interface Props {
  recommendation: IsocalRecommendation;
}

export function IsocalBanner({ recommendation }: Props) {
  if (!recommendation.show) return null;

  return (
    <Card className="border-2 border-[#00a0e0] bg-gradient-to-r from-blue-50 to-white">
      <CardContent className="py-5 space-y-3">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 bg-[#00a0e0] rounded-lg flex items-center justify-center text-white text-xs font-bold shrink-0">
            Isocal<br/>100
          </div>
          <div className="flex-1">
            <h4 className="font-bold text-lg text-[#00508c]">{recommendation.product_name}</h4>
            <p className="text-sm text-gray-700 mt-1">{recommendation.description}</p>
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-md p-3 text-xs text-gray-600 leading-relaxed whitespace-pre-line">
          {recommendation.permitted_claim}
        </div>
        <div className="flex gap-3">
          <a href={recommendation.brand_url} target="_blank" rel="noopener noreferrer">
            <Button variant="outline" className="border-[#00a0e0] text-[#00508c] hover:bg-blue-50">製品について詳しく</Button>
          </a>
          <a href={recommendation.purchase_url} target="_blank" rel="noopener noreferrer">
            <Button className="bg-[#00a0e0] hover:bg-[#0088c0] text-white">ご購入はこちら</Button>
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
