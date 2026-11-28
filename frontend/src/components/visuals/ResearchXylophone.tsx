import { useEffect, useRef } from "react";
import * as THREE from "three";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

// Glass-bar motion is illustrative. Six selectable bands navigate saved datasets.
export default function ResearchXylophone({
  selected,
  onSelect,
}: {
  selected: number;
  onSelect: (index: number) => void;
}) {
  const host = useRef<HTMLDivElement>(null),
    state = useRef({ selected, onSelect });
  const invalidate = useRef<() => void>(() => {});
  useEffect(() => {
    state.current = { selected, onSelect };
    invalidate.current();
  }, [selected, onSelect]);
  useEffect(() => {
    const el = host.current!;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        powerPreference: "low-power",
      });
    } catch {
      el.dataset.fallback = "true";
      return;
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.25));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const backdrop = document.createElement("canvas");
    backdrop.width = backdrop.height = 256;
    const ctx = backdrop.getContext("2d")!,
      gradient = ctx.createLinearGradient(0, 0, 256, 256);
    gradient.addColorStop(0, "#f3eced");
    gradient.addColorStop(0.5, "#e9e1f0");
    gradient.addColorStop(1, "#b2a0cf");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 256, 256);
    const background = new THREE.CanvasTexture(backdrop);
    background.colorSpace = THREE.SRGBColorSpace;
    scene.background = background;
    const pmrem = new THREE.PMREMGenerator(renderer),
      room = new RoomEnvironment();
    const environment = pmrem.fromScene(room, 0.04);
    scene.environment = environment.texture;
    room.dispose();
    pmrem.dispose();
    scene.add(new THREE.HemisphereLight("#ffffff", "#a79ab3", 1.8));
    const light = new THREE.DirectionalLight("#fff3db", 3);
    light.position.set(-3, 5, 8);
    scene.add(light);
    const rim = new THREE.DirectionalLight("#c7b9ff", 2);
    rim.position.set(4, -2, -2);
    scene.add(rim);
    const camera = new THREE.OrthographicCamera(-6, 6, 4.8, -4.8, 0.1, 50);
    camera.position.set(0, 0, 14);
    const geometry = new THREE.CapsuleGeometry(0.135, 3.1, 6, 14);
    const material = new THREE.MeshPhysicalMaterial({
      color: "#ffffff",
      roughness: 0.18,
      metalness: 0.05,
      transmission: 0.24,
      thickness: 0.45,
      ior: 1.4,
      iridescence: 0.35,
      iridescenceIOR: 1.3,
      iridescenceThicknessRange: [180, 520],
      clearcoat: 1,
      envMapIntensity: 1.4,
    });
    const count = 64,
      mesh = new THREE.InstancedMesh(geometry, material, count);
    mesh.frustumCulled = false;
    mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
    mesh.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 16);
    scene.add(mesh);
    const object = new THREE.Object3D(),
      color = new THREE.Color(),
      highlight = new THREE.Color("#e8a445");
    const palette = [
      new THREE.Color("#8d67ba"),
      new THREE.Color("#55a6b7"),
      new THREE.Color("#b5759a"),
      new THREE.Color("#667ec0"),
      new THREE.Color("#c79650"),
      new THREE.Color("#aa789d"),
    ];
    const raycaster = new THREE.Raycaster(),
      reduced = matchMedia("(prefers-reduced-motion: reduce)");
    let frame = 0,
      disposed = false,
      visible = false,
      last = 0,
      time = 0,
      orbit = 0,
      scrollPhase = 0,
      downX: number | null = null,
      distance = 0,
      lastPick = 0;
    function draw(now: number) {
      frame = 0;
      if (!visible || disposed || document.hidden) return;
      const moving = !reduced.matches;
      if (moving && now - last < 33) {
        frame = requestAnimationFrame(draw);
        return;
      }
      if (moving) time += Math.min((now - last) / 1000, 0.05);
      last = now;
      for (let i = 0; i < count; i++) {
        const t = i / (count - 1),
          theta = t * Math.PI * 3 + orbit + time * 0.22 + scrollPhase;
        const band = Math.min(5, Math.floor(t * 6)),
          active = band === state.current.selected,
          y = (t - 0.5) * 14;
        object.position.set(
          Math.sin(theta) * 0.65 + y * 0.28,
          y,
          Math.cos(theta) * 0.65 + (active ? 0.12 : 0),
        );
        object.rotation.set(0.08, theta, Math.PI / 2 + 0.12);
        object.scale.set(
          1,
          0.72 + 0.28 * Math.sin(t * Math.PI) + (active ? 0.06 : 0),
          1,
        );
        object.updateMatrix();
        mesh.setMatrixAt(i, object.matrix);
        color
          .copy(palette[state.current.selected])
          .lerp(highlight, active ? 0.85 : 0.08);
        mesh.setColorAt(i, color);
      }
      mesh.instanceMatrix.needsUpdate = true;
      if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
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
      const half = 7.8,
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
      const hit = raycaster.intersectObject(mesh, false)[0];
      return hit?.instanceId === undefined
        ? undefined
        : Math.min(5, Math.floor((hit.instanceId / count) * 6));
    }
    function down(e: PointerEvent) {
      downX = e.clientX;
      distance = 0;
      el.setPointerCapture(e.pointerId);
    }
    function move(e: PointerEvent) {
      if (downX !== null) {
        const dx = e.clientX - downX;
        orbit += dx * 0.008;
        distance += Math.abs(dx);
        downX = e.clientX;
        wake();
      } else if (e.pointerType !== "touch" && e.timeStamp - lastPick > 65) {
        lastPick = e.timeStamp;
        const index = pick(e);
        el.style.cursor = index === undefined ? "grab" : "pointer";
        if (index !== undefined) state.current.onSelect(index);
      }
    }
    function up(e: PointerEvent) {
      downX = null;
      if (distance < 6) {
        const index = pick(e);
        if (index !== undefined) state.current.onSelect(index);
      }
    }
    function key(e: KeyboardEvent) {
      if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) {
        e.preventDefault();
        state.current.onSelect(
          (state.current.selected +
            (["ArrowLeft", "ArrowUp"].includes(e.key) ? 5 : 1)) %
            6,
        );
      }
      if (e.key === "Home") {
        e.preventDefault();
        orbit = 0;
        wake();
      }
    }
    function scroll() {
      scrollPhase =
        (el.getBoundingClientRect().top / Math.max(1, innerHeight)) * 0.6;
      wake();
    }
    function visibility() {
      if (document.hidden) {
        cancelAnimationFrame(frame);
        frame = 0;
      } else wake();
    }
    const ro = new ResizeObserver(resize);
    ro.observe(el);
    const io = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      if (visible) resize();
      else {
        cancelAnimationFrame(frame);
        frame = 0;
      }
    });
    io.observe(el);
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", up);
    el.addEventListener("keydown", key);
    addEventListener("scroll", scroll, { passive: true });
    document.addEventListener("visibilitychange", visibility);
    reduced.addEventListener("change", wake);
    return () => {
      disposed = true;
      invalidate.current = () => {};
      cancelAnimationFrame(frame);
      ro.disconnect();
      io.disconnect();
      el.removeEventListener("pointerdown", down);
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerup", up);
      el.removeEventListener("pointercancel", up);
      el.removeEventListener("keydown", key);
      removeEventListener("scroll", scroll);
      document.removeEventListener("visibilitychange", visibility);
      reduced.removeEventListener("change", wake);
      geometry.dispose();
      material.dispose();
      environment.dispose();
      background.dispose();
      mesh.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);
  return (
    <div
      ref={host}
      className="research-spiral research-xylophone"
      role="img"
      tabIndex={0}
      aria-label="Interactive glass xylophone: six selectable bands navigate the six saved datasets. Geometry is illustrative, not an error-rate plot. Drag to turn the bars; arrow keys select datasets; Home resets the view."
    >
      <div className="spiral-fallback" aria-hidden="true">
        {Array.from({ length: 18 }, (_, i) => (
          <i key={i} style={{ transform: `rotateY(${i * 18}deg)` }} />
        ))}
      </div>
    </div>
  );
}
