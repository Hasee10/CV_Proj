import { useEffect, useRef } from "react";
import * as THREE from "three";

// Independent WebGL implementation of the extruded-icosahedron concept in
// Francesco Michelini's Codrops 3D Cluster. See VISUAL_CREDITS.md.
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
    renderer.setPixelRatio(Math.min(devicePixelRatio, 1.25));
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 30);
    camera.position.z = 4.5;
    const group = new THREE.Group();
    scene.add(group);
    const base = new THREE.IcosahedronGeometry(1, 1),
      attr = base.getAttribute("position");
    const material = new THREE.MeshStandardMaterial({
      color: "#c8cbc5",
      metalness: 0.22,
      roughness: 0.48,
      flatShading: true,
    });
    const pieces: { mesh: THREE.Mesh; center: THREE.Vector3; phase: number }[] =
      [];
    for (let i = 0; i < attr.count; i += 3) {
      const tri = [0, 1, 2].map((j) =>
        new THREE.Vector3().fromBufferAttribute(attr, i + j),
      );
      const center = tri[0].clone().add(tri[1]).add(tri[2]).divideScalar(3);
      const radial = center.clone().normalize().multiplyScalar(0.38);
      const vertices = [...tri, ...tri.map((v) => v.clone().add(radial))].map(
        (v) => v.sub(center),
      );
      const indices = [
        0, 2, 1, 3, 4, 5, 0, 1, 4, 0, 4, 3, 1, 2, 5, 1, 5, 4, 2, 0, 3, 2, 3, 5,
      ];
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute(
        "position",
        new THREE.Float32BufferAttribute(
          indices.flatMap((index) => vertices[index].toArray()),
          3,
        ),
      );
      geometry.computeVertexNormals();
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.copy(center);
      group.add(mesh);
      pieces.push({ mesh, center, phase: i * 0.76 });
    }
    base.dispose();
    scene.add(new THREE.AmbientLight("#b2beb8", 1.1));
    const key = new THREE.DirectionalLight("#ffffff", 4);
    key.position.set(-3, 4, 5);
    scene.add(key);
    const rim = new THREE.DirectionalLight("#83b6a1", 2);
    rim.position.set(4, 0, -2);
    scene.add(rim);
    const lower = new THREE.DirectionalLight("#e6d9bd", 1.3);
    lower.position.set(-1, -4, 1);
    scene.add(lower);
    const pointer = new THREE.Vector2(3, 3),
      raycaster = new THREE.Raycaster();
    const sphere = new THREE.Sphere(new THREE.Vector3(), 1.15),
      point = new THREE.Vector3();
    const local = new THREE.Vector3(),
      inverse = new THREE.Matrix4();
    let strength = 0,
      visible = false,
      frame = 0,
      last = -100,
      disposed = false;
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    let dragging = false,
      dragX = 0,
      rotation = 0;
    function move(e: PointerEvent) {
      const rect = el.getBoundingClientRect();
      pointer.set(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        (-(e.clientY - rect.top) / rect.height) * 2 + 1,
      );
      if (dragging) {
        rotation += (e.clientX - dragX) * 0.008;
        dragX = e.clientX;
      }
      if (reduced.matches) restart();
    }
    function down(e: PointerEvent) {
      dragging = true;
      dragX = e.clientX;
      el.setPointerCapture(e.pointerId);
    }
    function up() {
      dragging = false;
    }
    function leave() {
      pointer.set(3, 3);
    }
    function draw(t: number) {
      if (disposed) return;
      if (visible && !document.hidden && t - last >= 33) {
        last = t;
        const seconds = reduced.matches ? 0 : t * 0.001;
        group.rotation.set(
          0.16 + Math.sin(seconds * 0.13) * 0.12,
          seconds * 0.16 + rotation,
          0.12,
        );
        group.updateMatrixWorld(true);
        raycaster.setFromCamera(pointer, camera);
        const hovering = Boolean(raycaster.ray.intersectSphere(sphere, point));
        strength += (Number(hovering) - strength) * 0.1;
        inverse.copy(group.matrixWorld).invert();
        local.copy(point).applyMatrix4(inverse);
        for (const p of pieces) {
          const wave = 0.5 + 0.2 * Math.sin(seconds * 0.65 + p.phase);
          const hover =
            Math.max(0, 1 - local.distanceTo(p.center) / 0.85) * strength;
          p.mesh.scale.setScalar(wave + hover * 0.52);
          p.mesh.position.copy(p.center).multiplyScalar(1 + hover * 0.08);
        }
        renderer.render(scene, camera);
      }
      if (visible && !document.hidden && !reduced.matches)
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
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      restart();
    }
    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(el);
    const observer = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting;
      restart();
    });
    observer.observe(el);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", up);
    el.addEventListener("lostpointercapture", up);
    el.addEventListener("pointerleave", leave);
    document.addEventListener("visibilitychange", restart);
    reduced.addEventListener("change", restart);
    resize();
    return () => {
      disposed = true;
      cancelAnimationFrame(frame);
      resizeObserver.disconnect();
      observer.disconnect();
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerdown", down);
      el.removeEventListener("pointerup", up);
      el.removeEventListener("pointercancel", up);
      el.removeEventListener("lostpointercapture", up);
      el.removeEventListener("pointerleave", leave);
      document.removeEventListener("visibilitychange", restart);
      reduced.removeEventListener("change", restart);
      pieces.forEach((p) => p.mesh.geometry.dispose());
      material.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);
  return (
    <div
      ref={host}
      className="cluster-stage"
      role="img"
      aria-label="Interactive rotating cluster of triangular prisms. Move to expand the facets or drag to rotate. Decorative illustration, not model output."
    />
  );
}
