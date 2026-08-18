import qrcode
from urllib.parse import quote


content = "<script>alert(1)</script>"

qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10, border=4)

qr.add_data(f"data:text/html;charset=utf-8," + quote(content))
qr.make(fit=True)

qr.make_image(fill_color="black", back_color="white").save("qrcode.png")
