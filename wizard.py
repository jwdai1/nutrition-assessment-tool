"""4ステップ アセスメントウィザード（QDialog + QStackedWidget）"""
from __future__ import annotations
from typing import Optional

from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QWidget, QLabel, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QFrame, QGroupBox,
    QButtonGroup, QRadioButton, QScrollArea, QDateEdit,
    QFormLayout, QSizePolicy, QMessageBox,
)

from models import Patient, Assessment, MNAAnswers, GLIMAnswers
import logic


# ──────────────────────────────────────────────
# カラーパレット
# ──────────────────────────────────────────────
C_PRIMARY   = '#1a56a4'
C_PRIMARY_L = '#e8f0fb'
C_NORMAL    = '#1a7a4a'
C_NORMAL_BG = '#e6f5ec'
C_RISK      = '#b45309'
C_RISK_BG   = '#fef3c7'
C_MAL       = '#c0392b'
C_MAL_BG    = '#fdecea'
C_BORDER    = '#d1d5db'
C_MUTED     = '#6b7280'
C_TEXT      = '#111827'
C_BG        = '#f3f4f6'

QSS_BASE = f"""
QDialog {{ background: {C_BG}; }}
QGroupBox {{
    font-weight: bold; font-size: 13px;
    border: 1px solid {C_BORDER}; border-radius: 6px;
    margin-top: 8px; padding-top: 8px;
    background: white;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; }}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
    border: 1px solid {C_BORDER}; border-radius: 5px;
    padding: 5px 8px; font-size: 13px; background: white;
    min-height: 28px;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QComboBox:focus, QDateEdit:focus {{
    border-color: {C_PRIMARY};
}}
QPushButton {{
    border-radius: 5px; padding: 7px 18px;
    font-size: 13px; font-weight: 600;
}}
QPushButton#btnPrimary {{
    background: {C_PRIMARY}; color: white; border: none;
}}
QPushButton#btnPrimary:hover {{ background: #1648b0; }}
QPushButton#btnSecondary {{
    background: white; color: {C_TEXT};
    border: 1.5px solid {C_BORDER};
}}
QPushButton#btnSecondary:hover {{ background: #f9fafb; }}
QPushButton#btnSuccess {{
    background: {C_NORMAL}; color: white; border: none;
}}
QPushButton#btnSuccess:hover {{ background: #155d38; }}
QRadioButton {{ font-size: 13px; spacing: 6px; }}
QCheckBox {{ font-size: 13px; spacing: 6px; }}
QLabel#sectionTitle {{
    font-size: 15px; font-weight: 700; color: {C_PRIMARY};
    padding-bottom: 6px; border-bottom: 2px solid {C_PRIMARY_L};
}}
QScrollArea {{ border: none; background: transparent; }}
"""


# ──────────────────────────────────────────────
# プログレスバー（カスタム描画）
# ──────────────────────────────────────────────
class StepProgressBar(QWidget):
    STEPS = ['患者情報', 'MNA-SF', 'GLIM評価', '結果']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current = 0
        self.setFixedHeight(56)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_step(self, index: int):
        self.current = index
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        n = len(self.STEPS)
        w = self.width()
        h = self.height()
        cx_list = [int(w * (i + 0.5) / n) for i in range(n)]
        cy = 20
        r = 14

        # Connectors
        for i in range(n - 1):
            x1 = cx_list[i] + r
            x2 = cx_list[i + 1] - r
            col = QColor(C_NORMAL) if i < self.current else QColor(C_BORDER)
            pen = QPen(col, 2)
            p.setPen(pen)
            p.drawLine(x1, cy, x2, cy)

        # Circles + labels
        for i, label in enumerate(self.STEPS):
            cx = cx_list[i]
            if i < self.current:
                bg = QColor(C_NORMAL)
                text_col = QColor('white')
            elif i == self.current:
                bg = QColor(C_PRIMARY)
                text_col = QColor('white')
            else:
                bg = QColor('white')
                text_col = QColor(C_MUTED)

            # Circle
            p.setBrush(bg)
            p.setPen(QPen(bg if i <= self.current else QColor(C_BORDER), 2))
            p.drawEllipse(cx - r, cy - r, r * 2, r * 2)

            # Number
            p.setPen(text_col)
            f = QFont()
            f.setPointSize(9)
            f.setBold(True)
            p.setFont(f)
            p.drawText(cx - r, cy - r, r * 2, r * 2, Qt.AlignCenter, str(i + 1))

            # Label below
            lf = QFont()
            lf.setPointSize(9)
            lf.setBold(i == self.current)
            p.setFont(lf)
            lc = QColor(C_PRIMARY if i == self.current else C_MUTED)
            p.setPen(lc)
            p.drawText(cx - 50, cy + r + 2, 100, 18, Qt.AlignCenter, label)

        p.end()


# ──────────────────────────────────────────────
# Helper widgets
# ──────────────────────────────────────────────
def _make_frame(bg: str, border: str) -> QFrame:
    f = QFrame()
    f.setStyleSheet(
        f'QFrame {{ background: {bg}; border: 1px solid {border}; border-radius: 6px; }}'
    )
    return f


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName('sectionTitle')
    return lbl


def _color_label(text: str, color: str, bold: bool = False) -> QLabel:
    lbl = QLabel(text)
    weight = 'bold' if bold else 'normal'
    lbl.setStyleSheet(f'color: {color}; font-weight: {weight};')
    return lbl


def _info_frame(text: str) -> QFrame:
    f = QFrame()
    f.setStyleSheet(
        'QFrame { background: #fffbeb; border: 1px solid #fcd34d; '
        'border-radius: 6px; padding: 6px; }'
    )
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet('color: #78350f; font-size: 12px; border: none; background: transparent;')
    lay = QVBoxLayout(f)
    lay.setContentsMargins(8, 6, 8, 6)
    lay.addWidget(lbl)
    return f


# ──────────────────────────────────────────────
# Page 0: 患者情報
# ──────────────────────────────────────────────
class Page0(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        root.addWidget(_section_label('患者基本情報'))

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 患者ID
        self.patient_id_edit = QLineEdit()
        self.patient_id_edit.setPlaceholderText('例: PT-0001（患者一覧から自動入力）')
        self.patient_id_edit.setReadOnly(True)
        self.patient_id_edit.setStyleSheet('background: #f0f0f0;')
        form.addRow('患者ID:', self.patient_id_edit)

        # 評価日
        self.assess_date = QDateEdit()
        self.assess_date.setCalendarPopup(True)
        self.assess_date.setDate(QDate.currentDate())
        self.assess_date.setDisplayFormat('yyyy-MM-dd')
        form.addRow('評価日 *:', self.assess_date)

        # 性別（患者から引き継ぎ、表示のみ）
        self.gender_label = QLabel('（患者情報から引き継ぎ）')
        self.gender_label.setStyleSheet(f'color: {C_MUTED}; font-size: 12px;')
        form.addRow('性別:', self.gender_label)

        # 年齢
        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 120)
        self.age_spin.setSuffix(' 歳')
        form.addRow('年齢 *:', self.age_spin)

        # 身長
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(50, 250)
        self.height_spin.setSingleStep(0.1)
        self.height_spin.setDecimals(1)
        self.height_spin.setSuffix(' cm')
        self.height_spin.setValue(160.0)
        form.addRow('身長 *:', self.height_spin)

        # 現在体重
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(10, 300)
        self.weight_spin.setSingleStep(0.1)
        self.weight_spin.setDecimals(1)
        self.weight_spin.setSuffix(' kg')
        self.weight_spin.setValue(55.0)
        form.addRow('現在体重 *:', self.weight_spin)

        # 3ヶ月前体重
        row_3m = QHBoxLayout()
        self.weight_3m_spin = QDoubleSpinBox()
        self.weight_3m_spin.setRange(10, 300)
        self.weight_3m_spin.setSingleStep(0.1)
        self.weight_3m_spin.setDecimals(1)
        self.weight_3m_spin.setSuffix(' kg')
        self.weight_3m_spin.setValue(0.0)
        self.weight_3m_unknown = QCheckBox('不明')
        row_3m.addWidget(self.weight_3m_spin)
        row_3m.addWidget(self.weight_3m_unknown)
        form.addRow('3ヶ月前体重:', row_3m)

        # 6ヶ月前体重
        row_6m = QHBoxLayout()
        self.weight_6m_spin = QDoubleSpinBox()
        self.weight_6m_spin.setRange(10, 300)
        self.weight_6m_spin.setSingleStep(0.1)
        self.weight_6m_spin.setDecimals(1)
        self.weight_6m_spin.setSuffix(' kg')
        self.weight_6m_spin.setValue(0.0)
        self.weight_6m_unknown = QCheckBox('不明')
        row_6m.addWidget(self.weight_6m_spin)
        row_6m.addWidget(self.weight_6m_unknown)
        form.addRow('6ヶ月前体重:', row_6m)

        # CC
        row_cc = QHBoxLayout()
        self.cc_spin = QDoubleSpinBox()
        self.cc_spin.setRange(10, 60)
        self.cc_spin.setSingleStep(0.1)
        self.cc_spin.setDecimals(1)
        self.cc_spin.setSuffix(' cm')
        self.cc_spin.setValue(0.0)
        self.cc_unknown = QCheckBox('不明')
        row_cc.addWidget(self.cc_spin)
        row_cc.addWidget(self.cc_unknown)
        form.addRow('下腿周囲長 CC:', row_cc)

        root.addLayout(form)

        # リアルタイム計算表示
        self.calc_frame = QFrame()
        self.calc_frame.setStyleSheet(
            f'QFrame {{ background: {C_PRIMARY_L}; border: 1px solid #bdd3f5; '
            f'border-radius: 6px; padding: 10px; }}'
        )
        calc_lay = QHBoxLayout(self.calc_frame)
        calc_lay.setSpacing(24)

        self.bmi_lbl = QLabel('—')
        self.wl3m_lbl = QLabel('—')
        self.wl6m_lbl = QLabel('—')

        for title, lbl in [('BMI', self.bmi_lbl), ('3ヶ月体重減少率', self.wl3m_lbl), ('6ヶ月体重減少率', self.wl6m_lbl)]:
            col = QVBoxLayout()
            t = QLabel(title)
            t.setStyleSheet(f'color: {C_MUTED}; font-size: 11px; border: none; background: transparent;')
            lbl.setStyleSheet(f'font-size: 20px; font-weight: bold; color: {C_PRIMARY}; border: none; background: transparent;')
            col.addWidget(t)
            col.addWidget(lbl)
            calc_lay.addLayout(col)

        root.addWidget(self.calc_frame)

        # エラーラベル
        self.error_lbl = QLabel()
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setStyleSheet(
            'color: #991b1b; background: #fef2f2; border: 1px solid #fca5a5; '
            'border-radius: 5px; padding: 6px 10px; font-size: 12px;'
        )
        self.error_lbl.hide()
        root.addWidget(self.error_lbl)

        # Signals
        self.height_spin.valueChanged.connect(self._update_calc)
        self.weight_spin.valueChanged.connect(self._update_calc)
        self.weight_3m_spin.valueChanged.connect(self._update_calc)
        self.weight_6m_spin.valueChanged.connect(self._update_calc)
        self.weight_3m_unknown.toggled.connect(self._toggle_3m)
        self.weight_6m_unknown.toggled.connect(self._toggle_6m)
        self.cc_unknown.toggled.connect(self._toggle_cc)

        self._update_calc()

    def _toggle_3m(self, checked):
        self.weight_3m_spin.setEnabled(not checked)
        if checked:
            self.weight_3m_spin.setValue(0.0)
        self._update_calc()

    def _toggle_6m(self, checked):
        self.weight_6m_spin.setEnabled(not checked)
        if checked:
            self.weight_6m_spin.setValue(0.0)
        self._update_calc()

    def _toggle_cc(self, checked):
        self.cc_spin.setEnabled(not checked)
        if checked:
            self.cc_spin.setValue(0.0)

    def _update_calc(self):
        h = self.height_spin.value()
        w = self.weight_spin.value()
        w3 = self.weight_3m_spin.value() if not self.weight_3m_unknown.isChecked() else None
        w6 = self.weight_6m_spin.value() if not self.weight_6m_unknown.isChecked() else None

        bmi = logic.calc_bmi(w, h)
        wl3 = logic.calc_weight_loss_pct(w, w3) if w3 and w3 > 0 else None
        wl6 = logic.calc_weight_loss_pct(w, w6) if w6 and w6 > 0 else None

        if bmi is not None:
            color = C_MAL if bmi < 18.5 else (C_RISK if bmi < 20 else C_PRIMARY)
            self.bmi_lbl.setText(f'{bmi:.1f}')
            self.bmi_lbl.setStyleSheet(
                f'font-size: 20px; font-weight: bold; color: {color}; border: none; background: transparent;'
            )
        else:
            self.bmi_lbl.setText('—')
            self.bmi_lbl.setStyleSheet(
                f'font-size: 20px; font-weight: bold; color: {C_PRIMARY}; border: none; background: transparent;'
            )

        if wl3 is not None:
            color = C_MAL if wl3 > 10 else (C_RISK if wl3 > 5 else C_PRIMARY)
            self.wl3m_lbl.setText(f'{wl3:.1f}%')
            self.wl3m_lbl.setStyleSheet(
                f'font-size: 20px; font-weight: bold; color: {color}; border: none; background: transparent;'
            )
        else:
            self.wl3m_lbl.setText('—')
            self.wl3m_lbl.setStyleSheet(
                f'font-size: 20px; font-weight: bold; color: {C_PRIMARY}; border: none; background: transparent;'
            )

        if wl6 is not None:
            color = C_MAL if wl6 > 20 else (C_RISK if wl6 > 10 else C_PRIMARY)
            self.wl6m_lbl.setText(f'{wl6:.1f}%')
            self.wl6m_lbl.setStyleSheet(
                f'font-size: 20px; font-weight: bold; color: {color}; border: none; background: transparent;'
            )
        else:
            self.wl6m_lbl.setText('—')
            self.wl6m_lbl.setStyleSheet(
                f'font-size: 20px; font-weight: bold; color: {C_PRIMARY}; border: none; background: transparent;'
            )

    def set_patient(self, patient: Patient):
        self.patient_id_edit.setText(patient.patient_code)
        gender_map = {'male': '男性', 'female': '女性', 'other': 'その他'}
        self.gender_label.setText(gender_map.get(patient.gender, patient.gender))

    def validate(self) -> list[str]:
        errors = []
        if self.age_spin.value() == 0:
            errors.append('年齢を入力してください。')
        if self.height_spin.value() < 50:
            errors.append('身長を正しく入力してください（50〜250cm）。')
        if self.weight_spin.value() < 10:
            errors.append('現在体重を正しく入力してください（10〜300kg）。')
        return errors

    def show_errors(self, errors: list[str]):
        if errors:
            self.error_lbl.setText('入力内容を確認してください:\n• ' + '\n• '.join(errors))
            self.error_lbl.show()
        else:
            self.error_lbl.hide()

    def get_values(self) -> dict:
        return {
            'assess_date': self.assess_date.date().toString('yyyy-MM-dd'),
            'age': self.age_spin.value(),
            'height': self.height_spin.value(),
            'weight': self.weight_spin.value(),
            'weight_3m': self.weight_3m_spin.value() if not self.weight_3m_unknown.isChecked() and self.weight_3m_spin.value() > 0 else None,
            'weight_6m': self.weight_6m_spin.value() if not self.weight_6m_unknown.isChecked() and self.weight_6m_spin.value() > 0 else None,
            'cc': self.cc_spin.value() if not self.cc_unknown.isChecked() and self.cc_spin.value() > 0 else None,
        }


# ──────────────────────────────────────────────
# Page 1: MNA-SF
# ──────────────────────────────────────────────
class Page1(QWidget):
    MNA_QUESTIONS = [
        ('A', '過去3ヶ月間で食欲不振、消化器系の問題、咀嚼・嚥下困難などにより食事量が減少しましたか？', [
            (0, '著しく減少した'),
            (1, '中程度の減少'),
            (2, '食事量の変化なし'),
        ]),
        ('B', '過去3ヶ月間の体重減少', [
            (0, '3kg以上の体重減少'),
            (1, 'わからない'),
            (2, '1〜3kgの体重減少'),
            (3, '体重減少なし'),
        ], True),  # auto_estimate=True
        ('C', '移動能力はどうですか？', [
            (0, 'ベッドや椅子から動けない'),
            (1, 'ベッドや椅子から離れられるが、自由には歩けない'),
            (2, '自由に歩ける'),
        ]),
        ('D', '過去3ヶ月間に精神的なストレスがかかりましたか、または急性疾患を罹患しましたか？', [
            (0, 'はい'),
            (2, 'いいえ'),
        ]),
        ('E', '神経・精神的問題はありますか？', [
            (0, '高度の認知症またはうつ状態'),
            (1, '軽度の認知症'),
            (2, '精神的問題なし'),
        ]),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        root.addWidget(_section_label('MNA-SF スクリーニング'))
        sub = QLabel('Mini Nutritional Assessment Short Form（14点満点）')
        sub.setStyleSheet(f'color: {C_MUTED}; font-size: 12px;')
        root.addWidget(sub)

        self.radio_groups: dict[str, QButtonGroup] = {}
        self.group_boxes: dict[str, QGroupBox] = {}

        # Questions A-E
        for item in self.MNA_QUESTIONS:
            q_key = item[0]
            q_text = item[1]
            options = item[2]
            auto = len(item) > 3 and item[3]

            box = QGroupBox(f'問 {q_key}')
            if auto:
                box.setTitle(f'問 {q_key}  【自動推定】')
                box.setStyleSheet(
                    'QGroupBox { border: 1px solid #93c5fd; border-radius: 6px; '
                    'background: #f0f7ff; margin-top: 8px; padding-top: 8px; }'
                    'QGroupBox::title { subcontrol-origin: margin; left: 10px; '
                    'padding: 0 4px; color: #1d4ed8; font-weight: bold; }'
                )
            box_lay = QVBoxLayout(box)
            box_lay.setSpacing(4)

            q_lbl = QLabel(q_text)
            q_lbl.setWordWrap(True)
            q_lbl.setStyleSheet('font-size: 13px; background: transparent; border: none;')
            box_lay.addWidget(q_lbl)

            if q_key == 'B':
                self.q_b_note = QLabel('3ヶ月前体重データから自動推定。確認の上、必要に応じて変更してください。')
                self.q_b_note.setWordWrap(True)
                self.q_b_note.setStyleSheet(f'color: {C_MUTED}; font-size: 11px; background: transparent; border: none;')
                box_lay.addWidget(self.q_b_note)

            bg = QButtonGroup(self)
            bg.setExclusive(True)
            for val, text in options:
                rb = QRadioButton(f'{text}  [{val}点]')
                rb.setProperty('score_value', val)
                rb.setStyleSheet('font-size: 13px; padding: 3px 0;')
                bg.addButton(rb, val)
                box_lay.addWidget(rb)

            bg.buttonToggled.connect(self._update_score)
            self.radio_groups[q_key] = bg
            self.group_boxes[q_key] = box
            root.addWidget(box)

        # Question F (BMI / CC)
        self._build_q_f(root)

        # Score meter
        score_frame = QFrame()
        score_frame.setStyleSheet(
            f'QFrame {{ background: white; border: 1px solid {C_BORDER}; '
            f'border-radius: 6px; }}'
        )
        score_lay = QVBoxLayout(score_frame)
        score_lay.setContentsMargins(14, 10, 14, 10)
        score_lay.setSpacing(4)

        score_title = QLabel('現在のMNA-SFスコア')
        score_title.setStyleSheet(f'color: {C_MUTED}; font-size: 12px; border: none; background: transparent;')
        score_lay.addWidget(score_title)

        self.score_bar = _ScoreBar()
        score_lay.addWidget(self.score_bar)

        self.score_display = QLabel('— / 14点')
        self.score_display.setAlignment(Qt.AlignCenter)
        self.score_display.setStyleSheet(
            f'font-size: 22px; font-weight: 800; color: {C_PRIMARY}; border: none; background: transparent;'
        )
        score_lay.addWidget(self.score_display)

        root.addWidget(score_frame)

        # Error label
        self.error_lbl = QLabel()
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setStyleSheet(
            'color: #991b1b; background: #fef2f2; border: 1px solid #fca5a5; '
            'border-radius: 5px; padding: 6px 10px; font-size: 12px;'
        )
        self.error_lbl.hide()
        root.addWidget(self.error_lbl)

    def _build_q_f(self, root):
        box = QGroupBox('問 F  【自動推定】')
        box.setStyleSheet(
            'QGroupBox { border: 1px solid #93c5fd; border-radius: 6px; '
            'background: #f0f7ff; margin-top: 8px; padding-top: 8px; }'
            'QGroupBox::title { subcontrol-origin: margin; left: 10px; '
            'padding: 0 4px; color: #1d4ed8; font-weight: bold; }'
        )
        box_lay = QVBoxLayout(box)
        box_lay.setSpacing(4)

        self.q_f_title = QLabel('BMI または 下腿周囲長（CC）')
        self.q_f_title.setStyleSheet('font-size: 13px; font-weight: bold; background: transparent; border: none;')
        box_lay.addWidget(self.q_f_title)

        self.q_f_note = QLabel('')
        self.q_f_note.setWordWrap(True)
        self.q_f_note.setStyleSheet(f'color: {C_MUTED}; font-size: 11px; background: transparent; border: none;')
        box_lay.addWidget(self.q_f_note)

        bg_f = QButtonGroup(self)
        bg_f.setExclusive(True)
        self.q_f_bg = bg_f

        self.q_f_bmi_options = [
            (0, 'BMI 19未満'),
            (1, 'BMI 19以上〜21未満'),
            (2, 'BMI 21以上〜23未満'),
            (3, 'BMI 23以上'),
        ]
        self.q_f_cc_options = [
            (0, 'CC 31cm未満'),
            (3, 'CC 31cm以上'),
        ]

        self._f_radios: list[QRadioButton] = []
        for val, text in self.q_f_bmi_options + self.q_f_cc_options:
            rb = QRadioButton(f'{text}  [{val}点]')
            rb.setProperty('score_value', val)
            rb.setStyleSheet('font-size: 13px; padding: 3px 0;')
            bg_f.addButton(rb, val)
            self._f_radios.append(rb)
            box_lay.addWidget(rb)

        bg_f.buttonToggled.connect(self._update_score)
        self.group_boxes['F'] = box
        root.addWidget(box)

    def auto_estimate(self, values: dict):
        """Page0のvaluesを受け取って自動推定を適用"""
        w = values.get('weight')
        w3 = values.get('weight_3m')
        h = values.get('height')
        cc = values.get('cc')

        bmi = logic.calc_bmi(w, h)

        # Q-B
        rec_b = logic.auto_estimate_mna_q_b(w, w3)
        bg_b = self.radio_groups['B']
        if rec_b is not None and bg_b.checkedId() == -1:
            btn = bg_b.button(rec_b)
            if btn:
                btn.setChecked(True)
            if w3:
                loss = (w3 - w) if w and w3 else 0
                pct = logic.calc_weight_loss_pct(w, w3)
                pct_str = f'{pct:.1f}%' if pct else '—'
                self.q_b_note.setText(
                    f'3ヶ月体重減少: {abs(loss):.1f}kg（{pct_str}）より推定。変更可能です。'
                )
        else:
            self.q_b_note.setText('3ヶ月前体重データがないため、手動で選択してください。')

        # Q-F
        bg_f = self.q_f_bg
        using_cc = (bmi is None and cc is not None)

        bmi_vals = {v for v, _ in self.q_f_bmi_options}
        cc_vals = {v for v, _ in self.q_f_cc_options}

        for rb in self._f_radios:
            val = rb.property('score_value')
            text = rb.text()
            if using_cc:
                rb.setVisible('CC' in text)
            else:
                rb.setVisible('BMI' in text)

        if bmi is not None:
            self.q_f_title.setText('問 F: BMI（自動推定）')
            self.q_f_note.setText(f'BMI {bmi:.1f} より推定。変更可能です。')
            rec_f = logic.auto_estimate_mna_q_f_bmi(bmi)
        elif cc is not None:
            self.q_f_title.setText('問 F: 下腿周囲長 CC（自動推定）')
            self.q_f_note.setText(f'CC {cc:.1f}cm より推定（BMI計算不可のためCC使用）。')
            rec_f = logic.auto_estimate_mna_q_f_cc(cc)
        else:
            self.q_f_title.setText('問 F: BMI または 下腿周囲長（CC）')
            self.q_f_note.setText('身長・体重・CCのいずれかを入力すると自動推定されます。')
            rec_f = None

        if rec_f is not None and bg_f.checkedId() == -1:
            btn = bg_f.button(rec_f)
            if btn:
                btn.setChecked(True)

        self._update_score()

    def _update_score(self):
        total = 0
        answered = 0
        for key, bg in list(self.radio_groups.items()) + [('F', self.q_f_bg)]:
            btn = bg.checkedButton()
            if btn:
                total += btn.property('score_value')
                answered += 1

        if answered == 6:
            interp = logic.interpret_mna_sf_score(total)
            color_map = {'normal': C_NORMAL, 'risk': C_RISK, 'mal': C_MAL, 'muted': C_MUTED}
            color = color_map.get(interp['color_key'], C_PRIMARY)
            self.score_display.setText(f'{total} / 14点')
            self.score_display.setStyleSheet(
                f'font-size: 22px; font-weight: 800; color: {color}; border: none; background: transparent;'
            )
            self.score_bar.set_score(total)
        else:
            self.score_display.setText('— / 14点')
            self.score_display.setStyleSheet(
                f'font-size: 22px; font-weight: 800; color: {C_PRIMARY}; border: none; background: transparent;'
            )
            self.score_bar.set_score(None)

    def validate(self) -> list[str]:
        errors = []
        for key, bg in list(self.radio_groups.items()) + [('F', self.q_f_bg)]:
            if bg.checkedId() == -1:
                errors.append(f'問{key}を選択してください。')
        return errors

    def show_errors(self, errors: list[str]):
        if errors:
            self.error_lbl.setText('入力内容を確認してください:\n• ' + '\n• '.join(errors))
            self.error_lbl.show()
        else:
            self.error_lbl.hide()

    def get_mna_answers(self) -> MNAAnswers:
        def get_val(bg):
            btn = bg.checkedButton()
            return btn.property('score_value') if btn else None

        return MNAAnswers(
            q_a=get_val(self.radio_groups['A']),
            q_b=get_val(self.radio_groups['B']),
            q_c=get_val(self.radio_groups['C']),
            q_d=get_val(self.radio_groups['D']),
            q_e=get_val(self.radio_groups['E']),
            q_f=get_val(self.q_f_bg),
        )


class _ScoreBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._score: Optional[int] = None
        self.setFixedHeight(28)

    def set_score(self, score: Optional[int]):
        self._score = score
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = 14
        y = 2
        r = 7

        # Background gradient bar (red/yellow/green)
        # Draw 3 segments
        seg1 = int(w * 7 / 14)
        seg2 = int(w * 11 / 14)

        from PySide6.QtGui import QBrush
        p.setBrush(QBrush(QColor('#ef4444')))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, y, seg1, h, r, r)

        p.setBrush(QBrush(QColor('#f59e0b')))
        p.drawRect(seg1, y, seg2 - seg1, h)

        p.setBrush(QBrush(QColor('#22c55e')))
        p.drawRoundedRect(seg2, y, w - seg2, h, r, r)

        # Indicator
        if self._score is not None:
            pct = min(self._score / 14, 0.97)
            ix = int(w * pct)
            p.setBrush(QBrush(QColor('white')))
            p.setPen(QPen(QColor(C_PRIMARY), 3))
            p.drawEllipse(ix - 10, y - 3, 20, 20)

        # Labels
        p.setPen(QColor(C_MUTED))
        f = QFont()
        f.setPointSize(9)
        p.setFont(f)
        for val, label in [(0, '0'), (7, '7'), (11, '11'), (14, '14')]:
            x = int(w * val / 14)
            p.drawText(x - 8, h + y + 4, 16, 14, Qt.AlignCenter, label)

        p.end()


# ──────────────────────────────────────────────
# Page 2: GLIM
# ──────────────────────────────────────────────
class Page2(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)

        self.skip_frame = QFrame()
        self.skip_frame.setStyleSheet(
            f'QFrame {{ background: {C_NORMAL_BG}; border: 1px solid #86efac; '
            f'border-radius: 6px; padding: 12px; }}'
        )
        skip_lbl = QLabel('✓ MNA-SFスコアが12〜14点のため、GLIM評価は省略されます。')
        skip_lbl.setStyleSheet(f'color: {C_NORMAL}; font-weight: bold; font-size: 13px; border: none; background: transparent;')
        skip_lbl.setWordWrap(True)
        QVBoxLayout(self.skip_frame).addWidget(skip_lbl)
        self.skip_frame.hide()
        root.addWidget(self.skip_frame)

        self.form_widget = QWidget()
        form_lay = QVBoxLayout(self.form_widget)
        form_lay.setContentsMargins(0, 0, 0, 0)
        form_lay.setSpacing(10)

        # ── 表現型基準 ──
        form_lay.addWidget(_section_label('GLIM 表現型基準（Phenotypic Criteria）'))
        sub1 = QLabel('以下のうち1項目以上を満たす場合、表現型基準を充足')
        sub1.setStyleSheet(f'color: {C_MUTED}; font-size: 12px;')
        form_lay.addWidget(sub1)

        # 体重減少
        wl_box = QGroupBox('意図しない体重減少  [表現型]')
        wl_box_lay = QVBoxLayout(wl_box)
        self.wl_auto_lbl = QLabel('—')
        self.wl_auto_lbl.setStyleSheet('font-weight: bold; font-size: 14px; background: transparent; border: none;')
        self.wl_detail_lbl = QLabel('—')
        self.wl_detail_lbl.setStyleSheet(f'color: {C_MUTED}; font-size: 12px; background: transparent; border: none;')
        self.glim_wl_cb = QCheckBox('体重減少あり（意図しない）と判断する')
        self.glim_wl_cb.setStyleSheet('font-size: 13px;')
        wl_note = QLabel('基準: 過去6ヶ月で5%超 または 6ヶ月超で10%超')
        wl_note.setStyleSheet(f'color: {C_MUTED}; font-size: 11px; background: transparent; border: none;')
        wl_box_lay.addWidget(self.wl_auto_lbl)
        wl_box_lay.addWidget(self.wl_detail_lbl)
        wl_box_lay.addWidget(self.glim_wl_cb)
        wl_box_lay.addWidget(wl_note)
        form_lay.addWidget(wl_box)

        # 低BMI
        bmi_box = QGroupBox('低BMI（アジア人基準）  [表現型]')
        bmi_box_lay = QVBoxLayout(bmi_box)
        self.bmi_auto_lbl = QLabel('—')
        self.bmi_auto_lbl.setStyleSheet('font-weight: bold; font-size: 14px; background: transparent; border: none;')
        self.bmi_detail_lbl = QLabel('—')
        self.bmi_detail_lbl.setStyleSheet(f'color: {C_MUTED}; font-size: 12px; background: transparent; border: none;')
        self.glim_bmi_cb = QCheckBox('低BMIあり（アジア人基準）と判断する')
        self.glim_bmi_cb.setStyleSheet('font-size: 13px;')
        bmi_note = QLabel('70歳未満: <20 / 70歳以上: <22（アジア人基準）')
        bmi_note.setStyleSheet(f'color: {C_MUTED}; font-size: 11px; background: transparent; border: none;')
        bmi_box_lay.addWidget(self.bmi_auto_lbl)
        bmi_box_lay.addWidget(self.bmi_detail_lbl)
        bmi_box_lay.addWidget(self.glim_bmi_cb)
        bmi_box_lay.addWidget(bmi_note)
        form_lay.addWidget(bmi_box)

        # 筋肉量
        muscle_box = QGroupBox('筋肉量・筋量の低下（サルコペニア）  [表現型]')
        muscle_box_lay = QVBoxLayout(muscle_box)
        muscle_info = _info_frame(
            '客観的測定（DXA・BIA・握力等）が望ましいですが、臨床的判断を入力してください。'
        )
        muscle_box_lay.addWidget(muscle_info)
        muscle_row = QHBoxLayout()
        muscle_lbl = QLabel('筋肉量の評価:')
        muscle_lbl.setStyleSheet('font-size: 13px; background: transparent; border: none;')
        self.muscle_combo = QComboBox()
        self.muscle_combo.addItem('問題なし（筋肉量の低下なし）', 'none')
        self.muscle_combo.addItem('軽〜中等度の筋肉量低下', 'mild')
        self.muscle_combo.addItem('高度の筋肉量低下', 'severe')
        muscle_row.addWidget(muscle_lbl)
        muscle_row.addWidget(self.muscle_combo, 1)
        muscle_box_lay.addLayout(muscle_row)
        form_lay.addWidget(muscle_box)

        # ── 病因基準 ──
        form_lay.addWidget(_section_label('GLIM 病因基準（Etiologic Criteria）'))
        sub2 = QLabel('以下のうち1項目以上を満たす場合、病因基準を充足')
        sub2.setStyleSheet(f'color: {C_MUTED}; font-size: 12px;')
        form_lay.addWidget(sub2)

        # 食事摂取量
        intake_box = QGroupBox('食事摂取量の低下 または 消化吸収障害  [病因]')
        intake_box_lay = QVBoxLayout(intake_box)
        self.glim_intake_cb = QCheckBox('食事摂取量が必要量の50%以下（2週間以上）')
        self.glim_intake_cb.setStyleSheet('font-size: 13px;')
        intake_note = QLabel('消化・吸収障害（炎症性腸疾患、短腸症候群等）を含む')
        intake_note.setStyleSheet(f'color: {C_MUTED}; font-size: 11px; background: transparent; border: none;')
        intake_box_lay.addWidget(self.glim_intake_cb)
        intake_box_lay.addWidget(intake_note)
        form_lay.addWidget(intake_box)

        # 炎症
        inflam_box = QGroupBox('炎症・疾患負荷  [病因]')
        inflam_box_lay = QVBoxLayout(inflam_box)
        self.glim_inflam_cb = QCheckBox('急性疾患 / 外傷 による炎症')
        self.glim_inflam_cb.setStyleSheet('font-size: 13px;')
        inflam_note = QLabel('例: 敗血症、術後、重篤な外傷、TBI')
        inflam_note.setStyleSheet(f'color: {C_MUTED}; font-size: 11px; background: transparent; border: none;')
        self.glim_chronic_cb = QCheckBox('慢性疾患 による炎症（中等度）')
        self.glim_chronic_cb.setStyleSheet('font-size: 13px;')
        chronic_note = QLabel('例: 悪性腫瘍、心不全、慢性腎臓病、COPD、その他臓器機能不全')
        chronic_note.setStyleSheet(f'color: {C_MUTED}; font-size: 11px; background: transparent; border: none;')
        inflam_box_lay.addWidget(self.glim_inflam_cb)
        inflam_box_lay.addWidget(inflam_note)
        inflam_box_lay.addWidget(self.glim_chronic_cb)
        inflam_box_lay.addWidget(chronic_note)
        form_lay.addWidget(inflam_box)

        root.addWidget(self.form_widget)

        # Error label
        self.error_lbl = QLabel()
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setStyleSheet(
            'color: #991b1b; background: #fef2f2; border: 1px solid #fca5a5; '
            'border-radius: 5px; padding: 6px 10px; font-size: 12px;'
        )
        self.error_lbl.hide()
        root.addWidget(self.error_lbl)

    def auto_fill(self, values: dict, mna_score: Optional[int]):
        """Step1のデータを受け取ってGLIMを自動入力"""
        skip = mna_score is not None and mna_score >= 12
        self.skip_frame.setVisible(skip)
        self.form_widget.setVisible(not skip)
        if skip:
            return

        age = values.get('age', 0)
        bmi = logic.calc_bmi(values.get('weight'), values.get('height'))
        wl3 = logic.calc_weight_loss_pct(values.get('weight'), values.get('weight_3m'))
        wl6 = logic.calc_weight_loss_pct(values.get('weight'), values.get('weight_6m'))

        # Weight loss
        wl = logic.interpret_weight_loss_glim(wl3, wl6)
        if wl['present']:
            self.wl_auto_lbl.setText('基準を満たす（体重減少あり）')
            self.wl_auto_lbl.setStyleSheet(f'font-weight: bold; font-size: 14px; color: {C_MAL}; background: transparent; border: none;')
        elif wl3 is None and wl6 is None:
            self.wl_auto_lbl.setText('体重データなし（手動確認要）')
            self.wl_auto_lbl.setStyleSheet(f'font-weight: bold; font-size: 14px; color: {C_MUTED}; background: transparent; border: none;')
        else:
            self.wl_auto_lbl.setText('基準を満たさない（体重減少なし）')
            self.wl_auto_lbl.setStyleSheet(f'font-weight: bold; font-size: 14px; color: {C_NORMAL}; background: transparent; border: none;')
        self.wl_detail_lbl.setText(wl['detail'])
        self.glim_wl_cb.setChecked(wl['present'])

        # BMI
        low_bmi = logic.is_low_bmi_glim(bmi, age)
        if bmi is not None:
            if low_bmi:
                self.bmi_auto_lbl.setText(f'BMI {bmi:.1f} — 低BMI基準を満たす')
                self.bmi_auto_lbl.setStyleSheet(f'font-weight: bold; font-size: 14px; color: {C_MAL}; background: transparent; border: none;')
            else:
                self.bmi_auto_lbl.setText(f'BMI {bmi:.1f} — 低BMI基準を満たさない')
                self.bmi_auto_lbl.setStyleSheet(f'font-weight: bold; font-size: 14px; color: {C_NORMAL}; background: transparent; border: none;')
            self.bmi_detail_lbl.setText('70歳以上: <22 を適用' if age >= 70 else '70歳未満: <20 を適用')
        else:
            self.bmi_auto_lbl.setText('BMI計算不可（手動確認要）')
            self.bmi_auto_lbl.setStyleSheet(f'font-weight: bold; font-size: 14px; color: {C_MUTED}; background: transparent; border: none;')
            self.bmi_detail_lbl.setText('身長・体重が未入力')
        self.glim_bmi_cb.setChecked(low_bmi)

    def validate(self, mna_score: Optional[int]) -> list[str]:
        if mna_score is not None and mna_score >= 12:
            return []
        errors = []
        phenotypic = (
            self.glim_wl_cb.isChecked()
            or self.glim_bmi_cb.isChecked()
            or self.muscle_combo.currentData() != 'none'
        )
        etiologic = (
            self.glim_intake_cb.isChecked()
            or self.glim_inflam_cb.isChecked()
            or self.glim_chronic_cb.isChecked()
        )
        if not phenotypic:
            errors.append('表現型基準を少なくとも1項目選択してください。')
        if not etiologic:
            errors.append('病因基準を少なくとも1項目選択してください。')
        return errors

    def show_errors(self, errors: list[str]):
        if errors:
            self.error_lbl.setText('入力内容を確認してください:\n• ' + '\n• '.join(errors))
            self.error_lbl.show()
        else:
            self.error_lbl.hide()

    def get_glim_answers(self) -> GLIMAnswers:
        return GLIMAnswers(
            weight_loss=int(self.glim_wl_cb.isChecked()),
            low_bmi=int(self.glim_bmi_cb.isChecked()),
            muscle=self.muscle_combo.currentData(),
            intake=int(self.glim_intake_cb.isChecked()),
            inflam=int(self.glim_inflam_cb.isChecked()),
            chronic=int(self.glim_chronic_cb.isChecked()),
        )


# ──────────────────────────────────────────────
# Page 3: 結果
# ──────────────────────────────────────────────
class Page3(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(10)
        root.addWidget(self.content_widget)

    def render(self, patient: Patient, values: dict, mna: MNAAnswers, glim: GLIMAnswers):
        # Clear
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        age = values['age']
        bmi = logic.calc_bmi(values['weight'], values['height'])
        wl3 = logic.calc_weight_loss_pct(values['weight'], values.get('weight_3m'))
        wl6 = logic.calc_weight_loss_pct(values['weight'], values.get('weight_6m'))
        mna_total = mna.total
        mna_interp = logic.interpret_mna_sf_score(mna_total)
        skip_glim = mna_total is not None and mna_total >= 12

        glim_result = None
        if not skip_glim:
            glim_result = logic.calc_glim_severity(
                glim_weight_loss=bool(glim.weight_loss),
                glim_low_bmi=bool(glim.low_bmi),
                glim_muscle=glim.muscle,
                glim_intake=bool(glim.intake),
                glim_inflam=bool(glim.inflam),
                glim_chronic=bool(glim.chronic),
                age=age,
                bmi=bmi,
                wl_pct_3m=wl3,
                wl_pct_6m=wl6,
            )

        # ── 結果バナー ──
        if skip_glim:
            banner_color, icon, title, desc = C_NORMAL_BG, '✅', '栄養良好', 'MNA-SFスコアが12〜14点のため低栄養のリスクは低いと判断されます。'
            border_color = C_NORMAL
        elif not glim_result or not glim_result.get('diagnosed'):
            banner_color, icon, title, desc = C_RISK_BG, '⚠', '低栄養非該当（要観察）', 'GLIM診断基準を満たしませんが、MNA-SFでリスクが検出されています。継続的な観察と栄養ケアを推奨します。'
            border_color = C_RISK
        else:
            severity = glim_result.get('severity')
            banner_color, icon, border_color = C_MAL_BG, '●', C_MAL
            title = '低栄養（Stage 2: 高度）' if severity == 'stage2' else '低栄養（Stage 1: 中等度）'
            desc = 'GLIM基準により低栄養と診断されます。栄養介入計画の策定を推奨します。'

        banner = QFrame()
        banner.setStyleSheet(
            f'QFrame {{ background: {banner_color}; border: 2px solid {border_color}; '
            f'border-radius: 8px; padding: 12px; }}'
        )
        banner_lay = QHBoxLayout(banner)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f'font-size: 28px; border: none; background: transparent;')
        icon_lbl.setFixedWidth(40)
        banner_lay.addWidget(icon_lbl)
        text_col = QVBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f'font-size: 18px; font-weight: 800; color: {border_color}; border: none; background: transparent;')
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f'font-size: 12px; color: {C_MUTED}; border: none; background: transparent;')
        text_col.addWidget(title_lbl)
        text_col.addWidget(desc_lbl)
        if glim_result and glim_result.get('severity'):
            sev = glim_result['severity']
            sev_lbl = QLabel('Stage 2（高度栄養不良）' if sev == 'stage2' else 'Stage 1（中等度栄養不良）')
            sev_lbl.setStyleSheet(
                ('background: #fecaca; color: #7f1d1d;' if sev == 'stage2' else 'background: #fde68a; color: #92400e;') +
                ' border-radius: 10px; padding: 2px 10px; font-weight: bold; font-size: 12px;'
            )
            text_col.addWidget(sev_lbl)
        banner_lay.addLayout(text_col)
        self.content_layout.addWidget(banner)

        # ── 患者サマリ ──
        summary_box = QGroupBox('患者情報')
        summary_lay = QFormLayout(summary_box)
        summary_lay.setSpacing(4)
        gender_map = {'male': '男性', 'female': '女性', 'other': 'その他'}
        items = [
            ('患者ID', patient.patient_code),
            ('評価日', values['assess_date']),
            ('性別 / 年齢', f"{gender_map.get(patient.gender, '')} / {age}歳"),
            ('身長 / 体重', f"{values['height']:.1f}cm / {values['weight']:.1f}kg"),
            ('BMI', f'{bmi:.1f}' if bmi else '—'),
            ('体重減少率', f'{wl3:.1f}%（3M）' if wl3 else (f'{wl6:.1f}%（6M）' if wl6 else '—')),
        ]
        for label, val in items:
            v_lbl = QLabel(val)
            v_lbl.setStyleSheet('font-weight: 600; font-size: 13px; background: transparent; border: none;')
            summary_lay.addRow(label + ':', v_lbl)
        self.content_layout.addWidget(summary_box)

        # ── MNA スコア ──
        mna_box = QGroupBox('MNA-SF スコア')
        mna_box_lay = QVBoxLayout(mna_box)
        color_map = {'normal': C_NORMAL, 'risk': C_RISK, 'severe': C_MAL, 'unknown': C_MUTED}
        mna_color = color_map.get(mna_interp.get('category', 'unknown'), C_PRIMARY)
        mna_score_lbl = QLabel(f'{mna_total}  / 14点')
        mna_score_lbl.setStyleSheet(f'font-size: 28px; font-weight: 800; color: {mna_color}; background: transparent; border: none;')
        mna_cat_lbl = QLabel(mna_interp.get('label', ''))
        mna_cat_lbl.setStyleSheet(f'font-size: 13px; font-weight: 700; color: {mna_color}; background: transparent; border: none;')
        mna_box_lay.addWidget(mna_score_lbl)
        mna_box_lay.addWidget(mna_cat_lbl)
        self.content_layout.addWidget(mna_box)

        # ── GLIM 結果 ──
        if not skip_glim and glim_result:
            glim_box = QGroupBox('GLIM 評価結果')
            glim_box_lay = QVBoxLayout(glim_box)

            # Phenotypic / Etiologic
            criteria_row = QHBoxLayout()
            for label, items_list, met in [
                ('表現型基準', glim_result.get('phenotypic_items', []), glim_result.get('phenotypic_met', False)),
                ('病因基準', glim_result.get('etiologic_items', []), glim_result.get('etiologic_met', False)),
            ]:
                f = QFrame()
                bg = C_MAL_BG if met else C_NORMAL_BG
                border = '#fca5a5' if met else '#d1fae5'
                f.setStyleSheet(f'QFrame {{ background: {bg}; border: 1px solid {border}; border-radius: 6px; padding: 8px; }}')
                lay = QVBoxLayout(f)
                lay.setSpacing(3)
                t = QLabel(label)
                t.setStyleSheet(f'font-size: 11px; font-weight: 600; color: {C_MUTED}; border: none; background: transparent;')
                v = QLabel('充足' if met else '非充足')
                v.setStyleSheet(f'font-size: 16px; font-weight: 800; color: {C_MAL if met else C_NORMAL}; border: none; background: transparent;')
                items_lbl = QLabel('、'.join(items_list) if items_list else '該当なし')
                items_lbl.setWordWrap(True)
                items_lbl.setStyleSheet(f'font-size: 12px; border: none; background: transparent;')
                lay.addWidget(t)
                lay.addWidget(v)
                lay.addWidget(items_lbl)
                criteria_row.addWidget(f)
            glim_box_lay.addLayout(criteria_row)

            # Reasons
            if glim_result.get('diagnosed') and glim_result.get('reasons'):
                reasons_lbl = QLabel('診断根拠:')
                reasons_lbl.setStyleSheet(f'font-weight: 700; font-size: 13px; background: transparent; border: none;')
                glim_box_lay.addWidget(reasons_lbl)
                for r in glim_result['reasons']:
                    r_lbl = QLabel(f'✓  {r}')
                    r_lbl.setWordWrap(True)
                    r_lbl.setStyleSheet(f'color: {C_MAL}; font-size: 13px; background: transparent; border: none;')
                    glim_box_lay.addWidget(r_lbl)

            self.content_layout.addWidget(glim_box)

        # ── 推奨アクション ──
        rec_box = QGroupBox('推奨アクション')
        rec_lay = QVBoxLayout(rec_box)
        diagnosed = glim_result.get('diagnosed') if glim_result else None
        severity = glim_result.get('severity') if glim_result else None
        recs = logic.get_recommendations(
            mna_interp.get('category'),
            diagnosed,
            severity,
        )
        for rec in recs:
            r_lbl = QLabel(rec)
            r_lbl.setWordWrap(True)
            r_lbl.setStyleSheet(
                f'font-size: 13px; background: {C_RISK_BG}; border-radius: 5px; '
                f'padding: 6px 10px; border: none; color: {C_TEXT};'
            )
            rec_lay.addWidget(r_lbl)
        self.content_layout.addWidget(rec_box)

        # Disclaimer
        disc = QLabel(
            'このツールは臨床判断を支援するためのものです。診断・治療方針は必ず臨床医が総合的に判断してください。\n'
            'MNA® は Nestlé の登録商標です。GLIM基準: Cederholm T, et al. JPEN 2019.'
        )
        disc.setWordWrap(True)
        disc.setAlignment(Qt.AlignCenter)
        disc.setStyleSheet(f'font-size: 11px; color: {C_MUTED}; background: transparent;')
        self.content_layout.addWidget(disc)

        self.content_layout.addStretch()

    def get_result_data(self, patient: Patient, values: dict, mna: MNAAnswers, glim: GLIMAnswers) -> Assessment:
        """計算結果をAssessmentに詰めて返す"""
        age = values['age']
        bmi = logic.calc_bmi(values['weight'], values['height'])
        wl3 = logic.calc_weight_loss_pct(values['weight'], values.get('weight_3m'))
        wl6 = logic.calc_weight_loss_pct(values['weight'], values.get('weight_6m'))
        mna_total = mna.total
        mna_interp = logic.interpret_mna_sf_score(mna_total)
        skip_glim = mna_total is not None and mna_total >= 12

        glim_result = None
        if not skip_glim:
            glim_result = logic.calc_glim_severity(
                glim_weight_loss=bool(glim.weight_loss),
                glim_low_bmi=bool(glim.low_bmi),
                glim_muscle=glim.muscle,
                glim_intake=bool(glim.intake),
                glim_inflam=bool(glim.inflam),
                glim_chronic=bool(glim.chronic),
                age=age,
                bmi=bmi,
                wl_pct_3m=wl3,
                wl_pct_6m=wl6,
            )

        return Assessment(
            id=None,
            patient_id=patient.id,
            assess_date=values['assess_date'],
            age_at_assess=age,
            height_cm=values['height'],
            weight_kg=values['weight'],
            weight_3m_kg=values.get('weight_3m'),
            weight_6m_kg=values.get('weight_6m'),
            cc_cm=values.get('cc'),
            bmi=bmi,
            wl_pct_3m=wl3,
            wl_pct_6m=wl6,
            mna=mna,
            glim=glim,
            mna_category=mna_interp.get('category'),
            glim_diagnosed=glim_result.get('diagnosed') if glim_result else None,
            glim_severity=glim_result.get('severity') if glim_result else None,
        )


# ──────────────────────────────────────────────
# メインウィザードダイアログ
# ──────────────────────────────────────────────
class AssessmentWizard(QDialog):
    def __init__(self, patient: Patient, parent=None):
        super().__init__(parent)
        self.patient = patient
        self.saved_assessment: Optional[Assessment] = None
        self.setWindowTitle(f'新規評価 — {patient.patient_code}')
        self.setMinimumSize(640, 680)
        self.setStyleSheet(QSS_BASE)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        # Progress bar
        self.progress = StepProgressBar()
        root.addWidget(self.progress)

        # Stacked pages inside scroll area
        self.stack = QStackedWidget()

        self.page0 = Page0()
        self.page1 = Page1()
        self.page2 = Page2()
        self.page3 = Page3()

        self.page0.set_patient(patient=self.patient)

        # Wrap pages in scroll areas
        for page in [self.page0, self.page1, self.page2, self.page3]:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
            self.stack.addWidget(scroll)

        root.addWidget(self.stack, 1)

        # Navigation buttons
        nav = QHBoxLayout()
        nav.setSpacing(8)
        self.btn_back = QPushButton('◀ 戻る')
        self.btn_back.setObjectName('btnSecondary')
        self.btn_back.setEnabled(False)
        self.btn_next = QPushButton('次へ ▶')
        self.btn_next.setObjectName('btnPrimary')

        nav.addWidget(self.btn_back)
        nav.addStretch()
        nav.addWidget(self.btn_next)
        root.addLayout(nav)

        self.btn_back.clicked.connect(self._go_back)
        self.btn_next.clicked.connect(self._go_next)

        self._current = 0

    def _go_next(self):
        if self._current == 0:
            errors = self.page0.validate()
            self.page0.show_errors(errors)
            if errors:
                return
            self._values = self.page0.get_values()
            self.page1.auto_estimate(self._values)
            self._advance(1)

        elif self._current == 1:
            errors = self.page1.validate()
            self.page1.show_errors(errors)
            if errors:
                return
            self._mna = self.page1.get_mna_answers()
            self.page2.auto_fill(self._values, self._mna.total)
            self._advance(2)

        elif self._current == 2:
            errors = self.page2.validate(self._mna.total)
            self.page2.show_errors(errors)
            if errors:
                return
            self._glim = self.page2.get_glim_answers()
            self.page3.render(self.patient, self._values, self._mna, self._glim)
            self._advance(3)
            self.btn_next.setText('保存')
            self.btn_next.setObjectName('btnSuccess')
            self.btn_next.setStyleSheet(
                f'QPushButton {{ background: {C_NORMAL}; color: white; border: none; '
                f'border-radius: 5px; padding: 7px 18px; font-size: 13px; font-weight: 600; }}'
                f'QPushButton:hover {{ background: #155d38; }}'
            )

        elif self._current == 3:
            self._save()

    def _go_back(self):
        if self._current > 0:
            if self._current == 3:
                self.btn_next.setText('次へ ▶')
                self.btn_next.setObjectName('btnPrimary')
                self.btn_next.setStyleSheet('')
            self._advance(self._current - 1)

    def _advance(self, index: int):
        self._current = index
        self.stack.setCurrentIndex(index)
        self.progress.set_step(index)
        self.btn_back.setEnabled(index > 0)

    def _save(self):
        import database
        try:
            assess = self.page3.get_result_data(
                self.patient, self._values, self._mna, self._glim
            )
            assess.id = database.insert_assessment(assess)
            self.saved_assessment = assess
            QMessageBox.information(self, '保存完了', '評価データを保存しました。')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, 'エラー', f'保存に失敗しました:\n{e}')
