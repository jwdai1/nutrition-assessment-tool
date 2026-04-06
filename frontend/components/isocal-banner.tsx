"use client";

import { Button } from "@/components/ui/button";
import type { IsocalRecommendation } from "@/lib/api";

interface Props {
  recommendation: IsocalRecommendation;
}

export function IsocalBanner({ recommendation }: Props) {
  if (!recommendation.show) return null;

  return (
    <div className="rounded-2xl border-2 border-[#00a0e0] overflow-hidden">
      {/* Catchphrase bar */}
      <div className="bg-gradient-to-r from-[#0078C8] to-[#00A0E0] px-6 py-4 text-center">
        <p className="text-white text-xl font-bold tracking-wide">低栄養にはアイソカル100!</p>
      </div>

      {/* Content */}
      <div className="bg-gradient-to-b from-[#f2f8ff] to-white px-6 py-5 space-y-4">
        {/* Product info */}
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 bg-[#00a0e0] rounded-xl flex flex-col items-center justify-center text-white shrink-0">
            <span className="text-[10px] font-bold leading-tight">Isocal</span>
            <span className="text-base font-bold leading-tight">100</span>
          </div>
          <div className="flex-1">
            <h4 className="font-bold text-lg text-[#00508c]">{recommendation.product_name}</h4>
            <p className="text-sm text-gray-600 mt-0.5">{recommendation.description}</p>
          </div>
        </div>

        {/* Permitted claim */}
        <div className="bg-white border border-gray-200 rounded-lg p-3.5 text-xs text-gray-500 leading-relaxed whitespace-pre-line">
          {recommendation.permitted_claim}
        </div>

        {/* CTA buttons */}
        <div className="flex gap-3">
          <a href={recommendation.brand_url} target="_blank" rel="noopener noreferrer">
            <Button variant="outline" className="border-[#00a0e0] text-[#00508c] hover:bg-blue-50 rounded-lg">
              製品について詳しく
            </Button>
          </a>
          <a href={recommendation.purchase_url} target="_blank" rel="noopener noreferrer">
            <Button className="bg-[#00a0e0] hover:bg-[#0088c0] text-white rounded-lg">
              ご購入はこちら
            </Button>
          </a>
        </div>
      </div>
    </div>
  );
}
