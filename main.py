"""メインウィンドウ — QMainWindow（患者一覧 + 評価履歴）"""
from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional

# nutrition_tool/ をsys.pathに追加
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QDialog, QFormLayout,
    QComboBox, QTextEdit, QMessageBox, QSplitter, QHeaderView,
    QAbstractItemView, QFrame, QScrollArea, QGroupBox, QDateEdit,
)
from PySide6.QtCore import QDate

import database
from models import Patient, Assessment
from wizard import AssessmentWizard, C_PRIMARY, C_NORMAL, C_RISK, C_MAL, C_MUTED, C_BORDER, C_BG
import pdf_export

# ──────────────────────────────────────────────
# QSS
# ──────────────────────────────────────────────
APP_QSS = f"""
QMainWindow {{ background: {C_BG}; }}
QWidget {{ font-family: "Hiragino Sans", "Yu Gothic", sans-serif; }}
QListWidget {{
    border: 1px solid {C_BORDER};
    border-radius: 6px;
    background: white;
    font-size: 13px;
}}
QListWidget::item {{
    padding: 8px 10px;
    border-bottom: 1px solid #f0f0f0;
}}
QListWidget::item:selected {{
    background: #e8f0fb;
    color: {C_PRIMARY};
    font-weight: bold;
}}
QTableWidget {{
    border: 1px solid {C_BORDER};
    border-radius: 6px;
    background: white;
    gridline-color: #f0f0f0;
    font-size: 12px;
}}
QTableWidget::item {{ padding: 4px 8px; }}
QTableWidget::item:selected {{ background: #e8f0fb; color: {C_PRIMARY}; }}
QHeaderView::section {{
    background: #f8fafc;
    border: none;
    border-bottom: 1px solid {C_BORDER};
    padding: 5px 8px;
    font-weight: bold;
    font-size: 12px;
    color: {C_MUTED};
}}
QPushButton {{
    border-radius: 5px; padding: 6px 14px;
    font-size: 12px; font-weight: 600;
}}
QPushButton#btnPrimary {{
    background: {C_PRIMARY}; color: white; border: none;
}}
QPushButton#btnPrimary:hover {{ background: #1648b0; }}
QPushButton#btnSuccess {{
    background: {C_NORMAL}; color: white; border: none;
}}
QPushButton#btnDanger {{
    background: {C_MAL}; color: white; border: none;
}}
QPushButton#btnSecondary {{
    background: white; color: #374151; border: 1.5px solid {C_BORDER};
}}
QPushButton#btnSecondary:hover {{ background: #f9fafb; }}
QLineEdit {{
    border: 1px solid {C_BORDER}; border-radius: 5px;
    padding: 5px 8px; font-size: 12px; background: white;
    min-height: 26px;
}}
QLineEdit:focus {{ border-color: {C_PRIMARY}; }}
QLabel#panelTitle {{
    font-size: 13px; font-weight: 700; color: {C_PRIMARY};
}}
"""


# ──────────────────────────────────────────────
# 患者追加・編集ダイアログ
# ──────────────────────────────────────────────
class PatientDialog(QDialog):
    def __init__(self, patient: Optional[Patient] = None, parent=None):
        super().__init__(parent)
        self.is_edit = patient is not None
        self.setWindowTitle('患者編集' if self.is_edit else '患者追加')
        self.setMinimumWidth(400)
        self.setStyleSheet(APP_QSS)
        self._build(patient)

    def _build(self, patient: Optional[Patient]):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText('例: PT-0001')
        if patient:
            self.code_edit.setText(patient.patient_code)
        form.addRow('患者ID *:', self.code_edit)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('任意')
        if patient:
            self.name_edit.setText(patient.name)
        form.addRow('氏名:', self.name_edit)

        self.gender_combo = QComboBox()
        self.gender_combo.addItem('男性', 'male')
        self.gender_combo.addItem('女性', 'female')
        self.gender_combo.addItem('その他', 'other')
        if patient:
            idx = {'male': 0, 'female': 1, 'other': 2}.get(patient.gender, 0)
            self.gender_combo.setCurrentIndex(idx)
        form.addRow('性別 *:', self.gender_combo)

        self.birth_edit = QLineEdit()
        self.birth_edit.setPlaceholderText('例: 1945-03-15（任意）')
        if patient:
            self.birth_edit.setText(patient.birth_date or '')
        form.addRow('生年月日:', self.birth_edit)

        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText('メモ（任意）')
        if patient:
            self.notes_edit.setPlainText(patient.notes)
        form.addRow('備考:', self.notes_edit)

        layout.addLayout(form)

        # Error label
        self.error_lbl = QLabel()
        self.error_lbl.setWordWrap(True)
        self.error_lbl.setStyleSheet(
            'color: #991b1b; background: #fef2f2; border: 1px solid #fca5a5; '
            'border-radius: 5px; padding: 6px 10px; font-size: 12px;'
        )
        self.error_lbl.hide()
        layout.addWidget(self.error_lbl)

        # Buttons
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton('キャンセル')
        cancel_btn.setObjectName('btnSecondary')
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton('保存')
        save_btn.setObjectName('btnPrimary')
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        self._patient_id = patient.id if patient else None

    def _save(self):
        code = self.code_edit.text().strip()
        if not code:
            self.error_lbl.setText('患者IDを入力してください。')
            self.error_lbl.show()
            return

        if database.patient_code_exists(code, exclude_id=self._patient_id):
            self.error_lbl.setText(f'患者ID "{code}" は既に使用されています。')
            self.error_lbl.show()
            return

        self.result_patient = Patient(
            id=self._patient_id,
            patient_code=code,
            name=self.name_edit.text().strip(),
            gender=self.gender_combo.currentData(),
            birth_date=self.birth_edit.text().strip() or None,
            notes=self.notes_edit.toPlainText().strip(),
        )
        self.accept()


# ──────────────────────────────────────────────
# 評価サマリダイアログ（読み取り専用）
# ──────────────────────────────────────────────
class AssessmentSummaryDialog(QDialog):
    def __init__(self, patient: Patient, assessment: Assessment, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'評価詳細 — {patient.patient_code}  {assessment.assess_date}')
        self.setMinimumSize(500, 580)
        self.setStyleSheet(APP_QSS)
        self._build(patient, assessment)

    def _build(self, patient: Patient, assessment: Assessment):
        root = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; }')

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(10)

        a = assessment
        bmi = a.bmi
        wl3 = a.wl_pct_3m
        wl6 = a.wl_pct_6m
        mna_interp = logic_import().interpret_mna_sf_score(a.mna.total)

        # 患者情報
        info_box = QGroupBox('患者情報')
        info_lay = QFormLayout(info_box)
        gender_map = {'male': '男性', 'female': '女性', 'other': 'その他'}
        rows = [
            ('患者ID', patient.patient_code),
            ('評価日', a.assess_date),
            ('性別 / 年齢', f"{gender_map.get(patient.gender, '')} / {a.age_at_assess}歳"),
            ('身長 / 体重', f'{a.height_cm:.1f}cm / {a.weight_kg:.1f}kg'),
            ('BMI', f'{bmi:.1f}' if bmi else '—'),
            ('3M体重減少率', f'{wl3:.1f}%' if wl3 else '—'),
            ('6M体重減少率', f'{wl6:.1f}%' if wl6 else '—'),
        ]
        for label, val in rows:
            v = QLabel(val)
            v.setStyleSheet('font-weight: 600;')
            info_lay.addRow(label + ':', v)
        lay.addWidget(info_box)

        # MNA
        mna_box = QGroupBox('MNA-SF')
        mna_lay = QFormLayout(mna_box)
        color_map = {'normal': C_NORMAL, 'risk': C_RISK, 'severe': C_MAL}
        mna_color = color_map.get(mna_interp.get('category', ''), C_PRIMARY)
        total_lbl = QLabel(f"{a.mna.total} / 14点  —  {mna_interp.get('label', '')}")
        total_lbl.setStyleSheet(f'font-weight: bold; color: {mna_color};')
        mna_lay.addRow('スコア:', total_lbl)
        lay.addWidget(mna_box)

        # GLIM
        if a.mna.total is not None and a.mna.total < 12:
            glim_box = QGroupBox('GLIM 評価')
            glim_lay = QFormLayout(glim_box)
            diag_text = '低栄養あり' if a.glim_diagnosed else '低栄養なし'
            sev_text = {'stage1': 'Stage 1（中等度）', 'stage2': 'Stage 2（高度）'}.get(a.glim_severity or '', '—')
            d_lbl = QLabel(diag_text)
            d_lbl.setStyleSheet(f'font-weight: bold; color: {C_MAL if a.glim_diagnosed else C_NORMAL};')
            glim_lay.addRow('診断:', d_lbl)
            if a.glim_diagnosed:
                s_lbl = QLabel(sev_text)
                s_lbl.setStyleSheet(f'font-weight: bold; color: {C_MAL};')
                glim_lay.addRow('重症度:', s_lbl)
            lay.addWidget(glim_box)
        else:
            skip_lbl = QLabel('MNA-SF ≥12 のため GLIM 評価は省略されました')
            skip_lbl.setStyleSheet(f'color: {C_NORMAL}; font-weight: bold;')
            lay.addWidget(skip_lbl)

        lay.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

        close_btn = QPushButton('閉じる')
        close_btn.setObjectName('btnSecondary')
        close_btn.clicked.connect(self.accept)
        root.addWidget(close_btn)


def logic_import():
    import logic as lg
    return lg


# ──────────────────────────────────────────────
# メインウィンドウ
# ──────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('低栄養診断ツール（MNA-SF / GLIM）')
        self.setMinimumSize(900, 620)
        self.setStyleSheet(APP_QSS)

        self._current_patient: Optional[Patient] = None
        self._patients: list[Patient] = []
        self._assessments: list[Assessment] = []

        self._build_ui()
        self._load_patients()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_lay = QVBoxLayout(central)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── アプリヘッダー ──
        header = QFrame()
        header.setStyleSheet(f'QFrame {{ background: {C_PRIMARY}; }}')
        header.setFixedHeight(48)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 16, 0)
        title_lbl = QLabel('低栄養診断ツール')
        title_lbl.setStyleSheet('color: white; font-size: 15px; font-weight: 700; background: transparent;')
        sub_lbl = QLabel('MNA-SF スクリーニング ／ GLIM 基準による診断・重症度評価')
        sub_lbl.setStyleSheet('color: rgba(255,255,255,0.8); font-size: 11px; background: transparent;')
        h_lay.addWidget(title_lbl)
        h_lay.addWidget(sub_lbl)
        h_lay.addStretch()
        main_lay.addWidget(header)

        # ── スプリッター ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setContentsMargins(8, 8, 8, 8)

        # ── 左パネル: 患者リスト ──
        left = QWidget()
        left.setMinimumWidth(220)
        left.setMaximumWidth(260)
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(6)

        pt_title = QLabel('患者リスト')
        pt_title.setObjectName('panelTitle')
        left_lay.addWidget(pt_title)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('患者IDまたは氏名で検索…')
        self.search_edit.textChanged.connect(self._on_search)
        left_lay.addWidget(self.search_edit)

        self.patient_list = QListWidget()
        self.patient_list.currentItemChanged.connect(self._on_patient_selected)
        left_lay.addWidget(self.patient_list, 1)

        add_pt_btn = QPushButton('＋ 患者追加')
        add_pt_btn.setObjectName('btnPrimary')
        add_pt_btn.clicked.connect(self._add_patient)
        edit_pt_btn = QPushButton('患者編集')
        edit_pt_btn.setObjectName('btnSecondary')
        edit_pt_btn.clicked.connect(self._edit_patient)
        del_pt_btn = QPushButton('患者削除')
        del_pt_btn.setObjectName('btnDanger')
        del_pt_btn.clicked.connect(self._delete_patient)

        left_lay.addWidget(add_pt_btn)
        btn_row = QHBoxLayout()
        btn_row.addWidget(edit_pt_btn)
        btn_row.addWidget(del_pt_btn)
        left_lay.addLayout(btn_row)

        splitter.addWidget(left)

        # ── 右パネル: 評価履歴 ──
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(6)

        self.history_title = QLabel('評価履歴')
        self.history_title.setObjectName('panelTitle')
        right_lay.addWidget(self.history_title)

        # テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(['評価日', '年齢', 'BMI', 'MNA合計', 'MNA判定', 'GLIM診断', '重症度'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet('QTableWidget { alternate-background-color: #f8fafc; }')
        self.table.doubleClicked.connect(self._on_table_double_click)
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        right_lay.addWidget(self.table, 1)

        # ボタン行
        btn_row2 = QHBoxLayout()
        self.new_assess_btn = QPushButton('新規評価')
        self.new_assess_btn.setObjectName('btnSuccess')
        self.new_assess_btn.clicked.connect(self._new_assessment)
        self.new_assess_btn.setEnabled(False)

        self.pdf_btn = QPushButton('PDF出力')
        self.pdf_btn.setObjectName('btnSecondary')
        self.pdf_btn.clicked.connect(self._export_pdf)
        self.pdf_btn.setEnabled(False)

        self.del_assess_btn = QPushButton('評価削除')
        self.del_assess_btn.setObjectName('btnDanger')
        self.del_assess_btn.clicked.connect(self._delete_assessment)
        self.del_assess_btn.setEnabled(False)

        btn_row2.addWidget(self.new_assess_btn)
        btn_row2.addStretch()
        btn_row2.addWidget(self.pdf_btn)
        btn_row2.addWidget(self.del_assess_btn)
        right_lay.addLayout(btn_row2)

        splitter.addWidget(right)
        splitter.setSizes([230, 670])

        main_lay.addWidget(splitter, 1)

        # ステータスバー
        self.statusBar().showMessage('準備完了')

    # ──────────────────────────────────────────
    # 患者リスト操作
    # ──────────────────────────────────────────

    def _load_patients(self, query: str = ''):
        if query:
            self._patients = database.search_patients(query)
        else:
            self._patients = database.get_all_patients()

        self.patient_list.blockSignals(True)
        self.patient_list.clear()
        for pt in self._patients:
            label = pt.patient_code
            if pt.name:
                label += f'  {pt.name}'
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, pt.id)
            self.patient_list.addItem(item)
        self.patient_list.blockSignals(False)

        # 選択を復元
        if self._current_patient:
            for i in range(self.patient_list.count()):
                if self.patient_list.item(i).data(Qt.UserRole) == self._current_patient.id:
                    self.patient_list.setCurrentRow(i)
                    break

    def _on_search(self, text: str):
        self._load_patients(text.strip())

    def _on_patient_selected(self, current, previous):
        if current is None:
            self._current_patient = None
            self._clear_table()
            self.new_assess_btn.setEnabled(False)
            return

        patient_id = current.data(Qt.UserRole)
        self._current_patient = database.get_patient(patient_id)
        if self._current_patient:
            self.history_title.setText(
                f'評価履歴 — {self._current_patient.patient_code}'
                + (f'  {self._current_patient.name}' if self._current_patient.name else '')
            )
            self._load_assessments()
            self.new_assess_btn.setEnabled(True)
        self.statusBar().showMessage(f'患者: {self._current_patient.patient_code}')

    def _add_patient(self):
        dlg = PatientDialog(parent=self)
        if dlg.exec() == QDialog.Accepted:
            try:
                pid = database.insert_patient(dlg.result_patient)
                self._load_patients(self.search_edit.text().strip())
                # 新しい患者を選択
                for i in range(self.patient_list.count()):
                    if self.patient_list.item(i).data(Qt.UserRole) == pid:
                        self.patient_list.setCurrentRow(i)
                        break
                self.statusBar().showMessage('患者を追加しました。')
            except Exception as e:
                QMessageBox.critical(self, 'エラー', str(e))

    def _edit_patient(self):
        if not self._current_patient:
            QMessageBox.information(self, '情報', '患者を選択してください。')
            return
        dlg = PatientDialog(patient=self._current_patient, parent=self)
        if dlg.exec() == QDialog.Accepted:
            try:
                database.update_patient(dlg.result_patient)
                self._current_patient = dlg.result_patient
                self._load_patients(self.search_edit.text().strip())
                self.statusBar().showMessage('患者情報を更新しました。')
            except Exception as e:
                QMessageBox.critical(self, 'エラー', str(e))

    def _delete_patient(self):
        if not self._current_patient:
            QMessageBox.information(self, '情報', '患者を選択してください。')
            return
        reply = QMessageBox.question(
            self, '確認',
            f'患者 {self._current_patient.patient_code} とすべての評価データを削除しますか？\nこの操作は取り消せません。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                database.delete_patient(self._current_patient.id)
                self._current_patient = None
                self._clear_table()
                self._load_patients(self.search_edit.text().strip())
                self.new_assess_btn.setEnabled(False)
                self.history_title.setText('評価履歴')
                self.statusBar().showMessage('患者を削除しました。')
            except Exception as e:
                QMessageBox.critical(self, 'エラー', str(e))

    # ──────────────────────────────────────────
    # 評価履歴テーブル
    # ──────────────────────────────────────────

    def _load_assessments(self):
        if not self._current_patient:
            return
        self._assessments = database.get_assessments_for_patient(self._current_patient.id)
        self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(0)
        mna_color = {'normal': C_NORMAL, 'risk': C_RISK, 'severe': C_MAL}
        for a in self._assessments:
            row = self.table.rowCount()
            self.table.insertRow(row)

            mna_cat = a.mna_category or ''
            mna_labels = {'normal': '栄養良好', 'risk': 'リスクあり', 'severe': '低栄養疑い'}
            sev_labels = {'stage1': 'Stage 1', 'stage2': 'Stage 2'}
            glim_diag = '低栄養あり' if a.glim_diagnosed else ('省略' if a.mna_category == 'normal' else '低栄養なし')
            glim_sev = sev_labels.get(a.glim_severity or '', '—')

            cells = [
                a.assess_date,
                f'{a.age_at_assess}歳',
                f'{a.bmi:.1f}' if a.bmi else '—',
                f'{a.mna.total} / 14' if a.mna.total is not None else '—',
                mna_labels.get(mna_cat, '—'),
                glim_diag,
                glim_sev,
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                # 色付け
                if col == 4 and mna_cat in mna_color:
                    item.setForeground(QColor(mna_color[mna_cat]))
                if col == 5 and a.glim_diagnosed:
                    item.setForeground(QColor(C_MAL))
                if col == 6 and a.glim_severity == 'stage2':
                    item.setForeground(QColor(C_MAL))
                self.table.setItem(row, col, item)

        self.pdf_btn.setEnabled(False)
        self.del_assess_btn.setEnabled(False)

    def _clear_table(self):
        self.table.setRowCount(0)
        self._assessments = []

    def _on_table_double_click(self, index):
        row = index.row()
        if 0 <= row < len(self._assessments) and self._current_patient:
            dlg = AssessmentSummaryDialog(self._current_patient, self._assessments[row], self)
            dlg.exec()

    def _on_table_selection_changed(self):
        selected = self.table.selectedItems()
        has_selection = len(selected) > 0
        self.pdf_btn.setEnabled(has_selection)
        self.del_assess_btn.setEnabled(has_selection)

    # ──────────────────────────────────────────
    # 評価操作
    # ──────────────────────────────────────────

    def _new_assessment(self):
        if not self._current_patient:
            return
        dlg = AssessmentWizard(self._current_patient, parent=self)
        if dlg.exec() == QDialog.Accepted and dlg.saved_assessment:
            self._load_assessments()
            self.statusBar().showMessage('評価を保存しました。')

    def _export_pdf(self):
        rows = list({idx.row() for idx in self.table.selectedIndexes()})
        if not rows or not self._current_patient:
            return
        row = rows[0]
        if 0 <= row < len(self._assessments):
            assess = self._assessments[row]
            ok = pdf_export.export_pdf(self._current_patient, assess, parent=self)
            if ok:
                self.statusBar().showMessage('PDFを保存しました。')

    def _delete_assessment(self):
        rows = list({idx.row() for idx in self.table.selectedIndexes()})
        if not rows:
            return
        row = rows[0]
        if 0 <= row < len(self._assessments):
            assess = self._assessments[row]
            reply = QMessageBox.question(
                self, '確認',
                f'{assess.assess_date} の評価データを削除しますか？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                database.delete_assessment(assess.id)
                self._load_assessments()
                self.statusBar().showMessage('評価を削除しました。')


# ──────────────────────────────────────────────
# エントリーポイント
# ──────────────────────────────────────────────
def main():
    database.init_db()

    app = QApplication(sys.argv)
    app.setApplicationName('低栄養診断ツール')
    app.setApplicationVersion('1.0.0')

    # フォント設定（macOS）
    font = QFont()
    font.setFamily('Hiragino Sans')
    font.setPointSize(12)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
