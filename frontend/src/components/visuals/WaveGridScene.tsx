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
    camera.position.set(0, -2.2, 18);
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
    key.shadow.mapSize.set(2048, 2048);
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
    let hovering = false,
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
      lavender = new THREE.Color("#927ccf");
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
      hovering = true;
      restart();
    }
    function leave() {
      hovering = false;
      restart();
    }
    function render(t: number) {
      if (disposed) return;
      let rendered = false;
      let needsMore = false;
      if (mesh && visible && !document.hidden && t - last >= 33) {
        last = t;
        const goal = hovering ? 1 : 0;
        strength = reduced.matches
          ? goal
          : THREE.MathUtils.lerp(strength, goal, 0.2);
        if (Math.abs(strength - goal) < 0.002) strength = goal;
        if (pointer.x > 100) smoothPointer.copy(pointer);
        else if (reduced.matches) smoothPointer.copy(pointer);
        else smoothPointer.lerp(pointer, 0.2);
        needsMore =
          Math.abs(strength - goal) > 0.002 ||
          smoothPointer.distanceTo(pointer) > 0.002;
        let index = 0;
        for (let row = 0; row < rows; row++)
          for (let col = 0; col < columns; col++) {
            const x = col - (columns - 1) / 2,
              y = row - (rows - 1) / 2;
            const distance = Math.hypot(
              x - smoothPointer.x,
              y - smoothPointer.y,
            );
            const hover = Math.exp((-distance * distance) / 2.8) * strength;
            object.position.set(x, y, reduced.matches ? 0 : hover * 0.62);
            object.scale.setScalar(1.02);
            object.rotation.set(0, 0, 0);
            object.updateMatrix();
            mesh.setMatrixAt(index, object.matrix);
            color.copy(neutral).lerp(lavender, strength * 0.1 + hover * 0.88);
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
        (!rendered || (!reduced.matches && needsMore))
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
      aria-label="Aligned pale tiles that rise and turn violet under the pointer, with a subtle background colour response. They return flat when the pointer leaves. Decorative illustration, not model output."
    />
  );
}
