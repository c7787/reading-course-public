#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成「扫码体验」二维码（SVG，无需 Pillow）。
部署拿到域名后，运行：
    python3 marketing/make_qr.py https://你的域名.example.com
会生成 marketing/reading-qr.svg，把它放进 扫码体验海报.html 的二维码占位区即可。
也可以改成输出 PNG（需 pip install 'qrcode[pil]'）。
"""
import sys
import qrcode
import qrcode.image.svg  # 显式导入，否则 qrcode.image.svg 属性不可用

def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "https://你的域名.example.com/"
    out = sys.argv[2] if len(sys.argv) > 2 else "marketing/reading-qr.svg"
    qr = qrcode.QRCode(box_size=10, border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(image_factory=qrcode.image.svg.SvgImage)
    img.save(out)
    print(f"已生成二维码：{out}")
    print(f"内容（体验地址）：{url}")

if __name__ == "__main__":
    main()
