"""PDF出力 — QPrinter + QPainter（reportlab不要）"""
from __future__ import annotations
from typing import Optional

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QPageSize
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QFileDialog

from models import Patient, Assessment
import logic

# ──────────────────────────────────────────────
# カラー
# ──────────────────────────────────────────────
C_PRIMARY = QColor('#1a56a4')
C_NORMAL  = QColor('#1a7a4a')
C_RISK    = QColor('#b45309')
C_MAL     = QColor('#c0392b')
C_MUTED   = QColor('#6b7280')
C_BORDER  = QColor('#d1d5db')
C_BG      = QColor('#f3f4f6')
C_WHITE   = QColor('#ffffff')
C_YELLOW_BG = QColor('#fef3c7')
C_RED_BG    = QColor('#fdecea')
C_GREEN_BG  = QColor('#e6f5ec')


def export_pdf(
    patient: Patient,
    assessment: Assessment,
    parent=None,
) -> bool:
    """
    PDF保存ダイアログを開き、レポートを出力する。
    戻り値: 保存成功=True, キャンセル=False
    """
    path, _ = QFileDialog.getSaveFileName(
        parent,
        'PDFとして保存',
        f'栄養評価_{patient.patient_code}_{assessment.assess_date}.pdf',
        'PDF ファイル (*.pdf)',
    )
    if not path:
        return False

    printer = QPrinter(QPrinter.HighResolution)
    printer.setPageSize(QPageSize(QPageSize.A4))
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(path)

    painter = QPainter()
    if not painter.begin(printer):
        return False

    try:
        _draw_report(painter, printer, patient, assessment)
    finally:
        painter.end()

    return True


# ──────────────────────────────────────────────
# 描画ヘルパー
# ──────────────────────────────────────────────
class _DrawContext:
    """描画状態の管理"""
    def __init__(self, painter: QPainter, printer: QPrinter):
        self.painter = painter
        self.printer = printer
        rect = printer.pageRect(QPrinter.DevicePixel)
        self.page_w = rect.width()
        self.page_h = rect.height()
        # マージン: 約12mm (300dpi換算で約142px)
        self.margin = int(self.page_w * 0.08)
        self.content_w = int(self.page_w - self.margin * 2)
        self.y = self.margin  # 現在のY座標
        self.line_h = int(self.page_h * 0.022)

    def new_page(self):
        self.printer.newPage()
        self.y = self.margin

    def check_page(self, needed: int = 60):
        if self.y + needed > self.page_h - self.margin:
            self.new_page()

    def draw_text(
        self,
        text: str,
        font_size: int = 10,
        bold: bool = False,
        color: QColor = None,
        indent: int = 0,
        wrap: bool = True,
    ) -> int:
        """テキストを描画してy座標を進める。戻り値: 描画したピクセル高さ"""
        if color is None:
            color = QColor('#111827')
        p = self.painter
        f = QFont()
        f.setPointSizeF(font_size)
        f.setBold(bold)
        p.setFont(f)
        p.setPen(color)

        x = self.margin + indent
        w = self.content_w - indent
        flags = Qt.TextWordWrap | Qt.AlignLeft if wrap else Qt.AlignLeft

        rect = QRectF(x, self.y, w, self.page_h)
        bound = p.boundingRect(rect, flags, text)
        h = int(bound.height()) + 4
        p.drawText(QRectF(x, self.y, w, h), flags, text)
        self.y += h
        return h

    def draw_hline(self, color: QColor = None, thickness: int = 1):
        if color is None:
            color = C_BORDER
        p = self.painter
        p.setPen(QPen(color, thickness))
        p.drawLine(self.margin, self.y, self.margin + self.content_w, self.y)
        self.y += thickness + 4

    def draw_filled_rect(self, height: int, color: QColor, border: QColor = None, radius: int = 4):
        p = self.painter
        p.setBrush(color)
        if border:
            p.setPen(QPen(border, 1.5))
        else:
            p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.margin, self.y, self.content_w, height, radius, radius)
        self.y += height

    def draw_key_value(self, label: str, value: str, col_w_ratio: float = 0.35):
        p = self.painter
        label_w = int(self.content_w * col_w_ratio)
        value_w = self.content_w - label_w

        f_label = QFont()
        f_label.setPointSizeF(9)
        p.setFont(f_label)
        p.setPen(C_MUTED)
        p.drawText(QRectF(self.margin, self.y, label_w, 20), Qt.AlignLeft | Qt.AlignVCenter, label)

        f_value = QFont()
        f_value.setPointSizeF(9)
        f_value.setBold(True)
        p.setFont(f_value)
        p.setPen(QColor('#111827'))
        p.drawText(QRectF(self.margin + label_w, self.y, value_w, 20), Qt.AlignLeft | Qt.AlignVCenter, value)

        self.y += 22

    def section_header(self, text: str):
        self.check_page(50)
        self.y += 8
        f = QFont()
        f.setPointSizeF(10)
        f.setBold(True)
        self.painter.setFont(f)
        self.painter.setPen(C_PRIMARY)
        self.painter.drawText(
            QRectF(self.margin, self.y, self.content_w, 22),
            Qt.AlignLeft | Qt.AlignVCenter, text
        )
        self.y += 24
        self.draw_hline(C_PRIMARY, 1)


def _draw_report(
    painter: QPainter,
    printer: QPrinter,
    patient: Patient,
    assessment: Assessment,
):
    ctx = _DrawContext(painter, printer)
    a = assessment
    p = patient

    bmi = a.bmi
    wl3 = a.wl_pct_3m
    wl6 = a.wl_pct_6m
    mna_total = a.mna.total
    mna_interp = logic.interpret_mna_sf_score(mna_total)
    skip_glim = mna_total is not None and mna_total >= 12

    glim_result = None
    if not skip_glim:
        glim_result = logic.calc_glim_severity(
            glim_weight_loss=bool(a.glim.weight_loss),
            glim_low_bmi=bool(a.glim.low_bmi),
            glim_muscle=a.glim.muscle,
            glim_intake=bool(a.glim.intake),
            glim_inflam=bool(a.glim.inflam),
            glim_chronic=bool(a.glim.chronic),
            age=a.age_at_assess,
            bmi=bmi,
            wl_pct_3m=wl3,
            wl_pct_6m=wl6,
        )

    # ── ヘッダー ──
    painter.setBrush(C_PRIMARY)
    painter.setPen(Qt.NoPen)
    painter.drawRect(0, 0, ctx.page_w, int(ctx.margin * 1.4))

    f = QFont()
    f.setPointSizeF(14)
    f.setBold(True)
    painter.setFont(f)
    painter.setPen(QColor('white'))
    painter.drawText(
        QRectF(ctx.margin, 0, ctx.content_w, int(ctx.margin * 1.4)),
        Qt.AlignLeft | Qt.AlignVCenter,
        '低栄養診断レポート（MNA-SF / GLIM）',
    )
    ctx.y = int(ctx.margin * 1.4) + 16

    # ── 患者情報 ──
    ctx.section_header('患者情報')
    gender_map = {'male': '男性', 'female': '女性', 'other': 'その他'}
    ctx.draw_key_value('患者ID', p.patient_code)
    ctx.draw_key_value('氏名', p.name or '—')
    ctx.draw_key_value('評価日', a.assess_date)
    ctx.draw_key_value('性別 / 年齢', f"{gender_map.get(p.gender, p.gender)} / {a.age_at_assess}歳")
    ctx.draw_key_value('身長 / 体重', f'{a.height_cm:.1f}cm / {a.weight_kg:.1f}kg')
    ctx.draw_key_value('BMI', f'{bmi:.1f}' if bmi else '—')
    if a.weight_3m_kg:
        ctx.draw_key_value('3ヶ月前体重', f'{a.weight_3m_kg:.1f}kg')
    if a.weight_6m_kg:
        ctx.draw_key_value('6ヶ月前体重', f'{a.weight_6m_kg:.1f}kg')
    ctx.draw_key_value('体重減少率（3M / 6M）',
                       f'{wl3:.1f}% / ' if wl3 else '— / ' +
                       f'{wl6:.1f}%' if wl6 else '—')

    # ── 診断結果バナー ──
    ctx.check_page(80)
    ctx.y += 8

    if skip_glim:
        bg, border, result_text = C_GREEN_BG, C_NORMAL, '栄養良好（MNA-SF ≥12）'
    elif not glim_result or not glim_result.get('diagnosed'):
        bg, border, result_text = C_YELLOW_BG, C_RISK, '低栄養非該当（要観察）'
    else:
        sev = glim_result.get('severity')
        bg, border = C_RED_BG, C_MAL
        result_text = '低栄養（Stage 2: 高度）' if sev == 'stage2' else '低栄養（Stage 1: 中等度）'

    banner_h = 52
    painter.setBrush(bg)
    painter.setPen(QPen(border, 2))
    painter.drawRoundedRect(ctx.margin, ctx.y, ctx.content_w, banner_h, 6, 6)

    f2 = QFont()
    f2.setPointSizeF(13)
    f2.setBold(True)
    painter.setFont(f2)
    painter.setPen(border)
    painter.drawText(
        QRectF(ctx.margin + 14, ctx.y, ctx.content_w - 28, banner_h),
        Qt.AlignLeft | Qt.AlignVCenter,
        result_text,
    )
    ctx.y += banner_h + 10

    # ── MNA-SF ──
    ctx.section_header('MNA-SF スコア')
    color_map = {'normal': C_NORMAL, 'risk': C_RISK, 'severe': C_MAL}
    mna_color = color_map.get(mna_interp.get('category'), C_PRIMARY)

    ctx.draw_text(
        f"{mna_total} / 14点 — {mna_interp.get('label', '')}",
        font_size=12,
        bold=True,
        color=mna_color,
    )
    q_labels = {
        'A': ('食事量の変化', {0: '著しく減少', 1: '中程度の減少', 2: '変化なし'}),
        'B': ('体重減少（3M）', {0: '3kg以上', 1: '不明', 2: '1〜3kg', 3: '減少なし'}),
        'C': ('移動能力', {0: 'ベッド・椅子のみ', 1: '自由に歩けない', 2: '自由に歩ける'}),
        'D': ('ストレス/急性疾患', {0: 'はい', 2: 'いいえ'}),
        'E': ('精神的問題', {0: '高度認知症・うつ', 1: '軽度認知症', 2: 'なし'}),
        'F': ('BMI / CC', {0: 'BMI<19 / CC<31', 1: '19≤BMI<21', 2: '21≤BMI<23', 3: 'BMI≥23 / CC≥31'}),
    }
    mna_data = {
        'A': a.mna.q_a, 'B': a.mna.q_b, 'C': a.mna.q_c,
        'D': a.mna.q_d, 'E': a.mna.q_e, 'F': a.mna.q_f,
    }
    for key, (title, opts) in q_labels.items():
        val = mna_data.get(key)
        answer = opts.get(val, '—') if val is not None else '—'
        ctx.draw_key_value(f'問{key}（{title}）', f'{answer}  [{val}点]' if val is not None else '—')

    # ── GLIM（スキップされていない場合）──
    if not skip_glim:
        ctx.section_header('GLIM 評価結果')

        if glim_result:
            pmet = glim_result.get('phenotypic_met', False)
            emet = glim_result.get('etiologic_met', False)
            ctx.draw_key_value('表現型基準', '充足 — ' + '、'.join(glim_result.get('phenotypic_items', [])) if pmet else '非充足')
            ctx.draw_key_value('病因基準', '充足 — ' + '、'.join(glim_result.get('etiologic_items', [])) if emet else '非充足')
            ctx.draw_key_value('低栄養診断', 'あり' if glim_result.get('diagnosed') else 'なし')
            if glim_result.get('severity'):
                ctx.draw_key_value('重症度', 'Stage 2（高度）' if glim_result['severity'] == 'stage2' else 'Stage 1（中等度）')

            if glim_result.get('reasons'):
                ctx.y += 4
                ctx.draw_text('診断根拠:', font_size=9, bold=True)
                for reason in glim_result['reasons']:
                    ctx.draw_text(f'  ✓  {reason}', font_size=9, color=C_MAL, indent=10)

    # ── 推奨アクション ──
    ctx.check_page(80)
    ctx.section_header('推奨アクション')
    diagnosed = glim_result.get('diagnosed') if glim_result else None
    severity = glim_result.get('severity') if glim_result else None
    recs = logic.get_recommendations(
        mna_interp.get('category'),
        diagnosed,
        severity,
    )
    for rec in recs:
        ctx.check_page(30)
        bg_c = C_RED_BG if severity == 'stage2' else C_YELLOW_BG
        ctx.draw_filled_rect(28, bg_c, QColor('#fca5a5' if severity == 'stage2' else '#fcd34d'), radius=4)
        ctx.y -= 24
        ctx.draw_text(rec, font_size=9, indent=8)
        ctx.y += 4

    # ── フッター ──
    ctx.y = ctx.page_h - ctx.margin
    ctx.draw_hline(C_BORDER)
    ctx.draw_text(
        'このツールは臨床判断を支援するためのものです。MNA® は Nestlé の登録商標です。GLIM基準: Cederholm T, et al. JPEN 2019.',
        font_size=8,
        color=C_MUTED,
    )
