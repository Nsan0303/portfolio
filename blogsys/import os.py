import os
import shutil

thumb_dir = "blog-posts/test1_2025_08_17_11_48_html"
thumb_path = os.path.join(thumb_dir, "tmb.png")
default_thumb = "blogsys/src/tmb.png"  # サンプル画像のパス

if not os.path.exists(thumb_dir):
    os.makedirs(thumb_dir)

if not os.path.exists(thumb_path):
    if os.path.exists(default_thumb):
        shutil.copy(default_thumb, thumb_path)
        print(f"Copied default thumbnail: {thumb_path}")
    else:
        with open(thumb_path, "wb") as f:
            f.write(b"")  # 空ファイル
        print(f"Created empty thumbnail: {thumb_path}")
else:
    print(f"Thumbnail already exists: {thumb_path}")