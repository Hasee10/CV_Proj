import { useEffect, useRef } from "react";
import * as THREE from "three";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";

// Original procedural model. No remote assets, AI service, or model inference.
export default function GuideCharacter3D() {
  const host = useRef<HTMLSpanElement>(null);
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
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setClearColor(0, 0);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    el.appendChild(renderer.domElement);
    const scene = new THREE.Scene(),
      model = new THREE.Group();
    scene.add(model);
    const camera = new THREE.OrthographicCamera(
      -1.9,
      1.9,
      2.25,
      -2.25,
      0.1,
      30,
    );
    camera.position.set(3, 1.6, 8);
    camera.lookAt(0, 0.1, 0);
    scene.add(new THREE.HemisphereLight("#fffaf1", "#b2a0c1", 2.5));
    const key = new THREE.DirectionalLight("#fff5df", 4.2);
    key.position.set(-4, 6, 7);
    scene.add(key);
    const rim = new THREE.DirectionalLight("#c8b5ff", 3);
    rim.position.set(4, 3, -3);
    scene.add(rim);
    const fill = new THREE.DirectionalLight("#e1f3e7", 1.5);
    fill.position.set(-3, -1, 3);
    scene.add(fill);
    const pearl = new THREE.MeshPhysicalMaterial({
      color: "#f8f2e7",
      roughness: 0.24,
      metalness: 0.04,
      clearcoat: 1,
      clearcoatRoughness: 0.18,
    });
    const lilac = new THREE.MeshPhysicalMaterial({
      color: "#b299c7",
      roughness: 0.28,
      metalness: 0.18,
      clearcoat: 0.8,
    });
    const joint = new THREE.MeshStandardMaterial({
      color: "#80688f",
      roughness: 0.34,
      metalness: 0.3,
    });
    const glass = new THREE.MeshPhysicalMaterial({
      color: "#382e46",
      roughness: 0.2,
      metalness: 0.1,
      clearcoat: 1,
    });
    const eyeInk = new THREE.MeshBasicMaterial({ color: "#d8edb8" });
    const softWhite = new THREE.MeshBasicMaterial({
      color: "#fff8f0",
      transparent: true,
      opacity: 0.25,
    });
    const paper = new THREE.MeshStandardMaterial({
      color: "#fffaf0",
      roughness: 0.6,
    });
    const green = new THREE.MeshStandardMaterial({
      color: "#637d60",
      roughness: 0.4,
    });
    const sphere = new THREE.SphereGeometry(1, 20, 14);
    function box(
      w: number,
      h: number,
      d: number,
      r: number,
      mat: THREE.Material,
      parent: THREE.Object3D = model,
    ) {
      const mesh = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 3, r), mat);
      parent.add(mesh);
      return mesh;
    }
    function ball(
      x: number,
      y: number,
      z: number,
      r: number,
      mat: THREE.Material,
      parent: THREE.Object3D = model,
    ) {
      const mesh = new THREE.Mesh(sphere, mat);
      mesh.scale.setScalar(r);
      mesh.position.set(x, y, z);
      parent.add(mesh);
      return mesh;
    }
    const body = box(1.1, 0.84, 0.78, 0.18, pearl);
    body.position.y = -0.6;
    const collar = box(0.65, 0.15, 0.52, 0.06, joint);
    collar.position.y = -0.08;
    const head = new THREE.Group();
    head.position.y = 0.55;
    model.add(head);
    box(1.76, 1.26, 0.98, 0.3, pearl, head);
    const visor = box(1.43, 0.66, 0.17, 0.21, glass, head);
    visor.position.set(0, 0.02, 0.5);
    const reflection = box(1.02, 0.025, 0.014, 0.01, softWhite, head);
    reflection.position.set(-0.06, 0.23, 0.592);
    const eyes = new THREE.Group();
    head.add(eyes);
    [-0.32, 0.32].forEach((x) => {
      const eye = box(0.115, 0.23, 0.065, 0.055, eyeInk, eyes);
      eye.position.set(x, 0.04, 0.609);
    });
    const smile = new THREE.Mesh(
      new THREE.TorusGeometry(0.11, 0.016, 6, 16, Math.PI),
      eyeInk,
    );
    smile.rotation.z = Math.PI;
    smile.position.set(0, -0.17, 0.603);
    head.add(smile);
    [-1, 1].forEach((side) => {
      const ear = box(0.16, 0.42, 0.46, 0.075, lilac, head);
      ear.position.set(side * 0.94, -0.04, -0.015);
    });
    const antenna = box(0.08, 0.36, 0.08, 0.03, joint, head);
    antenna.position.set(0.3, 0.78, -0.05);
    ball(0.3, 0.99, -0.05, 0.13, lilac, head);
    ball(0.3, 1.01, 0.06, 0.065, eyeInk, head);
    const left = new THREE.Group();
    left.position.set(-0.67, -0.39, 0);
    left.rotation.z = -0.28;
    model.add(left);
    ball(0, 0, 0, 0.16, joint, left);
    const arm = box(0.22, 0.58, 0.26, 0.1, lilac, left);
    arm.position.y = -0.28;
    ball(0, -0.59, 0, 0.16, pearl, left);
    const right = new THREE.Group();
    right.position.set(0.67, -0.36, 0);
    right.rotation.z = -0.76;
    model.add(right);
    ball(0, 0, 0, 0.16, joint, right);
    const waving = box(0.22, 0.54, 0.26, 0.1, lilac, right);
    waving.position.y = 0.27;
    ball(0, 0.57, 0, 0.17, pearl, right);
    [-0.31, 0.31].forEach((x) => {
      const leg = box(0.22, 0.3, 0.25, 0.07, joint);
      leg.position.set(x, -1.12, 0);
      const foot = box(0.43, 0.21, 0.57, 0.095, lilac);
      foot.position.set(x, -1.3, 0.13);
    });
    const sheet = box(0.53, 0.43, 0.055, 0.035, paper);
    sheet.position.set(0, -0.56, 0.422);
    sheet.rotation.z = -0.13;
    const check = new THREE.Group();
    check.position.set(0, -0.56, 0.468);
    check.rotation.z = -0.13;
    model.add(check);
    const short = box(0.06, 0.19, 0.04, 0.02, green, check);
    short.position.set(-0.07, -0.015, 0);
    short.rotation.z = 0.75;
    const long = box(0.06, 0.32, 0.04, 0.02, green, check);
    long.position.set(0.055, 0.035, 0);
    long.rotation.z = -0.65;
    const shadowCanvas = document.createElement("canvas");
    shadowCanvas.width = shadowCanvas.height = 64;
    const ctx = shadowCanvas.getContext("2d")!,
      gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    gradient.addColorStop(0, "rgba(73,48,94,.28)");
    gradient.addColorStop(1, "rgba(73,48,94,0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 64, 64);
    const shadowTexture = new THREE.CanvasTexture(shadowCanvas),
      shadowMaterial = new THREE.MeshBasicMaterial({
        map: shadowTexture,
        transparent: true,
        depthWrite: false,
      });
    const shadow = new THREE.Mesh(
      new THREE.PlaneGeometry(2.7, 1.1),
      shadowMaterial,
    );
    shadow.rotation.x = -Math.PI / 2;
    shadow.position.set(0, -1.44, 0);
    scene.add(shadow);
    const reduced = matchMedia("(prefers-reduced-motion: reduce)");
    let frame = 0,
      disposed = false,
      visible = true,
      hover = false,
      last = 0,
      blinkAt = -1000,
      welcomeUntil = performance.now() + 1400,
      target = 0.0;
    function render(now: number) {
      frame = 0;
      if (disposed || !visible || document.hidden) return;
      const animate =
        !reduced.matches &&
        (hover || now < welcomeUntil || now - blinkAt < 220);
      if (animate && now - last < 40) {
        frame = requestAnimationFrame(render);
        return;
      }
      last = now;
      const t = now / 1000;
      model.rotation.y = hover ? target : 0;
      model.position.y = animate ? Math.sin(t * 2.5) * 0.035 : 0;
      right.rotation.z = -0.76 + (animate ? Math.sin(t * 7) * 0.16 : 0);
      eyes.scale.y = !reduced.matches && now - blinkAt < 180 ? 0.12 : 1;
      renderer.render(scene, camera);
      if (animate) frame = requestAnimationFrame(render);
    }
    function wake() {
      if (!frame && !disposed && visible && !document.hidden)
        frame = requestAnimationFrame(render);
    }
    function resize() {
      const { width, height } = el.getBoundingClientRect();
      if (width && height) {
        renderer.setSize(width, height);
        wake();
      }
    }
    function move(e: PointerEvent) {
      const rect = el.getBoundingClientRect();
      target = ((e.clientX - rect.left) / rect.width - 0.5) * 0.35;
      hover = true;
      wake();
    }
    function leave() {
      hover = false;
      wake();
    }
    function visibility() {
      if (document.hidden) {
        cancelAnimationFrame(frame);
        frame = 0;
      } else wake();
    }
    const timer = setInterval(() => {
      if (!reduced.matches && visible && !document.hidden) {
        blinkAt = performance.now();
        wake();
      }
    }, 5200);
    const ro = new ResizeObserver(resize);
    ro.observe(el);
    const io = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      if (visible) wake();
      else {
        cancelAnimationFrame(frame);
        frame = 0;
      }
    });
    io.observe(el);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerleave", leave);
    document.addEventListener("visibilitychange", visibility);
    reduced.addEventListener("change", wake);
    el.dataset.ready = "true";
    resize();
    return () => {
      disposed = true;
      clearInterval(timer);
      cancelAnimationFrame(frame);
      ro.disconnect();
      io.disconnect();
      el.removeEventListener("pointermove", move);
      el.removeEventListener("pointerleave", leave);
      document.removeEventListener("visibilitychange", visibility);
      reduced.removeEventListener("change", wake);
      const geometries = new Set<THREE.BufferGeometry>();
      scene.traverse((obj) => {
        if (obj instanceof THREE.Mesh) geometries.add(obj.geometry);
      });
      geometries.forEach((g) => g.dispose());
      [
        pearl,
        lilac,
        joint,
        glass,
        eyeInk,
        softWhite,
        paper,
        green,
        shadowMaterial,
      ].forEach((m) => m.dispose());
      shadowTexture.dispose();
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);
  return (
    <span ref={host} className="guide-model" aria-hidden="true">
      <span className="guide-model-fallback">✦</span>
    </span>
  );
}
