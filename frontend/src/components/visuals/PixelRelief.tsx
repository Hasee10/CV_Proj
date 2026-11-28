import { useEffect, useRef } from "react";
import * as THREE from "three";

// This is a paper-relative darkness illustration of the original DEV crop.
// Height encodes darkness, not confidence, attention, or learned features.
export default function PixelRelief({ src }: { src: string }) {
  const host = useRef<HTMLDivElement>(null);
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
    const camera = new THREE.OrthographicCamera(-6.3, 6.3, 3.5, -3.5, 0.1, 100);
    camera.position.set(1.5, -7.5, 12);
    camera.lookAt(0, 0, 0);
    scene.add(new THREE.HemisphereLight("#f3ffe6", "#183c31", 1.65));
    const key = new THREE.DirectionalLight("#fff7df", 4.5);
    key.position.set(-5, -3, 9);
    scene.add(key);
    const rim = new THREE.DirectionalLight("#b2a4de", 2);
    rim.position.set(5, -2, 4);
    scene.add(rim);
    const group = new THREE.Group();
    group.rotation.z = -0.035;
    scene.add(group);
    const boardGeometry = new THREE.BoxGeometry(10.5, 3.5, 0.11);
    const boardMaterial = new THREE.MeshStandardMaterial({
      color: "#e1e8d5",
      roughness: 0.8,
    });
    const board = new THREE.Mesh(boardGeometry, boardMaterial);
    board.position.z = -0.09;
    group.add(board);
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    // Separate face materials make the pixel sidewalls legible at rest.
    const material = [
      "#355d48",
      "#4c7056",
      "#466b50",
      "#254a37",
      "#eef5d8",
      "#254a37",
    ].map(
      (color) =>
        new THREE.MeshStandardMaterial({
          color,
          roughness: 0.6,
          metalness: 0.04,
        }),
    );
    let mesh: THREE.InstancedMesh | undefined,
      disposed = false,
      visible = false,
      frame = 0,
      drag = false,
      lastX = 0,
      lastY = 0;
    let targetX = 0,
      targetZ = -0.035;
    const img = new Image();
    img.onload = () => {
      if (disposed) return;
      try {
        const canvas = document.createElement("canvas");
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        const context = canvas.getContext("2d", { willReadFrequently: true });
        if (!context) throw new Error("Pixel view unavailable");
        context.drawImage(img, 0, 0);
        const { data } = context.getImageData(
          0,
          0,
          canvas.width,
          canvas.height,
        );
        // Paper-relative darkness prevents gray scanned paper from becoming
        // a raised solid wall. This changes only the illustrative height map.
        const luminances: number[] = [];
        for (let i = 0; i < data.length; i += 4)
          luminances.push(
            (0.2126 * data[i] + 0.7152 * data[i + 1] + 0.0722 * data[i + 2]) /
              255,
          );
        const sorted = [...luminances].sort((a, b) => a - b);
        const paper = Math.max(
          0.1,
          sorted[Math.floor((sorted.length - 1) * 0.9)],
        );
        const samples: { x: number; y: number; ink: number }[] = [];
        const step = Math.max(1, Math.ceil(canvas.width / 160));
        for (let y = 0; y < canvas.height; y += step)
          for (let x = 0; x < canvas.width; x += step) {
            const ink = Math.max(
              0,
              (paper - luminances[y * canvas.width + x]) / paper,
            );
            // Keep near-white paper flat so its cell edges do not obscure ink.
            // This display threshold never changes the source or model input.
            if (ink >= 0.1) samples.push({ x, y, ink });
          }
        mesh = new THREE.InstancedMesh(geometry, material, samples.length);
        const object = new THREE.Object3D(),
          light = new THREE.Color("#e1e8d5"),
          dark = new THREE.Color("#86aa87");
        const unit = Math.min(10 / canvas.width, 2.8 / canvas.height);
        samples.forEach(({ x, y, ink }, i) => {
          const height = 0.012 + ink * 1.05;
          object.position.set(
            (x + step / 2 - canvas.width / 2) * unit,
            (canvas.height / 2 - y - step / 2) * unit,
            height / 2,
          );
          object.scale.set(step * unit * 0.9, step * unit * 0.9, height);
          object.updateMatrix();
          mesh!.setMatrixAt(i, object.matrix);
          mesh!.setColorAt(i, light.clone().lerp(dark, ink));
        });
        group.add(mesh);
        el.dataset.ready = "true";
        restart();
      } catch {
        el.dataset.fallback = "true";
        renderer.domElement.hidden = true;
      }
    };
    img.onerror = () => {
      if (!disposed) {
        el.dataset.fallback = "true";
        renderer.domElement.hidden = true;
      }
    };
    img.src = src;
    const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
    function render() {
      frame = 0;
      if (disposed || !visible) return;
      const blend = reducedMotion.matches ? 1 : 0.2;
      group.rotation.x += (targetX - group.rotation.x) * blend;
      group.rotation.z += (targetZ - group.rotation.z) * blend;
      renderer.render(scene, camera);
      if (
        Math.abs(targetX - group.rotation.x) +
          Math.abs(targetZ - group.rotation.z) >
        0.001
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
      const halfWidth = 6.35;
      camera.left = -halfWidth;
      camera.right = halfWidth;
      camera.top = (halfWidth * height) / width;
      camera.bottom = -camera.top;
      camera.updateProjectionMatrix();
      restart();
    }
    function down(e: PointerEvent) {
      drag = true;
      lastX = e.clientX;
      lastY = e.clientY;
      el.setPointerCapture(e.pointerId);
    }
    function move(e: PointerEvent) {
      if (!drag) return;
      targetZ += (e.clientX - lastX) * 0.006;
      targetX = Math.max(
        -0.55,
        Math.min(0.55, targetX + (e.clientY - lastY) * 0.006),
      );
      lastX = e.clientX;
      lastY = e.clientY;
      restart();
    }
    function up() {
      drag = false;
    }
    function keyboard(e: KeyboardEvent) {
      if (
        ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home"].includes(
          e.key,
        )
      ) {
        e.preventDefault();
        if (e.key === "Home") {
          targetX = 0;
          targetZ = -0.035;
        } else {
          targetZ +=
            e.key === "ArrowLeft" ? -0.15 : e.key === "ArrowRight" ? 0.15 : 0;
          targetX = Math.max(
            -0.55,
            Math.min(
              0.55,
              targetX +
                (e.key === "ArrowUp"
                  ? -0.12
                  : e.key === "ArrowDown"
                    ? 0.12
                    : 0),
            ),
          );
        }
        restart();
      }
    }
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(el);
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      if (visible) resize();
      else {
        cancelAnimationFrame(frame);
        frame = 0;
      }
    });
    observer.observe(el);
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", up);
    el.addEventListener("keydown", keyboard);
    return () => {
      disposed = true;
      img.onload = null;
      img.onerror = null;
      cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      observer.disconnect();
      el.removeEventListener("pointerdown", down);
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerup", up);
      el.removeEventListener("pointercancel", up);
      el.removeEventListener("keydown", keyboard);
      mesh?.dispose();
      geometry.dispose();
      material.forEach((face) => face.dispose());
      boardGeometry.dispose();
      boardMaterial.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, [src]);
  return (
    <div
      ref={host}
      className="pixel-relief"
      role="img"
      tabIndex={0}
      aria-label="3D relief of the original numeric crop. Pixels darker than the estimated paper tone are taller. Drag or use arrow keys to inspect; Home resets the view. This is not a learned feature map."
    >
      <img
        className="relief-fallback"
        src={src}
        alt="Original numeric crop; 3D view unavailable"
      />
    </div>
  );
}
