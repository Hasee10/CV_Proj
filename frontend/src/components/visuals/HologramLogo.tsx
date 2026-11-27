import { useEffect, useRef, useState } from "react";
import * as THREE from "three";

const outlines = [
  [
    [8, 8],
    [31, 8],
    [31, 18],
    [18, 18],
    [18, 46],
    [31, 46],
    [31, 56],
    [8, 56],
  ],
  [
    [26, 32],
    [36, 42],
    [55, 15],
    [63, 21],
    [37, 57],
    [20, 40],
  ],
];
function contains(x: number, y: number, polygon: number[][]) {
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const [xi, yi] = polygon[i],
      [xj, yj] = polygon[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi)
      inside = !inside;
  }
  return inside;
}
export default function HologramLogo() {
  const host = useRef<HTMLDivElement>(null);
  const [fallback, setFallback] = useState(false);
  useEffect(() => {
    const element = host.current;
    if (!element) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    } catch {
      setFallback(true);
      return;
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
    element.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    camera.position.z = 5;
    const group = new THREE.Group();
    scene.add(group);
    const positions: number[] = [];
    for (let y = 8; y <= 57; y += 1.65)
      for (let x = 8; x <= 63; x += 1.65)
        if (outlines.some((p) => contains(x, y, p)))
          for (const z of [-0.08, 0.08])
            positions.push((x - 35) / 28, (32 - y) / 28, z);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute(
      "position",
      new THREE.Float32BufferAttribute(positions, 3),
    );
    const material = new THREE.ShaderMaterial({
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      uniforms: { pixelRatio: { value: Math.min(devicePixelRatio, 1.5) } },
      vertexShader: `uniform float pixelRatio; varying float depth;
        void main(){ vec4 p=modelViewMatrix*vec4(position,1.); depth=position.z;
          gl_PointSize=pixelRatio*(7.5/-p.z)*4.; gl_Position=projectionMatrix*p; }`,
      fragmentShader: `varying float depth; void main(){float d=length(gl_PointCoord-.5);
        float core=1.-smoothstep(.1,.3,d); float glow=exp(-d*6.);
        vec3 c=mix(vec3(.45,.83,.85),vec3(.93,1.,.91),core);
        gl_FragColor=vec4(c*1.8,min(1.,core*.95+glow*.8));}`,
    });
    group.add(new THREE.Points(geometry, material));
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    let frame = 0,
      last = -100,
      visible = true;
    const target = new THREE.Vector2();
    const render = (time: number) => {
      if (visible && !document.hidden && time - last > 33) {
        last = time;
        group.rotation.y = reduced.matches
          ? -0.12
          : Math.sin(time * 0.00032) * 0.16 + target.x * 0.18;
        group.rotation.x = reduced.matches ? 0.03 : target.y * 0.1;
        group.position.y = reduced.matches
          ? 0
          : Math.sin(time * 0.0008) * 0.035;
        renderer.render(scene, camera);
      }
      if (visible && !document.hidden && !reduced.matches)
        frame = requestAnimationFrame(render);
    };
    const restart = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(render);
    };
    const resize = () => {
      if (!element.clientWidth || !element.clientHeight) return;
      renderer.setSize(element.clientWidth, element.clientHeight);
      camera.aspect = element.clientWidth / element.clientHeight;
      camera.updateProjectionMatrix();
      restart();
    };
    const move = (e: PointerEvent) => {
      target.set(e.clientX / innerWidth - 0.5, e.clientY / innerHeight - 0.5);
      if (reduced.matches) restart();
    };
    const observer = new ResizeObserver(resize);
    observer.observe(element);
    const intersection = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      restart();
    });
    intersection.observe(element);
    document.addEventListener("pointermove", move);
    document.addEventListener("visibilitychange", restart);
    reduced.addEventListener("change", restart);
    resize();
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      intersection.disconnect();
      document.removeEventListener("pointermove", move);
      document.removeEventListener("visibilitychange", restart);
      reduced.removeEventListener("change", restart);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);
  return (
    <div ref={host} className="hologram-logo">
      {fallback && <img src="/brand/mark-3d.png" alt="" />}
    </div>
  );
}
