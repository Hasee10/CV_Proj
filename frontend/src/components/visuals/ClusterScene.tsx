import { useEffect, useRef } from "react";
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";

// Original geometry and interaction inspired by Francesco Michelini's 3D Cluster.
// A visual metaphor for inspecting evidence; it does not represent model features.
export default function ClusterScene() {
  const host = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = host.current!;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        alpha: true,
        antialias: true,
        powerPreference: "low-power",
      });
    } catch {
      el.dataset.fallback = "true";
      return;
    }
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
    renderer.setClearColor(0, 0);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100);
    camera.position.set(0, 0, 10.5);
    scene.add(new THREE.HemisphereLight("#edffe9", "#142b29", 2.7));
    const key = new THREE.DirectionalLight("#fffae7", 5);
    key.position.set(-4, 5, 6);
    scene.add(key);
    const rim = new THREE.DirectionalLight("#a99be6", 4);
    rim.position.set(4, -1, -2);
    scene.add(rim);
    const geometry = new RoundedBoxGeometry(0.58, 0.58, 0.58, 2, 0.018);
    const material = new THREE.MeshStandardMaterial({
      color: "#dae6d0",
      roughness: 0.3,
      metalness: 0.25,
    });
    const mesh = new THREE.InstancedMesh(geometry, material, 80);
    const group = new THREE.Group();
    group.add(mesh);
    scene.add(group);
    const points: THREE.Vector3[] = [];
    const object = new THREE.Object3D();
    for (let i = 0; i < 80; i++) {
      const y = 1 - (2 * (i + 0.5)) / 80,
        radius = Math.sqrt(1 - y * y),
        angle = i * Math.PI * (3 - Math.sqrt(5));
      points.push(
        new THREE.Vector3(
          Math.cos(angle) * radius,
          y,
          Math.sin(angle) * radius,
        ).multiplyScalar(1.95),
      );
      mesh.setColorAt(
        i,
        new THREE.Color(
          i % 11 === 0 ? "#a89bc2" : i % 5 === 0 ? "#779b90" : "#e2e7d4",
        ),
      );
    }
    let frame = 0,
      visible = false,
      disposed = false,
      hover = false,
      strength = 0,
      drag = false;
    let targetX = -0.2,
      targetY = -0.35,
      lastX = 0,
      lastY = 0,
      lastTime = 0;
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    function render(time: number) {
      frame = 0;
      if (disposed || !visible) return;
      if (time - lastTime < 32) {
        frame = requestAnimationFrame(render);
        return;
      }
      lastTime = time;
      const next = hover && !reduced.matches ? 0.8 : 0;
      strength += (next - strength) * 0.12;
      group.rotation.x += (targetX - group.rotation.x) * 0.1;
      group.rotation.y += (targetY - group.rotation.y) * 0.1;
      points.forEach((p, i) => {
        object.position.copy(p).multiplyScalar(1 + strength * 0.24);
        object.rotation.set(
          p.y * 0.2 + strength * 0.24,
          p.x * 0.22,
          p.z * 0.18,
        );
        object.updateMatrix();
        mesh.setMatrixAt(i, object.matrix);
      });
      mesh.instanceMatrix.needsUpdate = true;
      renderer.render(scene, camera);
      if (
        Math.abs(next - strength) > 0.001 ||
        Math.abs(targetX - group.rotation.x) > 0.001 ||
        Math.abs(targetY - group.rotation.y) > 0.001
      )
        restart();
    }
    function restart() {
      if (!frame && visible && !disposed) frame = requestAnimationFrame(render);
    }
    function resize() {
      const { width, height } = el.getBoundingClientRect();
      if (!width || !height) return;
      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      restart();
    }
    function move(e: PointerEvent) {
      hover = true;
      if (drag) {
        targetY += (e.clientX - lastX) * 0.008;
        targetX += (e.clientY - lastY) * 0.008;
      }
      lastX = e.clientX;
      lastY = e.clientY;
      restart();
    }
    function down(e: PointerEvent) {
      drag = true;
      lastX = e.clientX;
      lastY = e.clientY;
      el.setPointerCapture(e.pointerId);
    }
    function up() {
      drag = false;
    }
    function leave() {
      hover = false;
      drag = false;
      restart();
    }
    function keyboard(e: KeyboardEvent) {
      if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)) {
        e.preventDefault();
        targetY +=
          e.key === "ArrowLeft" ? -0.2 : e.key === "ArrowRight" ? 0.2 : 0;
        targetX += e.key === "ArrowUp" ? -0.2 : e.key === "ArrowDown" ? 0.2 : 0;
        restart();
      }
    }
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(el);
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      if (visible) {
        resize();
        restart();
      } else {
        cancelAnimationFrame(frame);
        frame = 0;
      }
    });
    observer.observe(el);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointerleave", leave);
    el.addEventListener("keydown", keyboard);
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      observer.disconnect();
      resizeObserver.disconnect();
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerdown", down);
      el.removeEventListener("pointerup", up);
      el.removeEventListener("pointerleave", leave);
      el.removeEventListener("keydown", keyboard);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);
  return (
    <div
      ref={host}
      className="cluster-canvas"
      tabIndex={0}
      role="img"
      aria-label="Interactive cubic evidence sculpture. Drag or use arrow keys to rotate. Decorative illustration, not a model output."
    />
  );
}
