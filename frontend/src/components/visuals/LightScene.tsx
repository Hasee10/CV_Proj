import { useEffect, useRef } from "react";
import * as THREE from "three";

// Original procedural scene. The light study by Cullen Webber is a visual
// reference only; no source, hand model, textures or shaders are copied.
const fragment = `
precision mediump float;
uniform vec2 resolution;
uniform float time;
varying vec2 vUv;
float hash(vec2 p) { return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
void main() {
  vec2 uv = vUv;
  vec3 col = mix(vec3(.027,.051,.065),vec3(.055,.094,.12),uv.y);
  // Integrate an angled cone through a sparse, slowly drifting fog field.
  vec3 ray=normalize(vec3((uv-.5)*vec2(resolution.x/resolution.y,1.),-1.4));
  float light=0.;
  for(int i=0;i<24;i++) {
    float d=float(i)*.16;
    vec3 p=vec3(0.,0.,2.)+ray*d;
    float axis=p.x*.57+p.y*.82;
    float along=p.x*.82-p.y*.57;
    float cone=exp(-pow((axis-.27)/(max(.13,(along+1.8)*.29)),2.)*2.5);
    float mist=.65+.16*sin(p.x*6.+p.z*3.+time*.12)*sin(p.y*8.-time*.08);
    light+=cone*mist*.025;
  }
  col+=vec3(.33,.48,.47)*light;
  float source=exp(-length((uv-vec2(1.04,.95))*vec2(1.,1.5))*6.);
  col+=vec3(.18,.24,.22)*source;
  col+=(hash(gl_FragCoord.xy)-.5)*.014;
  col*=1.-.32*length(uv-.5);
  gl_FragColor=vec4(col,1.);
}`;

function paperTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 1200;
  canvas.height = 580;
  const c = canvas.getContext("2d")!;
  c.fillStyle = "#e6e9df";
  c.fillRect(0, 0, 1200, 580);
  c.strokeStyle = "#ccd5cb";
  c.lineWidth = 1;
  for (let x = 0; x < 1200; x += 18) {
    c.beginPath();
    c.moveTo(x, 0);
    c.bezierCurveTo(x + 55, 190, x - 55, 390, x, 580);
    c.stroke();
  }
  c.fillStyle = "#edf0e7";
  c.fillRect(55, 50, 1090, 480);
  c.fillStyle = "#304c49";
  c.font = "500 32px Arial";
  c.fillText("ChequeVerify", 85, 110);
  c.font = "16px monospace";
  c.fillText("DOCUMENT STUDY / SYNTHETIC ILLUSTRATION", 85, 145);
  c.strokeStyle = "#9aaba0";
  c.lineWidth = 1;
  for (const y of [238, 320, 408]) {
    c.beginPath();
    c.moveTo(85, y);
    c.lineTo(1110, y);
    c.stroke();
  }
  c.fillStyle = "#62766a";
  c.font = "16px Arial";
  c.fillText("AMOUNT IN WORDS", 85, 212);
  c.fillText("AMOUNT IN FIGURES", 790, 375);
  c.strokeStyle = "#26675e";
  c.lineWidth = 2;
  c.strokeRect(80, 252, 780, 55);
  c.strokeRect(786, 391, 320, 65);
  c.fillStyle = "#62766a";
  c.font = "15px monospace";
  c.fillText("SELECTED REGIONS", 85, 485);
  c.fillText("NO BANK DATA", 915, 485);
  return new THREE.CanvasTexture(canvas);
}

export default function LightScene() {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = host.current!;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: false,
        alpha: true,
        powerPreference: "low-power",
      });
    } catch {
      return;
    } // CSS atmosphere and navigation remain without WebGL.
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.25));
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 50);
    camera.position.z = 8;
    const uniforms = {
      resolution: { value: new THREE.Vector2() },
      time: { value: 0 },
    };
    const fogMaterial = new THREE.ShaderMaterial({
      uniforms,
      vertexShader:
        "varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position.xy,1.,1.);}",
      fragmentShader: fragment,
      depthTest: false,
      depthWrite: false,
    });
    const backdrop = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), fogMaterial);
    backdrop.renderOrder = -1;
    backdrop.frustumCulled = false;
    scene.add(backdrop);
    const geometry = new THREE.PlaneGeometry(3.6, 1.74, 32, 10);
    const positions = geometry.attributes.position;
    for (let i = 0; i < positions.count; i++) {
      const x = positions.getX(i);
      positions.setZ(i, 0.09 * x * x);
    }
    geometry.computeVertexNormals();
    const texture = paperTexture();
    texture.colorSpace = THREE.SRGBColorSpace;
    const material = new THREE.MeshStandardMaterial({
      map: texture,
      roughness: 0.88,
      side: THREE.DoubleSide,
    });
    const paper = new THREE.Mesh(geometry, material);
    paper.rotation.set(-0.26, -0.38, -0.22);
    scene.add(paper);
    const ambient = new THREE.AmbientLight("#8aa5a4", 1.6);
    scene.add(ambient);
    const key = new THREE.DirectionalLight("#f5f5db", 3);
    key.position.set(3, 5, 5);
    scene.add(key);
    let visible = true,
      frame = 0,
      last = -100,
      disposed = false;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    function draw(t: number) {
      if (disposed) return;
      if (visible && !document.hidden && t - last >= 33) {
        last = t;
        const seconds = reduced.matches ? 0 : t * 0.001;
        uniforms.time.value = seconds;
        paper.rotation.z = -0.22 + Math.sin(seconds * 0.22) * 0.025;
        paper.rotation.y = -0.38 + Math.sin(seconds * 0.18) * 0.04;
        renderer.render(scene, camera);
      }
      if (!reduced.matches && visible && !document.hidden)
        frame = requestAnimationFrame(draw);
    }
    function restart() {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(draw);
    }
    function resize() {
      const w = el.clientWidth,
        h = el.clientHeight;
      if (!w || !h) return;
      renderer.setSize(w, h);
      uniforms.resolution.value.set(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      const narrow = w < 760;
      paper.position.set(narrow ? 0.05 : 1.8, narrow ? -1.12 : 0.05, 0);
      paper.scale.setScalar(narrow ? 0.5 : w < 1100 ? 0.86 : 1);
      restart();
    }
    const observer = new ResizeObserver(resize);
    observer.observe(el);
    const intersection = new IntersectionObserver((entries) => {
      visible = entries[0].isIntersecting;
      restart();
    });
    intersection.observe(el);
    const lost = (e: Event) => {
      e.preventDefault();
      cancelAnimationFrame(frame);
      renderer.domElement.style.display = "none";
    };
    renderer.domElement.addEventListener("webglcontextlost", lost);
    document.addEventListener("visibilitychange", restart);
    reduced.addEventListener("change", restart);
    resize();
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      observer.disconnect();
      intersection.disconnect();
      document.removeEventListener("visibilitychange", restart);
      reduced.removeEventListener("change", restart);
      renderer.domElement.removeEventListener("webglcontextlost", lost);
      geometry.dispose();
      material.dispose();
      texture.dispose();
      backdrop.geometry.dispose();
      fogMaterial.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);
  return <div className="light-scene" ref={host} aria-hidden="true" />;
}
