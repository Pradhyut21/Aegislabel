"""Build a seekable local Hyperframes cut from the measured real capture."""

import json
import shutil
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
scenes = json.loads((ROOT / "artifacts/demo/capture.json").read_text())
project = ROOT / "demo/composition"
assets = project / "assets"
assets.mkdir(exist_ok=True)
(assets / ".gitkeep").touch()
shutil.copyfile(
    ROOT / "demo/node_modules/gsap/dist/gsap.min.js", assets / "gsap.min.js"
)
parts = []
start = 0
for index, scene in enumerate(scenes):
    duration = scene["duration"]
    scene_id = scene["id"]
    timing = f'data-start="{start:.3f}" data-duration="{duration:.3f}"'
    title = escape(scene["title"])
    if "media_start" in scene:
        content = f'<video id="video-{scene_id}" class="clip footage" {timing} data-media-start="{scene["media_start"]}" src="assets/app-footage.webm" muted playsinline></video>'
    else:
        body = {
            "intro": '<p class="eyebrow">CHANGE-SAFE MEDICAL DEVICE LABELING</p><h1>A tiny change.<br>A critical consequence.</h1><p class="lead">Watch a missed safety warning become a blocked release.</p><div class="warning">Do not reuse. <strong>Inspect packaging before use.</strong></div>',
            "data": '<p class="eyebrow">PUBLIC REFERENCE RESEARCH · SEPARATE FROM THE TEST CORPUS</p><h1>Two FDA sources.<br>Preserved provenance.</h1><div class="sources"><div>Device UDI<small>Identifiers and product codes</small></div><span>→</span><div>Device Classification<small>Device class and category</small></div></div><p class="lead">6 public devices · 8 product-code matches</p><p class="detail">Explicit joins · source URLs · retrieval timestamps · raw response hashes<br>GMDN terminology and contact details excluded</p>',
            "outro": '<p class="eyebrow">AEGISLABEL-FX · EDUCATIONAL RESEARCH PROTOTYPE</p><h1>AI proposes.<br>Rules decide.<br><em>Humans approve.</em></h1><p class="lead">React interface · optional server-side Meta API integration</p><p class="detail">Recorded in deterministic mode. No live Meta inference claimed.<br>Not certified, production-ready, or endorsed by Meta or FDA.</p>',
        }[scene["id"]]
        content = f'<section id="card-{scene_id}" data-hold class="clip card" {timing}>{body}</section>'
    parts.extend(
        [
            content,
            f'<div id="chapter-{scene_id}" class="clip chapter" {timing}><span>{index + 1:02d} / 12</span> {title}</div>',
            f'<audio id="audio-{scene_id}" data-start="{start:.3f}" data-duration="{scene["speech_duration"]:.3f}" src="assets/{scene["id"]}.wav"></audio>',
        ]
    )
    start += duration
html = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=1920,height=1080"><title>AegisLabel-FX — real workflow demo</title><script src="assets/gsap.min.js"></script><style>
*{box-sizing:border-box;margin:0}html,body{width:1920px;height:1080px;overflow:hidden;background:#10263F;color:#fff;font-family:Arial,sans-serif}.clip{position:absolute}#root{position:relative;width:1920px;height:1080px;overflow:hidden}.brand{position:absolute;left:64px;top:28px;font-size:29px;letter-spacing:1px;font-weight:700}.disclosure{position:absolute;right:64px;top:34px;font-size:28px;color:#C8D5E2}.footage{left:48px;top:101px;width:1824px;height:900px;object-fit:contain;background:#F8FAFC;border:1px solid #64748B;border-radius:12px}.chapter{left:64px;top:1030px;font-size:28px;font-weight:600}.chapter span{color:#5EEAD4;margin-right:24px}.card{left:0;top:90px;width:1920px;height:920px;padding:92px 140px;background:#10263F}.eyebrow{font-size:28px;letter-spacing:3px;color:#5EEAD4;margin-bottom:36px}h1{font-size:91px;line-height:1.1;letter-spacing:-3px;font-weight:700}em{font-style:normal;color:#5EEAD4}.lead{font-size:31px;color:#E2E8F0;margin-top:36px;line-height:1.4}.detail{font-size:28px;color:#CBD5E1;margin-top:28px;line-height:1.6}.warning{margin-top:42px;padding:28px;border-left:5px solid #5EEAD4;background:#19374D;font-size:32px}.warning strong{color:#5EEAD4}.sources{display:flex;align-items:center;gap:32px;margin-top:40px}.sources div{border:1px solid #64748B;border-radius:12px;padding:26px 36px;font-size:30px}.sources small{display:block;font-size:28px;margin-top:12px;color:#CBD5E1}.sources span{font-size:46px;color:#5EEAD4}
</style></head><body><main id="root" data-composition-id="main" data-start="0" data-duration="DURATION" data-width="1920" data-height="1080">CONTENT<div class="brand">AEGISLABEL-FX</div><div class="disclosure">REAL APP CAPTURE · SYNTHETIC WORKSPACE · AI NARRATION</div></main><script>window.__timelines=window.__timelines||{};const tl=gsap.timeline({paused:true});tl.to({}, {duration:DURATION});window.__timelines.main=tl;</script></body></html>""".replace(
    "DURATION", f"{start:.3f}"
).replace("CONTENT", "\n".join(parts))
(project / "index.html").write_text(html)
(ROOT / "artifacts/demo/timeline.json").write_text(
    json.dumps({"duration": start, "scenes": scenes}, indent=2)
)
print(f"Built {start:.3f}s composition")
