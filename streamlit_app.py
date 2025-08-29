# -*- coding: utf-8 -*-
import io, os
from datetime import date
import streamlit as st
from fpdf import FPDF
from PIL import Image
import qrcode

def make_qr_image(qr_text):
    qr_obj = qrcode.QRCode(box_size=4, border=2)
    qr_obj.add_data(qr_text); qr_obj.make(fit=True)
    img = qr_obj.make_image(fill_color="black", back_color="white").convert("RGB")
    return img

class PDF(FPDF):
    pass

def generate_pdf():
    pdf = PDF()
    pdf.add_page(); pdf.set_font("helvetica", size=12)
    pdf.multi_cell(0, 10, "Test")
    out_bytes = pdf.output(dest="S")
    if isinstance(out_bytes, (bytes, bytearray)):
        return bytes(out_bytes)
    else:
        return out_bytes.encode("latin1")

st.write("ok")
