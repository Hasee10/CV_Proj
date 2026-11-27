import { useEffect, useRef } from "react";
import * as THREE from "three";

// Original instanced geometry and interaction, visually referencing Franky
// Hung / Arkon Digital's Wavy Cubes. No reference source or assets copied.
export default function WaveGridScene() {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = host.current!;
    const target = el.closest("section") ?? el;
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
    renderer.setClearColor("#c7cdca");
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-10, 10, 5, -5, 0.1, 100);
    camera.position.set(0, 0, 18);
    const geometry = new THREE.BoxGeometry(0.994, 0.994, 0.65);
    const material = new THREE.MeshStandardMaterial({
      color: "#ffffff",
      metalness: 0.12,
      roughness: 0.34,
    });
    scene.add(new THREE.HemisphereLight("#ffffff", "#bcc0c4", 2.1));
    const key = new THREE.DirectionalLight("#ffffff", 2.5);
    key.position.set(-4, 7, 12);
    scene.add(key);
    const rim = new THREE.DirectionalLight("#d8deeb", 1.1);
    rim.position.set(5, -3, 7);
    scene.add(rim);
    let mesh: THREE.InstancedMesh | undefined;
    let columns = 0,
      rows = 0,
      worldWidth = 0,
      worldHeight = 0;
    let visible = false,
      disposed = false,
      frame = 0,
      last = -100;
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    const pointer = new THREE.Vector2(1000, 1000),
      smoothPointer = pointer.clone();
    const object = new THREE.Object3D(),
      color = new THREE.Color();
    const neutral = new THREE.Color("#e4e7e4"),
      lavender = new THREE.Color("#b7b8dd");
    function move(e: PointerEvent) {
      const rect = el.getBoundingClientRect();
      pointer.set(
        ((e.clientX - rect.left) / rect.width - 0.5) * worldWidth,
        (0.5 - (e.clientY - rect.top) / rect.height) * worldHeight,
      );
      if (smoothPointer.x > 100) smoothPointer.copy(pointer);
      if (reduced.matches) restart();
    }
    function leave() {
      pointer.set(1000, 1000);
      if (reduced.matches) restart();
    }
    function render(t: number) {
      if (disposed) return;
      if (mesh && visible && !document.hidden && t - last >= 33) {
        last = t;
        const time = reduced.matches ? 0 : t * 0.00035;
        if (pointer.x > 100) smoothPointer.copy(pointer);
        else smoothPointer.lerp(pointer, 0.12);
        let index = 0;
        for (let row = 0; row < rows; row++)
          for (let col = 0; col < columns; col++) {
            const x = col - (columns - 1) / 2,
              y = row - (rows - 1) / 2;
            const wave =
              Math.sin(x * 0.49 + time) * Math.cos(y * 0.43 - time * 0.8);
            const distance = Math.hypot(
              x - smoothPointer.x,
              y - smoothPointer.y,
            );
            const hover = Math.exp((-distance * distance) / 3.7);
            const quietLeft = THREE.MathUtils.smoothstep(
              x / worldWidth + 0.5,
              0.12,
              0.6,
            );
            const amplitude = 0.16 + 0.26 * quietLeft;
            object.position.set(x, y, wave * amplitude + hover * 0.55);
            object.rotation.set(
              Math.sin(y * 0.43 - time * 0.8) * 0.045 * quietLeft +
                hover * 0.06,
              Math.cos(x * 0.49 + time) * 0.065 * quietLeft - hover * 0.04,
              0,
            );
            object.updateMatrix();
            mesh.setMatrixAt(index, object.matrix);
            color.copy(neutral).lerp(lavender, hover * 0.7);
            mesh.setColorAt(index, color);
            index++;
          }
        mesh.instanceMatrix.needsUpdate = true;
        if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
        renderer.render(scene, camera);
      }
      if (visible && !document.hidden && !reduced.matches)
        frame = requestAnimationFrame(render);
    }
    function restart() {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(render);
    }
    function resize() {
      const w = el.clientWidth,
        h = el.clientHeight;
      if (!w || !h) return;
      const cell = w < 600 ? 65 : 84;
      worldWidth = w / cell;
      worldHeight = h / cell;
      columns = Math.ceil(worldWidth) + 4;
      rows = Math.ceil(worldHeight) + 4;
      if (mesh) {
        scene.remove(mesh);
        mesh.dispose();
      }
      mesh = new THREE.InstancedMesh(geometry, material, columns * rows);
      mesh.frustumCulled = false;
      mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      scene.add(mesh);
      camera.left = -worldWidth / 2;
      camera.right = worldWidth / 2;
      camera.top = worldHeight / 2;
      camera.bottom = -worldHeight / 2;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
      restart();
    }
    const sizeObserver = new ResizeObserver(resize);
    sizeObserver.observe(el);
    const observer = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      restart();
    });
    observer.observe(el);
    target.addEventListener("pointermove", move as EventListener);
    target.addEventListener("pointerleave", leave);
    document.addEventListener("visibilitychange", restart);
    reduced.addEventListener("change", restart);
    resize();
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      sizeObserver.disconnect();
      observer.disconnect();
      target.removeEventListener("pointermove", move as EventListener);
      target.removeEventListener("pointerleave", leave);
      document.removeEventListener("visibilitychange", restart);
      reduced.removeEventListener("change", restart);
      mesh?.dispose();
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);
  return (
    <div
      ref={host}
      className="wave-grid-stage"
      role="img"
      aria-label="A full-width pale tiled surface with gently undulating cubes and a lavender highlight that follows the pointer. Decorative illustration, not model output."
    />
  );
}
