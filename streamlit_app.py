# -*- coding: utf-8 -*-
"""
Streamlit App — Декларация о месте жительства (FPDF2 + qrcode, Unicode)
Требует Unicode-шрифты (TTF) в папке ./fonts (например, DejaVu Sans).
Файлы (рекомендуется): 
- fonts/DejaVuSans.ttf
- fonts/DejaVuSans-Bold.ttf
- fonts/DejaVuSans-Oblique.ttf  (или DejaVuSans-Italic.ttf)
"""
import io
import os
from datetime import date
import streamlit as st
from fpdf import FPDF
from PIL import Image
import qrcode

st.set_page_config(page_title="DocGen - Декларация (FPDF2 Unicode)", page_icon="📄")

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

def fonts_available():
    return all(os.path.exists(os.path.join(FONTS_DIR, fname)) for fname in [
        "DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf"
    ])

def register_unicode_fonts(pdf: FPDF):
    pdf.add_font("DejaVu", style="", fname=os.path.join(FONTS_DIR, "DejaVuSans.ttf"), uni=True)
    pdf.add_font("DejaVu", style="B", fname=os.path.join(FONTS_DIR, "DejaVuSans-Bold.ttf"), uni=True)
    # Обозначаем курсив как Oblique (или замените на Italic, если у вас другой файл)
    pdf.add_font("DejaVu", style="I", fname=os.path.join(FONTS_DIR, "DejaVuSans-Oblique.ttf"), uni=True)

# -------- helpers --------
def soften_long_tokens(text: str, hard_limit: int = 40) -> str:
    def split_token(tok):
        if len(tok) <= hard_limit: 
            return tok
        parts = [tok[i:i+hard_limit] for i in range(0, len(tok), hard_limit)]
        return " ".join(parts)
    return " ".join(split_token(t) for t in (text or "").split())

def make_qr_image(qr_text: str, box_size: int = 6, border: int = 2) -> Image.Image:
    qr_obj = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr_obj.add_data(qr_text)
    qr_obj.make(fit=True)
    img = qr_obj.make_image(fill_color="black", back_color="white")
    return img.convert("RGB")

# ---------- PDF generator (FPDF2) ----------
class DeclaracaoPDF(FPDF):
    def header(self):
        pass

def generate_pdf(nome, doc_id, cpf, endereco, local, data_str, logo_bytes=None, qr_text=None):
    # Предобработка
    nome = soften_long_tokens(nome)
    doc_id = soften_long_tokens(doc_id)
    cpf = soften_long_tokens(cpf)
    endereco = soften_long_tokens(endereco)
    local = soften_long_tokens(local)
    if qr_text:
        qr_text = qr_text.strip()

    pdf = DeclaracaoPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Регистрируем Unicode-шрифты
    if fonts_available():
        register_unicode_fonts(pdf)
        base_font = "DejaVu"
    else:
        base_font = "helvetica"  # fallback (не поддерживает кириллицу)

    # Заголовок + логотип
    if logo_bytes:
        try:
            pdf.image(io.BytesIO(logo_bytes), x=15, y=12, w=30)
        except Exception:
            pass

    pdf.set_font(base_font, "B", 16 if base_font == "DejaVu" else 18)
    pdf.set_xy(0, 20)
    pdf.cell(w=0, h=10, txt="ДЕКЛАРАЦИЯ О МЕСТЕ ЖИТЕЛЬСТВА (DECLARAÇÃO DE RESIDÊNCIA)", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_font(base_font, "", 12)
    content_w = pdf.w - pdf.l_margin - pdf.r_margin
    pdf.set_x(pdf.l_margin)

    corpo1 = (
        f"Я, {nome}, удостоверение личности № {doc_id}, зарегистрированный(ая) в CPF № {cpf}, "
        f"заявляю под ответственность по закону, что проживаю по адресу: "
        f"(Eu, {nome}, portador(a) do documento de identidade nº {doc_id}, inscrito(a) no CPF sob nº {cpf}, "
        f"declaro, sob as penas da lei, que resido no seguinte endereço:)"
    )
    pdf.multi_cell(w=content_w, h=7, txt=corpo1, align="J")

    pdf.set_x(pdf.l_margin)
    pdf.set_font(base_font, "I", 12)
    pdf.multi_cell(w=content_w, h=7, txt=endereco, align="J")
    pdf.set_font(base_font, "", 12)

    pdf.ln(2)
    pdf.set_x(pdf.l_margin)
    corpo2 = (
        "Также заявляю, что представленная здесь информация является достоверной "
        "и полностью находится под моей ответственностью. "
        "(Declaro ainda que as informações aqui prestadas são verdadeiras "
        "e de minha inteira responsabilidade.)"
    )
    pdf.multi_cell(w=content_w, h=7, txt=corpo2, align="J")

    pdf.ln(5)
    pdf.set_x(pdf.l_margin)
    pdf.cell(w=content_w, h=7, txt=f"{local}, {data_str}", new_x="LMARGIN", new_y="NEXT")

    # Линия подписи
    pdf.ln(12)
    x = pdf.l_margin
    y = pdf.get_y()
    pdf.line(x, y, pdf.w - pdf.r_margin, y)
    pdf.set_y(y + 3)
    pdf.set_font(base_font, "", 10)
    pdf.cell(w=content_w, h=6, txt="Подпись заявителя (Assinatura do Declarante)", align="C", new_x="LMARGIN", new_y="NEXT")

    # QR
    if qr_text:
        try:
            img = make_qr_image(qr_text, box_size=4, border=2)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            pdf.ln(5)
            pdf.set_font(base_font, "", 10)
            pdf.set_x(pdf.l_margin)
            pdf.cell(w=content_w, h=6, txt="Проверка (Verificação):", new_x="LMARGIN", new_y="NEXT")
            pdf.image(buf, x=pdf.l_margin, w=30)
        except Exception:
            pass

    # Футер
    pdf.ln(6)
    if base_font != "helvetica":
        pdf.set_text_color(80, 80, 80)
        pdf.set_font(base_font, "", 9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(w=content_w, h=5, txt="Документ сгенерирован автоматически (Documento gerado automaticamente) — DocGen MVP", align="L")
        pdf.set_text_color(0, 0, 0)
    else:
        # Если нет Unicode-шрифтов — предупредим пользователя
        st.warning("⚠️ Не найдены Unicode-шрифты в папке ./fonts. Добавьте DejaVuSans.ttf, DejaVuSans-Bold.ttf, DejaVuSans-Oblique.ttf для поддержки кириллицы.")
    return pdf.output(dest="S").encode("latin1")

# -------- UI --------
st.title("📄 Декларация о месте жительства — FPDF2 (Unicode)")
st.write("Русский текст + португальский в скобках. Чтобы отображалась кириллица, положите Unicode-шрифты в папку **fonts/**.")

with st.form("doc_form"):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("ФИО (Nome completo)", "")
        doc_id = st.text_input("Документ (RG/RNE/RNM)", "")
        cpf = st.text_input("CPF", "")
        local = st.text_input("Место (Город/Штат) — Local (Cidade/UF)", "São Paulo/SP")
        data_input = st.date_input("Дата (Data)", value=date.today())
    with col2:
        logo_file = st.file_uploader("Логотип (PNG/JPG) — опционально (Logo opcional)", type=["png","jpg","jpeg"])
        qr_text = st.text_input("QR: ссылка/ID — опционально (Texto para QR — opcional)", "")
    endereco = st.text_area("Полный адрес (Endereço completo)", "")
    gerar = st.form_submit_button("Сгенерировать PDF (Gerar PDF)")

if 'last_pdf' not in st.session_state:
    st.session_state.last_pdf = None

if gerar:
    if not (nome and doc_id and cpf and endereco and local):
        st.error("Заполните все обязательные поля. (Preencha todos os campos obrigatórios.)")
    else:
        data_str = data_input.strftime("%d/%m/%Y")
        logo_bytes = logo_file.read() if logo_file else None
        try:
            pdf_bytes = generate_pdf(
                nome.strip(), doc_id.strip(), cpf.strip(), endereco.strip(), local.strip(),
                data_str, logo_bytes=logo_bytes, qr_text=(qr_text.strip() or None)
            )
            st.session_state.last_pdf = pdf_bytes
            st.success("PDF готов! Используйте кнопку ниже для скачивания. (PDF gerado! Use o botão abaixo.)")
        except Exception as e:
            st.error(f"Ошибка генерации PDF: {e}")

if st.session_state.last_pdf:
    st.download_button(
        label="⬇️ Скачать PDF (Baixar PDF)",
        data=st.session_state.last_pdf,
        file_name="declaracao_residencia_unicode.pdf",
        mime="application/pdf",
    )
