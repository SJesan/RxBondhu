"""Clean white + Bangla green UI helpers.

A small local Three.js scene gives a calm depth cue (a floating capsule), and
CSS adds subtle 3D tilt to cards. No CDN is required: three.min.js lives in
static/ and Streamlit serves it from /static/three.min.js.
"""

import streamlit as st

CLEAN_CSS = """
<style>
.block-container { padding-top: 1.1rem; max-width: 1180px; }
div[data-testid="stContainer"] {
  background: rgba(255,255,255,0.94);
  border: 1px solid #DCEBDD;
  border-radius: 18px;
  padding: 14px 18px;
  box-shadow: 0 10px 28px rgba(16,92,48,0.08);
  transition: transform 0.25s cubic-bezier(.2,.7,.3,1), box-shadow 0.25s;
  transform-style: preserve-3d;
}
div[data-testid="stContainer"]:hover {
  transform: perspective(900px) rotateX(2deg) translateY(-3px);
  box-shadow: 0 18px 38px rgba(16,92,48,0.16);
}
div.stButton > button {
  border-radius: 999px;
  border: 1px solid #0E6B3C;
  background: linear-gradient(135deg, #0E6B3C, #1B9A5A);
  color: #FFFFFF;
  font-weight: 700;
  padding: 0.55rem 1.25rem;
  box-shadow: 0 6px 16px rgba(14,107,60,0.24);
  transition: transform 0.2s, box-shadow 0.2s;
}
div.stButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(14,107,60,0.34);
}
div.stButton > button:active { transform: translateY(0); }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #F4FAF5 0%, #FFFFFF 100%);
  border-right: 1px solid #DCEBDD;
}
.rx-kicker {
  color: #0E6B3C; font-size: 0.78rem; font-weight: 800;
  letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 0.3rem;
}
.rx-step {
  display:inline-block; padding:0.3rem 0.75rem; border-radius:999px;
  background:#E8F5EC; color:#0E6B3C; font-weight:800; font-size:0.82rem;
  border:1px solid #CDE8D5; margin-bottom:0.5rem;
}
.rx-badge {
  display:inline-block; padding:0.25rem 0.7rem; border-radius:999px;
  font-weight:800; font-size:0.8rem; border:1px solid;
}
.rx-green { background:#E8F7ED; color:#0B6B3A; border-color:#BFE6CC; }
.rx-yellow { background:#FFF7DF; color:#8A6100; border-color:#F2D98D; }
.rx-red { background:#FDECEC; color:#9A2020; border-color:#F3C5C5; }
.rx-unverified { background:#EEF4FA; color:#26547A; border-color:#C6DCEC; }
.rx-disclaimer {
  background:#F2F7F2; border-left:4px solid #147D46; border-radius:10px;
  padding:0.7rem 0.9rem; color:#23452F;
}
hr { border-color: #DCEBDD; }
</style>
"""

HERO_HTML = """
<div class="rx-shell">
  <div class="rx-copy">
    <div class="rx-kicker">CoU AI Hackathon 2026 · Healthcare</div>
    <h1 style="margin:0 0 6px 0;font-size:1.9rem;color:#0B4B2A;letter-spacing:-.02em;">RxBondhu <span style="color:#147D46;">রক্সবন্ধু</span></h1>
    <p style="margin:0;color:#3D5B48;font-size:0.95rem;line-height:1.5;">
      Handwritten prescription photo → <b>two AI readers</b> → verified brand check → Bangla schedule + audio.<br>
      <span style="color:#0E6B3C;font-weight:700;">Safe by design: nothing appears before you confirm.</span>
    </p>
  </div>
  <div id="rx-fx" style="width:280px;height:170px;flex:0 0 280px;">
    <div class="rx-fallback-pill"><i></i><i></i></div>
  </div>
</div>
<style>
.rx-shell{display:flex;align-items:center;gap:24px;padding:18px 24px;border-radius:22px;
  background:linear-gradient(135deg,#FAFDFB 0%,#EDF7F0 100%);
  border:1px solid #D8EBDD;box-shadow:0 14px 34px rgba(12,80,40,0.10);}
.rx-fallback-pill{width:170px;height:64px;margin:50px auto;border-radius:999px;overflow:hidden;
  display:flex;box-shadow:0 10px 20px rgba(12,80,40,.18);transform:rotate(-18deg);}
.rx-fallback-pill i{flex:1;background:#147D46;}
.rx-fallback-pill i+i{background:#FFFFFF;border-left:2px solid #CFE3D5;}
@media(max-width:760px){.rx-shell{flex-direction:column;align-items:flex-start;}.rx-fx{width:100%!important;flex-basis:auto!important;}}
</style>
<script src="app/static/three.min.js"></script>
<script>
(function(){
  var host = document.getElementById('rx-fx');
  if (!host) return;
  if (typeof THREE === 'undefined') return; // CSS fallback stays visible
  host.innerHTML = '';
  var W = 280, H = 170;
  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(38, W/H, 0.1, 100);
  camera.position.set(0, 0.4, 6.4);
  var renderer = new THREE.WebGLRenderer({alpha:true, antialias:true});
  renderer.setSize(W, H);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  host.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0xffffff, 0.75));
  var key = new THREE.DirectionalLight(0xffffff, 0.95); key.position.set(2,3,4); scene.add(key);
  var rim = new THREE.PointLight(0x2fae6a, 0.9); rim.position.set(-3,1,2); scene.add(rim);

  var pill = new THREE.Group();
  var green = new THREE.MeshStandardMaterial({color:0x147D46, roughness:0.35, metalness:0.12});
  var white = new THREE.MeshStandardMaterial({color:0xF7FBF8, roughness:0.3, metalness:0.05});
  var body = new THREE.Mesh(new THREE.CylinderGeometry(0.62,0.62,1.55,48), green);
  body.rotation.z = Math.PI/2; pill.add(body);
  var left = new THREE.Mesh(new THREE.SphereGeometry(0.62,48,32), green);
  left.position.x = -0.78; pill.add(left);
  var right = new THREE.Mesh(new THREE.SphereGeometry(0.62,48,32), white);
  right.position.x = 0.78; pill.add(right);
  var band = new THREE.Mesh(new THREE.TorusGeometry(0.635,0.035,12,48), white);
  band.rotation.y = Math.PI/2; pill.add(band);
  pill.rotation.set(0.25,-0.5,0.35);
  scene.add(pill);

  var shadow = new THREE.Mesh(new THREE.CircleGeometry(1.05,48),
    new THREE.MeshBasicMaterial({color:0x0B6B3A, transparent:true, opacity:0.10}));
  shadow.rotation.x = -Math.PI/2; shadow.position.set(0,-1.15,0); scene.add(shadow);

  var start = Date.now();
  (function loop(){
    var t = (Date.now()-start)/1000;
    pill.rotation.y = -0.5 + t*0.35;
    pill.position.y = Math.sin(t*1.4)*0.09;
    shadow.material.opacity = 0.10 - Math.sin(t*1.4)*0.02;
    renderer.render(scene, camera);
    requestAnimationFrame(loop);
  })();
})();
</script>
"""


def inject_css() -> None:
    """Apply the clean white + Bangla green theme. Text size is set in app.py."""
    from streamlit import markdown
    markdown(CLEAN_CSS, unsafe_allow_html=True)


def hero() -> None:
    """Compact 3D hero card shown above the step content."""
    st.iframe(HERO_HTML, height=214)


def badge(colour: str) -> str:
    """HTML badge for GREEN / YELLOW / RED."""
    mapping = {
        "GREEN": ("rx-green", "🟢 GREEN"),
        "YELLOW": ("rx-yellow", "🟡 YELLOW"),
        "UNVERIFIED": ("rx-unverified", "🔍 UNVERIFIED"),
        "RED": ("rx-red", "🔴 RED"),
    }
    css, label = mapping.get(str(colour).upper(), ("rx-red", str(colour)))
    return f'<span class="rx-badge {css}">{label}</span>'


def step_header(step: int, bangla: str, english: str) -> None:
    from streamlit import markdown
    markdown(
        f'<div class="rx-step">STEP {step} / 3</div>'
        f'<h2 style="margin:0 0 4px 0;color:#0B4B2A;font-size:1.45rem;">{bangla}</h2>'
        f'<p style="margin:0 0 12px 0;color:#4A6654;">{english}</p>',
        unsafe_allow_html=True,
    )
