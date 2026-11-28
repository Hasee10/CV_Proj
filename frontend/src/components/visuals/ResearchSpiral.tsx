import { useEffect, useRef } from "react";
import * as THREE from "three";

// Dataset navigation inspired by Synordinate's rolling vertical panels.
// Spiral geometry is illustrative; measured error rates stay in live text.
export default function ResearchSpiral({
  selected,
  paused,
  onSelect,
}: {
  selected: number;
  paused: boolean;
  onSelect: (index: number) => void;
}) {
  const host = useRef<HTMLDivElement>(null);
  const state = useRef({ selected, paused, onSelect });
  const invalidate = useRef<() => void>(() => {});
  useEffect(() => {
    state.current = { selected, paused, onSelect };
    invalidate.current();
  }, [selected, paused, onSelect]);
  useEffect(() => {
    const el = host.current!;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "low-power",
      });
    } catch {
      el.dataset.fallback = "true";
      return;
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.25));
    renderer.setClearColor(0, 0);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-5, 5, 4.7, -4.7, 0.1, 60);
    camera.position.set(7, 2, 13);
    camera.lookAt(0, 0, 0);
    scene.add(new THREE.HemisphereLight("#f3f5df", "#10392a", 2));
    const sun = new THREE.DirectionalLight("#f2f6d9", 3.7);
    sun.position.set(4, 7, 7);
    scene.add(sun);
    const rim = new THREE.DirectionalLight("#b6a1e8", 3);
    rim.position.set(-5, 0, -3);
    scene.add(rim);
    const sculpture = new THREE.Group();
    sculpture.rotation.y = -0.35;
    scene.add(sculpture);
    const point = (t: number, phase = 0) => {
      const theta = t * Math.PI * 3.5 + phase;
      return new THREE.Vector3(
        Math.cos(theta) * 2.1,
        (t - 0.5) * 7.2,
        Math.sin(theta) * 2.1,
      );
    };
    const materials: THREE.Material[] = [];
    const geometries: THREE.BufferGeometry[] = [];
    function material(color: string, metalness = 0.12) {
      const m = new THREE.MeshStandardMaterial({
        color,
        metalness,
        roughness: 0.38,
      });
      materials.push(m);
      return m;
    }
    for (const phase of [0, Math.PI]) {
      const curve = new THREE.CatmullRomCurve3(
        Array.from({ length: 97 }, (_, i) => point(i / 96, phase)),
      );
      const geo = new THREE.TubeGeometry(curve, 150, 0.018, 5, false);
      geometries.push(geo);
      sculpture.add(new THREE.Mesh(geo, material(phase === 0 ? "#8da89b" : "#bed39c", 0.3)));
    }
    const shape = new THREE.Shape();
    const w = 0.16,
      h = 0.8,
      r = 0.025;
    shape.moveTo(-w / 2 + r, -h / 2);
    shape.lineTo(w / 2 - r, -h / 2);
    shape.quadraticCurveTo(w / 2, -h / 2, w / 2, -h / 2 + r);
    shape.lineTo(w / 2, h / 2 - r);
    shape.quadraticCurveTo(w / 2, h / 2, w / 2 - r, h / 2);
    shape.lineTo(-w / 2 + r, h / 2);
    shape.quadraticCurveTo(-w / 2, h / 2, -w / 2, h / 2 - r);
    shape.lineTo(-w / 2, -h / 2 + r);
    shape.quadraticCurveTo(-w / 2, -h / 2, -w / 2 + r, -h / 2);
    const slatGeo = new THREE.ExtrudeGeometry(shape, {
      depth: 0.18,
      bevelEnabled: true,
      bevelSize: 0.018,
      bevelThickness: 0.018,
      bevelSegments: 2,
      steps: 1,
      curveSegments: 2,
    });
    slatGeo.translate(0, 0, -0.09);
    geometries.push(slatGeo);
    const slats: THREE.Mesh<
      THREE.ExtrudeGeometry,
      THREE.MeshStandardMaterial
    >[] = [];
    for (let i = 0; i < 64; i++) {
      const t = i / 63;
      const mesh = new THREE.Mesh(
        slatGeo,
        material(t < 4 / 6 ? "#9fbda0" : "#aaa1c2"),
      );
      mesh.position.copy(point(t));
      sculpture.add(mesh);
      slats.push(mesh);
    }
    const nodes: THREE.Mesh[] = [];
    const nodeGeo = new THREE.SphereGeometry(0.12, 14, 10);
    geometries.push(nodeGeo);
    const hitGeo = new THREE.SphereGeometry(0.36, 8, 6);
    geometries.push(hitGeo);
    const hitMat = new THREE.MeshBasicMaterial({ visible: false });
    materials.push(hitMat);
    const hits: THREE.Mesh[] = [];
    const rungs: THREE.Mesh<THREE.TubeGeometry, THREE.MeshStandardMaterial>[] =
      [];
    for (let i = 0; i < 6; i++) {
      const t = 0.06 + i * 0.176;
      const a = point(t),
        b = point(t, Math.PI);
      const curve = new THREE.LineCurve3(a, b);
      const geo = new THREE.TubeGeometry(curve, 1, 0.023, 6, false);
      geometries.push(geo);
      const rung = new THREE.Mesh(geo, material("#648772"));
      sculpture.add(rung);
      rungs.push(rung);
      for (const p of [a, b]) {
        const node = new THREE.Mesh(nodeGeo, material("#afc69d"));
        node.position.copy(p);
        sculpture.add(node);
        nodes.push(node);
        const hit = new THREE.Mesh(hitGeo, hitMat);
        hit.position.copy(p);
        hit.userData.index = i;
        sculpture.add(hit);
        hits.push(hit);
      }
    }
    const lightGeo = new THREE.SphereGeometry(0.035, 6, 4);
    geometries.push(lightGeo);
    const flowMat = new THREE.MeshBasicMaterial({ color: "#e4efbd" });
    materials.push(flowMat);
    const flow = Array.from({ length: 8 }, () => {
      const mesh = new THREE.Mesh(lightGeo, flowMat);
      sculpture.add(mesh);
      return mesh;
    });
    const baseGeo = new THREE.CylinderGeometry(1.9, 1.9, 0.035, 64);
    geometries.push(baseGeo);
    const base = new THREE.Mesh(baseGeo, material("#234a39"));
    base.position.y = -4.05;
    scene.add(base);
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    const raycaster = new THREE.Raycaster();
    let frame = 0,
      visible = false,
      disposed = false,
      last = 0,
      time = 0,
      orbit = 0,
      downX: number | null = null,
      dragDistance = 0;
    let active = -1;
    const highlight = new THREE.Color("#e1ecc3");
    function draw(now: number) {
      frame = 0;
      if (!visible || disposed || document.hidden) return;
      const moving = !state.current.paused && !reduced.matches;
      if (moving && now - last < 33) {
        frame = requestAnimationFrame(draw);
        return;
      }
      if (moving) time += Math.min((now - last) / 1000, 0.05);
      last = now;
      sculpture.rotation.y = -0.35 + orbit + time * 0.09;
      if (active !== state.current.selected) {
        active = state.current.selected;
        rungs.forEach((m, i) =>
          m.material.color.set(i === active ? "#e3edba" : "#5c8069"),
        );
        nodes.forEach((m, i) =>
          (m.material as THREE.MeshStandardMaterial).color.set(
            Math.floor(i / 2) === active
              ? "#f0f3cb"
              : i < 8
                ? "#9bb499"
                : "#b5a8cc",
          ),
        );
      }
      slats.forEach((m, i) => {
        const t = i / 63,
          strength = Math.exp(-Math.pow((t - (0.06 + active * 0.176)) * 12, 2));
        const phase = time * 0.24 - i * 0.16;
        m.rotation.set(
          0.15 * Math.sin(phase),
          -t * Math.PI * 3.5 + phase * 0.35,
          0.08 * Math.cos(phase),
        );
        m.scale.setScalar(1 + strength * 0.22);
        m.material.color
          .set(t < 4 / 6 ? "#9fbda0" : "#aaa1c2")
          .lerp(highlight, strength * 0.8);
      });
      flow.forEach((m, i) =>
        m.position.copy(point((time * 0.055 + i / 4) % 1, i % 2 ? Math.PI : 0)),
      );
      renderer.render(scene, camera);
      if (moving) frame = requestAnimationFrame(draw);
    }
    function wake() {
      if (!frame && visible && !disposed && !document.hidden)
        frame = requestAnimationFrame(draw);
    }
    invalidate.current = wake;
    function resize() {
      const { width, height } = el.getBoundingClientRect();
      if (!width || !height) return;
      renderer.setSize(width, height);
      const half = 4.6,
        aspect = width / height;
      camera.left = -half * aspect;
      camera.right = half * aspect;
      camera.top = half;
      camera.bottom = -half;
      camera.updateProjectionMatrix();
      wake();
    }
    function pick(e: PointerEvent) {
      const box = el.getBoundingClientRect();
      raycaster.setFromCamera(
        new THREE.Vector2(
          ((e.clientX - box.left) / box.width) * 2 - 1,
          (-(e.clientY - box.top) / box.height) * 2 + 1,
        ),
        camera,
      );
      return raycaster.intersectObjects(hits, false)[0]?.object.userData
        .index as number | undefined;
    }
    function down(e: PointerEvent) {
      downX = e.clientX;
      dragDistance = 0;
      el.setPointerCapture(e.pointerId);
    }
    function move(e: PointerEvent) {
      if (downX !== null) {
        const delta = e.clientX - downX;
        orbit += delta * 0.008;
        dragDistance += Math.abs(delta);
        downX = e.clientX;
        wake();
      } else if (e.pointerType !== "touch") {
        const index = pick(e);
        el.style.cursor = index === undefined ? "grab" : "pointer";
        if (index !== undefined) state.current.onSelect(index);
      }
    }
    function up(e: PointerEvent) {
      downX = null;
      if (dragDistance < 6) {
        const index = pick(e);
        if (index !== undefined) state.current.onSelect(index);
      }
    }
    function key(e: KeyboardEvent) {
      if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key)) {
        e.preventDefault();
        state.current.onSelect(
          (state.current.selected +
            (["ArrowUp", "ArrowLeft"].includes(e.key) ? 5 : 1)) %
            6,
        );
      }
      if (e.key === "Home") {
        e.preventDefault();
        orbit = 0;
        wake();
      }
    }
    function visibility() {
      if (document.hidden) {
        cancelAnimationFrame(frame);
        frame = 0;
      } else wake();
    }
    const ro = new ResizeObserver(resize);
    ro.observe(el);
    const io = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      if (visible) resize();
      else {
        cancelAnimationFrame(frame);
        frame = 0;
      }
    });
    io.observe(el);
    reduced.addEventListener("change", wake);
    document.addEventListener("visibilitychange", visibility);
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", up);
    el.addEventListener("keydown", key);
    return () => {
      disposed = true;
      invalidate.current = () => {};
      cancelAnimationFrame(frame);
      ro.disconnect();
      io.disconnect();
      reduced.removeEventListener("change", wake);
      document.removeEventListener("visibilitychange", visibility);
      el.removeEventListener("pointerdown", down);
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerup", up);
      el.removeEventListener("pointercancel", up);
      el.removeEventListener("keydown", key);
      geometries.forEach((g) => g.dispose());
      materials.forEach((m) => m.dispose());
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);
  return (
    <div
      className="research-spiral"
      ref={host}
      role="img"
      tabIndex={0}
      aria-label="Interactive research spiral: six dataset pairs around two paths, baseline and ATHN. Illustrative geometry does not encode error rate. Drag to orbit; arrow keys select a dataset; Home resets the view."
    >
      <div className="spiral-fallback" aria-hidden="true">
        {Array.from({ length: 18 }, (_, i) => (
          <i key={i} style={{ transform: `rotateY(${i * 24}deg)` }} />
        ))}
      </div>
    </div>
  );
}
