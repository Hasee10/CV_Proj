import { useEffect, useRef } from "react";
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";

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
    renderer.setClearColor("#ccd1ce");
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.3;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-10, 10, 5, -5, 0.1, 100);
    camera.position.set(0, 0, 18);
    camera.lookAt(0, 0, 0);
    const geometry = new RoundedBoxGeometry(0.965, 0.965, 0.88, 2, 0.03);
    const material = new THREE.MeshStandardMaterial({
      color: "#ffffff",
      metalness: 0.06,
      roughness: 0.4,
    });
    scene.add(new THREE.HemisphereLight("#ffffff", "#b7c1bb", 1.8));
    const key = new THREE.DirectionalLight("#fff9ef", 3);
    key.position.set(-6, 8, 9);
    key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024);
    key.shadow.bias = -0.00015;
    key.shadow.normalBias = 0.025;
    key.shadow.camera.near = 0.5;
    key.shadow.camera.far = 60;
    scene.add(key);
    const rim = new THREE.DirectionalLight("#d8deeb", 0.45);
    rim.position.set(5, -3, 7);
    scene.add(rim);
    const backingGeometry = new THREE.PlaneGeometry(1, 1);
    const backingMaterial = new THREE.MeshStandardMaterial({
      color: "#adb8b1",
      roughness: 1,
    });
    const backing = new THREE.Mesh(backingGeometry, backingMaterial);
    backing.position.z = -1.3;
    backing.receiveShadow = true;
    scene.add(backing);
    let mesh: THREE.InstancedMesh | undefined;
    let columns = 0,
      rows = 0,
      worldWidth = 0,
      worldHeight = 0;
    let visible = false,
      disposed = false,
      frame = 0,
      last = -100;
    let lastMovement = -1000,
      strength = 0;
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    const pointer = new THREE.Vector2(1000, 1000),
      smoothPointer = pointer.clone();
    const raycaster = new THREE.Raycaster();
    const pointerNdc = new THREE.Vector2();
    const surface = new THREE.Plane(new THREE.Vector3(0, 0, 1), 0);
    const intersection = new THREE.Vector3();
    const object = new THREE.Object3D(),
      color = new THREE.Color();
    const neutral = new THREE.Color("#e4e7e4"),
      lavender = new THREE.Color("#b7b8dd");
    function move(e: PointerEvent) {
      const rect = el.getBoundingClientRect();
      pointerNdc.set(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        1 - ((e.clientY - rect.top) / rect.height) * 2,
      );
      raycaster.setFromCamera(pointerNdc, camera);
      if (raycaster.ray.intersectPlane(surface, intersection))
        pointer.set(intersection.x, intersection.y);
      if (smoothPointer.x > 100) smoothPointer.copy(pointer);
      lastMovement = performance.now();
      restart();
    }
    function leave() {
      lastMovement = -1000;
      restart();
    }
    function render(t: number) {
      if (disposed) return;
      let rendered = false;
      if (mesh && visible && !document.hidden && t - last >= 33) {
        last = t;
        const moving = t - lastMovement < 140;
        strength = reduced.matches
          ? 0
          : THREE.MathUtils.lerp(strength, moving ? 1 : 0, 0.18);
        if (!moving && strength < 0.002) strength = 0;
        if (pointer.x > 100) smoothPointer.copy(pointer);
        else smoothPointer.lerp(pointer, 0.12);
        let index = 0;
        for (let row = 0; row < rows; row++)
          for (let col = 0; col < columns; col++) {
            const x = col - (columns - 1) / 2,
              y = row - (rows - 1) / 2;
            const distance = Math.hypot(
              x - smoothPointer.x,
              y - smoothPointer.y,
            );
            const hover = Math.exp((-distance * distance) / 3.1) * strength;
            const quietLeft = THREE.MathUtils.smoothstep(
              x / worldWidth + 0.5,
              0.12,
              0.6,
            );
            object.position.set(x, y, hover * (0.65 + 0.4 * quietLeft));
            object.scale.setScalar(1.025 - hover * 0.025);
            object.rotation.set(
              hover * Math.tanh(y - smoothPointer.y) * 0.13,
              -hover * Math.tanh(x - smoothPointer.x) * 0.13,
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
        rendered = true;
      }
      if (
        visible &&
        !document.hidden &&
        (!rendered ||
          (!reduced.matches && (strength > 0 || t - lastMovement < 140)))
      )
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
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      scene.add(mesh);
      camera.left = -worldWidth / 2;
      camera.right = worldWidth / 2;
      camera.top = worldHeight / 2;
      camera.bottom = -worldHeight / 2;
      camera.updateProjectionMatrix();
      backing.scale.set(worldWidth + 8, worldHeight + 8, 1);
      const shadowExtent = Math.max(worldWidth, worldHeight) * 0.75 + 3;
      Object.assign(key.shadow.camera, {
        left: -shadowExtent,
        right: shadowExtent,
        top: shadowExtent,
        bottom: -shadowExtent,
      });
      key.shadow.camera.updateProjectionMatrix();
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
      backingGeometry.dispose();
      backingMaterial.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);
  return (
    <div
      ref={host}
      className="wave-grid-stage"
      role="img"
      aria-label="Pale tiles that rise locally while the pointer moves, then settle flat when movement stops. Decorative illustration, not model output."
    />
  );
}
