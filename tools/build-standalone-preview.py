#!/usr/bin/env python3
"""
index.html → 메일로 보낼 수 있는 자체 완결형 미리보기 한 파일로 굽는다.

왜: preview.html은 index.html을 iframe으로 부르므로 파일 하나만 보내면
    빈 화면이 뜬다. 이 스크립트는 로컬 자산을 전부 data URI로 인라인하고
    기기 전환 + 단계 전환 툴바를 얹어서, 받는 쪽이 더블클릭만 하면
    모바일·태블릿·데스크톱 화면을 다 볼 수 있는 단일 HTML을 만든다.

구조: 바깥 = 툴바 + 기기 프레임, 안쪽 = srcdoc iframe에 담은 결과 화면.
      iframe을 쓰는 이유는 미디어쿼리가 뷰포트 폭에 반응하기 때문이다.
      래퍼 div로 폭만 줄이면 모바일 CSS가 발동하지 않는다.
      제어는 postMessage로 한다(file:// 에서도 동작하는 것 확인).

쓰기: python3 tools/build-standalone-preview.py
결과: dist/APEX-결과화면-미리보기.html
"""

import base64
import html as html_mod
import mimetypes
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"
OUT_DIR = ROOT / "dist"
OUT = OUT_DIR / "APEX-결과화면-미리보기.html"

TIERS = [
    ("심각", "#DB4142", 30),
    ("경계", "#F3631C", 62),
    ("주의", "#F2BA00", 78),
    ("관심", "#23A450", 90),
    ("사랑", "#1A6FEF", 98),
]

DEVICES = [
    ("모바일", 390, 844),
    ("태블릿", 768, 1024),
    ("데스크톱", 1280, 900),
]

DEFAULT_SCORE = 78


def data_uri(path: pathlib.Path) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    if path.suffix == ".svg":
        mime = "image/svg+xml"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def inline_assets(page: str) -> tuple[str, int]:
    """./로 시작하는 로컬 자산을 data URI(또는 인라인 스크립트)로 치환."""
    count = 0
    for ref in sorted(set(re.findall(r'"(\./[^"]+)"', page))):
        path = (ROOT / ref[2:]).resolve()
        if not path.is_file():
            print(f"  ! 없음, 건너뜀: {ref}", file=sys.stderr)
            continue
        if path.suffix == ".js":
            code = path.read_text(encoding="utf-8")
            page = re.sub(
                r'<script src="' + re.escape(ref) + r'"></script>',
                "<script>\n" + code + "\n</script>",
                page,
            )
        else:
            page = page.replace(f'"{ref}"', f'"{data_uri(path)}"')
        count += 1
    return page, count


INNER_BOOTSTRAP = """
<script>
  /* 검수용: OS '동작 줄이기'와 무관하게 모션을 보여준다 */
  window.__rxForceMotion = true;
  (function () {
    function show(score) {
      if (typeof window.showResultPreview === 'function') {
        window.showResultPreview(Math.max(0, Math.min(100, Number(score) || 0)));
      }
    }
    /* 바깥이 iframe 높이를 내용에 맞출 수 있게 알려준다 (중첩 스크롤 방지) */
    function reportHeight() {
      if (window.parent === window) return;
      window.parent.postMessage(
        { apexHeight: document.documentElement.scrollHeight }, '*'
      );
    }
    window.addEventListener('message', function (e) {
      var d = e.data;
      if (d && typeof d.apexScore !== 'undefined') {
        show(d.apexScore);
        setTimeout(reportHeight, 260);   /* 렌더가 끝난 뒤 실제 높이 */
      }
    });
    window.addEventListener('resize', reportHeight);
    window.addEventListener('load', function () {
      setTimeout(function () {
        show(__DEFAULT_SCORE__);
        reportHeight();
        if (window.parent !== window) window.parent.postMessage({ apexReady: true }, '*');
      }, 60);
    });
  })();
</script>
</body>
"""


def build_wrapper(inner_escaped: str) -> str:
    tier_buttons = "\n".join(
        f'      <button class="tier" data-score="{score}" style="--c:{color}"><i></i>{label}</button>'
        for label, color, score in TIERS
    )
    device_buttons = "\n".join(
        f'      <button class="dev" data-w="{w}" data-h="{h}">{name} {w}</button>'
        for name, w, h in DEVICES
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>APEX 결과화면 미리보기</title>
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: #0F1115; color: #E8EAEE;
    font: 14px/1.5 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  }}
  header {{
    position: sticky; top: 0; z-index: 10;
    display: flex; flex-wrap: wrap; align-items: center; gap: 16px;
    padding: 12px 18px;
    background: rgba(15,17,21,.94); backdrop-filter: blur(10px);
    border-bottom: 1px solid #2C313C;
  }}
  h1 {{ margin: 0; font-size: 14px; font-weight: 800; white-space: nowrap; }}
  .grp {{ display: flex; align-items: center; gap: 6px; }}
  .grp > span {{ font-size: 11px; font-weight: 700; color: #949CAB; letter-spacing: .04em; }}
  button {{
    display: inline-flex; align-items: center; gap: 7px;
    padding: 7px 13px; border-radius: 999px; cursor: pointer;
    border: 1px solid #333A47; background: #1F232C; color: #E8EAEE;
    font: inherit; font-size: 12px; font-weight: 700;
    transition: background 140ms ease, border-color 140ms ease;
  }}
  button:hover {{ background: #2A303B; }}
  button i {{ width: 9px; height: 9px; border-radius: 50%; background: var(--c); }}
  .tier[aria-pressed="true"] {{ border-color: var(--c); background: color-mix(in srgb, var(--c) 22%, #1F232C); }}
  .dev {{ border-radius: 8px; }}
  .dev[aria-pressed="true"] {{ background: #3A4150; border-color: #4A5163; color: #fff; }}
  #replay {{ border-color: #3C5BD6; background: #2B45B8; }}
  input[type=range] {{ width: 150px; accent-color: #5B8CFF; }}
  #out {{ font-family: ui-monospace, monospace; font-size: 15px; font-weight: 700; min-width: 2.4em; }}
  .note {{ margin-left: auto; font-size: 12px; color: #98A0AE; }}

  main {{ display: flex; justify-content: center; padding: 26px 18px 60px; }}
  #stage {{
    background: #FBFAFF; border-radius: 18px; overflow: hidden;
    border: 1px solid #2C313C; box-shadow: 0 20px 50px rgba(0,0,0,.45);
    transition: width 180ms ease;
  }}
  #frame {{ display: block; width: 100%; border: 0; }}
  kbd {{
    padding: 2px 6px; border-radius: 4px; background: #1F232C;
    border: 1px solid #2C313C; font-family: ui-monospace, monospace; font-size: 11px;
  }}
</style>
</head>
<body>

<header>
  <h1>APEX 결과화면 미리보기</h1>

  <div class="grp"><span>단계</span>
{tier_buttons}
  </div>

  <div class="grp"><span>기기</span>
{device_buttons}
  </div>

  <div class="grp">
    <input type="range" id="score" min="0" max="100" value="{DEFAULT_SCORE}" />
    <b id="out">{DEFAULT_SCORE}</b><span>점</span>
  </div>

  <button id="replay">▶ 모션 재생</button>
  <span class="note">검수용 화면입니다 · <kbd>←</kbd><kbd>→</kbd> 1점 이동</span>
</header>

<main>
  <div id="stage">
    <iframe id="frame" title="APEX 결과 화면" srcdoc="{inner_escaped}"></iframe>
  </div>
</main>

<script>
  (function () {{
    var frame = document.getElementById('frame');
    var stage = document.getElementById('stage');
    var range = document.getElementById('score');
    var out = document.getElementById('out');
    var tiers = [].slice.call(document.querySelectorAll('.tier'));
    var devs = [].slice.call(document.querySelectorAll('.dev'));
    var score = {DEFAULT_SCORE};

    function push() {{
      out.textContent = score;
      range.value = score;
      tiers.forEach(function (b) {{
        b.setAttribute('aria-pressed', String(Number(b.dataset.score) === score));
      }});
      if (frame.contentWindow) frame.contentWindow.postMessage({{ apexScore: score }}, '*');
    }}

    function setScore(v) {{
      score = Math.max(0, Math.min(100, Number(v) || 0));
      push();
    }}

    function setDevice(w, h) {{
      // #stage에 1px 테두리가 있어 border-box 기준 안쪽이 2px 줄어든다.
      // iframe 뷰포트를 정확히 w로 맞추려면 그만큼 더한다.
      stage.style.width = (w + 2) + 'px';
      frame.style.height = h + 'px';
      devs.forEach(function (b) {{
        b.setAttribute('aria-pressed', String(Number(b.dataset.w) === w));
      }});
      // 폭이 바뀌면 미디어쿼리가 다시 걸리므로 모션도 다시 보여준다
      setTimeout(push, 120);
    }}

    tiers.forEach(function (b) {{ b.addEventListener('click', function () {{ setScore(b.dataset.score); }}); }});
    devs.forEach(function (b) {{
      b.addEventListener('click', function () {{ setDevice(Number(b.dataset.w), Number(b.dataset.h)); }});
    }});
    range.addEventListener('input', function () {{ setScore(range.value); }});
    document.getElementById('replay').addEventListener('click', push);
    document.addEventListener('keydown', function (e) {{
      if (e.target === range) return;
      if (e.key === 'ArrowLeft') {{ setScore(score - 1); e.preventDefault(); }}
      if (e.key === 'ArrowRight') {{ setScore(score + 1); e.preventDefault(); }}
      if (e.key === 'r' || e.key === 'R') push();
    }});
    window.addEventListener('message', function (e) {{
      if (!e.data) return;
      if (e.data.apexReady) push();
      // 내용 높이에 맞춰 iframe을 늘려 중첩 스크롤을 없앤다
      if (e.data.apexHeight) frame.style.height = e.data.apexHeight + 'px';
    }});

    setDevice({DEVICES[0][1]}, {DEVICES[0][2]});
  }})();
</script>
</body>
</html>
"""


def main() -> int:
    if not SRC.is_file():
        print(f"index.html 없음: {SRC}", file=sys.stderr)
        return 1

    inner = SRC.read_text(encoding="utf-8")
    inner, inlined = inline_assets(inner)
    inner = inner.replace(
        "</body>", INNER_BOOTSTRAP.replace("__DEFAULT_SCORE__", str(DEFAULT_SCORE))
    )

    wrapper = build_wrapper(html_mod.escape(inner, quote=True))

    OUT_DIR.mkdir(exist_ok=True)
    OUT.write_text(wrapper, encoding="utf-8")

    print(
        f"자산 {inlined}개 인라인 → {OUT.relative_to(ROOT)}"
        f"  ({OUT.stat().st_size / 1024:.0f} KB)"
    )
    print(f"  기기: {', '.join(f'{n} {w}' for n, w, _ in DEVICES)}")
    print(f"  단계: {', '.join(t[0] for t in TIERS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
