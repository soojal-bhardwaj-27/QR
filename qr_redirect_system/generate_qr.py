import qrcode

# This URL NEVER changes
STATIC_QR_URL = "http://localhost:5000/qr"

qr = qrcode.QRCode(
    version=1,
    box_size=10,
    border=4
)

qr.add_data(STATIC_QR_URL)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save("static_qr.png")

print("✅ Static QR code generated: static_qr.png")
