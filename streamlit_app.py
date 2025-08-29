# -*- coding: utf-8 -*-
"""
Streamlit + FPDF2 (Unicode)
UI на русском, PDF целиком на португальском.
— Структурированные "дополнительные лица"
— Маски/валидация (даты/CPF/документы)
— Опция: подчёркивать пустые поля
"""
import io, os, re
from datetime import date
import streamlit as st
from fpdf import FPDF
from PIL import Image
import qrcode

st.set_page_config(page_title="DocGen - Declaração (Unicode, PRO)", page_icon="📄")

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

def fonts_available():
    return all(os.path.exists(os.path.join(FONTS_DIR, f)) for f in [
        "DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf"
    ])

def register_unicode_fonts(pdf: FPDF):
    pdf.add_font("DejaVu", style="", fname=os.path.join(FONTS_DIR, "DejaVuSans.ttf"), uni=True)
    pdf.add_font("DejaVu", style="B", fname=os.path.join(FONTS_DIR, "DejaVuSans-Bold.ttf"), uni=True)
    pdf.add_font("DejaVu", style="I", fname=os.path.join(FONTS_DIR, "DejaVuSans-Oblique.ttf"), uni=True)

def soften_long_tokens(text: str, hard_limit: int = 40) -> str:
    def split_token(tok):
        if len(tok) <= hard_limit: return tok
        return " ".join(tok[i:i+hard_limit] for i in range(0, len(tok), hard_limit))
    return " ".join(split_token(t) for t in (text or "").split())

def make_qr_image(qr_text: str, box_size: int = 6, border: int = 2) -> Image.Image:
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=box_size, border=border)
    qr.add_data(qr_text); qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")

def bytes_from_output(pdf: FPDF) -> bytes:
    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin1")

# ---------- Helpers: формат/валидация ----------
re_date = re.compile(r"^\d{2}/\d{2}/\d{4}$")
re_cpf  = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")

def mask_hint(label, example):
    st.caption(f"Формат: `{example}`")

def ensure(value, placeholder):
    return value if value.strip() else placeholder

def underline_if_empty(value, length=10):
    return value.strip() if value.strip() else "_" * length

# ---------- PDF ----------
class PDF(FPDF):
    def header(self): pass

def build_declaro_block(pessoas, underline):
    lines = []
    for p in pessoas:
        nome = underline_if_empty(p["nome"], 12) if underline else p["nome"]
        nasc = underline_if_empty(p["nascimento"], 10) if underline else p["nascimento"]
        doctype = underline_if_empty(p["doc_tipo"], 6) if underline else p["doc_tipo"]
        docnum = underline_if_empty(p["doc_numero"], 8) if underline else p["doc_numero"]
        emissor = underline_if_empty(p["doc_emissor"], 10) if underline else p["doc_emissor"]
        line = f"{nome.upper()}, nascido(a) em {nasc}, {doctype} nº {docnum} emitido por {emissor}"
        lines.append(line)
    if not lines:
        return ""
    return "DECLARO, SOB AS PENAS DA LEI que " + "; ".join(lines) + "."

def generate_pdf(dados, pessoas, underline_blanks=False) -> bytes:
    # данные заявителя
    nome       = soften_long_tokens(dados["nome"])
    nasc       = soften_long_tokens(dados["nascimento"])
    cpf        = soften_long_tokens(dados["cpf"])
    rg         = soften_long_tokens(dados["rg"])
    endereco   = soften_long_tokens(dados["endereco"])
    cidade_uf  = soften_long_tokens(dados["cidade_uf"])
    data_str   = dados["data_str"]
    qr_text    = (dados["qr_text"] or "").strip() or None
    logo_bytes = dados["logo_bytes"]

    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # шрифты
    if fonts_available():
        register_unicode_fonts(pdf)
        font = "DejaVu"
    else:
        font = "helvetica"
        st.warning("⚠️ Нет Unicode-шрифтов в ./fonts — добавьте DejaVuSans*.ttf для кириллицы в именах/адресе.")

    # логотип (опц.)
    if logo_bytes:
        try: pdf.image(io.BytesIO(logo_bytes), x=15, y=12, w=30)
        except Exception: pass

    # Заголовок
    pdf.set_font(font, "B", 16 if font == "DejaVu" else 18)
    pdf.set_xy(0, 20)
    pdf.cell(w=0, h=10, txt="DECLARAÇÃO DE RESIDÊNCIA", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3); pdf.set_font(font, "", 12)
    content_w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_x(pdf.l_margin)

    # 1-й абзац — заявитель
    _nome = underline_if_empty(nome, 12) if underline_blanks else nome
    _nasc = underline_if_empty(nasc, 10) if underline_blanks else nasc
    _cpf  = underline_if_empty(cpf, 14)  if underline_blanks else cpf
    _rg   = underline_if_empty(rg, 10)   if underline_blanks else rg
    _end  = underline_if_empty(endereco, 20) if underline_blanks else endereco

    corpo1 = (
        f"Eu, {_nome.upper()} nascido(a) em {_nasc}, inscrito(a) no CPF sob o nº {_cpf}, "
        f"portador(a) da Cédula de Identidade RG nº {_rg}, residente e situado(a) na {_end}."
    )
    pdf.multi_cell(w=content_w, h=7, txt=corpo1, align="J")

    # 2-й абзац — DECLARO... (если есть люди)
    declaro = build_declaro_block(pessoas, underline_blanks)
    if declaro:
        pdf.ln(3); pdf.set_x(pdf.l_margin); pdf.set_font(font, "B", 12)
        pdf.multi_cell(w=content_w, h=7, txt=declaro, align="J")
        pdf.set_font(font, "", 12)

    # 3-й абзац — Art. 299
    pdf.ln(3); pdf.set_x(pdf.l_margin)
    rodape_legal = (
        "É considerado crime, com pena de reclusão e multa, omitir, em documento público ou particular, "
        "declaração que dele devia constar, ou nele inserir ou fazer inserir declaração falsa ou diversa da que "
        "devia ser escrita, com o fim de prejudicar direito, criar obrigação ou alterar a verdade sobre fato "
        "juridicamente relevante (Art. 299, do Código Penal)."
    )
    pdf.multi_cell(w=content_w, h=7, txt=rodape_legal, align="J")

    # Город/дата
    pdf.ln(6); pdf.set_x(pdf.l_margin)
    pdf.cell(w=content_w, h=7, txt=f"{cidade_uf}, {data_str}", new_x="LMARGIN", new_y="NEXT")

    # Подпись + имя
    pdf.ln(14); x = pdf.l_margin; y = pdf.get_y()
    pdf.line(x, y, pdf.w - pdf.r_margin, y)
    pdf.set_y(y + 4)
    pdf.set_font(font, "B", 12)
    pdf.cell(w=content_w, h=7, txt=nome.upper(), align="C", new_x="LMARGIN", new_y="NEXT")

    # QR (опц.)
    if qr_text:
        try:
            img = make_qr_image(qr_text, box_size=4, border=2)
            buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
            pdf.ln(2); pdf.set_font(font, "", 10); pdf.set_x(pdf.l_margin)
            pdf.cell(w=content_w, h=6, txt="Verificação:", new_x="LMARGIN", new_y="NEXT")
            pdf.image(buf, x=pdf.l_margin, w=30)
        except Exception:
            pass

    return bytes_from_output(pdf)

# ---------------- UI ----------------
st.title("📄 Декларация о месте жительства — генератор PDF (PT)")

# Храним список лиц в session_state
if "pessoas" not in st.session_state:
    st.session_state.pessoas = []

with st.form("doc_form"):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("ФИО (как в документе)", "")
        nascimento = st.text_input("Дата рождения", placeholder="DD/MM/AAAA")
        mask_hint("Дата рождения", "DD/MM/AAAA")
        cpf = st.text_input("CPF", placeholder="000.000.000-00")
        mask_hint("CPF", "000.000.000-00")
        rg = st.text_input("RG (номер удостоверения)", "")
    with col2:
        cidade_uf = st.text_input("Место (Город/Штат)", "Rio de Janeiro / RJ")
        data_input = st.date_input("Дата документа", value=date.today())
        logo_file = st.file_uploader("Логотип (PNG/JPG) — опционально", type=["png","jpg","jpeg"])
        qr_text = st.text_input("QR: ссылка/ID — опционально", "")
    endereco = st.text_area("Полный адрес (Rua, nº, complemento, bairro, cidade/UF, CEP)", "")

    st.subheader("Дополнительные лица (для блока 'DECLARO, SOB AS PENAS DA LEI…')")
    add_col1, add_col2, add_col3, add_col4, add_col5 = st.columns([2,1.2,1.6,1.4,1.6])
    with add_col1:
        p_nome = st.text_input("ФИО", key="p_nome")
    with add_col2:
        p_nasc = st.text_input("Дата рожд.", key="p_nasc", placeholder="DD/MM/AAAA")
    with add_col3:
        p_tipo = st.selectbox("Документ", ["passaporte", "RG", "RNM", "CPF", "MATRICULA"], key="p_tipo")
    with add_col4:
        p_num  = st.text_input("№ документа", key="p_num")
    with add_col5:
        p_emissor = st.text_input("Кем выдан", key="p_emissor", placeholder="Federação Russa / REPÚBLICA FEDERATIVA DO BRASIL ...")

    c1, c2, c3 = st.columns([1,1,2])
    add_btn = c1.button("➕ Добавить лицо")
    clear_btn = c2.button("🗑 Очистить список")
    underline_blanks = c3.checkbox("Подчёркивать пустые поля в PDF", value=False)

    # показать текущий список
    if st.session_state.pessoas:
        st.markdown("**Текущий список:**")
        for i, p in enumerate(st.session_state.pessoas):
            st.write(f"{i+1}. {p['nome']} — {p['nascimento']} — {p['doc_tipo']} nº {p['doc_numero']} — {p['doc_emissor']}")
        del_idx = st.number_input("Удалить №", min_value=0, max_value=len(st.session_state.pessoas), value=0, step=1)
        if st.form_submit_button("Удалить выбранного"):
            if 1 <= del_idx <= len(st.session_state.pessoas):
                st.session_state.pessoas.pop(del_idx-1)
                st.success("Удалён.")

    gerar = st.form_submit_button("Сгенерировать PDF")

# обработка кнопок добавления/очистки (вне формы)
if 'after_add' not in st.session_state: st.session_state.after_add = False
if st.session_state.after_add:
    st.session_state.after_add = False
if add_btn:
    st.session_state.pessoas.append({
        "nome": p_nome.strip(),
        "nascimento": p_nasc.strip(),
        "doc_tipo": p_tipo.strip(),
        "doc_numero": p_num.strip(),
        "doc_emissor": p_emissor.strip(),
    })
    st.session_state.after_add = True
    st.experimental_rerun()
if clear_btn:
    st.session_state.pessoas = []
    st.experimental_rerun()

# генерация PDF
if 'last_pdf' not in st.session_state:
    st.session_state.last_pdf = None

if gerar:
    # валидация базовых полей
    errs = []
    if not nome or not nascimento or not cpf or not rg or not endereco or not cidade_uf:
        errs.append("Заполните все обязательные поля.")
    if nascimento and not re_date.match(nascimento):
        errs.append("Дата рождения должна быть в формате DD/MM/AAAA.")
    if cpf and not re_cpf.match(cpf):
        errs.append("CPF должен быть в формате 000.000.000-00.")
    if errs:
        for e in errs: st.error(e)
    else:
        try:
            dados = {
                "nome": nome, "nascimento": nascimento, "cpf": cpf, "rg": rg,
                "endereco": endereco, "cidade_uf": cidade_uf,
                "data_str": data_input.strftime("%d/%m/%Y"),
                "qr_text": qr_text, "logo_bytes": (logo_file.read() if logo_file else None),
            }
            pdf_bytes = generate_pdf(dados, st.session_state.pessoas, underline_blanks)
            st.session_state.last_pdf = pdf_bytes
            st.success("PDF сгенерирован. Ниже доступна кнопка скачивания.")
        except Exception as e:
            st.error(f"Ошибка генерации PDF: {e}")

if st.session_state.last_pdf:
    st.download_button(
        label="⬇️ Скачать PDF",
        data=st.session_state.last_pdf,
        file_name="declaracao_residencia.pdf",
        mime="application/pdf",
    )
