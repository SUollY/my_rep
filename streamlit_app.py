# -*- coding: utf-8 -*-
"""
Streamlit + FPDF2 (Unicode)
UI на русском, сам PDF полностью на португальском.
"""
import io, os
from datetime import date
import streamlit as st
from fpdf import FPDF
from PIL import Image
import qrcode

st.set_page_config(page_title="DocGen - Декларация (Unicode)", page_icon="📄")

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
    qr_obj = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M,
                           box_size=box_size, border=border)
    qr_obj.add_data(qr_text); qr_obj.make(fit=True)
    return qr_obj.make_image(fill_color="black", back_color="white").convert("RGB")

class PDF(FPDF):
    def header(self): pass

def bytes_from_output(pdf: FPDF) -> bytes:
    out = pdf.output(dest="S")
    return bytes(out) if isinstance(out, (bytes, bytearray)) else out.encode("latin1")

def generate_pdf(nome, doc_id, cpf, endereco, local, data_str, logo_bytes=None, qr_text=None) -> bytes:
    # предобработка
    nome, doc_id, cpf = map(soften_long_tokens, [nome, doc_id, cpf])
    endereco, local = map(soften_long_tokens, [endereco, local])
    qr_text = (qr_text or "").strip() or None

    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # шрифты
    if fonts_available():
        register_unicode_fonts(pdf)
        font = "DejaVu"
    else:
        font = "helvetica"  # если DejaVu отсутствуют
        st.warning("⚠️ Нет Unicode-шрифтов в ./fonts — добавьте DejaVuSans*.ttf для кириллицы в именах/адресе.")

    # логотип (опц.)
    if logo_bytes:
        try: pdf.image(io.BytesIO(logo_bytes), x=15, y=12, w=30)
        except Exception: pass

    # заголовок (PT)
    pdf.set_font(font, "B", 16 if font == "DejaVu" else 18)
    pdf.set_xy(0, 20)
    pdf.cell(w=0, h=10, txt="DECLARAÇÃO DE RESIDÊNCIA",
             align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3); pdf.set_font(font, "", 12)
    content_w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_x(pdf.l_margin)

    # corpo 1 (PT)
    corpo1 = (
        f"Eu, {nome}, portador(a) do documento de identidade nº {doc_id}, "
        f"inscrito(a) no CPF sob nº {cpf}, declaro, sob as penas da lei, "
        "que resido no seguinte endereço:"
    )
    pdf.multi_cell(w=content_w, h=7, txt=corpo1, align="J")

    # endereço (itálico)
    pdf.set_x(pdf.l_margin); pdf.set_font(font, "I", 12)
    pdf.multi_cell(w=content_w, h=7, txt=endereco, align="J")
    pdf.set_font(font, "", 12)

    # corpo 2 (PT)
    pdf.ln(2); pdf.set_x(pdf.l_margin)
    corpo2 = (
        "Declaro ainda que as informações aqui prestadas são verdadeiras "
        "e de minha inteira responsabilidade."
    )
    pdf.multi_cell(w=content_w, h=7, txt=corpo2, align="J")

    # local/data
    pdf.ln(5); pdf.set_x(pdf.l_margin)
    pdf.cell(w=content_w, h=7, txt=f"{local}, {data_str}", new_x="LMARGIN", new_y="NEXT")

    # assinatura
    pdf.ln(12); x = pdf.l_margin; y = pdf.get_y()
    pdf.line(x, y, pdf.w - pdf.r_margin, y)
    pdf.set_y(y + 3); pdf.set_font(font, "", 10)
    pdf.cell(w=content_w, h=6, txt="Assinatura do Declarante", align="C",
             new_x="LMARGIN", new_y="NEXT")

    # QR (опц.)
    if qr_text:
        try:
            img = make_qr_image(qr_text, box_size=4, border=2)
            buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
            pdf.ln(5); pdf.set_font(font, "", 10); pdf.set_x(pdf.l_margin)
            pdf.cell(w=content_w, h=6, txt="Verificação:", new_x="LMARGIN", new_y="NEXT")
            pdf.image(buf, x=pdf.l_margin, w=30)
        except Exception:
            pass

    # rodapé
    pdf.ln(6); pdf.set_font(font, "", 9); pdf.set_text_color(80, 80, 80); pdf.set_x(pdf.l_margin)
    pdf.multi_cell(w=content_w, h=5, txt="Documento gerado automaticamente — DocGen MVP", align="L")
    pdf.set_text_color(0, 0, 0)

    return bytes_from_output(pdf)

# ===== UI (русский) =====
st.title("📄 Декларация о месте жительства — генератор PDF (текст в PDF на португальском)")

with st.form("doc_form"):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("ФИО (как в документе)", "")
        doc_id = st.text_input("Документ (RG/RNE/RNM)", "")
        cpf = st.text_input("CPF", "")
        local = st.text_input("Место (Город/Штат) — в PDF попадёт без изменений", "São Paulo/SP")
        data_input = st.date_input("Дата", value=date.today())
    with col2:
        logo_file = st.file_uploader("Логотип (PNG/JPG) — опционально", type=["png","jpg","jpeg"])
        qr_text = st.text_input("QR: ссылка/ID — опционально", "")
    endereco = st.text_area("Полный адрес (Rua, nº, complemento, bairro, cidade/UF, CEP)", "")
    gerar = st.form_submit_button("Сгенерировать PDF")

if 'last_pdf' not in st.session_state:
    st.session_state.last_pdf = None

if gerar:
    if not (nome and doc_id and cpf and endereco and local):
        st.error("Заполните все обязательные поля.")
    else:
        try:
            pdf_bytes = generate_pdf(
                nome.strip(), doc_id.strip(), cpf.strip(), endereco.strip(),
                local.strip(), data_input.strftime("%d/%m/%Y"),
                logo_bytes=(logo_file.read() if logo_file else None),
                qr_text=(qr_text.strip() or None),
            )
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
