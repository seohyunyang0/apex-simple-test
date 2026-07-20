#!/usr/bin/env python3
"""
index.html → 자체 완결형 미리보기 파일 하나로 굽는다.

왜: preview.html은 index.html을 iframe으로 부르기 때문에 파일 하나만
    메일로 보내면 빈 화면이 뜬다. 이 스크립트는 모든 자산을 data URI로
    인라인하고 티어 전환 툴바를 얹어서, 받는 쪽이 더블클릭만 하면
    5단계 결과를 다 볼 수 있는 단일 HTML을 만든다.

쓰기: python3 tools/build-standalone-preview.py
결과: dist/APEX-결과화면-미리보기.html
"""

import base64
import mimetypes
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "index.html"
OUT_DIR = ROOT / "dist"
OUT = OUT_DIR / "APEX-결과화면-미리보기.html"

TIERS = [
    ("t1", "심각", "#DB4142", 30),
    ("t2", "경계", "#F3631C", 62),
    ("t3", "주의", "#F2BA00", 78),
    ("t4", "관심", "#23A450", 90),
    ("t5", "사랑", "#1A6FEF", 98),
]


def data_uri(path: pathlib.Path) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    if path.suffix == ".svg":
        mime = "image/svg+xml"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def inline_assets(html: str) -> tuple[str, int]:
    """./로 시작하는 로컬 자산을 전부 data URI로 치환."""
    count = 0
    for ref in sorted(set(re.findall(r'"(\./[^"]+)"', html))):
        path = (ROOT / ref[2:]).resolve()
        if not path.is_file():
            print(f"  ! 없음, 건너뜀: {ref}", file=sys.stderr)
            continue
        if path.suffix == ".js":
            # <script src="..."></script> → 내용을 그대로 인라인
            code = path.read_text(encoding="utf-8")
            html = re.sub(
                r'<script src="' + re.escape(ref) + r'"></script>',
                "<script>\n" + code + "\n</script>",
                html,
            )
        else:
            html = html.replace(f'"{ref}"', f'"{data_uri(path)}"')
        count += 1
    return html, count


def build_toolbar() -> str:
    buttons = "\n".join(
        f'      <button data-score="{score}" style="--c:{color}">'
        f'<i></i>{label}</button>'
        for _key, label, color, score in TIERS
    )
    return f"""
<div id="apexPreviewBar">
  <strong>APEX 결과화면 미리보기</strong>
  <div class="grp">
{buttons}
  </div>
  <label class="grp">
    <input type="range" id="apxScore" min="0" max="100" value="78" />
    <b id="apxOut">78</b>점
  </label>
  <button id="apxReplay">▶ 모션 재생</button>
  <span class="note">이 툴바는 검수용입니다. 실제 사용자에게는 보이지 않습니다.</span>
</div>

<style>
  #apexPreviewBar {{
    position: fixed; inset: 0 0 auto 0; z-index: 99999;
    display: flex; flex-wrap: wrap; align-items: center; gap: 14px;
    padding: 10px 16px;
    background: #14161B; color: #E8EAEE;
    font: 13px/1.4 'Pretendard Variable', Pretendard, -apple-system, system-ui, sans-serif;
    box-shadow: 0 2px 14px rgba(0,0,0,.35);
  }}
  #apexPreviewBar strong {{ font-size: 13px; white-space: nowrap; }}
  #apexPreviewBar .grp {{ display: flex; align-items: center; gap: 6px; }}
  #apexPreviewBar button {{
    display: inline-flex; align-items: center; gap: 6px;
    padding: 6px 12px; border-radius: 999px; cursor: pointer;
    border: 1px solid #333A47; background: #1F232C; color: #E8EAEE;
    font: inherit; font-weight: 700;
  }}
  #apexPreviewBar button:hover {{ background: #2A303B; }}
  #apexPreviewBar button[aria-pressed="true"] {{
    border-color: var(--c); background: color-mix(in srgb, var(--c) 22%, #1F232C);
  }}
  #apexPreviewBar button i {{
    width: 9px; height: 9px; border-radius: 50%; background: var(--c);
  }}
  #apexPreviewBar #apxReplay {{ border-color: #3C5BD6; background: #2B45B8; }}
  #apexPreviewBar input[type=range] {{ width: 150px; accent-color: #5B8CFF; }}
  #apexPreviewBar b {{ font-family: ui-monospace, monospace; font-size: 15px; }}
  #apexPreviewBar .note {{ margin-left: auto; color: #98A0AE; font-size: 12px; }}
  body {{ padding-top: 56px !important; }}
  @media print {{ #apexPreviewBar {{ display: none; }} body {{ padding-top: 0 !important; }} }}
</style>

<script>
  // 검수용이므로 OS '동작 줄이기'와 무관하게 모션을 보여준다
  window.__rxForceMotion = true;

  (function () {{
    var bar = document.getElementById('apexPreviewBar');
    var range = document.getElementById('apxScore');
    var out = document.getElementById('apxOut');
    var picks = bar.querySelectorAll('button[data-score]');

    function show(score) {{
      score = Math.max(0, Math.min(100, Number(score) || 0));
      range.value = score;
      out.textContent = score;
      if (typeof window.showResultPreview === 'function') {{
        window.showResultPreview(score);
      }}
      var tier = document.getElementById('resultPanel');
      picks.forEach(function (b) {{
        b.setAttribute('aria-pressed', String(b.dataset.score === String(score)));
      }});
      void tier;
    }}

    picks.forEach(function (b) {{
      b.addEventListener('click', function () {{ show(b.dataset.score); }});
    }});
    range.addEventListener('input', function () {{ show(range.value); }});
    document.getElementById('apxReplay').addEventListener('click', function () {{
      show(range.value);
    }});
    document.addEventListener('keydown', function (e) {{
      if (e.target === range) return;
      if (e.key === 'ArrowLeft') {{ show(Number(range.value) - 1); e.preventDefault(); }}
      if (e.key === 'ArrowRight') {{ show(Number(range.value) + 1); e.preventDefault(); }}
      if (e.key === 'r' || e.key === 'R') show(range.value);
    }});

    // 페이지 스크립트가 다 뜬 뒤 첫 렌더
    window.addEventListener('load', function () {{ setTimeout(function () {{ show(78); }}, 60); }});
  }})();
</script>
"""


def main() -> int:
    if not SRC.is_file():
        print(f"index.html 없음: {SRC}", file=sys.stderr)
        return 1

    html = SRC.read_text(encoding="utf-8")
    html, inlined = inline_assets(html)

    # 외부 CDN(폰트·Supabase)은 남긴다. 오프라인이면 시스템 폰트로 폴백하고,
    # Supabase는 미설정 상태라 로드 실패해도 화면에 영향이 없다.
    html = html.replace("</body>", build_toolbar() + "\n</body>")
    html = html.replace(
        "<title>", "<!-- 검수용 단일 파일 · tools/build-standalone-preview.py 로 생성 -->\n  <title>", 1
    )

    OUT_DIR.mkdir(exist_ok=True)
    OUT.write_text(html, encoding="utf-8")

    size = OUT.stat().st_size / 1024
    print(f"자산 {inlined}개 인라인 → {OUT.relative_to(ROOT)}  ({size:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
